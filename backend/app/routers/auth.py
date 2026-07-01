import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Role
from app.schemas import (
    UserCreate, UserResponse, TokenResponse,
    TokenRefreshRequest, TokenRefreshResponse
)
from app.auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token
)

logger = logging.getLogger("app.routers.auth")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    logger.info(f"Registering user: {user_in.username}")
    
    # Check if username exists
    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        logger.warning(f"Registration failed: Username '{user_in.username}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email exists
    existing_email = db.query(User).filter(User.email == user_in.email).first()
    if existing_email:
        logger.warning(f"Registration failed: Email '{user_in.email}' already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Verify role exists
    role = db.query(Role).filter(Role.id == user_in.role_id).first()
    if not role:
        logger.warning(f"Registration failed: Role ID {user_in.role_id} does not exist")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specified Role ID does not exist"
        )

    # Create new user
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pwd,
        role_id=user_in.role_id,
        is_active=True
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User '{user_in.username}' successfully registered with ID {new_user.id}")
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving user to database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user credentials and return access + refresh tokens."""
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid credentials for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        logger.warning(f"Login failed: User '{form_data.username}' is inactive")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Generate tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    logger.info(f"User '{user.username}' successfully logged in")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh(refresh_in: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Renew access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_in.refresh_token, expected_type="refresh")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token payload"
            )
    except HTTPException as e:
        logger.warning(f"Refresh failed: {e.detail}")
        raise e

    # Retrieve user
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.warning(f"Refresh failed: User '{username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
        
    if not user.is_active:
        logger.warning(f"Refresh failed: User '{username}' is inactive")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
        
    # Generate new access token
    new_access_token = create_access_token(data={"sub": user.username})
    logger.info(f"Successfully refreshed access token for user: {user.username}")
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
