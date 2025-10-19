"""
Storage factory for selecting the appropriate storage adapter.

This factory implements the Factory Pattern to create the correct storage
adapter based on the application configuration (environment variables).
"""

import logging
from typing import Optional

from app.application.services.i_storage_service import IStorageService
from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.storage.s3_storage import S3StorageAdapter
from app.config import settings

logger = logging.getLogger(__name__)

# Global storage instance (singleton)
_storage_instance: Optional[IStorageService] = None


def get_storage_service() -> IStorageService:
    """
    Get the configured storage service instance.

    This function creates and returns the appropriate storage adapter based
    on the STORAGE_TYPE environment variable. It uses a singleton pattern
    to ensure only one instance is created.

    Returns:
        IStorageService: Storage service instance (LocalStorageAdapter or S3StorageAdapter)

    Raises:
        ValueError: If STORAGE_TYPE is invalid or required configuration is missing
    """
    global _storage_instance

    # Return existing instance if already created
    if _storage_instance is not None:
        return _storage_instance

    storage_type = settings.STORAGE_TYPE.lower()

    if storage_type == "local":
        logger.info("Initializing LocalStorageAdapter")
        _storage_instance = LocalStorageAdapter(
            base_path=settings.UPLOAD_DIR,
            base_url=settings.BASE_URL
        )

    elif storage_type == "s3":
        logger.info("Initializing S3StorageAdapter")

        # Validate required S3 settings
        if not settings.AWS_S3_BUCKET_NAME:
            raise ValueError(
                "AWS_S3_BUCKET_NAME is required when STORAGE_TYPE=s3. "
                "Please set the environment variable."
            )

        _storage_instance = S3StorageAdapter(
            bucket_name=settings.AWS_S3_BUCKET_NAME,
            region=settings.AWS_REGION,
            access_key=settings.AWS_ACCESS_KEY_ID,
            secret_key=settings.AWS_SECRET_ACCESS_KEY,
            public_read=True  # Make images publicly accessible
        )

    else:
        raise ValueError(
            f"Invalid STORAGE_TYPE: {storage_type}. "
            f"Supported values are: 'local', 's3'"
        )

    logger.info(f"Storage service initialized: {storage_type}")
    return _storage_instance


def reset_storage_service() -> None:
    """
    Reset the storage service singleton.

    This is primarily useful for testing purposes to allow creating
    a new storage instance with different configuration.
    """
    global _storage_instance
    _storage_instance = None
    logger.info("Storage service instance reset")


# Dependency injection function for FastAPI
def get_storage() -> IStorageService:
    """
    FastAPI dependency for injecting storage service.

    Usage in endpoints:
        @router.post("/upload")
        async def upload(storage: IStorageService = Depends(get_storage)):
            ...

    Returns:
        IStorageService: Configured storage service instance
    """
    return get_storage_service()
