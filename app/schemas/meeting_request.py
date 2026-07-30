from datetime import date, datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.meeting_request import MeetingRequestStatus


class MeetingRequestBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    company_name: str = Field(..., max_length=150)
    business_email: EmailStr
    meeting_date: date
    comment: Optional[str] = Field(None, max_length=5000)

    @field_validator("comment", mode="before")
    @classmethod
    def sanitize_comment(cls, v: Any) -> Optional[str]:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @field_validator("meeting_date", mode="before")
    @classmethod
    def validate_meeting_date(cls, v: Any) -> Any:
        if isinstance(v, str):
            from datetime import datetime
            try:
                return datetime.strptime(v.split("T")[0], "%Y-%m-%d").date()
            except Exception:
                pass
        return v


class MeetingRequestCreate(MeetingRequestBase):
    pass


class MeetingRequestUpdate(BaseModel):
    status: MeetingRequestStatus


class MeetingRequestResponse(MeetingRequestBase):
    id: UUID
    status: MeetingRequestStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingRequestListResponse(BaseModel):
    items: list[MeetingRequestResponse]
    total: int
    page: int
    size: int
