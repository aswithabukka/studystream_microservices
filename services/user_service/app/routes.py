"""
API routes for User Service
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis
import json
import logging

from app.database import get_db
from app.models import UserProfile
from app.schemas import UserProfileCreate, UserProfileUpdate, UserProfileResponse, MessageResponse
from app.dependencies import get_current_user
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client for caching
redis_client = None


async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


@router.post("/users", response_model=UserProfileResponse, status_code=201)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create user profile"""
    
    # Check if profile already exists
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == profile_data.user_id)
    )
    existing_profile = result.scalar_one_or_none()
    
    if existing_profile:
        raise HTTPException(
            status_code=400,
            detail="Profile already exists for this user"
        )
    
    # Create new profile
    new_profile = UserProfile(
        user_id=profile_data.user_id,
        bio=profile_data.bio,
        avatar_url=profile_data.avatar_url,
        preferences=profile_data.preferences or {}
    )
    
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    
    logger.info(f"Profile created for user: {new_profile.user_id}")
    
    return new_profile.to_dict()


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile (with caching)"""
    
    # Try cache first
    redis_conn = await get_redis()
    cache_key = f"user:profile:{user_id}"
    
    try:
        cached = await redis_conn.get(cache_key)
        if cached:
            logger.info(f"Cache hit for user profile: {user_id}")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis error: {e}")
    
    # Cache miss - query database
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    profile_dict = profile.to_dict()
    
    # Store in cache with TTL
    try:
        await redis_conn.setex(
            cache_key,
            settings.cache_ttl_seconds,
            json.dumps(profile_dict)
        )
        logger.info(f"Cached user profile: {user_id}")
    except Exception as e:
        logger.warning(f"Failed to cache profile: {e}")
    
    return profile_dict


@router.patch("/users/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    updates: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile (owner only)"""
    
    # Check ownership
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Can only update own profile"
        )
    
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    await db.commit()
    await db.refresh(profile)
    
    # Invalidate cache
    redis_conn = await get_redis()
    try:
        await redis_conn.delete(f"user:profile:{user_id}")
        logger.info(f"Cache invalidated for user: {user_id}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
    
    logger.info(f"Profile updated for user: {user_id}")
    
    return profile.to_dict()


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user profile (owner only)"""
    
    # Check ownership
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Can only delete own profile"
        )
    
    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    # Delete profile
    await db.delete(profile)
    await db.commit()
    
    # Invalidate cache
    redis_conn = await get_redis()
    try:
        await redis_conn.delete(f"user:profile:{user_id}")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache: {e}")
    
    logger.info(f"Profile deleted for user: {user_id}")
    
    return MessageResponse(
        message="Profile deleted successfully",
        success=True
    )
