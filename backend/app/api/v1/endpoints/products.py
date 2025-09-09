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
from app.infrastructure.auth.auth_dependency import get_current_user_sync
from app.domain.models.user import User, UserRole
from app.infrastructure.middleware.tenant_middleware import get_tenant_context
from app.domain.models.tenant_context import TenantContext

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
    product_repo: SQLProductRepository = Depends(get_product_repository),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_sync),
    tenant_context: TenantContext = Depends(get_tenant_context)
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
        # Validar que hay contexto local para crear stock inicial
        if not tenant_context.local_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere seleccionar un local para crear productos. Use el selector de contexto."
            )
        
        # Convertir al formato de dominio y asignar tienda del contexto
        from app.domain.models.product import ProductCreate
        
        domain_product_data = ProductCreate(
            sku=product_data.sku,
            nombre=product_data.nombre,
            descripcion=product_data.descripcion,
            url_foto=product_data.url_foto,
            precio_base=product_data.precio_base,
            precio_publico=product_data.precio_publico,
            tienda_id=tenant_context.tienda_id,
            stock_inicial=product_data.stock_inicial or 0
        )
        
        # Crear el producto
        use_case = CreateProductUseCase(product_repo)
        product = await use_case.execute(domain_product_data)
        
        # IMPORTANTE: Crear automáticamente el registro de stock inicial en el local seleccionado
        from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
        from app.domain.models.stock_local import StockLocalCreate
        
        stock_repo = StockLocalRepository(session)
        
        # Crear stock inicial con la cantidad especificada en el local seleccionado
        stock_inicial = product_data.stock_inicial or 0
        stock_create = StockLocalCreate(
            local_id=tenant_context.local_id,
            producto_id=product.id,
            cantidad=stock_inicial,
            stock_minimo=0,
            stock_maximo=None,
            costo_promedio=product.precio_base
        )
        
        initial_stock = stock_repo.create(stock_create)
        
        print(f"✅ Stock inicial creado para producto {product.sku} en local {tenant_context.local_id}")
        
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
    summary="Listar productos por contexto local",
    description="Obtiene una lista paginada de productos filtrada por el contexto local seleccionado.",
    responses={
        200: {"description": "Lista de productos obtenida exitosamente"},
        422: {"description": "Error de validación en parámetros de consulta"},
        400: {"description": "Se requiere seleccionar un contexto local"}
    }
)
async def list_products(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Productos por página"),
    search: Optional[str] = Query(None, description="Buscar por nombre o SKU"),
    only_active: bool = Query(True, description="Solo productos activos"),
    todos_los_locales: bool = Query(False, description="Mostrar productos de todos los locales (requiere permisos de administrador/gerente)"),
    product_repo: SQLProductRepository = Depends(get_product_repository),
    current_user: User = Depends(get_current_user_sync),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> ProductListResponse:
    """
    Listar productos filtrados por contexto local con información de stock específica.
    
    - **page**: Número de página (empezando en 1)
    - **limit**: Número de productos por página (máximo 100)
    - **search**: Término de búsqueda por nombre o SKU
    - **only_active**: Si solo mostrar productos activos
    - **todos_los_locales**: Mostrar productos de todos los locales (solo administradores/gerentes)
    
    NOTA: Debe seleccionar un local para ver productos con información de stock.
    """
    try:
        # Verificar que hay contexto de local o permiso para ver todos
        if not todos_los_locales and not tenant_context.tiene_contexto_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe seleccionar un local para ver productos con stock"
            )
        
        # Verificar permisos para ver todos los locales
        if todos_los_locales:
            if current_user.rol not in [UserRole.ADMINISTRADOR, UserRole.GERENTE_VENTAS]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para ver productos de todos los locales"
                )
        
        # Verificar que el usuario tiene tienda asignada
        if not current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene tienda asignada"
            )
        
        # Usar el local_id del contexto del usuario
        local_id = tenant_context.local_id
        
        # Obtener productos con filtrado local-específico
        from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
        stock_repo = StockLocalRepository(session)
        
        if todos_los_locales:
            # Mostrar productos de todos los locales de la tienda
            products_with_stock = await _get_products_all_locals(
                stock_repo, current_user.tienda_id, page, limit, search, only_active
            )
        else:
            # Mostrar solo productos del local específico
            products_with_stock = await _get_products_by_local(
                stock_repo, local_id, page, limit, search, only_active
            )
        
        # Construir respuesta con paginación correcta
        total_pages = (products_with_stock['total'] + limit - 1) // limit
        response = ProductListResponse(
            products=products_with_stock['products'],
            total=products_with_stock['total'],
            page=page,
            limit=limit,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Obtener producto por ID con información de stock",
    description="Obtiene un producto específico por su ID único con información de stock local.",
    responses={
        200: {"description": "Producto encontrado"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        422: {"description": "ID de producto inválido"}
    }
)
async def get_product(
    product_id: UUID,
    product_repo: SQLProductRepository = Depends(get_product_repository),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> ProductResponse:
    """
    Obtener un producto por su ID con información de stock local.
    
    - **product_id**: UUID único del producto
    """
    try:
        use_case = GetProductUseCase(product_repo)
        product = await use_case.execute(product_id)
        
        # Calcular información de stock usando el contexto local del usuario
        from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
        stock_repo = StockLocalRepository(session)
        
        # Verificar que hay contexto de local
        if not tenant_context.tiene_contexto_local:
            raise HTTPException(
                status_code=400, 
                detail="Debe seleccionar un local para ver información de stock del producto"
            )
        
        local_id = tenant_context.local_id
        
        # Obtener stock local
        stock_local = stock_repo.get_by_producto_and_local(product_id, local_id)
        
        # Crear respuesta con información de stock
        product_response = ProductResponse(
            id=product.id,
            sku=product.sku,
            nombre=product.nombre,
            descripcion=product.descripcion,
            url_foto=product.url_foto,
            precio_base=product.precio_base,
            precio_publico=product.precio_publico,
            tienda_id=product.tienda_id,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            # Información de stock local
            stock_local_actual=stock_local.cantidad if stock_local else 0,
            stock_total_tienda=stock_local.cantidad if stock_local else 0,
            valor_total_inventario=stock_local.valor_total_inventario if stock_local else Decimal("0.00"),
            locales_con_stock=[local_id] if stock_local and stock_local.cantidad > 0 else [],
            costo_promedio_local=stock_local.costo_promedio if stock_local else Decimal("0.00"),
            local_id=str(local_id),
            local_nombre=tenant_context.local_nombre
        )
        
        return product_response
        
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
    summary="Actualizar stock de producto en local actual",
    description="Actualiza el stock de un producto en el local actual del usuario. Requiere local_id como header o parámetro.",
    responses={
        200: {"description": "Stock actualizado exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        400: {"model": ErrorResponse, "description": "Stock inválido (no puede ser negativo)"},
        403: {"model": ErrorResponse, "description": "Sin contexto de local válido"}
    }
)
async def update_product_stock(
    product_id: UUID,
    stock_data: ProductStockUpdateRequest,
    local_id: Optional[UUID] = Query(None, description="ID del local donde actualizar el stock"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_sync)
) -> ProductStockUpdateResponse:
    """
    Actualizar el stock de un producto en un local específico.
    
    - **product_id**: UUID único del producto
    - **stock**: Nueva cantidad de stock (no puede ser negativo) 
    - **local_id**: ID del local donde actualizar el stock (requerido)
    """
    try:
        # Verificar que se proporciona local_id
        if not local_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se requiere local_id para actualizar stock. Use el selector de contexto para elegir un local."
            )
        
        # Verificar que el usuario tiene tienda asignada
        if not current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene tienda asignada"
            )
        
        # Verificar que el producto existe y pertenece a la tienda del usuario
        product_repo = SQLProductRepository(session)
        product = await product_repo.get_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        if product.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado en su tienda"
            )
        
        # Verificar que el local pertenece a la tienda del usuario
        from app.infrastructure.repositories.local_repository import LocalRepository
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(local_id)
        
        if not local or local.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local no válido para su tienda"
            )
        
        # Obtener o crear stock en el local especificado
        from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
        from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
        from app.domain.models.stock_local import StockLocalCreate
        from app.domain.models.movimiento_inventario import MovimientoInventarioCreate, TipoMovimiento
        
        stock_repo = StockLocalRepository(session)
        inventario_repo = SQLInventarioRepository(session, product_repo, stock_repo)
        
        stock_local = stock_repo.get_by_producto_and_local(product_id, local_id)
        
        previous_stock = 0
        if stock_local:
            previous_stock = stock_local.cantidad
        else:
            # Crear nuevo stock en el local si no existe
            stock_create = StockLocalCreate(
                local_id=local_id,
                producto_id=product_id,
                cantidad=0,  # Empezar con 0, el movimiento de inventario lo ajustará
                stock_minimo=0,
                stock_maximo=None,
                costo_promedio=product.precio_base
            )
            stock_repo.create(stock_create)
            previous_stock = 0
        
        # IMPORTANTE: Usar el sistema de movimientos de inventario para la actualización
        # Esto garantiza que el kardex tenga registro de todos los cambios
        diferencia = stock_data.stock - previous_stock
        
        if diferencia != 0:
            # Crear movimiento de inventario de tipo AJUSTE
            tipo_movimiento = TipoMovimiento.AJUSTE
            cantidad_movimiento = abs(diferencia)
            
            # Si la diferencia es negativa, es una salida (ajuste negativo)
            if diferencia < 0:
                tipo_movimiento = TipoMovimiento.SALIDA
            
            movimiento_data = MovimientoInventarioCreate(
                producto_id=product_id,
                local_id=local_id,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad_movimiento,
                precio_unitario=product.precio_publico,
                costo_unitario=product.precio_base,
                referencia=f"Ajuste manual de stock",
                observaciones=f"Ajuste de stock: {previous_stock} → {stock_data.stock} (diferencia: {diferencia:+})"
            )
            
            # Crear el movimiento que automáticamente actualizará el stock_local
            await inventario_repo.create_movimiento(movimiento_data, current_user.id)
        
        # Obtener el stock actualizado después del movimiento
        updated_stock_local = stock_repo.get_by_producto_and_local(product_id, local_id)
        final_stock = updated_stock_local.cantidad if updated_stock_local else stock_data.stock
        
        return ProductStockUpdateResponse(
            product_id=product_id,
            previous_stock=previous_stock,
            new_stock=final_stock,
            message=f"Stock actualizado de {previous_stock} a {final_stock} en {local.nombre} (con movimiento de inventario registrado)"
        )
        
    except HTTPException:
        raise
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


