
from pydantic import BaseModel

from app.db.models import User as DbUser

class User(BaseModel):
    @classmethod
    def from_instance(cls, user: DbUser) -> User:
        """Copy ctor to streamline conversion from sensitive DB instance to safe API version."""
        return cls(username=user.username, disabled=user.disabled)
    
    username: str
    disabled: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str