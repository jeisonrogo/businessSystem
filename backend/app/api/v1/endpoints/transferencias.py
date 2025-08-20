"""
Endpoints para gestión de transferencias de inventario entre locales.

Proporciona el workflow completo de transferencias: solicitud → envío → recepción
con control de estados y actualizaciones automáticas de stock.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.transferencia_repository import TransferenciaRepository
from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
from app.infrastructure.middleware.tenant_middleware import (
    get_tenant_context,
    require_local_context,
    require_permission
)
from app.domain.models.tenant_context import TenantContext
from app.domain.models.transferencia import EstadoTransferencia
from app.api.v1.schemas_multi_tenant import (
    TransferenciaCreate,
    TransferenciaEnvio,
    TransferenciaRecepcion,
    TransferenciaCancelacion,
    TransferenciaResponse,
    TransferenciaEstadisticas,
    EstadoTransferenciaEnum,
    ErrorResponse
)

router = APIRouter(
    prefix="/transferencias",
    tags=["Transferencias de Inventario"]
)


@router.post(
    "/",
    response_model=TransferenciaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de transferencia",
    description="Crea una nueva solicitud de transferencia entre locales de la misma tienda."
)
async def crear_transferencia(
    transferencia_data: TransferenciaCreate,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Crea una nueva solicitud de transferencia.
    
    - **producto_id**: ID del producto a transferir
    - **local_origen_id**: Local desde donde se envía
    - **local_destino_id**: Local que recibirá
    - **cantidad_solicitada**: Cantidad a transferir
    - **usuario_solicita_id**: Usuario que solicita (automático)
    - **observaciones**: Notas adicionales (opcional)
    """
    try:
        # Validar que el usuario puede transferir desde el local origen
        if not tenant_context.puede_transferir_desde_local(transferencia_data.local_origen_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para transferir desde este local"
            )
        
        # El usuario que crea la transferencia es el que solicita
        transferencia_data.usuario_solicita_id = tenant_context.user_id
        
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        transferencia = await transferencia_repo.create(transferencia_data)
        return transferencia
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
            detail="Error interno al crear la transferencia"
        )


