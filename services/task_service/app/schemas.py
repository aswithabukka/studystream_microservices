"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class TaskCreate(BaseModel):
    """Schema for creating task"""
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    task_type: str = Field(default='note', pattern='^(note|link|video|file)$')
    task_metadata: Optional[Dict[str, Any]] = {}


class TaskUpdate(BaseModel):
    """Schema for updating task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    task_type: Optional[str] = Field(None, pattern='^(note|link|video|file)$')
    task_metadata: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern='^(active|completed|archived)$')


class TaskResponse(BaseModel):
    """Schema for task response"""
    id: str
    user_id: str
    title: str
    content: Optional[str] = None
    task_type: str
    task_metadata: Dict[str, Any] = {}
    status: str
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
