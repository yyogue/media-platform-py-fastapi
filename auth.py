# Import datetime class to work with dates and times
from datetime import (
    datetime,
    timedelta,  # Used to add/subtract time periods (e.g., add 30 minutes)
)
# Import JWT utilities for creating and validating JSON Web Tokens
from jose import JWTError, jwt  # type: ignore
# Import password hashing context for secure password storage
from passlib.context import CryptContext  # type: ignore
# Import FastAPI dependencies and utilities
from fastapi import (  # type: ignore
    Depends,  # Dependency injection system
    HTTPException,  # Exception class for HTTP errors
    status,  # HTTP status codes (200, 401, etc.)
)
# Import security utilities for handling Bearer token authentication
from fastapi.security import (  # type: ignore
    HTTPBearer,  # Handles Bearer token extraction from Authorization header
    HTTPAuthorizationCredentials,  # Type for authorization credentials
)
# Import SQLAlchemy Session for database operations
from sqlalchemy.orm import Session  # type: ignore
# Import application configuration settings
from config import get_settings
# Import database session dependency
from database import get_db
# Import database models (User model, etc.)
import models


# Get application settings (SECRET_KEY, token expiry time, etc.)
settings = get_settings()
# Create password context using bcrypt hashing algorithm
# "deprecated='auto'" automatically handles outdated hash formats
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Create HTTPBearer instance for extracting Bearer tokens from requests
security = HTTPBearer


def hash_password(password: str) -> str:
    """Hash a password"""
    # Take plain text password and convert it to a secure hash
    # This hash is what gets stored in the dtbase(never store plain passwords!)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    # Compare a plain text password with a hashed password
    # Returns True if they match, False otherwise
    # Used during login to check if the provided password is correct
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    # Create a copy of the data dictionary to avoid modifying the original
    to_encode = data.copy()
    # Calculate when the token should expire
    # Gets current UTC time and adds the configured number of minutes
    expire = datetime.utcnow() + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # Add the expiration time to the token payload
    # "exp" is a standard JWT claim for expiration
    to_encode.update({"exp": expire})
    # Encode the data into a JWT token string
    # Uses the secret key and algorithm from settings to sign the token
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key,
        algorithm=settings.algorithm
    )
    # Return the token as a string (this is what gets sent to the client)
    return encoded_jwt


def get_current_user(
    # Depends(security) extracts the Bearer token from the Authorization header
    credentials: HTTPAuthorizationCredentials = Depends(security),
    # Depends(get_db) provides a database session for querying
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    # Create an exception to raise if authentication fails
    # 401 status means "Unauthorized"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Extract the actual token string from the credentials object
        token = credentials.credentials
        # Decode and verify the JWT token
        # This checks the signature and extracts the payload data
        payload = jwt.decode(
            token,
            settings.secret_key,  # Must match the key used to create the token
            algorithms=[settings.algorithm]  # Must match the algorithm used
        )
        # Extract the user ID from the token payload
        # "sub" (subject) is a standard JWT claim for the user identifier
        user_id: int = payload.get("sub")
        # If there's no user ID in the token, it's invalid
        if user_id is None:
            raise credentials_exception
    # If JWT decoding fails (invalid token, expired, wrong signature, etc.)
    except JWTError:
        raise credentials_exception
    # Query the database to find the user with this ID
    # .first() returns the first matching user or None if not found
    user = db.query(models.User).filter(models.User.id == user_id).first()
    # If no user found with this ID, the token is invalid
    if user is None:
        raise credentials_exception
    # Return the user object
    # (now available in route handlers that use this dependency)
    return user
