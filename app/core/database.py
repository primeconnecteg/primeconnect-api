import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

# Set up a basic logger for database-related events
logger = logging.getLogger(__name__)

# ==========================================
# 1. THE ASYNC ENGINE
# ==========================================
_engine_kwargs = {
    "url": settings.SQLALCHEMY_DATABASE_URI,
    "echo": False,
}

if settings.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
    _engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
    })

engine = create_async_engine(**_engine_kwargs)

# ==========================================
# 2. THE ASYNC SESSION FACTORY
# ==========================================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ==========================================
# 3. NAMING CONVENTIONS & DECLARATIVE BASE
# ==========================================
# Consistent naming conventions for database constraints
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Apply conventions to MetaData
metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.0 declarative models.
    Provides the metadata with standardized naming conventions.
    """
    metadata = metadata

# ==========================================
# 4. DEPENDENCY INJECTION (get_db)
# ==========================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an asynchronous database session.
    The session's lifecycle is managed here, but transaction boundaries
    (commit/rollback) belong in the Services layer.
    """
    async with AsyncSessionLocal() as session:
        yield session

# ==========================================
# 5. CONNECTION TEST & LIFECYCLE HELPERS
# ==========================================
async def check_database_connection() -> None:
    """
    Tests the database connectivity by executing a simple query.
    Fails fast by raising an exception if the connection is invalid.
    """
    try:
        # Use connect() to verify connectivity without starting a transaction
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info(f"Successfully connected to the database ({engine.url.get_backend_name()}).")
    except SQLAlchemyError as e:
        logger.critical(f"Database connection failed during startup: {e}")
        raise  # Fail fast!

async def close_database_connection() -> None:
    """
    Disposes of the engine and safely closes all connections in the pool.
    """
    await engine.dispose()
    logger.info("Database connection pool disposed.")
