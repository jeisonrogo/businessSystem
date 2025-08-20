"""
Endpoints para gestión de locales en el sistema multi-tenant.

Proporciona operaciones CRUD para locales dentro de tiendas,
incluyendo búsquedas, estadísticas y gestión de usuarios por local.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.middleware.tenant_middleware import (
    get_tenant_context,
    require_local_context,
    require_permission
)
from app.domain.models.tenant_context import TenantContext
from app.api.v1.schemas_multi_tenant import (
    LocalCreate,
    LocalUpdate,
    LocalResponse,
    LocalEstadisticas,
    ErrorResponse
)

router = APIRouter(
    prefix="/locales",
    tags=["Locales Multi-Tenant"]
)


@router.post(
    "/",
    response_model=LocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo local",
    description="Crea un nuevo local dentro de una tienda. Requiere permisos de gestión de usuarios."
)
def crear_local(
    local_data: LocalCreate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Crea un nuevo local en la tienda.
    
    - **tienda_id**: ID de la tienda propietaria
    - **codigo**: Código único del local dentro de la tienda
    - **nombre**: Nombre descriptivo del local
    - **direccion**: Dirección física del local (opcional)
    - **ciudad**: Ciudad donde se ubica (opcional)
    - **departamento**: Departamento/estado (opcional)
    - **telefono**: Teléfono de contacto (opcional)
    - **email**: Email de contacto (opcional)
    """
    try:
        # Validar que el local se cree en la tienda del usuario
        if local_data.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede crear locales en su tienda asignada"
            )
        
        local_repo = LocalRepository(session)
        local = local_repo.create(local_data)
        return local
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
            detail="Error interno al crear el local"
        )


@router.get(
    "/",
    response_model=List[LocalResponse],
    summary="Listar locales de la tienda",
    description="Obtiene todos los locales de la tienda del usuario con paginación opcional."
)
def listar_locales(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros a retornar"),
    include_inactive: bool = Query(False, description="Incluir locales inactivos"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene la lista de locales de la tienda del usuario.
    """
    try:
        local_repo = LocalRepository(session)
        locales = local_repo.get_by_tienda(
            tenant_context.tienda_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        return locales
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los locales"
        )


@router.get(
    "/activos",
    response_model=List[LocalResponse],
    summary="Listar locales activos de la tienda",
    description="Obtiene solo los locales activos de la tienda del usuario."
)
def listar_locales_activos(
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene todos los locales activos de la tienda.
    
    Endpoint útil para selecciones en frontend.
    """
    try:
        local_repo = LocalRepository(session)
        locales = local_repo.get_locales_activos_by_tienda(tenant_context.tienda_id)
        return locales
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los locales activos"
        )


@router.get(
    "/usuario",
    response_model=List[LocalResponse],
    summary="Locales donde el usuario tiene permisos",
    description="Obtiene los locales donde el usuario autenticado tiene permisos asignados."
)
def listar_locales_usuario(
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene los locales donde el usuario tiene permisos.
    
    Útil para mostrar opciones de local en el frontend.
    """
    try:
        local_repo = LocalRepository(session)
        locales = local_repo.get_locales_usuario(tenant_context.user_id)
        return locales
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los locales del usuario"
        )


@router.get(
    "/{local_id}",
    response_model=LocalResponse,
    summary="Obtener local por ID",
    description="Obtiene los datos de un local específico por su ID."
)
def obtener_local(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene un local específico por ID.
    
    Solo se pueden ver locales de la tienda del usuario.
    """
    try:
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(local_id)
        
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        # Validar que el local pertenece a la tienda del usuario
        if local.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este local"
            )
        
        return local
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el local"
        )


@router.get(
    "/codigo/{codigo}",
    response_model=LocalResponse,
    summary="Obtener local por código",
    description="Obtiene un local por su código único dentro de la tienda."
)
def obtener_local_por_codigo(
    codigo: str,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene un local por su código dentro de la tienda.
    """
    try:
        local_repo = LocalRepository(session)
        local = local_repo.get_by_codigo_and_tienda(codigo, tenant_context.tienda_id)
        
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        return local
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el local"
        )


@router.put(
    "/{local_id}",
    response_model=LocalResponse,
    summary="Actualizar local",
    description="Actualiza los datos de un local existente."
)
def actualizar_local(
    local_id: UUID,
    local_data: LocalUpdate,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Actualiza un local existente.
    
    Requiere permisos de gestión de usuarios.
    """
    try:
        local_repo = LocalRepository(session)
        
        # Verificar que el local existe y pertenece a la tienda
        local_existente = local_repo.get_by_id(local_id)
        if not local_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        if local_existente.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede actualizar locales de otra tienda"
            )
        
        local = local_repo.update(local_id, local_data)
        return local
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
            detail="Error interno al actualizar el local"
        )


