import logging
import jwt

from datetime import datetime, timezone, timedelta
from typing import Any

from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import User as DbUser
from app.schemas.auth import Token

class AuthService:
    """Service layer for managing auth and user-related operations."""
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        self.password_hash = PasswordHash.recommended()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a hashed password."""
        return self.password_hash.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a plaintext password."""
        return self.password_hash.hash(password)
    
    def create_user(self, username: str, password: str) -> DbUser:
        """Create a new user with the provided username and password."""
        hashed_password = self.hash_password(password)
        new_user = DbUser(username=username, password_hash=hashed_password, disabled=False)
        self.db_session.add(new_user)
        self.db_session.commit()
        self.db_session.refresh(new_user)
        return new_user
    
    def get_user(self, username: str) -> DbUser | None:
        """Retrieve a user by their username."""
        self.logger.debug(f"Retrieving user with username: {username}")
        
        user = self.db_session.query(DbUser).filter_by(username=username).first()
        if user is None:
            self.logger.warning(f"User with username: {username} not found.")
            return None
        
        return user
    
    def get_users(self) -> list[DbUser]:
        """Retrieve all users."""
        self.logger.debug("Retrieving all users from the database.")
        users = self.db_session.query(DbUser).all()
        self.logger.info(f"Retrieved {len(users)} users from the database.")
        return users
    
    def delete_user(self, username: str) -> bool:
        """Delete a user by their username."""
        user = self.get_user(username)
        if user is None:
            self.logger.warning(f"Cannot delete user with username: {username} - not found.")
            return False
        
        self.db_session.delete(user)
        self.db_session.commit()
        self.logger.info(f"Deleted user with username: {username}")
        return True
    
    def authenticate_user(self, username: str, password: str) -> DbUser | None:
        """Validate provided username & password against DB usernames and hashed passwords."""
        user = self.get_user(username)
        if not user or not self.verify_password(password, user.password_hash):
            user = None        
        return user
    
    def create_access_token(self, username: str, expires_min: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> Token:
        """Build and return a JWT toekn for user to expire in given minutes."""
        to_encode: dict[str, Any] = {
            "sub": username,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_min)
        }
        jwt_tok = jwt.encode(payload=to_encode, key=settings.user_secret_key, algorithm=self.ALGORITHM) # type: ignore
        return Token(access_token=jwt_tok, token_type="bearer")