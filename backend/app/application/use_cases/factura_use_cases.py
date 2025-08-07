"""
Casos de uso para la gestión de facturas.

Implementa la lógica de negocio para facturación, incluyendo validaciones,
integración con inventario y generación de asientos contables automáticos.
"""

from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from app.application.services.i_factura_repository import IFacturaRepository
from app.application.services.i_cliente_repository import IClienteRepository
from app.application.services.i_product_repository import IProductRepository
from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.application.services.i_asiento_contable_repository import IAsientoContableRepository
from app.application.services.integracion_contable_service import IntegracionContableService
from app.domain.models.facturacion import (
    Factura,
    FacturaCreate,
    FacturaUpdate,
    EstadoFactura,
    TipoFactura
)


# Excepciones personalizadas

class FacturaError(Exception):
    """Excepción base para errores de factura."""
    pass


class FacturaNotFoundError(FacturaError):
    """Error cuando no se encuentra una factura."""
    pass


class ClienteNotFoundForFacturaError(FacturaError):
    """Error cuando el cliente de la factura no existe."""
    pass


class ProductoNotFoundForFacturaError(FacturaError):
    """Error cuando un producto de la factura no existe."""
    pass


class StockInsuficienteError(FacturaError):
    """Error cuando no hay suficiente stock para la venta."""
    pass


class FacturaStateError(FacturaError):
    """Error por estado inválido de la factura."""
    pass


class InvalidFacturaDataError(FacturaError):
    """Error por datos inválidos en la factura."""
    pass


# Casos de uso

class CreateFacturaUseCase:
    """Caso de uso para crear una nueva factura."""
    
    def __init__(
        self,
        factura_repository: IFacturaRepository,
        cliente_repository: IClienteRepository,
        product_repository: IProductRepository,
        cuenta_repository: Optional[ICuentaContableRepository] = None,
        asiento_repository: Optional[IAsientoContableRepository] = None
    ):
        self.factura_repository = factura_repository
        self.cliente_repository = cliente_repository
        self.product_repository = product_repository
        
        # Servicio de integración contable (opcional)
        if cuenta_repository and asiento_repository:
            self.integracion_contable = IntegracionContableService(
                cuenta_repository, asiento_repository
            )
        else:
            self.integracion_contable = None
    
    async def execute(self, factura_data: FacturaCreate, created_by: Optional[UUID] = None) -> Factura:
        """
        Crear una nueva factura con validaciones completas.
        
        Args:
            factura_data: Datos de la factura a crear
            created_by: UUID del usuario que crea la factura
            
        Returns:
            Factura: La factura creada con detalles
            
        Raises:
            ClienteNotFoundForFacturaError: Si el cliente no existe
            ProductoNotFoundForFacturaError: Si algún producto no existe
            StockInsuficienteError: Si no hay suficiente stock
            InvalidFacturaDataError: Si los datos son inválidos
        """
        try:
            # Validar que el cliente existe
            cliente = await self.cliente_repository.get_by_id(factura_data.cliente_id)
            if not cliente:
                raise ClienteNotFoundForFacturaError(
                    f"Cliente con ID {factura_data.cliente_id} no encontrado"
                )
            
            if not cliente.is_active:
                raise ClienteNotFoundForFacturaError(
                    f"Cliente {cliente.nombre_completo} está inactivo"
                )
            
            # Validar productos y stock
            for detalle in factura_data.detalles:
                producto = await self.product_repository.get_by_id(detalle.producto_id)
                if not producto:
                    raise ProductoNotFoundForFacturaError(
                        f"Producto con ID {detalle.producto_id} no encontrado"
                    )
                
                if not producto.is_active:
                    raise ProductoNotFoundForFacturaError(
                        f"Producto {producto.nombre} está inactivo"
                    )
                
                if producto.stock < detalle.cantidad:
                    raise StockInsuficienteError(
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Disponible: {producto.stock}, Solicitado: {detalle.cantidad}"
                    )
            
            # Crear la factura
            factura = await self.factura_repository.create(factura_data, created_by)
            
            # Generar asiento contable automático si está configurado
            if self.integracion_contable:
                try:
                    asiento_id = await self.integracion_contable.generar_asiento_emision_factura(
                        factura, created_by
                    )
                    # TODO: Vincular asiento con factura si se implementa relación
                except Exception as e:
                    # Log del error pero no fallar la creación de la factura
                    print(f"Error al generar asiento contable: {str(e)}")
            
            return factura
        
        except (ClienteNotFoundForFacturaError, ProductoNotFoundForFacturaError, 
                StockInsuficienteError, InvalidFacturaDataError):
            raise
        except Exception as e:
            raise FacturaError(f"Error al crear la factura: {str(e)}")


