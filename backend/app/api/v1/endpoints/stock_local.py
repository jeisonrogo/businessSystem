"""
Endpoints para gestión de stock por local en el sistema multi-tenant.

Proporciona operaciones para inventario independiente por local incluyendo
ajustes, consultas, estadísticas y operaciones de stock con costo promedio.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.infrastructure.middleware.tenant_middleware import (
    get_tenant_context,
    require_local_context,
    require_permission
)
from app.domain.models.tenant_context import TenantContext
from app.api.v1.schemas_multi_tenant import (
    StockLocalCreate,
    StockLocalUpdate,
    StockLocalAjuste,
    StockLocalResponse,
    StockLocalResumen,
    ErrorResponse
)

router = APIRouter(
    prefix="/stock-local",
    tags=["Stock por Local"]
)


@router.post(
    "/",
    response_model=StockLocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear stock inicial en local",
    description="Crea un registro de stock inicial para un producto en un local específico."
)
def crear_stock_local(
    stock_data: StockLocalCreate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Crea stock inicial para un producto en un local.
    
    - **producto_id**: ID del producto
    - **local_id**: ID del local donde crear el stock
    - **cantidad**: Cantidad inicial de stock
    - **stock_minimo**: Stock mínimo requerido
    - **stock_maximo**: Stock máximo permitido (opcional)
    - **costo_promedio**: Costo promedio inicial del producto
    """
    try:
        # Validar que el local pertenece a la tienda del usuario
        if not tenant_context.puede_ver_stock_local(stock_data.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para crear stock en este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.create(stock_data)
        return stock
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el stock"
        )


@router.get(
    "/local/{local_id}",
    response_model=List[StockLocalResponse],
    summary="Listar stock de un local",
    description="Obtiene todo el inventario de un local específico con paginación."
)
def listar_stock_por_local(
    local_id: UUID,
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    incluir_sin_stock: bool = Query(True, description="Incluir productos sin stock"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene todo el stock de un local específico.
    
    Requiere permisos de consulta de stock en el local.
    """
    try:
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver stock de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock_items = stock_repo.get_by_local(
            local_id,
            skip=skip,
            limit=limit,
            incluir_sin_stock=incluir_sin_stock
        )
        return stock_items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el stock del local"
        )


@router.get(
    "/producto/{producto_id}",
    response_model=List[StockLocalResponse],
    summary="Stock de producto en todos los locales",
    description="Obtiene el stock de un producto específico en todos los locales de la tienda."
)
def obtener_stock_producto_global(
    producto_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene el stock de un producto en todos los locales de la tienda.
    
    Solo muestra locales donde el usuario tiene permisos de consulta.
    """
    try:
        stock_repo = StockLocalRepository(session)
        all_stock = stock_repo.get_by_producto(producto_id)
        
        # Filtrar solo locales donde el usuario tiene permisos
        stock_permitido = [
            stock for stock in all_stock
            if tenant_context.puede_ver_stock_local(stock.local_id)
        ]
        
        return stock_permitido
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el stock del producto"
        )


@router.get(
    "/tienda",
    response_model=List[StockLocalResponse],
    summary="Stock de toda la tienda",
    description="Obtiene todo el stock de la tienda (todos los locales) con paginación."
)
def listar_stock_tienda(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todo el stock de la tienda con paginación.
    
    Requiere permisos de reportes para ver stock global.
    """
    try:
        stock_repo = StockLocalRepository(session)
        stock_items = stock_repo.get_by_tienda(
            tenant_context.tienda_id,
            skip=skip,
            limit=limit
        )
        return stock_items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el stock de la tienda"
        )


@router.get(
    "/{stock_id}",
    response_model=StockLocalResponse,
    summary="Obtener stock por ID",
    description="Obtiene un registro específico de stock por su ID."
)
def obtener_stock_por_id(
    stock_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene un registro de stock específico por ID.
    """
    try:
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.get_by_id(stock_id)
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de stock no encontrado"
            )
        
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(stock.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este stock"
            )
        
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el registro de stock"
        )


@router.get(
    "/producto/{producto_id}/local/{local_id}",
    response_model=StockLocalResponse,
    summary="Stock específico producto-local",
    description="Obtiene el stock de un producto específico en un local específico."
)
def obtener_stock_producto_local(
    producto_id: UUID,
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene el stock de un producto en un local específico.
    """
    try:
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver stock de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.get_by_producto_and_local(producto_id, local_id)
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe stock para este producto en el local"
            )
        
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el stock producto-local"
        )


@router.put(
    "/{stock_id}/configuracion",
    response_model=StockLocalResponse,
    summary="Actualizar configuración de stock",
    description="Actualiza la configuración de stock (mínimos, máximos) sin afectar cantidad."
)
def actualizar_configuracion_stock(
    stock_id: UUID,
    stock_data: StockLocalUpdate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Actualiza solo la configuración de stock (mínimos y máximos).
    
    No afecta la cantidad actual ni el costo promedio.
    """
    try:
        stock_repo = StockLocalRepository(session)
        
        # Verificar que existe y validar permisos
        stock_existente = stock_repo.get_by_id(stock_id)
        if not stock_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de stock no encontrado"
            )
        
        if not tenant_context.puede_ver_stock_local(stock_existente.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar este stock"
            )
        
        stock = stock_repo.update_configuracion(stock_id, stock_data)
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar la configuración"
        )


