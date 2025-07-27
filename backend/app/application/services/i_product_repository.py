from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.models.product import Product, ProductCreate, ProductUpdate


class IProductRepository(ABC):
    """
    Interfaz del repositorio para la gestión de productos.
    
    Define los métodos que debe implementar cualquier repositorio concreto
    que maneje la persistencia de productos, siguiendo el patrón Repository
    y el principio de Inversión de Dependencias.
    """

    @abstractmethod
    async def create(self, product_data: ProductCreate) -> Product:
        """
        Crear un nuevo producto.
        
        Args:
            product_data: Datos del producto a crear
            
        Returns:
            Product: El producto creado con su ID asignado
            
        Raises:
            ValueError: Si el SKU ya existe (BR-02: SKU único)
            Exception: En caso de error en la base de datos
        """
        pass

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Obtener un producto por su ID.
        
        Args:
            product_id: UUID del producto a buscar
            
        Returns:
            Product si existe y está activo, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Obtener un producto por su SKU.
        
        Args:
            sku: SKU del producto a buscar
            
        Returns:
            Product si existe y está activo, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        only_active: bool = True
    ) -> List[Product]:
        """
        Obtener lista paginada de productos.
        
        Args:
            skip: Número de productos a omitir (offset)
            limit: Número máximo de productos a retornar
            search: Término de búsqueda para filtrar por nombre o SKU
            only_active: Si True, solo retorna productos activos
            
        Returns:
            Lista de productos que cumplen los criterios
        """
        pass

    @abstractmethod
    async def update(self, product_id: UUID, product_data: ProductUpdate) -> Optional[Product]:
        """
        Actualizar un producto existente.
        
        Args:
            product_id: UUID del producto a actualizar
            product_data: Datos a actualizar (campos opcionales)
            
        Returns:
            Product actualizado si existe, None si no se encuentra
            
        Raises:
            ValueError: Si hay errores de validación de negocio
            Exception: En caso de error en la base de datos
            
        Note:
            - El SKU no se puede modificar (BR-02)
            - El stock se modifica a través de movimientos de inventario
        """
        pass

    @abstractmethod
    async def delete(self, product_id: UUID) -> bool:
        """
        Eliminar un producto (soft delete).
        
        Args:
            product_id: UUID del producto a eliminar
            
        Returns:
            True si se eliminó exitosamente, False si no se encontró
            
        Note:
            Implementa soft delete marcando is_active = False
        """
        pass

    @abstractmethod
    async def exists_by_sku(self, sku: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Verificar si existe un producto con el SKU dado.
        
        Args:
            sku: SKU a verificar
            exclude_id: ID del producto a excluir de la búsqueda (útil para updates)
            
        Returns:
            True si existe un producto con ese SKU, False en caso contrario
        """
        pass

    @abstractmethod
    async def count_total(self, search: Optional[str] = None, only_active: bool = True) -> int:
        """
        Contar el total de productos que cumplen los criterios.
        
        Args:
            search: Término de búsqueda para filtrar
            only_active: Si True, solo cuenta productos activos
            
        Returns:
            Número total de productos
        """
        pass

    @abstractmethod
    async def update_stock(self, product_id: UUID, new_stock: int) -> Optional[Product]:
        """
        Actualizar solo el stock de un producto.
        
        Args:
            product_id: UUID del producto
            new_stock: Nueva cantidad de stock (debe ser >= 0)
            
        Returns:
            Product actualizado si existe, None si no se encuentra
            
        Raises:
            ValueError: Si new_stock < 0 (BR-01: stock no negativo)
            
        Note:
            Este método será usado por el servicio de inventario
        """
        pass

    @abstractmethod
    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """
        Obtener productos con stock bajo.
        
        Args:
            threshold: Umbral mínimo de stock
            
        Returns:
            Lista de productos activos con stock <= threshold
        """
        pass 