class GetFacturaUseCase:
    """Caso de uso para obtener una factura por ID."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(self, factura_id: UUID) -> Factura:
        """
        Obtener una factura por ID.
        
        Args:
            factura_id: UUID de la factura
            
        Returns:
            Factura: La factura encontrada
            
        Raises:
            FacturaNotFoundError: Si no se encuentra la factura
        """
        factura = await self.factura_repository.get_by_id(factura_id)
        if not factura:
            raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
        
        return factura


class GetFacturaByNumeroUseCase:
    """Caso de uso para obtener una factura por número."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(self, numero_factura: str) -> Factura:
        """
        Obtener una factura por número.
        
        Args:
            numero_factura: Número de la factura
            
        Returns:
            Factura: La factura encontrada
            
        Raises:
            FacturaNotFoundError: Si no se encuentra la factura
        """
        factura = await self.factura_repository.get_by_numero(numero_factura)
        if not factura:
            raise FacturaNotFoundError(f"Factura número {numero_factura} no encontrada")
        
        return factura


class ListFacturasUseCase:
    """Caso de uso para listar facturas con paginación y filtros."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        page: int = 1,
        limit: int = 50,
        cliente_id: Optional[UUID] = None,
        estado: Optional[EstadoFactura] = None,
        tipo_factura: Optional[TipoFactura] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        search: Optional[str] = None
    ) -> dict:
        """
        Listar facturas con paginación y filtros.
        
        Args:
            page: Número de página (1-indexed)
            limit: Número de registros por página
            cliente_id: Filtrar por cliente
            estado: Filtrar por estado
            tipo_factura: Filtrar por tipo
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha
            search: Término de búsqueda
            
        Returns:
            dict: Lista de facturas con metadatos de paginación
        """
        # Validar parámetros
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50
        
        skip = (page - 1) * limit
        
        # Obtener facturas y total
        facturas = await self.factura_repository.get_all(
            skip=skip,
            limit=limit,
            cliente_id=cliente_id,
            estado=estado,
            tipo_factura=tipo_factura,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            search=search
        )
        
        total = await self.factura_repository.count_total(
            cliente_id=cliente_id,
            estado=estado,
            tipo_factura=tipo_factura,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            search=search
        )
        
        # Calcular metadatos
        has_next = skip + limit < total
        has_prev = page > 1
        
        return {
            "facturas": facturas,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }


class UpdateFacturaUseCase:
    """Caso de uso para actualizar una factura."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(self, factura_id: UUID, factura_data: FacturaUpdate) -> Factura:
        """
        Actualizar una factura existente.
        
        Args:
            factura_id: UUID de la factura a actualizar
            factura_data: Nuevos datos de la factura
            
        Returns:
            Factura: La factura actualizada
            
        Raises:
            FacturaNotFoundError: Si no se encuentra la factura
            FacturaStateError: Si el estado no permite modificaciones
        """
        try:
            # Verificar que existe la factura
            existing_factura = await self.factura_repository.get_by_id(factura_id)
            if not existing_factura:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            # Actualizar la factura
            updated_factura = await self.factura_repository.update(factura_id, factura_data)
            if not updated_factura:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            return updated_factura
        
        except FacturaNotFoundError:
            raise
        except ValueError as e:
            if "estado" in str(e).lower():
                raise FacturaStateError(str(e))
            raise FacturaError(f"Error al actualizar la factura: {str(e)}")
        except Exception as e:
            raise FacturaError(f"Error al actualizar la factura: {str(e)}")


