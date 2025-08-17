"""
Casos de uso para autenticación de usuarios.
Implementa la lógica de negocio para login y registro de usuarios.
"""

from typing import Optional, Dict, Any

from app.domain.models.user import User, UserCreate, UserRole
from app.application.services.i_user_repository import IUserRepository
from app.infrastructure.auth.auth_utils import AuthenticationUtils


class AuthenticationError(Exception):
    """
    Excepción personalizada para errores de autenticación.
    """
    pass


class RegistrationError(Exception):
    """
    Excepción personalizada para errores de registro.
    """
    pass


class LoginUseCase:
    """
    Caso de uso para el login de usuarios.
    
    Maneja la autenticación de credenciales y generación de tokens JWT.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.
        
        Args:
            user_repository (IUserRepository): Repositorio para acceso a datos de usuarios
        """
        self.user_repository = user_repository
        self.auth_utils = AuthenticationUtils()
    
    async def execute(self, email: str, password: str) -> Dict[str, Any]:
        """
        Ejecuta el proceso de login.
        
        Args:
            email (str): Email del usuario
            password (str): Contraseña en texto plano
            
        Returns:
            Dict[str, Any]: Datos de respuesta con token y información del usuario
            
        Raises:
            AuthenticationError: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        user = await self.user_repository.get_by_email(email)
        
        if not user:
            raise AuthenticationError("Credenciales inválidas")
        
        # Verificar que el usuario esté activo
        if not user.is_active:
            raise AuthenticationError("Usuario inactivo")
        
        # Verificar contraseña
        if not self.auth_utils.verify_password(password, user.hashed_password):
            raise AuthenticationError("Credenciales inválidas")
        
        # Generar token JWT
        access_token = self.auth_utils.create_user_token(user)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "nombre": user.nombre,
                "rol": user.rol,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
        }


class RegisterUseCase:
    """
    Caso de uso para el registro de nuevos usuarios.
    
    Maneja la creación de nuevos usuarios con validaciones de negocio.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.
        
        Args:
            user_repository (IUserRepository): Repositorio para acceso a datos de usuarios
        """
        self.user_repository = user_repository
        self.auth_utils = AuthenticationUtils()
    
    async def execute(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Ejecuta el proceso de registro de un nuevo usuario.
        
        Args:
            user_data (UserCreate): Datos para crear el usuario
            
        Returns:
            Dict[str, Any]: Datos de respuesta con token y información del usuario creado
            
        Raises:
            RegistrationError: Si hay errores en el proceso de registro
        """
        try:
            # Validar rol
            if not UserRole.is_valid_role(user_data.rol):
                raise RegistrationError(f"Rol inválido: {user_data.rol}")
            
            # Verificar que el email no exista
            if await self.user_repository.exists_by_email(user_data.email):
                raise RegistrationError(f"Ya existe un usuario con el email: {user_data.email}")
            
            # Crear usuario
            created_user = await self.user_repository.create(user_data)
            
            # Generar token JWT para el usuario recién creado
            access_token = self.auth_utils.create_user_token(created_user)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": str(created_user.id),
                    "email": created_user.email,
                    "nombre": created_user.nombre,
                    "rol": created_user.rol,
                    "is_active": created_user.is_active,
                    "created_at": created_user.created_at.isoformat()
                },
                "message": "Usuario creado exitosamente"
            }
            
        except ValueError as e:
            # Re-lanzar errores de validación como errores de registro
            raise RegistrationError(str(e))
        except Exception as e:
            # Manejar otros errores
            raise RegistrationError(f"Error al crear usuario: {str(e)}")


