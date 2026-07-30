import enum
import uuid
from sqlalchemy import String, Text, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ContactStatus(str, enum.Enum):
    """
    Enumeration for the status of a ContactRequest.
    Inheriting from `str` and `enum.Enum` helps with Pydantic serialization later.
    """
    NEW = "NEW"
    READ = "READ"
    REPLIED = "REPLIED"


class ContactRequest(Base, TimestampMixin):
    """
    Represents a contact form submission from a visitor.
    """
    __tablename__ = "contact_requests"  # Plural naming convention

    # Uuid(as_uuid=True) provides database-agnostic UUID column support
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Bounding string length prevents malicious massive payloads from wasting database space.
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Indexed to enable fast dashboard filtering by company name.
    company: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Indexed to allow the Admin to quickly search all messages from a specific email.
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Text type is used for long-form content with no strict upper limit in Postgres.
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Stored as an Enum in PostgreSQL natively.
    # This prevents invalid data (like status="IGNORED") from ever being saved.
    status: Mapped[ContactStatus] = mapped_column(
        Enum(ContactStatus, native_enum=True),
        nullable=False,
        default=ContactStatus.NEW,
        server_default=ContactStatus.NEW.value,
        index=True,  # Indexed because the Admin dashboard will heavily filter by status.
    )

    def __repr__(self) -> str:
        return f"<ContactRequest(email='{self.email}', status='{self.status.value}')>"
