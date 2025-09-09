"""
Modelo de dominio para Locales en el sistema multi-tenant.

Un Local representa un punto de venta específico dentro de una Tienda.
Cada local maneja su propio inventario y puede tener usuarios asignados.
"""

from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, JSON, Relationship


class Local(SQLModel, table=True):
    """
    Modelo de dominio para Locales multi-tenant.
    
    Representa un punto de venta específico dentro de una tienda con:
    - Inventario independiente por productos
    - Usuarios asignados con permisos específicos
    - Ubicación física y datos de contacto
    - Configuración específica del local
    """
    __tablename__ = "locales"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    tienda_id: UUID = SQLField(foreign_key="tiendas.id", nullable=False, index=True,
                              description="ID de la tienda a la que pertenece")
    
    # Identificación del local
    codigo: str = SQLField(max_length=20, nullable=False, index=True,
                          description="Código único del local dentro de la tienda (ej: CENTRO, NORTE)")
    nombre: str = SQLField(max_length=255, nullable=False,
                          description="Nombre descriptivo del local")
    
    # Información de ubicación
    direccion: Optional[str] = SQLField(default=None, max_length=500,
                                      description="Dirección física del local")
    ciudad: Optional[str] = SQLField(default=None, max_length=100,
                                   description="Ciudad donde se encuentra el local")
    departamento: Optional[str] = SQLField(default=None, max_length=100,
                                         description="Departamento/Estado del local")
    codigo_postal: Optional[str] = SQLField(default=None, max_length=10,
                                          description="Código postal del local")
    telefono: Optional[str] = SQLField(default=None, max_length=20,
                                     description="Teléfono de contacto del local")
    email: Optional[str] = SQLField(default=None, max_length=255,
                                  description="Email de contacto del local")
    
    # Configuración específica del local
    configuracion: Optional[dict] = SQLField(sa_column=Column(JSON), default=None,
                                           description="Configuraciones específicas del local")
    
    # Control de estado
    is_active: bool = SQLField(default=True, description="Estado activo del local")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    
    # Relaciones
    tienda: "Tienda" = Relationship(back_populates="locales")
    stock_productos: List["StockLocal"] = Relationship(back_populates="local", cascade_delete=True)
    usuarios_locales: List["UsuarioLocal"] = Relationship(back_populates="local", cascade_delete=True)
    facturas: List["Factura"] = Relationship(back_populates="local")
    movimientos_inventario: List["MovimientoInventario"] = Relationship(back_populates="local")
    transferencias_origen: List["TransferenciaInventario"] = Relationship(
        back_populates="local_origen",
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.local_origen_id"}
    )
    transferencias_destino: List["TransferenciaInventario"] = Relationship(
        back_populates="local_destino", 
        sa_relationship_kwargs={"foreign_keys": "TransferenciaInventario.local_destino_id"}
    )
    # Temporarily disabled until these relationships are properly implemented
    # clientes_origen: List["Cliente"] = Relationship(back_populates="local_origen")
    # asientos_contables: List["AsientoContable"] = Relationship(back_populates="local")
    
    @field_validator('codigo')
    @classmethod
    def codigo_uppercase_alphanumeric(cls, v: str) -> str:
        """Convertir código a mayúsculas y validar formato."""
        codigo_clean = v.upper().strip()
        if not codigo_clean.replace('_', '').replace('-', '').isalnum():
            raise ValueError('El código solo puede contener letras, números, guiones y guiones bajos')
        return codigo_clean

    def get_direccion_completa(self) -> str:
        """
        Retorna la dirección completa formateada del local.
        
        Returns:
            str: Dirección completa o 'Sin dirección' si no está definida
        """
        if not self.direccion:
            return "Sin dirección"
        
        partes = [self.direccion]
        if self.ciudad:
            partes.append(self.ciudad)
        if self.departamento:
            partes.append(self.departamento)
        if self.codigo_postal:
            partes.append(f"CP: {self.codigo_postal}")
            
        return ", ".join(partes)

    def actualizar_timestamp(self) -> None:
        """Actualiza el timestamp de modificación."""
        self.updated_at = datetime.now(UTC)