class AnularFacturaUseCase:
    """Caso de uso para anular una factura."""
    
    def __init__(
        self,
        factura_repository: IFacturaRepository,
        cuenta_repository: Optional[ICuentaContableRepository] = None,
        asiento_repository: Optional[IAsientoContableRepository] = None
    ):
        self.factura_repository = factura_repository
        
        # Servicio de integración contable (opcional)
        if cuenta_repository and asiento_repository:
            self.integracion_contable = IntegracionContableService(
                cuenta_repository, asiento_repository
            )
        else:
            self.integracion_contable = None
    
    async def execute(
        self, 
        factura_id: UUID,
        motivo_anulacion: str = "Anulación de factura",
        created_by: Optional[UUID] = None
    ) -> bool:
        """
        Anular una factura y revertir el stock.
        
        Args:
            factura_id: UUID de la factura a anular
            
        Returns:
            bool: True si se anuló exitosamente
            
        Raises:
            FacturaNotFoundError: Si no se encuentra la factura
            FacturaStateError: Si la factura ya está anulada
        """
        try:
            # Verificar que existe la factura
            factura = await self.factura_repository.get_by_id(factura_id)
            if not factura:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            if factura.estado == EstadoFactura.ANULADA:
                raise FacturaStateError("La factura ya está anulada")
            
            # Anular la factura
            success = await self.factura_repository.delete(factura_id)
            if not success:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            # Generar asiento contable automático si está configurado
            if self.integracion_contable:
                try:
                    asiento_id = await self.integracion_contable.generar_asiento_anulacion_factura(
                        factura, motivo_anulacion, created_by
                    )
                    # TODO: Vincular asiento con factura si se implementa relación
                except Exception as e:
                    # Log del error pero no revertir la anulación
                    print(f"Error al generar asiento contable de anulación: {str(e)}")
            
            return True
        
        except (FacturaNotFoundError, FacturaStateError):
            raise
        except Exception as e:
            raise FacturaError(f"Error al anular la factura: {str(e)}")


class MarcarFacturaPagadaUseCase:
    """Caso de uso para marcar una factura como pagada."""
    
    def __init__(
        self,
        factura_repository: IFacturaRepository,
        cuenta_repository: Optional[ICuentaContableRepository] = None,
        asiento_repository: Optional[IAsientoContableRepository] = None
    ):
        self.factura_repository = factura_repository
        
        # Servicio de integración contable (opcional)
        if cuenta_repository and asiento_repository:
            self.integracion_contable = IntegracionContableService(
                cuenta_repository, asiento_repository
            )
        else:
            self.integracion_contable = None
    
    async def execute(
        self, 
        factura_id: UUID, 
        fecha_pago: Optional[datetime] = None,
        forma_pago: str = "EFECTIVO",
        created_by: Optional[UUID] = None
    ) -> bool:
        """
        Marcar una factura como pagada.
        
        Args:
            factura_id: UUID de la factura
            fecha_pago: Fecha del pago (opcional)
            
        Returns:
            bool: True si se marcó como pagada
            
        Raises:
            FacturaNotFoundError: Si no se encuentra la factura
            FacturaStateError: Si el estado no permite el cambio
        """
        try:
            # Verificar que existe la factura
            factura = await self.factura_repository.get_by_id(factura_id)
            if not factura:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            if factura.estado == EstadoFactura.ANULADA:
                raise FacturaStateError("No se puede marcar como pagada una factura anulada")
            
            if factura.estado == EstadoFactura.PAGADA:
                raise FacturaStateError("La factura ya está marcada como pagada")
            
            # Marcar como pagada
            success = await self.factura_repository.marcar_como_pagada(factura_id, fecha_pago)
            if not success:
                raise FacturaNotFoundError(f"Factura con ID {factura_id} no encontrada")
            
            # Generar asiento contable automático si está configurado
            if self.integracion_contable:
                try:
                    asiento_id = await self.integracion_contable.generar_asiento_pago_factura(
                        factura, forma_pago, created_by
                    )
                    # TODO: Vincular asiento con factura si se implementa relación
                except Exception as e:
                    # Log del error pero no revertir el pago
                    print(f"Error al generar asiento contable de pago: {str(e)}")
            
            return True
        
        except (FacturaNotFoundError, FacturaStateError):
            raise
        except Exception as e:
            raise FacturaError(f"Error al marcar la factura como pagada: {str(e)}")


