"""
Pruebas básicas para los endpoints del dashboard.
Valida que los endpoints de dashboard funcionen correctamente.
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from main import app
from app.infrastructure.database.session import get_session

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
    """Crea una sesión de base de datos para las pruebas."""
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(session):
    """Cliente de prueba con override de sesión de base de datos."""
    def get_test_session():
        return session
    
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


class TestDashboardEndpointsBasic:
    """Pruebas básicas para endpoints del dashboard."""

    def test_get_metricas_rapidas_success(self, client: TestClient):
        """Prueba obtener métricas rápidas exitosamente."""
        response = client.get("/api/v1/dashboard/metricas-rapidas")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        required_fields = [
            "ventas_hoy", "ventas_mes", "facturas_pendientes", 
            "stock_critico", "nuevos_clientes_mes"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Verificar tipos de datos
        assert isinstance(data["facturas_pendientes"], int)
        assert isinstance(data["stock_critico"], int)
        assert isinstance(data["nuevos_clientes_mes"], int)

    def test_get_kpis_principales_success(self, client: TestClient):
        """Prueba obtener KPIs principales exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = client.get(
            "/api/v1/dashboard/kpis",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "incluir_comparacion": True
            }
        )
        
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        
        # Verificar KPIs principales
        required_kpis = [
            "ventas_del_periodo", "numero_facturas", "ticket_promedio",
            "cartera_pendiente", "cartera_vencida", "valor_inventario",
            "productos_activos", "productos_sin_stock", "productos_stock_bajo",
            "clientes_activos", "clientes_nuevos"
        ]
        
        for kpi in required_kpis:
            assert kpi in data

    def test_get_kpis_fechas_invalidas(self, client: TestClient):
        """Prueba KPIs con fechas inválidas."""
        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        
        response = client.get(
            "/api/v1/dashboard/kpis",
            params={
                "fecha_inicio": hoy.isoformat(),
                "fecha_fin": ayer.isoformat(),  # Fecha fin anterior a inicio
                "incluir_comparacion": False
            }
        )
        
        assert response.status_code == 400
        assert "fecha de inicio debe ser anterior" in response.json()["detail"].lower()

    def test_get_ventas_por_periodo_success(self, client: TestClient):
        """Prueba obtener ventas por período exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = client.get(
            "/api/v1/dashboard/ventas-por-periodo",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "agrupacion": "mes"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)

    def test_get_productos_top_success(self, client: TestClient):
        """Prueba obtener productos top exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = client.get(
            "/api/v1/dashboard/productos-top",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "limite": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 5  # Respeta el límite

    def test_get_alertas_success(self, client: TestClient):
        """Prueba obtener alertas exitosamente."""
        response = client.get("/api/v1/dashboard/alertas")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)

    def test_get_estado_sistema_success(self, client: TestClient):
        """Prueba obtener estado del sistema exitosamente."""
        response = client.get("/api/v1/dashboard/estado-sistema")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del estado
        required_sections = [
            "fecha_consulta", "metricas_rapidas", "salud_sistema",
            "alertas", "resumen_modulos"
        ]
        
        for section in required_sections:
            assert section in data
        
        # Verificar salud del sistema
        salud = data["salud_sistema"]
        assert "puntuacion" in salud
        assert "estado" in salud
        assert "color" in salud
        assert 0 <= salud["puntuacion"] <= 100

    def test_get_periodos_disponibles_success(self, client: TestClient):
        """Prueba obtener períodos disponibles exitosamente."""
        response = client.get("/api/v1/dashboard/configuracion/periodos")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "periodos" in data
        periodos = data["periodos"]
        
        # Verificar que tenga los períodos esperados
        valores_esperados = ["hoy", "semana", "mes", "trimestre", "semestre", "ano", "personalizado"]
        valores_encontrados = [p["valor"] for p in periodos]
        
        for valor in valores_esperados:
            assert valor in valores_encontrados