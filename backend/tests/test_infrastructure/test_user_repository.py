"""
Pruebas de integración para SQLUserRepository.
Estas pruebas verifican que el repositorio de usuarios funciona correctamente
con una base de datos real de PostgreSQL.
"""

import pytest
import asyncio
from uuid import uuid4
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from app.domain.models.user import User, UserCreate, UserUpdate, UserRole
from app.infrastructure.repositories.user_repository import SQLUserRepository


# Configuración de base de datos de prueba en memoria
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """
    Crea un engine de base de datos SQLite en memoria para las pruebas.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """
    Proporciona una sesión de base de datos para cada prueba.
    """
    with Session(engine) as session:
        yield session


@pytest.fixture
def user_repository(session):
    """
    Crea una instancia del repositorio de usuarios para las pruebas.
    """
    return SQLUserRepository(session)


@pytest.fixture
def sample_user_data():
    """
    Datos de ejemplo para crear un usuario.
    """
    return UserCreate(
        email="test@example.com",
        nombre="Usuario Test",
        rol=UserRole.VENDEDOR,
        password="password123"
    )


class TestSQLUserRepository:
    """
    Suite de pruebas para SQLUserRepository.
    """
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, sample_user_data):
        """
        Prueba la creación exitosa de un usuario.
        """
        # Act
        created_user = await user_repository.create(sample_user_data)
        
        # Assert
        assert created_user.id is not None
        assert created_user.email == sample_user_data.email
        assert created_user.nombre == sample_user_data.nombre
        assert created_user.rol == sample_user_data.rol
        assert created_user.is_active is True
        assert created_user.hashed_password != sample_user_data.password  # Debe estar hasheada
        assert created_user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_repository, sample_user_data):
        """
        Prueba que no se puede crear un usuario con email duplicado.
        """
        # Arrange
        await user_repository.create(sample_user_data)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Ya existe un usuario con el email"):
            await user_repository.create(sample_user_data)
    
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, user_repository, sample_user_data):
        """
        Prueba la obtención de un usuario por ID.
        """
        # Arrange
        created_user = await user_repository.create(sample_user_data)
        
        # Act
        found_user = await user_repository.get_by_id(created_user.id)
        
        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, user_repository):
        """
        Prueba que retorna None cuando no se encuentra un usuario por ID.
        """
        # Act
        found_user = await user_repository.get_by_id(uuid4())
        
        # Assert
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_by_email_success(self, user_repository, sample_user_data):
        """
        Prueba la obtención de un usuario por email.
        """
        # Arrange
        created_user = await user_repository.create(sample_user_data)
        
        # Act
        found_user = await user_repository.get_by_email(sample_user_data.email)
        
        # Assert
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == sample_user_data.email
    
    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repository):
        """
        Prueba que retorna None cuando no se encuentra un usuario por email.
        """
        # Act
        found_user = await user_repository.get_by_email("nonexistent@example.com")
        
        # Assert
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository, sample_user_data):
        """
        Prueba la obtención de todos los usuarios.
        """
        # Arrange
        user1_data = UserCreate(
            email="user1@example.com",
            nombre="Usuario 1",
            rol=UserRole.VENDEDOR,
            password="password123"
        )
        user2_data = UserCreate(
            email="user2@example.com",
            nombre="Usuario 2",
            rol=UserRole.ADMINISTRADOR,
            password="password123"
        )
        
        await user_repository.create(user1_data)
        await user_repository.create(user2_data)
        
        # Act
        users = await user_repository.get_all(skip=0, limit=10)
        
        # Assert
        assert len(users) == 2
        emails = [user.email for user in users]
        assert "user1@example.com" in emails
        assert "user2@example.com" in emails
    
    @pytest.mark.asyncio
    async def test_get_all_users_pagination(self, user_repository):
        """
        Prueba la paginación en la obtención de usuarios.
        """
        # Arrange - Crear 3 usuarios
        for i in range(3):
            user_data = UserCreate(
                email=f"user{i}@example.com",
                nombre=f"Usuario {i}",
                rol=UserRole.VENDEDOR,
                password="password123"
            )
            await user_repository.create(user_data)
        
        # Act
        first_page = await user_repository.get_all(skip=0, limit=2)
        second_page = await user_repository.get_all(skip=2, limit=2)
        
        # Assert
        assert len(first_page) == 2
        assert len(second_page) == 1
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_repository, sample_user_data):
        """
        Prueba la actualización exitosa de un usuario.
        """
        # Arrange
        created_user = await user_repository.create(sample_user_data)
        update_data = UserUpdate(
            nombre="Usuario Actualizado",
            rol=UserRole.ADMINISTRADOR
        )
        
        # Act
        updated_user = await user_repository.update(created_user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.nombre == "Usuario Actualizado"
        assert updated_user.rol == UserRole.ADMINISTRADOR
        assert updated_user.email == sample_user_data.email  # No cambió
    
    @pytest.mark.asyncio
    async def test_update_user_password(self, user_repository, sample_user_data):
        """
        Prueba la actualización de contraseña de un usuario.
        """
        # Arrange
        created_user = await user_repository.create(sample_user_data)
        original_password_hash = created_user.hashed_password
        update_data = UserUpdate(password="newpassword123")
        
        # Act
        updated_user = await user_repository.update(created_user.id, update_data)
        
        # Assert
        assert updated_user is not None
        assert updated_user.hashed_password != original_password_hash
        assert updated_user.hashed_password != "newpassword123"  # Debe estar hasheada
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_repository):
        """
        Prueba que retorna None al intentar actualizar un usuario inexistente.
        """
        # Act
        update_data = UserUpdate(nombre="Usuario Inexistente")
        updated_user = await user_repository.update(uuid4(), update_data)
        
        # Assert
        assert updated_user is None
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, user_repository, sample_user_data):
        """
        Prueba la eliminación exitosa de un usuario (soft delete).
        """
        # Arrange
        created_user = await user_repository.create(sample_user_data)
        
        # Act
        result = await user_repository.delete(created_user.id)
        
        # Assert
        assert result is True
        
        # Verificar que el usuario ya no es encontrado en búsquedas normales
        found_user = await user_repository.get_by_id(created_user.id)
        assert found_user is None
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, user_repository):
        """
        Prueba que retorna False al intentar eliminar un usuario inexistente.
        """
        # Act
        result = await user_repository.delete(uuid4())
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_exists_by_email(self, user_repository, sample_user_data):
        """
        Prueba la verificación de existencia de un usuario por email.
        """
        # Arrange
        await user_repository.create(sample_user_data)
        
        # Act & Assert
        assert await user_repository.exists_by_email(sample_user_data.email) is True
        assert await user_repository.exists_by_email("nonexistent@example.com") is False
    
    @pytest.mark.asyncio
    async def test_count_total(self, user_repository, sample_user_data):
        """
        Prueba el conteo total de usuarios activos.
        """
        # Arrange
        initial_count = await user_repository.count_total()
        
        # Crear dos usuarios
        user1_data = UserCreate(
            email="user1@example.com",
            nombre="Usuario 1",
            rol=UserRole.VENDEDOR,
            password="password123"
        )
        user2_data = UserCreate(
            email="user2@example.com",
            nombre="Usuario 2",
            rol=UserRole.CONTADOR,
            password="password123"
        )
        
        user1 = await user_repository.create(user1_data)
        await user_repository.create(user2_data)
        
        # Act
        count_after_creation = await user_repository.count_total()
        
        # Eliminar un usuario
        await user_repository.delete(user1.id)
        count_after_deletion = await user_repository.count_total()
        
        # Assert
        assert count_after_creation == initial_count + 2
        assert count_after_deletion == initial_count + 1 