from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class AdminResponse(BaseModel):
    """
    Schema for returning Admin details to the frontend.
    Notice that `password_hash` is STRICTLY EXCLUDED.
    """
    id: UUID
    username: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
