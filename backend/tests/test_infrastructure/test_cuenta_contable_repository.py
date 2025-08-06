"""
Pruebas de integración para SQLCuentaContableRepository.
Prueba todas las operaciones CRUD del plan de cuentas.
"""

import pytest
from uuid import uuid4

from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.domain.models.contabilidad import CuentaContable, CuentaContableCreate, TipoCuenta
from app.domain.models.user import User  # Import User model for foreign key
from app.domain.models.product import Product  # Import Product model
from app.infrastructure.repositories.cuenta_contable_repository import SQLCuentaContableRepository


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
def cuenta_repository(session):
    """Crear una instancia del repositorio de cuentas contables."""
    return SQLCuentaContableRepository(session)


@pytest.fixture
def sample_cuenta_activo():
    """Datos de ejemplo para cuenta de activo."""
    return CuentaContableCreate(
        codigo="1105",
        nombre="Efectivo y Equivalentes",
        tipo_cuenta=TipoCuenta.ACTIVO
    )


@pytest.fixture
def sample_cuenta_subcuenta():
    """Datos de ejemplo para una subcuenta."""
    return CuentaContableCreate(
        codigo="110505",
        nombre="Caja",
        tipo_cuenta=TipoCuenta.ACTIVO
    )


class TestCuentaContableRepositoryCreate:
    """Pruebas de creación de cuentas contables."""
    
    @pytest.mark.asyncio
    async def test_create_cuenta_success(self, cuenta_repository, sample_cuenta_activo):
        """Debe crear una cuenta contable exitosamente."""
        cuenta = await cuenta_repository.create(sample_cuenta_activo)
        
        assert cuenta.codigo == "1105"
        assert cuenta.nombre == "Efectivo y Equivalentes"
        assert cuenta.tipo_cuenta == TipoCuenta.ACTIVO
        assert cuenta.cuenta_padre_id is None
        assert cuenta.is_active is True
        assert cuenta.created_at is not None
        assert cuenta.id is not None
    
    @pytest.mark.asyncio
    async def test_create_cuenta_with_padre(self, cuenta_repository, sample_cuenta_activo, sample_cuenta_subcuenta):
        """Debe crear una subcuenta con cuenta padre."""
        # Crear cuenta padre primero
        cuenta_padre = await cuenta_repository.create(sample_cuenta_activo)
        
        # Crear subcuenta
        sample_cuenta_subcuenta.cuenta_padre_id = cuenta_padre.id
        subcuenta = await cuenta_repository.create(sample_cuenta_subcuenta)
        
        assert subcuenta.cuenta_padre_id == cuenta_padre.id
        assert subcuenta.codigo == "110505"
        assert subcuenta.nombre == "Caja"
    
    @pytest.mark.asyncio
    async def test_create_cuenta_codigo_duplicado_fails(self, cuenta_repository, sample_cuenta_activo):
        """Debe fallar al crear cuenta con código duplicado."""
        await cuenta_repository.create(sample_cuenta_activo)
        
        with pytest.raises(ValueError, match="Ya existe una cuenta con el código"):
            await cuenta_repository.create(sample_cuenta_activo)
    
    @pytest.mark.asyncio
    async def test_create_cuenta_padre_inexistente_fails(self, cuenta_repository, sample_cuenta_subcuenta):
        """Debe fallar al crear cuenta con padre inexistente."""
        sample_cuenta_subcuenta.cuenta_padre_id = uuid4()
        
        with pytest.raises(ValueError, match="no existe"):
            await cuenta_repository.create(sample_cuenta_subcuenta)


class TestCuentaContableRepositoryRead:
    """Pruebas de lectura de cuentas contables."""
    
    @pytest.mark.asyncio
    async def test_get_by_id_exists(self, cuenta_repository, sample_cuenta_activo):
        """Debe obtener cuenta por ID cuando existe."""
        created_cuenta = await cuenta_repository.create(sample_cuenta_activo)
        
        found_cuenta = await cuenta_repository.get_by_id(created_cuenta.id)
        
        assert found_cuenta is not None
        assert found_cuenta.id == created_cuenta.id
        assert found_cuenta.codigo == "1105"
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_exists(self, cuenta_repository):
        """Debe retornar None cuando la cuenta no existe."""
        fake_id = uuid4()
        
        found_cuenta = await cuenta_repository.get_by_id(fake_id)
        
        assert found_cuenta is None
    
    @pytest.mark.asyncio
    async def test_get_by_codigo_exists(self, cuenta_repository, sample_cuenta_activo):
        """Debe obtener cuenta por código cuando existe."""
        await cuenta_repository.create(sample_cuenta_activo)
        
        found_cuenta = await cuenta_repository.get_by_codigo("1105")
        
        assert found_cuenta is not None
        assert found_cuenta.codigo == "1105"
        assert found_cuenta.nombre == "Efectivo y Equivalentes"
    
    @pytest.mark.asyncio
    async def test_get_by_codigo_not_exists(self, cuenta_repository):
        """Debe retornar None cuando el código no existe."""
        found_cuenta = await cuenta_repository.get_by_codigo("9999")
        
        assert found_cuenta is None


