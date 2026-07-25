import logging
from uuid import UUID
from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks

from app.models.contact_request import ContactRequest, ContactStatus
from app.schemas.contact import ContactCreate
from app.utils.email import EmailService
from app.utils.broadcaster import broadcaster

logger = logging.getLogger(__name__)

class ContactService:
    """
    Handles all business logic for Contact Requests.
    Manages database transactions (commit/rollback/refresh) explicitly.
    """
    
    @staticmethod
    async def create_contact(db: AsyncSession, contact_data: ContactCreate, background_tasks: BackgroundTasks = None) -> ContactRequest:
        """
        Transforms validated Pydantic data into an ORM model and saves it.
        """
        # 1. Create the SQLAlchemy Model instance
        db_contact = ContactRequest(
            name=contact_data.name,
            company=contact_data.company,
            email=contact_data.email,
            message=contact_data.message,
            status=ContactStatus.NEW
        )
        
        # 2. Add to the session (pending state)
        db.add(db_contact)
        
        # 3. Handle the transaction
        try:
            await db.commit()           # Flush to Postgres and finalize transaction
            await db.refresh(db_contact) # Reload the object from DB to get the generated 'id' and 'created_at'
            
            # Broadcast real-time SSE event to connected Admin Dashboards
            lead_type = "Discovery Call" if "discovery call" in (contact_data.message or "").lower() else "Contact Form"
            await broadcaster.broadcast("new_lead", {
                "id": str(db_contact.id),
                "name": db_contact.name,
                "company": db_contact.company or "Not specified",
                "email": db_contact.email,
                "message": db_contact.message,
                "status": "New",
                "createdAt": db_contact.created_at.isoformat(),
                "type": lead_type
            })

            # Email Delivery is a Side Effect. 
            if background_tasks:
                background_tasks.add_task(EmailService.send_contact_notification, db_contact)
            else:
                EmailService.send_contact_notification(db_contact)
            
            return db_contact
        except Exception as e:
            await db.rollback()         # Abort transaction if anything fails (e.g. database disconnects)
            logger.error(f"Failed to create contact request: {e}")
            raise # We raise the raw exception here; the Global Exception Handler will catch it later.

    @staticmethod
    async def list_contacts(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ContactStatus] = None,
        search: Optional[str] = None
    ) -> Sequence[ContactRequest]:
        """
        Fetches contact requests with optional filtering, search, and pagination.
        """
        query = select(ContactRequest).order_by(ContactRequest.created_at.desc())
        
        # Apply Status Filter
        if status:
            query = query.where(ContactRequest.status == status)
            
        # Apply Search Filter (ILike is case-insensitive in PostgreSQL)
        if search:
            search_term = f"%{search}%"
            # Using the OR operator (|) inside the where clause
            query = query.where(
                (ContactRequest.name.ilike(search_term)) |
                (ContactRequest.company.ilike(search_term)) |
                (ContactRequest.email.ilike(search_term))
            )
            
        # Apply Pagination
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        # scalars().all() extracts the actual models from the SQLAlchemy Result object
        return result.scalars().all()
        
    @staticmethod
    async def get_contact(db: AsyncSession, contact_id: UUID) -> Optional[ContactRequest]:
        """
        Fetches a single contact request by Primary Key.
        db.get() is the most highly optimized way to fetch by PK in SQLAlchemy 2.0.
        """
        return await db.get(ContactRequest, contact_id)
        
    @staticmethod
    async def update_status(db: AsyncSession, contact_id: UUID, new_status: ContactStatus) -> Optional[ContactRequest]:
        """
        Updates the status of an existing message.
        """
        contact = await db.get(ContactRequest, contact_id)
        if not contact:
            return None
            
        contact.status = new_status
        
        try:
            await db.commit()
            await db.refresh(contact)
            return contact
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update contact {contact_id}: {e}")
            raise
            
    @staticmethod
    async def delete_contact(db: AsyncSession, contact_id: UUID) -> bool:
        """
        Deletes a message from the database.
        Returns True if deleted, False if it didn't exist.
        """
        contact = await db.get(ContactRequest, contact_id)
        if not contact:
            return False
            
        await db.delete(contact)
        try:
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete contact {contact_id}: {e}")
            raise
