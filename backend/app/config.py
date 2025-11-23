"""
Application configuration module.

This module loads configuration from environment variables and provides
centralized access to application settings.
"""

import os
import json
from typing import Optional, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment Variables:
    - DATABASE_URL: PostgreSQL connection string
    - JWT_SECRET_KEY: Secret key for JWT token generation
    - ALGORITHM: JWT algorithm (default: HS256)
    - ACCESS_TOKEN_EXPIRE_MINUTES: JWT token expiration time
    - STORAGE_TYPE: Type of storage to use ("local" or "s3")
    - UPLOAD_DIR: Local storage directory (default: "uploads")
    - BASE_URL: Base URL of the application
    - AWS_S3_BUCKET_NAME: S3 bucket name (required for S3 storage)
    - AWS_REGION: AWS region (default: us-east-1)
    - AWS_ACCESS_KEY_ID: AWS access key (optional, uses IAM role if not set)
    - AWS_SECRET_ACCESS_KEY: AWS secret key (optional, uses IAM role if not set)
    """

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://admin:admin@localhost:5432/inventario",
        description="PostgreSQL database URL"
    )

    # JWT settings
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token generation"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )

    # Application settings
    BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Base URL of the application"
    )

    # Storage settings
    STORAGE_TYPE: str = Field(
        default="local",
        description="Type of storage: 'local' or 's3'"
    )
    UPLOAD_DIR: str = Field(
        default="uploads",
        description="Directory for local file uploads"
    )

    # AWS S3 settings (only required when STORAGE_TYPE=s3)
    AWS_S3_BUCKET_NAME: Optional[str] = Field(
        default=None,
        description="AWS S3 bucket name"
    )
    AWS_REGION: str = Field(
        default="us-east-1",
        description="AWS region"
    )
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="AWS access key ID (optional if using IAM roles)"
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        description="AWS secret access key (optional if using IAM roles)"
    )

    # CORS settings
    CORS_ORIGINS: Union[list[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins (JSON array string or list)"
    )

    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from JSON string if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's a single URL string, wrap it in a list
                return [v]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def validate_storage_config(self) -> None:
        """
        Validate storage configuration based on STORAGE_TYPE.

        Raises:
            ValueError: If required S3 settings are missing when STORAGE_TYPE=s3
        """
        if self.STORAGE_TYPE == "s3":
            if not self.AWS_S3_BUCKET_NAME:
                raise ValueError(
                    "AWS_S3_BUCKET_NAME is required when STORAGE_TYPE=s3"
                )


# Global settings instance
settings = Settings()

# Validate storage configuration on import
try:
    settings.validate_storage_config()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Storage configuration validation: {str(e)}")
