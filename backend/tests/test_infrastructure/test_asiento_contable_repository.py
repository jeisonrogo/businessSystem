"""
Pruebas de integración para SQLAsientoContableRepository.
Prueba todas las operaciones CRUD de asientos contables.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.contabilidad import (
    AsientoContable, 
    AsientoContableCreate,
    DetalleAsientoCreate,
    CuentaContable,
    CuentaContableCreate,
    TipoCuenta,
    TipoMovimiento
)
from app.domain.models.user import User  # Import User model for foreign key
from app.domain.models.product import Product  # Import Product model
from app.infrastructure.repositories.asiento_contable_repository import SQLAsientoContableRepository


@pytest.fixture
def engine():
    """Crear un motor de base de datos en memoria para las pruebas."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Crear una sesión de base de datos para las pruebas."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def asiento_repository(session):
    """Crear una instancia del repositorio de asientos contables."""
    return SQLAsientoContableRepository(session)


@pytest.fixture
def sample_cuentas(session):
    """Crear cuentas contables de muestra para las pruebas."""
    # Crear cuenta de efectivo (débito)
    cuenta_efectivo = CuentaContable(
        codigo="1105",
        nombre="EFECTIVO",
        tipo_cuenta=TipoCuenta.ACTIVO
    )
    session.add(cuenta_efectivo)
    
    # Crear cuenta de capital (crédito)
    cuenta_capital = CuentaContable(
        codigo="3115",
        nombre="CAPITAL SOCIAL",
        tipo_cuenta=TipoCuenta.PATRIMONIO
    )
    session.add(cuenta_capital)
    
    session.commit()
    session.refresh(cuenta_efectivo)
    session.refresh(cuenta_capital)
    
    return {
        "efectivo": cuenta_efectivo,
        "capital": cuenta_capital
    }


@pytest.fixture
def sample_asiento_data(sample_cuentas):
    """Datos de ejemplo para crear un asiento contable."""
    cuentas = sample_cuentas
    
    return AsientoContableCreate(
        fecha=date(2024, 1, 15),
        comprobante="AST-001",
        descripcion="Aporte inicial de capital en efectivo",
        detalles=[
            DetalleAsientoCreate(
                cuenta_id=cuentas["efectivo"].id,
                tipo_movimiento=TipoMovimiento.DEBITO,
                monto=Decimal("1000000"),
                descripcion="Efectivo recibido por aporte de capital"
            ),
            DetalleAsientoCreate(
                cuenta_id=cuentas["capital"].id,
                tipo_movimiento=TipoMovimiento.CREDITO,
                monto=Decimal("1000000"),
                descripcion="Capital social aportado"
            )
        ]
    )


class TestAsientoContableRepositoryCreate:
    """Pruebas de creación de asientos contables."""
    
    @pytest.mark.asyncio
    async def test_create_asiento_success(self, asiento_repository, sample_asiento_data):
        """Debe crear un asiento contable exitosamente."""
        asiento_data = sample_asiento_data
        asiento = await asiento_repository.create(asiento_data)
        
        assert asiento.comprobante == "AST-001"
        assert asiento.descripcion == "Aporte inicial de capital en efectivo"
        assert asiento.fecha.date() == date(2024, 1, 15)
        assert len(asiento.detalles) == 2
        assert asiento.id is not None
        
        # Verificar detalles
        debito = next(d for d in asiento.detalles if d.tipo_movimiento == TipoMovimiento.DEBITO)
        credito = next(d for d in asiento.detalles if d.tipo_movimiento == TipoMovimiento.CREDITO)
        
        assert debito.monto == Decimal("1000000")
        assert credito.monto == Decimal("1000000")
    
    @pytest.mark.asyncio
    async def test_create_asiento_duplicate_comprobante_fails(self, asiento_repository, sample_asiento_data):
        """Debe fallar al crear asiento con comprobante duplicado."""
        asiento_data = sample_asiento_data
        
        # Crear primer asiento
        await asiento_repository.create(asiento_data)
        
        # Intentar crear segundo con mismo comprobante
        with pytest.raises(ValueError, match="Ya existe un asiento con el comprobante"):
            await asiento_repository.create(asiento_data)


