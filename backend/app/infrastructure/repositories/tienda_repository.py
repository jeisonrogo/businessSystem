"""
Implementación concreta del repositorio para la entidad Tienda.

Maneja la persistencia de tiendas con SQLAlchemy/SQLModel incluyendo
operaciones CRUD y consultas específicas del negocio.
"""

from typing import List, Optional
from uuid import UUID
from sqlmodel import Session
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload

from app.domain.models.tienda import Tienda, TiendaCreate, TiendaUpdate
from app.application.services.i_tienda_repository import ITiendaRepository


class TiendaRepository(ITiendaRepository):
    """
    Implementación del repositorio de tiendas usando SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, tienda_data: TiendaCreate) -> Tienda:
        """
        Crea una nueva tienda en el sistema.
        """
        # Verificar que el código no exista
        codigo_existe = self.verificar_codigo_disponible(tienda_data.codigo)
        if not codigo_existe:
            raise ValueError(f"El código '{tienda_data.codigo}' ya está en uso")

        # Crear tienda
        tienda = Tienda(**tienda_data.model_dump())
        self.session.add(tienda)
        self.session.commit()
        self.session.refresh(tienda)
        
        return tienda

    def get_by_id(self, tienda_id: UUID) -> Optional[Tienda]:
        """
        Obtiene una tienda por su ID.
        """
        result = self.session.exec(
            select(Tienda).where(Tienda.id == tienda_id)
        )
        return result.scalar_one_or_none()

    def get_by_codigo(self, codigo: str) -> Optional[Tienda]:
        """
        Obtiene una tienda por su código único.
        """
        result = self.session.exec(
            select(Tienda).where(Tienda.codigo == codigo)
        )
        return result.scalar_one_or_none()

    def get_by_dominio(self, dominio: str) -> Optional[Tienda]:
        """
        Obtiene una tienda por su dominio.
        """
        result = self.session.exec(
            select(Tienda).where(Tienda.dominio == dominio)
        )
        return result.scalar_one_or_none()

    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Tienda]:
        """
        Obtiene todas las tiendas con paginación.
        """
        query = select(Tienda)
        
        if not include_inactive:
            query = query.where(Tienda.is_active == True)
        
        query = query.offset(skip).limit(limit).order_by(Tienda.created_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def update(self, tienda_id: UUID, tienda_data: TiendaUpdate) -> Optional[Tienda]:
        """
        Actualiza una tienda existente.
        """
        # Obtener tienda actual
        tienda = self.get_by_id(tienda_id)
        if not tienda:
            return None

        # Verificar código único si se está cambiando
        if tienda_data.codigo and tienda_data.codigo != tienda.codigo:
            codigo_disponible = self.verificar_codigo_disponible(
                tienda_data.codigo, tienda_id
            )
            if not codigo_disponible:
                raise ValueError(f"El código '{tienda_data.codigo}' ya está en uso")

        # Actualizar campos
        update_data = tienda_data.model_dump(exclude_unset=True)
        if update_data:
            tienda.actualizar_timestamp()
            for field, value in update_data.items():
                setattr(tienda, field, value)

        self.session.commit()
        self.session.refresh(tienda)
        return tienda

    def delete(self, tienda_id: UUID) -> bool:
        """
        Elimina (desactiva) una tienda.
        """
        tienda = self.get_by_id(tienda_id)
        if not tienda:
            return False

        tienda.is_active = False
        tienda.actualizar_timestamp()
        self.session.commit()
        return True

    def get_tiendas_activas(self) -> List[Tienda]:
        """
        Obtiene todas las tiendas activas.
        """
        result = self.session.exec(
            select(Tienda).where(Tienda.is_active == True).order_by(Tienda.nombre)
        )
        return list(result.scalars().all())

    def incrementar_consecutivo_factura(self, tienda_id: UUID) -> Optional[str]:
        """
        Incrementa el consecutivo de facturación y retorna el número generado.
        """
        # Usar transacción explícita para evitar condiciones de carrera
        with self.session.begin():
            # Obtener tienda con lock para update
            result = self.session.exec(
                select(Tienda)
                .where(Tienda.id == tienda_id)
                .with_for_update()
            )
            tienda = result.scalar_one_or_none()
            
            if not tienda:
                return None

            # Generar número de factura
            numero_factura = tienda.obtener_siguiente_numero_factura()
            
            # Incrementar consecutivo
            tienda.consecutivo_facturas += 1
            tienda.actualizar_timestamp()
            
            self.session.commit()
            return numero_factura

    def verificar_codigo_disponible(
        self, 
        codigo: str, 
        tienda_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si un código de tienda está disponible.
        """
        query = select(Tienda).where(Tienda.codigo == codigo)
        
        if tienda_id:
            query = query.where(Tienda.id != tienda_id)
        
        result = self.session.exec(query)
        return result.scalar_one_or_none() is None

    def get_with_locales(self, tienda_id: UUID) -> Optional[Tienda]:
        """
        Obtiene una tienda con sus locales asociados.
        """
        result = self.session.exec(
            select(Tienda)
            .options(selectinload(Tienda.locales))
            .where(Tienda.id == tienda_id)
        )
        return result.scalar_one_or_none()

    def get_estadisticas_tienda(self, tienda_id: UUID) -> dict:
        """
        Obtiene estadísticas básicas de una tienda.
        """
        from app.domain.models.local import Local
        from app.domain.models.product import Product
        from app.domain.models.user import User

        # Contar locales
        result_locales = self.session.exec(
            select(func.count(Local.id))
            .where(Local.tienda_id == tienda_id)
        )
        total_locales = result_locales.scalar() or 0

        # Contar locales activos
        result_locales_activos = self.session.exec(
            select(func.count(Local.id))
            .where(and_(Local.tienda_id == tienda_id, Local.is_active == True))
        )
        locales_activos = result_locales_activos.scalar() or 0

        # Contar productos
        result_productos = self.session.exec(
            select(func.count(Product.id))
            .where(Product.tienda_id == tienda_id)
        )
        total_productos = result_productos.scalar() or 0

        # Contar usuarios
        result_usuarios = self.session.exec(
            select(func.count(User.id))
            .where(User.tienda_id == tienda_id)
        )
        total_usuarios = result_usuarios.scalar() or 0

        return {
            "total_locales": total_locales,
            "locales_activos": locales_activos,
            "total_productos": total_productos,
            "total_usuarios": total_usuarios
        }