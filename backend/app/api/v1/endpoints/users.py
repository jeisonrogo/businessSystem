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
        user = await user_repository.get_by_id(user_data["id"])
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
    pass


class UserDetailResponse(UserRead):
    """Schema detallado para un usuario específico."""
    pass


class CreateUserRequest(UserCreate):
    """Schema para crear usuario desde administración."""
    pass


class UpdateUserRequest(UserUpdate):
    """Schema para actualizar usuario desde administración."""
    pass


class ChangePasswordRequest(BaseModel):
    """Schema para cambio de contraseña."""
    new_password: str = Field(min_length=8, description="Nueva contraseña")


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
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Listar usuarios del sistema con paginación y filtros.
    Solo accesible para administradores.
    """
    try:
        use_case = ListUsersUseCase(user_repository)
        users = await use_case.execute(
            page=page,
            limit=limit,
            search=search,
            role=role,
            is_active=is_active
        )
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: CreateUserRequest,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Crear un nuevo usuario en el sistema.
    Solo accesible para administradores.
    """
    try:
        use_case = CreateUserUseCase(user_repository)
        user = await use_case.execute(user_data)
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
            detail="Error interno del servidor"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin_role),
    user_repository: SQLUserRepository = Depends(get_user_repository)
):
    """
    Obtener detalles de un usuario específico.
    Solo accesible para administradores.
    """
    try:
        use_case = GetUserByIdUseCase(user_repository)
        user = await use_case.execute(user_id)
        return user
        
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
    Solo accesible para administradores.
    """
    try:
        use_case = ListUsersUseCase(user_repository)
        stats = await use_case.get_user_statistics()
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