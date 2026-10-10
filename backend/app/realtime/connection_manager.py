"""In-memory WebSocket connection manager for a single FastAPI process."""

import json
import logging
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per incident room."""

    def __init__(self):
        # incident_id -> set of (user_id, WebSocket)
        self._rooms: dict[UUID, dict[UUID, WebSocket]] = {}

    async def connect(self, incident_id: UUID, user_id: UUID, websocket: WebSocket):
        await websocket.accept()
        if incident_id not in self._rooms:
            self._rooms[incident_id] = {}
        # If user already connected, close old connection
        old_ws = self._rooms[incident_id].get(user_id)
        if old_ws:
            try:
                await old_ws.close(code=4001, reason="Replaced by new connection")
            except Exception:
                pass
        self._rooms[incident_id][user_id] = websocket
        logger.info(f"User {user_id} connected to incident {incident_id}")

    def disconnect(self, incident_id: UUID, user_id: UUID):
        room = self._rooms.get(incident_id)
        if room and user_id in room:
            del room[user_id]
            if not room:
                del self._rooms[incident_id]
        logger.info(f"User {user_id} disconnected from incident {incident_id}")

    async def broadcast_to_incident(self, incident_id: UUID, message: dict, exclude_user: UUID | None = None):
        """Broadcast a JSON message to all connected clients in an incident room."""
        room = self._rooms.get(incident_id)
        if not room:
            return
        payload = json.dumps(message, default=str)
        disconnected = []
        for uid, ws in room.items():
            if exclude_user and uid == exclude_user:
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(uid)
        # Clean up broken connections
        for uid in disconnected:
            self.disconnect(incident_id, uid)

    def get_connected_users(self, incident_id: UUID) -> list[UUID]:
        room = self._rooms.get(incident_id, {})
        return list(room.keys())

    def get_room_count(self, incident_id: UUID) -> int:
        return len(self._rooms.get(incident_id, {}))


# Singleton instance
manager = ConnectionManager()
