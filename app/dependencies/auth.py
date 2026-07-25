import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.admin import Admin
from app.schemas.auth import TokenPayload

# OAuth2PasswordBearer is a FastAPI utility. 
# It looks at the incoming HTTP request, finds the "Authorization" header,
# verifies it starts with "Bearer ", and extracts the token string.
# 'tokenUrl' tells the Swagger UI docs where to send the username/password to get this token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Admin:
    """
    FastAPI dependency that extracts the JWT, verifies it, 
    and fetches the corresponding Admin from the database.
    """
    
    # We define a reusable HTTP 401 exception.
    # The WWW-Authenticate header is an HTTP standard instructing the client 
    # on how they should authenticate (using a Bearer token).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Step 1: Decode the JWT. (This will raise ValueError if expired or tampered with).
        payload = decode_access_token(token)
        
        # Step 2: Validate the payload structure using Pydantic.
        # This guarantees 'sub' and 'exp' are present in the dictionary.
        token_data = TokenPayload(**payload)
        
        # Step 3: Parse the 'sub' claim (which we know is a UUID string) back into a Python UUID object.
        admin_id = uuid.UUID(token_data.sub)
        
    except (ValueError, ValidationError):
        # ValueError handles cryptography failures (expired, invalid signature) or invalid UUIDs.
        # ValidationError handles missing claims (e.g., token missing the 'sub' field).
        raise credentials_exception

    # Step 4: Verify the administrator actually exists in the database.
    # `db.get()` is SQLAlchemy 2.0's highly optimized method for Primary Key lookups.
    admin = await db.get(Admin, admin_id)
    
    if admin is None:
        # The token is cryptographically valid, but the user was deleted from the database!
        raise credentials_exception
        
    return admin
