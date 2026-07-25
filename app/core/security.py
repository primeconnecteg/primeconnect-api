import jwt
from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

# Initialize the Argon2 Password Hasher.
# We are using the native argon2-cffi library's PasswordHasher.
ph = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using the Argon2 algorithm.
    
    Argon2 generates a unique cryptographic salt automatically and embeds it 
    into the returned hash string, making it safe to store in the database.
    """
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plaintext password against a stored Argon2 hash.
    Returns True if they match, False otherwise.
    """
    try:
        # ph.verify raises a VerifyMismatchError if the passwords do not match.
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(subject: str) -> str:
    """
    Generates a JSON Web Token (JWT) for authentication.
    
    Args:
        subject: The unique identifier of the user (e.g., admin username or UUID).
        
    Returns:
        The encoded JWT string.
    """
    # Use timezone-aware UTC datetime for cryptographic timestamps
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Standard JWT claims
    to_encode = {
        "sub": str(subject),  # Subject: Who this token is for
        "exp": expire,        # Expiration: When this token becomes invalid
        "iat": now,           # Issued At: When this token was created
    }
    
    # Cryptographically sign the payload using our secret key
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodes and strictly validates a JWT token.
    
    Args:
        token: The JWT string provided by the client.
        
    Returns:
        A dictionary containing the decoded claims.
        
    Raises:
        ValueError: If the token is expired, malformed, or has an invalid signature.
    """
    try:
        # jwt.decode automatically verifies the signature and the 'exp' claim.
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        # The token is structurally valid but the current time is past the 'exp' time.
        raise ValueError("Token has expired")
        
    except jwt.InvalidSignatureError:
        # The token payload or header was tampered with, so the signature doesn't match.
        raise ValueError("Invalid token signature")
        
    except jwt.DecodeError:
        # The token is malformed (not a valid Base64 JSON format).
        raise ValueError("Malformed token")
        
    except jwt.InvalidTokenError:
        # Catch-all for any other JWT-related error (e.g. missing claims if we required them).
        raise ValueError("Invalid token")
