"""
Tests for storage adapters (Local and S3).

This module tests both storage implementations to ensure they follow
the IStorageService contract and handle all business rules correctly.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
from unittest.mock import MagicMock, patch, Mock
from moto import mock_aws
import boto3

from app.application.services.i_storage_service import IStorageService
from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.storage.s3_storage import S3StorageAdapter


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_upload_dir():
    """Create a temporary directory for test uploads."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def local_storage(temp_upload_dir):
    """Create a LocalStorageAdapter instance for testing."""
    return LocalStorageAdapter(
        base_path=temp_upload_dir,
        base_url="http://test.local:8000"
    )


@pytest.fixture
def mock_s3():
    """Mock AWS S3 for testing."""
    with mock_aws():
        # Create S3 client and bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bucket"
        s3_client.create_bucket(Bucket=bucket_name)

        yield {
            "client": s3_client,
            "bucket_name": bucket_name,
            "region": "us-east-1"
        }


@pytest.fixture
def s3_storage(mock_s3):
    """Create an S3StorageAdapter instance for testing."""
    return S3StorageAdapter(
        bucket_name=mock_s3["bucket_name"],
        region=mock_s3["region"],
        public_read=True
    )


def create_test_image(content: bytes = b"fake image content", filename: str = "test.jpg"):
    """Helper function to create a test UploadFile."""
    file_obj = BytesIO(content)
    return UploadFile(
        file=file_obj,
        filename=filename,
        headers={"content-type": "image/jpeg"}
    )


# ============================================================================
# LOCAL STORAGE ADAPTER TESTS
# ============================================================================

