from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.admin import Admin
from app.schemas.auth import LoginRequest
from app.core.security import verify_password, create_access_token

class AuthenticationService:
    """
    Handles all business logic related to Admin authentication.
    Notice that this service does NOT raise HTTPExceptions. It simply returns None
    if authentication fails. It is the Route's job to translate None into an HTTP 401.
    """
    
    @staticmethod
    async def authenticate_admin(db: AsyncSession, login_data: LoginRequest) -> Optional[Admin]:
        """
        Verifies the admin's username and password against the database.
        
        - Uses `select()` to build the query.
        - Uses `where()` to filter by username.
        - Uses `scalar_one_or_none()` which returns exactly one result, or None if not found.
        """
        # Query the database for an admin with the matching username
        query = select(Admin).where(Admin.username == login_data.username)
        result = await db.execute(query)
        admin = result.scalar_one_or_none()
        
        if admin is None:
            # Username does not exist
            return None
            
        # Verify the provided plain password against the stored Argon2 hash
        if not verify_password(login_data.password, admin.password_hash):
            # Password does not match
            return None
            
        return admin

    @staticmethod
    def create_token_for_admin(admin: Admin) -> str:
        """
        Generates a JWT for the authenticated admin.
        We strictly pass the admin.id (UUID) as a string to the 'sub' claim.
        """
        return create_access_token(subject=str(admin.id))
