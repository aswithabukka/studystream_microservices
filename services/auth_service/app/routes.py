"""
API routes for Auth Service
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.database import get_db
from app.models import User
from app.schemas import (
    UserRegister, UserLogin, UserResponse, TokenResponse,
    TokenVerifyRequest, TokenVerifyResponse, MessageResponse
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    decode_access_token, blacklist_token, is_token_blacklisted
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate JWT token
    token, exp = create_access_token(str(new_user.id), new_user.email)
    
    logger.info(f"User registered: {new_user.email}")
    
    return TokenResponse(
        access_token=token,
        expires_in=exp,
        user_id=str(new_user.id),
        email=new_user.email
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return JWT token"""
    
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is disabled"
        )
    
    # Generate JWT token
    token, exp = create_access_token(str(user.id), user.email)
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=token,
        expires_in=exp,
        user_id=str(user.id),
        email=user.email
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked"
        )
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token(verify_request: TokenVerifyRequest):
    """Verify JWT token (for other services)"""
    
    token = verify_request.token
    
    # Check if token is blacklisted
    if await is_token_blacklisted(token):
        return TokenVerifyResponse(
            valid=False,
            user_id=None,
            email=None
        )
    
    # Decode token
    payload = decode_access_token(token)
    
    if not payload:
        return TokenVerifyResponse(
            valid=False,
            user_id=None,
            email=None
        )
    
    return TokenVerifyResponse(
        valid=True,
        user_id=payload.get("sub"),
        email=payload.get("email"),
        exp=payload.get("exp")
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user (blacklist token)"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Decode token to get expiration
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    # Blacklist token
    await blacklist_token(token, payload.get("exp"))
    
    logger.info(f"User logged out: {payload.get('email')}")
    
    return MessageResponse(
        message="Successfully logged out",
        success=True
    )
