"""
SQLite database connection management and schema initialization.
Provides centralized database setup and connection logic.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class DatabaseManager:
    """
    SQLite database manager for connection handling and schema management.
    
    Provides connection pooling-like behavior through context managers
    and handles automatic schema initialization.
    """
    
    _instance: Optional['DatabaseManager'] = None
    
    def __init__(self, db_path: str = "tasks.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._initialized = False
    
    @classmethod
    def get_instance(cls, db_path: str = "tasks.db") -> 'DatabaseManager':
        """
        Get or create the singleton database manager instance.
        
        Args:
            db_path: Path to the SQLite database file.
        
        Returns:
            DatabaseManager: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls(db_path)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
    
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with Row factory enabled.
        
        Raises:
            DatabaseError: If connection fails.
        """
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database connection error: {e}")
        finally:
            if conn:
                conn.close()
    
    def initialize_schema(self) -> None:
        """
        Initialize the database schema.
        Creates the tasks table if it doesn't exist.
        
        Raises:
            DatabaseError: If schema creation fails.
        """
        if self._initialized:
            return
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            due_date DATETIME,
            status TEXT NOT NULL DEFAULT 'Open',
            comments TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
        """
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                self._initialized = True
                logger.info(f"Database schema initialized at: {self.db_path.absolute()}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def close(self) -> None:
        """
        Close the database manager and cleanup resources.
        """
        self._initialized = False
        logger.info("Database manager closed")


# Module-level convenience functions
_db_manager: Optional[DatabaseManager] = None


def init_db(db_path: str = "tasks.db") -> DatabaseManager:
    """
    Initialize the database and return the manager instance.
    
    Args:
        db_path: Path to the SQLite database file.
    
    Returns:
        DatabaseManager: Initialized database manager.
    """
    global _db_manager
    _db_manager = DatabaseManager.get_instance(db_path)
    _db_manager.initialize_schema()
    return _db_manager


def get_db() -> DatabaseManager:
    """
    Get the current database manager instance.
    
    Returns:
        DatabaseManager: The current database manager.
    
    Raises:
        DatabaseError: If database has not been initialized.
    """
    if _db_manager is None:
        raise DatabaseError("Database not initialized. Call init_db() first.")
    return _db_manager


def close_db() -> None:
    """
    Close the database connection and cleanup.
    """
    global _db_manager
    if _db_manager:
        _db_manager.close()
        DatabaseManager.reset_instance()
        _db_manager = None