class GetCurrentUserUseCase:
    """
    Caso de uso para obtener información del usuario actual basado en el token JWT.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.
        
        Args:
            user_repository (IUserRepository): Repositorio para acceso a datos de usuarios
        """
        self.user_repository = user_repository
        self.auth_utils = AuthenticationUtils()
    
    async def execute(self, token: str) -> Dict[str, Any]:
        """
        Obtiene la información del usuario actual desde el token JWT.
        
        Args:
            token (str): Token JWT del usuario
            
        Returns:
            Dict[str, Any]: Información del usuario actual
            
        Raises:
            AuthenticationError: Si el token es inválido o el usuario no existe
        """
        # Extraer información del token
        token_data = self.auth_utils.get_user_from_token(token)
        
        if not token_data:
            raise AuthenticationError("Token inválido")
        
        # Obtener usuario actualizado de la base de datos
        from uuid import UUID
        user_id = UUID(token_data["user_id"])
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            raise AuthenticationError("Usuario no encontrado")
        
        if not user.is_active:
            raise AuthenticationError("Usuario inactivo")
        
        return {
            "id": str(user.id),
            "email": user.email,
            "nombre": user.nombre,
            "rol": user.rol,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        }


class UpdateProfileUseCase:
    """
    Caso de uso para actualizar el perfil del usuario actual.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.
        
        Args:
            user_repository (IUserRepository): Repositorio para acceso a datos de usuarios
        """
        self.user_repository = user_repository
        self.auth_utils = AuthenticationUtils()
    
    async def execute(self, token: str, profile_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Actualiza el perfil del usuario actual.
        
        Args:
            token (str): Token JWT del usuario
            profile_data (Dict[str, str]): Datos del perfil a actualizar (nombre, email)
            
        Returns:
            Dict[str, Any]: Información del usuario actualizado
            
        Raises:
            AuthenticationError: Si el token es inválido o el usuario no existe
            RegistrationError: Si hay errores en la validación
        """
        # Obtener usuario del token
        token_data = self.auth_utils.get_user_from_token(token)
        
        if not token_data:
            raise AuthenticationError("Token inválido")
        
        from uuid import UUID
        user_id = UUID(token_data["user_id"])
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            raise AuthenticationError("Usuario no encontrado")
        
        if not user.is_active:
            raise AuthenticationError("Usuario inactivo")
        
        # Verificar si el email ya existe (solo si se está cambiando)
        if profile_data.get("email") and profile_data["email"] != user.email:
            if await self.user_repository.exists_by_email(profile_data["email"]):
                raise RegistrationError(f"Ya existe un usuario con el email: {profile_data['email']}")
        
        # Actualizar usuario
        updated_user = await self.user_repository.update_profile(
            user_id, 
            profile_data.get("nombre", user.nombre),
            profile_data.get("email", user.email)
        )
        
        return {
            "id": str(updated_user.id),
            "email": updated_user.email,
            "nombre": updated_user.nombre,
            "rol": updated_user.rol,
            "is_active": updated_user.is_active,
            "created_at": updated_user.created_at.isoformat()
        }


class ChangePasswordUseCase:
    """
    Caso de uso para cambiar la contraseña del usuario actual.
    """
    
    def __init__(self, user_repository: IUserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.
        
        Args:
            user_repository (IUserRepository): Repositorio para acceso a datos de usuarios
        """
        self.user_repository = user_repository
        self.auth_utils = AuthenticationUtils()
    
    async def execute(self, token: str, current_password: str, new_password: str) -> None:
        """
        Cambia la contraseña del usuario actual.
        
        Args:
            token (str): Token JWT del usuario
            current_password (str): Contraseña actual
            new_password (str): Nueva contraseña
            
        Raises:
            AuthenticationError: Si el token es inválido, el usuario no existe o la contraseña actual es incorrecta
        """
        # Obtener usuario del token
        token_data = self.auth_utils.get_user_from_token(token)
        
        if not token_data:
            raise AuthenticationError("Token inválido")
        
        from uuid import UUID
        user_id = UUID(token_data["user_id"])
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            raise AuthenticationError("Usuario no encontrado")
        
        if not user.is_active:
            raise AuthenticationError("Usuario inactivo")
        
        # Verificar contraseña actual
        if not self.auth_utils.verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Contraseña actual incorrecta")
        
        # Actualizar contraseña
        await self.user_repository.change_password(user_id, new_password) 