class GetFacturasVencidasUseCase:
    """Caso de uso para obtener facturas vencidas."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(self, fecha_corte: Optional[date] = None) -> List[Factura]:
        """
        Obtener facturas vencidas.
        
        Args:
            fecha_corte: Fecha de corte para determinar vencimiento
            
        Returns:
            List[Factura]: Lista de facturas vencidas
        """
        return await self.factura_repository.get_facturas_vencidas(fecha_corte)


class GetFacturasPorClienteUseCase:
    """Caso de uso para obtener facturas de un cliente."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        cliente_id: UUID,
        page: int = 1,
        limit: int = 50,
        estado: Optional[EstadoFactura] = None
    ) -> dict:
        """
        Obtener facturas de un cliente.
        
        Args:
            cliente_id: UUID del cliente
            page: Número de página
            limit: Límite de registros
            estado: Filtrar por estado
            
        Returns:
            dict: Facturas con metadatos de paginación
        """
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 50
        
        skip = (page - 1) * limit
        
        facturas = await self.factura_repository.get_facturas_por_cliente(
            cliente_id, skip, limit, estado
        )
        
        # Para el total, usar la función de conteo general con filtro de cliente
        total = await self.factura_repository.count_total(
            cliente_id=cliente_id,
            estado=estado
        )
        
        has_next = skip + limit < total
        has_prev = page > 1
        
        return {
            "facturas": facturas,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }


class GetResumenVentasUseCase:
    """Caso de uso para obtener resumen de ventas."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        cliente_id: Optional[UUID] = None
    ) -> dict:
        """
        Obtener resumen de ventas para un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            cliente_id: Cliente específico (opcional)
            
        Returns:
            dict: Resumen de ventas con estadísticas
        """
        if fecha_desde > fecha_hasta:
            raise InvalidFacturaDataError("La fecha inicial debe ser menor o igual a la final")
        
        return await self.factura_repository.get_resumen_ventas(
            fecha_desde, fecha_hasta, cliente_id
        )


class GetProductosMasVendidosUseCase:
    """Caso de uso para obtener productos más vendidos."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtener productos más vendidos en un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            limit: Número máximo de productos
            
        Returns:
            List[dict]: Lista de productos más vendidos
        """
        if fecha_desde > fecha_hasta:
            raise InvalidFacturaDataError("La fecha inicial debe ser menor o igual a la final")
        
        if limit < 1 or limit > 50:
            limit = 10
        
        return await self.factura_repository.get_productos_mas_vendidos(
            fecha_desde, fecha_hasta, limit
        )


class GetClientesTopUseCase:
    """Caso de uso para obtener clientes top."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        fecha_desde: date,
        fecha_hasta: date,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtener clientes top por compras en un período.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            limit: Número máximo de clientes
            
        Returns:
            List[dict]: Lista de clientes top
        """
        if fecha_desde > fecha_hasta:
            raise InvalidFacturaDataError("La fecha inicial debe ser menor o igual a la final")
        
        if limit < 1 or limit > 50:
            limit = 10
        
        return await self.factura_repository.get_clientes_top(
            fecha_desde, fecha_hasta, limit
        )


class GetValorCarteraUseCase:
    """Caso de uso para obtener valor de cartera."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(
        self,
        cliente_id: Optional[UUID] = None,
        solo_vencida: bool = False
    ) -> dict:
        """
        Obtener valor de cartera (facturas pendientes).
        
        Args:
            cliente_id: Cliente específico (opcional)
            solo_vencida: Si solo incluir cartera vencida
            
        Returns:
            dict: Valor de cartera con estadísticas
        """
        return await self.factura_repository.get_valor_cartera(cliente_id, solo_vencida)


class GetEstadisticasFacturacionUseCase:
    """Caso de uso para obtener estadísticas completas de facturación."""
    
    def __init__(self, factura_repository: IFacturaRepository):
        self.factura_repository = factura_repository
    
    async def execute(self, fecha_desde: date, fecha_hasta: date) -> dict:
        """
        Obtener estadísticas completas de facturación.
        
        Args:
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            
        Returns:
            dict: Estadísticas completas de facturación
        """
        if fecha_desde > fecha_hasta:
            raise InvalidFacturaDataError("La fecha inicial debe ser menor o igual a la final")
        
        return await self.factura_repository.get_estadisticas_facturacion(
            fecha_desde, fecha_hasta
        )