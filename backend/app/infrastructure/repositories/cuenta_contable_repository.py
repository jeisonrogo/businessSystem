"""
Implementación concreta del repositorio de cuentas contables usando SQLModel y PostgreSQL.
Maneja todas las operaciones CRUD y consultas especializadas para el plan de cuentas.
"""

from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select, and_, func

from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.domain.models.contabilidad import (
    CuentaContable,
    CuentaContableCreate,
    CuentaContableUpdate,
    TipoCuenta,
    CodigosCuentasEstandar
)


class SQLCuentaContableRepository(ICuentaContableRepository):
    """
    Implementación del repositorio de cuentas contables usando SQLModel.
    """
    
    def __init__(self, session: Session):
        """
        Inicializar el repositorio con una sesión de base de datos.
        
        Args:
            session: Sesión de SQLModel para operaciones de base de datos
        """
        self.session = session
    
    async def create(self, cuenta_data: CuentaContableCreate) -> CuentaContable:
        """Crear una nueva cuenta contable."""
        # Verificar que el código no exista
        if await self.exists_by_codigo(cuenta_data.codigo):
            raise ValueError(f"Ya existe una cuenta con el código {cuenta_data.codigo}")
        
        # Verificar que la cuenta padre exista (si se especifica)
        if cuenta_data.cuenta_padre_id:
            cuenta_padre = await self.get_by_id(cuenta_data.cuenta_padre_id)
            if not cuenta_padre:
                raise ValueError(f"La cuenta padre con ID {cuenta_data.cuenta_padre_id} no existe")
            if not cuenta_padre.is_active:
                raise ValueError("La cuenta padre debe estar activa")
        
        # Crear la cuenta
        cuenta = CuentaContable(**cuenta_data.model_dump())
        
        try:
            self.session.add(cuenta)
            self.session.commit()
            self.session.refresh(cuenta)
            return cuenta
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al crear la cuenta contable: {str(e)}")
    
    async def get_by_id(self, cuenta_id: UUID) -> Optional[CuentaContable]:
        """Obtener una cuenta contable por su ID."""
        statement = select(CuentaContable).where(CuentaContable.id == cuenta_id)
        result = self.session.exec(statement)
        return result.first()
    
    async def get_by_codigo(self, codigo: str) -> Optional[CuentaContable]:
        """Obtener una cuenta contable por su código único."""
        statement = select(CuentaContable).where(CuentaContable.codigo == codigo)
        result = self.session.exec(statement)
        return result.first()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo_cuenta: Optional[TipoCuenta] = None,
        only_active: bool = True,
        only_main_accounts: bool = False
    ) -> List[CuentaContable]:
        """Obtener lista de cuentas contables con filtros y paginación."""
        statement = select(CuentaContable)
        
        # Aplicar filtros
        conditions = []
        
        if only_active:
            conditions.append(CuentaContable.is_active == True)
        
        if tipo_cuenta:
            conditions.append(CuentaContable.tipo_cuenta == tipo_cuenta)
        
        if only_main_accounts:
            conditions.append(CuentaContable.cuenta_padre_id == None)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        # Aplicar ordenamiento por código
        statement = statement.order_by(CuentaContable.codigo)
        
        # Aplicar paginación
        statement = statement.offset(skip).limit(limit)
        
        result = self.session.exec(statement)
        return result.all()
    
    async def update(self, cuenta_id: UUID, cuenta_data: CuentaContableUpdate) -> Optional[CuentaContable]:
        """Actualizar una cuenta contable existente."""
        cuenta = await self.get_by_id(cuenta_id)
        if not cuenta:
            return None
        
        # Verificar cuenta padre si se está actualizando
        if cuenta_data.cuenta_padre_id is not None:
            if cuenta_data.cuenta_padre_id != cuenta.cuenta_padre_id:
                # Verificar que la nueva cuenta padre exista
                cuenta_padre = await self.get_by_id(cuenta_data.cuenta_padre_id)
                if not cuenta_padre:
                    raise ValueError(f"La cuenta padre con ID {cuenta_data.cuenta_padre_id} no existe")
                
                # Evitar referencias circulares
                if await self._would_create_circular_reference(cuenta_id, cuenta_data.cuenta_padre_id):
                    raise ValueError("La actualización crearía una referencia circular")
        
        # Aplicar actualización
        update_data = cuenta_data.model_dump(exclude_unset=True)
        
        try:
            for field, value in update_data.items():
                setattr(cuenta, field, value)
            
            self.session.commit()
            self.session.refresh(cuenta)
            return cuenta
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al actualizar la cuenta contable: {str(e)}")
    
    async def delete(self, cuenta_id: UUID) -> bool:
        """Eliminar una cuenta contable (soft delete)."""
        cuenta = await self.get_by_id(cuenta_id)
        if not cuenta:
            return False
        
        # Verificar que no tenga subcuentas activas
        subcuentas = await self.get_subcuentas(cuenta_id)
        if subcuentas:
            active_subcuentas = [sc for sc in subcuentas if sc.is_active]
            if active_subcuentas:
                raise ValueError("No se puede eliminar una cuenta que tiene subcuentas activas")
        
        # TODO: Verificar que no tenga movimientos contables asociados
        # Esta verificación se implementará cuando tengamos el módulo de asientos
        
        try:
            cuenta.is_active = False
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al eliminar la cuenta contable: {str(e)}")
    
    async def get_subcuentas(self, cuenta_padre_id: UUID) -> List[CuentaContable]:
        """Obtener todas las subcuentas de una cuenta padre."""
        statement = select(CuentaContable).where(
            CuentaContable.cuenta_padre_id == cuenta_padre_id
        ).order_by(CuentaContable.codigo)
        
        result = self.session.exec(statement)
        return result.all()
    
    async def get_cuentas_principales(self, tipo_cuenta: Optional[TipoCuenta] = None) -> List[CuentaContable]:
        """Obtener cuentas principales (sin cuenta padre)."""
        statement = select(CuentaContable).where(CuentaContable.cuenta_padre_id == None)
        
        if tipo_cuenta:
            statement = statement.where(CuentaContable.tipo_cuenta == tipo_cuenta)
        
        statement = statement.where(CuentaContable.is_active == True).order_by(CuentaContable.codigo)
        
        result = self.session.exec(statement)
        return result.all()
    
    async def exists_by_codigo(self, codigo: str, exclude_id: Optional[UUID] = None) -> bool:
        """Verificar si existe una cuenta con el código dado."""
        statement = select(CuentaContable).where(CuentaContable.codigo == codigo)
        
        if exclude_id:
            statement = statement.where(CuentaContable.id != exclude_id)
        
        result = self.session.exec(statement)
        return result.first() is not None
    
    async def count_total(
        self,
        tipo_cuenta: Optional[TipoCuenta] = None,
        only_active: bool = True
    ) -> int:
        """Contar el total de cuentas contables con filtros."""
        statement = select(func.count(CuentaContable.id))
        
        conditions = []
        
        if only_active:
            conditions.append(CuentaContable.is_active == True)
        
        if tipo_cuenta:
            conditions.append(CuentaContable.tipo_cuenta == tipo_cuenta)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return result.one()
    
    async def get_plan_cuentas_jerarquico(self) -> List[dict]:
        """Obtener el plan de cuentas en formato jerárquico."""
        # Obtener todas las cuentas activas ordenadas por código
        statement = select(CuentaContable).where(
            CuentaContable.is_active == True
        ).order_by(CuentaContable.codigo)
        
        result = self.session.exec(statement)
        todas_las_cuentas = result.all()
        
        # Crear un diccionario para acceso rápido por ID
        cuentas_dict = {cuenta.id: cuenta for cuenta in todas_las_cuentas}
        
        # Construir la estructura jerárquica
        plan_jerarquico = []
        cuentas_procesadas = set()
        
        # Primero, procesar las cuentas principales (sin padre)
        cuentas_principales = [c for c in todas_las_cuentas if c.cuenta_padre_id is None]
        
        for cuenta in cuentas_principales:
            cuenta_info = self._build_cuenta_hierarchy(cuenta, cuentas_dict, cuentas_procesadas, nivel=0)
            plan_jerarquico.append(cuenta_info)
        
        return plan_jerarquico
    
    async def seed_plan_cuentas_colombia(self) -> int:
        """Poblar la base de datos con el plan de cuentas estándar de Colombia."""
        
        # Plan de cuentas básico estándar colombiano
        cuentas_plan = [
            # ACTIVOS (1)
            {"codigo": "1", "nombre": "ACTIVO", "tipo": TipoCuenta.ACTIVO, "padre": None},
            {"codigo": "11", "nombre": "ACTIVO CORRIENTE", "tipo": TipoCuenta.ACTIVO, "padre": "1"},
            {"codigo": "1105", "nombre": "EFECTIVO Y EQUIVALENTES AL EFECTIVO", "tipo": TipoCuenta.ACTIVO, "padre": "11"},
            {"codigo": "110505", "nombre": "CAJA", "tipo": TipoCuenta.ACTIVO, "padre": "1105"},
            {"codigo": "110510", "nombre": "BANCOS", "tipo": TipoCuenta.ACTIVO, "padre": "1105"},
            {"codigo": "1205", "nombre": "CUENTAS POR COBRAR", "tipo": TipoCuenta.ACTIVO, "padre": "11"},
            {"codigo": "120505", "nombre": "CLIENTES NACIONALES", "tipo": TipoCuenta.ACTIVO, "padre": "1205"},
            {"codigo": "1435", "nombre": "INVENTARIOS", "tipo": TipoCuenta.ACTIVO, "padre": "11"},
            {"codigo": "143505", "nombre": "MERCANCÍAS NO FABRICADAS POR LA EMPRESA", "tipo": TipoCuenta.ACTIVO, "padre": "1435"},
            
            # PASIVOS (2)
            {"codigo": "2", "nombre": "PASIVO", "tipo": TipoCuenta.PASIVO, "padre": None},
            {"codigo": "21", "nombre": "PASIVO CORRIENTE", "tipo": TipoCuenta.PASIVO, "padre": "2"},
            {"codigo": "2205", "nombre": "CUENTAS POR PAGAR", "tipo": TipoCuenta.PASIVO, "padre": "21"},
            {"codigo": "220505", "nombre": "PROVEEDORES NACIONALES", "tipo": TipoCuenta.PASIVO, "padre": "2205"},
            {"codigo": "2440", "nombre": "IMPUESTOS GRAVÁMENES Y TASAS", "tipo": TipoCuenta.PASIVO, "padre": "21"},
            {"codigo": "244095", "nombre": "IVA POR PAGAR", "tipo": TipoCuenta.PASIVO, "padre": "2440"},
            
            # PATRIMONIO (3)
            {"codigo": "3", "nombre": "PATRIMONIO", "tipo": TipoCuenta.PATRIMONIO, "padre": None},
            {"codigo": "31", "nombre": "CAPITAL SOCIAL", "tipo": TipoCuenta.PATRIMONIO, "padre": "3"},
            {"codigo": "3115", "nombre": "APORTES SOCIALES", "tipo": TipoCuenta.PATRIMONIO, "padre": "31"},
            {"codigo": "36", "nombre": "RESULTADOS DEL EJERCICIO", "tipo": TipoCuenta.PATRIMONIO, "padre": "3"},
            {"codigo": "3605", "nombre": "UTILIDADES RETENIDAS", "tipo": TipoCuenta.PATRIMONIO, "padre": "36"},
            
            # INGRESOS (4)
            {"codigo": "4", "nombre": "INGRESOS", "tipo": TipoCuenta.INGRESO, "padre": None},
            {"codigo": "41", "nombre": "INGRESOS OPERACIONALES", "tipo": TipoCuenta.INGRESO, "padre": "4"},
            {"codigo": "4135", "nombre": "VENTAS DE MERCANCÍAS", "tipo": TipoCuenta.INGRESO, "padre": "41"},
            {"codigo": "413505", "nombre": "VENTAS DE PRODUCTOS", "tipo": TipoCuenta.INGRESO, "padre": "4135"},
            
            # EGRESOS/COSTOS (6)
            {"codigo": "6", "nombre": "COSTOS DE VENTAS", "tipo": TipoCuenta.EGRESO, "padre": None},
            {"codigo": "61", "nombre": "COSTO DE VENTAS", "tipo": TipoCuenta.EGRESO, "padre": "6"},
            {"codigo": "6135", "nombre": "COSTO DE VENTAS DE MERCANCÍAS", "tipo": TipoCuenta.EGRESO, "padre": "61"},
            {"codigo": "613505", "nombre": "COSTO DE PRODUCTOS VENDIDOS", "tipo": TipoCuenta.EGRESO, "padre": "6135"},
        ]
        
        cuentas_creadas = 0
        cuentas_por_codigo = {}  # Para resolver referencias padre
        
        try:
            # Crear cuentas en orden jerárquico
            for cuenta_info in cuentas_plan:
                # Verificar si ya existe
                if await self.exists_by_codigo(cuenta_info["codigo"]):
                    continue
                
                # Resolver cuenta padre
                cuenta_padre_id = None
                if cuenta_info["padre"]:
                    cuenta_padre = cuentas_por_codigo.get(cuenta_info["padre"])
                    if cuenta_padre:
                        cuenta_padre_id = cuenta_padre.id
                
                # Crear la cuenta
                cuenta_data = CuentaContableCreate(
                    codigo=cuenta_info["codigo"],
                    nombre=cuenta_info["nombre"],
                    tipo_cuenta=cuenta_info["tipo"],
                    cuenta_padre_id=cuenta_padre_id
                )
                
                cuenta = CuentaContable(**cuenta_data.model_dump())
                self.session.add(cuenta)
                self.session.flush()  # Para obtener el ID
                
                # Guardar referencia para futuras cuentas hija
                cuentas_por_codigo[cuenta.codigo] = cuenta
                cuentas_creadas += 1
            
            self.session.commit()
            return cuentas_creadas
            
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al crear el plan de cuentas: {str(e)}")
    
    async def _would_create_circular_reference(self, cuenta_id: UUID, nueva_cuenta_padre_id: UUID) -> bool:
        """Verificar si asignar una nueva cuenta padre crearía una referencia circular."""
        # Recorrer hacia arriba desde la nueva cuenta padre para ver si llegamos a cuenta_id
        current_id = nueva_cuenta_padre_id
        
        while current_id:
            if current_id == cuenta_id:
                return True
            
            cuenta = await self.get_by_id(current_id)
            if not cuenta or not cuenta.cuenta_padre_id:
                break
            
            current_id = cuenta.cuenta_padre_id
        
        return False
    
    def _build_cuenta_hierarchy(
        self, 
        cuenta: CuentaContable, 
        cuentas_dict: dict, 
        cuentas_procesadas: set,
        nivel: int = 0
    ) -> dict:
        """Construir la información jerárquica de una cuenta con sus subcuentas."""
        if cuenta.id in cuentas_procesadas:
            return None
        
        cuentas_procesadas.add(cuenta.id)
        
        # Encontrar subcuentas
        subcuentas = []
        for cuenta_id, cuenta_candidate in cuentas_dict.items():
            if (cuenta_candidate.cuenta_padre_id == cuenta.id and 
                cuenta_candidate.id not in cuentas_procesadas):
                subcuenta_info = self._build_cuenta_hierarchy(
                    cuenta_candidate, cuentas_dict, cuentas_procesadas, nivel + 1
                )
                if subcuenta_info:
                    subcuentas.append(subcuenta_info)
        
        return {
            "cuenta": {
                "id": str(cuenta.id),
                "codigo": cuenta.codigo,
                "nombre": cuenta.nombre,
                "tipo_cuenta": cuenta.tipo_cuenta.value,
                "is_active": cuenta.is_active,
                "created_at": cuenta.created_at.isoformat()
            },
            "nivel": nivel,
            "tiene_hijos": len(subcuentas) > 0,
            "subcuentas": sorted(subcuentas, key=lambda x: x["cuenta"]["codigo"])
        }