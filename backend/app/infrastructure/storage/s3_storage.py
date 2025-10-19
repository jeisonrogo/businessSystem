"""
AWS S3 storage adapter.

This adapter implements the IStorageService interface for storing files
in Amazon S3. It's used in production environments (AWS App Runner).
"""

import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import logging

from app.application.services.i_storage_service import IStorageService

logger = logging.getLogger(__name__)


class S3StorageAdapter(IStorageService):
    """
    AWS S3 storage implementation.

    This adapter stores files in Amazon S3 and generates pre-signed URLs
    or public URLs for accessing the files.

    Configuration (environment variables):
    - AWS_S3_BUCKET_NAME: Name of the S3 bucket
    - AWS_REGION: AWS region (e.g., us-east-1)
    - AWS_ACCESS_KEY_ID: AWS access key (optional if using IAM roles)
    - AWS_SECRET_ACCESS_KEY: AWS secret key (optional if using IAM roles)
    """

    # Allowed file types (MIME types)
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

    # Maximum file size (5MB)
    MAX_SIZE = 5 * 1024 * 1024

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        public_read: bool = True
    ):
        """
        Initialize S3 storage adapter.

        Args:
            bucket_name: Name of the S3 bucket
            region: AWS region
            access_key: AWS access key (optional, uses IAM role if not provided)
            secret_key: AWS secret key (optional, uses IAM role if not provided)
            public_read: Whether to make uploaded files publicly readable
        """
        self.bucket_name = bucket_name
        self.region = region
        self.public_read = public_read

        # Initialize S3 client
        session_kwargs = {"region_name": region}
        if access_key and secret_key:
            session_kwargs["aws_access_key_id"] = access_key
            session_kwargs["aws_secret_access_key"] = secret_key

        try:
            self.s3_client = boto3.client("s3", **session_kwargs)
            logger.info(f"S3 client initialized for bucket: {bucket_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise ValueError("AWS credentials not configured")

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
        Save a product image to S3.

        Args:
            file: The uploaded file object
            product_id: UUID of the product

        Returns:
            str: S3 key of the uploaded file (e.g., "products/abc123.jpg")

        Raises:
            ValueError: If file type or size is invalid
            Exception: For S3 errors
        """
        # Validate file type
        self.validate_file(file)

        # Get file extension
        file_extension = self._get_file_extension(file.filename, file.content_type)

        # Generate unique S3 key: products/{product_id}_{random}.{ext}
        filename = f"{product_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        s3_key = f"products/{filename}"

        # Read file content and validate size
        file_content = bytearray()
        while chunk := await file.read(8192):  # Read in 8KB chunks
            file_content.extend(chunk)
            if len(file_content) > self.MAX_SIZE:
                raise ValueError(
                    f"File size exceeds maximum allowed size of "
                    f"{self.MAX_SIZE // (1024*1024)}MB"
                )

        # Upload to S3
        try:
            extra_args = {
                "ContentType": file.content_type,
                "CacheControl": "max-age=31536000",  # Cache for 1 year
            }

            # Note: ACL is not used as modern S3 buckets have ACLs disabled by default.
            # Public access should be configured via bucket policy instead.
            # See STORAGE_SYSTEM.md for bucket policy configuration.

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=bytes(file_content),
                **extra_args
            )

            logger.info(f"File uploaded to S3: {s3_key}")
            return s3_key

        except ClientError as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")

    def delete_product_image(self, identifier: str) -> bool:
        """
        Delete a product image from S3.

        Args:
            identifier: S3 key or full S3 URL

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        if not identifier:
            logger.warning("delete_product_image called with empty identifier")
            return False

        # Extract S3 key from URL if needed
        s3_key = self._extract_s3_key(identifier)
        logger.info(f"Attempting to delete S3 object. Identifier: {identifier}, Extracted key: {s3_key}")

        try:
            # Check if file exists
            if not self.file_exists(s3_key):
                logger.warning(f"File does not exist in S3: {s3_key}")
                return False

            # Delete the object
            logger.info(f"Deleting S3 object: bucket={self.bucket_name}, key={s3_key}")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✅ File deleted from S3: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"❌ Error deleting from S3: {str(e)}")
            return False

    def get_image_url(self, identifier: str) -> str:
        """
        Get the public URL for accessing an image.

        Args:
            identifier: S3 key or full S3 URL

        Returns:
            str: Full public URL to access the file
        """
        if not identifier:
            return ""

        # If already a full URL, return it
        if identifier.startswith("http"):
            return identifier

        # Build public URL
        # Format: https://{bucket}.s3.{region}.amazonaws.com/{key}
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{identifier}"

    def file_exists(self, identifier: str) -> bool:
        """
        Check if a file exists in S3.

        Args:
            identifier: S3 key or full S3 URL

        Returns:
            bool: True if file exists, False otherwise
        """
        if not identifier:
            return False

        # Extract S3 key from URL if needed
        s3_key = self._extract_s3_key(identifier)

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False

    def _extract_s3_key(self, identifier: str) -> str:
        """
        Extract S3 key from a full URL or return the key as-is.

        Args:
            identifier: S3 key or full S3 URL

        Returns:
            str: S3 key
        """
        if not identifier.startswith("http"):
            return identifier

        # Extract key from URL
        # Format: https://{bucket}.s3.{region}.amazonaws.com/{key}
        if ".s3." in identifier:
            parts = identifier.split(".amazonaws.com/")
            if len(parts) == 2:
                return parts[1]

        # If we can't parse, assume it's already a key
        return identifier

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

    def generate_presigned_url(self, identifier: str, expiration: int = 3600) -> str:
        """
        Generate a pre-signed URL for private files.

        This method is useful when files are not publicly readable.

        Args:
            identifier: S3 key or full S3 URL
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            str: Pre-signed URL
        """
        s3_key = self._extract_s3_key(identifier)

        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception(f"Failed to generate presigned URL: {str(e)}")
