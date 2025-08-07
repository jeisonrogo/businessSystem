"""
Servicio de integración contable automática.

Maneja la creación automática de asientos contables cuando ocurren
eventos de facturación (emisión, pago, anulación).
"""

from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.application.services.i_cuenta_contable_repository import ICuentaContableRepository
from app.application.services.i_asiento_contable_repository import IAsientoContableRepository
from app.domain.models.contabilidad import (
    AsientoContableCreate,
    DetalleAsientoCreate,
    TipoMovimiento
)
from app.domain.models.facturacion import (
    Factura,
    EstadoFactura,
    TipoFactura
)


class IntegracionContableService:
    """
    Servicio para integración automática con el módulo contable.
    
    Genera asientos contables automáticamente basados en eventos
    de facturación siguiendo principios de contabilidad por partida doble.
    """
    
    def __init__(
        self,
        cuenta_repository: ICuentaContableRepository,
        asiento_repository: IAsientoContableRepository
    ):
        self.cuenta_repository = cuenta_repository
        self.asiento_repository = asiento_repository
    
    async def generar_asiento_emision_factura(
        self,
        factura: Factura,
        created_by: Optional[UUID] = None
    ) -> UUID:
        """
        Generar asiento contable por emisión de factura de venta.
        
        Movimiento: 
        - DÉBITO: Cuentas por Cobrar (Clientes)
        - CRÉDITO: Ingresos por Ventas
        - CRÉDITO: IVA por Pagar (si aplica)
        
        Args:
            factura: Factura emitida
            created_by: Usuario que crea el asiento
            
        Returns:
            UUID: ID del asiento contable creado
        """
        # Obtener cuentas contables necesarias
        cuenta_clientes = await self._obtener_cuenta_clientes()
        cuenta_ingresos_ventas = await self._obtener_cuenta_ingresos_ventas()
        cuenta_iva_por_pagar = await self._obtener_cuenta_iva_por_pagar()
        
        if not cuenta_clientes:
            raise ValueError("No se encontró la cuenta contable para clientes (13050500)")
        if not cuenta_ingresos_ventas:
            raise ValueError("No se encontró la cuenta contable para ingresos por ventas (41359500)")
        
        # Preparar detalles del asiento
        detalles = []
        
        # DÉBITO: Cuentas por cobrar (Clientes) - Valor total de la factura
        detalles.append(DetalleAsientoCreate(
            cuenta_id=cuenta_clientes.id,
            tipo_movimiento=TipoMovimiento.DEBITO,
            valor=factura.total_factura,
            descripcion=f"Factura de venta {factura.numero_factura} - {factura.cliente.nombre_completo}"
        ))
        
        # CRÉDITO: Ingresos por ventas - Subtotal sin impuestos
        valor_base = factura.subtotal - factura.total_descuento
        detalles.append(DetalleAsientoCreate(
            cuenta_id=cuenta_ingresos_ventas.id,
            tipo_movimiento=TipoMovimiento.CREDITO,
            valor=valor_base,
            descripcion=f"Venta registrada factura {factura.numero_factura}"
        ))
        
        # CRÉDITO: IVA por pagar (si hay impuestos)
        if factura.total_impuestos > 0 and cuenta_iva_por_pagar:
            detalles.append(DetalleAsientoCreate(
                cuenta_id=cuenta_iva_por_pagar.id,
                tipo_movimiento=TipoMovimiento.CREDITO,
                valor=factura.total_impuestos,
                descripcion=f"IVA factura {factura.numero_factura}"
            ))
        
        # Crear el asiento contable
        asiento_data = AsientoContableCreate(
            fecha_asiento=factura.fecha_emision,
            descripcion=f"Asiento automático - Emisión factura {factura.numero_factura}",
            concepto=f"Registro de venta a crédito - Cliente: {factura.cliente.nombre_completo}",
            tipo_asiento="AUTOMATICO",
            numero_comprobante=factura.numero_factura,
            detalles=detalles
        )
        
        # Guardar el asiento
        asiento = await self.asiento_repository.create(asiento_data, created_by)
        return asiento.id
    
    async def generar_asiento_pago_factura(
        self,
        factura: Factura,
        forma_pago: str = "EFECTIVO",
        created_by: Optional[UUID] = None
    ) -> UUID:
        """
        Generar asiento contable por pago de factura.
        
        Movimiento:
        - DÉBITO: Caja/Bancos (según forma de pago)
        - CRÉDITO: Cuentas por Cobrar (Clientes)
        
        Args:
            factura: Factura pagada
            forma_pago: Forma de pago (EFECTIVO, TRANSFERENCIA, etc.)
            created_by: Usuario que crea el asiento
            
        Returns:
            UUID: ID del asiento contable creado
        """
        # Obtener cuentas contables
        cuenta_clientes = await self._obtener_cuenta_clientes()
        cuenta_caja = await self._obtener_cuenta_por_forma_pago(forma_pago)
        
        if not cuenta_clientes:
            raise ValueError("No se encontró la cuenta contable para clientes")
        if not cuenta_caja:
            raise ValueError(f"No se encontró cuenta contable para forma de pago: {forma_pago}")
        
        # Preparar detalles del asiento
        detalles = [
            # DÉBITO: Caja/Bancos
            DetalleAsientoCreate(
                cuenta_id=cuenta_caja.id,
                tipo_movimiento=TipoMovimiento.DEBITO,
                valor=factura.total_factura,
                descripcion=f"Pago recibido factura {factura.numero_factura} - {forma_pago}"
            ),
            # CRÉDITO: Cuentas por cobrar
            DetalleAsientoCreate(
                cuenta_id=cuenta_clientes.id,
                tipo_movimiento=TipoMovimiento.CREDITO,
                valor=factura.total_factura,
                descripcion=f"Cancelación factura {factura.numero_factura} - {factura.cliente.nombre_completo}"
            )
        ]
        
        # Crear el asiento contable
        asiento_data = AsientoContableCreate(
            fecha_asiento=date.today(),
            descripcion=f"Asiento automático - Pago factura {factura.numero_factura}",
            concepto=f"Pago recibido {forma_pago} - Cliente: {factura.cliente.nombre_completo}",
            tipo_asiento="AUTOMATICO",
            numero_comprobante=f"PAG-{factura.numero_factura}",
            detalles=detalles
        )
        
        # Guardar el asiento
        asiento = await self.asiento_repository.create(asiento_data, created_by)
        return asiento.id
    
    async def generar_asiento_anulacion_factura(
        self,
        factura: Factura,
        motivo_anulacion: str,
        created_by: Optional[UUID] = None
    ) -> UUID:
        """
        Generar asiento contable por anulación de factura.
        
        Movimiento (reversa del asiento de emisión):
        - CRÉDITO: Cuentas por Cobrar (Clientes)
        - DÉBITO: Ingresos por Ventas
        - DÉBITO: IVA por Pagar (si aplica)
        
        Args:
            factura: Factura anulada
            motivo_anulacion: Motivo de la anulación
            created_by: Usuario que crea el asiento
            
        Returns:
            UUID: ID del asiento contable creado
        """
        # Obtener cuentas contables necesarias
        cuenta_clientes = await self._obtener_cuenta_clientes()
        cuenta_ingresos_ventas = await self._obtener_cuenta_ingresos_ventas()
        cuenta_iva_por_pagar = await self._obtener_cuenta_iva_por_pagar()
        
        if not cuenta_clientes:
            raise ValueError("No se encontró la cuenta contable para clientes")
        if not cuenta_ingresos_ventas:
            raise ValueError("No se encontró la cuenta contable para ingresos por ventas")
        
        # Preparar detalles del asiento (movimientos contrarios a la emisión)
        detalles = []
        
        # CRÉDITO: Cuentas por cobrar (reversa del débito original)
        detalles.append(DetalleAsientoCreate(
            cuenta_id=cuenta_clientes.id,
            tipo_movimiento=TipoMovimiento.CREDITO,
            valor=factura.total_factura,
            descripcion=f"Anulación factura {factura.numero_factura} - {factura.cliente.nombre_completo}"
        ))
        
        # DÉBITO: Ingresos por ventas (reversa del crédito original)
        valor_base = factura.subtotal - factura.total_descuento
        detalles.append(DetalleAsientoCreate(
            cuenta_id=cuenta_ingresos_ventas.id,
            tipo_movimiento=TipoMovimiento.DEBITO,
            valor=valor_base,
            descripcion=f"Reversa venta factura {factura.numero_factura} - {motivo_anulacion}"
        ))
        
        # DÉBITO: IVA por pagar (reversa del crédito original)
        if factura.total_impuestos > 0 and cuenta_iva_por_pagar:
            detalles.append(DetalleAsientoCreate(
                cuenta_id=cuenta_iva_por_pagar.id,
                tipo_movimiento=TipoMovimiento.DEBITO,
                valor=factura.total_impuestos,
                descripcion=f"Reversa IVA factura {factura.numero_factura}"
            ))
        
        # Crear el asiento contable
        asiento_data = AsientoContableCreate(
            fecha_asiento=date.today(),
            descripcion=f"Asiento automático - Anulación factura {factura.numero_factura}",
            concepto=f"Anulación de venta - {motivo_anulacion} - Cliente: {factura.cliente.nombre_completo}",
            tipo_asiento="AUTOMATICO",
            numero_comprobante=f"ANU-{factura.numero_factura}",
            detalles=detalles
        )
        
        # Guardar el asiento
        asiento = await self.asiento_repository.create(asiento_data, created_by)
        return asiento.id
    
    # Métodos auxiliares privados
    
    async def _obtener_cuenta_clientes(self):
        """Obtener cuenta contable de clientes (13050500)."""
        return await self.cuenta_repository.get_by_codigo("13050500")
    
    async def _obtener_cuenta_ingresos_ventas(self):
        """Obtener cuenta contable de ingresos por ventas (41359500)."""
        return await self.cuenta_repository.get_by_codigo("41359500")
    
    async def _obtener_cuenta_iva_por_pagar(self):
        """Obtener cuenta contable de IVA por pagar (24080500)."""
        return await self.cuenta_repository.get_by_codigo("24080500")
    
    async def _obtener_cuenta_por_forma_pago(self, forma_pago: str):
        """
        Obtener cuenta contable según forma de pago.
        
        Args:
            forma_pago: EFECTIVO, TRANSFERENCIA, CHEQUE, etc.
            
        Returns:
            Cuenta contable correspondiente
        """
        codigos_cuentas = {
            "EFECTIVO": "11050500",      # Caja General
            "TRANSFERENCIA": "11100500", # Bancos Nacionales
            "CHEQUE": "11100500",        # Bancos Nacionales
            "TARJETA": "11100500",       # Bancos Nacionales
            "DATAFONO": "13050500"       # Cuentas por Cobrar (temporal)
        }
        
        codigo = codigos_cuentas.get(forma_pago.upper(), "11050500")  # Default: Caja
        return await self.cuenta_repository.get_by_codigo(codigo)
    
    async def validar_cuentas_configuradas(self) -> dict:
        """
        Validar que todas las cuentas necesarias estén configuradas.
        
        Returns:
            dict: Estado de configuración de cuentas
        """
        cuentas_requeridas = {
            "clientes": "13050500",
            "ingresos_ventas": "41359500", 
            "iva_por_pagar": "24080500",
            "caja_general": "11050500",
            "bancos": "11100500"
        }
        
        resultado = {
            "todas_configuradas": True,
            "cuentas_faltantes": [],
            "detalles": {}
        }
        
        for nombre, codigo in cuentas_requeridas.items():
            cuenta = await self.cuenta_repository.get_by_codigo(codigo)
            configurada = cuenta is not None
            
            resultado["detalles"][nombre] = {
                "codigo": codigo,
                "configurada": configurada,
                "nombre": cuenta.nombre if cuenta else None
            }
            
            if not configurada:
                resultado["todas_configuradas"] = False
                resultado["cuentas_faltantes"].append({
                    "nombre": nombre,
                    "codigo": codigo
                })
        
        return resultado