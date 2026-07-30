import asyncio
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine, Base
from app.models.contact_request import ContactRequest
from app.models.meeting_request import MeetingRequest
from app.models.admin import Admin

async def init_db():
    print("Connecting to Supabase PostgreSQL database...")
    async with engine.begin() as conn:
        print("Creating missing database tables and enums...")
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
