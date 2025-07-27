"""
Esquemas Pydantic para la API.
Define los modelos de datos de entrada y salida para los endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# Esquemas de autenticación
class LoginRequest(BaseModel):
    """
    Esquema para la solicitud de login.
    """
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class TokenResponse(BaseModel):
    """
    Esquema para la respuesta de token JWT.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")


class UserResponse(BaseModel):
    """
    Esquema para la respuesta de información de usuario.
    """
    id: str = Field(..., description="ID único del usuario")
    email: str = Field(..., description="Email del usuario")
    nombre: str = Field(..., description="Nombre completo del usuario")
    rol: str = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Estado activo del usuario")
    created_at: str = Field(..., description="Fecha de creación en formato ISO")


class LoginResponse(BaseModel):
    """
    Esquema para la respuesta completa de login.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Información del usuario")


class RegisterRequest(BaseModel):
    """
    Esquema para la solicitud de registro de usuario.
    """
    email: EmailStr = Field(..., description="Email único del usuario")
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre completo del usuario")
    rol: str = Field(default="vendedor", description="Rol del usuario en el sistema")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class RegisterResponse(BaseModel):
    """
    Esquema para la respuesta de registro de usuario.
    """
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="bearer", description="Tipo de token")
    user: UserResponse = Field(..., description="Información del usuario creado")
    message: str = Field(..., description="Mensaje de confirmación")


# Esquemas de error
class ErrorResponse(BaseModel):
    """
    Esquema para respuestas de error.
    """
    detail: str = Field(..., description="Descripción del error")
    error_code: Optional[str] = Field(None, description="Código de error específico")


class ValidationErrorResponse(BaseModel):
    """
    Esquema para errores de validación.
    """
    detail: str = Field(..., description="Descripción del error")
    field_errors: Optional[dict] = Field(None, description="Errores específicos de campos")


# Esquemas generales
class HealthResponse(BaseModel):
    """
    Esquema para la respuesta del endpoint de salud.
    """
    status: str = Field(default="ok", description="Estado del servicio")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de la respuesta")


class MessageResponse(BaseModel):
    """
    Esquema para respuestas con mensaje simple.
    """
    message: str = Field(..., description="Mensaje de respuesta")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa")


# Esquemas de productos
# Re-exportamos los esquemas del dominio para mantener la separación de capas
from app.domain.models.product import (
    ProductCreate as DomainProductCreate,
    ProductUpdate as DomainProductUpdate,
    ProductResponse as DomainProductResponse,
    ProductListResponse as DomainProductListResponse
)


# Esquemas específicos para la API de productos
class ProductCreateRequest(DomainProductCreate):
    """
    Esquema para la solicitud de creación de producto.
    Hereda de DomainProductCreate para mantener la consistencia.
    """
    pass


class ProductUpdateRequest(DomainProductUpdate):
    """
    Esquema para la solicitud de actualización de producto.
    Hereda de DomainProductUpdate para mantener la consistencia.
    """
    pass


class ProductResponse(DomainProductResponse):
    """
    Esquema para la respuesta de información de producto.
    Hereda de DomainProductResponse para mantener la consistencia.
    """
    pass


class ProductListResponse(DomainProductListResponse):
    """
    Esquema para la respuesta de lista paginada de productos.
    Hereda de DomainProductListResponse para mantener la consistencia.
    """
    pass


class ProductStockUpdateRequest(BaseModel):
    """
    Esquema para la solicitud de actualización de stock.
    """
    stock: int = Field(..., ge=0, description="Nueva cantidad de stock (no puede ser negativo)")


class ProductStockUpdateResponse(BaseModel):
    """
    Esquema para la respuesta de actualización de stock.
    """
    product_id: UUID = Field(..., description="ID del producto actualizado")
    previous_stock: int = Field(..., description="Stock anterior")
    new_stock: int = Field(..., description="Stock actualizado")
    message: str = Field(..., description="Mensaje de confirmación")


class LowStockThresholdRequest(BaseModel):
    """
    Esquema para la solicitud de productos con stock bajo.
    """
    threshold: int = Field(10, ge=0, description="Umbral mínimo de stock")


class ProductDeleteResponse(BaseModel):
    """
    Esquema para la respuesta de eliminación de producto.
    """
    product_id: UUID = Field(..., description="ID del producto eliminado")
    message: str = Field(..., description="Mensaje de confirmación")
    success: bool = Field(default=True, description="Indica si la operación fue exitosa") 