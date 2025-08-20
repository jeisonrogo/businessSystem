"""
Modelo de dominio para la entidad Usuario.
Define la estructura y reglas de negocio para los usuarios del sistema.
"""

from datetime import datetime, UTC
from typing import Optional, List
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship


class UserBase(SQLModel):
    """
    Campos base compartidos entre diferentes representaciones del modelo User.
    """
    email: str = Field(unique=True, index=True, description="Email único del usuario")
    nombre: str = Field(min_length=2, max_length=100, description="Nombre completo del usuario")
    rol: str = Field(default="vendedor", description="Rol del usuario en el sistema")


class User(UserBase, table=True):
    """
    Modelo de dominio para la entidad Usuario en sistema multi-tenant.
    Representa un usuario del sistema con capacidades de autenticación y autorización.
    
    Reglas de negocio:
    - BR-06: Los usuarios solo pueden acceder a las funciones permitidas por su rol asignado
    - Cada usuario debe tener un email único
    - Las contraseñas se almacenan hasheadas (nunca en texto plano)
    - En multi-tenant: Un usuario pertenece a una tienda específica
    - Puede tener permisos granulares en múltiples locales de su tienda
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
    
    # Relaciones multi-tenant
    tienda_id: Optional[UUID] = Field(
        default=None,
        foreign_key="tiendas.id",
        index=True,
        description="ID de la tienda a la que pertenece el usuario"
    )
    
    local_principal_id: Optional[UUID] = Field(
        default=None,
        foreign_key="locales.id",
        description="ID del local principal asignado al usuario"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Fecha y hora de creación del usuario"
    )
    
    is_active: bool = Field(
        default=True,
        description="Indica si el usuario está activo en el sistema"
    )
    
    # Relaciones
    tienda: Optional["Tienda"] = Relationship(back_populates="usuarios")
    local_principal: Optional["Local"] = Relationship()
    permisos_locales: List["UsuarioLocal"] = Relationship(
        back_populates="usuario",
        cascade_delete=True
    )
    
    # Actividades del usuario
    transferencias_solicitadas: List["TransferenciaInventario"] = Relationship(
        back_populates="usuario_solicita",
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_solicita_id"}
    )
    transferencias_enviadas: List["TransferenciaInventario"] = Relationship(
        back_populates="usuario_envia",
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_envia_id"}
    )
    transferencias_recibidas: List["TransferenciaInventario"] = Relationship(
        back_populates="usuario_recibe",
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.usuario_recibe_id"}
    )
    
    def tiene_acceso_a_tienda(self, tienda_id: UUID) -> bool:
        """
        Verifica si el usuario tiene acceso a una tienda específica.
        
        Args:
            tienda_id: ID de la tienda a verificar
            
        Returns:
            bool: True si tiene acceso
        """
        return self.tienda_id == tienda_id and self.is_active
    
    def tiene_acceso_a_local(self, local_id: UUID) -> bool:
        """
        Verifica si el usuario tiene algún permiso en el local específico.
        
        Args:
            local_id: ID del local a verificar
            
        Returns:
            bool: True si tiene permisos en el local
        """
        if not self.is_active:
            return False
            
        for permiso_local in self.permisos_locales:
            if permiso_local.local_id == local_id and permiso_local.is_active:
                return True
        return False
    
    def get_permisos_en_local(self, local_id: UUID) -> Optional["UsuarioLocal"]:
        """
        Obtiene los permisos específicos del usuario en un local.
        
        Args:
            local_id: ID del local
            
        Returns:
            UsuarioLocal o None si no tiene permisos
        """
        for permiso_local in self.permisos_locales:
            if permiso_local.local_id == local_id and permiso_local.is_active:
                return permiso_local
        return None
    
    def es_responsable_de_algun_local(self) -> bool:
        """Verifica si el usuario es responsable de al menos un local."""
        return any(
            permiso.es_responsable and permiso.is_active 
            for permiso in self.permisos_locales
        )
    
    def get_locales_responsable(self) -> List[UUID]:
        """Retorna lista de IDs de locales donde es responsable."""
        return [
            permiso.local_id 
            for permiso in self.permisos_locales 
            if permiso.es_responsable and permiso.is_active
        ]


class UserCreate(UserBase):
    """
    Schema para la creación de un nuevo usuario en sistema multi-tenant.
    Incluye la contraseña en texto plano que será hasheada.
    """
    password: str = Field(
        min_length=8,
        description="Contraseña en texto plano (será hasheada)"
    )
    tienda_id: Optional[UUID] = Field(
        None,
        description="ID de la tienda a la que pertenece el usuario"
    )
    local_principal_id: Optional[UUID] = Field(
        None,
        description="ID del local principal del usuario"
    )


class UserRead(UserBase):
    """
    Schema para la lectura de datos de usuario multi-tenant.
    Excluye información sensible como la contraseña hasheada.
    """
    id: UUID
    tienda_id: Optional[UUID]
    local_principal_id: Optional[UUID]
    created_at: datetime
    is_active: bool


class UserUpdate(SQLModel):
    """
    Schema para la actualización de un usuario existente multi-tenant.
    Todos los campos son opcionales.
    """
    email: Optional[str] = Field(None, description="Nuevo email del usuario")
    nombre: Optional[str] = Field(None, min_length=2, max_length=100, description="Nuevo nombre del usuario")
    rol: Optional[str] = Field(None, description="Nuevo rol del usuario")
    tienda_id: Optional[UUID] = Field(None, description="Nueva tienda del usuario")
    local_principal_id: Optional[UUID] = Field(None, description="Nuevo local principal del usuario")
    is_active: Optional[bool] = Field(None, description="Estado activo del usuario")
    password: Optional[str] = Field(None, min_length=8, description="Nueva contraseña en texto plano")


class UserResponse(UserRead):
    """Schema de respuesta para usuarios con información multi-tenant."""
    
    class Config:
        from_attributes = True


class UserWithPermissions(UserResponse):
    """Usuario con información de permisos por local."""
    permisos_locales: List["UsuarioLocalResponse"] = []
    es_responsable_de_algun_local: bool = False
    locales_responsable: List[UUID] = []


class UserWithTienda(UserResponse):
    """Usuario con información de su tienda."""
    tienda: Optional["TiendaResponse"] = None
    local_principal: Optional["LocalResponse"] = None


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