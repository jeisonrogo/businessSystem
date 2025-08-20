"""
Modelo de dominio para Permisos de Usuario por Local.

Define los permisos granulares que tiene cada usuario en cada local específico,
permitiendo control de acceso detallado por operación y ubicación.
"""

from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field as SQLField, Relationship


class PermisoLocal(str, Enum):
    """Permisos específicos que un usuario puede tener en un local."""
    VER_STOCK = "ver_stock"                    # Puede ver inventario del local
    VENDER = "vender"                          # Puede crear facturas en el local
    TRANSFERIR = "transferir"                  # Puede crear transferencias desde el local
    RESPONSABLE = "responsable"                # Es responsable/administrador del local
    MODIFICAR_PRECIOS = "modificar_precios"    # Puede modificar precios de productos
    APLICAR_DESCUENTOS = "aplicar_descuentos"  # Puede aplicar descuentos en ventas
    VER_REPORTES = "ver_reportes"              # Puede acceder a reportes del local
    GESTIONAR_USUARIOS = "gestionar_usuarios"  # Puede gestionar usuarios del local


class UsuarioLocal(SQLModel, table=True):
    """
    Modelo de dominio para Permisos Usuario-Local.
    
    Define los permisos específicos que tiene un usuario en un local:
    - Permisos granulares por operación
    - Control de acceso basado en ubicación
    - Auditoría de asignación de permisos
    - Flexibilidad para diferentes roles por local
    """
    __tablename__ = "usuario_locales"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    user_id: UUID = SQLField(foreign_key="users.id", nullable=False, index=True,
                            description="ID del usuario")
    local_id: UUID = SQLField(foreign_key="locales.id", nullable=False, index=True,
                             description="ID del local")
    
    # Permisos específicos
    puede_vender: bool = SQLField(default=True, description="Puede crear facturas en este local")
    puede_ver_stock: bool = SQLField(default=True, description="Puede ver inventario del local")
    puede_transferir: bool = SQLField(default=False, description="Puede crear transferencias")
    es_responsable: bool = SQLField(default=False, description="Es responsable del local")
    puede_modificar_precios: bool = SQLField(default=False, description="Puede modificar precios")
    puede_aplicar_descuentos: bool = SQLField(default=False, description="Puede aplicar descuentos")
    puede_ver_reportes: bool = SQLField(default=False, description="Puede ver reportes")
    puede_gestionar_usuarios: bool = SQLField(default=False, description="Puede gestionar usuarios")
    
    # Límites específicos
    limite_descuento_porcentaje: Optional[float] = SQLField(default=None, ge=0, le=100,
                                                           description="Límite máximo de descuento %")
    limite_credito_monto: Optional[float] = SQLField(default=None, ge=0,
                                                    description="Límite máximo para ventas a crédito")
    
    # Control y auditoría
    is_active: bool = SQLField(default=True, description="Permisos activos")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    created_by: Optional[UUID] = SQLField(foreign_key="users.id", default=None,
                                        description="Usuario que asignó los permisos")
    
    # Relaciones
    usuario: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UsuarioLocal.user_id"}
    )
    local: "Local" = Relationship(back_populates="usuarios_locales")
    usuario_creador: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "UsuarioLocal.created_by"}
    )
    
    # Índice único: un usuario solo puede tener un registro de permisos por local
    __table_args__ = (
        {"extend_existing": True},
    )

    def get_permisos_activos(self) -> List[PermisoLocal]:
        """
        Retorna la lista de permisos activos del usuario en el local.
        
        Returns:
            List[PermisoLocal]: Lista de permisos que el usuario tiene
        """
        permisos = []
        
        if self.puede_ver_stock:
            permisos.append(PermisoLocal.VER_STOCK)
        if self.puede_vender:
            permisos.append(PermisoLocal.VENDER)
        if self.puede_transferir:
            permisos.append(PermisoLocal.TRANSFERIR)
        if self.es_responsable:
            permisos.append(PermisoLocal.RESPONSABLE)
        if self.puede_modificar_precios:
            permisos.append(PermisoLocal.MODIFICAR_PRECIOS)
        if self.puede_aplicar_descuentos:
            permisos.append(PermisoLocal.APLICAR_DESCUENTOS)
        if self.puede_ver_reportes:
            permisos.append(PermisoLocal.VER_REPORTES)
        if self.puede_gestionar_usuarios:
            permisos.append(PermisoLocal.GESTIONAR_USUARIOS)
            
        return permisos

    def tiene_permiso(self, permiso: PermisoLocal) -> bool:
        """
        Verifica si el usuario tiene un permiso específico en el local.
        
        Args:
            permiso: Permiso a verificar
            
        Returns:
            bool: True si tiene el permiso
        """
        if not self.is_active:
            return False
            
        permiso_map = {
            PermisoLocal.VER_STOCK: self.puede_ver_stock,
            PermisoLocal.VENDER: self.puede_vender,
            PermisoLocal.TRANSFERIR: self.puede_transferir,
            PermisoLocal.RESPONSABLE: self.es_responsable,
            PermisoLocal.MODIFICAR_PRECIOS: self.puede_modificar_precios,
            PermisoLocal.APLICAR_DESCUENTOS: self.puede_aplicar_descuentos,
            PermisoLocal.VER_REPORTES: self.puede_ver_reportes,
            PermisoLocal.GESTIONAR_USUARIOS: self.puede_gestionar_usuarios,
        }
        
        return permiso_map.get(permiso, False)

    def puede_aplicar_descuento(self, porcentaje_descuento: float) -> bool:
        """
        Verifica si el usuario puede aplicar un descuento específico.
        
        Args:
            porcentaje_descuento: Porcentaje de descuento a aplicar
            
        Returns:
            bool: True si puede aplicar el descuento
        """
        if not self.puede_aplicar_descuentos or not self.is_active:
            return False
            
        if self.limite_descuento_porcentaje is None:
            return True
            
        return porcentaje_descuento <= self.limite_descuento_porcentaje

    def puede_venta_credito(self, monto: float) -> bool:
        """
        Verifica si el usuario puede realizar una venta a crédito por el monto dado.
        
        Args:
            monto: Monto de la venta a crédito
            
        Returns:
            bool: True si puede realizar la venta
        """
        if not self.puede_vender or not self.is_active:
            return False
            
        if self.limite_credito_monto is None:
            return True
            
        return monto <= self.limite_credito_monto

    def actualizar_timestamp(self) -> None:
        """Actualiza el timestamp de modificación."""
        self.updated_at = datetime.now(UTC)

    @classmethod
    def crear_permisos_vendedor(
        cls, 
        user_id: UUID, 
        local_id: UUID, 
        created_by: Optional[UUID] = None
    ) -> "UsuarioLocal":
        """
        Crea permisos básicos de vendedor para un usuario en un local.
        
        Args:
            user_id: ID del usuario
            local_id: ID del local
            created_by: ID del usuario que crea los permisos
            
        Returns:
            UsuarioLocal: Instancia con permisos de vendedor
        """
        return cls(
            user_id=user_id,
            local_id=local_id,
            puede_vender=True,
            puede_ver_stock=True,
            puede_transferir=False,
            es_responsable=False,
            puede_modificar_precios=False,
            puede_aplicar_descuentos=True,
            puede_ver_reportes=False,
            puede_gestionar_usuarios=False,
            limite_descuento_porcentaje=5.0,  # 5% máximo para vendedores
            created_by=created_by
        )

    @classmethod
    def crear_permisos_responsable(
        cls, 
        user_id: UUID, 
        local_id: UUID, 
        created_by: Optional[UUID] = None
    ) -> "UsuarioLocal":
        """
        Crea permisos completos de responsable para un usuario en un local.
        
        Args:
            user_id: ID del usuario
            local_id: ID del local
            created_by: ID del usuario que crea los permisos
            
        Returns:
            UsuarioLocal: Instancia con permisos de responsable
        """
        return cls(
            user_id=user_id,
            local_id=local_id,
            puede_vender=True,
            puede_ver_stock=True,
            puede_transferir=True,
            es_responsable=True,
            puede_modificar_precios=True,
            puede_aplicar_descuentos=True,
            puede_ver_reportes=True,
            puede_gestionar_usuarios=True,
            limite_descuento_porcentaje=20.0,  # 20% máximo para responsables
            created_by=created_by
        )


