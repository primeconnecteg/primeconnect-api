from fastapi import APIRouter
from app.api.v1.contact import router as contact_router
from app.api.v1.auth import router as auth_router
from app.api.v1.admin import router as admin_router
from app.api.v1.meeting_requests import router as meeting_requests_router
from app.api.v1.admin_meeting_requests import router as admin_meeting_requests_router

# This is the master router for version 1 of our API.
api_router = APIRouter()

# Public Endpoints
api_router.include_router(
    contact_router,
    tags=["Public"]
)

api_router.include_router(
    meeting_requests_router,
    prefix="/meeting-requests",
    tags=["Meeting Requests (Public)"]
)

# Authentication Endpoints
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# Admin Endpoints
api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration"]
)

api_router.include_router(
    admin_meeting_requests_router,
    prefix="/admin/meeting-requests",
    tags=["Meeting Requests (Admin)"]
)
