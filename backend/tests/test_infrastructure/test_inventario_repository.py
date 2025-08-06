"""
Pruebas de integración para SQLInventarioRepository.
Prueba todas las operaciones CRUD, cálculo de costo promedio ponderado 
y reglas de negocio del repositorio de inventario.
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from uuid import UUID, uuid4

from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.product import Product, ProductCreate
from app.domain.models.movimiento_inventario import (
    MovimientoInventario,
    MovimientoInventarioCreate,
    MovimientoInventarioFilter,
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


@pytest.fixture
def sample_product_data():
    """Datos de ejemplo para crear productos."""
    return ProductCreate(
        sku="TEST-INV-001",
        nombre="Producto Inventario Test",
        descripcion="Producto para pruebas de inventario",
        precio_base=Decimal("10.00"),
        precio_publico=Decimal("15.00"),
        stock=0
    )


@pytest.fixture
async def sample_product(product_repository, sample_product_data):
    """Crear un producto de ejemplo en la base de datos."""
    return await product_repository.create(sample_product_data)


@pytest.fixture
def sample_product_data_2():
    """Datos de ejemplo para crear un segundo producto."""
    return ProductCreate(
        sku="TEST-INV-002",
        nombre="Segundo Producto Test",
        descripcion="Segundo producto para pruebas",
        precio_base=Decimal("20.00"),
        precio_publico=Decimal("30.00"),
        stock=0
    )


@pytest.fixture
def sample_movimiento_entrada():
    """Datos de ejemplo para un movimiento de entrada."""
    def _create_movimiento(producto_id: UUID, cantidad: int = 100, precio: Decimal = Decimal("12.00")):
        return MovimientoInventarioCreate(
            producto_id=producto_id,
            tipo_movimiento=TipoMovimiento.ENTRADA,
            cantidad=cantidad,
            precio_unitario=precio,
            referencia="FC-001",
            observaciones="Compra inicial de inventario"
        )
    return _create_movimiento


@pytest.fixture
def sample_movimiento_salida():
    """Datos de ejemplo para un movimiento de salida."""
    def _create_movimiento(producto_id: UUID, cantidad: int = 50, precio: Decimal = Decimal("15.00")):
        return MovimientoInventarioCreate(
            producto_id=producto_id,
            tipo_movimiento=TipoMovimiento.SALIDA,
            cantidad=cantidad,
            precio_unitario=precio,
            referencia="FV-001",
            observaciones="Venta de productos"
        )
    return _create_movimiento


class TestInventarioRepositoryCreate:
    """Pruebas para la creación de movimientos."""

    @pytest.mark.asyncio
    async def test_create_movimiento_entrada_success(
        self, inventario_repository, product_repository, sample_product_data, sample_movimiento_entrada
    ):
        """Debe crear un movimiento de entrada exitosamente."""
        # Crear producto primero
        sample_product = await product_repository.create(sample_product_data)
        movimiento_data = sample_movimiento_entrada(sample_product.id)
        
        movimiento = await inventario_repository.create_movimiento(movimiento_data)

        assert movimiento.id is not None
        assert isinstance(movimiento.id, UUID)
        assert movimiento.producto_id == sample_product.id
        assert movimiento.tipo_movimiento == TipoMovimiento.ENTRADA
        assert movimiento.cantidad == 100
        assert movimiento.precio_unitario == Decimal("12.00")
        assert movimiento.stock_anterior == 0
        assert movimiento.stock_posterior == 100
        assert movimiento.costo_unitario == Decimal("12.00")  # Primera entrada
        assert movimiento.referencia == "FC-001"
        assert movimiento.created_at is not None

    @pytest.mark.asyncio
    async def test_create_movimiento_salida_success(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe crear un movimiento de salida exitosamente después de una entrada."""
        # Crear entrada primero
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)

        # Crear salida
        salida_data = sample_movimiento_salida(sample_product.id)
        movimiento = await inventario_repository.create_movimiento(salida_data)

        assert movimiento.tipo_movimiento == TipoMovimiento.SALIDA
        assert movimiento.cantidad == 50
        assert movimiento.stock_anterior == 100
        assert movimiento.stock_posterior == 50
        assert movimiento.costo_unitario == Decimal("12.00")  # Costo de la entrada

    @pytest.mark.asyncio
    async def test_create_movimiento_stock_insuficiente_fails(
        self, inventario_repository, sample_product, sample_movimiento_salida
    ):
        """Debe fallar al crear una salida sin stock suficiente (BR-01)."""
        salida_data = sample_movimiento_salida(sample_product.id, cantidad=100)

        with pytest.raises(ValueError, match="Stock insuficiente"):
            await inventario_repository.create_movimiento(salida_data)

    @pytest.mark.asyncio
    async def test_create_movimiento_producto_no_existe_fails(
        self, inventario_repository, sample_movimiento_entrada
    ):
        """Debe fallar al crear un movimiento para un producto inexistente."""
        producto_inexistente = uuid4()
        movimiento_data = sample_movimiento_entrada(producto_inexistente)

        with pytest.raises(ValueError, match="no encontrado"):
            await inventario_repository.create_movimiento(movimiento_data)


