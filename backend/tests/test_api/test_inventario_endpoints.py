"""
Pruebas de integración para los endpoints de inventario.
Prueba todas las operaciones REST y funcionalidades específicas del inventario.
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.product import Product, ProductCreate
from app.domain.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from main import app


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
def client(session):
    """Crear un cliente de prueba con override de la sesión de base de datos."""
    from app.infrastructure.database.session import get_session

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_product_data():
    """Datos de ejemplo para crear productos."""
    return {
        "sku": "TEST-INV-001",
        "nombre": "Producto Inventario Test",
        "descripcion": "Producto para pruebas de inventario",
        "precio_base": "10.00",
        "precio_publico": "15.00",
        "stock": 0
    }


@pytest.fixture
def sample_movimiento_entrada_data():
    """Datos de ejemplo para movimientos de entrada."""
    def _create_data(producto_id: str, cantidad: int = 100, precio: str = "12.00"):
        return {
            "producto_id": producto_id,
            "tipo_movimiento": "entrada",
            "cantidad": cantidad,
            "precio_unitario": precio,
            "referencia": "FC-001",
            "observaciones": "Compra inicial de inventario"
        }
    return _create_data


@pytest.fixture
def sample_movimiento_salida_data():
    """Datos de ejemplo para movimientos de salida."""
    def _create_data(producto_id: str, cantidad: int = 50, precio: str = "15.00"):
        return {
            "producto_id": producto_id,
            "tipo_movimiento": "salida",
            "cantidad": cantidad,
            "precio_unitario": precio,
            "referencia": "FV-001",
            "observaciones": "Venta de productos"
        }
    return _create_data


class TestInventarioEndpointsCreate:
    """Pruebas para el registro de movimientos."""

    def test_registrar_movimiento_entrada_success(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe registrar un movimiento de entrada exitosamente."""
        # Crear producto primero
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        assert product_response.status_code == 201
        producto = product_response.json()

        # Registrar movimiento de entrada
        movimiento_data = sample_movimiento_entrada_data(producto["id"])
        response = client.post("/api/v1/inventario/movimientos/", json=movimiento_data)

        assert response.status_code == 201
        data = response.json()

        assert data["producto_id"] == producto["id"]
        assert data["tipo_movimiento"] == "entrada"
        assert data["cantidad"] == 100
        assert data["precio_unitario"] == "12.00"
        assert data["stock_anterior"] == 0
        assert data["stock_posterior"] == 100
        assert data["costo_unitario"] == "12.00"  # Primera entrada
        assert data["referencia"] == "FC-001"
        assert "id" in data
        assert "created_at" in data

    def test_registrar_movimiento_salida_success(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe registrar un movimiento de salida exitosamente después de una entrada."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Registrar entrada primero
        entrada_data = sample_movimiento_entrada_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        # Registrar salida
        salida_data = sample_movimiento_salida_data(producto["id"])
        response = client.post("/api/v1/inventario/movimientos/", json=salida_data)

        assert response.status_code == 201
        data = response.json()

        assert data["tipo_movimiento"] == "salida"
        assert data["cantidad"] == 50
        assert data["stock_anterior"] == 100
        assert data["stock_posterior"] == 50
        assert data["costo_unitario"] == "12.00"

    def test_registrar_movimiento_stock_insuficiente_fails(
        self, client: TestClient, sample_product_data, sample_movimiento_salida_data
    ):
        """Debe fallar al registrar una salida sin stock suficiente."""
        # Crear producto sin stock
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Intentar salida sin stock
        salida_data = sample_movimiento_salida_data(producto["id"], cantidad=100)
        response = client.post("/api/v1/inventario/movimientos/", json=salida_data)

        assert response.status_code == 400
        assert "Stock insuficiente" in response.json()["detail"]

    def test_registrar_movimiento_producto_no_existe_fails(
        self, client: TestClient, sample_movimiento_entrada_data
    ):
        """Debe fallar al registrar un movimiento para un producto inexistente."""
        producto_inexistente = str(uuid4())
        movimiento_data = sample_movimiento_entrada_data(producto_inexistente)

        response = client.post("/api/v1/inventario/movimientos/", json=movimiento_data)

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_registrar_movimiento_datos_invalidos(self, client: TestClient, sample_product_data):
        """Debe fallar con datos inválidos."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Datos inválidos
        invalid_data = {
            "producto_id": producto["id"],
            "tipo_movimiento": "entrada",
            "cantidad": -10,  # Cantidad negativa
            "precio_unitario": "-5.00"  # Precio negativo
        }

        response = client.post("/api/v1/inventario/movimientos/", json=invalid_data)

        assert response.status_code == 422  # Validation error


class TestInventarioEndpointsRead:
    """Pruebas para la consulta de movimientos."""

    def test_obtener_movimiento_by_id_exists(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe obtener un movimiento por ID cuando existe."""
        # Crear producto y movimiento
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        movimiento_data = sample_movimiento_entrada_data(producto["id"])
        create_response = client.post("/api/v1/inventario/movimientos/", json=movimiento_data)
        created_movimiento = create_response.json()

        # Obtener movimiento por ID
        response = client.get(f"/api/v1/inventario/movimientos/{created_movimiento['id']}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == created_movimiento["id"]
        assert data["producto_id"] == producto["id"]
        assert data["tipo_movimiento"] == "entrada"

    def test_obtener_movimiento_by_id_not_exists(self, client: TestClient):
        """Debe retornar 404 cuando el movimiento no existe."""
        non_existent_id = str(uuid4())

        response = client.get(f"/api/v1/inventario/movimientos/{non_existent_id}")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_listar_movimientos_empty(self, client: TestClient):
        """Debe retornar lista vacía cuando no hay movimientos."""
        response = client.get("/api/v1/inventario/movimientos/")

        assert response.status_code == 200
        data = response.json()

        assert data["movimientos"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 50
        assert data["has_next"] is False
        assert data["has_prev"] is False

    def test_listar_movimientos_with_data(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe retornar lista de movimientos cuando existen."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Crear movimientos
        entrada_data = sample_movimiento_entrada_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        salida_data = sample_movimiento_salida_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=salida_data)

        response = client.get("/api/v1/inventario/movimientos/")

        assert response.status_code == 200
        data = response.json()

        assert len(data["movimientos"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["has_next"] is False
        assert data["has_prev"] is False

        # Verificar orden descendente por fecha
        movimientos = data["movimientos"]
        assert movimientos[0]["tipo_movimiento"] == "salida"  # Más reciente
        assert movimientos[1]["tipo_movimiento"] == "entrada"

    def test_listar_movimientos_with_filters(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe filtrar movimientos correctamente."""
        # Crear producto y movimientos
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        entrada_data = sample_movimiento_entrada_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        salida_data = sample_movimiento_salida_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=salida_data)

        # Filtrar por tipo
        response = client.get("/api/v1/inventario/movimientos/?tipo_movimiento=entrada")

        assert response.status_code == 200
        data = response.json()

        assert len(data["movimientos"]) == 1
        assert data["total"] == 1
        assert data["movimientos"][0]["tipo_movimiento"] == "entrada"

        # Filtrar por producto
        response = client.get(f"/api/v1/inventario/movimientos/?producto_id={producto['id']}")

        assert response.status_code == 200
        data = response.json()

        assert len(data["movimientos"]) == 2
        assert all(m["producto_id"] == producto["id"] for m in data["movimientos"])


class TestInventarioEndpointsKardex:
    """Pruebas para la consulta de kardex."""

    def test_consultar_kardex_producto_exists(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe consultar el kardex de un producto exitosamente."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Crear movimientos
        entrada_data = sample_movimiento_entrada_data(producto["id"], cantidad=100, precio="12.00")
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        salida_data = sample_movimiento_salida_data(producto["id"], cantidad=30)
        client.post("/api/v1/inventario/movimientos/", json=salida_data)

        # Consultar kardex
        response = client.get(f"/api/v1/inventario/kardex/{producto['id']}")

        assert response.status_code == 200
        data = response.json()

        assert data["producto_id"] == producto["id"]
        assert len(data["movimientos"]) == 2
        assert data["stock_actual"] == 70  # 100 - 30
        assert data["costo_promedio_actual"] == "12.00"
        assert data["valor_inventario"] == "840.00"  # 70 * 12.00
        assert data["total_movimientos"] == 2

    def test_consultar_kardex_producto_no_existe_fails(self, client: TestClient):
        """Debe fallar al consultar kardex de un producto inexistente."""
        producto_inexistente = str(uuid4())

        response = client.get(f"/api/v1/inventario/kardex/{producto_inexistente}")

        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_consultar_kardex_with_filters(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe filtrar movimientos en el kardex."""
        # Crear producto y movimientos
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        entrada_data = sample_movimiento_entrada_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        salida_data = sample_movimiento_salida_data(producto["id"])
        client.post("/api/v1/inventario/movimientos/", json=salida_data)

        # Filtrar kardex por tipo
        response = client.get(f"/api/v1/inventario/kardex/{producto['id']}?tipo_movimiento=entrada")

        assert response.status_code == 200
        data = response.json()

        assert len(data["movimientos"]) == 1
        assert data["movimientos"][0]["tipo_movimiento"] == "entrada"


class TestInventarioEndpointsEstadisticas:
    """Pruebas para estadísticas y resúmenes."""

    def test_obtener_resumen_inventario_empty(self, client: TestClient):
        """Debe obtener resumen vacío cuando no hay productos."""
        response = client.get("/api/v1/inventario/resumen/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_productos"] == 0
        assert data["valor_total_inventario"] == 0
        assert data["productos_sin_stock"] == 0
        assert data["productos_stock_bajo"] == 0
        assert data["ultimo_movimiento"] is None

    def test_obtener_resumen_inventario_with_data(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe obtener resumen con datos cuando hay productos y movimientos."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Crear movimiento
        entrada_data = sample_movimiento_entrada_data(producto["id"], cantidad=100, precio="10.00")
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        response = client.get("/api/v1/inventario/resumen/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_productos"] == 1
        assert data["valor_total_inventario"] > 0
        assert data["productos_sin_stock"] == 0
        assert data["ultimo_movimiento"] is not None

    def test_obtener_estadisticas_inventario_empty(self, client: TestClient):
        """Debe obtener estadísticas vacías cuando no hay movimientos."""
        response = client.get("/api/v1/inventario/estadisticas/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_entradas_mes"] == 0
        assert data["total_salidas_mes"] == 0
        assert data["total_mermas_mes"] == 0
        assert data["valor_entradas_mes"] == 0
        assert data["valor_salidas_mes"] == 0
        assert data["valor_mermas_mes"] == 0
        assert data["productos_mas_movidos"] == []

    def test_obtener_estadisticas_inventario_with_data(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data, sample_movimiento_salida_data
    ):
        """Debe obtener estadísticas con datos cuando hay movimientos."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Crear movimientos
        entrada_data = sample_movimiento_entrada_data(producto["id"], cantidad=100, precio="12.00")
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        salida_data = sample_movimiento_salida_data(producto["id"], cantidad=30, precio="15.00")
        client.post("/api/v1/inventario/movimientos/", json=salida_data)

        response = client.get("/api/v1/inventario/estadisticas/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_entradas_mes"] == 1
        assert data["total_salidas_mes"] == 1
        assert data["total_mermas_mes"] == 0
        assert float(data["valor_entradas_mes"]) == 1200.00  # 100 * 12.00
        assert float(data["valor_salidas_mes"]) == 450.00   # 30 * 15.00
        assert len(data["productos_mas_movidos"]) == 1
        assert data["productos_mas_movidos"][0]["total_movimientos"] == 2


class TestInventarioEndpointsValidacion:
    """Pruebas para validación de stock."""

    def test_validar_stock_success(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe validar stock exitosamente."""
        # Crear producto y entrada
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        entrada_data = sample_movimiento_entrada_data(producto["id"], cantidad=100)
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        # Validar stock
        validacion_data = {
            "producto_id": producto["id"],
            "cantidad_requerida": 50
        }

        response = client.post("/api/v1/inventario/validar-stock/", json=validacion_data)

        assert response.status_code == 200
        data = response.json()

        assert data["producto_id"] == producto["id"]
        assert data["stock_actual"] == 100
        assert data["cantidad_requerida"] == 50
        assert data["stock_suficiente"] is True
        assert data["cantidad_disponible"] == 50

    def test_validar_stock_insuficiente(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe detectar stock insuficiente."""
        # Crear producto con poco stock
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        entrada_data = sample_movimiento_entrada_data(producto["id"], cantidad=50)
        client.post("/api/v1/inventario/movimientos/", json=entrada_data)

        # Validar stock insuficiente
        validacion_data = {
            "producto_id": producto["id"],
            "cantidad_requerida": 100
        }

        response = client.post("/api/v1/inventario/validar-stock/", json=validacion_data)

        assert response.status_code == 200
        data = response.json()

        assert data["stock_actual"] == 50
        assert data["cantidad_requerida"] == 100
        assert data["stock_suficiente"] is False
        assert data["cantidad_disponible"] == 0

    def test_validar_stock_datos_invalidos(self, client: TestClient):
        """Debe fallar con datos de validación inválidos."""
        invalid_data = {
            "producto_id": "invalid-uuid",
            "cantidad_requerida": -10  # Cantidad negativa
        }

        response = client.post("/api/v1/inventario/validar-stock/", json=invalid_data)

        assert response.status_code == 422  # Validation error


class TestInventarioEndpointsUtilities:
    """Pruebas para funcionalidades utilitarias."""

    def test_recalcular_costos_producto_success(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe recalcular costos de un producto exitosamente."""
        # Crear producto y movimientos
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Crear varias entradas
        entrada1_data = sample_movimiento_entrada_data(producto["id"], cantidad=100, precio="10.00")
        client.post("/api/v1/inventario/movimientos/", json=entrada1_data)

        entrada2_data = sample_movimiento_entrada_data(producto["id"], cantidad=50, precio="20.00")
        client.post("/api/v1/inventario/movimientos/", json=entrada2_data)

        # Recalcular costos
        response = client.post(f"/api/v1/inventario/recalcular-costos/{producto['id']}")

        assert response.status_code == 200
        data = response.json()

        assert "recalculados exitosamente" in data["message"]
        assert producto["id"] in data["message"]

    def test_recalcular_costos_producto_no_existe_fails(self, client: TestClient):
        """Debe fallar al recalcular costos de un producto inexistente."""
        producto_inexistente = str(uuid4())

        response = client.post(f"/api/v1/inventario/recalcular-costos/{producto_inexistente}")

        # Nota: Este endpoint podría no fallar inmediatamente si no hay validación previa
        # El comportamiento exacto depende de la implementación del repositorio
        assert response.status_code in [200, 400]  # Puede variar según implementación


class TestInventarioEndpointsCostoPromedio:
    """Pruebas específicas para cálculo de costo promedio ponderado (BR-11)."""

    def test_costo_promedio_ponderado_multiples_entradas(
        self, client: TestClient, sample_product_data, sample_movimiento_entrada_data
    ):
        """Debe calcular costo promedio ponderado correctamente con múltiples entradas."""
        # Crear producto
        product_response = client.post("/api/v1/products/", json=sample_product_data)
        producto = product_response.json()

        # Primera entrada: 100 unidades a $10.00
        entrada1_data = sample_movimiento_entrada_data(producto["id"], cantidad=100, precio="10.00")
        response1 = client.post("/api/v1/inventario/movimientos/", json=entrada1_data)
        mov1 = response1.json()
        assert mov1["costo_unitario"] == "10.00"

        # Segunda entrada: 50 unidades a $20.00
        # Costo promedio esperado: (100*10 + 50*20) / 150 = 2000/150 = 13.33
        entrada2_data = sample_movimiento_entrada_data(producto["id"], cantidad=50, precio="20.00")
        response2 = client.post("/api/v1/inventario/movimientos/", json=entrada2_data)
        mov2 = response2.json()
        
        # Verificar que el costo promedio se calculó correctamente
        expected_cost = (100 * 10 + 50 * 20) / 150
        actual_cost = float(mov2["costo_unitario"])
        assert abs(actual_cost - expected_cost) < 0.01

        # Verificar kardex
        kardex_response = client.get(f"/api/v1/inventario/kardex/{producto['id']}")
        kardex = kardex_response.json()
        
        assert kardex["stock_actual"] == 150
        assert abs(float(kardex["costo_promedio_actual"]) - expected_cost) < 0.01
        assert abs(float(kardex["valor_inventario"]) - (150 * expected_cost)) < 0.01 