from typing import Optional, List
from uuid import UUID

from sqlmodel import Session, select, and_, or_, func
from sqlalchemy.exc import IntegrityError

from app.application.services.i_product_repository import IProductRepository
from app.domain.models.product import Product, ProductCreate, ProductUpdate


class SQLProductRepository(IProductRepository):
    """
    Implementación del repositorio de productos usando SQLModel y PostgreSQL.
    
    Implementa todas las operaciones CRUD y métodos auxiliares definidos
    en IProductRepository, aplicando las reglas de negocio correspondientes.
    """

    def __init__(self, session: Session):
        self.session = session

    async def create(self, product_data: ProductCreate) -> Product:
        """
        Crear un nuevo producto.
        
        Implementa BR-02: SKU único que no puede ser duplicado.
        """
        try:
            # Verificar que el SKU no exista
            if await self.exists_by_sku(product_data.sku):
                raise ValueError(f"Ya existe un producto con el SKU: {product_data.sku}")
            
            # Crear el producto
            product = Product(**product_data.model_dump())
            
            self.session.add(product)
            self.session.commit()
            self.session.refresh(product)
            
            return product
            
        except ValueError as e:
            self.session.rollback()
            raise e
        except IntegrityError as e:
            self.session.rollback()
            if "sku" in str(e.orig).lower():
                raise ValueError(f"Ya existe un producto con el SKU: {product_data.sku}")
            raise Exception(f"Error de integridad al crear el producto: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al crear el producto: {str(e)}")

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Obtener un producto por su ID.
        
        Solo retorna productos activos.
        """
        try:
            statement = select(Product).where(
                and_(
                    Product.id == product_id,
                    Product.is_active == True
                )
            )
            result = self.session.exec(statement)
            return result.first()
        except Exception as e:
            raise Exception(f"Error al obtener el producto por ID: {str(e)}")

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Obtener un producto por su SKU.
        
        Solo retorna productos activos.
        """
        try:
            statement = select(Product).where(
                and_(
                    Product.sku == sku,
                    Product.is_active == True
                )
            )
            result = self.session.exec(statement)
            return result.first()
        except Exception as e:
            raise Exception(f"Error al obtener el producto por SKU: {str(e)}")

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        only_active: bool = True
    ) -> List[Product]:
        """
        Obtener lista paginada de productos con filtros opcionales.
        """
        try:
            statement = select(Product)
            
            # Filtro por estado activo
            if only_active:
                statement = statement.where(Product.is_active == True)
            
            # Filtro de búsqueda por nombre o SKU
            if search:
                search_filter = or_(
                    Product.nombre.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%")
                )
                statement = statement.where(search_filter)
            
            # Paginación y ordenamiento
            statement = statement.order_by(Product.nombre).offset(skip).limit(limit)
            
            result = self.session.exec(statement)
            return result.all()
        except Exception as e:
            raise Exception(f"Error al obtener la lista de productos: {str(e)}")

    async def update(self, product_id: UUID, product_data: ProductUpdate) -> Optional[Product]:
        """
        Actualizar un producto existente.
        
        Implementa BR-02: SKU no se puede modificar una vez creado.
        """
        try:
            # Obtener el producto actual
            product = await self.get_by_id(product_id)
            if not product:
                return None
            
            # Aplicar los cambios especificados
            update_data = product_data.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                setattr(product, field, value)
            
            self.session.add(product)
            self.session.commit()
            self.session.refresh(product)
            
            return product
            
        except ValueError as e:
            self.session.rollback()
            raise e
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al actualizar el producto: {str(e)}")

    async def delete(self, product_id: UUID) -> bool:
        """
        Eliminar un producto (soft delete).
        
        Marca el producto como inactivo en lugar de eliminarlo físicamente.
        """
        try:
            product = await self.get_by_id(product_id)
            if not product:
                return False
            
            product.is_active = False
            self.session.add(product)
            self.session.commit()
            
            return True
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al eliminar el producto: {str(e)}")

    async def exists_by_sku(self, sku: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Verificar si existe un producto con el SKU dado.
        
        Incluye productos tanto activos como inactivos.
        """
        try:
            statement = select(Product).where(Product.sku == sku)
            
            if exclude_id:
                statement = statement.where(Product.id != exclude_id)
            
            result = self.session.exec(statement)
            return result.first() is not None
        except Exception as e:
            raise Exception(f"Error al verificar existencia del SKU: {str(e)}")

    async def count_total(self, search: Optional[str] = None, only_active: bool = True) -> int:
        """
        Contar el total de productos que cumplen los criterios.
        """
        try:
            statement = select(func.count(Product.id))
            
            # Filtro por estado activo
            if only_active:
                statement = statement.where(Product.is_active == True)
            
            # Filtro de búsqueda
            if search:
                search_filter = or_(
                    Product.nombre.ilike(f"%{search}%"),
                    Product.sku.ilike(f"%{search}%")
                )
                statement = statement.where(search_filter)
            
            result = self.session.exec(statement)
            return result.one()
        except Exception as e:
            raise Exception(f"Error al contar productos: {str(e)}")

    async def update_stock(self, product_id: UUID, new_stock: int) -> Optional[Product]:
        """
        Actualizar solo el stock de un producto.
        
        Implementa BR-01: Stock no puede ser negativo.
        """
        try:
            if new_stock < 0:
                raise ValueError("El stock no puede ser negativo (BR-01)")
            
            product = await self.get_by_id(product_id)
            if not product:
                return None
            
            product.stock = new_stock
            self.session.add(product)
            self.session.commit()
            self.session.refresh(product)
            
            return product
            
        except ValueError as e:
            self.session.rollback()
            raise e
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al actualizar el stock: {str(e)}")

    async def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """
        Obtener productos con stock bajo.
        """
        try:
            statement = select(Product).where(
                and_(
                    Product.stock <= threshold,
                    Product.is_active == True
                )
            ).order_by(Product.stock, Product.nombre)
            
            result = self.session.exec(statement)
            return result.all()
        except Exception as e:
            raise Exception(f"Error al obtener productos con stock bajo: {str(e)}") 