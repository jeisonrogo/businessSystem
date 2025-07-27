"""
Pruebas de integración para los endpoints de productos.
Prueba todas las operaciones CRUD y funcionalidades específicas de los productos.
"""

import pytest
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.product import Product
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
        "sku": "TEST-001",
        "nombre": "Producto de Prueba",
        "descripcion": "Descripción del producto de prueba",
        "url_foto": "https://example.com/image.jpg",
        "precio_base": "10.00",
        "precio_publico": "15.00",
        "stock": 100
    }


@pytest.fixture
def sample_product_data_2():
    """Segundo conjunto de datos de ejemplo para pruebas."""
    return {
        "sku": "TEST-002",
        "nombre": "Segundo Producto",
        "descripcion": "Otro producto de prueba",
        "precio_base": "20.00",
        "precio_publico": "25.00",
        "stock": 50
    }


class TestProductsEndpointsCreate:
    """Pruebas para la creación de productos."""

    def test_create_product_success(self, client: TestClient, sample_product_data):
        """Debe crear un producto exitosamente."""
        response = client.post("/api/v1/products/", json=sample_product_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["sku"] == sample_product_data["sku"]
        assert data["nombre"] == sample_product_data["nombre"]
        assert data["descripcion"] == sample_product_data["descripcion"]
        assert data["url_foto"] == sample_product_data["url_foto"]
        assert data["precio_base"] == sample_product_data["precio_base"]
        assert data["precio_publico"] == sample_product_data["precio_publico"]
        assert data["stock"] == sample_product_data["stock"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_create_product_duplicate_sku_fails(self, client: TestClient, sample_product_data):
        """Debe fallar al crear un producto con SKU duplicado."""
        # Crear el primer producto
        response1 = client.post("/api/v1/products/", json=sample_product_data)
        assert response1.status_code == 201
        
        # Intentar crear otro producto con el mismo SKU
        duplicate_data = sample_product_data.copy()
        duplicate_data["nombre"] = "Producto Duplicado"
        
        response2 = client.post("/api/v1/products/", json=duplicate_data)
        
        assert response2.status_code == 400
        assert "Ya existe un producto con el SKU" in response2.json()["detail"]

    def test_create_product_invalid_data(self, client: TestClient):
        """Debe fallar con datos inválidos."""
        invalid_data = {
            "sku": "",  # SKU vacío
            "nombre": "",  # Nombre vacío
            "precio_base": "-5.00",  # Precio negativo
            "precio_publico": "1.00"  # Precio público menor que base
        }
        
        response = client.post("/api/v1/products/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_product_minimal_data(self, client: TestClient):
        """Debe crear un producto con datos mínimos."""
        minimal_data = {
            "sku": "MIN-001",
            "nombre": "Producto Mínimo",
            "precio_base": "1.00",
            "precio_publico": "2.00"
        }
        
        response = client.post("/api/v1/products/", json=minimal_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["sku"] == "MIN-001"
        assert data["nombre"] == "Producto Mínimo"
        assert data["descripcion"] is None
        assert data["url_foto"] is None
        assert data["stock"] == 0


class TestProductsEndpointsRead:
    """Pruebas para la lectura de productos."""

    def test_get_product_by_id_exists(self, client: TestClient, sample_product_data):
        """Debe obtener un producto por ID cuando existe."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Obtener el producto por ID
        response = client.get(f"/api/v1/products/{created_product['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == created_product["id"]
        assert data["sku"] == sample_product_data["sku"]
        assert data["nombre"] == sample_product_data["nombre"]

    def test_get_product_by_id_not_exists(self, client: TestClient):
        """Debe retornar 404 cuando el producto no existe."""
        non_existent_id = str(uuid4())
        
        response = client.get(f"/api/v1/products/{non_existent_id}")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_get_product_by_sku_exists(self, client: TestClient, sample_product_data):
        """Debe obtener un producto por SKU cuando existe."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        
        # Obtener el producto por SKU
        response = client.get(f"/api/v1/products/sku/{sample_product_data['sku']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sku"] == sample_product_data["sku"]
        assert data["nombre"] == sample_product_data["nombre"]

    def test_get_product_by_sku_not_exists(self, client: TestClient):
        """Debe retornar 404 cuando el SKU no existe."""
        response = client.get("/api/v1/products/sku/NON-EXISTENT")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]


class TestProductsEndpointsList:
    """Pruebas para listar productos."""

    def test_list_products_empty(self, client: TestClient):
        """Debe retornar lista vacía cuando no hay productos."""
        response = client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["products"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["limit"] == 10
        assert data["has_next"] is False
        assert data["has_prev"] is False

    def test_list_products_with_data(self, client: TestClient, sample_product_data, sample_product_data_2):
        """Debe retornar lista de productos cuando existen."""
        # Crear productos
        client.post("/api/v1/products/", json=sample_product_data)
        client.post("/api/v1/products/", json=sample_product_data_2)
        
        response = client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["products"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["has_next"] is False
        assert data["has_prev"] is False
        
        # Verificar que ambos productos están en la respuesta
        skus = [p["sku"] for p in data["products"]]
        assert sample_product_data["sku"] in skus
        assert sample_product_data_2["sku"] in skus

    def test_list_products_pagination(self, client: TestClient, sample_product_data, sample_product_data_2):
        """Debe respetar los parámetros de paginación."""
        # Crear productos
        client.post("/api/v1/products/", json=sample_product_data)
        client.post("/api/v1/products/", json=sample_product_data_2)
        
        # Primera página con límite de 1
        response1 = client.get("/api/v1/products/?page=1&limit=1")
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        assert len(data1["products"]) == 1
        assert data1["total"] == 2
        assert data1["page"] == 1
        assert data1["limit"] == 1
        assert data1["has_next"] is True
        assert data1["has_prev"] is False
        
        # Segunda página
        response2 = client.get("/api/v1/products/?page=2&limit=1")
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert len(data2["products"]) == 1
        assert data2["page"] == 2
        assert data2["has_next"] is False
        assert data2["has_prev"] is True
        
        # Verificar que son productos diferentes
        assert data1["products"][0]["id"] != data2["products"][0]["id"]

    def test_list_products_search(self, client: TestClient, sample_product_data, sample_product_data_2):
        """Debe filtrar productos por término de búsqueda."""
        # Crear productos
        client.post("/api/v1/products/", json=sample_product_data)
        client.post("/api/v1/products/", json=sample_product_data_2)
        
        # Buscar por nombre
        response = client.get("/api/v1/products/?search=Segundo")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["products"]) == 1
        assert data["total"] == 1
        assert data["products"][0]["sku"] == "TEST-002"


class TestProductsEndpointsUpdate:
    """Pruebas para la actualización de productos."""

    def test_update_product_success(self, client: TestClient, sample_product_data):
        """Debe actualizar un producto exitosamente."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Actualizar el producto
        update_data = {
            "nombre": "Producto Actualizado",
            "descripcion": "Descripción actualizada",
            "precio_base": "12.00"
        }
        
        response = client.put(f"/api/v1/products/{created_product['id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == created_product["id"]
        assert data["sku"] == created_product["sku"]  # SKU no debe cambiar
        assert data["nombre"] == "Producto Actualizado"
        assert data["descripcion"] == "Descripción actualizada"
        assert data["precio_base"] == "12.00"
        assert data["precio_publico"] == created_product["precio_publico"]  # No cambió

    def test_update_product_not_exists(self, client: TestClient):
        """Debe retornar 404 al actualizar un producto que no existe."""
        non_existent_id = str(uuid4())
        update_data = {"nombre": "No Existe"}
        
        response = client.put(f"/api/v1/products/{non_existent_id}", json=update_data)
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]

    def test_update_product_partial(self, client: TestClient, sample_product_data):
        """Debe permitir actualizaciones parciales."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Solo actualizar el nombre
        update_data = {"nombre": "Solo Nombre Cambiado"}
        
        response = client.put(f"/api/v1/products/{created_product['id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["nombre"] == "Solo Nombre Cambiado"
        assert data["descripcion"] == created_product["descripcion"]
        assert data["precio_base"] == created_product["precio_base"]


class TestProductsEndpointsDelete:
    """Pruebas para la eliminación de productos."""

    def test_delete_product_success(self, client: TestClient, sample_product_data):
        """Debe eliminar un producto exitosamente."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Eliminar el producto
        response = client.delete(f"/api/v1/products/{created_product['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == created_product["id"]
        assert data["success"] is True
        assert "eliminado exitosamente" in data["message"]
        
        # Verificar que el producto ya no se puede obtener
        get_response = client.get(f"/api/v1/products/{created_product['id']}")
        assert get_response.status_code == 404

    def test_delete_product_not_exists(self, client: TestClient):
        """Debe retornar 404 al eliminar un producto que no existe."""
        non_existent_id = str(uuid4())
        
        response = client.delete(f"/api/v1/products/{non_existent_id}")
        
        assert response.status_code == 404
        assert "no encontrado" in response.json()["detail"]


class TestProductsEndpointsStock:
    """Pruebas para la gestión de stock."""

    def test_update_stock_success(self, client: TestClient, sample_product_data):
        """Debe actualizar el stock exitosamente."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Actualizar el stock
        stock_data = {"stock": 75}
        
        response = client.patch(f"/api/v1/products/{created_product['id']}/stock", json=stock_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_id"] == created_product["id"]
        assert data["previous_stock"] == 100
        assert data["new_stock"] == 75
        assert "actualizado" in data["message"]

    def test_update_stock_negative_fails(self, client: TestClient, sample_product_data):
        """Debe fallar al intentar establecer stock negativo."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Intentar establecer stock negativo
        stock_data = {"stock": -5}
        
        response = client.patch(f"/api/v1/products/{created_product['id']}/stock", json=stock_data)
        
        assert response.status_code == 422  # Validation error por Pydantic
        assert "Input should be greater than or equal to 0" in str(response.json())

    def test_update_stock_zero_allowed(self, client: TestClient, sample_product_data):
        """Debe permitir stock en cero."""
        # Crear un producto
        create_response = client.post("/api/v1/products/", json=sample_product_data)
        assert create_response.status_code == 201
        created_product = create_response.json()
        
        # Establecer stock en cero
        stock_data = {"stock": 0}
        
        response = client.patch(f"/api/v1/products/{created_product['id']}/stock", json=stock_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["new_stock"] == 0

    def test_get_low_stock_products(self, client: TestClient, sample_product_data, sample_product_data_2):
        """Debe retornar productos con stock bajo."""
        # Crear productos
        create_response1 = client.post("/api/v1/products/", json=sample_product_data)
        create_response2 = client.post("/api/v1/products/", json=sample_product_data_2)
        
        assert create_response1.status_code == 201
        assert create_response2.status_code == 201
        
        product1 = create_response1.json()
        product2 = create_response2.json()
        
        # Actualizar stock para que estén bajo el umbral
        client.patch(f"/api/v1/products/{product1['id']}/stock", json={"stock": 5})  # Bajo umbral
        client.patch(f"/api/v1/products/{product2['id']}/stock", json={"stock": 15})  # Por encima del umbral
        
        # Obtener productos con stock bajo
        response = client.get("/api/v1/products/low-stock/?threshold=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["id"] == product1["id"]
        assert data[0]["stock"] == 5


class TestProductsEndpointsValidation:
    """Pruebas para validaciones específicas."""

    def test_create_product_price_validation(self, client: TestClient):
        """Debe validar que precio_publico >= precio_base."""
        invalid_data = {
            "sku": "PRICE-001",
            "nombre": "Producto Inválido",
            "precio_base": "20.00",
            "precio_publico": "15.00"  # Menor que precio_base
        }
        
        response = client.post("/api/v1/products/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error por Pydantic
        assert "precio público debe ser mayor o igual al precio base" in str(response.json())

    def test_invalid_uuid_format(self, client: TestClient):
        """Debe fallar con formato de UUID inválido."""
        response = client.get("/api/v1/products/invalid-uuid")
        
        assert response.status_code == 422  # Validation error

    def test_negative_stock_in_create(self, client: TestClient):
        """Debe fallar con stock negativo al crear."""
        invalid_data = {
            "sku": "STOCK-001",
            "nombre": "Producto Stock Negativo",
            "precio_base": "10.00",
            "precio_publico": "15.00",
            "stock": -10
        }
        
        response = client.post("/api/v1/products/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error 