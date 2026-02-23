import logging

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr

from app.api.deps import get_auth_service, get_current_active_user
from app.service.auth_service import AuthService
from app.schemas.auth import Token, User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/token", status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> Token:
    """Endpoint to authenticate user and return JWT access token."""
    logger.debug(f"Auth request to authenticate user: {form_data.username}")
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Authentication failed for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"User {form_data.username} authenticated successfully, generating access token.")
    
    # Return JWT token good for 30 minutes
    return auth_service.create_access_token(user.username)

@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(username: str, password: SecretStr, auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> User:
    """Endpoint to create a new user with provided username and password."""    
    existing_user = auth_service.get_user(username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    
    new_user = auth_service.create_user(username=username, password=password.get_secret_value())
    return User.from_instance(new_user)

@router.get("/users", status_code=status.HTTP_200_OK)
async def list_users(auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> list[User]:
    """Endpoint to list all users."""
    users = auth_service.get_users()
    return [User.from_instance(user) for user in users]

@router.get("/users/me", status_code=status.HTTP_200_OK)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    """Endpoint to retrieve current authenticated user's information."""
    return current_user

@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(username: str, auth_service: Annotated[AuthService, Depends(get_auth_service)]) -> None:
    """Endpoint to delete a user by their username."""
    success = auth_service.delete_user(username)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")