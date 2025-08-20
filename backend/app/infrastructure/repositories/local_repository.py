"""
Implementación concreta del repositorio para la entidad Local.

Maneja la persistencia de locales (ubicaciones físicas) dentro de tiendas
con SQLAlchemy/SQLModel incluyendo operaciones CRUD y consultas específicas.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlmodel import Session
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.domain.models.local import Local, LocalCreate, LocalUpdate
from app.application.services.i_local_repository import ILocalRepository


class LocalRepository(ILocalRepository):
    """
    Implementación del repositorio de locales usando SQLAlchemy.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, local_data: LocalCreate) -> Local:
        """
        Crea un nuevo local en una tienda.
        """
        # Verificar que el código no exista en la tienda
        codigo_disponible = self.verificar_codigo_disponible(
            local_data.codigo, local_data.tienda_id
        )
        if not codigo_disponible:
            raise ValueError(
                f"El código '{local_data.codigo}' ya existe en la tienda"
            )

        # Crear local
        local = Local(**local_data.model_dump())
        self.session.add(local)
        self.session.commit()
        self.session.refresh(local)
        
        return local

    def get_by_id(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local por su ID.
        """
        result = self.session.exec(
            select(Local).where(Local.id == local_id)
        )
        return result.scalar_one_or_none()

    def get_by_codigo_and_tienda(
        self, 
        codigo: str, 
        tienda_id: UUID
    ) -> Optional[Local]:
        """
        Obtiene un local por su código dentro de una tienda específica.
        """
        result = self.session.exec(
            select(Local).where(
                and_(Local.codigo == codigo, Local.tienda_id == tienda_id)
            )
        )
        return result.scalar_one_or_none()

    def get_by_tienda(
        self, 
        tienda_id: UUID, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Local]:
        """
        Obtiene todos los locales de una tienda con paginación.
        """
        query = select(Local).where(Local.tienda_id == tienda_id)
        
        if not include_inactive:
            query = query.where(Local.is_active == True)
        
        query = query.offset(skip).limit(limit).order_by(Local.created_at.desc())
        
        result = self.session.exec(query)
        return list(result.scalars().all())

    def get_locales_activos_by_tienda(self, tienda_id: UUID) -> List[Local]:
        """
        Obtiene todos los locales activos de una tienda.
        """
        result = self.session.exec(
            select(Local).where(
                and_(Local.tienda_id == tienda_id, Local.is_active == True)
            ).order_by(Local.nombre)
        )
        return list(result.scalars().all())

    def update(self, local_id: UUID, local_data: LocalUpdate) -> Optional[Local]:
        """
        Actualiza un local existente.
        """
        # Obtener local actual
        local = self.get_by_id(local_id)
        if not local:
            return None

        # Verificar código único si se está cambiando
        if local_data.codigo and local_data.codigo != local.codigo:
            codigo_disponible = self.verificar_codigo_disponible(
                local_data.codigo, local.tienda_id, local_id
            )
            if not codigo_disponible:
                raise ValueError(
                    f"El código '{local_data.codigo}' ya existe en la tienda"
                )

        # Actualizar campos
        update_data = local_data.model_dump(exclude_unset=True)
        if update_data:
            local.actualizar_timestamp()
            for field, value in update_data.items():
                setattr(local, field, value)

        self.session.commit()
        self.session.refresh(local)
        return local

    def delete(self, local_id: UUID) -> bool:
        """
        Elimina (desactiva) un local.
        """
        local = self.get_by_id(local_id)
        if not local:
            return False

        local.is_active = False
        local.actualizar_timestamp()
        self.session.commit()
        return True

    def verificar_codigo_disponible(
        self, 
        codigo: str, 
        tienda_id: UUID, 
        local_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica si un código de local está disponible dentro de una tienda.
        """
        query = select(Local).where(
            and_(Local.codigo == codigo, Local.tienda_id == tienda_id)
        )
        
        if local_id:
            query = query.where(Local.id != local_id)
        
        result = self.session.exec(query)
        return result.scalar_one_or_none() is None

    def get_with_stock(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local con su información de stock asociado.
        """
        result = self.session.exec(
            select(Local)
            .options(selectinload(Local.stock_productos))
            .where(Local.id == local_id)
        )
        return result.scalar_one_or_none()

    def get_with_usuarios(self, local_id: UUID) -> Optional[Local]:
        """
        Obtiene un local con los usuarios que tienen permisos en él.
        """
        result = self.session.exec(
            select(Local)
            .options(selectinload(Local.usuarios_con_permisos))
            .where(Local.id == local_id)
        )
        return result.scalar_one_or_none()

    def get_locales_usuario(self, user_id: UUID) -> List[Local]:
        """
        Obtiene todos los locales donde un usuario tiene permisos.
        """
        from app.domain.models.usuario_local import UsuarioLocal

        result = self.session.exec(
            select(Local)
            .join(UsuarioLocal, Local.id == UsuarioLocal.local_id)
            .where(
                and_(
                    UsuarioLocal.user_id == user_id,
                    UsuarioLocal.is_active == True,
                    Local.is_active == True
                )
            )
            .order_by(Local.nombre)
        )
        return list(result.scalars().all())

    def get_locales_para_transferencia(
        self, 
        local_origen_id: UUID
    ) -> List[Local]:
        """
        Obtiene locales disponibles para transferencia desde un local origen.
        """
        # Obtener la tienda del local origen
        local_origen = self.get_by_id(local_origen_id)
        if not local_origen:
            return []

        # Obtener todos los locales activos de la misma tienda excepto el origen
        result = self.session.exec(
            select(Local).where(
                and_(
                    Local.tienda_id == local_origen.tienda_id,
                    Local.id != local_origen_id,
                    Local.is_active == True
                )
            ).order_by(Local.nombre)
        )
        return list(result.scalars().all())

    def get_estadisticas_local(self, local_id: UUID) -> Dict[str, Any]:
        """
        Obtiene estadísticas básicas de un local.
        """
        from app.domain.models.stock_local import StockLocal
        from app.domain.models.usuario_local import UsuarioLocal
        from app.domain.models.transferencia import TransferenciaInventario, EstadoTransferencia

        # Contar productos con stock
        result_productos = self.session.exec(
            select(func.count(StockLocal.id))
            .where(StockLocal.local_id == local_id)
        )
        total_productos = result_productos.scalar() or 0

        # Sumar stock total
        result_stock_total = self.session.exec(
            select(func.coalesce(func.sum(StockLocal.cantidad), 0))
            .where(StockLocal.local_id == local_id)
        )
        total_stock = result_stock_total.scalar() or 0

        # Sumar valor del inventario
        result_valor = self.session.exec(
            select(func.coalesce(func.sum(StockLocal.valor_total_inventario), 0))
            .where(StockLocal.local_id == local_id)
        )
        valor_inventario = result_valor.scalar() or 0

        # Contar productos bajo mínimo
        result_bajo_minimo = self.session.exec(
            select(func.count(StockLocal.id))
            .where(
                and_(
                    StockLocal.local_id == local_id,
                    StockLocal.cantidad <= StockLocal.stock_minimo
                )
            )
        )
        productos_bajo_minimo = result_bajo_minimo.scalar() or 0

        # Contar usuarios con permisos
        result_usuarios = self.session.exec(
            select(func.count(UsuarioLocal.id))
            .where(
                and_(
                    UsuarioLocal.local_id == local_id,
                    UsuarioLocal.is_active == True
                )
            )
        )
        total_usuarios = result_usuarios.scalar() or 0

        # Contar transferencias pendientes
        result_transferencias = self.session.exec(
            select(func.count(TransferenciaInventario.id))
            .where(
                and_(
                    or_(
                        TransferenciaInventario.local_origen_id == local_id,
                        TransferenciaInventario.local_destino_id == local_id
                    ),
                    TransferenciaInventario.estado.in_([
                        EstadoTransferencia.PENDIENTE,
                        EstadoTransferencia.ENVIADO
                    ])
                )
            )
        )
        transferencias_pendientes = result_transferencias.scalar() or 0

        return {
            "total_productos": total_productos,
            "total_stock": total_stock,
            "valor_inventario": float(valor_inventario),
            "productos_bajo_minimo": productos_bajo_minimo,
            "total_usuarios": total_usuarios,
            "transferencias_pendientes": transferencias_pendientes
        }

    def buscar_locales(
        self, 
        tienda_id: UUID,
        texto_busqueda: str,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None
    ) -> List[Local]:
        """
        Busca locales por texto en nombre, código o dirección.
        """
        query = select(Local).where(Local.tienda_id == tienda_id)
        
        # Filtro por texto
        if texto_busqueda:
            texto_busqueda = f"%{texto_busqueda}%"
            query = query.where(
                or_(
                    Local.nombre.ilike(texto_busqueda),
                    Local.codigo.ilike(texto_busqueda),
                    Local.direccion.ilike(texto_busqueda)
                )
            )
        
        # Filtros adicionales
        if ciudad:
            query = query.where(Local.ciudad.ilike(f"%{ciudad}%"))
        
        if departamento:
            query = query.where(Local.departamento.ilike(f"%{departamento}%"))
        
        query = query.where(Local.is_active == True).order_by(Local.nombre)
        
        result = self.session.exec(query)
        return list(result.scalars().all())