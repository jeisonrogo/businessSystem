"""
Endpoints for file upload operations.

This module uses the storage service abstraction to support both local
and S3 storage based on configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.application.services.i_storage_service import IStorageService
from app.infrastructure.storage.storage_factory import get_storage
from app.infrastructure.storage.local_storage import LocalStorageAdapter
from app.infrastructure.auth.auth_dependency import get_current_user_sync
from app.domain.models.user import User
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.config import settings
from sqlmodel import Session

router = APIRouter()


@router.post(
    "/product-image/{product_id}",
    summary="Upload product image",
    description="Upload an image file for a product. Supported formats: JPEG, PNG, GIF, WebP. Max size: 5MB.",
    responses={
        200: {"description": "Image uploaded successfully"},
        400: {"description": "Invalid file type or size"},
        404: {"description": "Product not found"},
        413: {"description": "File too large"},
        422: {"description": "Validation error"}
    }
)
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user_sync),
    session: Session = Depends(get_session),
    storage: IStorageService = Depends(get_storage)
):
    """
    Upload an image for a product.

    - **product_id**: UUID of the product
    - **file**: Image file (JPEG, PNG, GIF, WebP, max 5MB)

    Returns the storage identifier (path or URL) and public URL to the uploaded image.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Verify product exists before uploading
        product_repo = SQLProductRepository(session)
        product = await product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Save the file using the configured storage service
        image_identifier = await storage.save_product_image(file, str(product_id))

        # Update product with new image identifier
        try:
            from app.domain.models.product import ProductUpdate
            update_data = ProductUpdate(imagen_path=image_identifier)
            await product_repo.update(product_id, update_data)

        except Exception as e:
            # If product update fails, clean up the uploaded file
            storage.delete_product_image(image_identifier)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating product: {str(e)}"
            )

        # Generate public URL
        image_url = storage.get_image_url(image_identifier)

        return {
            "message": "Image uploaded successfully",
            "image_path": image_identifier,
            "image_url": image_url,
            "filename": file.filename,
            "storage_type": settings.STORAGE_TYPE
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get(
    "/product-image/{product_id}",
    response_class=FileResponse,
    summary="Get product image",
    description="Retrieve the image file for a product. Only works for local storage."
)
async def get_product_image(
    product_id: UUID,
    image_path: str,
    storage: IStorageService = Depends(get_storage)
):
    """
    Get a product image file.

    NOTE: This endpoint only works for local storage. For S3 storage,
    use the direct URL returned by the upload endpoint.

    - **product_id**: UUID of the product
    - **image_path**: Relative path to the image
    """
    try:
        # Only local storage supports direct file serving
        if not isinstance(storage, LocalStorageAdapter):
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Direct file serving is only available for local storage. "
                       "Use the image_url from the product response for S3 storage."
            )

        if not storage.file_exists(image_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )

        full_path = storage.get_file_path(image_path)

        return FileResponse(
            full_path,
            media_type="image/*",
            filename=full_path.name
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving file: {str(e)}"
        )


@router.delete(
    "/product-image/{product_id}",
    summary="Delete product image",
    description="Delete an image file for a product."
)
async def delete_product_image(
    product_id: UUID,
    image_path: str,
    current_user: User = Depends(get_current_user_sync),
    session: Session = Depends(get_session),
    storage: IStorageService = Depends(get_storage)
):
    """
    Delete a product image file.

    - **product_id**: UUID of the product
    - **image_path**: Storage identifier (path for local, key/URL for S3)
    """
    try:
        # Verify product exists and user has permission
        product_repo = SQLProductRepository(session)
        product = await product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Delete the file from storage
        deleted = storage.delete_product_image(image_path)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found in storage"
            )

        # Clear image path from product
        from app.domain.models.product import ProductUpdate
        update_data = ProductUpdate(imagen_path=None)
        await product_repo.update(product_id, update_data)

        return {
            "message": "Image deleted successfully",
            "storage_type": settings.STORAGE_TYPE
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )


@router.get(
    "/storage-info",
    summary="Get storage configuration",
    description="Get information about the current storage configuration."
)
async def get_storage_info(
    current_user: User = Depends(get_current_user_sync),
    storage: IStorageService = Depends(get_storage)
):
    """
    Get storage configuration information.

    Useful for debugging and understanding which storage backend is being used.
    """
    storage_info = {
        "storage_type": settings.STORAGE_TYPE,
        "adapter_class": storage.__class__.__name__
    }

    if settings.STORAGE_TYPE == "local":
        storage_info["upload_dir"] = settings.UPLOAD_DIR
        storage_info["base_url"] = settings.BASE_URL
    elif settings.STORAGE_TYPE == "s3":
        storage_info["bucket_name"] = settings.AWS_S3_BUCKET_NAME
        storage_info["region"] = settings.AWS_REGION
        storage_info["using_iam_role"] = settings.AWS_ACCESS_KEY_ID is None

    return storage_info
