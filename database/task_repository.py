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
    
    def get_all(
        self, 
        status_filter: Optional[str] = None,
        exclude_closed_deleted: bool = False,
        sort_by_due_date: bool = False
    ) -> List[dict]:
        """
        Retrieve all tasks with optional status filtering.
        
        Args:
            status_filter: Optional status to filter tasks by.
            exclude_closed_deleted: If True, excludes Closed and Deleted tasks.
            sort_by_due_date: If True, sorts by due_date ASC (nulls last).
        
        Returns:
            List[dict]: List of task dictionaries.
        
        Raises:
            DatabaseError: If retrieval fails.
        """
        # Build WHERE clause
        where_clauses = []
        params = []
        
        if status_filter:
            where_clauses.append("status = ?")
            params.append(status_filter)
        elif exclude_closed_deleted:
            where_clauses.append("status NOT IN ('Closed', 'Deleted')")
        
        # Build ORDER BY clause
        if sort_by_due_date:
            # Sort by due_date ASC, with NULLs at the end
            order_by = "ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC"
        else:
            order_by = "ORDER BY created_at DESC"
        
        # Build full query
        if where_clauses:
            select_sql = f"SELECT * FROM tasks WHERE {' AND '.join(where_clauses)} {order_by}"
        else:
            select_sql = f"SELECT * FROM tasks {order_by}"
        
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
    
    def query(
        self,
        status: Optional[str] = None,
        due_date_before: Optional[str] = None,
        due_date_after: Optional[str] = None,
        has_due_date: Optional[bool] = None,
        exclude_closed_deleted: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[dict]:
        """
        Advanced query for tasks with multiple filter and sort options.
        
        Args:
            status: Filter by exact status value.
            due_date_before: Filter tasks with due_date before this date (ISO format).
            due_date_after: Filter tasks with due_date after this date (ISO format).
            has_due_date: If True, only tasks with due_date. If False, only tasks without.
            exclude_closed_deleted: If True, excludes Closed and Deleted tasks.
            sort_by: Field to sort by (created_at, due_date, updated_at, title).
            sort_order: Sort direction (asc or desc).
        
        Returns:
            List[dict]: List of task dictionaries matching criteria.
        
        Raises:
            DatabaseError: If query fails.
            ValueError: If invalid sort_by or sort_order provided.
        """
        # Validate sort parameters
        valid_sort_fields = ["created_at", "due_date", "updated_at", "title", "status"]
        valid_sort_orders = ["asc", "desc"]
        
        if sort_by not in valid_sort_fields:
            raise ValueError(f"Invalid sort_by '{sort_by}'. Valid values: {valid_sort_fields}")
        if sort_order.lower() not in valid_sort_orders:
            raise ValueError(f"Invalid sort_order '{sort_order}'. Valid values: {valid_sort_orders}")
        
        # Build WHERE clauses
        where_clauses = []
        params = []
        
        if status:
            where_clauses.append("status = ?")
            params.append(status)
        elif exclude_closed_deleted:
            where_clauses.append("status NOT IN ('Closed', 'Deleted')")
        
        if due_date_before:
            where_clauses.append("due_date < ?")
            params.append(due_date_before)
        
        if due_date_after:
            where_clauses.append("due_date > ?")
            params.append(due_date_after)
        
        if has_due_date is True:
            where_clauses.append("due_date IS NOT NULL")
        elif has_due_date is False:
            where_clauses.append("due_date IS NULL")
        
        # Build ORDER BY clause
        sort_order_sql = sort_order.upper()
        if sort_by == "due_date":
            # Handle NULLs for due_date sorting
            if sort_order_sql == "ASC":
                order_by = "ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date ASC"
            else:
                order_by = "ORDER BY CASE WHEN due_date IS NULL THEN 1 ELSE 0 END, due_date DESC"
        else:
            order_by = f"ORDER BY {sort_by} {sort_order_sql}"
        
        # Build full query
        if where_clauses:
            select_sql = f"SELECT * FROM tasks WHERE {' AND '.join(where_clauses)} {order_by}"
        else:
            select_sql = f"SELECT * FROM tasks {order_by}"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, params)
                rows = cursor.fetchall()
                return [self._row_to_dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to query tasks: {e}")
            raise DatabaseError(f"Failed to query tasks: {e}")
    
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

