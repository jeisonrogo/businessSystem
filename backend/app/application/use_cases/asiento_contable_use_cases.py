"""
Casos de uso para la gestión de asientos contables manuales.
Implementa la lógica de negocio para la creación y gestión de asientos contables
siguiendo los principios de doble partida.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.application.services.i_asiento_contable_repository import IAsientoContableRepository
from app.domain.models.contabilidad import (
    AsientoContable,
    AsientoContableCreate,
    AsientoContableResponse,
    AsientoContableListResponse,
    DetalleAsiento,
    DetalleAsientoCreate,
    TipoMovimiento
)


# ==================== EXCEPCIONES ====================

class AsientoContableError(Exception):
    """Excepción base para errores de asientos contables."""
    pass


class AsientoContableNotFoundError(AsientoContableError):
    """Error cuando un asiento contable no es encontrado."""
    pass


class DesequilibrioContableError(AsientoContableError):
    """Error cuando un asiento contable no está balanceado (débitos ≠ créditos)."""
    pass


class CuentaInactivaError(AsientoContableError):
    """Error cuando se intenta usar una cuenta inactiva en un asiento."""
    pass


class AsientoContableDuplicadoError(AsientoContableError):
    """Error cuando se intenta crear un asiento con comprobante duplicado."""
    pass



# ==================== CASOS DE USO ====================

class CreateAsientoContableUseCase:
    """Caso de uso para crear un nuevo asiento contable manual."""
    
    def __init__(
        self, 
        asiento_repository: IAsientoContableRepository,
        cuenta_repository: ICuentaContableRepository
    ):
        self.asiento_repository = asiento_repository
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, asiento_data: AsientoContableCreate) -> AsientoContable:
        """
        Crear un nuevo asiento contable con validaciones de negocio.
        
        Args:
            asiento_data: Datos del asiento contable
            
        Returns:
            AsientoContable: El asiento creado
            
        Raises:
            DesequilibrioContableError: Si débitos ≠ créditos
            CuentaInactivaError: Si alguna cuenta está inactiva
            AsientoContableDuplicadoError: Si el comprobante ya existe
        """
        # 1. Validar que no existe asiento con el mismo comprobante
        if asiento_data.comprobante:
            existing = await self.asiento_repository.get_by_comprobante(asiento_data.comprobante)
            if existing:
                raise AsientoContableDuplicadoError(
                    f"Ya existe un asiento contable con el comprobante {asiento_data.comprobante}"
                )
        
        # 2. Validar que todas las cuentas existen y están activas
        for detalle in asiento_data.detalles:
            cuenta = await self.cuenta_repository.get_by_id(detalle.cuenta_contable_id)
            if not cuenta:
                raise AsientoContableError(
                    f"La cuenta contable con ID {detalle.cuenta_contable_id} no existe"
                )
            if not cuenta.is_active:
                raise CuentaInactivaError(
                    f"La cuenta {cuenta.codigo} - {cuenta.nombre} está inactiva"
                )
        
        # 3. Validar balance contable (débitos = créditos)
        total_debitos = sum(
            detalle.monto for detalle in asiento_data.detalles 
            if detalle.tipo_movimiento == TipoMovimiento.DEBITO
        )
        total_creditos = sum(
            detalle.monto for detalle in asiento_data.detalles 
            if detalle.tipo_movimiento == TipoMovimiento.CREDITO
        )
        
        if abs(total_debitos - total_creditos) > Decimal('0.01'):  # Tolerancia de 1 centavo
            raise DesequilibrioContableError(
                f"El asiento no está balanceado. Débitos: {total_debitos}, Créditos: {total_creditos}"
            )
        
        # 4. Crear el asiento contable
        try:
            return await self.asiento_repository.create(asiento_data)
        except Exception as e:
            raise AsientoContableError(f"Error al crear el asiento contable: {str(e)}")


class GetAsientoContableUseCase:
    """Caso de uso para obtener un asiento contable por ID."""
    
    def __init__(self, asiento_repository: IAsientoContableRepository):
        self.asiento_repository = asiento_repository
    
    async def execute(self, asiento_id: UUID) -> AsientoContable:
        """
        Obtener un asiento contable por su ID.
        
        Args:
            asiento_id: UUID del asiento
            
        Returns:
            AsientoContable: El asiento encontrado
            
        Raises:
            AsientoContableNotFoundError: Si el asiento no existe
        """
        asiento = await self.asiento_repository.get_by_id(asiento_id)
        if not asiento:
            raise AsientoContableNotFoundError(
                f"Asiento contable con ID {asiento_id} no encontrado"
            )
        return asiento


class GetAsientoContableByComprobanteUseCase:
    """Caso de uso para obtener un asiento contable por comprobante."""
    
    def __init__(self, asiento_repository: IAsientoContableRepository):
        self.asiento_repository = asiento_repository
    
    async def execute(self, comprobante: str) -> AsientoContable:
        """
        Obtener un asiento contable por su número de comprobante.
        
        Args:
            comprobante: Número de comprobante
            
        Returns:
            AsientoContable: El asiento encontrado
            
        Raises:
            AsientoContableNotFoundError: Si el asiento no existe
        """
        asiento = await self.asiento_repository.get_by_comprobante(comprobante)
        if not asiento:
            raise AsientoContableNotFoundError(
                f"Asiento contable con comprobante {comprobante} no encontrado"
            )
        return asiento


class ListAsientosContablesUseCase:
    """Caso de uso para listar asientos contables con filtros y paginación."""
    
    def __init__(self, asiento_repository: IAsientoContableRepository):
        self.asiento_repository = asiento_repository
    
    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        comprobante: Optional[str] = None
    ) -> dict:
        """
        Listar asientos contables con filtros y paginación.
        
        Args:
            page: Número de página (empezando en 1)
            limit: Número de elementos por página
            fecha_desde: Fecha desde para filtrar
            fecha_hasta: Fecha hasta para filtrar
            comprobante: Filtrar por comprobante
            
        Returns:
            dict: Diccionario con asientos, total y metadatos de paginación
        """
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if limit < 1:
            limit = 50
        if limit > 500:  # Límite máximo
            limit = 500
        
        skip = (page - 1) * limit
        
        # Obtener asientos y total
        asientos = await self.asiento_repository.get_all(
            skip=skip,
            limit=limit,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            comprobante=comprobante
        )
        
        total = await self.asiento_repository.count_total(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            comprobante=comprobante
        )
        
        # Calcular metadatos de paginación
        has_next = (skip + limit) < total
        has_prev = page > 1
        
        return {
            "asientos": asientos,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }


class DeleteAsientoContableUseCase:
    """Caso de uso para eliminar un asiento contable."""
    
    def __init__(self, asiento_repository: IAsientoContableRepository):
        self.asiento_repository = asiento_repository
    
    async def execute(self, asiento_id: UUID) -> bool:
        """
        Eliminar un asiento contable.
        
        Args:
            asiento_id: UUID del asiento a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            AsientoContableNotFoundError: Si el asiento no existe
        """
        success = await self.asiento_repository.delete(asiento_id)
        if not success:
            raise AsientoContableNotFoundError(
                f"Asiento contable con ID {asiento_id} no encontrado"
            )
        return True


class ValidateAsientoContableBalanceUseCase:
    """Caso de uso para validar el balance de un asiento contable."""
    
    def execute(self, detalles: List[DetalleAsientoCreate]) -> dict:
        """
        Validar que un conjunto de detalles está balanceado.
        
        Args:
            detalles: Lista de detalles del asiento
            
        Returns:
            dict: Resultado de la validación con totales
        """
        total_debitos = sum(
            detalle.monto for detalle in detalles 
            if detalle.tipo_movimiento == TipoMovimiento.DEBITO
        )
        total_creditos = sum(
            detalle.monto for detalle in detalles 
            if detalle.tipo_movimiento == TipoMovimiento.CREDITO
        )
        
        diferencia = abs(total_debitos - total_creditos)
        esta_balanceado = diferencia <= Decimal('0.01')  # Tolerancia de 1 centavo
        
        return {
            "esta_balanceado": esta_balanceado,
            "total_debitos": total_debitos,
            "total_creditos": total_creditos,
            "diferencia": diferencia,
            "cantidad_detalles": len(detalles)
        }