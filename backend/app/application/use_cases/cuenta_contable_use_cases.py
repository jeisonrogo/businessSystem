"""
Casos de uso para la gestión de cuentas contables.
Implementa la lógica de negocio para el plan de cuentas de la empresa.
"""

from typing import List, Optional
from uuid import UUID

from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.domain.models.contabilidad import (
    CuentaContable,
    CuentaContableCreate,
    CuentaContableUpdate,
    CuentaContableResponse,
    TipoCuenta
)


# ==================== EXCEPCIONES ====================

class CuentaContableError(Exception):
    """Excepción base para errores de cuentas contables."""
    pass


class CuentaContableNotFoundError(CuentaContableError):
    """Error cuando una cuenta contable no es encontrada."""
    pass


class DuplicateCodigoError(CuentaContableError):
    """Error cuando se intenta crear una cuenta con código duplicado."""
    pass


class InvalidHierarchyError(CuentaContableError):
    """Error en la jerarquía de cuentas."""
    pass


# ==================== CASOS DE USO ====================

class CreateCuentaContableUseCase:
    """Caso de uso para crear una nueva cuenta contable."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, cuenta_data: CuentaContableCreate) -> CuentaContable:
        """
        Crear una nueva cuenta contable.
        
        Args:
            cuenta_data: Datos de la cuenta a crear
            
        Returns:
            CuentaContable: La cuenta creada
            
        Raises:
            DuplicateCodigoError: Si el código ya existe
            InvalidHierarchyError: Si la cuenta padre no existe
        """
        try:
            return await self.cuenta_repository.create(cuenta_data)
        except ValueError as e:
            if "código" in str(e) and "existe" in str(e):
                raise DuplicateCodigoError(str(e))
            elif "padre" in str(e):
                raise InvalidHierarchyError(str(e))
            else:
                raise CuentaContableError(str(e))


class GetCuentaContableUseCase:
    """Caso de uso para obtener una cuenta contable por ID."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, cuenta_id: UUID) -> CuentaContable:
        """
        Obtener una cuenta contable por su ID.
        
        Args:
            cuenta_id: UUID de la cuenta
            
        Returns:
            CuentaContable: La cuenta encontrada
            
        Raises:
            CuentaContableNotFoundError: Si la cuenta no existe
        """
        cuenta = await self.cuenta_repository.get_by_id(cuenta_id)
        if not cuenta:
            raise CuentaContableNotFoundError(f"Cuenta contable con ID {cuenta_id} no encontrada")
        return cuenta


class GetCuentaContableByCodigoUseCase:
    """Caso de uso para obtener una cuenta contable por código."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, codigo: str) -> CuentaContable:
        """
        Obtener una cuenta contable por su código.
        
        Args:
            codigo: Código de la cuenta
            
        Returns:
            CuentaContable: La cuenta encontrada
            
        Raises:
            CuentaContableNotFoundError: Si la cuenta no existe
        """
        cuenta = await self.cuenta_repository.get_by_codigo(codigo)
        if not cuenta:
            raise CuentaContableNotFoundError(f"Cuenta contable con código {codigo} no encontrada")
        return cuenta


class ListCuentasContablesUseCase:
    """Caso de uso para listar cuentas contables con filtros y paginación."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        tipo_cuenta: Optional[TipoCuenta] = None,
        only_active: bool = True,
        only_main_accounts: bool = False
    ) -> dict:
        """
        Listar cuentas contables con filtros y paginación.
        
        Args:
            page: Número de página (empezando en 1)
            limit: Número de elementos por página
            tipo_cuenta: Filtrar por tipo de cuenta específico
            only_active: Solo cuentas activas
            only_main_accounts: Solo cuentas principales
            
        Returns:
            dict: Diccionario con cuentas, total y metadatos de paginación
        """
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if limit < 1:
            limit = 50
        if limit > 500:  # Límite máximo para evitar sobrecarga
            limit = 500
        
        skip = (page - 1) * limit
        
        # Obtener cuentas y total
        cuentas = await self.cuenta_repository.get_all(
            skip=skip,
            limit=limit,
            tipo_cuenta=tipo_cuenta,
            only_active=only_active,
            only_main_accounts=only_main_accounts
        )
        
        total = await self.cuenta_repository.count_total(
            tipo_cuenta=tipo_cuenta,
            only_active=only_active
        )
        
        # Calcular metadatos de paginación
        has_next = (skip + limit) < total
        has_prev = page > 1
        
        return {
            "cuentas": cuentas,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }


