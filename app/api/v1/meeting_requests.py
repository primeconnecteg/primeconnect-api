from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.meeting_request_repository import MeetingRequestRepository
from app.schemas.meeting_request import MeetingRequestCreate
from app.services.meeting_request_service import MeetingRequestService

from app.core.limiter import limiter

router = APIRouter()

def get_meeting_request_service(db: AsyncSession = Depends(get_db)) -> MeetingRequestService:
    repository = MeetingRequestRepository(db)
    return MeetingRequestService(repository)

@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_meeting_request(
    request: Request,
    meeting_request_in: MeetingRequestCreate,
    background_tasks: BackgroundTasks,
    service: MeetingRequestService = Depends(get_meeting_request_service)
):
    """
    Create a new discovery call request.
    """
    await service.create_meeting_request(meeting_request_in, background_tasks=background_tasks)
    return {"message": "Discovery call request submitted successfully."}

@router.get("/check")
async def check_pending_request(
    email: str = Query(..., description="Business email to check"),
    meeting_date: date = Query(..., alias="date", description="Meeting date to check"),
    service: MeetingRequestService = Depends(get_meeting_request_service)
):
    """
    Check if a pending meeting request already exists for the given email and date.
    """
    exists = await service.check_pending_exists(email, meeting_date)
    return {"exists": exists}