class TestCuentaContableRepositoryList:
    """Pruebas de listado de cuentas contables."""
    
    @pytest.mark.asyncio
    async def test_get_all_empty(self, cuenta_repository):
        """Debe retornar lista vacía cuando no hay cuentas."""
        cuentas = await cuenta_repository.get_all()
        
        assert cuentas == []
    
    @pytest.mark.asyncio
    async def test_get_all_with_data(self, cuenta_repository, sample_cuenta_activo):
        """Debe retornar cuentas cuando existen."""
        await cuenta_repository.create(sample_cuenta_activo)
        
        cuenta_pasivo = CuentaContableCreate(
            codigo="2205",
            nombre="Cuentas por Pagar",
            tipo_cuenta=TipoCuenta.PASIVO
        )
        await cuenta_repository.create(cuenta_pasivo)
        
        cuentas = await cuenta_repository.get_all()
        
        assert len(cuentas) == 2
        # Deben estar ordenadas por código
        assert cuentas[0].codigo == "1105"
        assert cuentas[1].codigo == "2205"
    
    @pytest.mark.asyncio
    async def test_get_all_filter_by_tipo(self, cuenta_repository, sample_cuenta_activo):
        """Debe filtrar cuentas por tipo."""
        await cuenta_repository.create(sample_cuenta_activo)
        
        cuenta_pasivo = CuentaContableCreate(
            codigo="2205",
            nombre="Cuentas por Pagar",
            tipo_cuenta=TipoCuenta.PASIVO
        )
        await cuenta_repository.create(cuenta_pasivo)
        
        # Filtrar solo activos
        cuentas_activo = await cuenta_repository.get_all(tipo_cuenta=TipoCuenta.ACTIVO)
        
        assert len(cuentas_activo) == 1
        assert cuentas_activo[0].tipo_cuenta == TipoCuenta.ACTIVO
    
    @pytest.mark.asyncio
    async def test_count_total(self, cuenta_repository, sample_cuenta_activo):
        """Debe contar total de cuentas correctamente."""
        count_inicial = await cuenta_repository.count_total()
        assert count_inicial == 0
        
        await cuenta_repository.create(sample_cuenta_activo)
        
        count_despues = await cuenta_repository.count_total()
        assert count_despues == 1


class TestCuentaContableRepositorySeeding:
    """Pruebas de seeding del plan de cuentas."""
    
    @pytest.mark.asyncio
    async def test_seed_plan_cuentas_colombia(self, cuenta_repository):
        """Debe poblar el plan de cuentas de Colombia."""
        cuentas_creadas = await cuenta_repository.seed_plan_cuentas_colombia()
        
        # Verificar que se crearon cuentas
        assert cuentas_creadas > 0
        
        # Verificar algunas cuentas específicas
        cuenta_activo = await cuenta_repository.get_by_codigo("1")
        assert cuenta_activo is not None
        assert cuenta_activo.nombre == "ACTIVO"
        assert cuenta_activo.tipo_cuenta == TipoCuenta.ACTIVO
        
        cuenta_caja = await cuenta_repository.get_by_codigo("110505")
        assert cuenta_caja is not None
        assert cuenta_caja.nombre == "CAJA"
        assert cuenta_caja.tipo_cuenta == TipoCuenta.ACTIVO
    
    @pytest.mark.asyncio
    async def test_seed_plan_cuentas_idempotent(self, cuenta_repository):
        """El seeding debe ser idempotente (no crear duplicados)."""
        # Primera ejecución
        cuentas_primera = await cuenta_repository.seed_plan_cuentas_colombia()
        
        # Segunda ejecución
        cuentas_segunda = await cuenta_repository.seed_plan_cuentas_colombia()
        
        # La segunda vez no debe crear nuevas cuentas
        assert cuentas_segunda == 0
        
        # Verificar que no hay duplicados
        total_cuentas = await cuenta_repository.count_total()
        assert total_cuentas == cuentas_primera


