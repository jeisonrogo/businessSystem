"""
Modelo de contexto para Multi-Tenant.

Define el contexto de tenant que se propaga a través de toda la aplicación,
incluyendo información de tienda, local activo y permisos del usuario.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class TenantContextType(str, Enum):
    """Tipos de contexto multi-tenant."""
    TIENDA_ONLY = "tienda_only"      # Solo contexto de tienda
    TIENDA_LOCAL = "tienda_local"    # Contexto completo tienda + local


class TenantContext(BaseModel):
    """
    Contexto de tenant que se propaga a través de la aplicación.
    
    Contiene toda la información necesaria para:
    - Filtrar datos por tienda/local
    - Validar permisos por ubicación
    - Personalizar comportamiento por contexto
    """
    
    # Contexto principal
    tienda_id: UUID = Field(..., description="ID de la tienda activa")
    tienda_codigo: str = Field(..., description="Código de la tienda activa")
    tienda_nombre: str = Field(..., description="Nombre de la tienda activa")
    
    # Contexto de local (opcional)
    local_id: Optional[UUID] = Field(None, description="ID del local activo")
    local_codigo: Optional[str] = Field(None, description="Código del local activo")
    local_nombre: Optional[str] = Field(None, description="Nombre del local activo")
    
    # Usuario y permisos
    user_id: UUID = Field(..., description="ID del usuario actual")
    user_nombre: str = Field(..., description="Nombre del usuario actual")
    user_rol: str = Field(..., description="Rol base del usuario")
    
    # Permisos por local (UUID del local -> lista de permisos)
    permisos_locales: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Permisos del usuario por local"
    )
    
    # Configuraciones de contexto
    tipo_contexto: TenantContextType = Field(
        default=TenantContextType.TIENDA_ONLY,
        description="Tipo de contexto activo"
    )
    
    class Config:
        use_enum_values = True

    @property
    def tiene_contexto_local(self) -> bool:
        """Verifica si el contexto incluye un local específico."""
        return self.local_id is not None and self.tipo_contexto == TenantContextType.TIENDA_LOCAL

    def get_filters_base(self) -> Dict[str, Any]:
        """
        Retorna filtros base para queries que requieren contexto de tienda.
        
        Returns:
            Dict[str, Any]: Filtros para aplicar en queries
        """
        return {"tienda_id": self.tienda_id}

    def get_filters_con_local(self) -> Dict[str, Any]:
        """
        Retorna filtros incluyendo local si está disponible.
        
        Returns:
            Dict[str, Any]: Filtros para aplicar en queries
        """
        filters = self.get_filters_base()
        if self.tiene_contexto_local:
            filters["local_id"] = self.local_id
        return filters

    def puede_vender_en_local(self, local_id: UUID) -> bool:
        """
        Verifica si el usuario puede vender en el local específico.
        
        Args:
            local_id: ID del local a verificar
            
        Returns:
            bool: True si puede vender en el local
        """
        local_key = str(local_id)
        permisos = self.permisos_locales.get(local_key, [])
        return "vender" in permisos

    def puede_ver_stock_local(self, local_id: UUID) -> bool:
        """
        Verifica si el usuario puede ver stock del local específico.
        
        Args:
            local_id: ID del local a verificar
            
        Returns:
            bool: True si puede ver stock del local
        """
        local_key = str(local_id)
        permisos = self.permisos_locales.get(local_key, [])
        return "ver_stock" in permisos

    def puede_transferir_desde_local(self, local_id: UUID) -> bool:
        """
        Verifica si el usuario puede crear transferencias desde el local.
        
        Args:
            local_id: ID del local a verificar
            
        Returns:
            bool: True si puede transferir desde el local
        """
        local_key = str(local_id)
        permisos = self.permisos_locales.get(local_key, [])
        return "transferir" in permisos

    def es_responsable_local(self, local_id: UUID) -> bool:
        """
        Verifica si el usuario es responsable del local específico.
        
        Args:
            local_id: ID del local a verificar
            
        Returns:
            bool: True si es responsable del local
        """
        local_key = str(local_id)
        permisos = self.permisos_locales.get(local_key, [])
        return "responsable" in permisos

    def tiene_permiso_en_local(self, local_id: UUID, permiso: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico en el local.
        
        Args:
            local_id: ID del local a verificar
            permiso: Permiso a verificar (string)
            
        Returns:
            bool: True si tiene el permiso
        """
        local_key = str(local_id)
        permisos = self.permisos_locales.get(local_key, [])
        return permiso in permisos

    def get_locales_con_permiso(self, permiso: str) -> List[UUID]:
        """
        Retorna lista de locales donde el usuario tiene el permiso especificado.
        
        Args:
            permiso: Permiso a buscar (string)
            
        Returns:
            List[UUID]: Lista de IDs de locales con el permiso
        """
        locales_con_permiso = []
        for local_key, permisos in self.permisos_locales.items():
            if permiso in permisos:
                try:
                    locales_con_permiso.append(UUID(local_key))
                except ValueError:
                    continue  # Ignorar claves inválidas
        return locales_con_permiso

    def get_locales_venta_permitidos(self) -> List[UUID]:
        """
        Retorna locales donde el usuario puede realizar ventas.
        
        Returns:
            List[UUID]: Lista de IDs de locales donde puede vender
        """
        return self.get_locales_con_permiso("vender")

    def get_locales_transferencia_permitidos(self) -> List[UUID]:
        """
        Retorna locales desde donde el usuario puede crear transferencias.
        
        Returns:
            List[UUID]: Lista de IDs de locales donde puede transferir
        """
        return self.get_locales_con_permiso("transferir")

    def get_locales_responsable(self) -> List[UUID]:
        """
        Retorna locales donde el usuario es responsable.
        
        Returns:
            List[UUID]: Lista de IDs de locales donde es responsable
        """
        return self.get_locales_con_permiso("responsable")

    def validar_operacion_en_contexto_actual(self, operacion: str) -> bool:
        """
        Valida si una operación se puede realizar en el contexto actual.
        
        Args:
            operacion: Tipo de operación ('venta', 'transferencia', etc.)
            
        Returns:
            bool: True si la operación es válida en el contexto actual
        """
        if not self.tiene_contexto_local:
            # Sin contexto de local, solo operaciones a nivel tienda
            return operacion in ['consulta_tienda', 'reporte_consolidado']
        
        # Con contexto de local, verificar permisos específicos
        operacion_permiso_map = {
            'venta': 'vender',
            'transferencia': 'transferir',
            'consulta_stock': 'ver_stock',
            'gestion_usuarios': 'gestionar_usuarios',
            'modificar_precios': 'modificar_precios',
            'ver_reportes': 'ver_reportes',
        }
        
        permiso_requerido = operacion_permiso_map.get(operacion)
        if permiso_requerido:
            return self.tiene_permiso_en_local(self.local_id, permiso_requerido)
        
        return False

    def cambiar_contexto_local(self, local_id: UUID, local_codigo: str, local_nombre: str) -> None:
        """
        Cambia el contexto activo a un local específico.
        
        Args:
            local_id: ID del nuevo local activo
            local_codigo: Código del nuevo local activo
            local_nombre: Nombre del nuevo local activo
        """
        self.local_id = local_id
        self.local_codigo = local_codigo
        self.local_nombre = local_nombre
        self.tipo_contexto = TenantContextType.TIENDA_LOCAL

    def limpiar_contexto_local(self) -> None:
        """Limpia el contexto de local, dejando solo el contexto de tienda."""
        self.local_id = None
        self.local_codigo = None
        self.local_nombre = None
        self.tipo_contexto = TenantContextType.TIENDA_ONLY

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el contexto a diccionario para serialización.
        
        Returns:
            Dict[str, Any]: Contexto serializado
        """
        return {
            "tienda_id": str(self.tienda_id),
            "tienda_codigo": self.tienda_codigo,
            "tienda_nombre": self.tienda_nombre,
            "local_id": str(self.local_id) if self.local_id else None,
            "local_codigo": self.local_codigo,
            "local_nombre": self.local_nombre,
            "user_id": str(self.user_id),
            "user_nombre": self.user_nombre,
            "user_rol": self.user_rol,
            "tipo_contexto": self.tipo_contexto.value,
            "permisos_locales": self.permisos_locales,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenantContext":
        """
        Crea un contexto desde un diccionario.
        
        Args:
            data: Diccionario con datos del contexto
            
        Returns:
            TenantContext: Instancia del contexto
        """
        return cls(
            tienda_id=UUID(data["tienda_id"]),
            tienda_codigo=data["tienda_codigo"],
            tienda_nombre=data["tienda_nombre"],
            local_id=UUID(data["local_id"]) if data.get("local_id") else None,
            local_codigo=data.get("local_codigo"),
            local_nombre=data.get("local_nombre"),
            user_id=UUID(data["user_id"]),
            user_nombre=data["user_nombre"],
            user_rol=data["user_rol"],
            tipo_contexto=TenantContextType(data.get("tipo_contexto", TenantContextType.TIENDA_ONLY)),
            permisos_locales=data.get("permisos_locales", {}),
        )


# Esquemas para API de contexto
class TenantContextResponse(BaseModel):
    """Esquema para respuestas de contexto de tenant."""
    tienda_id: UUID
    tienda_codigo: str
    tienda_nombre: str
    local_id: Optional[UUID]
    local_codigo: Optional[str]
    local_nombre: Optional[str]
    tipo_contexto: TenantContextType
    locales_disponibles: List["LocalResponse"] = []
    permisos_en_contexto_actual: List[str] = []
    
    class Config:
        use_enum_values = True


class CambiarContextoRequest(BaseModel):
    """Esquema para solicitudes de cambio de contexto."""
    local_id: Optional[UUID] = Field(None, description="ID del local (None para contexto solo tienda)")


class ContextoDisponibleResponse(BaseModel):
    """Esquema para contextos disponibles del usuario."""
    tiendas_disponibles: List["TiendaResponse"] = []
    locales_por_tienda: Dict[str, List["LocalResponse"]] = {}
    contexto_actual: TenantContextResponse = None


# Excepciones específicas del contexto
class TenantContextError(Exception):
    """Error base para contexto de tenant."""
    pass


class PermisoInsuficienteError(TenantContextError):
    """Error cuando el usuario no tiene permisos suficientes."""
    def __init__(self, permiso_requerido: str, local_id: Optional[UUID] = None):
        self.permiso_requerido = permiso_requerido
        self.local_id = local_id
        mensaje = f"Permiso insuficiente: se requiere '{permiso_requerido}'"
        if local_id:
            mensaje += f" en local {local_id}"
        super().__init__(mensaje)


class ContextoInvalidoError(TenantContextError):
    """Error cuando el contexto no es válido para la operación."""
    pass