"""
Endpoints for file upload operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.infrastructure.storage.file_storage import file_storage
from app.infrastructure.auth.auth_dependency import get_current_user_sync
from app.domain.models.user import User
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.product_repository import SQLProductRepository
from sqlmodel import Session

router = APIRouter()


@router.post(
    "/product-image/{product_id}",
    summary="Upload product image",
    description="Upload an image file for a product. Supported formats: JPEG, PNG, GIF, WebP. Max size: 5MB.",
    responses={
        200: {"description": "Image uploaded successfully"},
        400: {"description": "Invalid file type or size"},
        413: {"description": "File too large"},
        422: {"description": "Validation error"}
    }
)
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(..., description="Image file to upload"),
    current_user: User = Depends(get_current_user_sync),
    session: Session = Depends(get_session)
):
    """
    Upload an image for a product.
    
    - **product_id**: UUID of the product
    - **file**: Image file (JPEG, PNG, GIF, WebP, max 5MB)
    
    Returns the relative path to the uploaded image.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Save the file
        image_path = await file_storage.save_product_image(file, str(product_id))

        # Update product with new image path
        product_repo = SQLProductRepository(session)
        try:
            product = await product_repo.get_by_id(product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )

            # Update the product's image path
            from app.domain.models.product import ProductUpdate
            update_data = ProductUpdate(imagen_path=image_path)
            await product_repo.update(product_id, update_data)

        except Exception as e:
            # If product update fails, clean up the uploaded file
            file_storage.delete_product_image(image_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating product: {str(e)}"
            )

        return {
            "message": "Image uploaded successfully",
            "image_path": image_path,
            "filename": file.filename
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
    description="Retrieve the image file for a product."
)
async def get_product_image(
    product_id: UUID,
    image_path: str
):
    """
    Get a product image file.
    
    - **product_id**: UUID of the product  
    - **image_path**: Relative path to the image
    """
    try:
        full_path = file_storage.base_path / image_path
        
        if not file_storage.file_exists(image_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        return FileResponse(
            full_path,
            media_type="image/*",
            filename=full_path.name
        )
        
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
    current_user: User = Depends(get_current_user_sync)
):
    """
    Delete a product image file.
    
    - **product_id**: UUID of the product
    - **image_path**: Relative path to the image to delete
    """
    try:
        deleted = file_storage.delete_product_image(image_path)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        return {"message": "Image deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}"
        )