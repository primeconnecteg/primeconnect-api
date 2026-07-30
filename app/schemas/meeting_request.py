from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.meeting_request import MeetingRequestStatus


class MeetingRequestBase(BaseModel):
    full_name: str = Field(..., alias="fullName")
    company_name: str = Field(..., alias="companyName")
    business_email: str = Field(..., alias="businessEmail")
    meeting_date: date = Field(..., alias="meetingDate")
    comment: Optional[str] = Field(None, alias="comments")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )

    @field_validator("full_name", mode="before")
    @classmethod
    def validate_full_name(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Missing full_name: Full Name is required.")
        val = v.strip()
        if len(val) < 2:
            raise ValueError("Missing full_name: Full Name must be at least 2 characters long.")
        if len(val) > 100:
            raise ValueError("Invalid full_name: Full Name cannot exceed 100 characters.")
        return val

    @field_validator("company_name", mode="before")
    @classmethod
    def validate_company_name(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Invalid company_name: Company Name is required.")
        val = v.strip()
        if len(val) > 150:
            raise ValueError("Invalid company_name: Company Name cannot exceed 150 characters.")
        return val

    @field_validator("business_email", mode="before")
    @classmethod
    def validate_business_email(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Invalid email: Business Email is required.")
        val = v.strip().lower()
        if "@" not in val or "." not in val.split("@")[-1]:
            raise ValueError("Invalid email: Please enter a valid business email address.")
        return val

    @field_validator("meeting_date", mode="before")
    @classmethod
    def validate_meeting_date(cls, v: Any) -> date:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Meeting date is required.")
        
        parsed_date: Optional[date] = None
        if isinstance(v, str):
            date_str = v.split("T")[0].strip()
            try:
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Invalid meeting_date: Expected format YYYY-MM-DD.")
        elif isinstance(v, date):
            parsed_date = v
        else:
            raise ValueError("Invalid meeting_date: Invalid date format.")

        # Allow 1 day grace period for timezone differences (UTC vs local time)
        yesterday = date.today() - timedelta(days=1)
        if parsed_date < yesterday:
            raise ValueError("Meeting date is in the past: Please select today or a future date.")

        return parsed_date

    @field_validator("comment", mode="before")
    @classmethod
    def sanitize_comment(cls, v: Any) -> Optional[str]:
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        val = str(v).strip()
        if len(val) > 5000:
            raise ValueError("Invalid comment: Comment cannot exceed 5,000 characters.")
        return val


class MeetingRequestCreate(MeetingRequestBase):
    pass


class MeetingRequestUpdate(BaseModel):
    status: str


class MeetingRequestResponse(MeetingRequestBase):
    id: UUID
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MeetingRequestListResponse(BaseModel):
    items: list[MeetingRequestResponse]
    total: int
    page: int
    size: int