# ============================================================================
# HELPER FUNCTIONS FOR LOCAL-CONTEXT AWARE PRODUCT FILTERING
# ============================================================================

async def _get_products_by_local(
    stock_repo,
    local_id: UUID,
    page: int,
    limit: int,
    search: Optional[str],
    only_active: bool
) -> dict:
    """
    Obtiene productos que tienen stock registrado en un local específico.
    Solo devuelve productos que existen en el local seleccionado.
    """
    from sqlmodel import select, and_, or_
    from sqlalchemy import func
    from app.domain.models.stock_local import StockLocal
    from app.domain.models.product import Product
    
    # Base query para productos con stock en el local específico
    query = (
        select(Product, StockLocal)
        .join(StockLocal, Product.id == StockLocal.producto_id)
        .where(StockLocal.local_id == local_id)
    )
    
    if only_active:
        query = query.where(Product.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Product.nombre.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        )
    
    # Contar total de productos - usar la misma query base pero con count
    count_query = (
        select(func.count(Product.id))
        .join(StockLocal, Product.id == StockLocal.producto_id)
        .where(StockLocal.local_id == local_id)
    )
    
    if only_active:
        count_query = count_query.where(Product.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            or_(
                Product.nombre.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        )
    
    # Ejecutar consulta de conteo
    total = stock_repo.session.scalar(count_query) or 0
    
    # Aplicar paginación
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit).order_by(Product.created_at.desc())
    
    result = stock_repo.session.exec(query)
    products_with_stock = list(result.all())
    
    # Procesar resultados y crear objetos ProductResponse
    from app.domain.models.product import ProductResponse
    enriched_products = []
    
    for product, stock_local in products_with_stock:
        # Get local name directly from the database
        local_nombre = 'Local'
        try:
            from app.infrastructure.repositories.local_repository import LocalRepository
            local_repo = LocalRepository(stock_repo.session)
            local = local_repo.get_by_id(stock_local.local_id)
            local_nombre = local.nombre if local else 'Local'
        except Exception:
            pass
        
        # Get stock total de tienda
        stock_total_tienda = stock_local.cantidad
        try:
            stock_total_tienda = stock_repo.get_stock_global_producto(product.id)['stock_total']
        except Exception:
            pass
        
        # Crear ProductResponse con todos los campos
        product_response = ProductResponse(
            id=product.id,
            sku=product.sku,
            nombre=product.nombre,
            descripcion=product.descripcion,
            url_foto=product.url_foto,
            precio_base=product.precio_base,
            precio_publico=product.precio_publico,
            tienda_id=product.tienda_id,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            # Campos de stock local-específico
            stock_local_actual=stock_local.cantidad,
            stock_total_tienda=stock_total_tienda,
            valor_total_inventario=stock_local.valor_total_inventario,
            locales_con_stock=[stock_local.local_id],
            costo_promedio_local=stock_local.costo_promedio,
            local_id=str(stock_local.local_id),
            local_nombre=local_nombre,
            locales_stock=[]
        )
        
        enriched_products.append(product_response)
    
    return {
        'products': enriched_products,
        'total': total
    }


