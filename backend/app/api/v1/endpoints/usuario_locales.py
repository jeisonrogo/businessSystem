"""
Endpoints para gestión de permisos granulares usuario-local.

Proporciona operaciones para asignar, actualizar y gestionar permisos
específicos de usuarios en locales individuales.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
from app.infrastructure.middleware.tenant_middleware import (
    get_tenant_context,
    require_permission
)
from app.domain.models.tenant_context import TenantContext
from app.domain.models.usuario_local import PerfilPermiso
from app.api.v1.schemas_multi_tenant import (
    UsuarioLocalCreate,
    UsuarioLocalUpdate,
    UsuarioLocalAsignarPerfil,
    UsuarioLocalResponse,
    UsuarioLocalEstadisticas,
    PerfilPermisoEnum,
    ErrorResponse
)

router = APIRouter(
    prefix="/usuario-locales",
    tags=["Permisos Usuario-Local"]
)


@router.post(
    "/",
    response_model=UsuarioLocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear permisos usuario-local",
    description="Crea una nueva asignación de permisos para un usuario en un local específico."
)
async def crear_permisos_usuario_local(
    usuario_local_data: UsuarioLocalCreate,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Crea permisos específicos para un usuario en un local.
    
    - **user_id**: ID del usuario
    - **local_id**: ID del local
    - **puede_vender**: Permiso para realizar ventas
    - **puede_ver_stock**: Permiso para consultar stock
    - **puede_transferir**: Permiso para hacer transferencias
    - **es_responsable**: Es responsable del local
    - **puede_modificar_precios**: Puede cambiar precios
    - **puede_aplicar_descuentos**: Puede aplicar descuentos
    - **puede_ver_reportes**: Puede ver reportes
    - **puede_gestionar_usuarios**: Puede gestionar usuarios del local
    - **limite_descuento_porcentaje**: Límite máximo de descuento (%)
    - **limite_credito_monto**: Límite máximo de crédito
    """
    try:
        # Validar que el local pertenece a la tienda del usuario
        if not tenant_context.puede_ver_stock_local(usuario_local_data.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede asignar permisos en locales de otra tienda"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        usuario_local = await usuario_local_repo.create(usuario_local_data)
        return usuario_local
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
            detail="Error interno al crear los permisos"
        )


@router.post(
    "/asignar-perfil",
    response_model=UsuarioLocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar perfil de permisos",
    description="Asigna un perfil predefinido de permisos a un usuario en un local."
)
async def asignar_perfil_permiso(
    asignacion_data: UsuarioLocalAsignarPerfil,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Asigna un perfil predefinido de permisos.
    
    Perfiles disponibles:
    - **VENDEDOR**: Permisos básicos de venta y consulta
    - **RESPONSABLE_LOCAL**: Permisos completos del local
    - **GERENTE_VENTAS**: Permisos de ventas y reportes
    - **CONTADOR**: Permisos de reportes y consultas
    - **ADMINISTRADOR**: Todos los permisos
    """
    try:
        # Validar que el local pertenece a la tienda
        if not tenant_context.puede_ver_stock_local(asignacion_data.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede asignar permisos en locales de otra tienda"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        
        # Convertir enum de API a domain enum
        perfil_domain = PerfilPermiso(asignacion_data.perfil.value)
        
        usuario_local = await usuario_local_repo.asignar_perfil_permiso(
            asignacion_data.user_id,
            asignacion_data.local_id,
            perfil_domain,
            tenant_context.user_id
        )
        return usuario_local
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
            detail="Error interno al asignar el perfil"
        )


@router.get(
    "/",
    response_model=List[UsuarioLocalResponse],
    summary="Listar permisos de la tienda",
    description="Obtiene todas las asignaciones de permisos de la tienda."
)
async def listar_permisos_tienda(
    incluir_inactivos: bool = Query(False, description="Incluir asignaciones inactivas"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todas las asignaciones de permisos de la tienda.
    
    Requiere permisos de reportes para ver asignaciones globales.
    """
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        asignaciones = await usuario_local_repo.get_by_tienda(
            tenant_context.tienda_id,
            incluir_inactivos=incluir_inactivos
        )
        return asignaciones
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los permisos"
        )


