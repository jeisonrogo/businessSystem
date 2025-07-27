"""
Modelo de dominio para la entidad Usuario.
Define la estructura y reglas de negocio para los usuarios del sistema.
"""

from datetime import datetime, UTC
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    """
    Campos base compartidos entre diferentes representaciones del modelo User.
    """
    email: str = Field(unique=True, index=True, description="Email único del usuario")
    nombre: str = Field(min_length=2, max_length=100, description="Nombre completo del usuario")
    rol: str = Field(default="vendedor", description="Rol del usuario en el sistema")


class User(UserBase, table=True):
    """
    Modelo de dominio para la entidad Usuario.
    Representa un usuario del sistema con capacidades de autenticación y autorización.
    
    Reglas de negocio:
    - BR-06: Los usuarios solo pueden acceder a las funciones permitidas por su rol asignado
    - Cada usuario debe tener un email único
    - Las contraseñas se almacenan hasheadas (nunca en texto plano)
    """
    __tablename__ = "users"
    
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Identificador único del usuario"
    )
    
    hashed_password: str = Field(
        description="Contraseña hasheada con bcrypt"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Fecha y hora de creación del usuario"
    )
    
    is_active: bool = Field(
        default=True,
        description="Indica si el usuario está activo en el sistema"
    )


class UserCreate(UserBase):
    """
    Schema para la creación de un nuevo usuario.
    Incluye la contraseña en texto plano que será hasheada.
    """
    password: str = Field(
        min_length=8,
        description="Contraseña en texto plano (será hasheada)"
    )


class UserRead(UserBase):
    """
    Schema para la lectura de datos de usuario.
    Excluye información sensible como la contraseña hasheada.
    """
    id: UUID
    created_at: datetime
    is_active: bool


class UserUpdate(SQLModel):
    """
    Schema para la actualización de un usuario existente.
    Todos los campos son opcionales.
    """
    email: Optional[str] = Field(None, description="Nuevo email del usuario")
    nombre: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre del usuario")
    rol: Optional[str] = Field(None, description="Nuevo rol del usuario")
    is_active: Optional[bool] = Field(None, description="Estado activo del usuario")
    password: Optional[str] = Field(None, min_length=8, description="Nueva contraseña en texto plano")


# Roles disponibles en el sistema según el diseño de negocio
class UserRole:
    """
    Constantes para los roles de usuario según el documento de diseño de negocio.
    """
    ADMINISTRADOR = "administrador"
    GERENTE_VENTAS = "gerente_ventas"
    CONTADOR = "contador"
    VENDEDOR = "vendedor"  # Rol por defecto
    
    @classmethod
    def all_roles(cls) -> list[str]:
        """Retorna todos los roles disponibles."""
        return [cls.ADMINISTRADOR, cls.GERENTE_VENTAS, cls.CONTADOR, cls.VENDEDOR]
    
    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """Verifica si un rol es válido."""
        return role in cls.all_roles() 