from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from fastapi import BackgroundTasks, HTTPException, status

from app.models.meeting_request import MeetingRequest, MeetingRequestStatus
from app.repositories.meeting_request_repository import MeetingRequestRepository
from app.schemas.meeting_request import MeetingRequestCreate, MeetingRequestUpdate
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

class MeetingRequestService:
    def __init__(self, repository: MeetingRequestRepository):
        self.repository = repository

    async def create_meeting_request(
        self,
        request_in: MeetingRequestCreate,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> MeetingRequest:
        # Check for duplicates
        is_duplicate = await self.repository.exists_pending(
            email=request_in.business_email,
            meeting_date=request_in.meeting_date
        )
        if is_duplicate:
            logger.warning(f"Duplicate meeting request attempt: {request_in.business_email} on {request_in.meeting_date}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending request already exists for this date."
            )
        
        # Create record
        meeting_request = await self.repository.create(request_in)
        logger.info(f"New meeting request created: {meeting_request.id}")

        # Schedule emails via BackgroundTasks
        if background_tasks is not None:
            logger.info(f"Scheduling meeting request emails via BackgroundTasks for ID {meeting_request.id}")
            background_tasks.add_task(EmailService.send_admin_meeting_notification, meeting_request)
            background_tasks.add_task(EmailService.send_user_meeting_confirmation, meeting_request)
        else:
            logger.info(f"Executing meeting request emails inline for ID {meeting_request.id}")
            EmailService.send_admin_meeting_notification(meeting_request)
            EmailService.send_user_meeting_confirmation(meeting_request)
            
        return meeting_request

    async def get_meeting_request(self, request_id: UUID) -> MeetingRequest:
        meeting_request = await self.repository.get(request_id)
        if not meeting_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting request not found."
            )
        return meeting_request

    async def list_meeting_requests(
        self,
        skip: int = 0,
        limit: int = 10,
        status: Optional[MeetingRequestStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        company_name: Optional[str] = None,
        business_email: Optional[str] = None
    ) -> Tuple[List[MeetingRequest], int]:
        return await self.repository.list(
            skip=skip,
            limit=limit,
            status=status,
            date_from=date_from,
            date_to=date_to,
            company_name=company_name,
            business_email=business_email
        )

    async def update_meeting_request(self, request_id: UUID, request_in: MeetingRequestUpdate) -> MeetingRequest:
        meeting_request = await self.get_meeting_request(request_id)
        
        updated_request = await self.repository.update(
            meeting_request,
            status=request_in.status
        )
        logger.info(f"Meeting request {request_id} status updated to {request_in.status}")
        return updated_request

    async def delete_meeting_request(self, request_id: UUID) -> bool:
        # Check if exists
        await self.get_meeting_request(request_id)
        
        success = await self.repository.soft_delete(request_id)
        if success:
            logger.info(f"Meeting request {request_id} soft deleted.")
        return success

    async def check_pending_exists(self, email: str, meeting_date: date) -> bool:
        return await self.repository.exists_pending(email, meeting_date)
