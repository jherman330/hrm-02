"""
Custom error classes and error handling middleware for the task management API.
Provides consistent JSON error responses with appropriate HTTP status codes.
"""

import logging
from typing import Optional

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors with HTTP status code support."""
    
    status_code: int = 500
    default_message: str = "An unexpected error occurred"
    
    def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None):
        """
        Initialize the API error.
        
        Args:
            message: Error message. Uses default_message if not provided.
            status_code: HTTP status code. Uses class default if not provided.
        """
        self.message = message or self.default_message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """
        Convert the error to a dictionary for JSON serialization.
        
        Returns:
            dict: Error details with standard response format.
        """
        return {
            "success": False,
            "data": None,
            "error": self.message
        }


class BadRequestError(APIError):
    """Error for invalid client requests (400)."""
    status_code = 400
    default_message = "Bad request"


class NotFoundError(APIError):
    """Error for resources that don't exist (404)."""
    status_code = 404
    default_message = "Resource not found"


class InternalServerError(APIError):
    """Error for server-side issues (500)."""
    status_code = 500
    default_message = "Internal server error"


class ValidationError(BadRequestError):
    """Error for request validation failures (400)."""
    default_message = "Validation error"


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers with the Flask application.
    
    Provides consistent JSON error responses for:
    - Custom APIError exceptions
    - Standard HTTP errors (400, 404, 500)
    - Uncaught exceptions
    
    Args:
        app: Flask application instance.
    """
    
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        """Handle custom API errors."""
        logger.warning(f"API Error: {error.message} (status: {error.status_code})")
        return jsonify(error.to_dict()), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors."""
        logger.warning(f"Bad Request: {error}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "Bad request"
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors."""
        logger.info(f"Not Found: {error}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "Resource not found"
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        logger.warning(f"Method Not Allowed: {error}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "Method not allowed"
        }), 405
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors."""
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "Internal server error"
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any uncaught exceptions."""
        logger.exception(f"Unexpected error: {error}")
        return jsonify({
            "success": False,
            "data": None,
            "error": "An unexpected error occurred"
        }), 500

