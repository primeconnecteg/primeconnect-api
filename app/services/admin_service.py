from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.contact_request import ContactRequest, ContactStatus

class AdminService:
    """
    Handles dashboard-specific business logic for the Administrator.
    """
    
    @staticmethod
    async def get_dashboard_stats(db: AsyncSession) -> dict:
        """
        Calculates total, new, read, and replied message counts.
        
        Efficiency Explanation:
        Instead of running `SELECT *` and doing a Python `len(messages)` (which would 
        crash the server if there are 1,000,000 messages), we use the database engine
        to do the heavy lifting via a GROUP BY aggregate query.
        
        SQL Generated:
        SELECT status, COUNT(*) FROM contact_requests GROUP BY status;
        """
        
        # Build the SQLAlchemy 2.0 query
        query = (
            select(ContactRequest.status, func.count(ContactRequest.id))
            .group_by(ContactRequest.status)
        )
        
        result = await db.execute(query)
        
        # result.all() returns a list of tuples: [('NEW', 50), ('READ', 20), ('REPLIED', 10)]
        # We parse this into a Python dictionary.
        counts_by_status = {status: count for status, count in result.all()}
        
        # Total is just the sum of all groups
        total = sum(counts_by_status.values())
        
        return {
            "total_messages": total,
            "new_messages": counts_by_status.get(ContactStatus.NEW, 0),
            "read_messages": counts_by_status.get(ContactStatus.READ, 0),
            "replied_messages": counts_by_status.get(ContactStatus.REPLIED, 0)
        }
