import asyncio
import logging
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.admin import Admin
from app.core.security import hash_password

# =============================================================================
# 1. LOGGING CONFIGURATION
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def seed_admin() -> None:
    """
    Idempotent script to seed the initial administrator account.
    Safe to run repeatedly.
    """
    logger.info("Seed started: Checking for initial administrator account.")
    
    # Fail fast if environment variables are missing
    if not settings.ADMIN_USERNAME or not settings.ADMIN_PASSWORD:
        logger.error("Seeding aborted: ADMIN_USERNAME or ADMIN_PASSWORD missing from configuration.")
        return

    # Use the session factory from app.core.database to spawn a new async connection
    async with AsyncSessionLocal() as session:
        try:
            # Deterministic check: Does THIS specific username exist?
            query = select(Admin).where(Admin.username == settings.ADMIN_USERNAME)
            result = await session.execute(query)
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                logger.info(f"Seed completed: Administrator '{settings.ADMIN_USERNAME}' already exists. No action taken.")
                return
                
            # Business Rule: Passwords must NEVER be stored in plaintext.
            # We hash it here so it is fully secure before it even hits the session.
            hashed_password = hash_password(settings.ADMIN_PASSWORD)
            
            # Create the SQLAlchemy model
            new_admin = Admin(
                username=settings.ADMIN_USERNAME,
                password_hash=hashed_password
            )
            
            # Persist to database
            session.add(new_admin)
            await session.commit()
            
            logger.info(f"Seed completed: Successfully created administrator '{settings.ADMIN_USERNAME}'.")
            
        except Exception as e:
            # If a database constraint fails or the network drops, rollback immediately.
            await session.rollback()
            logger.error(f"Unexpected failure during seed process: {e}")
            raise

if __name__ == "__main__":
    # This block only executes if the file is run directly (not imported).
    # Since SQLAlchemy is async, we need asyncio.run() to execute the coroutine.
    asyncio.run(seed_admin())
