"""
Interfaz abstracta para el repositorio de cuentas contables.
Define el contrato para operaciones CRUD y consultas especializadas del plan de cuentas.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.contabilidad import (
    CuentaContable,
    CuentaContableCreate,
    CuentaContableUpdate,
    TipoCuenta
)


class ICuentaContableRepository(ABC):
    """
    Interfaz del repositorio para cuentas contables.
    
    Define operaciones para el manejo del plan de cuentas de la empresa,
    incluyendo operaciones CRUD y consultas especializadas para reportes contables.
    """
    
    @abstractmethod
    async def create(self, cuenta_data: CuentaContableCreate) -> CuentaContable:
        """
        Crear una nueva cuenta contable.
        
        Args:
            cuenta_data: Datos para crear la cuenta
            
        Returns:
            CuentaContable: La cuenta creada
            
        Raises:
            ValueError: Si el código de cuenta ya existe
            ValueError: Si la cuenta padre no existe (cuando se especifica)
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, cuenta_id: UUID) -> Optional[CuentaContable]:
        """
        Obtener una cuenta contable por su ID.
        
        Args:
            cuenta_id: UUID de la cuenta
            
        Returns:
            Optional[CuentaContable]: La cuenta si existe, None si no existe
        """
        pass
    
    @abstractmethod
    async def get_by_codigo(self, codigo: str) -> Optional[CuentaContable]:
        """
        Obtener una cuenta contable por su código único.
        
        Args:
            codigo: Código único de la cuenta
            
        Returns:
            Optional[CuentaContable]: La cuenta si existe, None si no existe
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo_cuenta: Optional[TipoCuenta] = None,
        only_active: bool = True,
        only_main_accounts: bool = False
    ) -> List[CuentaContable]:
        """
        Obtener lista de cuentas contables con filtros y paginación.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            tipo_cuenta: Filtrar por tipo de cuenta específico
            only_active: Solo cuentas activas
            only_main_accounts: Solo cuentas principales (sin cuenta padre)
            
        Returns:
            List[CuentaContable]: Lista de cuentas
        """
        pass
    
    @abstractmethod
    async def update(self, cuenta_id: UUID, cuenta_data: CuentaContableUpdate) -> Optional[CuentaContable]:
        """
        Actualizar una cuenta contable existente.
        
        Args:
            cuenta_id: UUID de la cuenta a actualizar
            cuenta_data: Datos para actualizar
            
        Returns:
            Optional[CuentaContable]: La cuenta actualizada si existe, None si no existe
            
        Raises:
            ValueError: Si se intenta crear una referencia circular en la jerarquía
        """
        pass
    
    @abstractmethod
    async def delete(self, cuenta_id: UUID) -> bool:
        """
        Eliminar una cuenta contable (soft delete).
        
        Args:
            cuenta_id: UUID de la cuenta a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente, False si no existía
            
        Raises:
            ValueError: Si la cuenta tiene subcuentas activas
            ValueError: Si la cuenta tiene movimientos contables asociados
        """
        pass
    
    @abstractmethod
    async def get_subcuentas(self, cuenta_padre_id: UUID) -> List[CuentaContable]:
        """
        Obtener todas las subcuentas de una cuenta padre.
        
        Args:
            cuenta_padre_id: UUID de la cuenta padre
            
        Returns:
            List[CuentaContable]: Lista de subcuentas
        """
        pass
    
    @abstractmethod
    async def get_cuentas_principales(self, tipo_cuenta: Optional[TipoCuenta] = None) -> List[CuentaContable]:
        """
        Obtener cuentas principales (sin cuenta padre) organizadas jerárquicamente.
        
        Args:
            tipo_cuenta: Filtrar por tipo de cuenta específico
            
        Returns:
            List[CuentaContable]: Lista de cuentas principales
        """
        pass
    
    @abstractmethod
    async def exists_by_codigo(self, codigo: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Verificar si existe una cuenta con el código dado.
        
        Args:
            codigo: Código de cuenta a verificar
            exclude_id: ID de cuenta a excluir de la verificación (útil para updates)
            
        Returns:
            bool: True si existe, False si no existe
        """
        pass
    
    @abstractmethod
    async def count_total(
        self,
        tipo_cuenta: Optional[TipoCuenta] = None,
        only_active: bool = True
    ) -> int:
        """
        Contar el total de cuentas contables con filtros.
        
        Args:
            tipo_cuenta: Filtrar por tipo de cuenta específico
            only_active: Solo contar cuentas activas
            
        Returns:
            int: Número total de cuentas
        """
        pass
    
    @abstractmethod
    async def get_plan_cuentas_jerarquico(self) -> List[dict]:
        """
        Obtener el plan de cuentas en formato jerárquico para visualización.
        
        Returns:
            List[dict]: Plan de cuentas con estructura jerárquica
                Cada dict contiene: cuenta, nivel, tiene_hijos, subcuentas[]
        """
        pass
    
    @abstractmethod
    async def seed_plan_cuentas_colombia(self) -> int:
        """
        Poblar la base de datos con el plan de cuentas estándar de Colombia.
        Solo crea cuentas si no existen (no duplica).
        
        Returns:
            int: Número de cuentas creadas
            
        Note:
            Este método debe ser idempotente - se puede ejecutar múltiples veces
            sin crear duplicados.
        """
        pass