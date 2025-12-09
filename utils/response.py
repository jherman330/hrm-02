"""
Consistent JSON response utilities for the task management API.
All API responses follow a standardized format with 'success', 'data', and 'error' fields.
"""

from typing import Any, Optional

from flask import jsonify, Response


def api_response(
    success: bool,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    status_code: int = 200
) -> tuple[Response, int]:
    """
    Create a standardized API response.
    
    Args:
        success: Whether the operation was successful.
        data: Response data payload (for successful responses).
        error: Error message (for failed responses).
        status_code: HTTP status code.
    
    Returns:
        tuple: Flask JSON response and status code.
    """
    response_body = {
        "success": success,
        "data": data,
        "error": error
    }
    
    return jsonify(response_body), status_code


def success_response(data: Any = None, status_code: int = 200) -> tuple[Response, int]:
    """
    Create a successful API response.
    
    Args:
        data: Response data payload.
        status_code: HTTP status code (default: 200).
    
    Returns:
        tuple: Flask JSON response and status code.
    """
    return api_response(success=True, data=data, status_code=status_code)


def error_response(error: str, status_code: int = 400) -> tuple[Response, int]:
    """
    Create an error API response.
    
    Args:
        error: Error message describing what went wrong.
        status_code: HTTP status code (default: 400).
    
    Returns:
        tuple: Flask JSON response and status code.
    """
    return api_response(success=False, error=error, status_code=status_code)

