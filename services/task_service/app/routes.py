"""
API routes for Task Service
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import logging

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, MessageResponse
from app.dependencies import get_current_user
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


async def notify_task_created(user_id: str, task_id: str, task_title: str):
    """Send notification in background (non-blocking)"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.notification_service_url}/notifications/send",
                json={
                    "user_id": user_id,
                    "notification_type": "task_created",
                    "title": "Task Created",
                    "content": f"Your task '{task_title}' has been created successfully."
                },
                timeout=10.0
            )
            logger.info(f"Notification sent for task {task_id}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new task"""
    
    # Create task
    new_task = Task(
        user_id=current_user["user_id"],
        title=task.title,
        content=task.content,
        task_type=task.task_type,
        task_metadata=task.task_metadata or {}
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Schedule background notification (non-blocking)
    background_tasks.add_task(
        notify_task_created,
        user_id=current_user["user_id"],
        task_id=str(new_task.id),
        task_title=new_task.title
    )
    
    logger.info(f"Task created: {new_task.id}")
    
    return new_task.to_dict()


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    status: str = None,
    task_type: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's tasks with filters"""
    
    query = select(Task).where(Task.user_id == current_user["user_id"])
    
    if status:
        query = query.where(Task.status == status)
    
    if task_type:
        query = query.where(Task.task_type == task_type)
    
    query = query.limit(limit).offset(offset).order_by(Task.created_at.desc())
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return [task.to_dict() for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    # Check ownership
    if str(task.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this task"
        )
    
    return task.to_dict()


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update task (owner only)"""
    
    # Get task
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    # Check ownership
    if str(task.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this task"
        )
    
    # Update fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    logger.info(f"Task updated: {task.id}")
    
    return task.to_dict()


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete task (owner only)"""
    
    # Get task
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    # Check ownership
    if str(task.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this task"
        )
    
    # Delete task
    await db.delete(task)
    await db.commit()
    
    logger.info(f"Task deleted: {task_id}")
    
    return MessageResponse(
        message="Task deleted successfully",
        success=True
    )
