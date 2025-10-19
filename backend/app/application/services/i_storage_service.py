"""
Abstract interface for storage services.

This interface follows the Hexagonal Architecture pattern, defining the port
that storage adapters must implement. This allows the application to be
independent of specific storage implementations (local, S3, etc.).
"""

from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile


class IStorageService(ABC):
    """
    Abstract interface for file storage operations.

    Business Rules:
    - BR-STORAGE-01: All uploaded files must have unique names to prevent collisions
    - BR-STORAGE-02: Only image files (JPEG, PNG, GIF, WebP) are allowed
    - BR-STORAGE-03: Maximum file size is 5MB
    - BR-STORAGE-04: File paths must be safe and prevent directory traversal
    """

    @abstractmethod
    async def save_product_image(self, file: UploadFile, product_id: str) -> str:
        """
        Save a product image file.

        Args:
            file: The uploaded file object
            product_id: UUID of the product (used for filename generation)

        Returns:
            str: Storage identifier (path for local, S3 key for S3, or full URL)

        Raises:
            ValueError: If file type is not supported or file size exceeds limit
            Exception: For storage-specific errors
        """
        pass

    @abstractmethod
    def delete_product_image(self, identifier: str) -> bool:
        """
        Delete a product image file.

        Args:
            identifier: Storage identifier (path for local, S3 key/URL for S3)

        Returns:
            bool: True if file was deleted, False if file didn't exist

        Raises:
            Exception: For storage-specific errors
        """
        pass

    @abstractmethod
    def get_image_url(self, identifier: str) -> str:
        """
        Get the public URL to access an image.

        Args:
            identifier: Storage identifier (path for local, S3 key/URL for S3)

        Returns:
            str: Full public URL to access the image
        """
        pass

    @abstractmethod
    def file_exists(self, identifier: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            identifier: Storage identifier (path for local, S3 key/URL for S3)

        Returns:
            bool: True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def validate_file(self, file: UploadFile) -> None:
        """
        Validate that a file meets storage requirements.

        Args:
            file: The uploaded file object

        Raises:
            ValueError: If file doesn't meet requirements (type, size, etc.)
        """
        pass
