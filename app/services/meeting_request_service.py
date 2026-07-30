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
        logger.info(f"[MeetingRequest] Processing creation request for email '{request_in.business_email}' on date '{request_in.meeting_date}'")
        logger.info(f"[MeetingRequest] Validation passed: full_name='{request_in.full_name}', company_name='{request_in.company_name}'")

        # 1. Duplicate Request Check
        logger.info(f"[MeetingRequest] Executing duplicate check for email '{request_in.business_email}' on date '{request_in.meeting_date}'...")
        is_duplicate = await self.repository.exists_pending(
            email=request_in.business_email,
            meeting_date=request_in.meeting_date
        )
        if is_duplicate:
            error_msg = "A pending discovery call request already exists for this email and date."
            logger.warning(f"[MeetingRequest] Duplicate check failed (HTTP 409 Conflict): {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg
            )
        logger.info("[MeetingRequest] Duplicate check passed. No pending request exists.")

        # 2. Database Insertion
        logger.info("[MeetingRequest] Saving meeting request to database...")
        try:
            meeting_request = await self.repository.create(request_in)
            logger.info(f"[MeetingRequest] Database save successful. Created record ID '{meeting_request.id}'")
        except Exception as e:
            logger.error(f"[MeetingRequest] Database insertion failed: {e}")
            logger.exception(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database insertion failed: {str(e)}"
            )

        # 3. Schedule Email Notifications
        logger.info(f"[MeetingRequest] Scheduling email notifications for record ID '{meeting_request.id}'...")
        if background_tasks is not None:
            logger.info("[MeetingRequest] Scheduling admin notification email via BackgroundTasks...")
            background_tasks.add_task(EmailService.send_admin_meeting_notification, meeting_request)
            logger.info("[MeetingRequest] Scheduling user confirmation email via BackgroundTasks...")
            background_tasks.add_task(EmailService.send_user_meeting_confirmation, meeting_request)
        else:
            logger.info("[MeetingRequest] Executing admin notification email inline...")
            EmailService.send_admin_meeting_notification(meeting_request)
            logger.info("[MeetingRequest] Executing user confirmation email inline...")
            EmailService.send_user_meeting_confirmation(meeting_request)
            
        logger.info(f"[MeetingRequest] Meeting request processing completed successfully for record ID '{meeting_request.id}'")
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
