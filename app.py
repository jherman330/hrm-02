"""
Main Flask application for the task management system.
Provides RESTful API endpoints with SQLite database integration.
"""

import atexit
import logging
import sys
from datetime import datetime

from flask import Flask, request
from flask_cors import CORS

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
    
    # Enable CORS for local development
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
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
    
    # =========================================================================
    # /api/tasks endpoints (WO-11) - Default filtering excludes Closed/Deleted
    # =========================================================================
    
    @app.route("/api/tasks", methods=["GET"])
    def get_tasks_api():
        """
        Retrieve tasks with default filtering (excludes Closed/Deleted).
        
        Query Parameters:
            status: Optional filter by specific status. If provided, returns
                   only tasks with that status. If not provided, excludes
                   Closed and Deleted tasks.
        
        Returns:
            JSON response with list of tasks sorted by due_date ascending.
        """
        status_param = request.args.get("status")
        
        if status_param:
            try:
                # Validate status
                TaskStatus(status_param)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise BadRequestError(
                    f"Invalid status '{status_param}'. Valid values: {valid_statuses}"
                )
        
        try:
            tasks = app.task_repo.get_all(
                status_filter=status_param,
                exclude_closed_deleted=(status_param is None),
                sort_by_due_date=True
            )
            return success_response(tasks)
        except DatabaseError as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            raise InternalServerError("Failed to retrieve tasks")
    
    @app.route("/api/tasks/<task_id>", methods=["GET"])
    def get_task_api(task_id: str):
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
    
    @app.route("/api/tasks", methods=["POST"])
    def create_task_api():
        """
        Create a new task.
        
        Request Body (JSON):
            title: Required task title
            due_date: Optional due date (ISO 8601 format)
            comments: Optional comments
        
        Note: Status is automatically set to 'Open', ID and timestamps
              are auto-generated.
        
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
            
            # Force status to Open for new tasks
            data["status"] = TaskStatus.OPEN
            
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
    
    @app.route("/api/tasks/<task_id>", methods=["PUT"])
    def update_task_api(task_id: str):
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
                if not data["title"]:
                    raise BadRequestError("Title cannot be empty")
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
    
    # =========================================================================
    # /api/tasks/filter endpoint (WO-17) - Advanced filtering and sorting
    # =========================================================================
    
    @app.route("/api/tasks/filter", methods=["GET"])
    def filter_tasks():
        """
        Advanced task filtering and sorting endpoint.
        
        Query Parameters:
            status: Filter by exact status (Open, In Progress, Blocked, Closed, Deleted)
            due_date_before: Filter tasks due before this date (ISO 8601 format)
            due_date_after: Filter tasks due after this date (ISO 8601 format)
            has_due_date: Filter by whether task has a due date (true/false)
            sort_by: Field to sort by (created_at, due_date, updated_at, title, status)
            sort_order: Sort direction (asc, desc) - default: desc
        
        Returns:
            JSON response with filtered and sorted task list.
            Returns empty array if no tasks match criteria.
        """
        # Get query parameters
        status = request.args.get("status")
        due_date_before = request.args.get("due_date_before")
        due_date_after = request.args.get("due_date_after")
        has_due_date_param = request.args.get("has_due_date")
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        
        # Validate status if provided
        if status:
            try:
                TaskStatus(status)
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                raise BadRequestError(
                    f"Invalid status '{status}'. Valid values: {valid_statuses}"
                )
        
        # Validate and parse has_due_date
        has_due_date = None
        if has_due_date_param is not None:
            if has_due_date_param.lower() == "true":
                has_due_date = True
            elif has_due_date_param.lower() == "false":
                has_due_date = False
            else:
                raise BadRequestError(
                    f"Invalid has_due_date '{has_due_date_param}'. Valid values: true, false"
                )
        
        # Validate date formats
        if due_date_before:
            try:
                datetime.fromisoformat(due_date_before.replace("Z", "+00:00"))
            except ValueError:
                raise BadRequestError(
                    f"Invalid due_date_before format '{due_date_before}'. Use ISO 8601 format."
                )
        
        if due_date_after:
            try:
                datetime.fromisoformat(due_date_after.replace("Z", "+00:00"))
            except ValueError:
                raise BadRequestError(
                    f"Invalid due_date_after format '{due_date_after}'. Use ISO 8601 format."
                )
        
        # Validate sort parameters
        valid_sort_fields = ["created_at", "due_date", "updated_at", "title", "status"]
        valid_sort_orders = ["asc", "desc"]
        
        if sort_by not in valid_sort_fields:
            raise BadRequestError(
                f"Invalid sort_by '{sort_by}'. Valid values: {valid_sort_fields}"
            )
        
        if sort_order.lower() not in valid_sort_orders:
            raise BadRequestError(
                f"Invalid sort_order '{sort_order}'. Valid values: {valid_sort_orders}"
            )
        
        try:
            tasks = app.task_repo.query(
                status=status,
                due_date_before=due_date_before,
                due_date_after=due_date_after,
                has_due_date=has_due_date,
                sort_by=sort_by,
                sort_order=sort_order
            )
            return success_response(tasks)
        except ValueError as e:
            raise BadRequestError(str(e))
        except DatabaseError as e:
            logger.error(f"Failed to filter tasks: {e}")
            raise InternalServerError("Failed to filter tasks")
    
    # =========================================================================
    # /tasks endpoints (WO-10) - Basic CRUD without /api prefix
    # =========================================================================
    
    @app.route("/tasks", methods=["GET"])
    def get_all_tasks():
        """
        Retrieve all tasks.
        
        Returns:
            200: JSON response with list of all tasks.
            500: Server error.
        """
        try:
            tasks = app.task_repo.get_all()
            return success_response(tasks)
        except DatabaseError as e:
            logger.error(f"Failed to retrieve tasks: {e}")
            raise InternalServerError("Failed to retrieve tasks")
    
    @app.route("/tasks/<task_id>", methods=["GET"])
    def get_single_task(task_id: str):
        """
        Retrieve a specific task by ID.
        
        Args:
            task_id: Unique task identifier.
        
        Returns:
            200: JSON response with task data.
            404: Task not found.
            500: Server error.
        """
        try:
            task = app.task_repo.get_by_id(task_id)
            return success_response(task)
        except TaskNotFoundError:
            raise NotFoundError(f"Task with ID '{task_id}' not found")
        except DatabaseError as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            raise InternalServerError("Failed to retrieve task")
    
    @app.route("/tasks", methods=["POST"])
    def create_new_task():
        """
        Create a new task.
        
        Request Body (JSON):
            title: Required task title
            due_date: Optional due date (ISO 8601 format)
            status: Optional status (default: Open)
            comments: Optional comments
        
        Returns:
            201: JSON response with created task data.
            400: Invalid request data.
            500: Server error.
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
    
    @app.route("/tasks/<task_id>", methods=["PUT"])
    def update_existing_task(task_id: str):
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
            200: JSON response with updated task data.
            400: Invalid request data.
            404: Task not found.
            500: Server error.
        """
        if not request.is_json:
            raise BadRequestError("Request must be JSON")
        
        data = request.get_json()
        
        if not data:
            raise BadRequestError("Request body is required")
        
        try:
            update_data = {}
            
            if "title" in data:
                if not data["title"]:
                    raise BadRequestError("Title cannot be empty")
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
    
    @app.route("/tasks/<task_id>", methods=["DELETE"])
    def delete_existing_task(task_id: str):
        """
        Delete a task (soft delete - marks as Deleted status).
        
        Args:
            task_id: Unique task identifier.
        
        Returns:
            200: JSON response confirming deletion.
            404: Task not found.
            500: Server error.
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

