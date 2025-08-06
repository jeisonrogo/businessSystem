"""
Interfaz para el repositorio de asientos contables.
Define el contrato para las operaciones de persistencia de asientos contables.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.models.contabilidad import (
    AsientoContable,
    AsientoContableCreate
)


class IAsientoContableRepository(ABC):
    """
    Interfaz para el repositorio de asientos contables.
    Define las operaciones de persistencia para asientos contables manuales.
    """
    
    @abstractmethod
    async def create(self, asiento_data: AsientoContableCreate) -> AsientoContable:
        """
        Crear un nuevo asiento contable.
        
        Args:
            asiento_data: Datos del asiento contable a crear
            
        Returns:
            AsientoContable: El asiento contable creado
            
        Raises:
            ValueError: Si hay errores de validación o duplicados
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, asiento_id: UUID) -> Optional[AsientoContable]:
        """
        Obtener un asiento contable por su ID.
        
        Args:
            asiento_id: UUID del asiento contable
            
        Returns:
            Optional[AsientoContable]: El asiento si existe, None si no existe
        """
        pass
    
    @abstractmethod
    async def get_by_comprobante(self, comprobante: str) -> Optional[AsientoContable]:
        """
        Obtener un asiento contable por su número de comprobante.
        
        Args:
            comprobante: Número de comprobante único
            
        Returns:
            Optional[AsientoContable]: El asiento si existe, None si no existe
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        comprobante: Optional[str] = None
    ) -> List[AsientoContable]:
        """
        Obtener asientos contables con filtros opcionales.
        
        Args:
            skip: Número de elementos a saltar (paginación)
            limit: Número máximo de elementos a retornar
            fecha_desde: Fecha desde para filtrar
            fecha_hasta: Fecha hasta para filtrar
            comprobante: Filtro por número de comprobante (búsqueda parcial)
            
        Returns:
            List[AsientoContable]: Lista de asientos contables
        """
        pass
    
    @abstractmethod
    async def count_total(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        comprobante: Optional[str] = None
    ) -> int:
        """
        Contar el total de asientos contables con filtros opcionales.
        
        Args:
            fecha_desde: Fecha desde para filtrar
            fecha_hasta: Fecha hasta para filtrar
            comprobante: Filtro por número de comprobante (búsqueda parcial)
            
        Returns:
            int: Número total de asientos que cumplen los filtros
        """
        pass
    
    @abstractmethod
    async def delete(self, asiento_id: UUID) -> bool:
        """
        Eliminar un asiento contable.
        
        Args:
            asiento_id: UUID del asiento a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False si no existía
            
        Note:
            Elimina tanto el asiento como todos sus detalles asociados
        """
        pass
    
    @abstractmethod
    async def get_asientos_por_cuenta(
        self,
        cuenta_id: UUID,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[AsientoContable]:
        """
        Obtener asientos contables que afectan a una cuenta específica.
        
        Args:
            cuenta_id: UUID de la cuenta contable
            fecha_desde: Fecha desde para filtrar
            fecha_hasta: Fecha hasta para filtrar
            
        Returns:
            List[AsientoContable]: Lista de asientos que afectan la cuenta
        """
        pass
    
    @abstractmethod
    async def get_balance_cuenta(
        self,
        cuenta_id: UUID,
        fecha_hasta: Optional[date] = None
    ) -> dict:
        """
        Calcular el balance de una cuenta hasta una fecha específica.
        
        Args:
            cuenta_id: UUID de la cuenta contable
            fecha_hasta: Fecha hasta la cual calcular el balance
            
        Returns:
            dict: Diccionario con:
                - total_debitos: Total de débitos
                - total_creditos: Total de créditos
                - saldo: Saldo final
                - cantidad_movimientos: Número de movimientos
        """
        pass
    
    @abstractmethod
    async def get_libro_diario(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> List[AsientoContable]:
        """
        Obtener el libro diario para un rango de fechas.
        
        Args:
            fecha_desde: Fecha de inicio
            fecha_hasta: Fecha de fin
            
        Returns:
            List[AsientoContable]: Lista de asientos ordenados por fecha
        """
        pass