class TestLocalStorageAdapter:
    """Tests for LocalStorageAdapter."""

    @pytest.mark.asyncio
    async def test_save_product_image_success(self, local_storage):
        """Test successful image upload to local storage."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()

        # Act
        image_path = await local_storage.save_product_image(file, product_id)

        # Assert
        assert image_path.startswith("products/")
        assert product_id in image_path
        assert image_path.endswith(".jpg")
        assert local_storage.file_exists(image_path)

    @pytest.mark.asyncio
    async def test_save_product_image_invalid_type(self, local_storage):
        """Test rejection of invalid file types."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file_obj = BytesIO(b"fake pdf content")
        file = UploadFile(
            file=file_obj,
            filename="document.pdf",
            headers={"content-type": "application/pdf"}
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not supported"):
            await local_storage.save_product_image(file, product_id)

    @pytest.mark.asyncio
    async def test_save_product_image_exceeds_size_limit(self, local_storage):
        """Test rejection of files exceeding size limit."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        # Create a file larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        file = create_test_image(content=large_content)

        # Act & Assert
        with pytest.raises(ValueError, match="exceeds maximum"):
            await local_storage.save_product_image(file, product_id)

    @pytest.mark.asyncio
    async def test_delete_product_image_success(self, local_storage):
        """Test successful image deletion."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        image_path = await local_storage.save_product_image(file, product_id)

        # Act
        deleted = local_storage.delete_product_image(image_path)

        # Assert
        assert deleted is True
        assert not local_storage.file_exists(image_path)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_image(self, local_storage):
        """Test deletion of non-existent image returns False."""
        # Act
        deleted = local_storage.delete_product_image("products/nonexistent.jpg")

        # Assert
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_image_url(self, local_storage):
        """Test URL generation for local images."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        image_path = await local_storage.save_product_image(file, product_id)

        # Act
        url = local_storage.get_image_url(image_path)

        # Assert
        assert url.startswith("http://test.local:8000/uploads/")
        assert "products/" in url

    @pytest.mark.asyncio
    async def test_file_exists(self, local_storage):
        """Test file existence check."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        image_path = await local_storage.save_product_image(file, product_id)

        # Act & Assert
        assert local_storage.file_exists(image_path) is True
        assert local_storage.file_exists("products/nonexistent.jpg") is False

    @pytest.mark.asyncio
    async def test_different_file_extensions(self, local_storage):
        """Test handling of different image file extensions."""
        product_id = "550e8400-e29b-41d4-a716-446655440000"

        # Test PNG
        png_file = create_test_image(filename="test.png")
        png_file.headers = {"content-type": "image/png"}
        png_path = await local_storage.save_product_image(png_file, product_id)
        assert png_path.endswith(".png")

        # Test GIF
        gif_file = create_test_image(filename="test.gif")
        gif_file.headers = {"content-type": "image/gif"}
        gif_path = await local_storage.save_product_image(gif_file, product_id)
        assert gif_path.endswith(".gif")

        # Test WebP
        webp_file = create_test_image(filename="test.webp")
        webp_file.headers = {"content-type": "image/webp"}
        webp_path = await local_storage.save_product_image(webp_file, product_id)
        assert webp_path.endswith(".webp")


# ============================================================================
# S3 STORAGE ADAPTER TESTS
# ============================================================================

class TestS3StorageAdapter:
    """Tests for S3StorageAdapter."""

    @pytest.mark.asyncio
    async def test_save_product_image_success(self, s3_storage, mock_s3):
        """Test successful image upload to S3."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()

        # Act
        s3_key = await s3_storage.save_product_image(file, product_id)

        # Assert
        assert s3_key.startswith("products/")
        assert product_id in s3_key
        assert s3_key.endswith(".jpg")

        # Verify file exists in S3
        s3_client = mock_s3["client"]
        response = s3_client.head_object(
            Bucket=mock_s3["bucket_name"],
            Key=s3_key
        )
        assert response["ContentType"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_save_product_image_invalid_type(self, s3_storage):
        """Test rejection of invalid file types in S3."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file_obj = BytesIO(b"fake pdf content")
        file = UploadFile(
            file=file_obj,
            filename="document.pdf",
            headers={"content-type": "application/pdf"}
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not supported"):
            await s3_storage.save_product_image(file, product_id)

    @pytest.mark.asyncio
    async def test_save_product_image_exceeds_size_limit(self, s3_storage):
        """Test rejection of files exceeding size limit in S3."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        # Create a file larger than 5MB
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        file = create_test_image(content=large_content)

        # Act & Assert
        with pytest.raises(ValueError, match="exceeds maximum"):
            await s3_storage.save_product_image(file, product_id)

    @pytest.mark.asyncio
    async def test_delete_product_image_success(self, s3_storage, mock_s3):
        """Test successful image deletion from S3."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        s3_key = await s3_storage.save_product_image(file, product_id)

        # Act
        deleted = s3_storage.delete_product_image(s3_key)

        # Assert
        assert deleted is True
        assert not s3_storage.file_exists(s3_key)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_image(self, s3_storage):
        """Test deletion of non-existent image from S3."""
        # Act
        deleted = s3_storage.delete_product_image("products/nonexistent.jpg")

        # Assert
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_image_url(self, s3_storage, mock_s3):
        """Test URL generation for S3 images."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        s3_key = await s3_storage.save_product_image(file, product_id)

        # Act
        url = s3_storage.get_image_url(s3_key)

        # Assert
        assert url.startswith("https://")
        assert mock_s3["bucket_name"] in url
        assert "s3" in url
        assert s3_key in url

    @pytest.mark.asyncio
    async def test_get_image_url_with_full_url(self, s3_storage):
        """Test URL generation when input is already a full URL."""
        # Arrange
        full_url = "https://test-bucket.s3.us-east-1.amazonaws.com/products/test.jpg"

        # Act
        url = s3_storage.get_image_url(full_url)

        # Assert
        assert url == full_url

    @pytest.mark.asyncio
    async def test_file_exists(self, s3_storage, mock_s3):
        """Test file existence check in S3."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        s3_key = await s3_storage.save_product_image(file, product_id)

        # Act & Assert
        assert s3_storage.file_exists(s3_key) is True
        assert s3_storage.file_exists("products/nonexistent.jpg") is False

    @pytest.mark.asyncio
    async def test_extract_s3_key_from_url(self, s3_storage):
        """Test extraction of S3 key from full URL."""
        # Arrange
        s3_key = "products/test-image.jpg"
        full_url = f"https://test-bucket.s3.us-east-1.amazonaws.com/{s3_key}"

        # Act
        extracted_key = s3_storage._extract_s3_key(full_url)

        # Assert
        assert extracted_key == s3_key

    @pytest.mark.asyncio
    async def test_generate_presigned_url(self, s3_storage, mock_s3):
        """Test generation of pre-signed URLs for private files."""
        # Arrange
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()
        s3_key = await s3_storage.save_product_image(file, product_id)

        # Act
        presigned_url = s3_storage.generate_presigned_url(s3_key, expiration=3600)

        # Assert
        assert presigned_url.startswith("https://")
        assert mock_s3["bucket_name"] in presigned_url
        assert s3_key in presigned_url


# ============================================================================
# STORAGE FACTORY TESTS
# ============================================================================

class TestStorageFactory:
    """Tests for storage factory."""

    def test_get_local_storage(self):
        """Test factory returns LocalStorageAdapter when STORAGE_TYPE=local."""
        from app.infrastructure.storage.storage_factory import get_storage_service, reset_storage_service
        from app.config import settings

        # Reset to ensure clean state
        reset_storage_service()

        # Mock settings
        original_type = settings.STORAGE_TYPE
        settings.STORAGE_TYPE = "local"

        try:
            # Act
            storage = get_storage_service()

            # Assert
            assert isinstance(storage, LocalStorageAdapter)
        finally:
            # Cleanup
            settings.STORAGE_TYPE = original_type
            reset_storage_service()

    def test_get_s3_storage(self):
        """Test factory returns S3StorageAdapter when STORAGE_TYPE=s3."""
        from app.infrastructure.storage.storage_factory import get_storage_service, reset_storage_service
        from app.config import settings

        # Reset to ensure clean state
        reset_storage_service()

        # Mock settings
        original_type = settings.STORAGE_TYPE
        original_bucket = settings.AWS_S3_BUCKET_NAME

        settings.STORAGE_TYPE = "s3"
        settings.AWS_S3_BUCKET_NAME = "test-bucket"

        try:
            with mock_aws():
                # Create S3 bucket
                s3_client = boto3.client("s3", region_name="us-east-1")
                s3_client.create_bucket(Bucket="test-bucket")

                # Act
                storage = get_storage_service()

                # Assert
                assert isinstance(storage, S3StorageAdapter)
        finally:
            # Cleanup
            settings.STORAGE_TYPE = original_type
            settings.AWS_S3_BUCKET_NAME = original_bucket
            reset_storage_service()

    def test_invalid_storage_type(self):
        """Test factory raises error for invalid storage type."""
        from app.infrastructure.storage.storage_factory import get_storage_service, reset_storage_service
        from app.config import settings

        # Reset to ensure clean state
        reset_storage_service()

        # Mock settings
        original_type = settings.STORAGE_TYPE
        settings.STORAGE_TYPE = "invalid"

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="Invalid STORAGE_TYPE"):
                get_storage_service()
        finally:
            # Cleanup
            settings.STORAGE_TYPE = original_type
            reset_storage_service()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestStorageIntegration:
    """Integration tests for storage adapters."""

    @pytest.mark.asyncio
    async def test_local_storage_full_workflow(self, local_storage):
        """Test complete workflow: upload -> get URL -> delete."""
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()

        # Upload
        image_path = await local_storage.save_product_image(file, product_id)
        assert local_storage.file_exists(image_path)

        # Get URL
        url = local_storage.get_image_url(image_path)
        assert url
        assert image_path.replace("products/", "") in url

        # Delete
        deleted = local_storage.delete_product_image(image_path)
        assert deleted
        assert not local_storage.file_exists(image_path)

    @pytest.mark.asyncio
    async def test_s3_storage_full_workflow(self, s3_storage):
        """Test complete workflow: upload -> get URL -> delete."""
        product_id = "550e8400-e29b-41d4-a716-446655440000"
        file = create_test_image()

        # Upload
        s3_key = await s3_storage.save_product_image(file, product_id)
        assert s3_storage.file_exists(s3_key)

        # Get URL
        url = s3_storage.get_image_url(s3_key)
        assert url
        assert s3_key in url

        # Delete
        deleted = s3_storage.delete_product_image(s3_key)
        assert deleted
        assert not s3_storage.file_exists(s3_key)