class UpdateCuentaContableUseCase:
    """Caso de uso para actualizar una cuenta contable."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(
        self, 
        cuenta_id: UUID, 
        cuenta_data: CuentaContableUpdate
    ) -> CuentaContable:
        """
        Actualizar una cuenta contable existente.
        
        Args:
            cuenta_id: UUID de la cuenta a actualizar
            cuenta_data: Datos de actualización
            
        Returns:
            CuentaContable: La cuenta actualizada
            
        Raises:
            CuentaContableNotFoundError: Si la cuenta no existe
            InvalidHierarchyError: Si se crea una referencia circular
        """
        try:
            cuenta = await self.cuenta_repository.update(cuenta_id, cuenta_data)
            if not cuenta:
                raise CuentaContableNotFoundError(f"Cuenta contable con ID {cuenta_id} no encontrada")
            return cuenta
        except ValueError as e:
            if "circular" in str(e):
                raise InvalidHierarchyError(str(e))
            else:
                raise CuentaContableError(str(e))


class DeleteCuentaContableUseCase:
    """Caso de uso para eliminar una cuenta contable."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, cuenta_id: UUID) -> bool:
        """
        Eliminar una cuenta contable (soft delete).
        
        Args:
            cuenta_id: UUID de la cuenta a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            CuentaContableNotFoundError: Si la cuenta no existe
            InvalidHierarchyError: Si tiene subcuentas o movimientos
        """
        try:
            success = await self.cuenta_repository.delete(cuenta_id)
            if not success:
                raise CuentaContableNotFoundError(f"Cuenta contable con ID {cuenta_id} no encontrada")
            return True
        except ValueError as e:
            if "subcuentas" in str(e) or "movimientos" in str(e):
                raise InvalidHierarchyError(str(e))
            else:
                raise CuentaContableError(str(e))


class GetPlanCuentasJerarquicoUseCase:
    """Caso de uso para obtener el plan de cuentas en formato jerárquico."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self) -> List[dict]:
        """
        Obtener el plan de cuentas completo en formato jerárquico.
        
        Returns:
            List[dict]: Plan de cuentas con estructura jerárquica
        """
        return await self.cuenta_repository.get_plan_cuentas_jerarquico()


class GetSubcuentasUseCase:
    """Caso de uso para obtener subcuentas de una cuenta padre."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, cuenta_padre_id: UUID) -> List[CuentaContable]:
        """
        Obtener todas las subcuentas de una cuenta padre.
        
        Args:
            cuenta_padre_id: UUID de la cuenta padre
            
        Returns:
            List[CuentaContable]: Lista de subcuentas
            
        Raises:
            CuentaContableNotFoundError: Si la cuenta padre no existe
        """
        # Verificar que la cuenta padre existe
        cuenta_padre = await self.cuenta_repository.get_by_id(cuenta_padre_id)
        if not cuenta_padre:
            raise CuentaContableNotFoundError(f"Cuenta padre con ID {cuenta_padre_id} no encontrada")
        
        return await self.cuenta_repository.get_subcuentas(cuenta_padre_id)


class SeedPlanCuentasColombia:
    """Caso de uso para poblar el plan de cuentas estándar de Colombia."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self) -> dict:
        """
        Poblar la base de datos con el plan de cuentas estándar de Colombia.
        
        Returns:
            dict: Resultado con número de cuentas creadas
        """
        try:
            cuentas_creadas = await self.cuenta_repository.seed_plan_cuentas_colombia()
            
            return {
                "mensaje": "Plan de cuentas de Colombia cargado exitosamente",
                "cuentas_creadas": cuentas_creadas,
                "total_procesadas": cuentas_creadas
            }
        except Exception as e:
            raise CuentaContableError(f"Error al cargar el plan de cuentas: {str(e)}")


class GetCuentasPrincipalesUseCase:
    """Caso de uso para obtener cuentas principales (sin cuenta padre)."""
    
    def __init__(self, cuenta_repository: ICuentaContableRepository):
        self.cuenta_repository = cuenta_repository
    
    async def execute(self, tipo_cuenta: Optional[TipoCuenta] = None) -> List[CuentaContable]:
        """
        Obtener cuentas principales organizadas por tipo.
        
        Args:
            tipo_cuenta: Filtrar por tipo de cuenta específico
            
        Returns:
            List[CuentaContable]: Lista de cuentas principales
        """
        return await self.cuenta_repository.get_cuentas_principales(tipo_cuenta)