from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.admin import Admin
from app.models.meeting_request import MeetingRequestStatus
from app.repositories.meeting_request_repository import MeetingRequestRepository
from app.schemas.meeting_request import MeetingRequestListResponse, MeetingRequestResponse, MeetingRequestUpdate
from app.services.meeting_request_service import MeetingRequestService

router = APIRouter()

def get_meeting_request_service(db: AsyncSession = Depends(get_db)) -> MeetingRequestService:
    repository = MeetingRequestRepository(db)
    return MeetingRequestService(repository)

@router.get("", response_model=MeetingRequestListResponse)
async def list_meeting_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[MeetingRequestStatus] = Query(None, alias="status"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    company_name: Optional[str] = None,
    email: Optional[str] = None,
    service: MeetingRequestService = Depends(get_meeting_request_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    List all meeting requests with pagination and filtering.
    """
    items, total = await service.list_meeting_requests(
        skip=skip,
        limit=limit,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        company_name=company_name,
        business_email=email
    )
    return MeetingRequestListResponse(
        items=items,
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        size=limit
    )

@router.get("/{id}", response_model=MeetingRequestResponse)
async def get_meeting_request(
    id: UUID,
    service: MeetingRequestService = Depends(get_meeting_request_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Get meeting request details by ID.
    """
    return await service.get_meeting_request(id)

@router.patch("/{id}", response_model=MeetingRequestResponse)
async def update_meeting_request_status(
    id: UUID,
    request_in: MeetingRequestUpdate,
    service: MeetingRequestService = Depends(get_meeting_request_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Update meeting request status.
    """
    return await service.update_meeting_request(id, request_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting_request(
    id: UUID,
    service: MeetingRequestService = Depends(get_meeting_request_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    Soft delete a meeting request.
    """
    await service.delete_meeting_request(id)
