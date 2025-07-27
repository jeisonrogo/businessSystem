"""
Utilidades de autenticación para el sistema.
Maneja la creación y verificación de tokens JWT, y la verificación de contraseñas.
"""

import os
from datetime import datetime, timedelta, UTC
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.domain.models.user import User


# Configuración de JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Configuración de hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationUtils:
    """
    Clase que encapsula las utilidades de autenticación.
    
    Proporciona métodos para:
    - Hashear y verificar contraseñas
    - Crear y verificar tokens JWT
    - Validar credenciales de usuario
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashea una contraseña usando bcrypt.
        
        Args:
            password (str): Contraseña en texto plano
            
        Returns:
            str: Contraseña hasheada
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifica si una contraseña en texto plano coincide con su hash.
        
        Args:
            plain_password (str): Contraseña en texto plano
            hashed_password (str): Hash de la contraseña almacenada
            
        Returns:
            bool: True si las contraseñas coinciden
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crea un token JWT de acceso.
        
        Args:
            data (dict): Datos a incluir en el payload del token
            expires_delta (Optional[timedelta]): Tiempo personalizado de expiración
            
        Returns:
            str: Token JWT codificado
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verifica y decodifica un token JWT.
        
        Args:
            token (str): Token JWT a verificar
            
        Returns:
            Optional[dict]: Payload del token si es válido, None si es inválido
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(email: str, password: str, stored_user: User) -> bool:
        """
        Autentica un usuario verificando sus credenciales.
        
        Args:
            email (str): Email del usuario
            password (str): Contraseña en texto plano
            stored_user (User): Usuario almacenado en la base de datos
            
        Returns:
            bool: True si las credenciales son válidas
        """
        if not stored_user:
            return False
        
        if not stored_user.is_active:
            return False
        
        if stored_user.email != email:
            return False
        
        return AuthenticationUtils.verify_password(password, stored_user.hashed_password)
    
    @staticmethod
    def create_user_token(user: User) -> str:
        """
        Crea un token JWT específico para un usuario.
        
        Args:
            user (User): Usuario para el cual crear el token
            
        Returns:
            str: Token JWT con información del usuario
        """
        token_data = {
            "sub": str(user.id),  # Subject (ID del usuario)
            "email": user.email,
            "nombre": user.nombre,
            "rol": user.rol,
            "is_active": user.is_active
        }
        
        return AuthenticationUtils.create_access_token(token_data)
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[dict]:
        """
        Extrae la información del usuario desde un token JWT válido.
        
        Args:
            token (str): Token JWT
            
        Returns:
            Optional[dict]: Información del usuario si el token es válido
        """
        payload = AuthenticationUtils.verify_token(token)
        
        if payload is None:
            return None
        
        # Verificar que el token no haya expirado
        exp = payload.get("exp")
        if exp is None:
            return None
        
        if datetime.fromtimestamp(exp, tz=UTC) < datetime.now(UTC):
            return None
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "nombre": payload.get("nombre"),
            "rol": payload.get("rol"),
            "is_active": payload.get("is_active", True)
        }


# Esquemas de datos para autenticación
class TokenData:
    """
    Clase para representar datos extraídos de un token.
    """
    def __init__(self, user_id: str, email: str, nombre: str, rol: str, is_active: bool = True):
        self.user_id = user_id
        self.email = email
        self.nombre = nombre
        self.rol = rol
        self.is_active = is_active


class LoginCredentials:
    """
    Clase para representar credenciales de login.
    """
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password 