class TestAsientoContableRepositoryRead:
    """Pruebas de lectura de asientos contables."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, asiento_repository, sample_asiento_data):
        """Debe obtener un asiento por ID cuando existe."""
        asiento_data = sample_asiento_data
        created_asiento = await asiento_repository.create(asiento_data)
        
        found_asiento = await asiento_repository.get_by_id(created_asiento.id)
        
        assert found_asiento is not None
        assert found_asiento.id == created_asiento.id
        assert found_asiento.comprobante == "AST-001"
        assert len(found_asiento.detalles) == 2
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, asiento_repository):
        """Debe retornar None cuando el asiento no existe."""
        fake_id = uuid4()
        
        found_asiento = await asiento_repository.get_by_id(fake_id)
        
        assert found_asiento is None
    
    @pytest.mark.asyncio
    async def test_get_by_comprobante_exists(self, asiento_repository, sample_asiento_data):
        """Debe obtener un asiento por comprobante cuando existe."""
        asiento_data = sample_asiento_data
        await asiento_repository.create(asiento_data)
        
        found_asiento = await asiento_repository.get_by_comprobante("AST-001")
        
        assert found_asiento is not None
        assert found_asiento.comprobante == "AST-001"
        assert found_asiento.descripcion == "Aporte inicial de capital en efectivo"
    
    @pytest.mark.asyncio
    async def test_get_by_comprobante_not_exists(self, asiento_repository):
        """Debe retornar None cuando el comprobante no existe."""
        found_asiento = await asiento_repository.get_by_comprobante("NO-EXISTE")
        
        assert found_asiento is None


class TestAsientoContableRepositoryList:
    """Pruebas de listado de asientos contables."""
    
    @pytest.mark.asyncio
    async def test_get_all_empty(self, asiento_repository):
        """Debe retornar lista vacía cuando no hay asientos."""
        asientos = await asiento_repository.get_all()
        
        assert asientos == []
    
    @pytest.mark.asyncio
    async def test_get_all_with_data(self, asiento_repository, sample_asiento_data, sample_cuentas):
        """Debe retornar asientos cuando existen."""
        cuentas = sample_cuentas
        
        # Crear primer asiento
        asiento1_data = sample_asiento_data
        await asiento_repository.create(asiento1_data)
        
        # Crear segundo asiento
        asiento2_data = AsientoContableCreate(
            fecha=date(2024, 1, 16),
            comprobante="AST-002",
            descripcion="Segundo asiento de prueba",
            detalles=[
                DetalleAsientoCreate(
                    cuenta_id=cuentas["efectivo"].id,
                    tipo_movimiento=TipoMovimiento.CREDITO,
                    monto=Decimal("500000"),
                    descripcion="Salida de efectivo"
                ),
                DetalleAsientoCreate(
                    cuenta_id=cuentas["capital"].id,
                    tipo_movimiento=TipoMovimiento.DEBITO,
                    monto=Decimal("500000"),
                    descripcion="Reducción de capital"
                )
            ]
        )
        await asiento_repository.create(asiento2_data)
        
        asientos = await asiento_repository.get_all()
        
        assert len(asientos) == 2
        # Deben estar ordenados por fecha descendente
        assert asientos[0].comprobante == "AST-002"  # Más reciente primero
        assert asientos[1].comprobante == "AST-001"
    
    @pytest.mark.asyncio
    async def test_get_all_filter_by_fecha(self, asiento_repository, sample_asiento_data, sample_cuentas):
        """Debe filtrar asientos por rango de fechas."""
        cuentas = sample_cuentas
        
        # Crear asientos en diferentes fechas
        asiento1_data = sample_asiento_data  # fecha 2024-01-15
        await asiento_repository.create(asiento1_data)
        
        asiento2_data = AsientoContableCreate(
            fecha=date(2024, 2, 15),
            comprobante="AST-002",
            descripcion="Asiento de febrero",
            detalles=[
                DetalleAsientoCreate(
                    cuenta_id=cuentas["efectivo"].id,
                    tipo_movimiento=TipoMovimiento.DEBITO,
                    monto=Decimal("100000"),
                    descripcion="Entrada efectivo febrero"
                ),
                DetalleAsientoCreate(
                    cuenta_id=cuentas["capital"].id,
                    tipo_movimiento=TipoMovimiento.CREDITO,
                    monto=Decimal("100000"),
                    descripcion="Capital febrero"
                )
            ]
        )
        await asiento_repository.create(asiento2_data)
        
        # Filtrar solo enero
        asientos_enero = await asiento_repository.get_all(
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 31)
        )
        
        assert len(asientos_enero) == 1
        assert asientos_enero[0].comprobante == "AST-001"
    
    @pytest.mark.asyncio
    async def test_count_total(self, asiento_repository, sample_asiento_data):
        """Debe contar total de asientos correctamente."""
        count_inicial = await asiento_repository.count_total()
        assert count_inicial == 0
        
        asiento_data = sample_asiento_data
        await asiento_repository.create(asiento_data)
        
        count_despues = await asiento_repository.count_total()
        assert count_despues == 1


class TestAsientoContableRepositoryDelete:
    """Pruebas de eliminación de asientos contables."""
    
    @pytest.mark.asyncio
    async def test_delete_asiento_success(self, asiento_repository, sample_asiento_data):
        """Debe eliminar un asiento exitosamente."""
        asiento_data = sample_asiento_data
        asiento = await asiento_repository.create(asiento_data)
        
        success = await asiento_repository.delete(asiento.id)
        
        assert success is True
        
        # Verificar que no existe
        deleted_asiento = await asiento_repository.get_by_id(asiento.id)
        assert deleted_asiento is None
    
    @pytest.mark.asyncio
    async def test_delete_asiento_not_exists(self, asiento_repository):
        """Debe retornar False si el asiento no existe."""
        fake_id = uuid4()
        
        success = await asiento_repository.delete(fake_id)
        
        assert success is False


class TestAsientoContableRepositoryBalance:
    """Pruebas de funcionalidades de balance y consultas especiales."""
    
    @pytest.mark.asyncio
    async def test_get_balance_cuenta(self, asiento_repository, sample_asiento_data, sample_cuentas):
        """Debe calcular el balance de una cuenta correctamente."""
        cuentas = sample_cuentas
        asiento_data = sample_asiento_data
        await asiento_repository.create(asiento_data)
        
        # Balance de cuenta de efectivo (debe tener saldo débito de 1,000,000)
        balance_efectivo = await asiento_repository.get_balance_cuenta(cuentas["efectivo"].id)
        
        assert balance_efectivo["total_debitos"] == 1000000.0
        assert balance_efectivo["total_creditos"] == 0.0
        assert balance_efectivo["saldo"] == 1000000.0
        assert balance_efectivo["cantidad_movimientos"] == 1
        
        # Balance de cuenta de capital (debe tener saldo crédito de 1,000,000)
        balance_capital = await asiento_repository.get_balance_cuenta(cuentas["capital"].id)
        
        assert balance_capital["total_debitos"] == 0.0
        assert balance_capital["total_creditos"] == 1000000.0
        assert balance_capital["saldo"] == -1000000.0
        assert balance_capital["cantidad_movimientos"] == 1
    
    @pytest.mark.asyncio
    async def test_get_libro_diario(self, asiento_repository, sample_asiento_data, sample_cuentas):
        """Debe obtener el libro diario correctamente."""
        cuentas = sample_cuentas
        
        # Crear asientos en diferentes fechas
        asiento1_data = sample_asiento_data  # 2024-01-15
        await asiento_repository.create(asiento1_data)
        
        asiento2_data = AsientoContableCreate(
            fecha=date(2024, 1, 20),
            comprobante="AST-002",
            descripcion="Segundo asiento",
            detalles=[
                DetalleAsientoCreate(
                    cuenta_id=cuentas["efectivo"].id,
                    tipo_movimiento=TipoMovimiento.CREDITO,
                    monto=Decimal("200000"),
                    descripcion="Salida efectivo"
                ),
                DetalleAsientoCreate(
                    cuenta_id=cuentas["capital"].id,
                    tipo_movimiento=TipoMovimiento.DEBITO,
                    monto=Decimal("200000"),
                    descripcion="Reducción capital"
                )
            ]
        )
        await asiento_repository.create(asiento2_data)
        
        # Obtener libro diario de enero
        libro_diario = await asiento_repository.get_libro_diario(
            fecha_desde=date(2024, 1, 1),
            fecha_hasta=date(2024, 1, 31)
        )
        
        assert len(libro_diario) == 2
        # Deben estar ordenados por fecha
        assert libro_diario[0].fecha.date() == date(2024, 1, 15)
        assert libro_diario[1].fecha.date() == date(2024, 1, 20)
    
    @pytest.mark.asyncio
    async def test_get_asientos_por_cuenta(self, asiento_repository, sample_asiento_data, sample_cuentas):
        """Debe obtener asientos que afectan a una cuenta específica."""
        cuentas = sample_cuentas
        asiento_data = sample_asiento_data
        await asiento_repository.create(asiento_data)
        
        # Obtener asientos que afectan la cuenta de efectivo
        asientos_efectivo = await asiento_repository.get_asientos_por_cuenta(cuentas["efectivo"].id)
        
        assert len(asientos_efectivo) == 1
        assert asientos_efectivo[0].comprobante == "AST-001"
        
        # Verificar que tiene el detalle correspondiente
        detalle_efectivo = next(
            d for d in asientos_efectivo[0].detalles 
            if d.cuenta_id == cuentas["efectivo"].id
        )
        assert detalle_efectivo.tipo_movimiento == TipoMovimiento.DEBITO
        assert detalle_efectivo.monto == Decimal("1000000")