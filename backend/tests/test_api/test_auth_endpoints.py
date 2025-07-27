"""
Pruebas de integración para los endpoints de autenticación.
Verifican que los endpoints REST funcionen correctamente con la base de datos.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from main import app
from app.infrastructure.database.session import get_session
from app.domain.models.user import UserRole


# Configuración de base de datos de prueba
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    """Crea un engine de base de datos SQLite en memoria para las pruebas."""
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
    """Proporciona una sesión de base de datos para cada prueba."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    """Crea un cliente de prueba de FastAPI con la base de datos de prueba."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Datos de ejemplo para crear un usuario."""
    return {
        "email": "test@example.com",
        "nombre": "Usuario Test",
        "rol": UserRole.VENDEDOR,
        "password": "password123"
    }


class TestAuthEndpoints:
    """Suite de pruebas para los endpoints de autenticación."""
    
    def test_register_user_success(self, client, sample_user_data):
        """Prueba el registro exitoso de un usuario."""
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["user"]["nombre"] == sample_user_data["nombre"]
        assert data["user"]["rol"] == sample_user_data["rol"]
        assert data["user"]["is_active"] is True
        assert "message" in data
    
    def test_register_user_duplicate_email(self, client, sample_user_data):
        """Prueba que no se puede registrar un usuario con email duplicado."""
        # Crear primer usuario
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Intentar crear segundo usuario con mismo email
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert "Ya existe un usuario" in data["detail"]
    
    def test_register_user_invalid_role(self, client, sample_user_data):
        """Prueba que no se puede registrar un usuario con rol inválido."""
        sample_user_data["rol"] = "rol_inexistente"
        
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "Rol inválido" in data["detail"]
    
    def test_register_user_invalid_email(self, client, sample_user_data):
        """Prueba que no se puede registrar con email inválido."""
        sample_user_data["email"] = "email-invalido"
        
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_register_user_short_password(self, client, sample_user_data):
        """Prueba que no se puede registrar con contraseña muy corta."""
        sample_user_data["password"] = "123"
        
        response = client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, client, sample_user_data):
        """Prueba el login exitoso."""
        # Registrar usuario primero
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Hacer login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]
    
    def test_login_invalid_email(self, client, sample_user_data):
        """Prueba login con email inexistente."""
        login_data = {
            "email": "inexistente@example.com",
            "password": "password123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Credenciales inválidas" in data["detail"]
    
    def test_login_invalid_password(self, client, sample_user_data):
        """Prueba login con contraseña incorrecta."""
        # Registrar usuario primero
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Intentar login con contraseña incorrecta
        login_data = {
            "email": sample_user_data["email"],
            "password": "password_incorrecta"
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Credenciales inválidas" in data["detail"]
    
    def test_login_inactive_user(self, client, sample_user_data, session):
        """Prueba login con usuario inactivo."""
        # Registrar usuario
        client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Desactivar usuario directamente en la base de datos
        from app.domain.models.user import User
        from sqlmodel import select
        
        statement = select(User).where(User.email == sample_user_data["email"])
        user = session.exec(statement).first()
        user.is_active = False
        session.add(user)
        session.commit()
        
        # Intentar login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "Usuario inactivo" in data["detail"]
    
    def test_get_current_user_success(self, client, sample_user_data):
        """Prueba obtener información del usuario actual con token válido."""
        # Registrar y hacer login
        client.post("/api/v1/auth/register", json=sample_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Obtener usuario actual
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == sample_user_data["email"]
        assert data["nombre"] == sample_user_data["nombre"]
        assert data["rol"] == sample_user_data["rol"]
        assert data["is_active"] is True
    
    def test_get_current_user_no_token(self, client):
        """Prueba obtener usuario actual sin token."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 403  # Forbidden
    
    def test_get_current_user_invalid_token(self, client):
        """Prueba obtener usuario actual con token inválido."""
        headers = {"Authorization": "Bearer token_invalido"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_login_validation_errors(self, client):
        """Prueba errores de validación en login."""
        # Email inválido
        response = client.post("/api/v1/auth/login", json={
            "email": "email-invalido",
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Contraseña muy corta
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "123"
        })
        assert response.status_code == 422
        
        # Campos faltantes
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com"
        })
        assert response.status_code == 422
    
    def test_register_validation_errors(self, client):
        """Prueba errores de validación en registro."""
        # Nombre muy corto
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "nombre": "A",  # Muy corto
            "password": "password123"
        })
        assert response.status_code == 422
        
        # Nombre muy largo
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "nombre": "A" * 101,  # Muy largo
            "password": "password123"
        })
        assert response.status_code == 422
    
    def test_full_auth_flow(self, client, sample_user_data):
        """Prueba el flujo completo de autenticación."""
        # 1. Registrar usuario
        register_response = client.post("/api/v1/auth/register", json=sample_user_data)
        assert register_response.status_code == 201
        register_token = register_response.json()["access_token"]
        
        # 2. Verificar que el token de registro funciona
        headers = {"Authorization": f"Bearer {register_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # 3. Hacer login separado
        login_response = client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]
        
        # 4. Verificar que el token de login funciona
        headers = {"Authorization": f"Bearer {login_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        
        # 5. Verificar que ambos tokens retornan la misma información de usuario
        user_data = me_response.json()
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["nombre"] == sample_user_data["nombre"] 