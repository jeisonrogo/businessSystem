from typing import Optional, List
from uuid import UUID

from app.application.services.i_product_repository import IProductRepository
from app.domain.models.product import Product, ProductCreate, ProductUpdate, ProductListResponse


class ProductNotFoundError(Exception):
    """Excepción lanzada cuando un producto no se encuentra."""
    pass


class DuplicateSKUError(Exception):
    """Excepción lanzada cuando se intenta crear un producto con SKU duplicado."""
    pass


class InvalidStockError(Exception):
    """Excepción lanzada cuando se intenta establecer stock negativo."""
    pass


class CreateProductUseCase:
    """
    Caso de uso para crear un nuevo producto.
    
    Implementa las reglas de negocio:
    - BR-02: SKU único que no puede ser duplicado
    """

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_data: ProductCreate) -> Product:
        """
        Crear un nuevo producto.
        
        Args:
            product_data: Datos del producto a crear
            
        Returns:
            Product: El producto creado
            
        Raises:
            DuplicateSKUError: Si el SKU ya existe
            ValueError: Si hay errores de validación en los datos
        """
        try:
            return await self.product_repository.create(product_data)
        except ValueError as e:
            if "Ya existe un producto con el SKU" in str(e):
                raise DuplicateSKUError(str(e))
            raise e


class GetProductUseCase:
    """Caso de uso para obtener un producto por ID."""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: UUID) -> Product:
        """
        Obtener un producto por su ID.
        
        Args:
            product_id: UUID del producto a buscar
            
        Returns:
            Product: El producto encontrado
            
        Raises:
            ProductNotFoundError: Si el producto no existe o está inactivo
        """
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Producto con ID {product_id} no encontrado")
        return product


class GetProductBySKUUseCase:
    """Caso de uso para obtener un producto por SKU."""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, sku: str) -> Product:
        """
        Obtener un producto por su SKU.
        
        Args:
            sku: SKU del producto a buscar
            
        Returns:
            Product: El producto encontrado
            
        Raises:
            ProductNotFoundError: Si el producto no existe o está inactivo
        """
        product = await self.product_repository.get_by_sku(sku)
        if not product:
            raise ProductNotFoundError(f"Producto con SKU '{sku}' no encontrado")
        return product


class ListProductsUseCase:
    """Caso de uso para listar productos con paginación y filtros."""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(
        self,
        page: int = 1,
        limit: int = 100,
        search: Optional[str] = None,
        only_active: bool = True
    ) -> ProductListResponse:
        """
        Obtener lista paginada de productos.
        
        Args:
            page: Número de página (empezando en 1)
            limit: Productos por página (máximo 100)
            search: Término de búsqueda para filtrar por nombre o SKU
            only_active: Si True, solo retorna productos activos
            
        Returns:
            ProductListResponse: Lista paginada con metadatos
        """
        # Validar parámetros de paginación
        if page < 1:
            page = 1
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10

        skip = (page - 1) * limit
        
        # Obtener productos y conteo total
        products = await self.product_repository.get_all(
            skip=skip, 
            limit=limit, 
            search=search, 
            only_active=only_active
        )
        total = await self.product_repository.count_total(
            search=search, 
            only_active=only_active
        )
        
        # Calcular metadatos de paginación
        total_pages = (total + limit - 1) // limit  # Ceiling division
        has_next = page < total_pages
        has_prev = page > 1
        
        return ProductListResponse(
            products=products,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev
        )


class UpdateProductUseCase:
    """
    Caso de uso para actualizar un producto existente.
    
    Implementa las reglas de negocio:
    - BR-02: SKU no se puede modificar una vez creado
    - BR-04: Cambios de precios se registran en historial (futuro)
    """

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: UUID, product_data: ProductUpdate) -> Product:
        """
        Actualizar un producto existente.
        
        Args:
            product_id: UUID del producto a actualizar
            product_data: Datos a actualizar
            
        Returns:
            Product: El producto actualizado
            
        Raises:
            ProductNotFoundError: Si el producto no existe
            ValueError: Si hay errores de validación
        """
        # Verificar que el producto existe
        existing_product = await self.product_repository.get_by_id(product_id)
        if not existing_product:
            raise ProductNotFoundError(f"Producto con ID {product_id} no encontrado")
        
        # TODO: Implementar BR-04 - Historial de precios cuando cambie precio_base o precio_publico
        # if product_data.precio_base != existing_product.precio_base or 
        #    product_data.precio_publico != existing_product.precio_publico:
        #     await self.price_history_repository.create_price_change_record(...)
        
        updated_product = await self.product_repository.update(product_id, product_data)
        if not updated_product:
            raise ProductNotFoundError(f"Producto con ID {product_id} no encontrado")
        
        return updated_product


class DeleteProductUseCase:
    """Caso de uso para eliminar un producto (soft delete)."""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: UUID) -> bool:
        """
        Eliminar un producto (soft delete).
        
        Args:
            product_id: UUID del producto a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
            
        Raises:
            ProductNotFoundError: Si el producto no existe
        """
        success = await self.product_repository.delete(product_id)
        if not success:
            raise ProductNotFoundError(f"Producto con ID {product_id} no encontrado")
        return success


class UpdateProductStockUseCase:
    """
    Caso de uso para actualizar el stock de un producto.
    
    Implementa las reglas de negocio:
    - BR-01: Stock no puede ser negativo
    """

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, product_id: UUID, new_stock: int) -> Product:
        """
        Actualizar el stock de un producto.
        
        Args:
            product_id: UUID del producto
            new_stock: Nueva cantidad de stock
            
        Returns:
            Product: El producto con el stock actualizado
            
        Raises:
            ProductNotFoundError: Si el producto no existe
            InvalidStockError: Si el stock es negativo
        """
        if new_stock < 0:
            raise InvalidStockError("El stock no puede ser negativo (BR-01)")
        
        try:
            updated_product = await self.product_repository.update_stock(product_id, new_stock)
            if not updated_product:
                raise ProductNotFoundError(f"Producto con ID {product_id} no encontrado")
            return updated_product
        except ValueError as e:
            raise InvalidStockError(str(e))


class GetLowStockProductsUseCase:
    """Caso de uso para obtener productos with stock bajo."""

    def __init__(self, product_repository: IProductRepository):
        self.product_repository = product_repository

    async def execute(self, threshold: int = 10) -> List[Product]:
        """
        Obtener productos con stock bajo el umbral especificado.
        
        Args:
            threshold: Umbral mínimo de stock (default: 10)
            
        Returns:
            List[Product]: Lista de productos con stock bajo
        """
        if threshold < 0:
            threshold = 0
        
        return await self.product_repository.get_low_stock_products(threshold) 