class TestInventarioRepositoryRead:
    """Pruebas para la lectura de movimientos."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe obtener un movimiento por ID cuando existe."""
        movimiento_data = sample_movimiento_entrada(sample_product.id)
        created_movimiento = await inventario_repository.create_movimiento(movimiento_data)

        found_movimiento = await inventario_repository.get_by_id(created_movimiento.id)

        assert found_movimiento is not None
        assert found_movimiento.id == created_movimiento.id
        assert found_movimiento.producto_id == sample_product.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, inventario_repository):
        """Debe retornar None cuando el movimiento no existe."""
        non_existent_id = uuid4()

        movimiento = await inventario_repository.get_by_id(non_existent_id)

        assert movimiento is None

    @pytest.mark.asyncio
    async def test_get_movimientos_by_producto(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe obtener movimientos de un producto específico."""
        # Crear varios movimientos
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)
        
        salida_data = sample_movimiento_salida(sample_product.id)
        await inventario_repository.create_movimiento(salida_data)

        movimientos = await inventario_repository.get_movimientos_by_producto(sample_product.id)

        assert len(movimientos) == 2
        # Debe estar ordenado por fecha descendente (más reciente primero)
        assert movimientos[0].tipo_movimiento == TipoMovimiento.SALIDA
        assert movimientos[1].tipo_movimiento == TipoMovimiento.ENTRADA

    @pytest.mark.asyncio
    async def test_get_movimientos_by_producto_with_filters(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe filtrar movimientos por tipo."""
        # Crear varios movimientos
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)
        
        salida_data = sample_movimiento_salida(sample_product.id)
        await inventario_repository.create_movimiento(salida_data)

        # Filtrar solo entradas
        movimientos_entrada = await inventario_repository.get_movimientos_by_producto(
            sample_product.id, tipo_movimiento=TipoMovimiento.ENTRADA
        )

        assert len(movimientos_entrada) == 1
        assert movimientos_entrada[0].tipo_movimiento == TipoMovimiento.ENTRADA


