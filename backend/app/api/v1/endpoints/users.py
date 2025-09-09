"""
Endpoints para la administración de usuarios.
Proporciona funcionalidades CRUD para gestión de usuarios por administradores.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, Field
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

from app.domain.models.user import User, UserCreate, UserRead, UserUpdate, UserRole
from app.domain.models.usuario_local import UsuarioLocalCreate, UsuarioLocalUpdate, UsuarioLocalResponse, PerfilPermiso
from app.application.use_cases.user_management_use_cases import (
    ListUsersUseCase,
    GetUserByIdUseCase,
    CreateUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    ChangeUserPasswordUseCase,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidRoleError,
    PermissionDeniedError
)
from app.infrastructure.repositories.user_repository import SQLUserRepository
from app.infrastructure.repositories.usuario_local_repository import UsuarioLocalRepository
from app.infrastructure.repositories.local_repository import LocalRepository
from app.infrastructure.database.session import get_session
from app.application.use_cases.auth_use_cases import GetCurrentUserUseCase, AuthenticationError

router = APIRouter(tags=["Administración de Usuarios"])
security = HTTPBearer()


def get_user_repository(session: Session = Depends(get_session)) -> SQLUserRepository:
    """Dependency injection para el repositorio de usuarios."""
    return SQLUserRepository(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repository: SQLUserRepository = Depends(get_user_repository)
) -> User:
    """
    Dependency para obtener el usuario actual autenticado.
    
    Args:
        credentials: Token Bearer del header Authorization
        user_repository: Repositorio de usuarios
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido
    """
    try:
        token = credentials.credentials
        get_current_user_use_case = GetCurrentUserUseCase(user_repository)
        user_data = await get_current_user_use_case.execute(token)
        
        # Obtener el usuario completo del repositorio
        user = await user_repository.get_by_id_async(user_data["id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        return user
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error de autenticación"
        )


def require_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency que verifica que el usuario actual sea administrador.
    
    Args:
        current_user: Usuario autenticado
        
    Returns:
        User: Usuario con permisos de administrador
        
    Raises:
        HTTPException: Si el usuario no es administrador
    """
    if current_user.rol != UserRole.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador."
        )
    return current_user


# Schemas para responses
class UserListResponse(UserRead):
    """Schema extendido para lista de usuarios."""
    total_locales_asignados: Optional[int] = Field(0, description="Número total de locales asignados")
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserRead):
    """Schema detallado para un usuario específico."""
    locales_asignados: Optional[List[dict]] = Field([], description="Locales asignados al usuario")
    total_locales_asignados: Optional[int] = Field(0, description="Número total de locales asignados")
    
    class Config:
        from_attributes = True


class CreateUserRequest(UserCreate):
    """Schema para crear usuario desde administración."""
    pass


class UpdateUserRequest(UserUpdate):
    """Schema para actualizar usuario desde administración."""
    pass


