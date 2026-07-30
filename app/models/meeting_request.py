import uuid
import enum
from datetime import datetime, date

from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Uuid
from sqlalchemy.sql import func

from app.core.database import Base


class MeetingRequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class MeetingRequest(Base):
    __tablename__ = "meeting_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(100), nullable=False)
    company_name = Column(String(150), nullable=False)
    business_email = Column(String(255), nullable=False, index=True)
    meeting_date = Column(Date, nullable=False, index=True)
    comment = Column(Text, nullable=True)
    # Use String instead of Enum to avoid asyncpg enum type casting issues
    status = Column(String(20), default=MeetingRequestStatus.PENDING.value, nullable=False, index=True)

    # Soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<MeetingRequest {self.business_email} - {self.meeting_date} [{self.status}]>"
