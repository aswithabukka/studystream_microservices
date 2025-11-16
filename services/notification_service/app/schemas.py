"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    """Schema for creating notification"""
    user_id: str
    notification_type: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: str
    user_id: str
    notification_type: str
    title: str
    content: Optional[str] = None
    is_read: bool
    sent_at: datetime
    
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