@router.get(
    "/",
    response_model=List[TransferenciaResponse],
    summary="Listar transferencias de la tienda",
    description="Obtiene todas las transferencias de la tienda con filtros opcionales."
)
async def listar_transferencias(
    estado: Optional[EstadoTransferenciaEnum] = Query(None, description="Filtro por estado"),
    fecha_desde: Optional[datetime] = Query(None, description="Fecha inicio del rango"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha fin del rango"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todas las transferencias de la tienda con filtros.
    
    Requiere permisos de reportes para ver todas las transferencias.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        # Convertir enum a domain enum si es necesario
        estado_domain = EstadoTransferencia(estado.value) if estado else None
        
        transferencias = await transferencia_repo.get_by_tienda(
            tenant_context.tienda_id,
            estado=estado_domain,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            skip=skip,
            limit=limit
        )
        return transferencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener las transferencias"
        )


@router.get(
    "/pendientes",
    response_model=List[TransferenciaResponse],
    summary="Transferencias pendientes",
    description="Obtiene todas las transferencias pendientes de la tienda."
)
async def listar_transferencias_pendientes(
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene todas las transferencias pendientes que requieren acción.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        transferencias = await transferencia_repo.get_transferencias_pendientes(
            tenant_context.tienda_id
        )
        return transferencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener transferencias pendientes"
        )


@router.get(
    "/en-transito",
    response_model=List[TransferenciaResponse],
    summary="Transferencias en tránsito",
    description="Obtiene todas las transferencias enviadas pero no recibidas."
)
async def listar_transferencias_en_transito(
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene transferencias que están en tránsito (enviadas pero no recibidas).
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        transferencias = await transferencia_repo.get_transferencias_en_transito(
            tenant_context.tienda_id
        )
        return transferencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener transferencias en tránsito"
        )


@router.get(
    "/{transferencia_id}",
    response_model=TransferenciaResponse,
    summary="Obtener transferencia por ID",
    description="Obtiene una transferencia específica por su ID."
)
async def obtener_transferencia(
    transferencia_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene una transferencia específica por ID.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        transferencia = await transferencia_repo.get_by_id(transferencia_id)
        
        if not transferencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        # Validar que el usuario tiene acceso a esta transferencia
        # (debe tener permisos en origen o destino)
        if not (tenant_context.puede_ver_stock_local(transferencia.local_origen_id) or
                tenant_context.puede_ver_stock_local(transferencia.local_destino_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta transferencia"
            )
        
        return transferencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la transferencia"
        )


@router.get(
    "/numero/{numero_transferencia}",
    response_model=TransferenciaResponse,
    summary="Obtener transferencia por número",
    description="Obtiene una transferencia por su número único."
)
async def obtener_transferencia_por_numero(
    numero_transferencia: str,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene una transferencia por su número único.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        transferencia = await transferencia_repo.get_by_numero(numero_transferencia)
        
        if not transferencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        # Validar acceso
        if not (tenant_context.puede_ver_stock_local(transferencia.local_origen_id) or
                tenant_context.puede_ver_stock_local(transferencia.local_destino_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta transferencia"
            )
        
        return transferencia
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la transferencia"
        )


@router.get(
    "/local/{local_id}/origen",
    response_model=List[TransferenciaResponse],
    summary="Transferencias desde un local",
    description="Obtiene transferencias que salen de un local específico."
)
async def listar_transferencias_origen(
    local_id: UUID,
    estado: Optional[EstadoTransferenciaEnum] = Query(None, description="Filtro por estado"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene transferencias que salen de un local específico.
    """
    try:
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver transferencias de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        estado_domain = EstadoTransferencia(estado.value) if estado else None
        
        transferencias = await transferencia_repo.get_by_local_origen(
            local_id,
            estado=estado_domain,
            skip=skip,
            limit=limit
        )
        return transferencias
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener transferencias del local origen"
        )


@router.get(
    "/local/{local_id}/destino",
    response_model=List[TransferenciaResponse],
    summary="Transferencias hacia un local",
    description="Obtiene transferencias que llegan a un local específico."
)
async def listar_transferencias_destino(
    local_id: UUID,
    estado: Optional[EstadoTransferenciaEnum] = Query(None, description="Filtro por estado"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene transferencias que llegan a un local específico.
    """
    try:
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver transferencias a este local"
            )
        
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        estado_domain = EstadoTransferencia(estado.value) if estado else None
        
        transferencias = await transferencia_repo.get_by_local_destino(
            local_id,
            estado=estado_domain,
            skip=skip,
            limit=limit
        )
        return transferencias
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener transferencias del local destino"
        )


@router.get(
    "/producto/{producto_id}",
    response_model=List[TransferenciaResponse],
    summary="Transferencias de un producto",
    description="Obtiene todas las transferencias de un producto específico en la tienda."
)
async def listar_transferencias_producto(
    producto_id: UUID,
    estado: Optional[EstadoTransferenciaEnum] = Query(None, description="Filtro por estado"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todas las transferencias de un producto específico.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        estado_domain = EstadoTransferencia(estado.value) if estado else None
        
        transferencias = await transferencia_repo.get_by_producto(
            producto_id,
            tenant_context.tienda_id,
            estado=estado_domain
        )
        return transferencias
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener transferencias del producto"
        )


# ============ ENDPOINTS DE WORKFLOW ============

@router.put(
    "/{transferencia_id}/enviar",
    response_model=TransferenciaResponse,
    summary="Marcar transferencia como enviada",
    description="Marca una transferencia como enviada y actualiza el stock del local origen."
)
async def enviar_transferencia(
    transferencia_id: UUID,
    envio_data: TransferenciaEnvio,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_local_context)
):
    """
    Marca una transferencia como enviada.
    
    - Actualiza stock del local origen (decrementa)
    - Cambia estado a ENVIADO
    - Registra usuario y fecha de envío
    
    Requiere contexto de local y permisos de transferencia.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        # Obtener la transferencia para validaciones
        transferencia_existente = await transferencia_repo.get_by_id(transferencia_id)
        if not transferencia_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        # Validar que el usuario puede enviar desde el local origen
        if not tenant_context.puede_transferir_desde_local(transferencia_existente.local_origen_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para enviar desde este local"
            )
        
        # Validar que está en el contexto del local origen
        if tenant_context.local_id != transferencia_existente.local_origen_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe estar en el contexto del local origen para enviar"
            )
        
        transferencia = await transferencia_repo.marcar_como_enviado(
            transferencia_id,
            envio_data.cantidad_enviada,
            tenant_context.user_id,
            envio_data.observaciones
        )
        
        if not transferencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        return transferencia
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
            detail="Error interno al enviar la transferencia"
        )


@router.put(
    "/{transferencia_id}/recibir",
    response_model=TransferenciaResponse,
    summary="Marcar transferencia como recibida",
    description="Marca una transferencia como recibida y actualiza el stock del local destino."
)
async def recibir_transferencia(
    transferencia_id: UUID,
    recepcion_data: TransferenciaRecepcion,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_local_context)
):
    """
    Marca una transferencia como recibida.
    
    - Actualiza stock del local destino (incrementa)
    - Cambia estado a RECIBIDO
    - Registra usuario y fecha de recepción
    
    Requiere contexto de local y permisos de transferencia.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        # Obtener la transferencia para validaciones
        transferencia_existente = await transferencia_repo.get_by_id(transferencia_id)
        if not transferencia_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        # Validar que el usuario puede recibir en el local destino
        if not tenant_context.puede_transferir_desde_local(transferencia_existente.local_destino_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para recibir en este local"
            )
        
        # Validar que está en el contexto del local destino
        if tenant_context.local_id != transferencia_existente.local_destino_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe estar en el contexto del local destino para recibir"
            )
        
        transferencia = await transferencia_repo.marcar_como_recibido(
            transferencia_id,
            recepcion_data.cantidad_recibida,
            tenant_context.user_id,
            recepcion_data.observaciones
        )
        
        if not transferencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        return transferencia
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
            detail="Error interno al recibir la transferencia"
        )


@router.put(
    "/{transferencia_id}/cancelar",
    response_model=TransferenciaResponse,
    summary="Cancelar transferencia",
    description="Cancela una transferencia y revierte el stock si es necesario."
)
async def cancelar_transferencia(
    transferencia_id: UUID,
    cancelacion_data: TransferenciaCancelacion,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Cancela una transferencia.
    
    - Si está en estado ENVIADO, revierte el stock del origen
    - Cambia estado a CANCELADO
    - Registra motivo de cancelación
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        # Obtener la transferencia para validaciones
        transferencia_existente = await transferencia_repo.get_by_id(transferencia_id)
        if not transferencia_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        # Validar que el usuario puede cancelar (debe tener permisos en origen o destino)
        if not (tenant_context.puede_transferir_desde_local(transferencia_existente.local_origen_id) or
                tenant_context.puede_transferir_desde_local(transferencia_existente.local_destino_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para cancelar esta transferencia"
            )
        
        transferencia = await transferencia_repo.cancelar_transferencia(
            transferencia_id,
            tenant_context.user_id,
            cancelacion_data.motivo_cancelacion
        )
        
        if not transferencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transferencia no encontrada"
            )
        
        return transferencia
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
            detail="Error interno al cancelar la transferencia"
        )


# ============ ENDPOINTS DE CONSULTAS Y ESTADÍSTICAS ============

@router.get(
    "/estadisticas",
    response_model=TransferenciaEstadisticas,
    summary="Estadísticas de transferencias",
    description="Obtiene estadísticas completas de transferencias de la tienda."
)
async def obtener_estadisticas_transferencias(
    fecha_desde: Optional[datetime] = Query(None, description="Fecha inicio del período"),
    fecha_hasta: Optional[datetime] = Query(None, description="Fecha fin del período"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene estadísticas completas de transferencias.
    
    Incluye conteos por estado, locales más activos, productos más transferidos, etc.
    """
    try:
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        estadisticas = await transferencia_repo.get_estadisticas_transferencias(
            tenant_context.tienda_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        
        return TransferenciaEstadisticas(
            tienda_id=tenant_context.tienda_id,
            **estadisticas
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener estadísticas de transferencias"
        )


@router.get(
    "/historial/producto/{producto_id}/local/{local_id}",
    response_model=List[TransferenciaResponse],
    summary="Historial de transferencias producto-local",
    description="Obtiene el historial completo de transferencias de un producto en un local."
)
async def obtener_historial_producto_local(
    producto_id: UUID,
    local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene el historial de transferencias de un producto en un local.
    
    Incluye tanto transferencias enviadas como recibidas.
    """
    try:
        # Validar permisos en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver historial de este local"
            )
        
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        historial = await transferencia_repo.get_historial_producto_local(
            producto_id,
            local_id
        )
        return historial
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el historial"
        )


@router.post(
    "/validar",
    response_model=dict,
    summary="Validar transferencia posible",
    description="Valida si una transferencia es posible antes de crearla."
)
async def validar_transferencia_posible(
    producto_id: UUID = Query(..., description="ID del producto"),
    local_origen_id: UUID = Query(..., description="ID del local origen"),
    local_destino_id: UUID = Query(..., description="ID del local destino"),
    cantidad: int = Query(..., gt=0, description="Cantidad a transferir"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Valida si una transferencia es posible.
    
    Verifica stock disponible, que los locales sean diferentes,
    que pertenezcan a la misma tienda, etc.
    """
    try:
        # Validar permisos en local origen
        if not tenant_context.puede_transferir_desde_local(local_origen_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para transferir desde el local origen"
            )
        
        stock_repo = StockLocalRepository(session)
        transferencia_repo = TransferenciaRepository(session, stock_repo)
        
        validacion = await transferencia_repo.validar_transferencia_posible(
            producto_id,
            local_origen_id,
            local_destino_id,
            cantidad
        )
        
        return {
            "producto_id": str(producto_id),
            "local_origen_id": str(local_origen_id),
            "local_destino_id": str(local_destino_id),
            "cantidad_solicitada": cantidad,
            **validacion
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al validar la transferencia"
        )