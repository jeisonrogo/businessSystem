"""
Endpoints para gestión del contexto de tenant.

Proporciona operaciones para obtener información del contexto actual,
cambiar entre locales, y consultar información de tenant disponible.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select

from app.infrastructure.database.session import get_session
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.repositories.tienda_repository import TiendaRepository
from app.infrastructure.middleware.tenant_middleware import get_tenant_context
from app.application.services.tenant_context_service import TenantContextService
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User
from app.infrastructure.auth.auth_dependency import get_current_user_sync, get_current_user
from app.api.v1.schemas_multi_tenant import (
    TenantContextResponse,
    CambiarContextoRequest,
    LocalResponse
)
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository

router = APIRouter(
    prefix="/tenant-context",
    tags=["Contexto de Tenant"]
)


@router.get(
    "/debug",
    summary="Debug tenant context",
    description="Debug endpoint para entender problemas de tenant context."
)
def debug_tenant_context(
    session: Session = Depends(get_session)
):
    """Debug endpoint completo para tenant context."""
    from app.infrastructure.repositories.user_repository import SQLUserRepository
    from app.infrastructure.repositories.tienda_repository import TiendaRepository  
    from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
    from app.infrastructure.repositories.local_repository import LocalRepository
    from app.application.services.tenant_context_service import TenantContextService
    from sqlmodel import select
    from app.domain.models.user import User
    
    try:
        # Obtener admin user directamente
        admin = session.exec(select(User).where(User.email == 'admin@empresa.com')).first()
        
        if not admin:
            return {"error": "Admin user not found"}
        
        # Verificar datos básicos
        user_repo = SQLUserRepository(session)
        tienda_repo = TiendaRepository(session)
        usuario_local_repo = UsuarioLocalRepository(session)
        local_repo = LocalRepository(session)
        
        tienda = None
        if admin.tienda_id:
            tienda = tienda_repo.get_by_id(admin.tienda_id)
        
        permisos = usuario_local_repo.get_by_usuario(admin.id)
        
        # Crear instancia del servicio y probar crear contexto
        tenant_service = TenantContextService(
            tienda_repository=tienda_repo,
            local_repository=local_repo,
            usuario_local_repository=usuario_local_repo
        )
        
        contexto_resultado = None
        contexto_error = None
        
        try:
            # Intentar crear el contexto
            contexto = tenant_service.crear_contexto_para_usuario(admin, None)
            contexto_resultado = {
                "tienda_id": str(contexto.tienda_id),
                "tienda_codigo": contexto.tienda_codigo,
                "tienda_nombre": contexto.tienda_nombre,
                "user_id": str(contexto.user_id),
                "user_nombre": contexto.user_nombre,
                "permisos_locales": contexto.permisos_locales,
                "tipo_contexto": contexto.tipo_contexto.value
            }
        except Exception as ctx_e:
            contexto_error = {"error": str(ctx_e), "type": type(ctx_e).__name__}
        
        return {
            "admin_found": True,
            "admin_id": str(admin.id),
            "admin_email": admin.email,
            "tienda_id": str(admin.tienda_id) if admin.tienda_id else None,
            "tienda_found": tienda is not None,
            "tienda_info": {
                "id": str(tienda.id),
                "codigo": tienda.codigo,
                "nombre": tienda.nombre
            } if tienda else None,
            "permisos_count": len(permisos),
            "permisos_details": [
                {
                    "local_id": str(p.local_id),
                    "es_responsable": p.es_responsable,
                    "puede_vender": p.puede_vender,
                    "is_active": p.is_active,
                    "permisos_activos": [perm.value for perm in p.get_permisos_activos()]
                } for p in permisos
            ],
            "tenant_context_creation": contexto_resultado,
            "tenant_context_error": contexto_error
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}", "type": type(e).__name__}

@router.get(
    "/middleware-test",
    summary="Test middleware state",
    description="Test what's in request state from middleware."
)
def test_middleware_state(request: Request):
    """Test endpoint to check middleware state."""
    return {
        "has_current_user": hasattr(request.state, 'current_user'),
        "current_user": getattr(request.state, 'current_user', None),
        "has_tenant_context": hasattr(request.state, 'tenant_context'),
        "tenant_context": getattr(request.state, 'tenant_context', None),
        "state_attrs": dir(request.state) if hasattr(request, 'state') else "No state"
    }

@router.get(
    "/current",
    response_model=TenantContextResponse,
    summary="Contexto actual del usuario",
    description="Obtiene el contexto de tenant actual del usuario autenticado."
)
def obtener_contexto_actual(
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
def obtener_locales_disponibles(
    session: Session = Depends(get_session),
    tenant_context: TenantContext = Depends(get_tenant_context)
):
    """
    Obtiene los locales disponibles para cambio de contexto.
    
    Solo muestra locales donde el usuario tiene permisos asignados.
    """
    try:
        local_repo = LocalRepository(session)
        
        # Obtener todos los locales activos de la tienda
        locales_tienda = local_repo.get_locales_activos_by_tienda(tenant_context.tienda_id)
        
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
def cambiar_contexto_local(
    cambio_request: CambiarContextoRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user_sync)
):
    """
    Cambia el contexto activo del usuario.
    
    - **local_id**: ID del nuevo local (null para contexto solo tienda)  
    
    El cambio de contexto afecta los permisos disponibles y las operaciones
    que el usuario puede realizar.
    """
    try:
        # Verificar que el usuario tiene tienda asignada
        if not current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario no tiene tienda asignada"
            )
        
        # Obtener información de la tienda del usuario
        tienda_repo = TiendaRepository(session)
        tienda = tienda_repo.get_by_id(current_user.tienda_id)
        
        if not tienda:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tienda del usuario no encontrada"
            )
        
        # Validar local si se especifica
        local = None
        if cambio_request.local_id:
            local_repo = LocalRepository(session)
            local = local_repo.get_by_id(cambio_request.local_id)
            
            if not local or not local.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Local no encontrado o inactivo"
                )
            
            # Verificar que el local pertenece a la tienda del usuario
            if local.tienda_id != current_user.tienda_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="El local no pertenece a su tienda"
                )
        
        # Permisos básicos según el rol del usuario
        permisos_disponibles = ["consulta_tienda", "cambio_contexto"]
        
        # Agregar permisos según el rol
        if current_user.rol in ["ADMINISTRADOR", "GERENTE_VENTAS"]:
            permisos_disponibles.extend(["consulta_stock", "modificar_stock", "ver_reportes"])
        elif current_user.rol == "CONTADOR":
            permisos_disponibles.extend(["consulta_stock", "ver_reportes"])
        elif current_user.rol == "VENDEDOR":
            permisos_disponibles.extend(["consulta_stock", "venta"])
        
        return TenantContextResponse(
            tienda_id=tienda.id,
            tienda_codigo=tienda.codigo,
            tienda_nombre=tienda.nombre,
            local_id=local.id if local else None,
            local_codigo=local.codigo if local else None, 
            local_nombre=local.nombre if local else None,
            tiene_contexto_local=local is not None,
            permisos_disponibles=permisos_disponibles
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al cambiar el contexto: {str(e)}"
        )


@router.get(
    "/permisos",
    response_model=dict,
    summary="Permisos detallados del usuario",
    description="Obtiene información detallada de todos los permisos del usuario por local."
)
def obtener_permisos_detallados(
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
def validar_permiso_especifico(
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
def obtener_informacion_completa_tenant(
    session: Session = Depends(get_session),
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
        locales_tienda = local_repo.get_locales_activos_by_tienda(tenant_context.tienda_id)
        
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


# Función auxiliar para obtener el repositorio de usuario_locales
def get_usuario_local_repository(session: Session = Depends(get_session)) -> UsuarioLocalRepository:
    """Dependency para obtener el repositorio de usuario-locales."""
    return UsuarioLocalRepository(session)


@router.get("/mis-locales", response_model=List[LocalResponse])
async def get_my_locals(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Obtener los locales disponibles para el usuario actual basado en su rol.
    - ADMINISTRADOR/GERENTE: Todos los locales de la tienda
    - Otros roles: Solo locales asignados específicamente
    """
    try:
        local_repo = LocalRepository(session)
        usuario_local_repo = UsuarioLocalRepository(session)
        
        # Si es administrador o gerente, puede ver todos los locales de su tienda
        if current_user.rol in ["ADMINISTRADOR", "GERENTE"]:
            locals = local_repo.get_by_tienda(current_user.tienda_id, limit=1000)
        else:
            # Para otros roles, solo locales asignados
            user_assignments = usuario_local_repo.get_by_usuario(current_user.id)
            if not user_assignments:
                return []
                
            local_ids = [assignment.local_id for assignment in user_assignments]
            locals = []
            for local_id in local_ids:
                local = local_repo.get_by_id(local_id)
                if local and local.is_active:
                    locals.append(local)
        
        # Obtener estadísticas de stock por local
        from app.infrastructure.repositories.stock_local_repository import StockLocalRepository
        stock_repo = StockLocalRepository(session)
        
        local_responses = []
        for local in locals:
            # Obtener estadísticas de productos/stock del local
            try:
                stock_stats = stock_repo.get_statistics_by_local(local.id)
                total_productos = stock_stats.get('total_productos', 0) if stock_stats else 0
                valor_inventario = stock_stats.get('valor_total', 0.0) if stock_stats else 0.0
            except:
                total_productos = 0
                valor_inventario = 0.0
            
            local_responses.append(LocalResponse(
                id=local.id,
                nombre=local.nombre,
                codigo=local.codigo,
                direccion=local.direccion,
                ciudad=local.ciudad,
                departamento=local.departamento,
                codigo_postal=local.codigo_postal,
                telefono=local.telefono,
                email=local.email,
                configuracion=local.configuracion,
                tienda_id=local.tienda_id,
                is_active=local.is_active,
                created_at=local.created_at,
                updated_at=local.updated_at,
                total_productos=total_productos,
                valor_inventario=valor_inventario
            ))
        
        return local_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )