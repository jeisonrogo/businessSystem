"""
Local file system storage adapter.

This adapter implements the IStorageService interface for storing files
on the local file system. It's used in development environments.
"""

import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import aiofiles

from app.application.services.i_storage_service import IStorageService


class LocalStorageAdapter(IStorageService):
    """
    Local file system storage implementation.

    This adapter stores files on the local file system and serves them
    through the application's static file endpoint.

    Configuration:
    - UPLOAD_DIR: Base directory for uploads (default: "uploads")
    - BASE_URL: Base URL of the application for generating public URLs
    """

    # Allowed file types (MIME types)
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

    # Maximum file size (5MB)
    MAX_SIZE = 5 * 1024 * 1024

    def __init__(self, base_path: str = "uploads", base_url: str = ""):
        """
        Initialize local storage adapter.

        Args:
            base_path: Base directory for file uploads
            base_url: Base URL of the application (for generating public URLs)
        """
        self.base_path = Path(base_path)
        self.products_path = self.base_path / "products"
        self.base_url = base_url.rstrip('/')
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure upload directories exist."""
        self.base_path.mkdir(exist_ok=True, parents=True)
        self.products_path.mkdir(exist_ok=True, parents=True)

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate file type and prepare for size validation.

        Args:
            file: The uploaded file

        Raises:
            ValueError: If file type is not supported
        """
        if not file.content_type or file.content_type not in self.ALLOWED_TYPES:
            raise ValueError(
                f"File type {file.content_type} not supported. "
                f"Allowed types: {', '.join(self.ALLOWED_TYPES)}"
            )

    async def save_product_image(self, file: UploadFile, product_id: str) -> str:
        """
        Save a product image to local file system.

        Args:
            file: The uploaded file object
            product_id: UUID of the product

        Returns:
            str: Relative path to the saved file (e.g., "products/abc123.jpg")

        Raises:
            ValueError: If file type or size is invalid
            Exception: For file system errors
        """
        # Validate file type
        self.validate_file(file)

        # Get file extension
        file_extension = self._get_file_extension(file.filename, file.content_type)

        # Generate unique filename: {product_id}_{random}.{ext}
        filename = f"{product_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = self.products_path / filename

        # Save file and validate size
        file_size = 0
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):  # Read in 8KB chunks
                    file_size += len(chunk)
                    if file_size > self.MAX_SIZE:
                        # Clean up partial file
                        if file_path.exists():
                            file_path.unlink()
                        raise ValueError(
                            f"File size exceeds maximum allowed size of "
                            f"{self.MAX_SIZE // (1024*1024)}MB"
                        )
                    await f.write(chunk)
        except Exception as e:
            # Clean up on any error
            if file_path.exists():
                file_path.unlink()
            raise e

        # Return relative path from uploads directory
        return f"products/{filename}"

    def delete_product_image(self, identifier: str) -> bool:
        """
        Delete a product image from local file system.

        Args:
            identifier: Relative path to the image file (e.g., "products/abc123.jpg")

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        if not identifier:
            return False

        file_path = self.base_path / identifier
        if file_path.exists() and file_path.is_file():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False
        return False

    def get_image_url(self, identifier: str) -> str:
        """
        Get the full URL for accessing an image.

        Args:
            identifier: Relative path to the image file

        Returns:
            str: Full URL to access the file through the application
        """
        if not identifier:
            return ""
        return f"{self.base_url}/uploads/{identifier}"

    def file_exists(self, identifier: str) -> bool:
        """
        Check if a file exists in local storage.

        Args:
            identifier: Relative path to the image file

        Returns:
            bool: True if file exists, False otherwise
        """
        if not identifier:
            return False
        file_path = self.base_path / identifier
        return file_path.exists() and file_path.is_file()

    def get_file_path(self, identifier: str) -> Path:
        """
        Get the absolute file system path for an identifier.

        Args:
            identifier: Relative path to the image file

        Returns:
            Path: Absolute path to the file
        """
        return self.base_path / identifier

    def _get_file_extension(self, filename: Optional[str], content_type: str) -> str:
        """
        Get appropriate file extension based on filename or content type.

        Args:
            filename: Original filename (may be None)
            content_type: MIME type of the file

        Returns:
            str: File extension including dot (e.g., ".jpg")
        """
        if filename and "." in filename:
            return Path(filename).suffix.lower()

        # Fallback to content type
        extension_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp"
        }
        return extension_map.get(content_type, ".jpg")