class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña."""
    new_password: str = Field(min_length=8, description="Nueva contraseña")


class AssignLocalPerfilRequest(BaseModel):
    """Schema para asignar usuario a local con perfil predefinido."""
    local_id: UUID = Field(description="ID del local a asignar")
    perfil: PerfilPermiso = Field(description="Perfil de permisos predefinido")


class UserStatsResponse(BaseModel):
    """Schema para estadísticas de usuarios."""
    total_users: int
    active_users: int
    users_by_role: dict[str, int]


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(None, description="Buscar por nombre o email"),
    role: Optional[str] = Query(None, description="Filtrar por rol"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository),
    session: Session = Depends(get_session)
):
    """
    Listar usuarios del sistema con paginación y filtros.
    Solo muestra usuarios de la misma tienda del administrador.
    Solo accesible para administradores.
    """
    try:
        use_case = ListUsersUseCase(user_repository)
        users = await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active,
            tienda_id=current_user.tienda_id  # Filtrar solo usuarios de la misma tienda
        )
        
        # Enriquecer usuarios con conteo de locales asignados
        usuario_local_repo = UsuarioLocalRepository(session)
        users_enriched = []
        
        for user in users:
            # Convertir a dict y agregar información de locales
            user_dict = user.dict() if hasattr(user, 'dict') else user.__dict__.copy()
            
            # Contar locales asignados
            asignaciones = usuario_local_repo.get_by_usuario(user.id, incluir_inactivos=False)
            user_dict['total_locales_asignados'] = len(asignaciones)
            
            users_enriched.append(user_dict)
        
        return users_enriched
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository),
    session: Session = Depends(get_session)
):
    """
    Crear un nuevo usuario en el sistema.
    El usuario se asigna automáticamente a la misma tienda del administrador.
    Si el usuario tiene rol ADMINISTRADOR, se asigna automáticamente a todos los locales.
    Solo accesible para administradores.
    """
    try:
        # Asignar automáticamente la tienda del administrador al nuevo usuario
        user_data.tienda_id = current_user.tienda_id
        
        use_case = CreateUserUseCase(user_repository)
        user = await use_case.execute(user_data)
        
        # Si el nuevo usuario es ADMINISTRADOR, asignarle automáticamente todos los locales
        if user_data.rol == UserRole.ADMINISTRADOR:
            try:
                local_repo = LocalRepository(session)
                usuario_local_repo = UsuarioLocalRepository(session)
                
                # Obtener todos los locales de la tienda
                locales_tienda = local_repo.get_by_tienda(current_user.tienda_id, limit=1000)
                
                print(f"Asignando {len(locales_tienda)} locales al administrador {user.email}")
                
                # Asignar el usuario a todos los locales con permisos completos de administrador
                for local in locales_tienda:
                    assignment_data = UsuarioLocalCreate(
                        user_id=user.id,
                        local_id=local.id,
                        puede_vender=True,
                        puede_ver_stock=True,
                        puede_transferir=True,
                        es_responsable=True,
                        puede_modificar_precios=True,
                        puede_aplicar_descuentos=True,
                        puede_ver_reportes=True,
                        puede_gestionar_usuarios=True
                    )
                    usuario_local_repo.create(assignment_data)
                    print(f"✅ Asignado al local: {local.nombre}")
                    
            except Exception as assign_error:
                print(f"Error asignando locales al administrador: {assign_error}")
                # No fallar la creación del usuario por errores de asignación
        
        return user
        
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


# ============================================================================
# ENDPOINTS PARA GESTIÓN DE ASIGNACIÓN DE LOCALES
# (Deben ir ANTES que el endpoint /{user_id} para evitar conflictos de routing)
# ============================================================================

@router.get("/{user_id}/locales", response_model=List[UsuarioLocalResponse])
async def get_user_local_assignments(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Obtener todos los locales asignados a un usuario específico.
    Solo accesible para administradores.
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Obtener asignaciones de locales
        usuario_local_repo = UsuarioLocalRepository(session)
        local_repo = LocalRepository(session)
        asignaciones = usuario_local_repo.get_by_usuario(user_id, incluir_inactivos=False)
        
        # Enriquecer asignaciones con información del local
        asignaciones_enriquecidas = []
        for asignacion in asignaciones:
            local = local_repo.get_by_id(asignacion.local_id)
            asignacion_dict = asignacion.dict() if hasattr(asignacion, 'dict') else asignacion.__dict__
            
            # Agregar información del local
            asignacion_dict['local_nombre'] = local.nombre if local else 'Local no encontrado'
            asignacion_dict['local_codigo'] = local.codigo if local else 'N/A'
            asignacion_dict['assignment_id'] = asignacion.id
            
            asignaciones_enriquecidas.append(asignacion_dict)
        
        return asignaciones_enriquecidas
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{user_id}/locales/disponibles", response_model=List[dict])
async def get_available_locals_for_user(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Obtener locales disponibles para asignar a un usuario.
    Solo incluye locales de la misma tienda que aún no están asignados al usuario.
    Solo accesible para administradores.
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Obtener todos los locales de la tienda
        local_repo = LocalRepository(session)
        todos_locales = local_repo.get_by_tienda(current_user.tienda_id, include_inactive=False)
        
        # Obtener locales ya asignados al usuario
        usuario_local_repo = UsuarioLocalRepository(session)
        asignaciones = usuario_local_repo.get_by_usuario(user_id, incluir_inactivos=False)
        locales_asignados = {asignacion.local_id for asignacion in asignaciones}
        
        # Filtrar locales disponibles
        locales_disponibles = []
        for local in todos_locales:
            if local.id not in locales_asignados:
                # Manejo defensivo de la dirección
                direccion_str = None
                ciudad_str = None
                
                try:
                    if hasattr(local, 'direccion') and local.direccion:
                        if isinstance(local.direccion, dict):
                            direccion_str = local.direccion.get('direccion_principal')
                            ciudad_str = local.direccion.get('ciudad')
                        elif hasattr(local.direccion, 'direccion_principal'):
                            direccion_str = local.direccion.direccion_principal
                            ciudad_str = local.direccion.ciudad
                        else:
                            direccion_str = str(local.direccion)
                except Exception as addr_err:
                    print(f"Error procesando dirección del local {local.id}: {addr_err}")
                
                locales_disponibles.append({
                    "id": str(local.id),
                    "nombre": local.nombre,
                    "codigo": local.codigo,
                    "direccion": direccion_str,
                    "ciudad": ciudad_str,
                    "is_active": local.is_active
                })
        
        return locales_disponibles
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )


@router.post("/{user_id}/locales", response_model=UsuarioLocalResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_local(
    user_id: UUID,
    assignment_data: UsuarioLocalCreate,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Asignar un usuario a un local con permisos específicos.
    Solo accesible para administradores.
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Verificar que el local pertenece a la tienda del admin
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(assignment_data.local_id)
        if not local or local.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Local no válido para su tienda"
            )
        
        # Validar que user_id en la URL coincida con el del body
        if assignment_data.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El user_id en la URL no coincide con el del cuerpo de la petición"
            )
        
        # Crear la asignación
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion = usuario_local_repo.create(assignment_data)
        
        return asignacion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{user_id}/locales/perfil", response_model=UsuarioLocalResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_local_with_profile(
    user_id: UUID,
    assignment_request: AssignLocalPerfilRequest,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Asignar un usuario a un local usando un perfil predefinido de permisos.
    Solo accesible para administradores.
    
    Perfiles disponibles:
    - VENDEDOR: Permisos básicos de venta y consulta
    - RESPONSABLE_LOCAL: Permisos completos del local  
    - GERENTE_VENTAS: Permisos de ventas y reportes
    - CONTADOR: Permisos de reportes y consultas
    - ADMINISTRADOR: Todos los permisos
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Verificar que el local pertenece a la tienda del admin
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(assignment_request.local_id)
        if not local or local.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Local no válido para su tienda"
            )
        
        # Crear la asignación con perfil predefinido
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion = usuario_local_repo.asignar_perfil_permiso(
            user_id,
            assignment_request.local_id,
            assignment_request.perfil,
            created_by=current_user.id
        )
        
        return asignacion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{user_id}/locales/{assignment_id}", response_model=UsuarioLocalResponse)
async def update_user_local_assignment(
    user_id: UUID,
    assignment_id: UUID,
    update_data: UsuarioLocalUpdate,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Actualizar permisos de un usuario en un local específico.
    Solo accesible para administradores.
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Verificar que la asignación existe y pertenece al usuario correcto
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion_existente = usuario_local_repo.get_by_id(assignment_id)
        if not asignacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada"
            )
        
        if asignacion_existente.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La asignación no pertenece al usuario especificado"
            )
        
        # Verificar que el local pertenece a la tienda del admin
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(asignacion_existente.local_id)
        if not local or local.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar asignaciones en locales de otra tienda"
            )
        
        # Actualizar la asignación
        asignacion = usuario_local_repo.update(assignment_id, update_data)
        
        return asignacion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{user_id}/locales/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_local(
    user_id: UUID,
    assignment_id: UUID,
    current_user: User = Depends(require_admin_role),
    session: Session = Depends(get_session)
):
    """
    Remover un usuario de un local (eliminar asignación).
    Solo accesible para administradores.
    """
    try:
        # Verificar que el usuario existe
        user_repository = SQLUserRepository(session)
        user = await user_repository.get_by_id_async(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar usuarios de otra tienda"
            )
        
        # Verificar que la asignación existe y pertenece al usuario correcto
        usuario_local_repo = UsuarioLocalRepository(session)
        asignacion_existente = usuario_local_repo.get_by_id(assignment_id)
        if not asignacion_existente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada"
            )
        
        if asignacion_existente.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La asignación no pertenece al usuario especificado"
            )
        
        # Verificar que el local pertenece a la tienda del admin
        local_repo = LocalRepository(session)
        local = local_repo.get_by_id(asignacion_existente.local_id)
        if not local or local.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede gestionar asignaciones en locales de otra tienda"
            )
        
        # Eliminar la asignación (soft delete)
        eliminado = usuario_local_repo.delete(assignment_id)
        
        if not eliminado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asignación no encontrada"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository),
    session: Session = Depends(get_session)
):
    """
    Obtener detalles de un usuario específico con información de locales asignados.
    Solo accesible para administradores.
    """
    try:
        # Obtener información básica del usuario
        use_case = GetUserByIdUseCase(user_repository)
        user = await use_case.execute(user_id)
        
        # Verificar que el usuario pertenece a la misma tienda que el admin
        if user.tienda_id != current_user.tienda_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede ver usuarios de otra tienda"
            )
        
        # Obtener asignaciones de locales
        usuario_local_repo = UsuarioLocalRepository(session)
        local_repo = LocalRepository(session)
        asignaciones = usuario_local_repo.get_by_usuario(user_id, incluir_inactivos=False)
        
        # Construir información de locales asignados
        locales_asignados = []
        for asignacion in asignaciones:
            local = local_repo.get_by_id(asignacion.local_id)
            if local:
                locales_asignados.append({
                    "assignment_id": str(asignacion.id),
                    "local_id": str(local.id),
                    "local_nombre": local.nombre,
                    "local_codigo": local.codigo,
                    "puede_vender": asignacion.puede_vender,
                    "puede_ver_stock": asignacion.puede_ver_stock,
                    "puede_transferir": asignacion.puede_transferir,
                    "es_responsable": asignacion.es_responsable,
                    "puede_modificar_precios": asignacion.puede_modificar_precios,
                    "puede_aplicar_descuentos": asignacion.puede_aplicar_descuentos,
                    "puede_ver_reportes": asignacion.puede_ver_reportes,
                    "puede_gestionar_usuarios": asignacion.puede_gestionar_usuarios,
                    "limite_descuento_porcentaje": asignacion.limite_descuento_porcentaje,
                    "limite_credito_monto": asignacion.limite_credito_monto,
                    "is_active": asignacion.is_active,
                    "created_at": asignacion.created_at.isoformat() if asignacion.created_at else None
                })
        
        # Crear respuesta detallada
        user_detail = UserDetailResponse(
            id=user.id,
            email=user.email,
            nombre=user.nombre,
            rol=user.rol,
            tienda_id=user.tienda_id,
            local_principal_id=user.local_principal_id,
            created_at=user.created_at,
            is_active=user.is_active,
            locales_asignados=locales_asignados,
            total_locales_asignados=len(locales_asignados)
        )
        
        return user_detail
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_data: UpdateUserRequest,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Actualizar un usuario existente.
    Solo accesible para administradores.
    """
    try:
        use_case = UpdateUserUseCase(user_repository)
        user = await use_case.execute(user_id, user_data)
        return user
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except InvalidRoleError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Desactivar un usuario (soft delete).
    Solo accesible para administradores.
    """
    try:
        use_case = DeleteUserUseCase(user_repository)
        await use_case.execute(user_id, current_user.id)
        return {"message": "Usuario desactivado exitosamente"}
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionDeniedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Activar un usuario desactivado.
    Solo accesible para administradores.
    """
    try:
        use_case = UpdateUserUseCase(user_repository)
        user_data = UserUpdate(is_active=True)
        user = await use_case.execute(user_id, user_data)
        return {"message": "Usuario activado exitosamente", "user": user}
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{user_id}/change-password")
async def change_user_password(
    user_id: UUID,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Cambiar la contraseña de un usuario.
    Solo accesible para administradores.
    """
    try:
        use_case = ChangeUserPasswordUseCase(user_repository)
        await use_case.execute(user_id, password_data.new_password)
        return {"message": "Contraseña actualizada exitosamente"}
        
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/stats/summary", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Obtener estadísticas generales de usuarios.
    Solo incluye usuarios de la misma tienda del administrador.
    Solo accesible para administradores.
    """
    try:
        use_case = ListUsersUseCase(user_repository)
        stats = await use_case.get_user_statistics(tienda_id=current_user.tienda_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/roles/available", response_model=List[str])
async def get_available_roles(
    current_user: User = Depends(require_admin_role)
):
    """
    Obtener lista de roles disponibles en el sistema.
    Solo accesible para administradores.
    """
    return UserRole.all_roles()