# Esquemas para la API
class PermisosLocalBase(BaseModel):
    """Campos base para permisos por local."""
    puede_vender: bool = Field(True, description="Puede crear facturas")
    puede_ver_stock: bool = Field(True, description="Puede ver inventario")
    puede_transferir: bool = Field(False, description="Puede crear transferencias")
    es_responsable: bool = Field(False, description="Es responsable del local")
    puede_modificar_precios: bool = Field(False, description="Puede modificar precios")
    puede_aplicar_descuentos: bool = Field(False, description="Puede aplicar descuentos")
    puede_ver_reportes: bool = Field(False, description="Puede ver reportes")
    puede_gestionar_usuarios: bool = Field(False, description="Puede gestionar usuarios")
    limite_descuento_porcentaje: Optional[float] = Field(None, ge=0, le=100, description="Límite de descuento %")
    limite_credito_monto: Optional[float] = Field(None, ge=0, description="Límite de crédito")


class UsuarioLocalCreate(PermisosLocalBase):
    """Esquema para asignar permisos a un usuario en un local."""
    user_id: UUID = Field(..., description="ID del usuario")
    local_id: UUID = Field(..., description="ID del local")


class UsuarioLocalUpdate(PermisosLocalBase):
    """Esquema para actualizar permisos existentes."""
    is_active: Optional[bool] = Field(None, description="Estado de los permisos")


