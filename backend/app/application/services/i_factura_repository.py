"""
Interfaz del repositorio de facturas.

Define el contrato abstracto para el acceso a datos de facturas,
incluyendo operaciones especializadas para facturación y reportes.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from app.domain.models.facturacion import (
    Factura,
    FacturaCreate,
    FacturaUpdate,
    DetalleFactura,
    EstadoFactura,
    TipoFactura
)


class IFacturaRepository(ABC):
    """
    Interfaz abstracta para el repositorio de facturas.
    
    Define todas las operaciones de acceso a datos para la entidad Factura
    y sus detalles asociados.
    """

    @abstractmethod
    async def create(self, factura_data: FacturaCreate, created_by: Optional[UUID] = None) -> Factura:
        """
        Crear una nueva factura con sus detalles.
        
        Args:
            factura_data: Datos de la factura a crear
            created_by: UUID del usuario que crea la factura
            
        Returns:
            Factura: La factura creada con ID generado y detalles
            
        Raises:
            ValueError: Si hay problemas de validación
            StockInsuficienteError: Si no hay suficiente stock para algún producto
        """
        pass

    @abstractmethod
    async def get_by_id(self, factura_id: UUID) -> Optional[Factura]:
        """
        Obtener una factura por su ID con detalles cargados.
        
        Args:
            factura_id: UUID de la factura
            
        Returns:
            Optional[Factura]: La factura si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_by_numero(self, numero_factura: str) -> Optional[Factura]:
        """
        Obtener una factura por su número.
        
        Args:
            numero_factura: Número de la factura
            
        Returns:
            Optional[Factura]: La factura si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        cliente_id: Optional[UUID] = None,
        estado: Optional[EstadoFactura] = None,
        tipo_factura: Optional[TipoFactura] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        search: Optional[str] = None
    ) -> List[Factura]:
        """
        Obtener lista paginada de facturas con filtros opcionales.
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros
            cliente_id: Filtrar por cliente específico
            estado: Filtrar por estado de factura
            tipo_factura: Filtrar por tipo de factura
            fecha_desde: Filtrar facturas desde esta fecha
            fecha_hasta: Filtrar facturas hasta esta fecha
            search: Término de búsqueda en número, cliente
            
        Returns:
            List[Factura]: Lista de facturas que cumplen los criterios
        """
        pass

    @abstractmethod
    async def update(self, factura_id: UUID, factura_data: FacturaUpdate) -> Optional[Factura]:
        """
        Actualizar una factura existente.
        
        Args:
            factura_id: UUID de la factura a actualizar
            factura_data: Nuevos datos de la factura
            
        Returns:
            Optional[Factura]: La factura actualizada si existe, None en caso contrario
        """
        pass

    @abstractmethod
    async def delete(self, factura_id: UUID) -> bool:
        """
        Anular una factura.
        
        Cambia el estado a ANULADA y revierte el stock de los productos.
        
        Args:
            factura_id: UUID de la factura a anular
            
        Returns:
            bool: True si se anuló exitosamente, False si no existía
        """
        pass

    @abstractmethod
    async def count_total(
        self,
        cliente_id: Optional[UUID] = None,
        estado: Optional[EstadoFactura] = None,
        tipo_factura: Optional[TipoFactura] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Contar el número total de facturas que cumplen los criterios.
        
        Args:
            cliente_id: Filtrar por cliente específico
            estado: Filtrar por estado
            tipo_factura: Filtrar por tipo
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha
            search: Término de búsqueda
            
        Returns:
            int: Número total de facturas
        """
        pass

    @abstractmethod
    async def generar_numero_consecutivo(self, prefijo: str = "FV") -> str:
        """
        Generar el siguiente número consecutivo de factura.
        
        Args:
            prefijo: Prefijo de la factura
            
        Returns:
            str: Número de factura consecutivo (ej: FV-000001)
        """
        pass

    @abstractmethod
    async def get_facturas_vencidas(
        self,
        fecha_corte: Optional[date] = None
    ) -> List[Factura]:
        """
        Obtener facturas vencidas que no han sido pagadas.
        
        Args:
            fecha_corte: Fecha de corte para determinar vencimiento (default: hoy)
            
        Returns:
            List[Factura]: Lista de facturas vencidas
        """
        pass

    @abstractmethod
    async def get_facturas_por_cliente(
        self,
        cliente_id: UUID,
        skip: int = 0,
        limit: int = 50,
        estado: Optional[EstadoFactura] = None
    ) -> List[Factura]:
        """
        Obtener facturas de un cliente específico.
        
        Args:
            cliente_id: UUID del cliente
            skip: Registros a saltar
            limit: Límite de registros
            estado: Filtrar por estado específico
            
        Returns:
            List[Factura]: Lista de facturas del cliente
        """
        pass

    @abstractmethod
    async def get_resumen_ventas(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        cliente_id: Optional[UUID] = None
    ) -> dict:
        """
        Obtener resumen de ventas para un período.
        
        Args:
            fecha_desde: Fecha inicial del período
            fecha_hasta: Fecha final del período
            cliente_id: Cliente específico (opcional)
            
        Returns:
            dict: Resumen con totales, promedios, estadísticas
        """
        pass

    @abstractmethod
    async def get_productos_mas_vendidos(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtener los productos más vendidos en un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            limit: Número máximo de productos
            
        Returns:
            List[dict]: Lista de productos con cantidades vendidas
        """
        pass

    @abstractmethod
    async def get_clientes_top(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtener los clientes con más compras/facturación en un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            limit: Número máximo de clientes
            
        Returns:
            List[dict]: Lista de clientes con totales de compra
        """
        pass

    @abstractmethod
    async def cambiar_estado_factura(
        self,
        factura_id: UUID,
        nuevo_estado: EstadoFactura
    ) -> bool:
        """
        Cambiar el estado de una factura.
        
        Args:
            factura_id: UUID de la factura
            nuevo_estado: Nuevo estado a asignar
            
        Returns:
            bool: True si se cambió exitosamente, False si no existía
        """
        pass

    @abstractmethod
    async def marcar_como_pagada(
        self,
        factura_id: UUID,
        fecha_pago: Optional[datetime] = None
    ) -> bool:
        """
        Marcar una factura como pagada.
        
        Args:
            factura_id: UUID de la factura
            fecha_pago: Fecha del pago (default: now)
            
        Returns:
            bool: True si se marcó como pagada, False si no existía
        """
        pass

    @abstractmethod
    async def get_valor_cartera(
        self,
        cliente_id: Optional[UUID] = None,
        solo_vencida: bool = False
    ) -> dict:
        """
        Calcular el valor de la cartera (facturas pendientes de pago).
        
        Args:
            cliente_id: Cliente específico (opcional)
            solo_vencida: Si solo incluir cartera vencida
            
        Returns:
            dict: Valor total, cantidad de facturas, promedio
        """
        pass

    @abstractmethod
    async def get_estadisticas_facturacion(
        self,
        fecha_desde: date,
        fecha_hasta: date
    ) -> dict:
        """
        Obtener estadísticas completas de facturación para un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            
        Returns:
            dict: Estadísticas completas (totales, promedios, distribuciones)
        """
        pass

    @abstractmethod
    async def existe_numero_factura(self, numero_factura: str) -> bool:
        """
        Verificar si existe una factura con el número dado.
        
        Args:
            numero_factura: Número de factura a verificar
            
        Returns:
            bool: True si existe, False en caso contrario
        """
        pass

    @abstractmethod
    async def get_siguiente_consecutivo(self, prefijo: str = "FV") -> int:
        """
        Obtener el siguiente número consecutivo disponible.
        
        Args:
            prefijo: Prefijo de la factura
            
        Returns:
            int: Siguiente número consecutivo
        """
        pass