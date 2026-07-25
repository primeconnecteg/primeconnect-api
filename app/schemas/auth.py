from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """
    Schema for the login payload.
    """
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class TokenResponse(BaseModel):
    """
    Schema for returning the JWT to the client upon successful login.
    """
    access_token: str
    token_type: str = "bearer"
    # expires_in helps the frontend know exactly when to force a re-login.
    expires_in: int

class TokenPayload(BaseModel):
    """
    Schema for validating the decoded payload of a JWT.
    Used during authentication middleware to ensure the token structure is correct.
    """
    # 'sub' (Subject) is standard JWT terminology for the user's identifier.
    sub: str
    
    # 'exp' (Expiration Time) is standard JWT terminology for the expiration timestamp.
    exp: int
