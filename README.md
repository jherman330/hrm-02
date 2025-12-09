# Task Management System

A RESTful API backend for task management built with Flask and SQLite.

## Features

- **RESTful API**: Full CRUD operations for task management
- **SQLite Database**: Lightweight, file-based database with automatic initialization
- **Consistent JSON Responses**: All endpoints return standardized JSON format with `success`, `data`, and `error` fields
- **Robust Error Handling**: Appropriate HTTP status codes (400, 404, 500) with descriptive error messages
- **Configurable**: Environment-based configuration for development, testing, and production
- **Stateless**: No server-side session management

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. Clone the repository and navigate to the project directory:

```bash
cd hrm-02
```

2. Create and activate a virtual environment (recommended):

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

Navigate to the source directory and start the server:

```bash
cd src
python app.py
```

The API will be available at `http://localhost:5000`

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_HOST` | Server host address | `0.0.0.0` |
| `FLASK_PORT` | Server port | `5000` |
| `FLASK_DEBUG` | Enable debug mode | `false` |
| `FLASK_ENV` | Environment (development/production/testing) | `development` |
| `DATABASE_PATH` | Path to SQLite database | `tasks.db` |

## API Endpoints

### Health Check

```
GET /
GET /api/v1/health
```

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List all tasks (with optional status filter) |
| `GET` | `/api/v1/tasks/<id>` | Get a specific task |
| `POST` | `/api/v1/tasks` | Create a new task |
| `PUT/PATCH` | `/api/v1/tasks/<id>` | Update a task |
| `DELETE` | `/api/v1/tasks/<id>` | Delete a task (soft delete) |

### Response Format

All API responses follow this format:

```json
{
    "success": true,
    "data": { ... },
    "error": null
}
```

Error responses:

```json
{
    "success": false,
    "data": null,
    "error": "Error message describing what went wrong"
}
```

### Example Requests

**Create a task:**

```bash
curl -X POST http://localhost:5000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Complete documentation", "status": "Open"}'
```

**Get all tasks:**

```bash
curl http://localhost:5000/api/v1/tasks
```

**Filter tasks by status:**

```bash
curl "http://localhost:5000/api/v1/tasks?status=Open"
```

**Update a task:**

```bash
curl -X PUT http://localhost:5000/api/v1/tasks/<task-id> \
  -H "Content-Type: application/json" \
  -d '{"status": "Closed"}'
```

## Task Statuses

- `Open` - Task is open and not started
- `In Progress` - Task is currently being worked on
- `Blocked` - Task is blocked by dependencies
- `Closed` - Task has been completed
- `Deleted` - Task has been soft deleted

## Project Structure

```
hrm-02/
├── src/
│   ├── app.py           # Main Flask application
│   ├── config.py        # Configuration management
│   ├── database.py      # SQLite database operations
│   ├── models.py        # Pydantic data models
│   └── utils/
│       ├── __init__.py
│       ├── errors.py    # Error handling middleware
│       └── response.py  # JSON response utilities
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Development

### Running in Development Mode

```bash
set FLASK_DEBUG=true  # Windows
export FLASK_DEBUG=true  # Linux/macOS

cd src
python app.py
```

### Testing the API

After starting the server, you can test the health endpoint:

```bash
curl http://localhost:5000/
```

Expected response:

```json
{
    "success": true,
    "data": {
        "status": "healthy",
        "app_name": "Task Management System",
        "api_version": "v1",
        "timestamp": "2025-12-09T12:00:00.000000Z"
    },
    "error": null
}
```

## License

This project is for internal use.

