"""
Pruebas de integración para SQLProductRepository.
Prueba todas las operaciones CRUD y reglas de negocio del repositorio de productos.
"""

import pytest
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.product import Product, ProductCreate, ProductUpdate
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
def sample_product_data():
    """Datos de ejemplo para crear productos."""
    return ProductCreate(
        sku="TEST-001",
        nombre="Producto de Prueba",
        descripcion="Descripción del producto de prueba",
        url_foto="https://example.com/image.jpg",
        precio_base=Decimal("10.00"),
        precio_publico=Decimal("15.00"),
        stock=100
    )


@pytest.fixture
def sample_product_data_2():
    """Segundo conjunto de datos de ejemplo para pruebas."""
    return ProductCreate(
        sku="TEST-002",
        nombre="Segundo Producto",
        descripcion="Otro producto de prueba",
        precio_base=Decimal("20.00"),
        precio_publico=Decimal("25.00"),
        stock=50
    )


class TestProductRepositoryCreate:
    """Pruebas para la creación de productos."""

    @pytest.mark.asyncio
    async def test_create_product_success(self, product_repository, sample_product_data):
        """Debe crear un producto exitosamente."""
        product = await product_repository.create(sample_product_data)
        
        assert product.id is not None
        assert isinstance(product.id, UUID)
        assert product.sku == sample_product_data.sku
        assert product.nombre == sample_product_data.nombre
        assert product.descripcion == sample_product_data.descripcion
        assert product.url_foto == sample_product_data.url_foto
        assert product.precio_base == sample_product_data.precio_base
        assert product.precio_publico == sample_product_data.precio_publico
        assert product.stock == sample_product_data.stock
        assert product.is_active is True
        assert product.created_at is not None

    @pytest.mark.asyncio
    async def test_create_product_duplicate_sku_fails(self, product_repository, sample_product_data):
        """Debe fallar al crear un producto con SKU duplicado (BR-02)."""
        # Crear el primer producto
        await product_repository.create(sample_product_data)
        
        # Intentar crear otro producto con el mismo SKU
        duplicate_data = ProductCreate(
            sku=sample_product_data.sku,
            nombre="Producto Duplicado",
            precio_base=Decimal("5.00"),
            precio_publico=Decimal("8.00")
        )
        
        with pytest.raises(ValueError, match="Ya existe un producto con el SKU"):
            await product_repository.create(duplicate_data)

    @pytest.mark.asyncio
    async def test_create_product_minimal_data(self, product_repository):
        """Debe crear un producto con datos mínimos."""
        minimal_data = ProductCreate(
            sku="MIN-001",
            nombre="Producto Mínimo",
            precio_base=Decimal("1.00"),
            precio_publico=Decimal("2.00")
        )
        
        product = await product_repository.create(minimal_data)
        
        assert product.sku == "MIN-001"
        assert product.nombre == "Producto Mínimo"
        assert product.descripcion is None
        assert product.url_foto is None
        assert product.stock == 0
        assert product.is_active is True