@router.get(
    "/usuario/{user_id}",
    response_model=List[UsuarioLocalResponse],
    summary="Permisos de un usuario",
    description="Obtiene todas las asignaciones de permisos de un usuario específico."
)
async def listar_permisos_usuario(
    user_id: UUID,
    incluir_inactivos: bool = Query(False, description="Incluir asignaciones inactivas"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todas las asignaciones de un usuario.
    
    Los usuarios pueden ver solo sus propios permisos,
    los gestores pueden ver permisos de cualquier usuario.
    """
    try:
        # Validar que puede ver permisos de este usuario
        if (tenant_context.user_id != user_id and 
            not tenant_context.validar_operacion_en_contexto_actual("gestion_usuarios")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede ver sus propios permisos"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        asignaciones = await usuario_local_repo.get_by_usuario(
            user_id,
            incluir_inactivos=incluir_inactivos
        )
        
        # Filtrar solo locales de la tienda del usuario
        asignaciones_filtradas = []
        for asignacion in asignaciones:
            if tenant_context.puede_ver_stock_local(asignacion.local_id):
                asignaciones_filtradas.append(asignacion)
        
        return asignaciones_filtradas
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los permisos del usuario"
        )


@router.get(
    "/local/{local_id}",
    response_model=List[UsuarioLocalResponse],
    summary="Usuarios con permisos en un local",
    description="Obtiene todos los usuarios que tienen permisos en un local específico."
)
async def listar_usuarios_local(
    local_id: UUID,
    incluir_inactivos: bool = Query(False, description="Incluir asignaciones inactivas"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene todos los usuarios con permisos en un local.
    """
    try:
        # Validar que puede ver usuarios de este local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver usuarios de este local"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        usuarios_local = await usuario_local_repo.get_by_local(
            local_id,
            incluir_inactivos=incluir_inactivos
        )
        return usuarios_local
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener usuarios del local"
        )


@router.get(
    "/{usuario_local_id}",
    response_model=UsuarioLocalResponse,
    summary="Obtener asignación específica",
    description="Obtiene una asignación específica de permisos por su ID."
)
async def obtener_asignacion_permisos(
    usuario_local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene una asignación específica de permisos.
    """
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion = await usuario_local_repo.get_by_id(usuario_local_id)
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación de permisos no encontrada"
            )
        
        # Validar que puede ver esta asignación
        if not tenant_context.puede_ver_stock_local(asignacion.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta asignación"
            )
        
        return asignacion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener la asignación"
        )


@router.get(
    "/usuario/{user_id}/local/{local_id}",
    response_model=UsuarioLocalResponse,
    summary="Permisos específicos usuario-local",
    description="Obtiene los permisos específicos de un usuario en un local."
)
async def obtener_permisos_usuario_local(
    user_id: UUID,
    local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene los permisos específicos de un usuario en un local.
    
    Los usuarios pueden consultar sus propios permisos.
    """
    try:
        # Validar que puede consultar estos permisos
        if (tenant_context.user_id != user_id and 
            not tenant_context.validar_operacion_en_contexto_actual("ver_reportes")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede consultar sus propios permisos"
            )
        
        # Validar acceso al local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a este local"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion = await usuario_local_repo.get_by_usuario_and_local(user_id, local_id)
        
        if not asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no tiene permisos asignados en este local"
            )
        
        return asignacion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los permisos"
        )


@router.put(
    "/{usuario_local_id}",
    response_model=UsuarioLocalResponse,
    summary="Actualizar permisos",
    description="Actualiza los permisos de una asignación usuario-local existente."
)
async def actualizar_permisos(
    usuario_local_id: UUID,
    permisos_data: UsuarioLocalUpdate,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Actualiza los permisos de una asignación existente.
    """
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        
        # Verificar que la asignación existe y pertenece a la tienda
        asignacion_existente = await usuario_local_repo.get_by_id(usuario_local_id)
        if not asignacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación de permisos no encontrada"
            )
        
        if not tenant_context.puede_ver_stock_local(asignacion_existente.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede actualizar permisos en locales de otra tienda"
            )
        
        asignacion = await usuario_local_repo.update(usuario_local_id, permisos_data)
        return asignacion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar los permisos"
        )


@router.delete(
    "/{usuario_local_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar permisos",
    description="Desactiva una asignación de permisos (eliminación suave)."
)
async def eliminar_permisos(
    usuario_local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Elimina (desactiva) una asignación de permisos.
    
    La eliminación es suave (marca como inactiva).
    """
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        
        # Verificar que la asignación existe y pertenece a la tienda
        asignacion_existente = await usuario_local_repo.get_by_id(usuario_local_id)
        if not asignacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación de permisos no encontrada"
            )
        
        if not tenant_context.puede_ver_stock_local(asignacion_existente.local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede eliminar permisos en locales de otra tienda"
            )
        
        eliminado = await usuario_local_repo.delete(usuario_local_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación de permisos no encontrada"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar los permisos"
        )


# ============ ENDPOINTS ESPECIALIZADOS ============

@router.get(
    "/local/{local_id}/responsables",
    response_model=List[UsuarioLocalResponse],
    summary="Responsables de un local",
    description="Obtiene los usuarios responsables de un local específico."
)
async def obtener_responsables_local(
    local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene los usuarios responsables de un local.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver responsables de este local"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        responsables = await usuario_local_repo.get_responsables_local(local_id)
        return responsables
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los responsables"
        )


@router.get(
    "/local/{local_id}/vendedores",
    response_model=List[UsuarioLocalResponse],
    summary="Vendedores de un local",
    description="Obtiene los usuarios que pueden vender en un local específico."
)
async def obtener_vendedores_local(
    local_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene los usuarios que pueden vender en un local.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver vendedores de este local"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        vendedores = await usuario_local_repo.get_usuarios_vendedores_local(local_id)
        return vendedores
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los vendedores"
        )


