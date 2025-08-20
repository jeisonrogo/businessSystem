"""
Implementación concreta del repositorio para la entidad StockLocal.

Maneja la persistencia de stock independiente por local con cálculos
de costo promedio ponderado usando SQLAlchemy/SQLModel.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, UTC
from sqlmodel import Session
from sqlalchemy import select, and_, func, or_, update
from sqlalchemy.orm import selectinload

from app.domain.models.stock_local import StockLocal, StockLocalCreate, StockLocalUpdate
from app.application.services.i_stock_local_repository import IStockLocalRepository


class StockLocalRepository(IStockLocalRepository):
    """
    Implementación del repositorio de stock por local usando SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, stock_data: StockLocalCreate) -> StockLocal:
        """
        Crea un registro de stock inicial para un producto en un local.
        """
        # Verificar que no exista ya stock para este producto-local
        existing_stock = self.get_by_producto_and_local(
            stock_data.producto_id, stock_data.local_id
        )
        if existing_stock:
            raise ValueError(
                "Ya existe un registro de stock para este producto en el local"
            )

        # Crear stock
        stock = StockLocal(**stock_data.model_dump())
        stock.valor_total_inventario = stock.cantidad * stock.costo_promedio
        
        self.session.add(stock)
        self.session.commit()
        self.session.refresh(stock)
        
        return stock

    def get_by_id(self, stock_id: UUID) -> Optional[StockLocal]:
        """
        Obtiene un registro de stock por su ID.
        """
        result = self.session.exec(
            select(StockLocal).where(StockLocal.id == stock_id)
        )
        return result.scalar_one_or_none()

    def get_by_producto_and_local(
        self, 
        producto_id: UUID, 
        local_id: UUID
    ) -> Optional[StockLocal]:
        """
        Obtiene el stock de un producto específico en un local.
        """
        result = self.session.exec(
            select(StockLocal).where(
                and_(
                    StockLocal.producto_id == producto_id,
                    StockLocal.local_id == local_id
                )
            )
        )
        return result.scalar_one_or_none()

    def get_by_local(
        self, 
        local_id: UUID,
        skip: int = 0,
        limit: int = 100,
        incluir_sin_stock: bool = True
    ) -> List[StockLocal]:
        """
        Obtiene todo el stock de un local con paginación.
        """
        query = select(StockLocal).where(StockLocal.local_id == local_id)
        
        if not incluir_sin_stock:
            query = query.where(StockLocal.cantidad > 0)
        
        query = query.offset(skip).limit(limit).order_by(StockLocal.updated_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def get_by_producto(self, producto_id: UUID) -> List[StockLocal]:
        """
        Obtiene el stock de un producto en todos los locales.
        """
        result = self.session.exec(
            select(StockLocal)
            .where(StockLocal.producto_id == producto_id)
            .order_by(StockLocal.cantidad.desc())
        )
        return list(result.scalars().all())

    def get_by_tienda(
        self, 
        tienda_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockLocal]:
        """
        Obtiene todo el stock de una tienda (todos sus locales).
        """
        from app.domain.models.local import Local

        query = (
            select(StockLocal)
            .join(Local, StockLocal.local_id == Local.id)
            .where(Local.tienda_id == tienda_id)
            .offset(skip)
            .limit(limit)
            .order_by(StockLocal.updated_at.desc())
        )
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def actualizar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        nueva_cantidad: int,
        nuevo_costo: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Actualiza el stock de un producto en un local.
        """
        stock = self.get_by_producto_and_local(producto_id, local_id)
        if not stock:
            return None

        # Usar el método de dominio para actualizar
        stock.actualizar_stock(nueva_cantidad, nuevo_costo, usuario_id)
        
        self.session.commit()
        self.session.refresh(stock)
        return stock

    def incrementar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_incremento: int,
        costo_unitario: Optional[Decimal] = None,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Incrementa el stock con cálculo de costo promedio ponderado.
        """
        stock = self.get_by_producto_and_local(producto_id, local_id)
        if not stock:
            return None

        # Usar el método de dominio para incrementar
        stock.incrementar_stock(cantidad_incremento, costo_unitario, usuario_id)
        
        self.session.commit()
        self.session.refresh(stock)
        return stock

    def decrementar_stock(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_decremento: int,
        usuario_id: Optional[UUID] = None
    ) -> Optional[StockLocal]:
        """
        Decrementa el stock manteniendo el costo promedio.
        """
        stock = self.get_by_producto_and_local(producto_id, local_id)
        if not stock:
            return None

        # Usar el método de dominio para decrementar
        stock.decrementar_stock(cantidad_decremento, usuario_id)
        
        self.session.commit()
        self.session.refresh(stock)
        return stock

    def update_configuracion(
        self,
        stock_id: UUID,
        stock_data: StockLocalUpdate
    ) -> Optional[StockLocal]:
        """
        Actualiza la configuración de stock (mínimos, máximos, etc.).
        """
        stock = self.get_by_id(stock_id)
        if not stock:
            return None

        # Actualizar campos de configuración
        update_data = stock_data.model_dump(exclude_unset=True)
        if update_data:
            for field, value in update_data.items():
                setattr(stock, field, value)
            
            stock.updated_at = datetime.now(UTC)

        self.session.commit()
        self.session.refresh(stock)
        return stock

    def delete(self, stock_id: UUID) -> bool:
        """
        Elimina un registro de stock (solo si cantidad es 0).
        """
        stock = self.get_by_id(stock_id)
        if not stock:
            return False

        if stock.cantidad > 0:
            raise ValueError("No se puede eliminar stock con cantidad mayor a 0")

        self.session.delete(stock)
        self.session.commit()
        return True

    def get_productos_bajo_minimo(self, local_id: UUID) -> List[StockLocal]:
        """
        Obtiene productos con stock por debajo del mínimo en un local.
        """
        result = self.session.exec(
            select(StockLocal)
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad <= StockLocal.stock_minimo
                )
            )
            .order_by(StockLocal.cantidad.asc())
        )
        return list(result.scalars().all())

    def get_productos_agotados(self, local_id: UUID) -> List[StockLocal]:
        """
        Obtiene productos agotados (cantidad = 0) en un local.
        """
        result = self.session.exec(
            select(StockLocal)
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad == 0
                )
            )
            .order_by(StockLocal.updated_at.desc())
        )
        return list(result.scalars().all())

    def get_resumen_por_local(self, local_id: UUID) -> Dict[str, Any]:
        """
        Obtiene resumen de inventario de un local.
        """
        # Total de productos
        result_total = self.session.exec(
            select(func.count(StockLocal.id))
            .where(StockLocal.local_id == local_id)
        )
        total_productos = result_total.scalar() or 0

        # Productos con stock
        result_con_stock = self.session.exec(
            select(func.count(StockLocal.id))
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad > 0
                )
            )
        )
        productos_con_stock = result_con_stock.scalar() or 0

        # Productos bajo mínimo
        result_bajo_minimo = self.session.exec(
            select(func.count(StockLocal.id))
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad <= StockLocal.stock_minimo,
                    StockLocal.cantidad > 0
                )
            )
        )
        productos_bajo_minimo = result_bajo_minimo.scalar() or 0

        # Productos agotados
        result_agotados = self.session.exec(
            select(func.count(StockLocal.id))
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad == 0
                )
            )
        )
        productos_agotados = result_agotados.scalar() or 0

        # Valor total del inventario
        result_valor = self.session.exec(
            select(func.coalesce(func.sum(StockLocal.valor_total_inventario), 0))
            .where(StockLocal.local_id == local_id)
        )
        valor_total_inventario = result_valor.scalar() or 0

        return {
            "total_productos": total_productos,
            "productos_con_stock": productos_con_stock,
            "productos_bajo_minimo": productos_bajo_minimo,
            "productos_agotados": productos_agotados,
            "valor_total_inventario": float(valor_total_inventario)
        }

    def get_stock_global_producto(self, producto_id: UUID) -> Dict[str, Any]:
        """
        Obtiene el stock global de un producto en todos los locales.
        """
        stocks_locales = self.get_by_producto(producto_id)
        
        stock_total = sum(stock.cantidad for stock in stocks_locales)
        valor_total = sum(stock.valor_total_inventario for stock in stocks_locales)
        
        # Cálculo de costo promedio global ponderado
        if stock_total > 0:
            costo_promedio_global = valor_total / stock_total
        else:
            costo_promedio_global = Decimal('0.00')

        return {
            "stock_total": stock_total,
            "stock_por_local": stocks_locales,
            "costo_promedio_global": float(costo_promedio_global),
            "valor_total_global": float(valor_total)
        }

    def buscar_productos_con_stock(
        self,
        tienda_id: UUID,
        texto_busqueda: str,
        local_id: Optional[UUID] = None
    ) -> List[StockLocal]:
        """
        Busca productos con stock por nombre o SKU.
        """
        from app.domain.models.product import Product
        from app.domain.models.local import Local

        query = (
            select(StockLocal)
            .join(Product, StockLocal.producto_id == Product.id)
            .join(Local, StockLocal.local_id == Local.id)
            .where(Local.tienda_id == tienda_id)
        )

        if local_id:
            query = query.where(StockLocal.local_id == local_id)

        if texto_busqueda:
            texto_busqueda = f"%{texto_busqueda}%"
            query = query.where(
                or_(
                    Product.nombre.ilike(texto_busqueda),
                    Product.sku.ilike(texto_busqueda)
                )
            )

        query = query.where(StockLocal.cantidad > 0).order_by(Product.nombre)

        result = self.session.exec(query)
        return list(result.scalars().all())

    def validar_stock_disponible(
        self,
        producto_id: UUID,
        local_id: UUID,
        cantidad_requerida: int
    ) -> bool:
        """
        Valida si hay stock suficiente para una operación.
        """
        stock = self.get_by_producto_and_local(producto_id, local_id)
        if not stock:
            return False
        
        return stock.cantidad >= cantidad_requerida