class TestCuentaContableRepositoryUpdate:
    """Pruebas de actualización de cuentas contables."""
    
    @pytest.mark.asyncio
    async def test_update_cuenta_success(self, cuenta_repository, sample_cuenta_activo):
        """Debe actualizar una cuenta exitosamente."""
        cuenta = await cuenta_repository.create(sample_cuenta_activo)
        
        from app.domain.models.contabilidad import CuentaContableUpdate
        update_data = CuentaContableUpdate(
            nombre="Efectivo y Equivalentes Actualizado",
            is_active=False
        )
        
        updated_cuenta = await cuenta_repository.update(cuenta.id, update_data)
        
        assert updated_cuenta is not None
        assert updated_cuenta.nombre == "Efectivo y Equivalentes Actualizado"
        assert updated_cuenta.is_active is False
        assert updated_cuenta.codigo == "1105"  # No debe cambiar
    
    @pytest.mark.asyncio
    async def test_update_cuenta_not_exists(self, cuenta_repository):
        """Debe retornar None si la cuenta no existe."""
        from app.domain.models.contabilidad import CuentaContableUpdate
        update_data = CuentaContableUpdate(nombre="No existe")
        
        result = await cuenta_repository.update(uuid4(), update_data)
        
        assert result is None


class TestCuentaContableRepositoryDelete:
    """Pruebas de eliminación de cuentas contables."""
    
    @pytest.mark.asyncio
    async def test_delete_cuenta_success(self, cuenta_repository, sample_cuenta_activo):
        """Debe eliminar una cuenta exitosamente (soft delete)."""
        cuenta = await cuenta_repository.create(sample_cuenta_activo)
        
        success = await cuenta_repository.delete(cuenta.id)
        
        assert success is True
        
        # Verificar que está marcada como inactiva
        cuenta_inactiva = await cuenta_repository.get_by_id(cuenta.id)
        assert cuenta_inactiva.is_active is False
    
    @pytest.mark.asyncio
    async def test_delete_cuenta_not_exists(self, cuenta_repository):
        """Debe retornar False si la cuenta no existe."""
        success = await cuenta_repository.delete(uuid4())
        
        assert success is False


class TestCuentaContableRepositoryHierarchy:
    """Pruebas de funcionalidades jerárquicas."""
    
    @pytest.mark.asyncio
    async def test_get_subcuentas(self, cuenta_repository, sample_cuenta_activo, sample_cuenta_subcuenta):
        """Debe obtener subcuentas de una cuenta padre."""
        # Crear cuenta padre
        cuenta_padre = await cuenta_repository.create(sample_cuenta_activo)
        
        # Crear subcuenta
        sample_cuenta_subcuenta.cuenta_padre_id = cuenta_padre.id
        await cuenta_repository.create(sample_cuenta_subcuenta)
        
        # Obtener subcuentas
        subcuentas = await cuenta_repository.get_subcuentas(cuenta_padre.id)
        
        assert len(subcuentas) == 1
        assert subcuentas[0].codigo == "110505"
        assert subcuentas[0].cuenta_padre_id == cuenta_padre.id
    
    @pytest.mark.asyncio
    async def test_get_cuentas_principales(self, cuenta_repository, sample_cuenta_activo):
        """Debe obtener solo cuentas principales (sin padre)."""
        # Crear cuenta principal
        cuenta_padre = await cuenta_repository.create(sample_cuenta_activo)
        
        # Crear subcuenta
        subcuenta_data = CuentaContableCreate(
            codigo="110505",
            nombre="Caja",
            tipo_cuenta=TipoCuenta.ACTIVO,
            cuenta_padre_id=cuenta_padre.id
        )
        await cuenta_repository.create(subcuenta_data)
        
        # Obtener solo cuentas principales
        cuentas_principales = await cuenta_repository.get_cuentas_principales()
        
        assert len(cuentas_principales) == 1
        assert cuentas_principales[0].cuenta_padre_id is None
        assert cuentas_principales[0].codigo == "1105"