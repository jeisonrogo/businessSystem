"""
Endpoints para gestión del contexto de tenant.

Proporciona operaciones para obtener información del contexto actual,
cambiar entre locales, y consultar información de tenant disponible.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.middleware.tenant_middleware import get_tenant_context
from app.application.services.tenant_context_service import TenantContextService
from app.domain.models.tenant_context import TenantContext
from app.api.v1.schemas_multi_tenant import (
    TenantContextResponse,
    CambiarContextoRequest,
    LocalResponse
)

router = APIRouter(
    prefix="/tenant-context",
    tags=["Contexto de Tenant"]
)


@router.get(
    "/current",
    response_model=TenantContextResponse,
    summary="Contexto actual del usuario",
    description="Obtiene el contexto de tenant actual del usuario autenticado."
)
async def obtener_contexto_actual(
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene el contexto de tenant actual del usuario.
    
    Incluye información de tienda, local (si aplica) y permisos disponibles.
    """
    try:
        # Obtener permisos disponibles en el contexto actual
        permisos_disponibles = []
        if tenant_context.tiene_contexto_local:
            # Si tiene contexto de local, mostrar permisos específicos del local
            local_permisos = tenant_context.permisos_locales.get(str(tenant_context.local_id), {})
            permisos_disponibles = [
                permiso for permiso, activo in local_permisos.items() if activo
            ]
        else:
            # Si solo tiene contexto de tienda, mostrar permisos generales
            permisos_disponibles = ["consulta_tienda", "cambio_contexto"]
        
        return TenantContextResponse(
            tienda_id=tenant_context.tienda_id,
            tienda_codigo=tenant_context.tienda_codigo,
            tienda_nombre=tenant_context.tienda_nombre,
            local_id=tenant_context.local_id,
            local_codigo=tenant_context.local_codigo,
            local_nombre=tenant_context.local_nombre,
            tiene_contexto_local=tenant_context.tiene_contexto_local,
            permisos_disponibles=permisos_disponibles
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener el contexto actual"
        )


@router.get(
    "/locales-disponibles",
    response_model=List[LocalResponse],
    summary="Locales disponibles para el usuario",
    description="Obtiene los locales donde el usuario tiene permisos para cambiar contexto."
)
async def obtener_locales_disponibles(
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene los locales disponibles para cambio de contexto.
    
    Solo muestra locales donde el usuario tiene permisos asignados.
    """
    try:
        local_repo = LocalRepository(session)
        
        # Obtener todos los locales activos de la tienda
        locales_tienda = await local_repo.get_locales_activos_by_tienda(tenant_context.tienda_id)
        
        # Filtrar solo locales donde el usuario tiene permisos
        locales_disponibles = []
        for local in locales_tienda:
            if tenant_context.puede_ver_stock_local(local.id):
                locales_disponibles.append(local)
        
        return locales_disponibles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los locales disponibles"
        )


@router.post(
    "/cambiar-contexto",
    response_model=TenantContextResponse,
    summary="Cambiar contexto de local",
    description="Cambia el contexto activo a un local específico o a solo tienda."
)
async def cambiar_contexto_local(
    cambio_request: CambiarContextoRequest,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Cambia el contexto activo del usuario.
    
    - **local_id**: ID del nuevo local (null para contexto solo tienda)
    
    El cambio de contexto afecta los permisos disponibles y las operaciones
    que el usuario puede realizar.
    """
    try:
        # Validar que puede acceder al nuevo local si se especifica
        if cambio_request.local_id:
            if not tenant_context.puede_ver_stock_local(cambio_request.local_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tiene permisos para cambiar a este local"
                )
            
            # Obtener información del local para el contexto
            local_repo = LocalRepository(session)
            local = await local_repo.get_by_id(cambio_request.local_id)
            
            if not local or not local.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Local no encontrado o inactivo"
                )
            
            if local.tienda_id != tenant_context.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="El local no pertenece a su tienda"
                )
            
            # Cambiar a contexto de local
            tenant_context.cambiar_contexto_local(
                local.id, 
                local.codigo, 
                local.nombre
            )
        else:
            # Cambiar a contexto solo tienda
            tenant_context.limpiar_contexto_local()
        
        # Retornar nuevo contexto
        permisos_disponibles = []
        if tenant_context.tiene_contexto_local:
            local_permisos = tenant_context.permisos_locales.get(str(tenant_context.local_id), {})
            permisos_disponibles = [
                permiso for permiso, activo in local_permisos.items() if activo
            ]
        else:
            permisos_disponibles = ["consulta_tienda", "cambio_contexto"]
        
        return TenantContextResponse(
            tienda_id=tenant_context.tienda_id,
            tienda_codigo=tenant_context.tienda_codigo,
            tienda_nombre=tenant_context.tienda_nombre,
            local_id=tenant_context.local_id,
            local_codigo=tenant_context.local_codigo,
            local_nombre=tenant_context.local_nombre,
            tiene_contexto_local=tenant_context.tiene_contexto_local,
            permisos_disponibles=permisos_disponibles
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al cambiar el contexto"
        )