class TestInventarioRepositoryStock:
    """Pruebas para la gestión de stock."""

    @pytest.mark.asyncio
    async def test_get_stock_actual_empty(self, inventario_repository, sample_product):
        """Debe retornar 0 para un producto sin movimientos."""
        stock = await inventario_repository.get_stock_actual(sample_product.id)
        assert stock == 0

    @pytest.mark.asyncio
    async def test_get_stock_actual_with_movements(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe calcular stock actual basado en movimientos."""
        # Entrada de 100
        entrada_data = sample_movimiento_entrada(sample_product.id, cantidad=100)
        await inventario_repository.create_movimiento(entrada_data)

        # Salida de 30
        salida_data = sample_movimiento_salida(sample_product.id, cantidad=30)
        await inventario_repository.create_movimiento(salida_data)

        stock = await inventario_repository.get_stock_actual(sample_product.id)
        assert stock == 70

    @pytest.mark.asyncio
    async def test_validar_stock_suficiente_true(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe validar stock suficiente correctamente."""
        # Crear entrada de 100
        entrada_data = sample_movimiento_entrada(sample_product.id, cantidad=100)
        await inventario_repository.create_movimiento(entrada_data)

        stock_suficiente = await inventario_repository.validar_stock_suficiente(
            sample_product.id, 50
        )

        assert stock_suficiente is True

    @pytest.mark.asyncio
    async def test_validar_stock_suficiente_false(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe validar stock insuficiente correctamente."""
        # Crear entrada de 100
        entrada_data = sample_movimiento_entrada(sample_product.id, cantidad=100)
        await inventario_repository.create_movimiento(entrada_data)

        stock_suficiente = await inventario_repository.validar_stock_suficiente(
            sample_product.id, 150
        )

        assert stock_suficiente is False


class TestInventarioRepositoryCostoPromedio:
    """Pruebas para el cálculo de costo promedio ponderado (BR-11)."""

    @pytest.mark.asyncio
    async def test_calcular_costo_promedio_primera_entrada(
        self, inventario_repository, sample_product
    ):
        """Debe calcular costo promedio para la primera entrada."""
        calculo = await inventario_repository.calcular_costo_promedio(
            sample_product.id, cantidad_entrada=100, precio_entrada=Decimal("12.00")
        )

        assert calculo.stock_anterior == 0
        assert calculo.costo_anterior == Decimal("0.00")
        assert calculo.cantidad_entrada == 100
        assert calculo.precio_entrada == Decimal("12.00")
        assert calculo.stock_nuevo == 100
        assert calculo.costo_promedio_nuevo == Decimal("12.00")

    @pytest.mark.asyncio
    async def test_calcular_costo_promedio_segunda_entrada(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe calcular costo promedio ponderado para entradas sucesivas."""
        # Primera entrada: 100 unidades a $12.00
        entrada1_data = sample_movimiento_entrada(sample_product.id, cantidad=100, precio=Decimal("12.00"))
        await inventario_repository.create_movimiento(entrada1_data)

        # Calcular para segunda entrada: 50 unidades a $18.00
        calculo = await inventario_repository.calcular_costo_promedio(
            sample_product.id, cantidad_entrada=50, precio_entrada=Decimal("18.00")
        )

        # Cálculo esperado: (100*12 + 50*18) / 150 = (1200 + 900) / 150 = 14.00
        assert calculo.stock_anterior == 100
        assert calculo.costo_anterior == Decimal("12.00")
        assert calculo.cantidad_entrada == 50
        assert calculo.precio_entrada == Decimal("18.00")
        assert calculo.stock_nuevo == 150
        assert calculo.costo_promedio_nuevo == Decimal("14.00")

    @pytest.mark.asyncio
    async def test_get_costo_promedio_actual(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe obtener el costo promedio actual de un producto."""
        # Crear entrada
        entrada_data = sample_movimiento_entrada(sample_product.id, precio=Decimal("15.00"))
        await inventario_repository.create_movimiento(entrada_data)

        costo_promedio = await inventario_repository.get_costo_promedio_actual(sample_product.id)

        assert costo_promedio == Decimal("15.00")

    @pytest.mark.asyncio
    async def test_get_costo_promedio_actual_sin_entradas_fails(
        self, inventario_repository, sample_product
    ):
        """Debe fallar al obtener costo promedio sin entradas."""
        with pytest.raises(ValueError, match="No se encontraron movimientos de entrada"):
            await inventario_repository.get_costo_promedio_actual(sample_product.id)

    @pytest.mark.asyncio
    async def test_get_valor_inventario_producto(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe calcular el valor total del inventario de un producto."""
        # Entrada de 100 unidades a $12.00
        entrada_data = sample_movimiento_entrada(sample_product.id, cantidad=100, precio=Decimal("12.00"))
        await inventario_repository.create_movimiento(entrada_data)

        valor_inventario = await inventario_repository.get_valor_inventario_producto(sample_product.id)

        # 100 unidades * $12.00 = $1200.00
        assert valor_inventario == Decimal("1200.00")


class TestInventarioRepositoryList:
    """Pruebas para listar movimientos."""

    @pytest.mark.asyncio
    async def test_get_all_movimientos_empty(self, inventario_repository):
        """Debe retornar lista vacía cuando no hay movimientos."""
        movimientos = await inventario_repository.get_all_movimientos()
        assert movimientos == []

    @pytest.mark.asyncio
    async def test_get_all_movimientos_with_data(
        self, inventario_repository, sample_product, sample_product_2, 
        sample_movimiento_entrada
    ):
        """Debe retornar todos los movimientos ordenados por fecha."""
        # Crear movimientos en diferentes productos
        entrada1_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada1_data)

        entrada2_data = sample_movimiento_entrada(sample_product_2.id)
        await inventario_repository.create_movimiento(entrada2_data)

        movimientos = await inventario_repository.get_all_movimientos()

        assert len(movimientos) == 2
        # Verificar que están ordenados por fecha descendente
        assert movimientos[0].created_at >= movimientos[1].created_at

    @pytest.mark.asyncio
    async def test_get_all_movimientos_with_filters(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe filtrar movimientos correctamente."""
        # Crear entrada y salida
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)

        salida_data = sample_movimiento_salida(sample_product.id)
        await inventario_repository.create_movimiento(salida_data)

        # Filtrar solo por producto
        filtros = MovimientoInventarioFilter(producto_id=sample_product.id)
        movimientos = await inventario_repository.get_all_movimientos(filtros=filtros)

        assert len(movimientos) == 2
        assert all(m.producto_id == sample_product.id for m in movimientos)

        # Filtrar por tipo
        filtros = MovimientoInventarioFilter(tipo_movimiento=TipoMovimiento.ENTRADA)
        movimientos_entrada = await inventario_repository.get_all_movimientos(filtros=filtros)

        assert len(movimientos_entrada) == 1
        assert movimientos_entrada[0].tipo_movimiento == TipoMovimiento.ENTRADA

    @pytest.mark.asyncio
    async def test_count_movimientos(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe contar movimientos correctamente."""
        initial_count = await inventario_repository.count_movimientos()
        assert initial_count == 0

        # Crear movimientos
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)

        salida_data = sample_movimiento_salida(sample_product.id)
        await inventario_repository.create_movimiento(salida_data)

        total_count = await inventario_repository.count_movimientos()
        assert total_count == 2

        # Contar con filtros
        filtros = MovimientoInventarioFilter(tipo_movimiento=TipoMovimiento.ENTRADA)
        entrada_count = await inventario_repository.count_movimientos(filtros)
        assert entrada_count == 1


class TestInventarioRepositoryEstadisticas:
    """Pruebas para estadísticas de inventario."""

    @pytest.mark.asyncio
    async def test_get_ultimo_movimiento_producto(
        self, inventario_repository, sample_product, sample_movimiento_entrada, sample_movimiento_salida
    ):
        """Debe obtener el último movimiento de un producto."""
        # Sin movimientos
        ultimo = await inventario_repository.get_ultimo_movimiento_producto(sample_product.id)
        assert ultimo is None

        # Crear movimientos
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)

        salida_data = sample_movimiento_salida(sample_product.id)
        movimiento_salida = await inventario_repository.create_movimiento(salida_data)

        ultimo = await inventario_repository.get_ultimo_movimiento_producto(sample_product.id)
        assert ultimo is not None
        assert ultimo.id == movimiento_salida.id
        assert ultimo.tipo_movimiento == TipoMovimiento.SALIDA

    @pytest.mark.asyncio
    async def test_get_productos_mas_movidos(
        self, inventario_repository, sample_product, sample_product_2, sample_movimiento_entrada
    ):
        """Debe obtener productos más movidos."""
        # Crear más movimientos para producto 1
        for i in range(3):
            entrada_data = sample_movimiento_entrada(sample_product.id, cantidad=10*(i+1))
            await inventario_repository.create_movimiento(entrada_data)

        # Crear menos movimientos para producto 2
        entrada_data = sample_movimiento_entrada(sample_product_2.id)
        await inventario_repository.create_movimiento(entrada_data)

        productos_mas_movidos = await inventario_repository.get_productos_mas_movidos(limit=2)

        assert len(productos_mas_movidos) == 2
        # El producto 1 debe estar primero (más movimientos)
        assert productos_mas_movidos[0]["producto_id"] == sample_product.id
        assert productos_mas_movidos[0]["total_movimientos"] == 3
        assert productos_mas_movidos[1]["producto_id"] == sample_product_2.id
        assert productos_mas_movidos[1]["total_movimientos"] == 1


class TestInventarioRepositoryUtilities:
    """Pruebas para métodos utilitarios."""

    @pytest.mark.asyncio
    async def test_recalcular_costos_producto(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe recalcular costos de un producto correctamente."""
        # Crear varias entradas
        entrada1_data = sample_movimiento_entrada(sample_product.id, cantidad=100, precio=Decimal("10.00"))
        await inventario_repository.create_movimiento(entrada1_data)

        entrada2_data = sample_movimiento_entrada(sample_product.id, cantidad=50, precio=Decimal("20.00"))
        await inventario_repository.create_movimiento(entrada2_data)

        # Recalcular costos
        success = await inventario_repository.recalcular_costos_producto(sample_product.id)
        assert success is True

        # Verificar que los costos están correctos
        costo_actual = await inventario_repository.get_costo_promedio_actual(sample_product.id)
        # (100*10 + 50*20) / 150 = 2000 / 150 = 13.33
        expected_cost = Decimal("13.33")
        assert abs(costo_actual - expected_cost) < Decimal("0.01")

    @pytest.mark.asyncio
    async def test_get_movimientos_pendientes_costo(
        self, inventario_repository, sample_product, sample_movimiento_entrada
    ):
        """Debe obtener movimientos sin costo calculado."""
        # Inicialmente no hay movimientos pendientes
        pendientes = await inventario_repository.get_movimientos_pendientes_costo()
        assert len(pendientes) == 0

        # Crear un movimiento (que tendrá costo calculado automáticamente)
        entrada_data = sample_movimiento_entrada(sample_product.id)
        await inventario_repository.create_movimiento(entrada_data)

        # Después de crear, aún no debería haber pendientes
        pendientes = await inventario_repository.get_movimientos_pendientes_costo()
        assert len(pendientes) == 0 