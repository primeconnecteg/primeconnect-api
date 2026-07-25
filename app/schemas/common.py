from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel

# TypeVar allows us to create a Generic schema that can wrap ANY other schema.
T = TypeVar('T')

class MessageResponse(BaseModel):
    """
    Standardized response for simple success or error messages.
    Instead of returning a raw dictionary like {"message": "Success"} in routes,
    we use this schema to explicitly define the response structure.
    """
    message: str

class PaginatedResponse(BaseModel, Generic[T]):
    """
    A generic schema for returning lists of items (like a list of ContactRequests).
    It includes the total count for frontend pagination.
    """
    items: Sequence[T]
    total: int
