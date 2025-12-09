"""
Task data models for the task management system.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Enumeration of possible task statuses."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    CLOSED = "Closed"
    DELETED = "Deleted"


class TaskBase(BaseModel):
    """Base model for task data."""
    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    due_date: Optional[datetime] = Field(None, description="Optional due date for the task")
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="Current task status")
    comments: Optional[str] = Field(None, max_length=5000, description="Optional task comments")


class TaskCreate(TaskBase):
    """Model for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Model for updating an existing task. All fields are optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    comments: Optional[str] = Field(None, max_length=5000)


class Task(TaskBase):
    """Complete task model with all fields including timestamps."""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique task identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    class Config:
        from_attributes = True
    
    def to_db_dict(self) -> dict:
        """Convert task to dictionary for database storage."""
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "comments": self.comments,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def to_response_dict(self) -> dict:
        """Convert task to dictionary for API response."""
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "comments": self.comments,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

