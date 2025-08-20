"""
Interface del repositorio para la entidad TransferenciaInventario en el sistema multi-tenant.

Define las operaciones de persistencia para gestionar transferencias de inventario
entre locales de la misma tienda.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.models.transferencia import (
    TransferenciaInventario, 
    TransferenciaInventarioCreate,
    EstadoTransferencia
)


class ITransferenciaRepository(ABC):
    """
    Interface del repositorio para gestión de transferencias de inventario.
    
    Define las operaciones para el ciclo completo de transferencias
    entre locales con control de estados y auditoría.
    """

    @abstractmethod
    async def create(self, transferencia_data: TransferenciaInventarioCreate) -> TransferenciaInventario:
        """
        Crea una nueva solicitud de transferencia.

        Args:
            transferencia_data: Datos para crear la transferencia

        Returns:
            TransferenciaInventario: La transferencia creada

        Raises:
            ValueError: Si los locales no pertenecen a la misma tienda
            StockInsuficienteError: Si no hay stock suficiente en origen
            ForeignKeyError: Si producto, locales o usuario no existen
        """
        pass

    @abstractmethod
    async def get_by_id(self, transferencia_id: UUID) -> Optional[TransferenciaInventario]:
        """
        Obtiene una transferencia por su ID.

        Args:
            transferencia_id: ID único de la transferencia

        Returns:
            TransferenciaInventario o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_numero(self, numero_transferencia: str) -> Optional[TransferenciaInventario]:
        """
        Obtiene una transferencia por su número único.

        Args:
            numero_transferencia: Número de la transferencia

        Returns:
            TransferenciaInventario o None si no existe
        """
        pass

    @abstractmethod
    async def get_by_local_origen(
        self,
        local_origen_id: UUID,
        estado: Optional[EstadoTransferencia] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias desde un local origen.

        Args:
            local_origen_id: ID del local origen
            estado: Filtro opcional por estado
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar

        Returns:
            Lista de transferencias desde el local
        """
        pass

    @abstractmethod
    async def get_by_local_destino(
        self,
        local_destino_id: UUID,
        estado: Optional[EstadoTransferencia] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias hacia un local destino.

        Args:
            local_destino_id: ID del local destino
            estado: Filtro opcional por estado
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar

        Returns:
            Lista de transferencias hacia el local
        """
        pass

    @abstractmethod
    async def get_by_producto(
        self,
        producto_id: UUID,
        tienda_id: UUID,
        estado: Optional[EstadoTransferencia] = None
    ) -> List[TransferenciaInventario]:
        """
        Obtiene transferencias de un producto específico en una tienda.

        Args:
            producto_id: ID del producto
            tienda_id: ID de la tienda
            estado: Filtro opcional por estado

        Returns:
            Lista de transferencias del producto
        """
        pass

    @abstractmethod
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

        Args:
            tienda_id: ID de la tienda
            estado: Filtro opcional por estado
            fecha_desde: Fecha inicio del rango
            fecha_hasta: Fecha fin del rango
            skip: Número de registros a omitir
            limit: Número máximo de registros a retornar

        Returns:
            Lista de transferencias de la tienda
        """
        pass

    @abstractmethod
    async def marcar_como_enviado(
        self,
        transferencia_id: UUID,
        cantidad_enviada: int,
        usuario_envia_id: UUID,
        observaciones: Optional[str] = None
    ) -> Optional[TransferenciaInventario]:
        """
        Marca una transferencia como enviada y actualiza stock del local origen.

        Args:
            transferencia_id: ID de la transferencia
            cantidad_enviada: Cantidad efectivamente enviada
            usuario_envia_id: ID del usuario que envía
            observaciones: Observaciones del envío

        Returns:
            TransferenciaInventario actualizada o None si no existe

        Raises:
            EstadoInvalidoError: Si la transferencia no está en estado PENDIENTE
            StockInsuficienteError: Si no hay stock suficiente para envío
        """
        pass

    @abstractmethod
    async def marcar_como_recibido(
        self,
        transferencia_id: UUID,
        cantidad_recibida: int,
        usuario_recibe_id: UUID,
        observaciones: Optional[str] = None
    ) -> Optional[TransferenciaInventario]:
        """
        Marca una transferencia como recibida y actualiza stock del local destino.

        Args:
            transferencia_id: ID de la transferencia
            cantidad_recibida: Cantidad efectivamente recibida
            usuario_recibe_id: ID del usuario que recibe
            observaciones: Observaciones de la recepción

        Returns:
            TransferenciaInventario actualizada o None si no existe

        Raises:
            EstadoInvalidoError: Si la transferencia no está en estado ENVIADO
        """
        pass

    @abstractmethod
    async def cancelar_transferencia(
        self,
        transferencia_id: UUID,
        usuario_id: UUID,
        motivo_cancelacion: str
    ) -> Optional[TransferenciaInventario]:
        """
        Cancela una transferencia y revierte stock si es necesario.

        Args:
            transferencia_id: ID de la transferencia
            usuario_id: ID del usuario que cancela
            motivo_cancelacion: Motivo de la cancelación

        Returns:
            TransferenciaInventario cancelada o None si no existe

        Raises:
            EstadoInvalidoError: Si la transferencia ya fue recibida
        """
        pass

    @abstractmethod
    async def get_transferencias_pendientes(self, tienda_id: UUID) -> List[TransferenciaInventario]:
        """
        Obtiene todas las transferencias pendientes de una tienda.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Lista de transferencias pendientes
        """
        pass

    @abstractmethod
    async def get_transferencias_en_transito(self, tienda_id: UUID) -> List[TransferenciaInventario]:
        """
        Obtiene todas las transferencias enviadas pero no recibidas.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Lista de transferencias en tránsito
        """
        pass

    @abstractmethod
    async def get_estadisticas_transferencias(
        self,
        tienda_id: UUID,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de transferencias de una tienda.

        Args:
            tienda_id: ID de la tienda
            fecha_desde: Fecha inicio del período
            fecha_hasta: Fecha fin del período

        Returns:
            Diccionario con estadísticas:
            - total_transferencias: Total de transferencias
            - transferencias_por_estado: Conteo por estado
            - transferencias_por_local: Conteo por local origen/destino
            - productos_mas_transferidos: Top productos transferidos
            - tiempo_promedio_procesamiento: Tiempo promedio por transferencia
        """
        pass

    @abstractmethod
    async def generar_numero_transferencia(self, tienda_id: UUID) -> str:
        """
        Genera un número único para una nueva transferencia.

        Args:
            tienda_id: ID de la tienda

        Returns:
            Número de transferencia único (ej: "TRANS-2024-001")
        """
        pass

    @abstractmethod
    async def get_historial_producto_local(
        self,
        producto_id: UUID,
        local_id: UUID
    ) -> List[TransferenciaInventario]:
        """
        Obtiene el historial de transferencias de un producto en un local.

        Args:
            producto_id: ID del producto
            local_id: ID del local

        Returns:
            Lista de transferencias del producto (enviadas y recibidas)
        """
        pass

    @abstractmethod
    async def validar_transferencia_posible(
        self,
        producto_id: UUID,
        local_origen_id: UUID,
        local_destino_id: UUID,
        cantidad: int
    ) -> Dict[str, Any]:
        """
        Valida si una transferencia es posible.

        Args:
            producto_id: ID del producto
            local_origen_id: ID del local origen
            local_destino_id: ID del local destino
            cantidad: Cantidad a transferir

        Returns:
            Diccionario con validación:
            - es_valida: bool
            - motivos: lista de motivos si no es válida
            - stock_disponible: stock actual en origen
        """
        pass