"""Seed script to create demo users in the database."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.db.session import async_session_factory
from app.services.auth_service import create_user, get_user_by_email


DEMO_USERS = [
    {"name": "Alice Chen", "email": "alice@warroom.dev", "password": "password123"},
    {"name": "Bob Martinez", "email": "bob@warroom.dev", "password": "password123"},
    {"name": "Carol Singh", "email": "carol@warroom.dev", "password": "password123"},
    {"name": "David Kim", "email": "david@warroom.dev", "password": "password123"},
]


async def seed():
    print("Seeding demo users...")
    async with async_session_factory() as db:
        for user_data in DEMO_USERS:
            existing = await get_user_by_email(db, user_data["email"])
            if existing:
                print(f"  ✓ {user_data['email']} already exists")
            else:
                await create_user(db, user_data["name"], user_data["email"], user_data["password"])
                print(f"  + Created {user_data['name']} ({user_data['email']})")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(seed())
