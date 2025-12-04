"""
Main entry point for the task management system.
Initializes the database on application startup.
"""

import sys
from datetime import datetime, timedelta, timezone

from database import Database, DatabaseError, TaskNotFoundError
from models import TaskCreate, TaskStatus, TaskUpdate


def initialize_application() -> Database:
    """
    Initialize the application and database.
    
    Returns:
        Database: Initialized database instance.
    
    Raises:
        SystemExit: If database initialization fails.
    """
    print("Initializing Task Management System...")
    
    try:
        db = Database()
        db.initialize_db()
        print("Database initialized successfully.")
        return db
    except DatabaseError as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)


def demo_operations(db: Database) -> None:
    """
    Demonstrate database operations for testing purposes.
    
    Args:
        db: Initialized database instance.
    """
    print("\n" + "=" * 50)
    print("Running demonstration of database operations...")
    print("=" * 50)
    
    # Create a new task
    print("\n1. Creating a new task...")
    try:
        new_task = TaskCreate(
            title="Complete project documentation",
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            comments="Include API documentation and user guide"
        )
        created_task = db.create_task(new_task)
        print(f"   Created task: {created_task.title} (ID: {created_task.id})")
        print(f"   Status: {created_task.status.value}")
        print(f"   Due: {created_task.due_date}")
    except DatabaseError as e:
        print(f"   Error creating task: {e}")
        return
    
    # Create another task
    print("\n2. Creating another task...")
    try:
        another_task = TaskCreate(
            title="Review pull requests",
            status=TaskStatus.IN_PROGRESS
        )
        created_task_2 = db.create_task(another_task)
        print(f"   Created task: {created_task_2.title} (ID: {created_task_2.id})")
    except DatabaseError as e:
        print(f"   Error creating task: {e}")
    
    # Retrieve all tasks
    print("\n3. Retrieving all tasks...")
    try:
        all_tasks = db.get_tasks()
        print(f"   Found {len(all_tasks)} task(s):")
        for task in all_tasks:
            print(f"   - [{task.status.value}] {task.title}")
    except DatabaseError as e:
        print(f"   Error retrieving tasks: {e}")
    
    # Filter tasks by status
    print("\n4. Filtering tasks by status (Open)...")
    try:
        open_tasks = db.get_tasks(status_filter=TaskStatus.OPEN)
        print(f"   Found {len(open_tasks)} open task(s):")
        for task in open_tasks:
            print(f"   - {task.title}")
    except DatabaseError as e:
        print(f"   Error filtering tasks: {e}")
    
    # Update a task
    print("\n5. Updating task status...")
    try:
        update_data = TaskUpdate(
            status=TaskStatus.CLOSED,
            comments="Completed ahead of schedule!"
        )
        updated_task = db.update_task(created_task.id, update_data)
        print(f"   Updated task: {updated_task.title}")
        print(f"   New status: {updated_task.status.value}")
        print(f"   Comments: {updated_task.comments}")
    except (TaskNotFoundError, DatabaseError) as e:
        print(f"   Error updating task: {e}")
    
    # Retrieve task by ID
    print("\n6. Retrieving task by ID...")
    try:
        retrieved_task = db.get_task_by_id(created_task.id)
        print(f"   Retrieved: {retrieved_task.title}")
        print(f"   Created: {retrieved_task.created_timestamp}")
        print(f"   Updated: {retrieved_task.updated_timestamp}")
    except (TaskNotFoundError, DatabaseError) as e:
        print(f"   Error retrieving task: {e}")
    
    print("\n" + "=" * 50)
    print("Demonstration complete!")
    print("=" * 50)


def main() -> None:
    """Main entry point for the application."""
    db = initialize_application()
    
    # Run demo operations to test the database
    demo_operations(db)
    
    print("\nTask Management System is ready.")
    print(f"Database file location: {db.db_path.absolute()}")


if __name__ == "__main__":
    main()