class TestProductRepositoryRead:
    """Pruebas para la lectura de productos."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, product_repository, sample_product_data):
        """Debe obtener un producto por ID cuando existe."""
        created_product = await product_repository.create(sample_product_data)
        
        found_product = await product_repository.get_by_id(created_product.id)
        
        assert found_product is not None
        assert found_product.id == created_product.id
        assert found_product.sku == sample_product_data.sku

    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, product_repository):
        """Debe retornar None cuando el producto no existe."""
        non_existent_id = uuid4()
        
        product = await product_repository.get_by_id(non_existent_id)
        
        assert product is None

    @pytest.mark.asyncio
    async def test_get_by_id_inactive_product(self, product_repository, sample_product_data):
        """Debe retornar None para productos inactivos."""
        created_product = await product_repository.create(sample_product_data)
        await product_repository.delete(created_product.id)
        
        product = await product_repository.get_by_id(created_product.id)
        
        assert product is None

    @pytest.mark.asyncio
    async def test_get_by_sku_exists(self, product_repository, sample_product_data):
        """Debe obtener un producto por SKU cuando existe."""
        await product_repository.create(sample_product_data)
        
        found_product = await product_repository.get_by_sku(sample_product_data.sku)
        
        assert found_product is not None
        assert found_product.sku == sample_product_data.sku

    @pytest.mark.asyncio
    async def test_get_by_sku_not_exists(self, product_repository):
        """Debe retornar None cuando el SKU no existe."""
        product = await product_repository.get_by_sku("NON-EXISTENT")
        
        assert product is None


class TestProductRepositoryList:
    """Pruebas para listar productos."""

    @pytest.mark.asyncio
    async def test_get_all_empty(self, product_repository):
        """Debe retornar lista vacía cuando no hay productos."""
        products = await product_repository.get_all()
        
        assert products == []

    @pytest.mark.asyncio
    async def test_get_all_with_products(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe retornar todos los productos activos."""
        await product_repository.create(sample_product_data)
        await product_repository.create(sample_product_data_2)
        
        products = await product_repository.get_all()
        
        assert len(products) == 2
        skus = [p.sku for p in products]
        assert sample_product_data.sku in skus
        assert sample_product_data_2.sku in skus

    @pytest.mark.asyncio
    async def test_get_all_pagination(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe respetar los parámetros de paginación."""
        await product_repository.create(sample_product_data)
        await product_repository.create(sample_product_data_2)
        
        # Primera página con límite de 1
        products_page1 = await product_repository.get_all(skip=0, limit=1)
        assert len(products_page1) == 1
        
        # Segunda página
        products_page2 = await product_repository.get_all(skip=1, limit=1)
        assert len(products_page2) == 1
        
        # Verificar que son productos diferentes
        assert products_page1[0].id != products_page2[0].id

    @pytest.mark.asyncio
    async def test_get_all_search(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe filtrar productos por término de búsqueda."""
        await product_repository.create(sample_product_data)
        await product_repository.create(sample_product_data_2)
        
        # Buscar por nombre
        products = await product_repository.get_all(search="Segundo")
        assert len(products) == 1
        assert products[0].sku == "TEST-002"
        
        # Buscar por SKU
        products = await product_repository.get_all(search="TEST-001")
        assert len(products) == 1
        assert products[0].sku == "TEST-001"

    @pytest.mark.asyncio
    async def test_get_all_only_active(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe filtrar solo productos activos por defecto."""
        product1 = await product_repository.create(sample_product_data)
        await product_repository.create(sample_product_data_2)
        
        # Eliminar un producto (soft delete)
        await product_repository.delete(product1.id)
        
        # Solo debe retornar productos activos
        products = await product_repository.get_all(only_active=True)
        assert len(products) == 1
        assert products[0].sku == "TEST-002"
        
        # Debe retornar todos los productos si only_active=False
        all_products = await product_repository.get_all(only_active=False)
        assert len(all_products) == 2


class TestProductRepositoryUpdate:
    """Pruebas para la actualización de productos."""

    @pytest.mark.asyncio
    async def test_update_product_success(self, product_repository, sample_product_data):
        """Debe actualizar un producto exitosamente."""
        created_product = await product_repository.create(sample_product_data)
        
        update_data = ProductUpdate(
            nombre="Producto Actualizado",
            descripcion="Descripción actualizada",
            precio_base=Decimal("12.00")
        )
        
        updated_product = await product_repository.update(created_product.id, update_data)
        
        assert updated_product is not None
        assert updated_product.id == created_product.id
        assert updated_product.sku == created_product.sku  # SKU no debe cambiar
        assert updated_product.nombre == "Producto Actualizado"
        assert updated_product.descripcion == "Descripción actualizada"
        assert updated_product.precio_base == Decimal("12.00")
        assert updated_product.precio_publico == created_product.precio_publico  # No cambió

    @pytest.mark.asyncio
    async def test_update_product_not_exists(self, product_repository):
        """Debe retornar None al actualizar un producto que no existe."""
        non_existent_id = uuid4()
        update_data = ProductUpdate(nombre="No Existe")
        
        result = await product_repository.update(non_existent_id, update_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_product_partial(self, product_repository, sample_product_data):
        """Debe permitir actualizaciones parciales."""
        created_product = await product_repository.create(sample_product_data)
        
        # Solo actualizar el nombre
        update_data = ProductUpdate(nombre="Solo Nombre Cambiado")
        
        updated_product = await product_repository.update(created_product.id, update_data)
        
        assert updated_product.nombre == "Solo Nombre Cambiado"
        assert updated_product.descripcion == created_product.descripcion
        assert updated_product.precio_base == created_product.precio_base


class TestProductRepositoryDelete:
    """Pruebas para la eliminación de productos."""

    @pytest.mark.asyncio
    async def test_delete_product_success(self, product_repository, sample_product_data):
        """Debe eliminar un producto exitosamente (soft delete)."""
        created_product = await product_repository.create(sample_product_data)
        
        success = await product_repository.delete(created_product.id)
        
        assert success is True
        
        # El producto debe existir pero estar inactivo
        product = await product_repository.get_by_id(created_product.id)
        assert product is None  # get_by_id solo retorna productos activos

    @pytest.mark.asyncio
    async def test_delete_product_not_exists(self, product_repository):
        """Debe retornar False al eliminar un producto que no existe."""
        non_existent_id = uuid4()
        
        success = await product_repository.delete(non_existent_id)
        
        assert success is False


class TestProductRepositoryStock:
    """Pruebas para la gestión de stock."""

    @pytest.mark.asyncio
    async def test_update_stock_success(self, product_repository, sample_product_data):
        """Debe actualizar el stock exitosamente."""
        created_product = await product_repository.create(sample_product_data)
        original_stock = created_product.stock
        
        updated_product = await product_repository.update_stock(created_product.id, 75)
        
        assert updated_product is not None
        assert updated_product.stock == 75
        assert updated_product.stock != original_stock

    @pytest.mark.asyncio
    async def test_update_stock_negative_fails(self, product_repository, sample_product_data):
        """Debe fallar al intentar establecer stock negativo (BR-01)."""
        created_product = await product_repository.create(sample_product_data)
        
        with pytest.raises(ValueError, match="El stock no puede ser negativo"):
            await product_repository.update_stock(created_product.id, -5)

    @pytest.mark.asyncio
    async def test_update_stock_zero_allowed(self, product_repository, sample_product_data):
        """Debe permitir stock en cero."""
        created_product = await product_repository.create(sample_product_data)
        
        updated_product = await product_repository.update_stock(created_product.id, 0)
        
        assert updated_product is not None
        assert updated_product.stock == 0

    @pytest.mark.asyncio
    async def test_get_low_stock_products(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe retornar productos con stock bajo."""
        # Crear productos con diferentes niveles de stock
        product1 = await product_repository.create(sample_product_data)
        product2 = await product_repository.create(sample_product_data_2)
        
        # Actualizar stock para que estén bajo el umbral
        await product_repository.update_stock(product1.id, 5)  # Bajo umbral
        await product_repository.update_stock(product2.id, 15)  # Por encima del umbral
        
        low_stock_products = await product_repository.get_low_stock_products(threshold=10)
        
        assert len(low_stock_products) == 1
        assert low_stock_products[0].id == product1.id
        assert low_stock_products[0].stock == 5


class TestProductRepositoryUtilities:
    """Pruebas para métodos utilitarios."""

    @pytest.mark.asyncio
    async def test_exists_by_sku_true(self, product_repository, sample_product_data):
        """Debe retornar True cuando el SKU existe."""
        await product_repository.create(sample_product_data)
        
        exists = await product_repository.exists_by_sku(sample_product_data.sku)
        
        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_by_sku_false(self, product_repository):
        """Debe retornar False cuando el SKU no existe."""
        exists = await product_repository.exists_by_sku("NON-EXISTENT")
        
        assert exists is False

    @pytest.mark.asyncio
    async def test_exists_by_sku_exclude_id(self, product_repository, sample_product_data):
        """Debe excluir un ID específico de la verificación."""
        created_product = await product_repository.create(sample_product_data)
        
        # No debe existir si excluimos el ID del producto creado
        exists = await product_repository.exists_by_sku(
            sample_product_data.sku, 
            exclude_id=created_product.id
        )
        
        assert exists is False

    @pytest.mark.asyncio
    async def test_count_total(self, product_repository, sample_product_data, sample_product_data_2):
        """Debe contar el total de productos correctamente."""
        initial_count = await product_repository.count_total()
        assert initial_count == 0
        
        await product_repository.create(sample_product_data)
        await product_repository.create(sample_product_data_2)
        
        total_count = await product_repository.count_total()
        assert total_count == 2
        
        # Contar con búsqueda
        search_count = await product_repository.count_total(search="Segundo")
        assert search_count == 1 