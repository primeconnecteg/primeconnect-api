from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.meeting_request import MeetingRequestStatus


class MeetingRequestBase(BaseModel):
    full_name: str = Field(..., min_length=3, max_length=100)
    company_name: str = Field(..., max_length=150)
    business_email: EmailStr
    meeting_date: date
    comment: str = Field(..., min_length=1000, max_length=5000)

    @field_validator("meeting_date")
    @classmethod
    def validate_meeting_date(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Meeting date cannot be in the past.")
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