@router.put(
    "/producto/{producto_id}/local/{local_id}/ajustar",
    response_model=StockLocalResponse,
    summary="Ajustar stock manualmente",
    description="Realiza un ajuste manual de stock con nueva cantidad y/o costo."
)
def ajustar_stock(
    producto_id: UUID,
    local_id: UUID,
    ajuste_data: StockLocalAjuste,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_local_context)
):
    """
    Ajusta manualmente el stock de un producto en un local.
    
    Permite cambiar cantidad y costo promedio con auditoría.
    Requiere contexto de local específico.
    """
    try:
        # Validar que el contexto actual es del local correcto
        if tenant_context.local_id != local_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe estar en contexto del local para hacer ajustes"
            )
        
        # Validar permisos de gestión en el local
        if not tenant_context.validar_operacion_en_contexto_actual("gestion_stock"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ajustar stock en este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.actualizar_stock(
            producto_id,
            local_id,
            ajuste_data.nueva_cantidad,
            ajuste_data.nuevo_costo,
            tenant_context.user_id
        )
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe stock para este producto en el local"
            )
        
        return stock
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al ajustar el stock"
        )


@router.post(
    "/producto/{producto_id}/local/{local_id}/incrementar",
    response_model=StockLocalResponse,
    summary="Incrementar stock",
    description="Incrementa el stock con cálculo de costo promedio ponderado."
)
def incrementar_stock(
    producto_id: UUID,
    local_id: UUID,
    cantidad: int = Query(..., gt=0, description="Cantidad a incrementar"),
    costo_unitario: Optional[float] = Query(None, ge=0, description="Costo unitario del incremento"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_local_context)
):
    """
    Incrementa el stock con cálculo automático de costo promedio.
    
    Si se proporciona costo_unitario, recalcula el promedio ponderado.
    """
    try:
        # Validar contexto y permisos
        if tenant_context.local_id != local_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe estar en contexto del local para incrementar stock"
            )
        
        if not tenant_context.validar_operacion_en_contexto_actual("gestion_stock"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para incrementar stock en este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.incrementar_stock(
            producto_id,
            local_id,
            cantidad,
            costo_unitario,
            tenant_context.user_id
        )
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe stock para este producto en el local"
            )
        
        return stock
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al incrementar el stock"
        )


@router.post(
    "/producto/{producto_id}/local/{local_id}/decrementar",
    response_model=StockLocalResponse,
    summary="Decrementar stock",
    description="Decrementa el stock manteniendo el costo promedio."
)
def decrementar_stock(
    producto_id: UUID,
    local_id: UUID,
    cantidad: int = Query(..., gt=0, description="Cantidad a decrementar"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_local_context)
):
    """
    Decrementa el stock manteniendo el costo promedio actual.
    
    Valida que hay stock suficiente antes de decrementar.
    """
    try:
        # Validar contexto y permisos
        if tenant_context.local_id != local_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe estar en contexto del local para decrementar stock"
            )
        
        if not tenant_context.validar_operacion_en_contexto_actual("venta"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para decrementar stock en este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock = stock_repo.decrementar_stock(
            producto_id,
            local_id,
            cantidad,
            tenant_context.user_id
        )
        
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existe stock para este producto en el local"
            )
        
        return stock
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al decrementar el stock"
        )


