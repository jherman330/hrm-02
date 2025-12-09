"""
Configuration management for the task management system.
Provides centralized settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration with environment variable overrides."""
    
    # Server settings
    HOST: str = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("FLASK_PORT", "5000"))
    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    
    # Database settings
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "tasks.db")
    
    # Application settings
    APP_NAME: str = "Task Management System"
    API_VERSION: str = "v1"
    
    @classmethod
    def get_database_path(cls) -> Path:
        """
        Get the absolute path to the database file.
        
        Returns:
            Path: Absolute path to the SQLite database file.
        """
        db_path = Path(cls.DATABASE_PATH)
        if not db_path.is_absolute():
            # Make relative paths relative to the src directory
            db_path = Path(__file__).parent / db_path
        return db_path
    
    @classmethod
    def get_config_dict(cls) -> dict:
        """
        Get all configuration values as a dictionary.
        
        Returns:
            dict: Configuration key-value pairs.
        """
        return {
            "host": cls.HOST,
            "port": cls.PORT,
            "debug": cls.DEBUG,
            "database_path": str(cls.get_database_path()),
            "app_name": cls.APP_NAME,
            "api_version": cls.API_VERSION,
        }


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG: bool = True


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG: bool = False


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG: bool = True
    DATABASE_PATH: str = ":memory:"


def get_config(env: Optional[str] = None) -> type:
    """
    Get the appropriate configuration class based on environment.
    
    Args:
        env: Optional environment name. If not provided, uses FLASK_ENV variable.
    
    Returns:
        type: Configuration class for the specified environment.
    """
    env = env or os.getenv("FLASK_ENV", "development")
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    return config_map.get(env.lower(), DevelopmentConfig)

