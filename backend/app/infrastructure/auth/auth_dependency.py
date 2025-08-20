"""
Dependency de autenticación para FastAPI que integra con el sistema multi-tenant.

Proporciona funciones para extraer y validar usuarios autenticados
desde tokens JWT, compatible con el middleware de contexto multi-tenant.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.infrastructure.auth.auth_utils import AuthenticationUtils
from app.infrastructure.database.session import get_async_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.models.user import User

# Esquema de seguridad Bearer token
security = HTTPBearer()


class AuthDependency:
    """
    Dependency para autenticación que extrae el usuario actual del token JWT
    y lo almacena en el estado de la request para uso del tenant middleware.
    """

    def __init__(self):
        self.auth_utils = AuthenticationUtils()

    async def __call__(
        self, 
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        session: AsyncSession = Depends(get_async_session)
    ) -> User:
        """
        Extrae y valida el usuario desde el token JWT.

        Args:
            request: Request de FastAPI para almacenar el usuario en el estado
            credentials: Credenciales Bearer token
            session: Sesión de base de datos

        Returns:
            User: Usuario autenticado

        Raises:
            HTTPException: Si el token es inválido o el usuario no existe
        """
        token = credentials.credentials
        
        # Verificar y decodificar el token
        user_data = self.auth_utils.get_user_from_token(token)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Obtener el usuario de la base de datos
        user_repository = UserRepository(session)
        
        try:
            user_id = UUID(user_data["user_id"])
            user = await user_repository.get_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario no encontrado",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Usuario inactivo",
                    headers={"WWW-Authenticate": "Bearer"}
                )

            # Almacenar el usuario en el estado de la request
            # para que el tenant middleware pueda acceder a él
            request.state.current_user = user
            
            return user

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ID de usuario inválido en el token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al validar el usuario"
            )


class OptionalAuthDependency:
    """
    Dependency opcional de autenticación que permite requests sin autenticación.
    
    Útil para endpoints que pueden funcionar con o sin usuario autenticado.
    """

    def __init__(self):
        self.auth_utils = AuthenticationUtils()

    async def __call__(
        self, 
        request: Request,
        session: AsyncSession = Depends(get_async_session)
    ) -> Optional[User]:
        """
        Extrae el usuario del token si está presente.

        Args:
            request: Request de FastAPI
            session: Sesión de base de datos

        Returns:
            Optional[User]: Usuario si está autenticado, None si no
        """
        # Intentar extraer el token del header Authorization
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.replace("Bearer ", "")
        
        # Verificar y decodificar el token
        user_data = self.auth_utils.get_user_from_token(token)
        
        if not user_data:
            return None

        # Obtener el usuario de la base de datos
        user_repository = UserRepository(session)
        
        try:
            user_id = UUID(user_data["user_id"])
            user = await user_repository.get_by_id(user_id)
            
            if user and user.is_active:
                # Almacenar el usuario en el estado de la request
                request.state.current_user = user
                return user
            
            return None

        except (ValueError, Exception):
            return None


# Instancias de dependencies para uso en endpoints
get_current_user = AuthDependency()
get_optional_user = OptionalAuthDependency()


def require_role(required_role: str):
    """
    Factory para crear dependency que requiere un rol específico.
    
    Args:
        required_role: Rol requerido del usuario
        
    Returns:
        Dependency function que valida el rol
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if current_user.rol != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol '{required_role}' para esta operación"
            )
        return current_user
    
    return role_dependency


def require_active_user():
    """
    Dependency que requiere un usuario activo.
    
    Returns:
        User: Usuario activo validado
    """
    async def active_user_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )
        return current_user
    
    return active_user_dependency


# Dependencies pre-configuradas para roles específicos
require_admin = require_role("ADMINISTRADOR")
require_manager = require_role("GERENTE_VENTAS")
require_accountant = require_role("CONTADOR")
require_seller = require_role("VENDEDOR")