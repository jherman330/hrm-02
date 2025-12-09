"""
Task repository implementing the Data Access Object (DAO) pattern.
Provides a clean interface for task-related CRUD operations.
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from database.database import DatabaseManager, DatabaseError

logger = logging.getLogger(__name__)


class TaskNotFoundError(DatabaseError):
    """Raised when a task is not found in the database."""
    pass


class TaskRepository:
    """
    Repository for Task entities providing CRUD operations.
    
    Implements the repository pattern to abstract database interactions
    and provide a clean interface for task management.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the task repository.
        
        Args:
            db_manager: Database manager instance for connections.
        """
        self.db = db_manager
    
    def create(self, task_data: dict) -> dict:
        """
        Create a new task in the database.
        
        Args:
            task_data: Dictionary containing task fields:
                - id: Unique task identifier
                - title: Task title (required)
                - due_date: Optional due date
                - status: Task status (default: 'Open')
                - comments: Optional comments
                - created_at: Creation timestamp
                - updated_at: Last update timestamp
        
        Returns:
            dict: The created task data.
        
        Raises:
            DatabaseError: If task creation fails.
        """
        insert_sql = """
        INSERT INTO tasks (id, title, due_date, status, comments, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, (
                    task_data["id"],
                    task_data["title"],
                    task_data.get("due_date"),
                    task_data.get("status", "Open"),
                    task_data.get("comments"),
                    task_data["created_at"],
                    task_data["updated_at"]
                ))
                conn.commit()
                logger.info(f"Created task: {task_data['id']}")
                return task_data
        except sqlite3.IntegrityError as e:
            logger.error(f"Task with ID {task_data['id']} already exists: {e}")
            raise DatabaseError(f"Task with this ID already exists: {e}")
        except sqlite3.Error as e:
            logger.error(f"Failed to create task: {e}")
            raise DatabaseError(f"Failed to create task: {e}")
    
    def get_by_id(self, task_id: str) -> dict:
        """
        Retrieve a single task by its ID.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            dict: Task data.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If retrieval fails.
        """
        select_sql = "SELECT * FROM tasks WHERE id = ?"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, (task_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
                
                return self._row_to_dict(row)
        except TaskNotFoundError:
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            raise DatabaseError(f"Failed to retrieve task: {e}")
    
    def get_all(self, status_filter: Optional[str] = None) -> List[dict]:
        """
        Retrieve all tasks with optional status filtering.
        
        Args:
            status_filter: Optional status to filter tasks by.
        
        Returns:
            List[dict]: List of task dictionaries.
        
        Raises:
            DatabaseError: If retrieval fails.
        """
        if status_filter:
            select_sql = "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC"
            params = (status_filter,)
        else:
            select_sql = "SELECT * FROM tasks ORDER BY created_at DESC"
            params = ()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, params)
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            raise DatabaseError(f"Failed to retrieve tasks: {e}")
    
    def update(self, task_id: str, update_data: dict) -> dict:
        """
        Update an existing task.
        
        Args:
            task_id: The unique identifier of the task to update.
            update_data: Dictionary of fields to update.
        
        Returns:
            dict: The updated task data.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If update fails.
        """
        # Verify task exists
        self.get_by_id(task_id)
        
        if not update_data:
            return self.get_by_id(task_id)
        
        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Build dynamic UPDATE statement
        set_clauses = [f"{key} = ?" for key in update_data.keys()]
        values = list(update_data.values())
        values.append(task_id)
        
        update_sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(update_sql, values)
                conn.commit()
                
                if cursor.rowcount == 0:
                    raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
                
                logger.info(f"Updated task: {task_id}")
                return self.get_by_id(task_id)
        except TaskNotFoundError:
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise DatabaseError(f"Failed to update task: {e}")
    
    def delete(self, task_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a task from the database.
        
        Args:
            task_id: The unique identifier of the task to delete.
            soft_delete: If True, marks task as 'Deleted' status.
                        If False, permanently removes the record.
        
        Returns:
            bool: True if deletion was successful.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If deletion fails.
        """
        # Verify task exists
        self.get_by_id(task_id)
        
        if soft_delete:
            return self.update(task_id, {"status": "Deleted"}) is not None
        
        delete_sql = "DELETE FROM tasks WHERE id = ?"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (task_id,))
                conn.commit()
                
                if cursor.rowcount == 0:
                    raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
                
                logger.info(f"Permanently deleted task: {task_id}")
                return True
        except TaskNotFoundError:
            raise
        except sqlite3.Error as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise DatabaseError(f"Failed to delete task: {e}")
    
    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """
        Convert a database row to a dictionary.
        
        Args:
            row: SQLite Row object.
        
        Returns:
            dict: Task data as dictionary.
        """
        return {
            "id": row["id"],
            "title": row["title"],
            "due_date": row["due_date"],
            "status": row["status"],
            "comments": row["comments"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

