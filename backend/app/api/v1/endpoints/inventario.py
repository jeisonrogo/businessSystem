"""
Endpoints para la gestión de inventario.
Implementa las operaciones para movimientos de inventario, kardex y estadísticas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.api.v1.schemas import (
    MovimientoInventarioCreateRequest,
    MovimientoInventarioResponse,
    MovimientoInventarioListResponse,
    KardexResponse,
    InventarioResumenResponse,
    EstadisticasInventarioResponse,
    ValidarStockRequest,
    ValidarStockResponse,
    MovimientoInventarioFilterRequest,
    ErrorResponse,
    MessageResponse,
    TipoMovimiento,
    MovimientoInventarioFilter
)
from app.application.use_cases.inventario_use_cases import (
    RegistrarMovimientoUseCase,
    ConsultarKardexUseCase,
    ListarMovimientosUseCase,
    ObtenerResumenInventarioUseCase,
    ObtenerEstadisticasInventarioUseCase,
    ValidarStockUseCase,
    RecalcularCostosUseCase,
    ObtenerMovimientoPorIdUseCase,
    InventarioError,
    StockInsuficienteError,
    ProductoNoEncontradoError,
    MovimientoInvalidoError
)
from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.middleware.tenant_middleware import get_tenant_context
from app.domain.models.tenant_context import TenantContext
from app.infrastructure.auth.auth_dependency import get_current_user
from app.domain.models.user import User

router = APIRouter()


# Funciones de dependencia
def get_inventario_repository(session: Session = Depends(get_session)) -> SQLInventarioRepository:
    """Crear instancia del repositorio de inventario."""
    from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
    product_repository = SQLProductRepository(session)
    stock_local_repository = StockLocalRepository(session)
    return SQLInventarioRepository(session, product_repository, stock_local_repository)


def get_product_repository(session: Session = Depends(get_session)) -> SQLProductRepository:
    """Crear instancia del repositorio de productos."""
    return SQLProductRepository(session)


@router.post(
    "/movimientos/",
    response_model=MovimientoInventarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar movimiento de inventario",
    description="Registra un nuevo movimiento de inventario (entrada, salida, merma o ajuste) aplicando cálculo de costo promedio ponderado.",
    responses={
        201: {"description": "Movimiento registrado exitosamente"},
        400: {"model": ErrorResponse, "description": "Error de validación o stock insuficiente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        422: {"description": "Error de validación de datos"}
    }
)
async def registrar_movimiento(
    movimiento_data: MovimientoInventarioCreateRequest,
    tenant_context: TenantContext = Depends(get_tenant_context),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository)
) -> MovimientoInventarioResponse:
    """
    Registrar un nuevo movimiento de inventario.

    - **producto_id**: UUID del producto (requerido)
    - **tipo_movimiento**: Tipo de movimiento (entrada, salida, merma, ajuste)
    - **cantidad**: Cantidad del movimiento (positiva)
    - **precio_unitario**: Precio unitario de compra/venta
    - **referencia**: Referencia del movimiento (factura, orden, etc.)
    - **observaciones**: Observaciones adicionales

    **Reglas de negocio aplicadas:**
    - BR-01: Stock no puede ser negativo
    - BR-11: Cálculo de costo promedio ponderado
    """
    try:
        # Verificar que se tenga un contexto de local seleccionado
        if not tenant_context.tiene_contexto_local:
            raise HTTPException(
                status_code=400, 
                detail="Debe seleccionar un local para registrar movimientos de inventario. Use el selector de contexto local."
            )
        
        # Asegurar que el movimiento tenga el local_id del contexto seleccionado
        if not movimiento_data.local_id:
            movimiento_data.local_id = tenant_context.local_id
        elif movimiento_data.local_id != tenant_context.local_id:
            raise HTTPException(
                status_code=400,
                detail="El local del movimiento debe coincidir con el local seleccionado en el contexto."
            )
        
        # Validación final: asegurar que el movimiento tenga un local_id válido
        if not movimiento_data.local_id:
            raise HTTPException(
                status_code=400,
                detail="No se pudo determinar el local para el movimiento. Verifique el contexto de local seleccionado."
            )
        
        use_case = RegistrarMovimientoUseCase(inventario_repo, product_repo)
        # TODO: Obtener created_by del usuario autenticado
        movimiento = await use_case.execute(movimiento_data, created_by=None)
        return MovimientoInventarioResponse.model_validate(movimiento)
    except ProductoNoEncontradoError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except StockInsuficienteError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except MovimientoInvalidoError as e:
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
    "/movimientos/",
    response_model=MovimientoInventarioListResponse,
    summary="Listar movimientos de inventario",
    description="Obtiene una lista paginada de movimientos de inventario con filtros opcionales.",
    responses={
        200: {"description": "Lista de movimientos obtenida exitosamente"},
        422: {"description": "Error de validación en parámetros de consulta"}
    }
)
async def listar_movimientos(
    request: Request,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Movimientos por página"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    tipo_movimiento: Optional[TipoMovimiento] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    referencia: Optional[str] = Query(None, description="Filtrar por referencia"),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> MovimientoInventarioListResponse:
    """
    Listar movimientos de inventario con filtros y paginación.

    - **page**: Número de página (empezando en 1)
    - **limit**: Número de movimientos por página (máximo 100)
    - **producto_id**: Filtrar por producto específico
    - **tipo_movimiento**: Filtrar por tipo (entrada, salida, merma, ajuste)
    - **fecha_desde**: Filtrar desde esta fecha
    - **fecha_hasta**: Filtrar hasta esta fecha
    - **referencia**: Filtrar por referencia
    """
    try:
        # Determinar local_id basado en el contexto
        # Si hay contexto local específico, filtrar por ese local
        # Si no hay contexto local (opción "Toda la tienda"), no filtrar por local
        filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None
        
        # Construir filtros
        filtros = MovimientoInventarioFilter(
            producto_id=producto_id,
            tipo_movimiento=tipo_movimiento,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            referencia=referencia,
            local_id=filter_local_id
        )

        use_case = ListarMovimientosUseCase(inventario_repo, product_repo)
        return await use_case.execute(page=page, limit=limit, filtros=filtros)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/movimientos/{movimiento_id}",
    response_model=MovimientoInventarioResponse,
    summary="Obtener movimiento por ID",
    description="Obtiene un movimiento específico por su ID único.",
    responses={
        200: {"description": "Movimiento encontrado"},
        404: {"model": ErrorResponse, "description": "Movimiento no encontrado"},
        422: {"description": "ID de movimiento inválido"}
    }
)
async def obtener_movimiento(
    movimiento_id: UUID,
    request: Request,
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository)
) -> MovimientoInventarioResponse:
    """
    Obtener un movimiento por su ID.

    - **movimiento_id**: UUID único del movimiento
    """
    try:
        use_case = ObtenerMovimientoPorIdUseCase(inventario_repo)
        movimiento = await use_case.execute(movimiento_id)
        return MovimientoInventarioResponse.model_validate(movimiento)
    except InventarioError as e:
        if "no encontrado" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
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
    "/kardex/{producto_id}",
    response_model=KardexResponse,
    summary="Consultar kardex de producto",
    description="Obtiene el kardex (historial de movimientos) de un producto específico.",
    responses={
        200: {"description": "Kardex obtenido exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        422: {"description": "ID de producto inválido"}
    }
)
async def consultar_kardex(
    producto_id: UUID,
    request: Request,
    skip: int = Query(0, ge=0, description="Número de movimientos a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de movimientos"),
    tipo_movimiento: Optional[TipoMovimiento] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> KardexResponse:
    """
    Consultar el kardex de un producto.

    - **producto_id**: UUID único del producto
    - **skip**: Número de movimientos a omitir (para paginación)
    - **limit**: Número máximo de movimientos a retornar
    - **tipo_movimiento**: Filtrar por tipo de movimiento
    - **fecha_desde**: Filtrar desde esta fecha
    - **fecha_hasta**: Filtrar hasta esta fecha

    **Información incluida:**
    - Historial de movimientos del producto
    - Stock actual calculado
    - Costo promedio actual
    - Valor total del inventario
    """
    try:
        # Determinar local_id basado en el contexto
        # Si hay contexto local específico, filtrar por ese local
        # Si no hay contexto local (opción "Toda la tienda"), no filtrar por local
        filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None
        
        use_case = ConsultarKardexUseCase(inventario_repo, product_repo)
        return await use_case.execute(
            producto_id=producto_id,
            skip=skip,
            limit=limit,
            tipo_movimiento=tipo_movimiento,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            local_id=filter_local_id
        )
    except ProductoNoEncontradoError as e:
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
    "/resumen/",
    response_model=InventarioResumenResponse,
    summary="Obtener resumen de inventario",
    description="Obtiene un resumen general del inventario con estadísticas básicas.",
    responses={
        200: {"description": "Resumen obtenido exitosamente"}
    }
)
async def obtener_resumen_inventario(
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> InventarioResumenResponse:
    """
    Obtener resumen general del inventario.

    **Información incluida:**
    - Total de productos en el sistema
    - Valor total del inventario
    - Productos sin stock
    - Productos con stock bajo
    - Fecha del último movimiento
    """
    try:
        use_case = ObtenerResumenInventarioUseCase(inventario_repo, product_repo)
        return await use_case.execute(tenant_context)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.get(
    "/estadisticas/",
    response_model=EstadisticasInventarioResponse,
    summary="Obtener estadísticas de inventario",
    description="Obtiene estadísticas detalladas de inventario para un período específico.",
    responses={
        200: {"description": "Estadísticas obtenidas exitosamente"}
    }
)
async def obtener_estadisticas_inventario(
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde (default: inicio del mes)"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta (default: ahora)"),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    tenant_context: TenantContext = Depends(get_tenant_context)
) -> EstadisticasInventarioResponse:
    """
    Obtener estadísticas detalladas del inventario.

    - **fecha_desde**: Fecha desde para el cálculo (default: inicio del mes actual)
    - **fecha_hasta**: Fecha hasta para el cálculo (default: ahora)

    **Información incluida:**
    - Total de entradas, salidas y mermas en el período
    - Valor monetario de movimientos por tipo
    - Productos más movidos en el período
    """
    try:
        # Determinar local_id basado en el contexto
        filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None
        
        use_case = ObtenerEstadisticasInventarioUseCase(inventario_repo)
        return await use_case.execute(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, local_id=filter_local_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/validar-stock/",
    response_model=ValidarStockResponse,
    summary="Validar disponibilidad de stock",
    description="Valida si hay stock suficiente para una operación específica.",
    responses={
        200: {"description": "Validación realizada exitosamente"},
        400: {"model": ErrorResponse, "description": "Error de validación"},
        422: {"description": "Error de validación de datos"}
    }
)
async def validar_stock(
    validacion_data: ValidarStockRequest,
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository)
) -> ValidarStockResponse:
    """
    Validar disponibilidad de stock para una operación.

    - **producto_id**: UUID del producto
    - **cantidad_requerida**: Cantidad que se necesita

    **Información de respuesta:**
    - Stock actual del producto
    - Si hay stock suficiente
    - Cantidad disponible después de la operación
    """
    try:
        use_case = ValidarStockUseCase(inventario_repo)
        resultado = await use_case.execute(
            validacion_data.producto_id, 
            validacion_data.cantidad_requerida
        )
        return ValidarStockResponse(**resultado)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post(
    "/recalcular-costos/{producto_id}",
    response_model=MessageResponse,
    summary="Recalcular costos promedio de producto",
    description="Recalcula todos los costos promedio de un producto (útil para correcciones).",
    responses={
        200: {"description": "Costos recalculados exitosamente"},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        422: {"description": "ID de producto inválido"}
    }
)
async def recalcular_costos_producto(
    producto_id: UUID,
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository)
) -> MessageResponse:
    """
    Recalcular todos los costos promedio de un producto.

    - **producto_id**: UUID único del producto

    **Nota:** Esta operación recalcula secuencialmente todos los movimientos
    del producto para corregir inconsistencias en los costos promedio.
    """
    try:
        use_case = RecalcularCostosUseCase(inventario_repo)
        success = await use_case.execute(producto_id)
        
        if success:
            return MessageResponse(
                message=f"Costos promedio del producto {producto_id} recalculados exitosamente"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudieron recalcular los costos"
            )
    except InventarioError as e:
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
    "/movimientos/export/excel",
    summary="Exportar movimientos a Excel",
    description="Exporta la lista de movimientos de inventario a formato Excel (.xlsx) con formato profesional.",
    responses={
        200: {"description": "Archivo Excel generado", "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    }
)
async def export_movements_excel(
    request: Request,
    limit: int = Query(100, description="Número máximo de movimientos a incluir"),
    page: int = Query(1, description="Número de página"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto específico"),
    tipo_movimiento: Optional[TipoMovimiento] = Query(None, description="Filtrar por tipo de movimiento"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha de inicio del filtro"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha de fin del filtro"),
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository)
):
    """
    Exportar movimientos de inventario a Excel.

    - **limit**: Número máximo de movimientos (máximo 1000)
    - **page**: Número de página para paginación
    - **producto_id**: UUID del producto para filtrar (opcional)
    - **tipo_movimiento**: Tipo específico de movimiento (opcional)
    - **fecha_desde**: Fecha de inicio del período (opcional)
    - **fecha_hasta**: Fecha de fin del período (opcional)

    Genera un archivo Excel con formato profesional que incluye:
    - Títulos en negrita con colores corporativos
    - Filas alternadas para mejor legibilidad
    - Ajuste automático de columnas
    - Formato de moneda y fechas apropiado
    """
    try:
        from app.utils.excel_export import ExcelExporter, create_excel_response

        # Validar límite
        if limit > 1000:
            limit = 1000

        # Determinar filtro de local
        filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None

        # Crear filtros
        filters = MovimientoInventarioFilter(
            local_id=filter_local_id,
            producto_id=producto_id,
            tipo_movimiento=tipo_movimiento,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )

        # Obtener movimientos
        use_case = ListarMovimientosUseCase(inventario_repo, product_repo)
        result = await use_case.execute(
            page=page,
            limit=limit,
            filtros=filters
        )

        # Convertir a diccionarios para el exportador
        movements_data = []
        for movement in result.movimientos:
            movement_dict = {
                'id': str(movement.id),
                'created_at': movement.created_at.isoformat(),
                'tipo_movimiento': movement.tipo_movimiento,
                'cantidad': movement.cantidad,
                'precio_unitario': movement.precio_unitario,
                'costo_unitario': movement.costo_unitario,
                'stock_anterior': movement.stock_anterior,
                'stock_posterior': movement.stock_posterior,
                'referencia': movement.referencia,
                'observaciones': movement.observaciones,
                'producto': {
                    'nombre': movement.producto.nombre if movement.producto else 'N/A',
                    'sku': movement.producto.sku if movement.producto else 'N/A'
                }
            }
            movements_data.append(movement_dict)

        # Generar Excel
        exporter = ExcelExporter()
        excel_file = exporter.export_movements_to_excel(movements_data)

        # Crear nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"movimientos_inventario_{timestamp}.xlsx"

        return create_excel_response(excel_file, filename)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando archivo Excel: {str(e)}"
        )


@router.get(
    "/kardex/{producto_id}/export/excel",
    summary="Exportar kardex a Excel",
    description="Exporta el kardex de un producto específico a formato Excel (.xlsx) con formato profesional.",
    responses={
        200: {"description": "Archivo Excel generado", "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        404: {"model": ErrorResponse, "description": "Producto no encontrado"},
        500: {"model": ErrorResponse, "description": "Error interno del servidor"}
    }
)
async def export_kardex_excel(
    producto_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    tenant_context: TenantContext = Depends(get_tenant_context),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository)
):
    """
    Exportar kardex de producto a Excel.

    - **producto_id**: UUID único del producto

    Genera un archivo Excel con formato profesional que incluye:
    - Información resumida del producto
    - Títulos en negrita con colores corporativos
    - Historial completo de movimientos
    - Filas alternadas para mejor legibilidad
    - Ajuste automático de columnas
    - Formato de moneda y fechas apropiado
    """
    try:
        from app.utils.excel_export import ExcelExporter, create_excel_response

        # Determinar filtro de local
        filter_local_id = tenant_context.local_id if tenant_context.tiene_contexto_local else None

        # Obtener kardex
        use_case = ConsultarKardexUseCase(inventario_repo, product_repo)
        kardex = await use_case.execute(
            producto_id=producto_id,
            skip=0,
            limit=1000,
            tipo_movimiento=None,
            fecha_desde=None,
            fecha_hasta=None,
            local_id=filter_local_id
        )

        # Obtener información del producto
        product = await product_repo.get_by_id(producto_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )

        # Convertir kardex a diccionario
        kardex_data = {
            'stock_actual': kardex.stock_actual,
            'costo_promedio_actual': kardex.costo_promedio_actual,
            'valor_inventario': kardex.valor_inventario,
            'total_movimientos': kardex.total_movimientos,
            'movimientos': []
        }

        # Convertir movimientos
        for movement in kardex.movimientos:
            movement_dict = {
                'created_at': movement.created_at.isoformat(),
                'tipo_movimiento': movement.tipo_movimiento,
                'cantidad': movement.cantidad,
                'precio_unitario': movement.precio_unitario,
                'costo_unitario': movement.costo_unitario,
                'stock_anterior': movement.stock_anterior,
                'stock_posterior': movement.stock_posterior,
                'referencia': movement.referencia,
                'observaciones': movement.observaciones
            }
            kardex_data['movimientos'].append(movement_dict)

        # Generar Excel
        exporter = ExcelExporter()
        excel_file = exporter.export_kardex_to_excel(kardex_data, product)

        # Crear nombre de archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"kardex_{product.sku}_{timestamp}.xlsx"

        return create_excel_response(excel_file, filename)

    except ProductoNoEncontradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando archivo Excel: {str(e)}"
        )