@router.delete(
    "/{local_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar local",
    description="Desactiva un local del sistema (eliminación suave)."
)
def eliminar_local(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Elimina (desactiva) un local.
    
    La eliminación es suave (marca como inactivo).
    """
    try:
        local_repo = LocalRepository(session)
        
        # Verificar que el local existe y pertenece a la tienda
        local_existente = local_repo.get_by_id(local_id)
        if not local_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        if local_existente.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede eliminar locales de otra tienda"
            )
        
        eliminado = local_repo.delete(local_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar el local"
        )


@router.get(
    "/{local_id}/estadisticas",
    response_model=LocalEstadisticas,
    summary="Estadísticas de local",
    description="Obtiene estadísticas básicas de un local (productos, stock, usuarios, transferencias)."
)
def obtener_estadisticas_local(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene estadísticas básicas de un local.
    
    Requiere permisos de consulta de stock en el local.
    """
    try:
        # Validar que el usuario puede ver stock en este local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver estadísticas de este local"
            )
        
        local_repo = LocalRepository(session)
        
        # Verificar que el local existe y pertenece a la tienda
        local = local_repo.get_by_id(local_id)
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        if local.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este local"
            )
        
        # Obtener estadísticas
        estadisticas = local_repo.get_estadisticas_local(local_id)
        
        return LocalEstadisticas(
            local_id=local_id,
            **estadisticas
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener las estadísticas del local"
        )


@router.get(
    "/{local_id}/transferencias-disponibles",
    response_model=List[LocalResponse],
    summary="Locales disponibles para transferencia",
    description="Obtiene los locales disponibles para transferir desde un local origen."
)
def obtener_locales_para_transferencia(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("transferencia"))
):
    """
    Obtiene locales disponibles para transferencia desde un local origen.
    
    Retorna todos los locales activos de la misma tienda excepto el origen.
    """
    try:
        # Validar que el usuario puede hacer transferencias desde este local
        if not tenant_context.puede_transferir_desde_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para transferir desde este local"
            )
        
        local_repo = LocalRepository(session)
        
        # Verificar que el local origen existe y pertenece a la tienda
        local_origen = local_repo.get_by_id(local_id)
        if not local_origen:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local origen no encontrado"
            )
        
        if local_origen.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede transferir desde locales de otra tienda"
            )
        
        # Obtener locales disponibles para transferencia
        locales_destino = local_repo.get_locales_para_transferencia(local_id)
        return locales_destino
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener locales para transferencia"
        )


@router.get(
    "/buscar",
    response_model=List[LocalResponse],
    summary="Buscar locales",
    description="Busca locales por texto en nombre, código o dirección con filtros opcionales."
)
def buscar_locales(
    texto: str = Query(..., min_length=2, description="Texto a buscar"),
    ciudad: Optional[str] = Query(None, description="Filtro por ciudad"),
    departamento: Optional[str] = Query(None, description="Filtro por departamento"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Busca locales por texto en nombre, código o dirección.
    
    Permite filtros adicionales por ciudad y departamento.
    """
    try:
        local_repo = LocalRepository(session)
        locales = local_repo.buscar_locales(
            tienda_id=tenant_context.tienda_id,
            texto_busqueda=texto,
            ciudad=ciudad,
            departamento=departamento
        )
        return locales
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar locales"
        )


@router.get(
    "/verificar-codigo/{codigo}",
    response_model=dict,
    summary="Verificar disponibilidad de código",
    description="Verifica si un código de local está disponible en la tienda."
)
def verificar_codigo_disponible(
    codigo: str,
    local_id: Optional[UUID] = Query(None, description="ID de local a excluir (para updates)"),
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Verifica si un código de local está disponible en la tienda.
    
    Útil para validaciones en frontend antes de crear/actualizar.
    """
    try:
        local_repo = LocalRepository(session)
        disponible = local_repo.verificar_codigo_disponible(
            codigo, 
            tenant_context.tienda_id,
            local_id
        )
        
        return {
            "codigo": codigo,
            "tienda_id": str(tenant_context.tienda_id),
            "disponible": disponible
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el código"
        )


@router.get(
    "/{local_id}/with-stock",
    response_model=LocalResponse,
    summary="Obtener local con stock",
    description="Obtiene un local junto con toda su información de stock asociado."
)
def obtener_local_con_stock(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("consulta_stock"))
):
    """
    Obtiene un local con su información de stock cargada.
    """
    try:
        # Validar permisos de stock en el local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver stock de este local"
            )
        
        local_repo = LocalRepository(session)
        local = local_repo.get_with_stock(local_id)
        
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        # Validar tienda
        if local.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este local"
            )
        
        return local
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el local con stock"
        )


@router.get(
    "/{local_id}/with-usuarios",
    response_model=LocalResponse,
    summary="Obtener local con usuarios",
    description="Obtiene un local junto con los usuarios que tienen permisos en él."
)
def obtener_local_con_usuarios(
    local_id: UUID,
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene un local con los usuarios que tienen permisos cargados.
    """
    try:
        local_repo = LocalRepository(session)
        local = local_repo.get_with_usuarios(local_id)
        
        if not local:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Local no encontrado"
            )
        
        # Validar tienda
        if local.tienda_id != tenant_context.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para acceder a este local"
            )
        
        return local
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el local con usuarios"
        )