class PermisosLocalResponse(BaseModel):
    """Esquema para respuestas de permisos por local."""
    ver_stock: bool
    vender: bool
    transferir: bool
    responsable: bool
    modificar_precios: bool
    aplicar_descuentos: bool
    ver_reportes: bool
    gestionar_usuarios: bool
    limite_descuento_porcentaje: Optional[float]
    limite_credito_monto: Optional[float]
    
    class Config:
        from_attributes = True


class UsuarioLocalResponse(BaseModel):
    """Esquema para respuestas de usuario-local completas."""
    id: UUID
    user_id: UUID
    local_id: UUID
    puede_vender: bool
    puede_ver_stock: bool
    puede_transferir: bool
    es_responsable: bool
    puede_modificar_precios: bool
    puede_aplicar_descuentos: bool
    puede_ver_reportes: bool
    puede_gestionar_usuarios: bool
    limite_descuento_porcentaje: Optional[float]
    limite_credito_monto: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    
    # Campos calculados
    permisos_activos: List[str] = []
    
    class Config:
        from_attributes = True


class UsuarioLocalConDetalles(UsuarioLocalResponse):
    """Usuario-local con información del usuario y local."""
    usuario: "UserResponse" = None
    local: "LocalResponse" = None


class PermisosResumenPorUsuario(BaseModel):
    """Resumen de permisos de un usuario en todos sus locales."""
    user_id: UUID
    usuario_nombre: str
    total_locales_asignados: int
    locales_responsable: int
    locales_puede_vender: int
    locales_puede_transferir: int
    permisos_por_local: List[UsuarioLocalResponse]


# Constantes y plantillas
class PerfilPermisos:
    """Perfiles predefinidos de permisos."""
    
    VENDEDOR = {
        "puede_vender": True,
        "puede_ver_stock": True,
        "puede_transferir": False,
        "es_responsable": False,
        "puede_modificar_precios": False,
        "puede_aplicar_descuentos": True,
        "puede_ver_reportes": False,
        "puede_gestionar_usuarios": False,
        "limite_descuento_porcentaje": 5.0
    }
    
    RESPONSABLE_LOCAL = {
        "puede_vender": True,
        "puede_ver_stock": True,
        "puede_transferir": True,
        "es_responsable": True,
        "puede_modificar_precios": True,
        "puede_aplicar_descuentos": True,
        "puede_ver_reportes": True,
        "puede_gestionar_usuarios": True,
        "limite_descuento_porcentaje": 20.0
    }
    
    SUPERVISOR = {
        "puede_vender": True,
        "puede_ver_stock": True,
        "puede_transferir": True,
        "es_responsable": False,
        "puede_modificar_precios": False,
        "puede_aplicar_descuentos": True,
        "puede_ver_reportes": True,
        "puede_gestionar_usuarios": False,
        "limite_descuento_porcentaje": 10.0
    }
    
    SOLO_CONSULTA = {
        "puede_vender": False,
        "puede_ver_stock": True,
        "puede_transferir": False,
        "es_responsable": False,
        "puede_modificar_precios": False,
        "puede_aplicar_descuentos": False,
        "puede_ver_reportes": True,
        "puede_gestionar_usuarios": False
    }