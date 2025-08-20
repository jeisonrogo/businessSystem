"""
Modelo de dominio para Tiendas en el sistema multi-tenant.

Una Tienda representa una línea de negocio independiente (ej: zapatos, vidrios).
Cada tienda tiene múltiples locales y maneja su propia numeración de facturas.
"""

from datetime import datetime, UTC
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator
from sqlmodel import SQLModel, Field as SQLField, Column, String, Integer, JSON, Relationship


class Tienda(SQLModel, table=True):
    """
    Modelo de dominio para Tiendas multi-tenant.
    
    Representa una línea de negocio independiente con:
    - Múltiples locales bajo su administración
    - Numeración consecutiva de facturas propia
    - Configuración específica del negocio
    - Aislamiento completo de datos
    """
    __tablename__ = "tiendas"
    
    id: UUID = SQLField(default_factory=uuid4, primary_key=True)
    codigo: str = SQLField(sa_column=Column(String(20), unique=True, nullable=False, index=True),
                          description="Código único de la tienda (ej: ZAPATOS, VIDRIOS)")
    nombre: str = SQLField(max_length=255, nullable=False,
                          description="Nombre comercial de la tienda")
    descripcion: Optional[str] = SQLField(default=None,
                                        description="Descripción del negocio de la tienda")
    
    # Configuración específica de la tienda
    dominio: Optional[str] = SQLField(sa_column=Column(String(100), unique=True, nullable=True),
                                    description="Dominio web específico (ej: zapatos.empresa.com)")
    configuracion: Optional[dict] = SQLField(sa_column=Column(JSON), default=None,
                                           description="Configuraciones específicas del negocio")
    
    # Numeración de facturas por tienda
    consecutivo_facturas: int = SQLField(default=1, ge=1,
                                       description="Próximo número consecutivo de factura")
    prefijo_facturas: str = SQLField(default="F", max_length=10,
                                   description="Prefijo para numeración de facturas")
    
    # Control de estado
    is_active: bool = SQLField(default=True, description="Estado activo de la tienda")
    created_at: datetime = SQLField(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = SQLField(default=None)
    
    # Relaciones
    locales: List["Local"] = Relationship(back_populates="tienda", cascade_delete=True)
    usuarios: List["User"] = Relationship(back_populates="tienda")
    productos: List["Product"] = Relationship(back_populates="tienda")
    clientes: List["Cliente"] = Relationship(back_populates="tienda")
    facturas: List["Factura"] = Relationship(back_populates="tienda")
    asientos_contables: List["AsientoContable"] = Relationship(back_populates="tienda")
    cuentas_contables: List["CuentaContable"] = Relationship(back_populates="tienda")

    @field_validator('codigo')
    @classmethod
    def codigo_uppercase(cls, v: str) -> str:
        """Convertir código a mayúsculas para consistencia."""
        return v.upper().strip()

    @field_validator('prefijo_facturas')
    @classmethod 
    def prefijo_uppercase(cls, v: str) -> str:
        """Convertir prefijo a mayúsculas para consistencia."""
        return v.upper().strip()

    def obtener_siguiente_numero_factura(self) -> str:
        """
        Genera el siguiente número de factura para esta tienda.
        
        Returns:
            str: Número de factura formateado (ej: "F-001")
        """
        numero_formateado = f"{self.prefijo_facturas}-{self.consecutivo_facturas:03d}"
        return numero_formateado

    def incrementar_consecutivo_factura(self) -> int:
        """
        Incrementa el consecutivo de facturas y retorna el número usado.
        
        Returns:
            int: El número consecutivo que se debe usar para la factura actual
        """
        numero_actual = self.consecutivo_facturas
        self.consecutivo_facturas += 1
        self.updated_at = datetime.now(UTC)
        return numero_actual


# Esquemas para la API
class TiendaBase(BaseModel):
    """Campos base compartidos para crear y actualizar tiendas."""
    codigo: str = Field(..., min_length=1, max_length=20, 
                       description="Código único de la tienda")
    nombre: str = Field(..., min_length=1, max_length=255,
                       description="Nombre comercial de la tienda")
    descripcion: Optional[str] = Field(None, description="Descripción del negocio")
    dominio: Optional[str] = Field(None, max_length=100,
                                  description="Dominio web específico")
    configuracion: Optional[dict] = Field(None, description="Configuraciones específicas")
    prefijo_facturas: str = Field("F", max_length=10,
                                 description="Prefijo para facturas")


class TiendaCreate(TiendaBase):
    """Esquema para crear una nueva tienda."""
    
    @field_validator('codigo')
    @classmethod
    def validate_codigo_format(cls, v: str) -> str:
        """Validar formato del código de tienda."""
        codigo_clean = v.upper().strip()
        if not codigo_clean.replace('_', '').replace('-', '').isalnum():
            raise ValueError('El código solo puede contener letras, números, guiones y guiones bajos')
        return codigo_clean


class TiendaUpdate(BaseModel):
    """Esquema para actualizar una tienda existente."""
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    descripcion: Optional[str] = Field(None)
    dominio: Optional[str] = Field(None, max_length=100)
    configuracion: Optional[dict] = Field(None)
    prefijo_facturas: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = Field(None)
    
    # Nota: código no se puede modificar después de creación


class TiendaResponse(BaseModel):
    """Esquema para respuestas de la API con información de la tienda."""
    id: UUID
    codigo: str
    nombre: str
    descripcion: Optional[str]
    dominio: Optional[str]
    configuracion: Optional[dict]
    consecutivo_facturas: int
    prefijo_facturas: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TiendaWithLocales(TiendaResponse):
    """Esquema que incluye los locales de la tienda."""
    locales: List["LocalResponse"] = []


class TiendaListResponse(BaseModel):
    """Esquema para respuestas de lista paginada de tiendas."""
    tiendas: List[TiendaResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


# Constantes
class TiendaStatus:
    """Estados posibles de una tienda."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class TiendaConfigKeys:
    """Claves estándar para configuración de tiendas."""
    TEMA_COLOR = "tema_color"
    LOGO_URL = "logo_url"
    MONEDA_DEFAULT = "moneda_default"
    ZONA_HORARIA = "zona_horaria"
    IDIOMA = "idioma"
    PERMITIR_VENTAS_CREDITO = "permitir_ventas_credito"
    DIAS_VENCIMIENTO_FACTURAS = "dias_vencimiento_facturas"