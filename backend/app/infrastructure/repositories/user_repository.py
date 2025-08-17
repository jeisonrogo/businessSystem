"""
Implementación concreta del repositorio de usuarios usando SQLModel/SQLAlchemy.
Esta clase implementa la interfaz IUserRepository para acceso a datos de PostgreSQL.
"""

from typing import Optional, List
from uuid import UUID

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

from app.application.services.i_user_repository import IUserRepository
from app.domain.models.user import User, UserCreate, UserUpdate


class SQLUserRepository(IUserRepository):
    """
    Implementación concreta del repositorio de usuarios usando PostgreSQL.
    
    Esta clase implementa todos los métodos definidos en IUserRepository
    para realizar operaciones CRUD sobre la tabla users usando SQLModel.
    
    Características:
    - Manejo automático de transacciones
    - Hash de contraseñas con bcrypt
    - Validación de unicidad de emails
    - Soft delete (marca como inactivo en lugar de eliminar)
    """
    
    def __init__(self, session: Session):
        """
        Inicializa el repositorio con una sesión de base de datos.
        
        Args:
            session (Session): Sesión de SQLModel/SQLAlchemy
        """
        self.session = session
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _hash_password(self, password: str) -> str:
        """
        Hashea una contraseña usando bcrypt.
        
        Args:
            password (str): Contraseña en texto plano
            
        Returns:
            str: Contraseña hasheada
        """
        return self.pwd_context.hash(password)
    
    async def create(self, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario en la base de datos.
        
        Args:
            user_data (UserCreate): Datos del usuario a crear
            
        Returns:
            User: Usuario creado con ID asignado
            
        Raises:
            ValueError: Si el email ya existe
            Exception: Si ocurre un error durante la creación
        """
        try:
            # Verificar si el email ya existe
            if await self.exists_by_email(user_data.email):
                raise ValueError(f"Ya existe un usuario con el email: {user_data.email}")
            
            # Crear nuevo usuario con contraseña hasheada
            hashed_password = self._hash_password(user_data.password)
            
            db_user = User(
                email=user_data.email,
                nombre=user_data.nombre,
                rol=user_data.rol,
                hashed_password=hashed_password
            )
            
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            
            return db_user
            
        except ValueError as e:
            # Re-lanzar ValueError sin modificar (para emails duplicados)
            raise e
        except IntegrityError as e:
            self.session.rollback()
            if "users_email_key" in str(e):
                raise ValueError(f"Ya existe un usuario con el email: {user_data.email}")
            raise Exception(f"Error de integridad al crear usuario: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al crear usuario: {str(e)}")
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id (UUID): ID del usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        statement = select(User).where(User.id == user_id, User.is_active == True)
        result = self.session.exec(statement)
        return result.first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.
        
        Args:
            email (str): Email del usuario
            
        Returns:
            Optional[User]: Usuario encontrado o None
        """
        statement = select(User).where(User.email == email)
        result = self.session.exec(statement)
        return result.first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtiene una lista paginada de usuarios activos.
        
        Args:
            skip (int): Registros a omitir
            limit (int): Límite de registros
            
        Returns:
            List[User]: Lista de usuarios
        """
        statement = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = self.session.exec(statement)
        return list(result.all())
    
    async def update(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Actualiza un usuario existente.
        
        Args:
            user_id (UUID): ID del usuario
            user_data (UserUpdate): Datos de actualización
            
        Returns:
            Optional[User]: Usuario actualizado o None
            
        Raises:
            ValueError: Si el nuevo email ya existe
        """
        try:
            # Buscar el usuario
            db_user = await self.get_by_id(user_id)
            if not db_user:
                return None
            
            # Obtener datos de actualización excluyendo valores None
            update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
            
            # Verificar unicidad de email si se está actualizando
            if "email" in update_data:
                existing_user = await self.get_by_email(update_data["email"])
                if existing_user and existing_user.id != user_id:
                    raise ValueError(f"Ya existe un usuario con el email: {update_data['email']}")
            
            # Hashear nueva contraseña si se proporciona
            if "password" in update_data:
                update_data["hashed_password"] = self._hash_password(update_data["password"])
                del update_data["password"]
            
            # Aplicar actualizaciones
            for field, value in update_data.items():
                setattr(db_user, field, value)
            
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            
            return db_user
            
        except IntegrityError as e:
            self.session.rollback()
            if "users_email_key" in str(e):
                raise ValueError(f"Ya existe un usuario con el email especificado")
            raise Exception(f"Error de integridad al actualizar usuario: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al actualizar usuario: {str(e)}")
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario (soft delete).
        
        Args:
            user_id (UUID): ID del usuario
            
        Returns:
            bool: True si fue eliminado, False si no existe
        """
        try:
            db_user = await self.get_by_id(user_id)
            if not db_user:
                return False
            
            db_user.is_active = False
            self.session.add(db_user)
            self.session.commit()
            
            return True
            
        except Exception as e:
            self.session.rollback()
            raise Exception(f"Error al eliminar usuario: {str(e)}")
    
    async def exists_by_email(self, email: str) -> bool:
        """
        Verifica si existe un usuario con el email dado.
        
        Args:
            email (str): Email a verificar
            
        Returns:
            bool: True si existe
        """
        statement = select(User).where(User.email == email)
        result = self.session.exec(statement)
        return result.first() is not None
    
    async def count_total(self) -> int:
        """
        Cuenta el total de usuarios activos.
        
        Returns:
            int: Número total de usuarios activos
        """
        statement = select(User).where(User.is_active == True)
        result = self.session.exec(statement)
        return len(list(result.all()))
    
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
        try:
            # Construir la consulta base
            statement = select(User)
            
            # Aplicar filtros
            if search:
                search_filter = (
                    User.nombre.ilike(f"%{search}%") |
                    User.email.ilike(f"%{search}%")
                )
                statement = statement.where(search_filter)
            
            if role:
                statement = statement.where(User.rol == role)
            
            if is_active is not None:
                statement = statement.where(User.is_active == is_active)
            
            # Aplicar paginación
            offset = (page - 1) * limit
            statement = statement.offset(offset).limit(limit)
            
            # Ordenar por fecha de creación (más recientes primero)
            statement = statement.order_by(User.created_at.desc())
            
            # Ejecutar consulta
            result = self.session.exec(statement)
            return list(result.all())
            
        except Exception as e:
            raise Exception(f"Error al listar usuarios con filtros: {str(e)}") 