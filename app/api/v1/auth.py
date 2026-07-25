from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.authentication_service import AuthenticationService

router = APIRouter()

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Administrator Login",
    description="Authenticates the administrator and issues a JWT access token."
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate an admin and return a token.
    
    Args:
        login_data: The JSON payload containing 'username' and 'password'.
        db: The injected database session.
    """
    # 1. Call the Service Layer
    admin = await AuthenticationService.authenticate_admin(db, login_data)
    
    # 2. Handle Business Logic Failure
    if not admin:
        # We raise a 401 Unauthorized if the service returns None
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Generate the Token
    access_token = AuthenticationService.create_token_for_admin(admin)
    
    # 4. Return the standard OAuth2 token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 # Convert minutes to seconds
    )
