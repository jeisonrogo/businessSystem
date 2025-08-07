"""
Implementación del repositorio de clientes usando SQLModel/PostgreSQL.
Maneja la persistencia y consulta de clientes con validaciones de negocio.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, UTC
from sqlmodel import Session, select, and_, func, or_
from sqlalchemy.exc import IntegrityError

from app.application.services.i_cliente_repository import IClienteRepository
from app.domain.models.facturacion import (
    Cliente,
    ClienteCreate,
    ClienteUpdate,
    TipoCliente,
    TipoDocumento
)


class SQLClienteRepository(IClienteRepository):
    """
    Implementación del repositorio de clientes usando SQLModel/PostgreSQL.
    """
    
    def __init__(self, session: Session):
        self.session = session

    async def create(self, cliente_data: ClienteCreate) -> Cliente:
        """Crear un nuevo cliente."""
        try:
            # Verificar que no existe cliente con el mismo documento
            existing = await self.get_by_documento(cliente_data.numero_documento)
            if existing:
                raise ValueError(f"Ya existe un cliente con el documento {cliente_data.numero_documento}")

            # Crear el cliente
            cliente_dict = cliente_data.model_dump()
            cliente_dict['created_at'] = datetime.now(UTC)
            cliente = Cliente(**cliente_dict)
            
            self.session.add(cliente)
            self.session.commit()
            self.session.refresh(cliente)
            
            return cliente
        
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Error de integridad al crear cliente: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al crear el cliente: {str(e)}")

    async def get_by_id(self, cliente_id: UUID) -> Optional[Cliente]:
        """Obtener un cliente por su ID."""
        statement = select(Cliente).where(Cliente.id == cliente_id)
        result = self.session.exec(statement)
        return result.first()

    async def get_by_documento(self, numero_documento: str) -> Optional[Cliente]:
        """Obtener un cliente por su número de documento."""
        statement = select(Cliente).where(Cliente.numero_documento == numero_documento)
        result = self.session.exec(statement)
        return result.first()

    async def get_by_email(self, email: str) -> Optional[Cliente]:
        """Obtener un cliente por su email."""
        statement = select(Cliente).where(Cliente.email == email)
        result = self.session.exec(statement)
        return result.first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        tipo_cliente: Optional[TipoCliente] = None,
        only_active: bool = True
    ) -> List[Cliente]:
        """Obtener lista paginada de clientes con filtros opcionales."""
        statement = select(Cliente).offset(skip).limit(limit).order_by(Cliente.created_at.desc())
        
        # Aplicar filtros
        conditions = []
        
        if only_active:
            conditions.append(Cliente.is_active == True)
        
        if tipo_cliente:
            conditions.append(Cliente.tipo_cliente == tipo_cliente)
        
        if search:
            # Búsqueda en nombre, documento y email
            search_pattern = f"%{search}%"
            search_conditions = or_(
                Cliente.nombre_completo.ilike(search_pattern),
                Cliente.numero_documento.ilike(search_pattern),
                Cliente.email.ilike(search_pattern) if search else False,
                Cliente.nombre_comercial.ilike(search_pattern) if search else False
            )
            conditions.append(search_conditions)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return list(result.all())

    async def update(self, cliente_id: UUID, cliente_data: ClienteUpdate) -> Optional[Cliente]:
        """Actualizar un cliente existente."""
        try:
            cliente = await self.get_by_id(cliente_id)
            if not cliente:
                return None
            
            # Actualizar campos que no son None
            update_data = cliente_data.model_dump(exclude_unset=True)
            update_data['updated_at'] = datetime.now(UTC)
            
            for field, value in update_data.items():
                setattr(cliente, field, value)
            
            self.session.add(cliente)
            self.session.commit()
            self.session.refresh(cliente)
            
            return cliente
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al actualizar el cliente: {str(e)}")

    async def delete(self, cliente_id: UUID) -> bool:
        """Eliminar (desactivar) un cliente."""
        try:
            cliente = await self.get_by_id(cliente_id)
            if not cliente:
                return False
            
            cliente.is_active = False
            cliente.updated_at = datetime.now(UTC)
            
            self.session.add(cliente)
            self.session.commit()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al eliminar el cliente: {str(e)}")

    async def exists_by_documento(
        self,
        numero_documento: str,
        exclude_id: Optional[UUID] = None
    ) -> bool:
        """Verificar si existe un cliente con el número de documento dado."""
        statement = select(Cliente.id).where(Cliente.numero_documento == numero_documento)
        
        if exclude_id:
            statement = statement.where(Cliente.id != exclude_id)
        
        result = self.session.exec(statement)
        return result.first() is not None

    async def count_total(
        self,
        search: Optional[str] = None,
        tipo_cliente: Optional[TipoCliente] = None,
        only_active: bool = True
    ) -> int:
        """Contar el número total de clientes que cumplen los criterios."""
        statement = select(func.count(Cliente.id))
        
        # Aplicar filtros (mismo lógica que get_all)
        conditions = []
        
        if only_active:
            conditions.append(Cliente.is_active == True)
        
        if tipo_cliente:
            conditions.append(Cliente.tipo_cliente == tipo_cliente)
        
        if search:
            search_pattern = f"%{search}%"
            search_conditions = or_(
                Cliente.nombre_completo.ilike(search_pattern),
                Cliente.numero_documento.ilike(search_pattern),
                Cliente.email.ilike(search_pattern) if search else False,
                Cliente.nombre_comercial.ilike(search_pattern) if search else False
            )
            conditions.append(search_conditions)
        
        if conditions:
            statement = statement.where(and_(*conditions))
        
        result = self.session.exec(statement)
        return result.one()

    async def get_clientes_frecuentes(self, limit: int = 10) -> List[Cliente]:
        """Obtener los clientes más frecuentes basado en número de facturas."""
        # Importación diferida para evitar circular imports
        from app.domain.models.facturacion import Factura
        
        statement = (
            select(Cliente)
            .join(Factura, Cliente.id == Factura.cliente_id)
            .where(Cliente.is_active == True)
            .group_by(Cliente.id)
            .order_by(func.count(Factura.id).desc())
            .limit(limit)
        )
        
        result = self.session.exec(statement)
        return list(result.all())

    async def get_clientes_by_tipo(self, tipo_cliente: TipoCliente) -> List[Cliente]:
        """Obtener todos los clientes de un tipo específico."""
        statement = (
            select(Cliente)
            .where(
                and_(
                    Cliente.tipo_cliente == tipo_cliente,
                    Cliente.is_active == True
                )
            )
            .order_by(Cliente.nombre_completo)
        )
        
        result = self.session.exec(statement)
        return list(result.all())

    async def search_clientes(self, term: str, limit: int = 20) -> List[Cliente]:
        """Buscar clientes por término (nombre, documento, email)."""
        search_pattern = f"%{term}%"
        
        statement = (
            select(Cliente)
            .where(
                and_(
                    Cliente.is_active == True,
                    or_(
                        Cliente.nombre_completo.ilike(search_pattern),
                        Cliente.numero_documento.ilike(search_pattern),
                        Cliente.email.ilike(search_pattern),
                        Cliente.nombre_comercial.ilike(search_pattern)
                    )
                )
            )
            .order_by(Cliente.nombre_completo)
            .limit(limit)
        )
        
        result = self.session.exec(statement)
        return list(result.all())

    async def get_estadisticas_cliente(self, cliente_id: UUID) -> dict:
        """Obtener estadísticas de un cliente específico."""
        from app.domain.models.facturacion import Factura, EstadoFactura
        
        # Estadísticas básicas
        statement_facturas = (
            select(
                func.count(Factura.id).label('total_facturas'),
                func.coalesce(func.sum(Factura.total_factura), 0).label('total_monto'),
                func.coalesce(func.avg(Factura.total_factura), 0).label('promedio_compra'),
                func.max(Factura.fecha_emision).label('ultima_compra')
            )
            .where(
                and_(
                    Factura.cliente_id == cliente_id,
                    Factura.estado.in_([EstadoFactura.EMITIDA, EstadoFactura.PAGADA])
                )
            )
        )
        
        result = self.session.exec(statement_facturas).first()
        
        # Facturas pendientes
        statement_pendientes = (
            select(
                func.count(Factura.id).label('facturas_pendientes'),
                func.coalesce(func.sum(Factura.total_factura), 0).label('monto_pendiente')
            )
            .where(
                and_(
                    Factura.cliente_id == cliente_id,
                    Factura.estado == EstadoFactura.EMITIDA
                )
            )
        )
        
        result_pendientes = self.session.exec(statement_pendientes).first()
        
        return {
            "total_facturas": int(result.total_facturas) if result else 0,
            "total_monto": float(result.total_monto) if result else 0.0,
            "promedio_compra": float(result.promedio_compra) if result else 0.0,
            "ultima_compra": result.ultima_compra if result else None,
            "facturas_pendientes": int(result_pendientes.facturas_pendientes) if result_pendientes else 0,
            "monto_pendiente": float(result_pendientes.monto_pendiente) if result_pendientes else 0.0
        }

    async def activate_cliente(self, cliente_id: UUID) -> bool:
        """Reactivar un cliente desactivado."""
        try:
            cliente = await self.get_by_id(cliente_id)
            if not cliente:
                return False
            
            cliente.is_active = True
            cliente.updated_at = datetime.now(UTC)
            
            self.session.add(cliente)
            self.session.commit()
            
            return True
        
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error al reactivar el cliente: {str(e)}")