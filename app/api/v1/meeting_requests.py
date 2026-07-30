import logging
from datetime import date
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.meeting_request_repository import MeetingRequestRepository
from app.schemas.meeting_request import MeetingRequestCreate
from app.services.meeting_request_service import MeetingRequestService
from app.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


def get_meeting_request_service(db: AsyncSession = Depends(get_db)) -> MeetingRequestService:
    repository = MeetingRequestRepository(db)
    return MeetingRequestService(repository)


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_meeting_request(
    request: Request,
    background_tasks: BackgroundTasks,
    service: MeetingRequestService = Depends(get_meeting_request_service)
):
    """
    Create a new discovery call request.
    Captures raw body, logs validation steps, and returns explicit HTTP 400 error details.
    """
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"[API] Incoming POST /api/v1/meeting-requests from IP {client_ip}")

    # 1. Read and Log Raw HTTP Request Body
    raw_body = await request.body()
    raw_text = raw_body.decode("utf-8", errors="replace")
    logger.info(f"[API] Raw HTTP Request Body: {raw_text}")

    # 2. Parse JSON Payload
    try:
        import json
        json_data = json.loads(raw_text) if raw_text else {}
        logger.info(f"[API] Parsed JSON Data: {json_data}")
    except Exception as exc:
        error_msg = f"Invalid JSON payload: {exc}"
        logger.error(f"[API] HTTP 400 Bad Request - JSON Parse Error: {error_msg}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": error_msg,
                "error": error_msg,
                "errors": {"server": error_msg}
            }
        )

    # 3. Pydantic Model Validation with Explicit Step Logging
    try:
        meeting_request_in = MeetingRequestCreate.model_validate(json_data)
        logger.info(f"[API] Pydantic Validation Passed: {meeting_request_in.model_dump()}")
    except ValidationError as val_err:
        logger.error(f"[API] HTTP 400 Bad Request - Pydantic Validation Failed for payload: {json_data}")
        logger.error(f"[API] Exact Pydantic Validation Failure:\n{val_err}")

        field_errors = {}
        first_error_msg = "Invalid payload"

        for err in val_err.errors():
            msg = err.get("msg", "Invalid value")
            if msg.startswith("Value error, "):
                msg = msg.replace("Value error, ", "", 1)
            loc = err.get("loc", [])
            field = str(loc[-1]) if loc else "general"

            field_errors[field] = msg
            if first_error_msg == "Invalid payload":
                first_error_msg = msg

        logger.error(f"[API] HTTP 400 Bad Request - Formatted Field Errors: {field_errors}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": first_error_msg,
                "error": first_error_msg,
                "errors": field_errors,
                "raw_payload": json_data
            }
        )

    # 4. Service Layer Execution (Duplicate Check & DB Save)
    try:
        created_request = await service.create_meeting_request(meeting_request_in, background_tasks=background_tasks)
        logger.info(f"[API] POST /api/v1/meeting-requests completed successfully for ID {created_request.id}")
        return {
            "message": "Discovery call request submitted successfully.",
            "id": str(created_request.id),
            "status": created_request.status.value if hasattr(created_request.status, 'value') else str(created_request.status)
        }
    except HTTPException as http_exc:
        logger.error(f"[API] HTTP {http_exc.status_code} Error in MeetingRequestService: {http_exc.detail}")
        return JSONResponse(
            status_code=http_exc.status_code,
            content={
                "detail": str(http_exc.detail),
                "error": str(http_exc.detail),
                "errors": {"server": str(http_exc.detail)}
            }
        )
    except Exception as exc:
        logger.error(f"[API] Unhandled Exception in MeetingRequestService: {exc}")
        logger.exception(exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": f"Server processing error: {str(exc)}",
                "error": f"Server processing error: {str(exc)}",
                "errors": {"server": str(exc)}
            }
        )


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
