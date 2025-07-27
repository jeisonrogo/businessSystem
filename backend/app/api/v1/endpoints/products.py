"""
Endpoints para la gestión de productos.
Implementa las operaciones CRUD para productos del catálogo.
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductListResponse,
    ProductStockUpdateRequest,
    ProductStockUpdateResponse,
    LowStockThresholdRequest,
    ProductDeleteResponse,
    ErrorResponse,
    MessageResponse
)
from app.application.use_cases.product_use_cases import (
    CreateProductUseCase,
    GetProductUseCase,
    GetProductBySKUUseCase,
    ListProductsUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
    UpdateProductStockUseCase,
    GetLowStockProductsUseCase,
    ProductNotFoundError,
    DuplicateSKUError,
    InvalidStockError
)
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.product_repository import SQLProductRepository

router = APIRouter()


# Funciones de dependencia
def get_product_repository(session: Session = Depends(get_session)) -> SQLProductRepository:
    """Crear instancia del repositorio de productos."""
    return SQLProductRepository(session)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="Crea un nuevo producto en el catálogo. El SKU debe ser único.",
    responses={
        201: {"description": "Producto creado exitosamente"},
        400: {"model": ErrorResponse, "description": "Error de validación o SKU duplicado"},
        422: {"description": "Error de validación de datos"}
    }
)
async def create_product(
    product_data: ProductCreateRequest,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """
    Crear un nuevo producto.
    
    - **sku**: Código único del producto (requerido)
    - **nombre**: Nombre del producto (requerido)
    - **descripcion**: Descripción detallada (opcional)
    - **url_foto**: URL de la imagen del producto (opcional)
    - **precio_base**: Costo del producto para el negocio (requerido)
    - **precio_publico**: Precio de venta al público (requerido)
    - **stock**: Cantidad inicial en inventario (default: 0)
    """
    try:
        use_case = CreateProductUseCase(product_repo)
        product = await use_case.execute(product_data)
        return ProductResponse.model_validate(product)
    except DuplicateSKUError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Listar productos",
    description="Obtiene una lista paginada de productos con filtros opcionales.",
    responses={
        200: {"description": "Lista de productos obtenida exitosamente"},
        422: {"description": "Error de validación en parámetros de consulta"}
    }
)
async def list_products(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Productos por página"),
    search: Optional[str] = Query(None, description="Buscar por nombre o SKU"),
    only_active: bool = Query(True, description="Solo productos activos"),
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductListResponse:
    """
    Listar productos con paginación y filtros.
    
    - **page**: Número de página (empezando en 1)
    - **limit**: Número de productos por página (máximo 100)
    - **search**: Término de búsqueda por nombre o SKU
    - **only_active**: Si solo mostrar productos activos
    """
    try:
        use_case = ListProductsUseCase(product_repo)
        return await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            only_active=only_active
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Obtener producto por ID",
    description="Obtiene un producto específico por su ID único.",
    responses={
        200: {"description": "Producto encontrado"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        422: {"description": "ID de producto inválido"}
    }
)
async def get_product(
    product_id: UUID,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """
    Obtener un producto por su ID.
    
    - **product_id**: UUID único del producto
    """
    try:
        use_case = GetProductUseCase(product_repo)
        product = await use_case.execute(product_id)
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/sku/{sku}",
    response_model=ProductResponse,
    summary="Obtener producto por SKU",
    description="Obtiene un producto específico por su SKU único.",
    responses={
        200: {"description": "Producto encontrado"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"}
    }
)
async def get_product_by_sku(
    sku: str,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """
    Obtener un producto por su SKU.
    
    - **sku**: Código único del producto
    """
    try:
        use_case = GetProductBySKUUseCase(product_repo)
        product = await use_case.execute(sku)
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Actualizar producto",
    description="Actualiza un producto existente. El SKU no se puede modificar.",
    responses={
        200: {"description": "Producto actualizado exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        400: {"model": ErrorResponse, "description": "Error de validación"},
        422: {"description": "Error de validación de datos"}
    }
)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdateRequest,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductResponse:
    """
    Actualizar un producto existente.
    
    - **product_id**: UUID único del producto
    - **Nota**: El SKU no se puede modificar una vez creado (BR-02)
    - **Nota**: El stock se modifica a través de movimientos de inventario
    """
    try:
        use_case = UpdateProductUseCase(product_repo)
        product = await use_case.execute(product_id, product_data)
        return ProductResponse.model_validate(product)
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de validación: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
    summary="Eliminar producto",
    description="Elimina un producto (soft delete). El producto se marca como inactivo.",
    responses={
        200: {"description": "Producto eliminado exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"}
    }
)
async def delete_product(
    product_id: UUID,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductDeleteResponse:
    """
    Eliminar un producto (soft delete).
    
    - **product_id**: UUID único del producto
    - **Nota**: El producto no se elimina físicamente, solo se marca como inactivo
    """
    try:
        use_case = DeleteProductUseCase(product_repo)
        success = await use_case.execute(product_id)
        return ProductDeleteResponse(
            product_id=product_id,
            message="Producto eliminado exitosamente",
            success=success
        )
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.patch(
    "/{product_id}/stock",
    response_model=ProductStockUpdateResponse,
    summary="Actualizar stock de producto",
    description="Actualiza únicamente el stock de un producto específico.",
    responses={
        200: {"description": "Stock actualizado exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        400: {"model": ErrorResponse, "description": "Stock inválido (no puede ser negativo)"}
    }
)
async def update_product_stock(
    product_id: UUID,
    stock_data: ProductStockUpdateRequest,
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> ProductStockUpdateResponse:
    """
    Actualizar el stock de un producto.
    
    - **product_id**: UUID único del producto
    - **stock**: Nueva cantidad de stock (no puede ser negativo)
    - **Nota**: Se implementa BR-01 - Stock no puede ser negativo
    """
    try:
        # Obtener el stock actual para la respuesta
        get_use_case = GetProductUseCase(product_repo)
        current_product = await get_use_case.execute(product_id)
        previous_stock = current_product.stock
        
        # Actualizar el stock
        update_use_case = UpdateProductStockUseCase(product_repo)
        updated_product = await update_use_case.execute(product_id, stock_data.stock)
        
        return ProductStockUpdateResponse(
            product_id=product_id,
            previous_stock=previous_stock,
            new_stock=updated_product.stock,
            message=f"Stock actualizado de {previous_stock} a {updated_product.stock}"
        )
    except ProductNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/low-stock/",
    response_model=List[ProductResponse],
    summary="Obtener productos con stock bajo",
    description="Obtiene una lista de productos con stock bajo el umbral especificado.",
    responses={
        200: {"description": "Lista de productos con stock bajo"}
    }
)
async def get_low_stock_products(
    threshold: int = Query(10, ge=0, description="Umbral mínimo de stock"),
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> List[ProductResponse]:
    """
    Obtener productos con stock bajo.
    
    - **threshold**: Umbral mínimo de stock (default: 10)
    """
    try:
        use_case = GetLowStockProductsUseCase(product_repo)
        products = await use_case.execute(threshold)
        return [ProductResponse.model_validate(product) for product in products]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        ) 