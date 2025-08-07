"""
Pruebas para los endpoints del dashboard.
Valida que los endpoints de dashboard funcionen correctamente.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from sqlalchemy.pool import StaticPool

from app.domain.models.dashboard import PeriodoReporte
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


class TestDashboardEndpoints:
    """Pruebas para endpoints del dashboard."""

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
        assert isinstance(data["ventas_hoy"], (int, float, str))  # Decimal viene como string
        assert isinstance(data["ventas_mes"], (int, float, str))
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

    @pytest.mark.asyncio
    async def test_get_kpis_fechas_invalidas(self, client: AsyncClient):
        """Prueba KPIs con fechas inválidas."""
        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        
        response = await client.get(
            "/api/v1/dashboard/kpis",
            params={
                "fecha_inicio": hoy.isoformat(),
                "fecha_fin": ayer.isoformat(),  # Fecha fin anterior a inicio
                "incluir_comparacion": False
            }
        )
        
        assert response.status_code == 400
        assert "fecha de inicio debe ser anterior" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_ventas_por_periodo_success(self, client: AsyncClient):
        """Prueba obtener ventas por período exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
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
        
        # Si hay datos, verificar estructura
        if data:
            item = data[0]
            required_fields = [
                "periodo", "fecha_inicio", "fecha_fin", 
                "total_ventas", "numero_facturas", "ticket_promedio"
            ]
            
            for field in required_fields:
                assert field in item

    @pytest.mark.asyncio
    async def test_get_ventas_agrupacion_invalida(self, client: AsyncClient):
        """Prueba ventas por período con agrupación inválida."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/ventas-por-periodo",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "agrupacion": "ano_invalido"  # Agrupación no válida
            }
        )
        
        assert response.status_code == 422  # Validation error por regex

    @pytest.mark.asyncio
    async def test_get_productos_top_success(self, client: AsyncClient):
        """Prueba obtener productos top exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
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
        
        # Si hay datos, verificar estructura
        if data:
            item = data[0]
            required_fields = [
                "producto_id", "sku", "nombre", "cantidad_vendida",
                "total_ventas", "numero_facturas", "ticket_promedio"
            ]
            
            for field in required_fields:
                assert field in item

    @pytest.mark.asyncio
    async def test_get_productos_top_limite_invalido(self, client: AsyncClient):
        """Prueba productos top con límite inválido."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/productos-top",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "limite": 0  # Límite inválido
            }
        )
        
        assert response.status_code == 422  # Validation error por ge=1

    @pytest.mark.asyncio
    async def test_get_clientes_top_success(self, client: AsyncClient):
        """Prueba obtener clientes top exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/clientes-top",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "limite": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 10  # Respeta el límite
        
        # Si hay datos, verificar estructura
        if data:
            item = data[0]
            required_fields = [
                "cliente_id", "numero_documento", "nombre_completo",
                "total_compras", "numero_facturas", "ticket_promedio"
            ]
            
            for field in required_fields:
                assert field in item

    @pytest.mark.asyncio
    async def test_get_inventario_resumen_success(self, client: AsyncClient):
        """Prueba obtener resumen de inventario exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/inventario-resumen",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Si hay datos, verificar estructura
        if data:
            item = data[0]
            required_fields = [
                "tipo_movimiento", "cantidad_movimientos", 
                "cantidad_total", "valor_total"
            ]
            
            for field in required_fields:
                assert field in item

    @pytest.mark.asyncio
    async def test_get_balance_contable_success(self, client: AsyncClient):
        """Prueba obtener balance contable exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/balance-contable",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "solo_principales": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Si hay datos, verificar estructura
        if data:
            item = data[0]
            required_fields = [
                "codigo_cuenta", "nombre_cuenta", "tipo_cuenta",
                "total_debitos", "total_creditos", "saldo"
            ]
            
            for field in required_fields:
                assert field in item

    @pytest.mark.asyncio
    async def test_get_alertas_success(self, client: AsyncClient):
        """Prueba obtener alertas exitosamente."""
        response = await client.get("/api/v1/dashboard/alertas")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        
        # Si hay alertas, verificar estructura
        if data:
            alerta = data[0]
            required_fields = [
                "tipo", "titulo", "mensaje", "fecha", 
                "modulo", "requiere_accion"
            ]
            
            for field in required_fields:
                assert field in alerta
            
            # Verificar tipos válidos
            assert alerta["tipo"] in ["warning", "danger", "info"]
            assert isinstance(alerta["requiere_accion"], bool)

    @pytest.mark.asyncio
    async def test_get_dashboard_completo_success(self, client: AsyncClient):
        """Prueba obtener dashboard completo exitosamente."""
        response = await client.get(
            "/api/v1/dashboard/completo",
            params={
                "periodo": "mes",
                "limite_tops": 5,
                "incluir_comparacion": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura principal
        required_sections = [
            "fecha_generacion", "periodo", "fecha_inicio", "fecha_fin",
            "kpis", "ventas_por_periodo", "productos_top", "clientes_top",
            "movimientos_inventario", "balance_principales", "alertas"
        ]
        
        for section in required_sections:
            assert section in data
        
        # Verificar que las listas respeten el límite
        assert len(data["productos_top"]) <= 5
        assert len(data["clientes_top"]) <= 5

    @pytest.mark.asyncio
    async def test_get_dashboard_periodo_personalizado_sin_fechas(self, client: AsyncClient):
        """Prueba dashboard con período personalizado sin fechas."""
        response = await client.get(
            "/api/v1/dashboard/completo",
            params={
                "periodo": "personalizado",
                "limite_tops": 10
                # No se proporcionan fecha_inicio ni fecha_fin
            }
        )
        
        assert response.status_code == 400
        assert "personalizado" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_analisis_rentabilidad_success(self, client: AsyncClient):
        """Prueba análisis de rentabilidad exitosamente."""
        hoy = date.today()
        inicio_mes = date(hoy.year, hoy.month, 1)
        
        response = await client.get(
            "/api/v1/dashboard/analisis/rentabilidad",
            params={
                "fecha_inicio": inicio_mes.isoformat(),
                "fecha_fin": hoy.isoformat()
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del análisis
        required_sections = [
            "periodo", "metricas_financieras", "metricas_ventas",
            "productos_mas_rentables", "clientes_mas_rentables"
        ]
        
        for section in required_sections:
            assert section in data

    @pytest.mark.asyncio
    async def test_analisis_tendencias_ventas_success(self, client: AsyncClient):
        """Prueba análisis de tendencias exitosamente."""
        hoy = date.today()
        hace_3_meses = hoy - timedelta(days=90)
        
        response = await client.get(
            "/api/v1/dashboard/analisis/tendencias-ventas",
            params={
                "fecha_inicio": hace_3_meses.isoformat(),
                "fecha_fin": hoy.isoformat(),
                "agrupacion": "mes"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura del análisis
        required_sections = [
            "periodo_analisis", "tendencia_general", "crecimiento_promedio",
            "mejor_periodo", "peor_periodo", "datos_detallados"
        ]
        
        for section in required_sections:
            assert section in data

    @pytest.mark.asyncio
    async def test_get_estado_sistema_success(self, client: AsyncClient):
        """Prueba obtener estado del sistema exitosamente."""
        response = await client.get("/api/v1/dashboard/estado-sistema")
        
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

    @pytest.mark.asyncio
    async def test_get_periodos_disponibles_success(self, client: AsyncClient):
        """Prueba obtener períodos disponibles exitosamente."""
        response = await client.get("/api/v1/dashboard/configuracion/periodos")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "periodos" in data
        periodos = data["periodos"]
        
        # Verificar que tenga los períodos esperados
        valores_esperados = ["hoy", "semana", "mes", "trimestre", "semestre", "ano", "personalizado"]
        valores_encontrados = [p["valor"] for p in periodos]
        
        for valor in valores_esperados:
            assert valor in valores_encontrados
        
        # Verificar estructura de cada período
        for periodo in periodos:
            assert "valor" in periodo
            assert "etiqueta" in periodo

    @pytest.mark.asyncio
    async def test_export_excel_not_implemented(self, client: AsyncClient):
        """Prueba que exportación a Excel no está implementada."""
        response = await client.get(
            "/api/v1/dashboard/export/excel",
            params={"periodo": "mes"}
        )
        
        assert response.status_code == 501  # Not implemented
        assert "no implementada" in response.json()["detail"]