@router.get(
    "/permisos",
    response_model=dict,
    summary="Permisos detallados del usuario",
    description="Obtiene información detallada de todos los permisos del usuario por local."
)
async def obtener_permisos_detallados(
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene información detallada de permisos del usuario.
    
    Muestra permisos por local y permisos generales de tienda.
    """
    try:
        return {
            "user_id": str(tenant_context.user_id),
            "user_nombre": tenant_context.user_nombre,
            "user_rol": tenant_context.user_rol,
            "tienda_id": str(tenant_context.tienda_id),
            "tienda_codigo": tenant_context.tienda_codigo,
            "permisos_por_local": tenant_context.permisos_locales,
            "contexto_actual": {
                "tipo": tenant_context.tipo_contexto.value,
                "local_id": str(tenant_context.local_id) if tenant_context.local_id else None,
                "local_codigo": tenant_context.local_codigo,
                "permisos_activos": tenant_context.get_permisos_contexto_actual()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los permisos detallados"
        )


@router.get(
    "/validar-permiso/{permiso}",
    response_model=dict,
    summary="Validar permiso específico",
    description="Valida si el usuario tiene un permiso específico en el contexto actual."
)
async def validar_permiso_especifico(
    permiso: str,
    local_id: Optional[UUID] = None,
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Valida si el usuario tiene un permiso específico.
    
    - **permiso**: Nombre del permiso a validar
    - **local_id**: Local específico (opcional, usa contexto actual si no se especifica)
    """
    try:
        if local_id:
            # Validar permiso en local específico
            tiene_permiso = tenant_context.tiene_permiso_en_local(local_id, permiso)
        else:
            # Validar permiso en contexto actual
            tiene_permiso = tenant_context.validar_operacion_en_contexto_actual(permiso)
        
        return {
            "permiso": permiso,
            "local_id": str(local_id) if local_id else None,
            "contexto_actual": str(tenant_context.local_id) if tenant_context.local_id else "tienda_only",
            "tiene_permiso": tiene_permiso
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al validar el permiso"
        )


@router.get(
    "/info",
    response_model=dict,
    summary="Información completa del tenant",
    description="Obtiene información completa del tenant incluyendo configuración y estadísticas básicas."
)
async def obtener_informacion_completa_tenant(
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene información completa del tenant.
    
    Incluye datos de tienda, locales disponibles, contexto actual y estadísticas básicas.
    """
    try:
        local_repo = LocalRepository(session)
        
        # Obtener locales donde el usuario tiene permisos
        locales_usuario = []
        locales_tienda = await local_repo.get_locales_activos_by_tienda(tenant_context.tienda_id)
        
        for local in locales_tienda:
            if tenant_context.puede_ver_stock_local(local.id):
                permisos_local = tenant_context.permisos_locales.get(str(local.id), {})
                locales_usuario.append({
                    "local": local,
                    "permisos": permisos_local
                })
        
        return {
            "tenant_info": {
                "tienda_id": str(tenant_context.tienda_id),
                "tienda_codigo": tenant_context.tienda_codigo,
                "tienda_nombre": tenant_context.tienda_nombre
            },
            "user_info": {
                "user_id": str(tenant_context.user_id),
                "user_nombre": tenant_context.user_nombre,
                "user_rol": tenant_context.user_rol
            },
            "contexto_actual": {
                "tipo": tenant_context.tipo_contexto.value,
                "local_id": str(tenant_context.local_id) if tenant_context.local_id else None,
                "local_codigo": tenant_context.local_codigo,
                "local_nombre": tenant_context.local_nombre,
                "permisos_activos": tenant_context.get_permisos_contexto_actual()
            },
            "locales_disponibles": locales_usuario,
            "estadisticas": {
                "total_locales_acceso": len(locales_usuario),
                "tiene_permisos_administrador": tenant_context.user_rol == "ADMINISTRADOR",
                "puede_cambiar_contexto": True
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la información del tenant"
        )