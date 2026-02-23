import logging
import jwt

from collections.abc import Generator
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any

from app.service.simulation_service import SimulationService
from app.service.telemetry_service import TelemetryService
from app.service.auth_service import AuthService

from app.config import settings
from app.db.session import get_db_session
from app.queue.session import RedisSession
from app.schemas.auth import User, TokenData

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"

# FastAPI built-in OAuth2 support for use with authenticated endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db() -> Generator[Session, None, None]:
    db: Session = get_db_session()()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> Generator[Redis, None, None]:
    # for redis we keep a pool of persistent connections across multiple transactions
    yield RedisSession

def get_simulation_service(db: Annotated[Session, Depends(get_db)], redis: Annotated[Redis, Depends(get_redis)]) -> SimulationService:
    return SimulationService(db, redis)

def get_telemetry_service(db: Annotated[Session, Depends(get_db)]) -> TelemetryService:
    return TelemetryService(db)

def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)

def get_health(db: Annotated[Session, Depends(get_db)], redis: Annotated[Redis, Depends(get_redis)]) -> bool:
    """Simple dependency to check if we can connect to the database and Redis."""
    ret = True
    
    # NOTE: We intentionally test all dependencies rather than short-circuit to provide
    # useful logs. In production we might want to consider prioritizing resp speed 
    # over observability and short-circuiting on first failure.
    
    try:    # Try a simple query to check DB connectivity
        db.execute(text("SELECT 1"))
    except Exception as e:
        # Log the exception for debugging purposes
        logger.warning(f"Not healthy yet. Database connection error: {e}")
        ret = False
    
    try:    # Try a simple command to check Redis connectivity
        redis.ping() # type: ignore - no control over redis library
    except Exception as e:
        # Log the exception for debugging purposes
        logger.warning(f"Not healthy yet. Redis connection error: {e}")
        ret = False
    
    return ret

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> User:
    """Using the provided token, look for matching user and return if found. Otherwise raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.user_secret_key, algorithms=[JWT_ALGORITHM]) # type: ignore
        username = payload.get("sub")
        if not username:
            raise credentials_exception
        tok_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    user = auth_service.get_user(tok_data.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated",
                            headers={"WWW-Authenticate": "Bearer"})
    return User.from_instance(user)

def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Using provided token, look for matching user and check if active. If so return user, otherwise raise 400."""
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Inactive user")
    return current_user
