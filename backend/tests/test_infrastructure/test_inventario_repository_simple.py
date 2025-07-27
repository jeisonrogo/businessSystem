"""
Pruebas simplificadas de integración para SQLInventarioRepository.
Prueba las operaciones principales y reglas de negocio del repositorio de inventario.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.domain.models.product import Product, ProductCreate
from app.domain.models.movimiento_inventario import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    TipoMovimiento
)
from app.infrastructure.repositories.inventario_repository import SQLInventarioRepository
from app.infrastructure.repositories.product_repository import SQLProductRepository


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
def product_repository(session):
    """Crear una instancia del repositorio de productos."""
    return SQLProductRepository(session)


@pytest.fixture
def inventario_repository(session, product_repository):
    """Crear una instancia del repositorio de inventario."""
    return SQLInventarioRepository(session, product_repository)


class TestInventarioRepositoryBasic:
    """Pruebas básicas para el repositorio de inventario."""

    @pytest.mark.asyncio
    async def test_create_entrada_success(self, inventario_repository, product_repository):
        """Debe crear un movimiento de entrada exitosamente."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-001",
            nombre="Producto Test",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Crear movimiento de entrada
        movimiento_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00"),
            referencia="FC-001"
        )

        movimiento = await inventario_repository.create_movimiento(movimiento_data)

        assert movimiento.id is not None
        assert movimiento.producto_id == producto.id
        assert movimiento.tipo_movimiento == TipoMovimiento.ENTRADA
        assert movimiento.cantidad == 100
        assert movimiento.precio_unitario == Decimal("12.00")
        assert movimiento.stock_anterior == 0
        assert movimiento.stock_posterior == 100
        assert movimiento.costo_unitario == Decimal("12.00")  # Primera entrada

    @pytest.mark.asyncio
    async def test_create_salida_after_entrada(self, inventario_repository, product_repository):
        """Debe crear un movimiento de salida después de una entrada."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-002",
            nombre="Producto Test 2",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Crear entrada primero
        entrada_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )
        await inventario_repository.create_movimiento(entrada_data)

        # Crear salida
        salida_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=50,
            precio_unitario=Decimal("15.00")
        )

        movimiento = await inventario_repository.create_movimiento(salida_data)

        assert movimiento.tipo_movimiento == TipoMovimiento.SALIDA
        assert movimiento.cantidad == 50
        assert movimiento.stock_anterior == 100
        assert movimiento.stock_posterior == 50
        assert movimiento.costo_unitario == Decimal("12.00")

    @pytest.mark.asyncio
    async def test_stock_insuficiente_fails(self, inventario_repository, product_repository):
        """Debe fallar al crear una salida sin stock suficiente (BR-01)."""
        # Crear producto sin stock
        product_data = ProductCreate(
            sku="TEST-003",
            nombre="Producto Test 3",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Intentar salida sin stock
        salida_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=100,
            precio_unitario=Decimal("15.00")
        )

        with pytest.raises(ValueError, match="Stock insuficiente"):
            await inventario_repository.create_movimiento(salida_data)

    @pytest.mark.asyncio
    async def test_producto_no_existe_fails(self, inventario_repository):
        """Debe fallar al crear un movimiento para un producto inexistente."""
        movimiento_data = MovimientoInventarioCreate(
            producto_id=uuid4(),
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )

        with pytest.raises(ValueError, match="no encontrado"):
            await inventario_repository.create_movimiento(movimiento_data)

    @pytest.mark.asyncio
    async def test_get_stock_actual(self, inventario_repository, product_repository):
        """Debe calcular stock actual basado en movimientos."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-004",
            nombre="Producto Test 4",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Stock inicial debe ser 0
        stock = await inventario_repository.get_stock_actual(producto.id)
        assert stock == 0

        # Entrada de 100
        entrada_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )
        await inventario_repository.create_movimiento(entrada_data)

        # Stock debe ser 100
        stock = await inventario_repository.get_stock_actual(producto.id)
        assert stock == 100

        # Salida de 30
        salida_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=30,
            precio_unitario=Decimal("15.00")
        )
        await inventario_repository.create_movimiento(salida_data)

        # Stock debe ser 70
        stock = await inventario_repository.get_stock_actual(producto.id)
        assert stock == 70

    @pytest.mark.asyncio
    async def test_costo_promedio_ponderado(self, inventario_repository, product_repository):
        """Debe calcular costo promedio ponderado correctamente (BR-11)."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-005",
            nombre="Producto Test 5",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Primera entrada: 100 unidades a $10.00
        entrada1_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("10.00")
        )
        mov1 = await inventario_repository.create_movimiento(entrada1_data)
        assert mov1.costo_unitario == Decimal("10.00")

        # Segunda entrada: 50 unidades a $20.00
        # Costo promedio esperado: (100*10 + 50*20) / 150 = 2000/150 = 13.33
        entrada2_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=50,
            precio_unitario=Decimal("20.00")
        )
        mov2 = await inventario_repository.create_movimiento(entrada2_data)
        
        # Verificar que el costo promedio se calculó correctamente
        expected_cost = (100 * 10 + 50 * 20) / 150  # 13.333...
        actual_cost = float(mov2.costo_unitario)
        assert abs(actual_cost - expected_cost) < 0.01

    @pytest.mark.asyncio
    async def test_validar_stock_suficiente(self, inventario_repository, product_repository):
        """Debe validar stock suficiente correctamente."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-006",
            nombre="Producto Test 6",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Crear entrada de 100
        entrada_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )
        await inventario_repository.create_movimiento(entrada_data)

        # Validar stock suficiente
        stock_suficiente = await inventario_repository.validar_stock_suficiente(
            producto.id, 50
        )
        assert stock_suficiente is True

        # Validar stock insuficiente
        stock_insuficiente = await inventario_repository.validar_stock_suficiente(
            producto.id, 150
        )
        assert stock_insuficiente is False

    @pytest.mark.asyncio
    async def test_get_movimientos_by_producto(self, inventario_repository, product_repository):
        """Debe obtener movimientos de un producto específico."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-007",
            nombre="Producto Test 7",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Crear varios movimientos
        entrada_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )
        await inventario_repository.create_movimiento(entrada_data)
        
        salida_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=50,
            precio_unitario=Decimal("15.00")
        )
        await inventario_repository.create_movimiento(salida_data)

        movimientos = await inventario_repository.get_movimientos_by_producto(producto.id)

        assert len(movimientos) == 2
        # Debe estar ordenado por fecha descendente (más reciente primero)
        assert movimientos[0].tipo_movimiento == TipoMovimiento.SALIDA
        assert movimientos[1].tipo_movimiento == TipoMovimiento.ENTRADA

    @pytest.mark.asyncio
    async def test_get_valor_inventario_producto(self, inventario_repository, product_repository):
        """Debe calcular el valor total del inventario de un producto."""
        # Crear producto
        product_data = ProductCreate(
            sku="TEST-008",
            nombre="Producto Test 8",
            precio_base=Decimal("10.00"),
            precio_publico=Decimal("15.00"),
            stock=0
        )
        producto = await product_repository.create(product_data)

        # Entrada de 100 unidades a $12.00
        entrada_data = MovimientoInventarioCreate(
            producto_id=producto.id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=100,
            precio_unitario=Decimal("12.00")
        )
        await inventario_repository.create_movimiento(entrada_data)

        valor_inventario = await inventario_repository.get_valor_inventario_producto(producto.id)

        # 100 unidades * $12.00 = $1200.00
        assert valor_inventario == Decimal("1200.00") 