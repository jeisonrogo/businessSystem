"""
Endpoints para gestión de tiendas en el sistema multi-tenant.

Proporciona operaciones CRUD para tiendas, incluyendo estadísticas
y operaciones específicas del negocio.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.tienda_repository import TiendaRepository
from app.infrastructure.middleware.tenant_middleware import (
    get_tenant_context,
    require_permission
)
from app.infrastructure.auth.auth_dependency import get_current_user
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.api.v1.schemas_multi_tenant import (
    TiendaCreate,
    TiendaUpdate, 
    TiendaResponse,
    TiendaEstadisticas,
    PaginatedResponse,
    ErrorResponse
)

router = APIRouter(
    prefix="/tiendas",
    tags=["Tiendas Multi-Tenant"]
)


@router.post(
    "/",
    response_model=TiendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva tienda",
    description="Crea una nueva tienda en el sistema multi-tenant. Requiere permisos de administrador."
)
def crear_tienda(
    tienda_data: TiendaCreate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("admin"))
):
    """
    Crea una nueva tienda en el sistema.
    
    - **codigo**: Código único de la tienda (2-20 caracteres)
    - **nombre**: Nombre descriptivo de la tienda (3-255 caracteres)
    - **descripcion**: Descripción opcional de la tienda
    - **dominio**: Dominio para acceso multi-tenant (opcional)
    - **prefijo_facturas**: Prefijo para numeración de facturas (default: "F")
    - **consecutivo_facturas**: Número inicial para facturas (default: 1)
    """
    try:
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.create(tienda_data)
        return tienda
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear la tienda"
        )


@router.get(
    "/",
    response_model=List[TiendaResponse],
    summary="Listar tiendas",
    description="Obtiene la lista de todas las tiendas del sistema con paginación opcional."
)
def listar_tiendas(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    include_inactive: bool = Query(False, description="Incluir tiendas inactivas"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la lista de tiendas del usuario actual.
    
    Los usuarios solo pueden ver su tienda asignada.
    """
    try:
        tienda_repo = TiendaRepository(session)
        
        # Si el usuario no tiene tienda asignada, devolver lista vacía
        if not current_user.tienda_id:
            return []
        
        # Obtener solo la tienda del usuario actual
        tienda = tienda_repo.get_by_id(current_user.tienda_id)
        if not tienda or (not include_inactive and not tienda.is_active):
            return []
        
        tiendas = [tienda]
        
        # Convertir a TiendaResponse con total_locales calculado
        tiendas_response = []
        try:
            from app.infrastructure.repositories.local_repository import LocalRepository
            local_repo = LocalRepository(session)
            
            for tienda in tiendas:
                tienda_data = tienda.model_dump()
                try:
                    # Calcular total de locales reales
                    locales_count = local_repo.count_by_tienda(tienda.id)
                    tienda_data['total_locales'] = locales_count
                except Exception as e:
                    # Si falla el conteo, asignar 0
                    tienda_data['total_locales'] = 0
                tiendas_response.append(TiendaResponse(**tienda_data))
        except Exception as e:
            # Si falla completamente, asignar 0 a todas
            for tienda in tiendas:
                tienda_data = tienda.model_dump()
                tienda_data['total_locales'] = 0
                tiendas_response.append(TiendaResponse(**tienda_data))
        
        return tiendas_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener las tiendas: {str(e)}"
        )


@router.get(
    "/activas",
    response_model=List[TiendaResponse],
    summary="Listar tiendas activas",
    description="Obtiene solo las tiendas activas del sistema."
)
def listar_tiendas_activas(
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene todas las tiendas activas.
    
    Endpoint público para usuarios autenticados.
    """
    try:
        tienda_repo = TiendaRepository(session)
        tiendas = tienda_repo.get_tiendas_activas()
        return tiendas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener las tiendas activas"
        )


@router.get(
    "/{tienda_id}",
    response_model=TiendaResponse,
    summary="Obtener tienda por ID",
    description="Obtiene los datos de una tienda específica por su ID."
)
def obtener_tienda(
    tienda_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene una tienda específica por ID.
    
    Los usuarios pueden ver solo su tienda asignada, 
    los administradores pueden ver cualquier tienda.
    """
    try:
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.get_by_id(tienda_id)
        
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        # Validar acceso: usuarios solo pueden ver su tienda
        if tenant_context.user_rol != "ADMINISTRADOR":
            if tienda.id != tenant_context.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a esta tienda"
                )
        
        return tienda
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la tienda"
        )


