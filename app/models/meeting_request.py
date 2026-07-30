import uuid
import enum
from datetime import datetime, date

from sqlalchemy import Column, String, Text, DateTime, Date, Boolean, Enum, Uuid
from sqlalchemy.sql import func

from app.core.database import Base


class MeetingRequestStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    COMPLETED = "Completed"


class MeetingRequest(Base):
    __tablename__ = "meeting_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String(100), nullable=False)
    company_name = Column(String(150), nullable=False)
    business_email = Column(String(255), nullable=False, index=True)
    meeting_date = Column(Date, nullable=False, index=True)
    comment = Column(Text, nullable=True)
    status = Column(Enum(MeetingRequestStatus, name="meeting_request_status", create_constraint=True), default=MeetingRequestStatus.PENDING, nullable=False, index=True)
    
    # Soft delete flag
    is_deleted = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<MeetingRequest {self.business_email} - {self.meeting_date} [{self.status.value}]>"