# Esquemas para la API
class LocalBase(BaseModel):
    """Campos base compartidos para crear y actualizar locales."""
    codigo: str = Field(..., min_length=1, max_length=20,
                       description="Código único del local dentro de la tienda")
    nombre: str = Field(..., min_length=1, max_length=255,
                       description="Nombre descriptivo del local")
    direccion: Optional[str] = Field(None, max_length=500,
                                   description="Dirección física del local")
    ciudad: Optional[str] = Field(None, max_length=100,
                                description="Ciudad del local")
    departamento: Optional[str] = Field(None, max_length=100,
                                      description="Departamento/Estado del local")
    codigo_postal: Optional[str] = Field(None, max_length=10,
                                       description="Código postal")
    telefono: Optional[str] = Field(None, max_length=20,
                                  description="Teléfono de contacto")
    email: Optional[str] = Field(None, max_length=255,
                               description="Email de contacto")
    configuracion: Optional[dict] = Field(None,
                                        description="Configuraciones específicas")


class LocalCreate(LocalBase):
    """Esquema para crear un nuevo local."""
    tienda_id: UUID = Field(..., description="ID de la tienda a la que pertenece")
    
    @field_validator('codigo')
    @classmethod
    def validate_codigo_format(cls, v: str) -> str:
        """Validar formato del código de local."""
        codigo_clean = v.upper().strip()
        if not codigo_clean.replace('_', '').replace('-', '').isalnum():
            raise ValueError('El código solo puede contener letras, números, guiones y guiones bajos')
        return codigo_clean

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de email si se proporciona."""
        if v and '@' not in v:
            raise ValueError('Formato de email inválido')
        return v


class LocalUpdate(BaseModel):
    """Esquema para actualizar un local existente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    direccion: Optional[str] = Field(None, max_length=500)
    ciudad: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=10)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    configuracion: Optional[dict] = Field(None)
    is_active: Optional[bool] = Field(None)
    
    # Nota: código y tienda_id no se pueden modificar después de creación

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validar formato de email si se proporciona."""
        if v and '@' not in v:
            raise ValueError('Formato de email inválido')
        return v


class LocalResponse(BaseModel):
    """Esquema para respuestas de la API con información del local."""
    id: UUID
    tienda_id: UUID
    codigo: str
    nombre: str
    direccion: Optional[str]
    ciudad: Optional[str]
    departamento: Optional[str]
    codigo_postal: Optional[str]
    telefono: Optional[str]
    email: Optional[str]
    configuracion: Optional[dict]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Campos calculados
    direccion_completa: Optional[str] = None
    
    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_direccion(cls, local: Local) -> "LocalResponse":
        """Crear respuesta incluyendo dirección completa calculada."""
        response = cls.model_validate(local)
        response.direccion_completa = local.get_direccion_completa()
        return response


class LocalWithStock(LocalResponse):
    """Esquema que incluye información de stock del local."""
    total_productos_con_stock: int = 0
    valor_total_inventario: float = 0.0


class LocalWithPermisos(LocalResponse):
    """Esquema que incluye los permisos del usuario actual en el local."""
    permisos: "PermisosLocalResponse" = None


class LocalListResponse(BaseModel):
    """Esquema para respuestas de lista paginada de locales."""
    locales: List[LocalResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


# Constantes
class LocalStatus:
    """Estados posibles de un local."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"


class LocalConfigKeys:
    """Claves estándar para configuración de locales."""
    HORARIO_APERTURA = "horario_apertura"
    HORARIO_CIERRE = "horario_cierre"
    DIAS_OPERACION = "dias_operacion"
    RESPONSABLE_ID = "responsable_id"
    ALMACEN_PRINCIPAL = "almacen_principal"
    PERMITE_VENTAS_CREDITO = "permite_ventas_credito"
    LIMITE_DESCUENTO = "limite_descuento_porcentaje"
    IMPRESORA_FACTURAS = "impresora_facturas"
    CAJA_REGISTRADORA = "caja_registradora"