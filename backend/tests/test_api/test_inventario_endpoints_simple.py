"""
Pruebas simplificadas para los endpoints de inventario.
"""

import pytest
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

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


class TestInventarioEndpointsSimple:
    """Pruebas simplificadas para endpoints de inventario."""

    def test_registrar_movimiento_entrada_basic(self, client: TestClient):
        """Debe registrar un movimiento de entrada básico."""
        # Crear producto primero
        product_data = {
            "sku": "TEST-INV-001",
            "nombre": "Producto Test",
            "precio_base": "10.00",
            "precio_publico": "15.00",
            "stock": 0
        }
        
        product_response = client.post("/api/v1/products/", json=product_data)
        print(f"Product response: {product_response.status_code} - {product_response.text}")
        assert product_response.status_code == 201
        producto = product_response.json()

        # Registrar movimiento de entrada
        movimiento_data = {
            "producto_id": producto["id"],
            "tipo_movimiento": "entrada",
            "cantidad": 100,
            "precio_unitario": "12.00",
            "referencia": "FC-001"
        }

        response = client.post("/api/v1/inventario/movimientos/", json=movimiento_data)
        print(f"Movimiento response: {response.status_code} - {response.text}")
        
        if response.status_code != 201:
            print(f"Error details: {response.json()}")
        
        assert response.status_code == 201

    def test_listar_movimientos_empty(self, client: TestClient):
        """Debe retornar lista vacía cuando no hay movimientos."""
        response = client.get("/api/v1/inventario/movimientos/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["movimientos"] == []
        assert data["total"] == 0

    def test_obtener_resumen_inventario_empty(self, client: TestClient):
        """Debe obtener resumen vacío cuando no hay productos."""
        response = client.get("/api/v1/inventario/resumen/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_productos"] == 0

    def test_validar_stock_basic(self, client: TestClient):
        """Debe validar stock básico."""
        # Crear producto primero
        product_data = {
            "sku": "TEST-INV-002",
            "nombre": "Producto Test 2",
            "precio_base": "10.00",
            "precio_publico": "15.00",
            "stock": 0
        }
        
        product_response = client.post("/api/v1/products/", json=product_data)
        assert product_response.status_code == 201
        producto = product_response.json()

        # Validar stock
        validacion_data = {
            "producto_id": producto["id"],
            "cantidad_requerida": 50
        }

        response = client.post("/api/v1/inventario/validar-stock/", json=validacion_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock_actual"] == 0
        assert data["stock_suficiente"] is False 