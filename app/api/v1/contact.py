from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.contact import ContactCreate, ContactResponse
from app.services.contact_service import ContactService

# We create an APIRouter specifically for the Contact endpoints.
# This keeps our files organized and prevents a massive 10,000-line main.py file.
router = APIRouter()


# @router.post tells FastAPI this endpoint only accepts HTTP POST requests.
# POST is semantically correct for creating new resources.
# status.HTTP_201_CREATED tells FastAPI to return 201 instead of the default 200.
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
    """
    Submit a new contact request from the website frontend.
    
    Args:
        contact_in: The JSON payload, automatically parsed and strictly validated by Pydantic.
        db: The async database session, automatically injected by FastAPI's dependency injection.
        
    Returns:
        The newly created ContactRequest as a Pydantic ContactResponse.
    """
    # Notice how thin this route is! We do zero database queries here.
    # We do zero email logic here.
    # We pass the fully validated Pydantic object to our Service Layer.
    # Because Vercel Serverless freezes instantly after the response, we MUST
    # send the email synchronously, so we do not pass background_tasks here.
    contact_out = await ContactService.create_contact(db, contact_in)
    
    # FastAPI automatically serializes this SQLAlchemy model into JSON 
    # based on the `response_model=ContactResponse` parameter above.
    return contact_out
