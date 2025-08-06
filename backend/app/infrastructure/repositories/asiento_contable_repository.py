"""
Implementación del repositorio de asientos contables usando SQLModel/PostgreSQL.
Maneja la persistencia y consulta de asientos contables con sus detalles.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlmodel import Session, select, and_, func
from sqlalchemy.orm import selectinload

from app.application.services.i_asiento_contable_repository import IAsientoContableRepository
from app.domain.models.contabilidad import (
    AsientoContable,
    AsientoContableCreate,
    DetalleAsiento,
    DetalleAsientoCreate,
    TipoMovimiento
)


class SQLAsientoContableRepository(IAsientoContableRepository):
    """
    Implementación del repositorio de asientos contables usando SQLModel/PostgreSQL.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, asiento_data: AsientoContableCreate) -> AsientoContable:
        """Crear un nuevo asiento contable con sus detalles."""
        try:
            # Verificar que no existe asiento con el mismo comprobante
            if asiento_data.comprobante:
                existing = await self.get_by_comprobante(asiento_data.comprobante)
                if existing:
                    raise ValueError(f"Ya existe un asiento con el comprobante {asiento_data.comprobante}")
            
            # Crear el asiento contable
            asiento_dict = asiento_data.model_dump(exclude={'detalles'})
            asiento = AsientoContable(**asiento_dict)
            
            self.session.add(asiento)
            self.session.flush()  # Para obtener el ID del asiento
            
            # Crear los detalles del asiento
            for detalle_data in asiento_data.detalles:
                detalle_dict = detalle_data.model_dump()
                detalle_dict['asiento_id'] = asiento.id
                detalle = DetalleAsiento(**detalle_dict)
                self.session.add(detalle)
            
            self.session.commit()
            
            # Retornar el asiento con detalles cargados
            return await self.get_by_id(asiento.id)
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al crear el asiento contable: {str(e)}")
    
    async def get_by_id(self, asiento_id: UUID) -> Optional[AsientoContable]:
        """Obtener un asiento contable por ID con sus detalles."""
        statement = (
            select(AsientoContable)
            .options(selectinload(AsientoContable.detalles))
            .where(AsientoContable.id == asiento_id)
        )
        result = self.session.exec(statement)
        return result.first()
    
    async def get_by_comprobante(self, comprobante: str) -> Optional[AsientoContable]:
        """Obtener un asiento contable por comprobante."""
        statement = (
            select(AsientoContable)
            .options(selectinload(AsientoContable.detalles))
            .where(AsientoContable.comprobante == comprobante)
        )
        result = self.session.exec(statement)
        return result.first()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        comprobante: Optional[str] = None
    ) -> List[AsientoContable]:
        """Obtener asientos contables con filtros."""
        statement = (
            select(AsientoContable)
            .options(selectinload(AsientoContable.detalles))
            .offset(skip)
            .limit(limit)
            .order_by(AsientoContable.fecha.desc(), AsientoContable.created_at.desc())
        )
        
        # Aplicar filtros
        conditions = []
        
        if fecha_desde:
            conditions.append(AsientoContable.fecha >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(AsientoContable.fecha <= fecha_hasta)
        
        if comprobante:
            conditions.append(AsientoContable.comprobante.ilike(f"%{comprobante}%"))
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return list(result.all())
    
    async def count_total(
        self,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        comprobante: Optional[str] = None
    ) -> int:
        """Contar total de asientos contables con filtros."""
        statement = select(func.count(AsientoContable.id))
        
        # Aplicar filtros
        conditions = []
        
        if fecha_desde:
            conditions.append(AsientoContable.fecha >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(AsientoContable.fecha <= fecha_hasta)
        
        if comprobante:
            conditions.append(AsientoContable.comprobante.ilike(f"%{comprobante}%"))
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return result.one()
    
    async def delete(self, asiento_id: UUID) -> bool:
        """Eliminar un asiento contable y sus detalles."""
        try:
            # Buscar el asiento
            asiento = await self.get_by_id(asiento_id)
            if not asiento:
                return False
            
            # Eliminar detalles primero (por integridad referencial)
            statement_detalles = select(DetalleAsiento).where(
                DetalleAsiento.asiento_id == asiento_id
            )
            detalles = self.session.exec(statement_detalles).all()
            
            for detalle in detalles:
                self.session.delete(detalle)
            
            # Eliminar el asiento
            self.session.delete(asiento)
            self.session.commit()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al eliminar el asiento contable: {str(e)}")
    
    async def get_asientos_por_cuenta(
        self,
        cuenta_id: UUID,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> List[AsientoContable]:
        """Obtener asientos que afectan a una cuenta específica."""
        statement = (
            select(AsientoContable)
            .options(selectinload(AsientoContable.detalles))
            .join(DetalleAsiento)
            .where(DetalleAsiento.cuenta_id == cuenta_id)
            .order_by(AsientoContable.fecha.desc())
        )
        
        # Aplicar filtros de fecha
        conditions = []
        if fecha_desde:
            conditions.append(AsientoContable.fecha >= fecha_desde)
        
        if fecha_hasta:
            conditions.append(AsientoContable.fecha <= fecha_hasta)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return list(result.all())
    
    async def get_balance_cuenta(
        self,
        cuenta_id: UUID,
        fecha_hasta: Optional[date] = None
    ) -> dict:
        """Calcular el balance de una cuenta hasta una fecha."""
        # Consulta para débitos
        statement_debitos = (
            select(func.coalesce(func.sum(DetalleAsiento.monto), 0))
            .join(AsientoContable)
            .where(
                and_(
                    DetalleAsiento.cuenta_id == cuenta_id,
                    DetalleAsiento.tipo_movimiento == TipoMovimiento.DEBITO
                )
            )
        )
        
        # Consulta para créditos
        statement_creditos = (
            select(func.coalesce(func.sum(DetalleAsiento.monto), 0))
            .join(AsientoContable)
            .where(
                and_(
                    DetalleAsiento.cuenta_id == cuenta_id,
                    DetalleAsiento.tipo_movimiento == TipoMovimiento.CREDITO
                )
            )
        )
        
        # Aplicar filtro de fecha si se especifica
        if fecha_hasta:
            statement_debitos = statement_debitos.where(AsientoContable.fecha <= fecha_hasta)
            statement_creditos = statement_creditos.where(AsientoContable.fecha <= fecha_hasta)
        
        # Ejecutar consultas
        total_debitos = self.session.exec(statement_debitos).one()
        total_creditos = self.session.exec(statement_creditos).one()
        
        # Consulta para cantidad de movimientos
        statement_count = (
            select(func.count(DetalleAsiento.id))
            .join(AsientoContable)
            .where(DetalleAsiento.cuenta_id == cuenta_id)
        )
        
        if fecha_hasta:
            statement_count = statement_count.where(AsientoContable.fecha <= fecha_hasta)
        
        cantidad_movimientos = self.session.exec(statement_count).one()
        
        saldo = total_debitos - total_creditos
        
        return {
            "total_debitos": float(total_debitos),
            "total_creditos": float(total_creditos),
            "saldo": float(saldo),
            "cantidad_movimientos": cantidad_movimientos
        }
    
    async def get_libro_diario(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> List[AsientoContable]:
        """Obtener el libro diario para un rango de fechas."""
        statement = (
            select(AsientoContable)
            .options(selectinload(AsientoContable.detalles))
            .where(
                and_(
                    AsientoContable.fecha >= fecha_desde,
                    AsientoContable.fecha <= fecha_hasta
                )
            )
            .order_by(AsientoContable.fecha, AsientoContable.comprobante)
        )
        
        result = self.session.exec(statement)
        return list(result.all())
    
    async def exists_by_comprobante(self, comprobante: str) -> bool:
        """Verificar si existe un asiento con el comprobante dado."""
        statement = select(AsientoContable.id).where(AsientoContable.comprobante == comprobante)
        result = self.session.exec(statement)
        return result.first() is not None