@router.get(
    "/codigo/{codigo}",
    response_model=TiendaResponse,
    summary="Obtener tienda por código",
    description="Obtiene los datos de una tienda por su código único."
)
def obtener_tienda_por_codigo(
    codigo: str,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene una tienda por su código único.
    """
    try:
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.get_by_codigo(codigo)
        
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        # Validar acceso
        if tenant_context.user_rol != "ADMINISTRADOR":
            if tienda.id != tenant_context.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a esta tienda"
                )
        
        return tienda
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la tienda"
        )


@router.put(
    "/{tienda_id}",
    response_model=TiendaResponse,
    summary="Actualizar tienda",
    description="Actualiza los datos de una tienda existente."
)
def actualizar_tienda(
    tienda_id: UUID,
    tienda_data: TiendaUpdate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("admin"))
):
    """
    Actualiza una tienda existente.
    
    Solo administradores pueden actualizar tiendas.
    """
    try:
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.update(tienda_id, tienda_data)
        
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        return tienda
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
            detail="Error interno al actualizar la tienda"
        )


@router.delete(
    "/{tienda_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar tienda",
    description="Desactiva una tienda del sistema (eliminación suave)."
)
def eliminar_tienda(
    tienda_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("admin"))
):
    """
    Elimina (desactiva) una tienda.
    
    Solo administradores pueden eliminar tiendas.
    La eliminación es suave (marca como inactiva).
    """
    try:
        tienda_repo = TiendaRepository(session)
        eliminado = tienda_repo.delete(tienda_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar la tienda"
        )


@router.get(
    "/{tienda_id}/estadisticas",
    response_model=TiendaEstadisticas,
    summary="Estadísticas de tienda",
    description="Obtiene estadísticas básicas de una tienda (locales, productos, usuarios)."
)
def obtener_estadisticas_tienda(
    tienda_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene estadísticas básicas de una tienda.
    
    Incluye conteos de locales, productos y usuarios.
    """
    try:
        # Validar acceso a la tienda
        if tenant_context.user_rol != "ADMINISTRADOR":
            if tienda_id != tenant_context.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para ver estadísticas de esta tienda"
                )
        
        tienda_repo = TiendaRepository(session)
        
        # Verificar que la tienda existe
        tienda = tienda_repo.get_by_id(tienda_id)
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        # Obtener estadísticas
        estadisticas = tienda_repo.get_estadisticas_tienda(tienda_id)
        
        return TiendaEstadisticas(
            tienda_id=tienda_id,
            **estadisticas
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener las estadísticas"
        )


@router.post(
    "/{tienda_id}/generar-numero-factura",
    response_model=dict,
    summary="Generar número de factura",
    description="Genera el siguiente número consecutivo de factura para la tienda."
)
def generar_numero_factura(
    tienda_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("venta"))
):
    """
    Genera el siguiente número consecutivo de factura.
    
    Requiere permisos de venta en la tienda.
    """
    try:
        # Validar acceso a la tienda
        if tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede generar facturas para esta tienda"
            )
        
        tienda_repo = TiendaRepository(session)
        numero_factura = tienda_repo.incrementar_consecutivo_factura(tienda_id)
        
        if not numero_factura:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        return {
            "numero_factura": numero_factura,
            "tienda_id": str(tienda_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar número de factura"
        )


@router.get(
    "/{tienda_id}/with-locales",
    response_model=TiendaResponse,
    summary="Obtener tienda con locales",
    description="Obtiene una tienda junto con todos sus locales asociados."
)
def obtener_tienda_con_locales(
    tienda_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene una tienda con sus locales cargados.
    """
    try:
        # Validar acceso
        if tenant_context.user_rol != "ADMINISTRADOR":
            if tienda_id != tenant_context.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para acceder a esta tienda"
                )
        
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.get_with_locales(tienda_id)
        
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tienda no encontrada"
            )
        
        return tienda
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la tienda con locales"
        )


@router.get(
    "/verificar-codigo/{codigo}",
    response_model=dict,
    summary="Verificar disponibilidad de código",
    description="Verifica si un código de tienda está disponible."
)
def verificar_codigo_disponible(
    codigo: str,
    tienda_id: Optional[UUID] = Query(None, description="ID de tienda a excluir (para updates)"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("admin"))
):
    """
    Verifica si un código de tienda está disponible.
    
    Útil para validaciones en frontend antes de crear/actualizar.
    """
    try:
        tienda_repo = TiendaRepository(session)
        disponible = tienda_repo.verificar_codigo_disponible(codigo, tienda_id)
        
        return {
            "codigo": codigo,
            "disponible": disponible
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el código"
        )