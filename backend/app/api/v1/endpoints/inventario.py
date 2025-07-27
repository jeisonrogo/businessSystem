"""
Endpoints para la gestión de inventario.
Implementa las operaciones para movimientos de inventario, kardex y estadísticas.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
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

router = APIRouter()


# Funciones de dependencia
def get_inventario_repository(session: Session = Depends(get_session)) -> SQLInventarioRepository:
    """Crear instancia del repositorio de inventario."""
    product_repository = SQLProductRepository(session)
    return SQLInventarioRepository(session, product_repository)


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
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Movimientos por página"),
    producto_id: Optional[UUID] = Query(None, description="Filtrar por producto"),
    tipo_movimiento: Optional[TipoMovimiento] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    referencia: Optional[str] = Query(None, description="Filtrar por referencia"),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository)
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
        # Construir filtros
        filtros = MovimientoInventarioFilter(
            producto_id=producto_id,
            tipo_movimiento=tipo_movimiento,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            referencia=referencia
        )

        use_case = ListarMovimientosUseCase(inventario_repo)
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
    skip: int = Query(0, ge=0, description="Número de movimientos a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de movimientos"),
    tipo_movimiento: Optional[TipoMovimiento] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha hasta"),
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository),
    product_repo: SQLProductRepository = Depends(get_product_repository)
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
        use_case = ConsultarKardexUseCase(inventario_repo, product_repo)
        return await use_case.execute(
            producto_id=producto_id,
            skip=skip,
            limit=limit,
            tipo_movimiento=tipo_movimiento,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
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
    product_repo: SQLProductRepository = Depends(get_product_repository)
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
        return await use_case.execute()
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
    inventario_repo: SQLInventarioRepository = Depends(get_inventario_repository)
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
        use_case = ObtenerEstadisticasInventarioUseCase(inventario_repo)
        return await use_case.execute(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
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