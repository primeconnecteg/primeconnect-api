from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.models.contact_request import ContactStatus
from app.schemas.contact import ContactResponse, ContactStatusUpdate
from app.services.contact_service import ContactService
from app.services.admin_service import AdminService

router = APIRouter()

@router.get(
    "/dashboard",
    summary="Get Dashboard Statistics",
    description="Returns aggregate statistics for the admin dashboard (e.g., total messages, unread messages)."
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> dict:
    """
    Notice the `current_admin: Admin = Depends(get_current_admin)`.
    This completely protects the route. The route function will not even execute 
    if the visitor does not provide a valid JWT.
    """
    return await AdminService.get_dashboard_stats(db)

@router.get(
    "/messages",
    response_model=List[ContactResponse],
    summary="List Contact Requests"
)
async def list_messages(
    skip: int = Query(0, description="Pagination offset"),
    limit: int = Query(100, description="Pagination limit"),
    status: Optional[ContactStatus] = Query(None, description="Filter by message status"),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> List[ContactResponse]:
    """
    List messages with optional pagination, status filtering, and text search.
    """
    return await ContactService.list_contacts(
        db=db, skip=skip, limit=limit, status=status, search=search
    )

@router.get(
    "/messages/{message_id}",
    response_model=ContactResponse,
    summary="View Contact Request"
)
async def view_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> ContactResponse:
    """
    View a single message by its UUID.
    """
    message = await ContactService.get_contact(db, message_id)
    if not message:
        # 404 Not Found is the standard HTTP response when a requested resource does not exist.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

@router.patch(
    "/messages/{message_id}/status",
    response_model=ContactResponse,
    summary="Update Message Status"
)
async def update_message_status(
    message_id: UUID,
    status_update: ContactStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> ContactResponse:
    """
    PATCH is semantically used for partial updates (like changing just the status).
    """
    message = await ContactService.update_status(db, message_id, status_update.status)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return message

@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Contact Request"
)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
) -> None:
    """
    Permanently deletes a message.
    HTTP 204 No Content means "The action succeeded, but I have no data to return".
    """
    success = await ContactService.delete_contact(db, message_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
