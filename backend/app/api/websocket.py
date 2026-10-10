"""WebSocket endpoint for real-time incident room updates with visibility access control."""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.security import decode_access_token
from app.db.session import async_session_factory
from app.realtime.connection_manager import manager
from app.services.auth_service import get_user_by_id
from app.services.incident_service import _get_incident_or_404, can_view_incident

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/incidents/{incident_id}")
async def incident_websocket(
    websocket: WebSocket,
    incident_id: UUID,
    token: str = Query(...),
):
    """
    WebSocket endpoint for real-time incident room.
    Connect with: ws://host/ws/incidents/{id}?token=<jwt>
    Enforces authentication and visibility permissions.
    """
    # Authenticate via query parameter token
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4003, reason="Authentication failed")
        return

    # Enforce incident visibility and access control
    async with async_session_factory() as db:
        user = await get_user_by_id(db, user_id)
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return

        try:
            incident = await _get_incident_or_404(db, incident_id)
        except Exception:
            await websocket.close(code=4004, reason="Incident not found")
            return

        has_access = await can_view_incident(db, incident, user)
        if not has_access:
            await websocket.close(code=4003, reason="Access denied: unauthorized visibility")
            return

    await manager.connect(incident_id, user_id, websocket)

    # Notify room of new connection
    await manager.broadcast_to_incident(incident_id, {
        "type": "user_connected",
        "data": {"user_id": str(user_id), "connected_count": manager.get_room_count(incident_id)},
    }, exclude_user=user_id)

    try:
        while True:
            # Keep connection alive; handle client messages (ping/pong, etc.)
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(incident_id, user_id)
        await manager.broadcast_to_incident(incident_id, {
            "type": "user_disconnected",
            "data": {"user_id": str(user_id), "connected_count": manager.get_room_count(incident_id)},
        })
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id} in incident {incident_id}: {e}")
        manager.disconnect(incident_id, user_id)