@router.get(
    "/usuario/{user_id}/locales-responsable",
    response_model=List[UUID],
    summary="Locales donde usuario es responsable",
    description="Obtiene los locales donde un usuario es responsable."
)
async def obtener_locales_responsable(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene los locales donde un usuario es responsable.
    """
    try:
        # Validar que puede consultar estos datos
        if (tenant_context.user_id != user_id and 
            not tenant_context.validar_operacion_en_contexto_actual("ver_reportes")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede consultar sus propias responsabilidades"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        locales = await usuario_local_repo.get_locales_donde_usuario_es_responsable(user_id)
        return locales
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener los locales"
        )


@router.post(
    "/copiar-permisos",
    response_model=UsuarioLocalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Copiar permisos entre locales",
    description="Copia los permisos de un usuario de un local origen a un local destino."
)
async def copiar_permisos_entre_locales(
    user_id: UUID = Query(..., description="ID del usuario"),
    local_origen_id: UUID = Query(..., description="ID del local origen"),
    local_destino_id: UUID = Query(..., description="ID del local destino"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("gestion_usuarios"))
):
    """
    Copia los permisos de un usuario de un local a otro.
    
    Útil para asignar permisos similares en múltiples locales.
    No copia la responsabilidad por seguridad.
    """
    try:
        # Validar que puede gestionar ambos locales
        if not (tenant_context.puede_ver_stock_local(local_origen_id) and 
                tenant_context.puede_ver_stock_local(local_destino_id)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para gestionar estos locales"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        nueva_asignacion = await usuario_local_repo.copiar_permisos_entre_locales(
            user_id,
            local_origen_id,
            local_destino_id,
            tenant_context.user_id
        )
        
        if not nueva_asignacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existen permisos en el local origen"
            )
        
        return nueva_asignacion
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
            detail="Error interno al copiar los permisos"
        )


@router.get(
    "/estadisticas",
    response_model=UsuarioLocalEstadisticas,
    summary="Estadísticas de permisos",
    description="Obtiene estadísticas de permisos de usuario-local en la tienda."
)
async def obtener_estadisticas_permisos(
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Obtiene estadísticas completas de permisos en la tienda.
    
    Incluye conteos de asignaciones, usuarios únicos, responsables por local, etc.
    """
    try:
        usuario_local_repo = UsuarioLocalRepository(session)
        estadisticas = await usuario_local_repo.get_estadisticas_permisos_tienda(
            tenant_context.tienda_id
        )
        
        return UsuarioLocalEstadisticas(
            tienda_id=tenant_context.tienda_id,
            **estadisticas
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener las estadísticas"
        )


@router.post(
    "/validar-operacion",
    response_model=dict,
    summary="Validar límites de usuario",
    description="Valida si un usuario puede realizar una operación según sus límites."
)
async def validar_limites_usuario(
    user_id: UUID = Query(..., description="ID del usuario"),
    local_id: UUID = Query(..., description="ID del local"),
    tipo_operacion: str = Query(..., description="Tipo de operación: 'descuento' o 'credito'"),
    valor: float = Query(..., ge=0, description="Valor de la operación"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Valida si un usuario puede realizar una operación según sus límites.
    
    Tipos de operación:
    - **descuento**: Valida límite de descuento porcentual
    - **credito**: Valida límite de monto de crédito
    """
    try:
        # Validar que puede consultar este local
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para consultar este local"
            )
        
        if tipo_operacion not in ["descuento", "credito"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tipo de operación debe ser 'descuento' o 'credito'"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        puede_realizar = await usuario_local_repo.validar_limites_usuario(
            user_id,
            local_id,
            tipo_operacion,
            valor
        )
        
        return {
            "user_id": str(user_id),
            "local_id": str(local_id),
            "tipo_operacion": tipo_operacion,
            "valor_solicitado": valor,
            "puede_realizar": puede_realizar
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al validar los límites"
        )


@router.get(
    "/local/{local_id}/buscar-usuarios",
    response_model=List[UsuarioLocalResponse],
    summary="Buscar usuarios en local",
    description="Busca usuarios en un local por nombre o email."
)
async def buscar_usuarios_local(
    local_id: UUID,
    texto: str = Query(..., min_length=2, description="Texto a buscar"),
    session: AsyncSession = Depends(get_async_session),
    tenant_context: TenantContext = Depends(require_permission("ver_reportes"))
):
    """
    Busca usuarios en un local por nombre o email.
    """
    try:
        if not tenant_context.puede_ver_stock_local(local_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para buscar usuarios en este local"
            )
        
        usuario_local_repo = UsuarioLocalRepository(session)
        usuarios = await usuario_local_repo.buscar_usuarios_local(local_id, texto)
        return usuarios
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al buscar usuarios"
        )