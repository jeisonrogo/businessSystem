"""
Pruebas unitarias para los modelos de dominio de contabilidad.
Valida los esquemas Pydantic y las reglas de negocio básicas.
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from pydantic import ValidationError

from app.domain.models.contabilidad import (
    TipoCuenta,
    TipoMovimiento,
    CuentaContableCreate,
    AsientoContableCreate,
    DetalleAsientoCreate,
    CodigosCuentasEstandar,
)


class TestCuentaContableValidation:
    """Pruebas de validación para cuenta contable."""
    
    def test_cuenta_contable_create_valid(self):
        """Debe crear una cuenta contable válida."""
        cuenta_data = CuentaContableCreate(
            codigo="1105",
            nombre="Efectivo y Equivalentes",
            tipo_cuenta=TipoCuenta.ACTIVO
        )
        
        assert cuenta_data.codigo == "1105"
        assert cuenta_data.nombre == "Efectivo y Equivalentes"
        assert cuenta_data.tipo_cuenta == TipoCuenta.ACTIVO
        assert cuenta_data.cuenta_padre_id is None
    
    def test_codigo_debe_ser_numerico(self):
        """Debe validar que el código sea numérico."""
        with pytest.raises(ValidationError) as exc_info:
            CuentaContableCreate(
                codigo="ABC123",
                nombre="Cuenta Test",
                tipo_cuenta=TipoCuenta.ACTIVO
            )
        
        assert "debe ser numérico" in str(exc_info.value)
    
    def test_codigo_longitud_valida(self):
        """Debe validar la longitud del código."""
        # Muy corto
        with pytest.raises(ValidationError):
            CuentaContableCreate(
                codigo="1",
                nombre="Cuenta Test",
                tipo_cuenta=TipoCuenta.ACTIVO
            )
        
        # Muy largo
        with pytest.raises(ValidationError):
            CuentaContableCreate(
                codigo="123456789",
                nombre="Cuenta Test",
                tipo_cuenta=TipoCuenta.ACTIVO
            )


class TestAsientoContableValidation:
    """Pruebas de validación para asiento contable."""
    
    def test_asiento_balanceado_valido(self):
        """Debe crear un asiento balanceado correctamente."""
        cuenta_caja = uuid4()
        cuenta_ventas = uuid4()
        
        detalles = [
            DetalleAsientoCreate(
                cuenta_id=cuenta_caja,
                tipo_movimiento=TipoMovimiento.DEBITO,
                monto=Decimal("100.00"),
                descripcion="Ingreso por venta"
            ),
            DetalleAsientoCreate(
                cuenta_id=cuenta_ventas,
                tipo_movimiento=TipoMovimiento.CREDITO,
                monto=Decimal("100.00"),
                descripcion="Venta de producto"
            )
        ]
        
        asiento = AsientoContableCreate(
            fecha=datetime.now(UTC),
            descripcion="Venta de producto Test-001",
            detalles=detalles
        )
        
        assert len(asiento.detalles) == 2
        assert asiento.descripcion == "Venta de producto Test-001"
    
    def test_asiento_desbalanceado_falla(self):
        """Debe fallar si el asiento no está balanceado."""
        cuenta_caja = uuid4()
        cuenta_ventas = uuid4()
        
        detalles = [
            DetalleAsientoCreate(
                cuenta_id=cuenta_caja,
                tipo_movimiento=TipoMovimiento.DEBITO,
                monto=Decimal("100.00")
            ),
            DetalleAsientoCreate(
                cuenta_id=cuenta_ventas,
                tipo_movimiento=TipoMovimiento.CREDITO,
                monto=Decimal("90.00")  # Desbalanceado
            )
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            AsientoContableCreate(
                fecha=datetime.now(UTC),
                descripcion="Asiento desbalanceado",
                detalles=detalles
            )
        
        assert "no está balanceado" in str(exc_info.value)
    
    def test_asiento_minimo_dos_detalles(self):
        """Debe requerir al menos 2 detalles."""
        cuenta_caja = uuid4()
        
        detalles = [
            DetalleAsientoCreate(
                cuenta_id=cuenta_caja,
                tipo_movimiento=TipoMovimiento.DEBITO,
                monto=Decimal("100.00")
            )
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            AsientoContableCreate(
                fecha=datetime.now(UTC),
                descripcion="Un solo detalle",
                detalles=detalles
            )
        
        assert "at least 2 items" in str(exc_info.value)


class TestDetalleAsientoValidation:
    """Pruebas de validación para detalle de asiento."""
    
    def test_detalle_asiento_valido(self):
        """Debe crear un detalle de asiento válido."""
        cuenta_id = uuid4()
        
        detalle = DetalleAsientoCreate(
            cuenta_id=cuenta_id,
            tipo_movimiento=TipoMovimiento.DEBITO,
            monto=Decimal("150.75"),
            descripcion="Compra de inventario"
        )
        
        assert detalle.cuenta_id == cuenta_id
        assert detalle.tipo_movimiento == TipoMovimiento.DEBITO
        assert detalle.monto == Decimal("150.75")
        assert detalle.descripcion == "Compra de inventario"
    
    def test_monto_debe_ser_positivo(self):
        """Debe validar que el monto sea positivo."""
        cuenta_id = uuid4()
        
        with pytest.raises(ValidationError) as exc_info:
            DetalleAsientoCreate(
                cuenta_id=cuenta_id,
                tipo_movimiento=TipoMovimiento.DEBITO,
                monto=Decimal("-10.00")
            )
        
        # Pydantic genera este mensaje para gt validation
        assert "greater than 0" in str(exc_info.value)


class TestCodigosCuentasEstandar:
    """Pruebas de constantes de códigos de cuentas."""
    
    def test_codigos_principales_definidos(self):
        """Debe tener definidos los códigos principales."""
        assert CodigosCuentasEstandar.ACTIVO == "1"
        assert CodigosCuentasEstandar.PASIVO == "2"
        assert CodigosCuentasEstandar.PATRIMONIO == "3"
        assert CodigosCuentasEstandar.INGRESOS == "4"
        assert CodigosCuentasEstandar.EGRESOS == "5"
    
    def test_codigos_detallados_definidos(self):
        """Debe tener definidos códigos específicos importantes."""
        assert CodigosCuentasEstandar.EFECTIVO_Y_EQUIVALENTES == "1105"
        assert CodigosCuentasEstandar.CAJA == "110505"
        assert CodigosCuentasEstandar.INVENTARIOS == "1435"
        assert CodigosCuentasEstandar.VENTAS == "4135"
        assert CodigosCuentasEstandar.COSTO_VENTAS == "6135"


class TestTiposEnum:
    """Pruebas de los tipos enumerados."""
    
    def test_tipo_cuenta_valores(self):
        """Debe tener todos los tipos de cuenta definidos."""
        tipos = [TipoCuenta.ACTIVO, TipoCuenta.PASIVO, TipoCuenta.PATRIMONIO, 
                TipoCuenta.INGRESO, TipoCuenta.EGRESO]
        
        assert len(tipos) == 5
        assert TipoCuenta.ACTIVO.value == "ACTIVO"
    
    def test_tipo_movimiento_valores(self):
        """Debe tener los tipos de movimiento definidos."""
        assert TipoMovimiento.DEBITO.value == "DEBITO"
        assert TipoMovimiento.CREDITO.value == "CREDITO"