@router.delete(
    "/{stock_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar registro de stock",
    description="Elimina un registro de stock (solo si cantidad = 0)."
)
def eliminar_stock(
    stock_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Elimina un registro de stock.
    
    Solo permite eliminar registros con cantidad = 0.
    """
    try:
        stock_repo = StockLocalRepository(session)
        
        # Verificar que existe y validar permisos
        stock_existente = stock_repo.get_by_id(stock_id)
        if not stock_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de stock no encontrado"
            )
        
        if not tenant_context.puede_ver_stock_local(stock_existente.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para eliminar este stock"
            )
        
        eliminado = stock_repo.delete(stock_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de stock no encontrado"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar el stock"
        )


# ============ ENDPOINTS DE CONSULTAS ESPECIALES ============

@router.get(
    "/local/{local_id}/bajo-minimo",
    response_model=List[StockLocalResponse],
    summary="Productos bajo stock mínimo",
    description="Obtiene productos con stock por debajo del mínimo en un local."
)
def obtener_productos_bajo_minimo(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene productos con stock bajo mínimo en un local.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver stock de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        productos_bajo_minimo = stock_repo.get_productos_bajo_minimo(local_id)
        return productos_bajo_minimo
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener productos bajo mínimo"
        )


@router.get(
    "/local/{local_id}/agotados",
    response_model=List[StockLocalResponse],
    summary="Productos agotados",
    description="Obtiene productos agotados (cantidad = 0) en un local."
)
def obtener_productos_agotados(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene productos agotados en un local.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver stock de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        productos_agotados = stock_repo.get_productos_agotados(local_id)
        return productos_agotados
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener productos agotados"
        )


@router.get(
    "/local/{local_id}/resumen",
    response_model=StockLocalResumen,
    summary="Resumen de inventario por local",
    description="Obtiene un resumen completo del inventario de un local."
)
def obtener_resumen_inventario_local(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene resumen completo de inventario de un local.
    
    Incluye totales, productos con/sin stock, bajo mínimo, etc.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver resumen de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        resumen = stock_repo.get_resumen_por_local(local_id)
        
        return StockLocalResumen(
            local_id=local_id,
            **resumen
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el resumen de inventario"
        )


@router.get(
    "/producto/{producto_id}/global",
    response_model=dict,
    summary="Stock global de producto",
    description="Obtiene el stock global de un producto en todos los locales."
)
def obtener_stock_global_producto(
    producto_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene el stock global de un producto con totales y promedios.
    """
    try:
        stock_repo = StockLocalRepository(session)
        stock_global = stock_repo.get_stock_global_producto(producto_id)
        
        # Filtrar solo locales donde el usuario tiene permisos
        stock_por_local_filtrado = [
            stock for stock in stock_global["stock_por_local"]
            if tenant_context.puede_ver_stock_local(stock.local_id)
        ]
        
        # Recalcular totales con stock filtrado
        stock_total_filtrado = sum(stock.cantidad for stock in stock_por_local_filtrado)
        valor_total_filtrado = sum(stock.valor_total_inventario for stock in stock_por_local_filtrado)
        
        return {
            "producto_id": str(producto_id),
            "stock_total": stock_total_filtrado,
            "stock_por_local": stock_por_local_filtrado,
            "costo_promedio_global": stock_global["costo_promedio_global"],
            "valor_total_global": float(valor_total_filtrado)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el stock global del producto"
        )


@router.get(
    "/buscar",
    response_model=List[StockLocalResponse],
    summary="Buscar productos con stock",
    description="Busca productos con stock por nombre o SKU en la tienda."
)
def buscar_productos_con_stock(
    texto: str = Query(..., min_length=2, description="Texto a buscar"),
    local_id: Optional[UUID] = Query(None, description="Local específico (opcional)"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Busca productos con stock por nombre o SKU.
    
    Si se especifica local_id, busca solo en ese local.
    """
    try:
        # Validar permisos en local específico si se proporciona
        if local_id and not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para buscar en este local"
            )
        
        stock_repo = StockLocalRepository(session)
        productos = stock_repo.buscar_productos_con_stock(
            tenant_context.tienda_id,
            texto,
            local_id
        )
        
        # Si no se especificó local, filtrar por permisos
        if not local_id:
            productos = [
                producto for producto in productos
                if tenant_context.puede_ver_stock_local(producto.local_id)
            ]
        
        return productos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar productos"
        )


@router.get(
    "/validar-disponibilidad/producto/{producto_id}/local/{local_id}",
    response_model=dict,
    summary="Validar stock disponible",
    description="Valida si hay stock suficiente para una operación."
)
def validar_stock_disponible(
    producto_id: UUID,
    local_id: UUID,
    cantidad: int = Query(..., gt=0, description="Cantidad requerida"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Valida si hay stock suficiente para una operación.
    
    Útil antes de realizar ventas o transferencias.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para consultar stock de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        stock_suficiente = stock_repo.validar_stock_disponible(
            producto_id,
            local_id,
            cantidad
        )
        
        # Obtener stock actual para información adicional
        stock_actual = stock_repo.get_by_producto_and_local(producto_id, local_id)
        cantidad_actual = stock_actual.cantidad if stock_actual else 0
        
        return {
            "producto_id": str(producto_id),
            "local_id": str(local_id),
            "cantidad_requerida": cantidad,
            "cantidad_disponible": cantidad_actual,
            "stock_suficiente": stock_suficiente
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al validar stock disponible"
        )