async def _get_basic_product_list(
    product_repo,
    tienda_id: Optional[UUID],
    page: int,
    limit: int,
    search: Optional[str],
    only_active: bool
) -> dict:
    """
    Obtiene productos básicos sin información detallada de stock local.
    Útil para listados generales que no requieren contexto local específico.
    """
    from app.application.use_cases.product_use_cases import ListProductsUseCase
    from app.domain.models.product import ProductResponse
    
    try:
        # Usar el use case estándar para obtener productos básicos
        use_case = ListProductsUseCase(product_repo)
        
        # Obtener productos usando el use case - este ya retorna ProductListResponse
        product_list_response = await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            only_active=only_active
        )
        
        # Modificar los productos para mostrar que no tienen contexto local
        basic_products = []
        for product in product_list_response.products:
            # Crear nuevo ProductResponse con información básica
            product_response = ProductResponse(
                id=product.id,
                sku=product.sku,
                nombre=product.nombre,
                descripcion=product.descripcion,
                url_foto=product.url_foto,
                precio_base=product.precio_base,
                precio_publico=product.precio_publico,
                tienda_id=product.tienda_id,
                is_active=product.is_active,
                created_at=product.created_at,
                updated_at=product.updated_at,
                # Campos de stock básicos (sin información local específica)
                stock_local_actual=0,  # No disponible sin contexto local
                stock_total_tienda=0,  # Requiere cálculo agregado
                valor_total_inventario=0,
                locales_con_stock=[],
                costo_promedio_local=0,
                local_id=None,
                local_nombre="Sin contexto local",
                locales_stock=[]
            )
            basic_products.append(product_response)
        
        return ProductListResponse(
            products=basic_products,
            total=product_list_response.total,
            page=product_list_response.page,
            limit=product_list_response.limit,
            has_next=product_list_response.has_next,
            has_prev=product_list_response.has_prev
        )
        
    except Exception as e:
        # Si hay error, devolver lista vacía para no fallar completamente
        return ProductListResponse(
            products=[],
            total=0,
            page=page,
            limit=limit,
            has_next=False,
            has_prev=False
        )
