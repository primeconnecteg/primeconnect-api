import asyncio
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.contact import ContactCreate, ContactResponse
from app.services.contact_service import ContactService
from app.utils.broadcaster import broadcaster

# We create an APIRouter specifically for the Contact endpoints.
router = APIRouter()


@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Contact Request",
    description="Allows public visitors to submit a contact request. The request is saved securely in the database and an email notification is automatically dispatched.",
)
async def submit_contact_request(
    contact_in: ContactCreate,
    db: AsyncSession = Depends(get_db)
) -> ContactResponse:
    contact_out = await ContactService.create_contact(db, contact_in)
    return contact_out


@router.get(
    "/contact/stream",
    summary="Real-time Lead Stream (SSE)",
    description="Provides a Server-Sent Events stream emitting real-time contact form and discovery call notifications."
)
async def stream_leads():
    async def event_generator():
        queue = await broadcaster.subscribe()
        try:
            yield "event: connected\ndata: {\"status\":\"connected\"}\n\n"
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=20.0)
                    yield message
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except (asyncio.CancelledError, Exception):
            pass
        finally:
            broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
