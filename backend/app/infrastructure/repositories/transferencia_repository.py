"""
Implementación concreta del repositorio para la entidad TransferenciaInventario.

Maneja la persistencia de transferencias de inventario entre locales
con control de estados y actualizaciones de stock automáticas.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_, extract

from app.domain.models.transferencia import (
    TransferenciaInventario, 
    TransferenciaInventarioCreate,
    EstadoTransferencia
)
from app.application.services.i_transferencia_repository import ITransferenciaRepository
from app.application.services.i_stock_local_repository import IStockLocalRepository


class TransferenciaRepository(ITransferenciaRepository):
    """
    Implementación del repositorio de transferencias usando SQLAlchemy.
    """

    def __init__(self, session: AsyncSession, stock_local_repository: IStockLocalRepository):
        self.session = session
        self.stock_local_repository = stock_local_repository

    async def create(self, transferencia_data: TransferenciaInventarioCreate) -> TransferenciaInventario:
        """
        Crea una nueva solicitud de transferencia.
        """
        # Validar que los locales pertenezcan a la misma tienda
        validacion = await self.validar_transferencia_posible(
            transferencia_data.producto_id,
            transferencia_data.local_origen_id,
            transferencia_data.local_destino_id,
            transferencia_data.cantidad_solicitada
        )
        
        if not validacion["es_valida"]:
            raise ValueError(f"Transferencia no válida: {', '.join(validacion['motivos'])}")

        # Generar número de transferencia único
        from app.domain.models.local import Local
        local_origen = await self.session.get(Local, transferencia_data.local_origen_id)
        numero_transferencia = await self.generar_numero_transferencia(local_origen.tienda_id)

        # Crear transferencia
        transferencia_dict = transferencia_data.model_dump()
        transferencia_dict["numero_transferencia"] = numero_transferencia
        transferencia_dict["estado"] = EstadoTransferencia.PENDIENTE
        transferencia_dict["fecha_solicitud"] = datetime.now(UTC)
        
        transferencia = TransferenciaInventario(**transferencia_dict)
        self.session.add(transferencia)
        await self.session.commit()
        await self.session.refresh(transferencia)
        
        return transferencia

    async def get_by_id(self, transferencia_id: UUID) -> Optional[TransferenciaInventario]:
        """
        Obtiene una transferencia por su ID.
        """
        result = await self.session.execute(
            select(TransferenciaInventario).where(
                TransferenciaInventario.id == transferencia_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_numero(self, numero_transferencia: str) -> Optional[TransferenciaInventario]:
        """
        Obtiene una transferencia por su número único.
        """
        result = await self.session.execute(
            select(TransferenciaInventario).where(
                TransferenciaInventario.numero_transferencia == numero_transferencia
            )
        )
        return result.scalar_one_or_none()

    async def get_by_local_origen(
        self,
        local_origen_id: UUID,
        estado: Optional[EstadoTransferencia] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias desde un local origen.
        """
        query = select(TransferenciaInventario).where(
            TransferenciaInventario.local_origen_id == local_origen_id
        )
        
        if estado:
            query = query.where(TransferenciaInventario.estado == estado)
        
        query = query.offset(skip).limit(limit).order_by(
            TransferenciaInventario.fecha_solicitud.desc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_local_destino(
        self,
        local_destino_id: UUID,
        estado: Optional[EstadoTransferencia] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias hacia un local destino.
        """
        query = select(TransferenciaInventario).where(
            TransferenciaInventario.local_destino_id == local_destino_id
        )
        
        if estado:
            query = query.where(TransferenciaInventario.estado == estado)
        
        query = query.offset(skip).limit(limit).order_by(
            TransferenciaInventario.fecha_solicitud.desc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_producto(
        self,
        producto_id: UUID,
        tienda_id: UUID,
        estado: Optional[EstadoTransferencia] = None
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias de un producto específico en una tienda.
        """
        from app.domain.models.local import Local

        query = (
            select(TransferenciaInventario)
            .join(Local, TransferenciaInventario.local_origen_id == Local.id)
            .where(
                and_(
                    TransferenciaInventario.producto_id == producto_id,
                    Local.tienda_id == tienda_id
                )
            )
        )
        
        if estado:
            query = query.where(TransferenciaInventario.estado == estado)
        
        query = query.order_by(TransferenciaInventario.fecha_solicitud.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_tienda(
        self,
        tienda_id: UUID,
        estado: Optional[EstadoTransferencia] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias de una tienda con filtros.
        """
        from app.domain.models.local import Local

        query = (
            select(TransferenciaInventario)
            .join(Local, TransferenciaInventario.local_origen_id == Local.id)
            .where(Local.tienda_id == tienda_id)
        )
        
        if estado:
            query = query.where(TransferenciaInventario.estado == estado)
        
        if fecha_desde:
            query = query.where(TransferenciaInventario.fecha_solicitud >= fecha_desde)
        
        if fecha_hasta:
            query = query.where(TransferenciaInventario.fecha_solicitud <= fecha_hasta)
        
        query = query.offset(skip).limit(limit).order_by(
            TransferenciaInventario.fecha_solicitud.desc()
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def marcar_como_enviado(
        self,
        transferencia_id: UUID,
        cantidad_enviada: int,
        usuario_envia_id: UUID,
        observaciones: Optional[str] = None
    ) -> Optional[TransferenciaInventario]:
        """
        Marca una transferencia como enviada y actualiza stock del local origen.
        """
        transferencia = await self.get_by_id(transferencia_id)
        if not transferencia:
            return None

        if transferencia.estado != EstadoTransferencia.PENDIENTE:
            raise ValueError("Solo se pueden enviar transferencias en estado PENDIENTE")

        # Validar stock disponible
        stock_disponible = await self.stock_local_repository.validar_stock_disponible(
            transferencia.producto_id,
            transferencia.local_origen_id,
            cantidad_enviada
        )
        
        if not stock_disponible:
            raise ValueError("Stock insuficiente en el local origen")

        # Actualizar transferencia
        transferencia.cantidad_enviada = cantidad_enviada
        transferencia.estado = EstadoTransferencia.ENVIADO
        transferencia.usuario_envia_id = usuario_envia_id
        transferencia.fecha_envio = datetime.now(UTC)
        if observaciones:
            transferencia.observaciones = observaciones

        # Decrementar stock en local origen
        await self.stock_local_repository.decrementar_stock(
            transferencia.producto_id,
            transferencia.local_origen_id,
            cantidad_enviada,
            usuario_envia_id
        )

        await self.session.commit()
        await self.session.refresh(transferencia)
        return transferencia

    async def marcar_como_recibido(
        self,
        transferencia_id: UUID,
        cantidad_recibida: int,
        usuario_recibe_id: UUID,
        observaciones: Optional[str] = None
    ) -> Optional[TransferenciaInventario]:
        """
        Marca una transferencia como recibida y actualiza stock del local destino.
        """
        transferencia = await self.get_by_id(transferencia_id)
        if not transferencia:
            return None

        if transferencia.estado != EstadoTransferencia.ENVIADO:
            raise ValueError("Solo se pueden recibir transferencias en estado ENVIADO")

        # Actualizar transferencia
        transferencia.cantidad_recibida = cantidad_recibida
        transferencia.estado = EstadoTransferencia.RECIBIDO
        transferencia.usuario_recibe_id = usuario_recibe_id
        transferencia.fecha_recepcion = datetime.now(UTC)
        if observaciones:
            if transferencia.observaciones:
                transferencia.observaciones += f" | Recepción: {observaciones}"
            else:
                transferencia.observaciones = f"Recepción: {observaciones}"

        # Incrementar stock en local destino
        # Usar el costo promedio del local origen para mantener consistencia
        stock_origen = await self.stock_local_repository.get_by_producto_and_local(
            transferencia.producto_id,
            transferencia.local_origen_id
        )
        costo_transferencia = stock_origen.costo_promedio if stock_origen else None

        await self.stock_local_repository.incrementar_stock(
            transferencia.producto_id,
            transferencia.local_destino_id,
            cantidad_recibida,
            costo_transferencia,
            usuario_recibe_id
        )

        await self.session.commit()
        await self.session.refresh(transferencia)
        return transferencia

    async def cancelar_transferencia(
        self,
        transferencia_id: UUID,
        usuario_id: UUID,
        motivo_cancelacion: str
    ) -> Optional[TransferenciaInventario]:
        """
        Cancela una transferencia y revierte stock si es necesario.
        """
        transferencia = await self.get_by_id(transferencia_id)
        if not transferencia:
            return None

        if transferencia.estado == EstadoTransferencia.RECIBIDO:
            raise ValueError("No se puede cancelar una transferencia ya recibida")

        # Si está enviada, revertir el stock en origen
        if transferencia.estado == EstadoTransferencia.ENVIADO:
            await self.stock_local_repository.incrementar_stock(
                transferencia.producto_id,
                transferencia.local_origen_id,
                transferencia.cantidad_enviada,
                None,  # No cambiar costo promedio
                usuario_id
            )

        # Actualizar estado
        transferencia.estado = EstadoTransferencia.CANCELADO
        transferencia.observaciones = f"Cancelado: {motivo_cancelacion}"

        await self.session.commit()
        await self.session.refresh(transferencia)
        return transferencia

    async def get_transferencias_pendientes(self, tienda_id: UUID) -> List[TransferenciaInventario]:
        """
        Obtiene todas las transferencias pendientes de una tienda.
        """
        return await self.get_by_tienda(
            tienda_id, 
            estado=EstadoTransferencia.PENDIENTE
        )

    async def get_transferencias_en_transito(self, tienda_id: UUID) -> List[TransferenciaInventario]:
        """
        Obtiene todas las transferencias enviadas pero no recibidas.
        """
        return await self.get_by_tienda(
            tienda_id, 
            estado=EstadoTransferencia.ENVIADO
        )

    async def get_estadisticas_transferencias(
        self,
        tienda_id: UUID,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de transferencias de una tienda.
        """
        from app.domain.models.local import Local
        from app.domain.models.product import Product

        base_query = (
            select(TransferenciaInventario)
            .join(Local, TransferenciaInventario.local_origen_id == Local.id)
            .where(Local.tienda_id == tienda_id)
        )

        if fecha_desde:
            base_query = base_query.where(TransferenciaInventario.fecha_solicitud >= fecha_desde)
        if fecha_hasta:
            base_query = base_query.where(TransferenciaInventario.fecha_solicitud <= fecha_hasta)

        # Total de transferencias
        result_total = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total_transferencias = result_total.scalar() or 0

        # Transferencias por estado
        result_por_estado = await self.session.execute(
            select(
                TransferenciaInventario.estado,
                func.count(TransferenciaInventario.id)
            )
            .select_from(base_query.subquery())
            .group_by(TransferenciaInventario.estado)
        )
        transferencias_por_estado = dict(result_por_estado.all())

        return {
            "total_transferencias": total_transferencias,
            "transferencias_por_estado": transferencias_por_estado,
            "transferencias_por_local": {},  # Se puede implementar si es necesario
            "productos_mas_transferidos": [],  # Se puede implementar si es necesario
            "tiempo_promedio_procesamiento": 0  # Se puede implementar si es necesario
        }

    async def generar_numero_transferencia(self, tienda_id: UUID) -> str:
        """
        Genera un número único para una nueva transferencia.
        """
        # Obtener el año actual
        año_actual = datetime.now(UTC).year
        
        # Contar transferencias del año actual para la tienda
        from app.domain.models.local import Local
        
        result = await self.session.execute(
            select(func.count(TransferenciaInventario.id))
            .join(Local, TransferenciaInventario.local_origen_id == Local.id)
            .where(
                and_(
                    Local.tienda_id == tienda_id,
                    extract('year', TransferenciaInventario.fecha_solicitud) == año_actual
                )
            )
        )
        contador = result.scalar() or 0
        
        # Generar número secuencial
        numero_secuencial = contador + 1
        
        return f"TRANS-{año_actual}-{numero_secuencial:03d}"

    async def get_historial_producto_local(
        self,
        producto_id: UUID,
        local_id: UUID
    ) -> List[TransferenciaInventario]:
        """
        Obtiene el historial de transferencias de un producto en un local.
        """
        result = await self.session.execute(
            select(TransferenciaInventario)
            .where(
                and_(
                    TransferenciaInventario.producto_id == producto_id,
                    or_(
                        TransferenciaInventario.local_origen_id == local_id,
                        TransferenciaInventario.local_destino_id == local_id
                    )
                )
            )
            .order_by(TransferenciaInventario.fecha_solicitud.desc())
        )
        return list(result.scalars().all())

    async def validar_transferencia_posible(
        self,
        producto_id: UUID,
        local_origen_id: UUID,
        local_destino_id: UUID,
        cantidad: int
    ) -> Dict[str, Any]:
        """
        Valida si una transferencia es posible.
        """
        motivos = []
        
        # Verificar que los locales son diferentes
        if local_origen_id == local_destino_id:
            motivos.append("El local origen y destino no pueden ser el mismo")

        # Verificar que los locales pertenecen a la misma tienda
        from app.domain.models.local import Local
        
        result_locales = await self.session.execute(
            select(Local.tienda_id)
            .where(Local.id.in_([local_origen_id, local_destino_id]))
        )
        tiendas = list(result_locales.scalars().all())
        
        if len(set(tiendas)) > 1:
            motivos.append("Los locales deben pertenecer a la misma tienda")

        # Verificar stock disponible
        stock_disponible = await self.stock_local_repository.validar_stock_disponible(
            producto_id, local_origen_id, cantidad
        )
        
        if not stock_disponible:
            # Obtener stock actual para información
            stock_local = await self.stock_local_repository.get_by_producto_and_local(
                producto_id, local_origen_id
            )
            stock_actual = stock_local.cantidad if stock_local else 0
            motivos.append(f"Stock insuficiente (disponible: {stock_actual}, requerido: {cantidad})")
        else:
            stock_local = await self.stock_local_repository.get_by_producto_and_local(
                producto_id, local_origen_id
            )
            stock_actual = stock_local.cantidad if stock_local else 0

        return {
            "es_valida": len(motivos) == 0,
            "motivos": motivos,
            "stock_disponible": stock_actual if 'stock_actual' in locals() else 0
        }