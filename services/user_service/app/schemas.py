"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class UserProfileCreate(BaseModel):
    """Schema for creating user profile"""
    user_id: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = {}


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile"""
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=512)
    preferences: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile response"""
    id: str
    user_id: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message responses"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: Optional[str] = None
    success: bool = False
