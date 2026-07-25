# This file makes the schemas directory a Python package and exposes our schemas
# for easy importing (e.g. `from app.schemas import ContactCreate, AdminResponse`).

from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.contact import ContactCreate, ContactResponse
from app.schemas.admin import AdminResponse
from app.schemas.auth import LoginRequest, TokenResponse, TokenPayload
