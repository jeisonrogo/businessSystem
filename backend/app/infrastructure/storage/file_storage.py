"""
File storage service for handling product images and other files.
"""

import os
import uuid
from pathlib import Path
from typing import Optional
import shutil
from fastapi import UploadFile
import aiofiles


class FileStorageService:
    """Service for handling file uploads and storage."""
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.products_path = self.base_path / "products"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure upload directories exist."""
        self.base_path.mkdir(exist_ok=True)
        self.products_path.mkdir(exist_ok=True)
    
    async def save_product_image(self, file: UploadFile, product_id: str) -> str:
        """
        Save a product image file.
        
        Args:
            file: The uploaded file
            product_id: UUID of the product
            
        Returns:
            str: Relative path to the saved file
            
        Raises:
            ValueError: If file type is not supported
        """
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        if file.content_type not in allowed_types:
            raise ValueError(f"File type {file.content_type} not supported. Allowed: {allowed_types}")
        
        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        file_size = 0
        
        # Get file extension
        file_extension = self._get_file_extension(file.filename, file.content_type)
        
        # Generate unique filename
        filename = f"{product_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = self.products_path / filename
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)
                if file_size > max_size:
                    # Clean up partial file
                    if file_path.exists():
                        file_path.unlink()
                    raise ValueError(f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB")
                await f.write(chunk)
        
        # Return relative path from uploads directory
        return f"products/{filename}"
    
    def _get_file_extension(self, filename: Optional[str], content_type: str) -> str:
        """Get appropriate file extension based on filename or content type."""
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
    
    def delete_product_image(self, image_path: str) -> bool:
        """
        Delete a product image file.
        
        Args:
            image_path: Relative path to the image file
            
        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        if not image_path:
            return False
            
        file_path = self.base_path / image_path
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False
    
    def get_file_url(self, image_path: str, base_url: str) -> str:
        """
        Get the full URL for serving a file.
        
        Args:
            image_path: Relative path to the image file
            base_url: Base URL of the application
            
        Returns:
            str: Full URL to access the file
        """
        if not image_path:
            return ""
        return f"{base_url.rstrip('/')}/uploads/{image_path}"
    
    def file_exists(self, image_path: str) -> bool:
        """Check if a file exists."""
        if not image_path:
            return False
        file_path = self.base_path / image_path
        return file_path.exists() and file_path.is_file()


# Global instance
file_storage = FileStorageService()