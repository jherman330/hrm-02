"""
Database package for the task management system.
Provides database connection management and task repository.
"""

from database.database import DatabaseManager, get_db, init_db, close_db
from database.task_repository import TaskRepository

__all__ = [
    "DatabaseManager",
    "get_db",
    "init_db",
    "close_db",
    "TaskRepository",
]

