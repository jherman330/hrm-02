"""
Main Flask application for the task management system.
Provides RESTful API endpoints with SQLite database integration.
"""

import atexit
import logging
import sys
from datetime import datetime

from flask import Flask, request

from config import Config, get_config
from database import init_db, close_db, TaskRepository
from database.database import DatabaseError
from database.task_repository import TaskNotFoundError
from models import Task, TaskCreate, TaskStatus, TaskUpdate
from utils.errors import (
    BadRequestError,
    NotFoundError,
    InternalServerError,
    register_error_handlers,
)
from utils.response import success_response, error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def create_app(config_class=None) -> Flask:
    """
    Flask application factory.
    
    Creates and configures the Flask application with:
    - Database initialization
    - Error handlers
    - API routes
    - Graceful shutdown handling
    
    Args:
        config_class: Optional configuration class. Uses environment-based config if not provided.
    
    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # Initialize database
    db_path = str(config_class.get_database_path())
    try:
        db_manager = init_db(db_path)
        logger.info(f"Database initialized at: {db_path}")
    except DatabaseError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Create task repository
    app.task_repo = TaskRepository(db_manager)
    
    # Register shutdown handler
    atexit.register(close_db)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register routes
    register_routes(app)
    
    logger.info(f"Application '{config_class.APP_NAME}' initialized successfully")
    
    return app


def register_routes(app: Flask) -> None:
    """
    Register all API routes with the Flask application.
    
    Args:
        app: Flask application instance.
    """
    
    @app.route("/", methods=["GET"])
    def health_check():
        """
        Health check endpoint.
        
        Returns:
            JSON response with application status and metadata.
        """
        config = get_config()
        return success_response({
            "status": "healthy",
            "app_name": config.APP_NAME,
            "api_version": config.API_VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    @app.route("/api/v1/health", methods=["GET"])
    def api_health():
        """
        API health check endpoint with database connectivity test.
        
        Returns:
            JSON response with detailed health status.
        """
        db_status = "connected"
        try:
            # Test database connectivity by fetching tasks
            app.task_repo.get_all()
        except Exception as e:
            db_status = f"error: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        return success_response({
            "status": "healthy",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    
    @app.route("/api/v1/tasks", methods=["GET"])
    def get_tasks():
        """
        Retrieve all tasks with optional status filtering.
        
        Query Parameters:
            status: Optional filter by task status (Open, In Progress, Blocked, Closed, Deleted)
        
        Returns:
            JSON response with list of tasks.
        """
        status_param = request.args.get("status")
        status_filter = None
        
        if status_param:
            try:
                # Validate status
                TaskStatus(status_param)
                status_filter = status_param
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise BadRequestError(
                    f"Invalid status '{status_param}'. Valid values: {valid_statuses}"
                )
        
        try:
            tasks = app.task_repo.get_all(status_filter=status_filter)
            return success_response(tasks)
        except DatabaseError as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            raise InternalServerError("Failed to retrieve tasks")
    
    @app.route("/api/v1/tasks/<task_id>", methods=["GET"])
    def get_task(task_id: str):
        """
        Retrieve a single task by ID.
        
        Args:
            task_id: Unique task identifier.
        
        Returns:
            JSON response with task details.
        """
        try:
            task = app.task_repo.get_by_id(task_id)
            return success_response(task)
        except TaskNotFoundError:
            raise NotFoundError(f"Task with ID '{task_id}' not found")
        except DatabaseError as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            raise InternalServerError("Failed to retrieve task")
    
    @app.route("/api/v1/tasks", methods=["POST"])
    def create_task():
        """
        Create a new task.
        
        Request Body (JSON):
            title: Required task title (1-500 characters)
            due_date: Optional due date (ISO 8601 format)
            status: Optional initial status (default: Open)
            comments: Optional comments (max 5000 characters)
        
        Returns:
            JSON response with created task details.
        """
        if not request.is_json:
            raise BadRequestError("Request must be JSON")
        
        data = request.get_json()
        
        if not data:
            raise BadRequestError("Request body is required")
        
        if "title" not in data or not data["title"]:
            raise BadRequestError("Task title is required")
        
        try:
            # Parse due_date if provided
            if "due_date" in data and data["due_date"]:
                data["due_date"] = datetime.fromisoformat(
                    data["due_date"].replace("Z", "+00:00")
                )
            
            # Parse status if provided
            if "status" in data and data["status"]:
                try:
                    data["status"] = TaskStatus(data["status"])
                except ValueError:
                    valid_statuses = [s.value for s in TaskStatus]
                    raise BadRequestError(
                        f"Invalid status '{data['status']}'. Valid values: {valid_statuses}"
                    )
            
            # Create task model and convert to DB format
            task_create = TaskCreate(**data)
            task = Task(**task_create.model_dump())
            task_dict = task.to_db_dict()
            
            created_task = app.task_repo.create(task_dict)
            
            logger.info(f"Created task: {created_task['id']} - {created_task['title']}")
            return success_response(created_task, status_code=201)
        
        except BadRequestError:
            raise
        except ValueError as e:
            raise BadRequestError(f"Invalid data: {str(e)}")
        except DatabaseError as e:
            logger.error(f"Failed to create task: {e}")
            raise InternalServerError("Failed to create task")
    
    @app.route("/api/v1/tasks/<task_id>", methods=["PUT", "PATCH"])
    def update_task(task_id: str):
        """
        Update an existing task.
        
        Args:
            task_id: Unique task identifier.
        
        Request Body (JSON):
            title: Optional new title
            due_date: Optional new due date
            status: Optional new status
            comments: Optional new comments
        
        Returns:
            JSON response with updated task details.
        """
        if not request.is_json:
            raise BadRequestError("Request must be JSON")
        
        data = request.get_json()
        
        if not data:
            raise BadRequestError("Request body is required")
        
        try:
            # Build update dict
            update_data = {}
            
            if "title" in data:
                update_data["title"] = data["title"]
            
            if "due_date" in data:
                if data["due_date"]:
                    update_data["due_date"] = datetime.fromisoformat(
                        data["due_date"].replace("Z", "+00:00")
                    ).isoformat()
                else:
                    update_data["due_date"] = None
            
            if "status" in data:
                try:
                    status = TaskStatus(data["status"])
                    update_data["status"] = status.value
                except ValueError:
                    valid_statuses = [s.value for s in TaskStatus]
                    raise BadRequestError(
                        f"Invalid status '{data['status']}'. Valid values: {valid_statuses}"
                    )
            
            if "comments" in data:
                update_data["comments"] = data["comments"]
            
            updated_task = app.task_repo.update(task_id, update_data)
            
            logger.info(f"Updated task: {task_id}")
            return success_response(updated_task)
        
        except BadRequestError:
            raise
        except TaskNotFoundError:
            raise NotFoundError(f"Task with ID '{task_id}' not found")
        except ValueError as e:
            raise BadRequestError(f"Invalid data: {str(e)}")
        except DatabaseError as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise InternalServerError("Failed to update task")
    
    @app.route("/api/v1/tasks/<task_id>", methods=["DELETE"])
    def delete_task(task_id: str):
        """
        Delete a task (soft delete - marks as Deleted status).
        
        Args:
            task_id: Unique task identifier.
        
        Returns:
            JSON response confirming deletion.
        """
        try:
            app.task_repo.delete(task_id, soft_delete=True)
            logger.info(f"Deleted task: {task_id}")
            return success_response({"message": f"Task '{task_id}' deleted successfully"})
        except TaskNotFoundError:
            raise NotFoundError(f"Task with ID '{task_id}' not found")
        except DatabaseError as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise InternalServerError("Failed to delete task")


# Create application instance
app = create_app()


if __name__ == "__main__":
    config = get_config()
    logger.info(f"Starting {config.APP_NAME} on {config.HOST}:{config.PORT}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )

