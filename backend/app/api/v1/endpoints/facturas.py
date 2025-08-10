"""
Endpoints API para la gestión de facturas.

Proporciona endpoints REST para operaciones CRUD de facturas,
incluyendo reportes, estadísticas y gestión de estados.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.application.use_cases.factura_use_cases import (
    CreateFacturaUseCase,
    GetFacturaUseCase,
    GetFacturaByNumeroUseCase,
    ListFacturasUseCase,
    UpdateFacturaUseCase,
    AnularFacturaUseCase,
    MarcarFacturaPagadaUseCase,
    GetFacturasVencidasUseCase,
    GetFacturasPorClienteUseCase,
    GetResumenVentasUseCase,
    GetProductosMasVendidosUseCase,
    GetClientesTopUseCase,
    GetValorCarteraUseCase,
    GetEstadisticasFacturacionUseCase,
    # Excepciones
    FacturaNotFoundError,
    ClienteNotFoundForFacturaError,
    ProductoNotFoundForFacturaError,
    StockInsuficienteError,
    FacturaStateError,
    InvalidFacturaDataError,
    FacturaError
)
from app.application.services.i_factura_repository import IFacturaRepository
from app.application.services.i_cliente_repository import IClienteRepository
from app.application.services.i_product_repository import IProductRepository
from app.infrastructure.repositories.factura_repository import SQLFacturaRepository
from app.infrastructure.repositories.cliente_repository import SQLClienteRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository
from app.infrastructure.repositories.asiento_contable_repository import SQLAsientoContableRepository
from app.domain.models.facturacion import (
    Factura,
    FacturaCreate,
    FacturaUpdate,
    FacturaResponse,
    FacturaListResponse,
    FacturaListItem,
    EstadoFactura,
    TipoFactura
)
from app.infrastructure.database.session import get_session
from app.api.v1.endpoints.auth import get_current_user
from app.domain.models.user import User
from sqlmodel import Session

router = APIRouter(tags=["Facturas"])


def get_factura_repository(session: Session = Depends(get_session)) -> IFacturaRepository:
    """Dependencia para obtener el repositorio de facturas."""
    return SQLFacturaRepository(session)


def get_cliente_repository(session: Session = Depends(get_session)) -> IClienteRepository:
    """Dependencia para obtener el repositorio de clientes."""
    return SQLClienteRepository(session)


def get_product_repository(session: Session = Depends(get_session)) -> IProductRepository:
    """Dependencia para obtener el repositorio de productos."""
    return SQLProductRepository(session)


def get_cuenta_repository(session: Session = Depends(get_session)):
    """Dependencia para obtener el repositorio de cuentas contables."""
    return SQLCuentaContableRepository(session)


def get_asiento_repository(session: Session = Depends(get_session)):
    """Dependencia para obtener el repositorio de asientos contables."""
    return SQLAsientoContableRepository(session)


@router.post("/", response_model=FacturaResponse, status_code=201)
async def crear_factura(
    factura_data: FacturaCreate,
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository),
    cliente_repo: IClienteRepository = Depends(get_cliente_repository),
    product_repo: IProductRepository = Depends(get_product_repository),
    cuenta_repo = Depends(get_cuenta_repository),
    asiento_repo = Depends(get_asiento_repository)
):
    """
    Crear una nueva factura.
    
    - **cliente_id**: ID del cliente
    - **tipo_factura**: Tipo de factura (VENTA, SERVICIO)
    - **fecha_emision**: Fecha de emisión
    - **fecha_vencimiento**: Fecha de vencimiento (opcional)
    - **observaciones**: Observaciones adicionales (opcional)
    - **detalles**: Lista de productos/servicios facturados
    """
    try:
        use_case = CreateFacturaUseCase(
            factura_repo, cliente_repo, product_repo,
            cuenta_repo, asiento_repo  # Integración contable
        )
        factura = await use_case.execute(factura_data, current_user.id)
        return factura
    
    except ClienteNotFoundForFacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ProductoNotFoundForFacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except StockInsuficienteError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidFacturaDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/{factura_id}", response_model=FacturaResponse)
async def obtener_factura(
    factura_id: UUID,
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener una factura por su ID."""
    try:
        use_case = GetFacturaUseCase(factura_repo)
        factura = await use_case.execute(factura_id)
        return FacturaResponse.from_factura(factura)
    
    except FacturaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/numero/{numero_factura}", response_model=FacturaResponse)
async def obtener_factura_por_numero(
    numero_factura: str,
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener una factura por su número."""
    try:
        use_case = GetFacturaByNumeroUseCase(factura_repo)
        factura = await use_case.execute(numero_factura)
        return FacturaResponse.from_factura(factura)
    
    except FacturaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/", response_model=FacturaListResponse)
async def listar_facturas(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Registros por página"),
    cliente_id: Optional[UUID] = Query(None, description="Filtrar por cliente"),
    estado: Optional[EstadoFactura] = Query(None, description="Filtrar por estado"),
    tipo_factura: Optional[TipoFactura] = Query(None, description="Filtrar por tipo"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    search: Optional[str] = Query(None, description="Búsqueda en número/cliente"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """
    Listar facturas con paginación y filtros.
    
    - **page**: Número de página (inicia en 1)
    - **limit**: Número de registros por página (máximo 100)
    - **cliente_id**: Filtrar por cliente específico
    - **estado**: Filtrar por estado (EMITIDA, PAGADA, ANULADA)
    - **tipo_factura**: Filtrar por tipo (VENTA, SERVICIO)
    - **fecha_desde**: Filtrar desde fecha
    - **fecha_hasta**: Filtrar hasta fecha
    - **search**: Buscar en número de factura y datos del cliente
    """
    try:
        use_case = ListFacturasUseCase(factura_repo)
        result = await use_case.execute(
            page=page,
            limit=limit,
            cliente_id=cliente_id,
            estado=estado,
            tipo_factura=tipo_factura,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            search=search
        )
        
        # Transformar facturas a FacturaListItem
        facturas_transformadas = [
            FacturaListItem.from_factura(factura)
            for factura in result["facturas"]
        ]
        
        return FacturaListResponse(
            facturas=facturas_transformadas,
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.put("/{factura_id}", response_model=FacturaResponse)
async def actualizar_factura(
    factura_id: UUID,
    factura_data: FacturaUpdate,
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """
    Actualizar una factura existente.
    
    Nota: Solo se pueden modificar facturas en estado EMITIDA.
    """
    try:
        use_case = UpdateFacturaUseCase(factura_repo)
        factura = await use_case.execute(factura_id, factura_data)
        return factura
    
    except FacturaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FacturaStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.delete("/{factura_id}")
async def anular_factura(
    factura_id: UUID,
    motivo: str = Query("Anulación de factura", description="Motivo de anulación"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository),
    cuenta_repo = Depends(get_cuenta_repository),
    asiento_repo = Depends(get_asiento_repository)
):
    """
    Anular una factura.
    
    Cambia el estado a ANULADA y revierte el stock de los productos.
    """
    try:
        use_case = AnularFacturaUseCase(
            factura_repo, cuenta_repo, asiento_repo  # Integración contable
        )
        await use_case.execute(factura_id, motivo, current_user.id)
        return {"message": "Factura anulada exitosamente"}
    
    except FacturaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FacturaStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/{factura_id}/marcar-pagada")
async def marcar_factura_pagada(
    factura_id: UUID,
    forma_pago: str = Query("EFECTIVO", description="Forma de pago"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository),
    cuenta_repo = Depends(get_cuenta_repository),
    asiento_repo = Depends(get_asiento_repository)
):
    """Marcar una factura como pagada."""
    try:
        use_case = MarcarFacturaPagadaUseCase(
            factura_repo, cuenta_repo, asiento_repo  # Integración contable
        )
        await use_case.execute(factura_id, None, forma_pago, current_user.id)
        return {"message": "Factura marcada como pagada exitosamente"}
    
    except FacturaNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FacturaStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FacturaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/vencidas/lista", response_model=List[FacturaResponse])
async def obtener_facturas_vencidas(
    fecha_corte: Optional[date] = Query(None, description="Fecha de corte"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener facturas vencidas que no han sido pagadas."""
    try:
        use_case = GetFacturasVencidasUseCase(factura_repo)
        facturas = await use_case.execute(fecha_corte)
        return facturas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/cliente/{cliente_id}/lista", response_model=dict)
async def obtener_facturas_por_cliente(
    cliente_id: UUID,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Registros por página"),
    estado: Optional[EstadoFactura] = Query(None, description="Filtrar por estado"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener facturas de un cliente específico."""
    try:
        use_case = GetFacturasPorClienteUseCase(factura_repo)
        result = await use_case.execute(cliente_id, page, limit, estado)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# Endpoints de Reportes y Estadísticas

@router.get("/reportes/resumen-ventas", response_model=dict)
async def obtener_resumen_ventas(
    fecha_desde: date = Query(..., description="Fecha inicial del período"),
    fecha_hasta: date = Query(..., description="Fecha final del período"),
    cliente_id: Optional[UUID] = Query(None, description="Cliente específico"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener resumen de ventas para un período.
    
    Incluye totales de facturas, ventas, impuestos y promedios.
    """
    try:
        use_case = GetResumenVentasUseCase(factura_repo)
        resumen = await use_case.execute(fecha_desde, fecha_hasta, cliente_id)
        return resumen
    
    except InvalidFacturaDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/productos-mas-vendidos", response_model=List[dict])
async def obtener_productos_mas_vendidos(
    fecha_desde: date = Query(..., description="Fecha inicial del período"),
    fecha_hasta: date = Query(..., description="Fecha final del período"),
    limit: int = Query(10, ge=1, le=50, description="Número de productos"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener los productos más vendidos en un período."""
    try:
        use_case = GetProductosMasVendidosUseCase(factura_repo)
        productos = await use_case.execute(fecha_desde, fecha_hasta, limit)
        return productos
    
    except InvalidFacturaDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/clientes-top", response_model=List[dict])
async def obtener_clientes_top(
    fecha_desde: date = Query(..., description="Fecha inicial del período"),
    fecha_hasta: date = Query(..., description="Fecha final del período"),
    limit: int = Query(10, ge=1, le=50, description="Número de clientes"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """Obtener los clientes con más compras/facturación en un período."""
    try:
        use_case = GetClientesTopUseCase(factura_repo)
        clientes = await use_case.execute(fecha_desde, fecha_hasta, limit)
        return clientes
    
    except InvalidFacturaDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/valor-cartera", response_model=dict)
async def obtener_valor_cartera(
    cliente_id: Optional[UUID] = Query(None, description="Cliente específico"),
    solo_vencida: bool = Query(False, description="Solo cartera vencida"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener valor de cartera (facturas pendientes).
    
    Calcula el valor total de las facturas pendientes de pago.
    """
    try:
        use_case = GetValorCarteraUseCase(factura_repo)
        cartera = await use_case.execute(cliente_id, solo_vencida)
        return cartera
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/reportes/estadisticas-completas", response_model=dict)
async def obtener_estadisticas_facturacion(
    fecha_desde: date = Query(..., description="Fecha inicial del período"),
    fecha_hasta: date = Query(..., description="Fecha final del período"),
    current_user: User = Depends(get_current_user),
    factura_repo: IFacturaRepository = Depends(get_factura_repository)
):
    """
    Obtener estadísticas completas de facturación.
    
    Incluye resumen de ventas, productos más vendidos, clientes top,
    cartera total y cartera vencida.
    """
    try:
        use_case = GetEstadisticasFacturacionUseCase(factura_repo)
        estadisticas = await use_case.execute(fecha_desde, fecha_hasta)
        return estadisticas
    
    except InvalidFacturaDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/configuracion/validar-integracion-contable", response_model=dict)
async def validar_integracion_contable(
    current_user: User = Depends(get_current_user),
    cuenta_repo = Depends(get_cuenta_repository),
    asiento_repo = Depends(get_asiento_repository)
):
    """
    Validar configuración de integración contable.
    
    Verifica que todas las cuentas contables necesarias estén configuradas
    para la integración automática de facturas.
    """
    try:
        from app.application.services.integracion_contable_service import IntegracionContableService
        
        servicio_integracion = IntegracionContableService(cuenta_repo, asiento_repo)
        resultado = await servicio_integracion.validar_cuentas_configuradas()
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")