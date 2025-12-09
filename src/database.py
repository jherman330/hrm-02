"""
SQLite database operations for the task management system.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Optional

from models import Task, TaskCreate, TaskStatus, TaskUpdate


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class TaskNotFoundError(DatabaseError):
    """Raised when a task is not found."""
    pass


class Database:
    """SQLite database manager for task operations."""
    
    def __init__(self, db_path: str = "tasks.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
    
    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection object.
        
        Raises:
            DatabaseError: If connection fails.
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            raise DatabaseError(f"Database connection error: {e}")
        finally:
            if conn:
                conn.close()
    
    def initialize_db(self) -> None:
        """
        Initialize the database schema.
        Creates the tasks table if it doesn't exist.
        
        Raises:
            DatabaseError: If table creation fails.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            due_date DATETIME,
            status TEXT NOT NULL DEFAULT 'Open',
            comments TEXT,
            created_timestamp DATETIME NOT NULL,
            updated_timestamp DATETIME NOT NULL
        )
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create a new task in the database.
        
        Args:
            task_data: TaskCreate model with task information.
        
        Returns:
            Task: The created task with all fields populated.
        
        Raises:
            DatabaseError: If task creation fails.
        """
        task = Task(**task_data.model_dump())
        
        insert_sql = """
        INSERT INTO tasks (id, title, due_date, status, comments, created_timestamp, updated_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, (
                    task.id,
                    task.title,
                    task.due_date.isoformat() if task.due_date else None,
                    task.status.value,
                    task.comments,
                    task.created_timestamp.isoformat(),
                    task.updated_timestamp.isoformat()
                ))
                conn.commit()
                return task
        except sqlite3.IntegrityError as e:
            raise DatabaseError(f"Task with this ID already exists: {e}")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to create task: {e}")
    
    def get_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        Retrieve tasks from the database with optional status filtering.
        
        Args:
            status_filter: Optional TaskStatus to filter tasks by.
        
        Returns:
            List[Task]: List of tasks matching the criteria.
        
        Raises:
            DatabaseError: If retrieval fails.
        """
        if status_filter:
            select_sql = "SELECT * FROM tasks WHERE status = ? ORDER BY created_timestamp DESC"
            params = (status_filter.value,)
        else:
            select_sql = "SELECT * FROM tasks ORDER BY created_timestamp DESC"
            params = ()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, params)
                rows = cursor.fetchall()
                
                tasks = []
                for row in rows:
                    task = Task(
                        id=row["id"],
                        title=row["title"],
                        due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                        status=TaskStatus(row["status"]),
                        comments=row["comments"],
                        created_timestamp=datetime.fromisoformat(row["created_timestamp"]),
                        updated_timestamp=datetime.fromisoformat(row["updated_timestamp"])
                    )
                    tasks.append(task)
                
                return tasks
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve tasks: {e}")
    
    def get_task_by_id(self, task_id: str) -> Task:
        """
        Retrieve a single task by its ID.
        
        Args:
            task_id: The unique identifier of the task.
        
        Returns:
            Task: The requested task.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If retrieval fails.
        """
        select_sql = "SELECT * FROM tasks WHERE id = ?"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql, (task_id,))
                row = cursor.fetchone()
                
                if not row:
                    raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
                
                return Task(
                    id=row["id"],
                    title=row["title"],
                    due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                    status=TaskStatus(row["status"]),
                    comments=row["comments"],
                    created_timestamp=datetime.fromisoformat(row["created_timestamp"]),
                    updated_timestamp=datetime.fromisoformat(row["updated_timestamp"])
                )
        except TaskNotFoundError:
            raise
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to retrieve task: {e}")
    
    def update_task(self, task_id: str, task_data: TaskUpdate) -> Task:
        """
        Update an existing task by ID.
        
        Args:
            task_id: The unique identifier of the task to update.
            task_data: TaskUpdate model with fields to update.
        
        Returns:
            Task: The updated task.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If update fails.
        """
        # First, verify the task exists
        existing_task = self.get_task_by_id(task_id)
        
        # Build update data from provided fields
        update_fields = task_data.model_dump(exclude_unset=True)
        
        if not update_fields:
            return existing_task
        
        # Always update the updated_timestamp
        update_fields["updated_timestamp"] = datetime.now(timezone.utc)
        
        # Build the SQL dynamically based on provided fields
        set_clauses = []
        values = []
        
        for field, value in update_fields.items():
            set_clauses.append(f"{field} = ?")
            if field == "status" and value:
                values.append(value.value if isinstance(value, TaskStatus) else value)
            elif field in ("due_date", "updated_timestamp") and value:
                values.append(value.isoformat() if isinstance(value, datetime) else value)
            else:
                values.append(value)
        
        values.append(task_id)
        
        update_sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(update_sql, values)
                conn.commit()
                
                if cursor.rowcount == 0:
                    raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
                
                return self.get_task_by_id(task_id)
        except TaskNotFoundError:
            raise
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update task: {e}")
    
    def delete_task(self, task_id: str) -> bool:
        """
        Soft delete a task by setting its status to Deleted.
        
        Args:
            task_id: The unique identifier of the task to delete.
        
        Returns:
            bool: True if the task was deleted successfully.
        
        Raises:
            TaskNotFoundError: If the task doesn't exist.
            DatabaseError: If deletion fails.
        """
        update_data = TaskUpdate(status=TaskStatus.DELETED)
        self.update_task(task_id, update_data)
        return True
