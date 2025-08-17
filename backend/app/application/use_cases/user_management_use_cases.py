"""
Casos de uso para la gestión y administración de usuarios.
Implementa la lógica de negocio para operaciones CRUD de usuarios.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, UTC

from app.domain.models.user import User, UserCreate, UserRead, UserUpdate, UserRole
from app.application.services.i_user_repository import IUserRepository


# Excepciones específicas
class UserNotFoundError(Exception):
    """Error cuando no se encuentra un usuario."""
    pass


class UserAlreadyExistsError(Exception):
    """Error cuando ya existe un usuario con el mismo email."""
    pass


class InvalidRoleError(Exception):
    """Error cuando se asigna un rol inválido."""
    pass


class PermissionDeniedError(Exception):
    """Error cuando no se tienen permisos para realizar una acción."""
    pass


class ListUsersUseCase:
    """Caso de uso para listar usuarios con filtros y paginación."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[UserRead]:
        """
        Listar usuarios con filtros aplicados.
        
        Args:
            page: Número de página
            limit: Registros por página
            search: Texto para buscar en nombre y email
            role: Filtrar por rol específico
            is_active: Filtrar por estado activo
            
        Returns:
            List[UserRead]: Lista de usuarios filtrados
        """
        try:
            users = await self.user_repository.list_with_filters(
                page=page,
                limit=limit,
                search=search,
                role=role,
                is_active=is_active
            )
            
            return [
                UserRead(
                    id=user.id,
                    email=user.email,
                    nombre=user.nombre,
                    rol=user.rol,
                    created_at=user.created_at,
                    is_active=user.is_active
                )
                for user in users
            ]
            
        except Exception as e:
            raise Exception(f"Error al listar usuarios: {str(e)}")
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales de usuarios.
        
        Returns:
            Dict con estadísticas de usuarios
        """
        try:
            all_users = await self.user_repository.get_all()
            
            total_users = len(all_users)
            active_users = len([u for u in all_users if u.is_active])
            
            users_by_role = {}
            for role in UserRole.all_roles():
                users_by_role[role] = len([u for u in all_users if u.rol == role])
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "users_by_role": users_by_role
            }
            
        except Exception as e:
            raise Exception(f"Error al obtener estadísticas: {str(e)}")


class GetUserByIdUseCase:
    """Caso de uso para obtener un usuario por ID."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID) -> UserRead:
        """
        Obtener usuario por ID.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            UserRead: Datos del usuario
            
        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            
            return UserRead(
                id=user.id,
                email=user.email,
                nombre=user.nombre,
                rol=user.rol,
                created_at=user.created_at,
                is_active=user.is_active
            )
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Error al obtener usuario: {str(e)}")


class CreateUserUseCase:
    """Caso de uso para crear un nuevo usuario."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_data: UserCreate) -> UserRead:
        """
        Crear un nuevo usuario.
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            UserRead: Usuario creado
            
        Raises:
            UserAlreadyExistsError: Si ya existe un usuario con el email
            InvalidRoleError: Si el rol no es válido
        """
        try:
            # Validar que el rol sea válido
            if not UserRole.is_valid_role(user_data.rol):
                raise InvalidRoleError(f"Rol '{user_data.rol}' no es válido")
            
            # Verificar que no exista un usuario con el mismo email
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user:
                raise UserAlreadyExistsError(f"Ya existe un usuario con el email {user_data.email}")
            
            # Crear el usuario
            user = await self.user_repository.create(user_data)
            
            return UserRead(
                id=user.id,
                email=user.email,
                nombre=user.nombre,
                rol=user.rol,
                created_at=user.created_at,
                is_active=user.is_active
            )
            
        except (UserAlreadyExistsError, InvalidRoleError):
            raise
        except Exception as e:
            raise Exception(f"Error al crear usuario: {str(e)}")


class UpdateUserUseCase:
    """Caso de uso para actualizar un usuario existente."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID, user_data: UserUpdate) -> UserRead:
        """
        Actualizar un usuario existente.
        
        Args:
            user_id: ID del usuario a actualizar
            user_data: Datos a actualizar
            
        Returns:
            UserRead: Usuario actualizado
            
        Raises:
            UserNotFoundError: Si el usuario no existe
            UserAlreadyExistsError: Si el nuevo email ya existe
            InvalidRoleError: Si el nuevo rol no es válido
        """
        try:
            # Verificar que el usuario existe
            existing_user = await self.user_repository.get_by_id(user_id)
            if not existing_user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            
            # Validar rol si se proporciona
            if user_data.rol and not UserRole.is_valid_role(user_data.rol):
                raise InvalidRoleError(f"Rol '{user_data.rol}' no es válido")
            
            # Verificar email único si se cambia
            if user_data.email and user_data.email != existing_user.email:
                email_user = await self.user_repository.get_by_email(user_data.email)
                if email_user:
                    raise UserAlreadyExistsError(f"Ya existe un usuario con el email {user_data.email}")
            
            # Actualizar el usuario
            updated_user = await self.user_repository.update(user_id, user_data)
            
            return UserRead(
                id=updated_user.id,
                email=updated_user.email,
                nombre=updated_user.nombre,
                rol=updated_user.rol,
                created_at=updated_user.created_at,
                is_active=updated_user.is_active
            )
            
        except (UserNotFoundError, UserAlreadyExistsError, InvalidRoleError):
            raise
        except Exception as e:
            raise Exception(f"Error al actualizar usuario: {str(e)}")


class DeleteUserUseCase:
    """Caso de uso para desactivar (soft delete) un usuario."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID, admin_id: UUID) -> bool:
        """
        Desactivar un usuario (soft delete).
        
        Args:
            user_id: ID del usuario a desactivar
            admin_id: ID del administrador que realiza la acción
            
        Returns:
            bool: True si se desactivó exitosamente
            
        Raises:
            UserNotFoundError: Si el usuario no existe
            PermissionDeniedError: Si intenta desactivarse a sí mismo
        """
        try:
            # Verificar que el usuario existe
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            
            # No permitir que un admin se desactive a sí mismo
            if user_id == admin_id:
                raise PermissionDeniedError("No puedes desactivar tu propia cuenta")
            
            # Desactivar usuario
            user_data = UserUpdate(is_active=False)
            await self.user_repository.update(user_id, user_data)
            
            return True
            
        except (UserNotFoundError, PermissionDeniedError):
            raise
        except Exception as e:
            raise Exception(f"Error al desactivar usuario: {str(e)}")


class ChangeUserPasswordUseCase:
    """Caso de uso para cambiar la contraseña de un usuario."""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: UUID, new_password: str) -> bool:
        """
        Cambiar la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña en texto plano
            
        Returns:
            bool: True si se cambió exitosamente
            
        Raises:
            UserNotFoundError: Si el usuario no existe
        """
        try:
            # Verificar que el usuario existe
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(f"Usuario con ID {user_id} no encontrado")
            
            # Cambiar contraseña
            user_data = UserUpdate(password=new_password)
            await self.user_repository.update(user_id, user_data)
            
            return True
            
        except UserNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Error al cambiar contraseña: {str(e)}")