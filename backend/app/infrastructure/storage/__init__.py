"""
Storage module for file handling.

This module provides storage abstraction following hexagonal architecture:
- IStorageService: Abstract interface (port)
- LocalStorageAdapter: Local file system implementation
- S3StorageAdapter: AWS S3 implementation
- get_storage: Factory function for dependency injection
"""

from app.application.services.i_storage_service import IStorageService
from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.storage.s3_storage import S3StorageAdapter
from app.infrastructure.storage.storage_factory import get_storage, get_storage_service

__all__ = [
    "IStorageService",
    "LocalStorageAdapter",
    "S3StorageAdapter",
    "get_storage",
    "get_storage_service"
]

# Legacy support - deprecated, use get_storage() instead
# Note: file_storage is only imported when explicitly needed to avoid
# Lambda cold start issues with filesystem operations
def get_file_storage():
    from app.infrastructure.storage.file_storage import file_storage
    return file_storage
