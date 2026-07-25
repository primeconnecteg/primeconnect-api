from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.contact_request import ContactStatus

class ContactCreate(BaseModel):
    """
    Schema for receiving a new contact form submission.
    This strictly defines and validates what the visitor is allowed to send.
    """
    # Name must be provided, at least 2 chars, max 100.
    name: str = Field(..., min_length=2, max_length=100)
    
    # Company is optional. If provided, max 100 chars.
    company: Optional[str] = Field(None, max_length=100)
    
    # EmailStr strictly validates the string against proper email formats.
    email: EmailStr
    # The actual message must be substantial enough (10 chars) but bounded (5000 chars)
    # to protect the database from massive payload attacks.
    message: str = Field(..., min_length=10, max_length=5000)

class ContactResponse(BaseModel):
    """
    Schema for returning a ContactRequest to the Administrator dashboard.
    """
    id: UUID
    name: str
    company: Optional[str]
    email: EmailStr
    message: str
    status: ContactStatus
    created_at: datetime
    
    # In Pydantic v2, ConfigDict(from_attributes=True) replaces `orm_mode = True`.
    # This tells Pydantic to read data not just from dictionary keys, 
    # but also from object attributes (e.g., `model.email`).
    # This is critical for converting SQLAlchemy models directly into Pydantic schemas.
    model_config = ConfigDict(from_attributes=True)

class ContactStatusUpdate(BaseModel):
    """
    Schema for updating a message's status.
    By using the ContactStatus enum, FastAPI will automatically reject invalid statuses.
    """
    status: ContactStatus
