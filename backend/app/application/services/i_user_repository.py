"""
Interfaz del repositorio de usuarios.
Define el contrato que debe implementar cualquier repositorio de usuarios,
siguiendo el patrón Repository y el principio de inversión de dependencias.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from app.domain.models.user import User, UserCreate, UserUpdate


class IUserRepository(ABC):
    """
    Interfaz abstracta para el repositorio de usuarios.
    
    Esta interfaz define los métodos que debe implementar cualquier
    repositorio concreto de usuarios, permitiendo la inversión de
    dependencias y facilitando el testing con mocks.
    
    Principios aplicados:
    - Dependency Inversion Principle (DIP)
    - Repository Pattern
    - Interface Segregation Principle (ISP)
    """
    
    @abstractmethod
    async def create(self, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario en el sistema.
        
        Args:
            user_data (UserCreate): Datos para crear el usuario
            
        Returns:
            User: Usuario creado con ID asignado
            
        Raises:
            ValueError: Si el email ya existe
            Exception: Si ocurre un error durante la creación
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id (UUID): ID del usuario a buscar
            
        Returns:
            Optional[User]: Usuario encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email (str): Email del usuario a buscar
            
        Returns:
            Optional[User]: Usuario encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtiene una lista paginada de usuarios.
        
        Args:
            skip (int): Número de registros a omitir
            limit (int): Número máximo de registros a retornar
            
        Returns:
            List[User]: Lista de usuarios
        """
        pass
    
    @abstractmethod
    async def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Actualiza un usuario existente.
        
        Args:
            user_id (UUID): ID del usuario a actualizar
            user_data (UserUpdate): Datos de actualización
            
        Returns:
            Optional[User]: Usuario actualizado o None si no existe
            
        Raises:
            ValueError: Si el nuevo email ya existe (para otro usuario)
            Exception: Si ocurre un error durante la actualización
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario (soft delete - marca como inactivo).
        
        Args:
            user_id (UUID): ID del usuario a eliminar
            
        Returns:
            bool: True si el usuario fue eliminado, False si no existe
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email (str): Email a verificar
            
        Returns:
            bool: True si existe un usuario con ese email
        """
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """
        Cuenta el total de usuarios activos en el sistema.
        
        Returns:
            int: Número total de usuarios activos
        """
        pass
    
    @abstractmethod
    async def list_with_filters(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        Lista usuarios aplicando filtros y paginación.
        
        Args:
            page: Número de página
            limit: Registros por página
            search: Texto para buscar en nombre y email
            role: Filtrar por rol específico
            is_active: Filtrar por estado activo
            
        Returns:
            List[User]: Lista de usuarios filtrados
        """
        pass 