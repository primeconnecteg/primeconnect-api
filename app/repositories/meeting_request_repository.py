from datetime import date
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting_request import MeetingRequest, MeetingRequestStatus
from app.schemas.meeting_request import MeetingRequestCreate


class MeetingRequestRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request_in: MeetingRequestCreate) -> MeetingRequest:
        db_obj = MeetingRequest(
            full_name=request_in.full_name,
            company_name=request_in.company_name,
            business_email=request_in.business_email,
            meeting_date=request_in.meeting_date,
            comment=request_in.comment,
            status="PENDING"
        )
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def get(self, id: UUID) -> Optional[MeetingRequest]:
        stmt = select(MeetingRequest).where(MeetingRequest.id == id, MeetingRequest.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        *,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        company_name: Optional[str] = None,
        business_email: Optional[str] = None
    ) -> Tuple[List[MeetingRequest], int]:
        
        # Base query for count
        count_stmt = select(func.count()).select_from(MeetingRequest).where(MeetingRequest.is_deleted == False)
        
        # Base query for items
        stmt = select(MeetingRequest).where(MeetingRequest.is_deleted == False)

        if status:
            stmt = stmt.where(MeetingRequest.status == status)
            count_stmt = count_stmt.where(MeetingRequest.status == status)
            
        if date_from:
            stmt = stmt.where(MeetingRequest.meeting_date >= date_from)
            count_stmt = count_stmt.where(MeetingRequest.meeting_date >= date_from)
            
        if date_to:
            stmt = stmt.where(MeetingRequest.meeting_date <= date_to)
            count_stmt = count_stmt.where(MeetingRequest.meeting_date <= date_to)
            
        if company_name:
            stmt = stmt.where(MeetingRequest.company_name.ilike(f"%{company_name}%"))
            count_stmt = count_stmt.where(MeetingRequest.company_name.ilike(f"%{company_name}%"))
            
        if business_email:
            stmt = stmt.where(MeetingRequest.business_email.ilike(f"%{business_email}%"))
            count_stmt = count_stmt.where(MeetingRequest.business_email.ilike(f"%{business_email}%"))

        # Execute count
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Execute fetch with pagination
        stmt = stmt.order_by(MeetingRequest.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(self, db_obj: MeetingRequest, **kwargs) -> MeetingRequest:
        for field, value in kwargs.items():
            setattr(db_obj, field, value)
        
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def soft_delete(self, id: UUID) -> bool:
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        db_obj.is_deleted = True
        self.session.add(db_obj)
        await self.session.commit()
        return True

    async def exists_pending(self, email: str, meeting_date: date) -> bool:
        stmt = select(MeetingRequest).where(
            func.lower(MeetingRequest.business_email) == email.lower().strip(),
            MeetingRequest.meeting_date == meeting_date,
            MeetingRequest.status == "PENDING",
            MeetingRequest.is_deleted == False
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None
