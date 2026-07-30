import uuid
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Admin(Base, TimestampMixin):
    """
    Represents an Administrator in the database.
    Only one or a few of these will exist.
    They are the only users who can access the dashboard.
    """
    __tablename__ = "admins"  # Plural naming convention

    # Uuid(as_uuid=True) provides database-agnostic UUID column support (Postgres, SQLite, etc.)
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The username must be unique and indexed for fast login lookups.
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    # We store the Argon2 hash, never the plaintext password.
    # String(255) provides plenty of room for long hash outputs.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self) -> str:
        return f"<Admin(username='{self.username}')>"
