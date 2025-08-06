"""
Pruebas de integración para los endpoints de contabilidad.
Prueba todas las operaciones REST del módulo de cuentas contables.
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from app.domain.models.contabilidad import TipoCuenta


@pytest.fixture
def client():
    """Cliente de prueba para FastAPI."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers de autenticación para las pruebas."""
    # Por ahora retornamos headers vacíos ya que los endpoints no requieren auth
    return {}


class TestContabilidadEndpointsCreate:
    """Pruebas de creación de cuentas contables."""
    
    def test_create_cuenta_contable_success(self, client, auth_headers):
        """Debe crear una cuenta contable exitosamente."""
        cuenta_data = {
            "codigo": "99991105",
            "nombre": "Test Efectivo y Equivalentes",
            "tipo_cuenta": "ACTIVO"
        }
        
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "99991105"
        assert data["nombre"] == "Test Efectivo y Equivalentes"
        assert data["tipo_cuenta"] == "ACTIVO"
        assert data["is_active"] is True
        assert data["id"] is not None
    
    def test_create_cuenta_contable_duplicate_codigo(self, client, auth_headers):
        """Debe fallar al crear cuenta con código duplicado."""
        cuenta_data = {
            "codigo": "99991106",
            "nombre": "Test Duplicado",
            "tipo_cuenta": "ACTIVO"
        }
        
        # Primera creación debe ser exitosa
        response1 = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        assert response1.status_code == 201
        
        # Segunda creación debe fallar
        response2 = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        assert response2.status_code == 400
        assert "código" in response2.json()["detail"]
    
    def test_create_cuenta_contable_validation_errors(self, client, auth_headers):
        """Debe fallar con errores de validación."""
        # Código vacío
        cuenta_data = {
            "codigo": "",
            "nombre": "Test",
            "tipo_cuenta": "ACTIVO"
        }
        
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        assert response.status_code == 422


class TestContabilidadEndpointsRead:
    """Pruebas de lectura de cuentas contables."""
    
    def test_get_cuenta_contable_by_id_exists(self, client, auth_headers):
        """Debe obtener una cuenta por ID cuando existe."""
        # Crear cuenta primero
        cuenta_data = {
            "codigo": "99992205",
            "nombre": "Test Cuentas por Pagar",
            "tipo_cuenta": "PASIVO"
        }
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        created_cuenta = response.json()
        
        # Obtener por ID
        response = client.get(f"/api/v1/cuentas/{created_cuenta['id']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_cuenta["id"]
        assert data["codigo"] == "99992205"
    
    def test_get_cuenta_contable_by_id_not_exists(self, client, auth_headers):
        """Debe retornar 404 cuando la cuenta no existe."""
        fake_id = str(uuid4())
        
        response = client.get(f"/api/v1/cuentas/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_cuenta_contable_by_codigo_exists(self, client, auth_headers):
        """Debe obtener una cuenta por código cuando existe."""
        # Crear cuenta primero
        cuenta_data = {
            "codigo": "99993115",
            "nombre": "Test Aportes Sociales",
            "tipo_cuenta": "PATRIMONIO"
        }
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        
        # Obtener por código
        response = client.get(f"/api/v1/cuentas/codigo/99993115", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["codigo"] == "99993115"
        assert data["nombre"] == "Test Aportes Sociales"
    
    def test_get_cuenta_contable_by_codigo_not_exists(self, client, auth_headers):
        """Debe retornar 404 cuando el código no existe."""
        response = client.get(f"/api/v1/cuentas/codigo/9999", headers=auth_headers)
        
        assert response.status_code == 404


class TestContabilidadEndpointsList:
    """Pruebas de listado de cuentas contables."""
    
    def test_list_cuentas_contables_empty(self, client, auth_headers):
        """Debe retornar lista vacía cuando no hay cuentas."""
        response = client.get("/api/v1/cuentas/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["cuentas"] == []
        assert data["total"] == 0
    
    def test_list_cuentas_contables_with_data(self, client, auth_headers):
        """Debe retornar cuentas cuando existen."""
        # Crear algunas cuentas
        cuentas = [
            {"codigo": "99911105", "nombre": "Test Efectivo", "tipo_cuenta": "ACTIVO"},
            {"codigo": "99922205", "nombre": "Test Cuentas por Pagar", "tipo_cuenta": "PASIVO"},
        ]
        
        for cuenta_data in cuentas:
            client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        
        response = client.get("/api/v1/cuentas/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["cuentas"]) == 2
        assert data["total"] == 2
    
    def test_list_cuentas_contables_filter_by_tipo(self, client, auth_headers):
        """Debe filtrar cuentas por tipo."""
        # Crear cuentas de diferentes tipos
        cuentas = [
            {"codigo": "99921105", "nombre": "Test Efectivo", "tipo_cuenta": "ACTIVO"},
            {"codigo": "99932205", "nombre": "Test Cuentas por Pagar", "tipo_cuenta": "PASIVO"},
            {"codigo": "99943115", "nombre": "Test Aportes", "tipo_cuenta": "PATRIMONIO"},
        ]
        
        for cuenta_data in cuentas:
            client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        
        # Filtrar solo activos
        response = client.get("/api/v1/cuentas/?tipo_cuenta=ACTIVO", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["cuentas"]) == 1
        assert data["cuentas"][0]["tipo_cuenta"] == "ACTIVO"
    
    def test_list_cuentas_contables_pagination(self, client, auth_headers):
        """Debe paginar correctamente las cuentas."""
        # Crear varias cuentas
        for i in range(5):
            cuenta_data = {
                "codigo": f"999{i:03d}10",
                "nombre": f"Test Cuenta {i}",
                "tipo_cuenta": "ACTIVO"
            }
            client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        
        # Primera página con límite de 3
        response = client.get("/api/v1/cuentas/?page=1&limit=3", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["cuentas"]) == 3
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["limit"] == 3
        assert data["has_next"] is True
        assert data["has_prev"] is False


class TestContabilidadEndpointsUpdate:
    """Pruebas de actualización de cuentas contables."""
    
    def test_update_cuenta_contable_success(self, client, auth_headers):
        """Debe actualizar una cuenta exitosamente."""
        # Crear cuenta primero
        cuenta_data = {
            "codigo": "99994135",
            "nombre": "Test Ventas Originales",
            "tipo_cuenta": "INGRESO"
        }
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        created_cuenta = response.json()
        
        # Actualizar la cuenta
        update_data = {
            "nombre": "Ventas de Mercancías Actualizadas",
            "is_active": False
        }
        response = client.put(
            f"/api/v1/cuentas/{created_cuenta['id']}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Ventas de Mercancías Actualizadas"
        assert data["is_active"] is False
        assert data["codigo"] == "99994135"  # El código no debe cambiar
    
    def test_update_cuenta_contable_not_exists(self, client, auth_headers):
        """Debe retornar 404 si la cuenta no existe."""
        fake_id = str(uuid4())
        update_data = {"nombre": "No existe"}
        
        response = client.put(f"/api/v1/cuentas/{fake_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404


class TestContabilidadEndpointsDelete:
    """Pruebas de eliminación de cuentas contables."""
    
    def test_delete_cuenta_contable_success(self, client, auth_headers):
        """Debe eliminar una cuenta exitosamente."""
        # Crear cuenta primero
        cuenta_data = {
            "codigo": "99996135",
            "nombre": "Test Costo de Ventas",
            "tipo_cuenta": "EGRESO"
        }
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        created_cuenta = response.json()
        
        # Eliminar la cuenta
        response = client.delete(f"/api/v1/cuentas/{created_cuenta['id']}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "eliminada" in data["message"]
    
    def test_delete_cuenta_contable_not_exists(self, client, auth_headers):
        """Debe retornar 404 si la cuenta no existe."""
        fake_id = str(uuid4())
        
        response = client.delete(f"/api/v1/cuentas/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404


class TestContabilidadEndpointsHierarchy:
    """Pruebas de funcionalidades jerárquicas."""
    
    def test_get_cuentas_principales(self, client, auth_headers):
        """Debe obtener solo cuentas principales (sin padre)."""
        # Crear cuenta principal
        principal_data = {
            "codigo": "99981",
            "nombre": "TEST ACTIVO",
            "tipo_cuenta": "ACTIVO"
        }
        principal_response = client.post("/api/v1/cuentas/", json=principal_data, headers=auth_headers)
        principal_cuenta = principal_response.json()
        
        # Crear subcuenta
        subcuenta_data = {
            "codigo": "99982",
            "nombre": "TEST ACTIVO CORRIENTE",
            "tipo_cuenta": "ACTIVO",
            "cuenta_padre_id": principal_cuenta["id"]
        }
        client.post("/api/v1/cuentas/", json=subcuenta_data, headers=auth_headers)
        
        # Obtener solo principales
        response = client.get("/api/v1/cuentas/principales/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["cuentas"]) == 1
        assert data["cuentas"][0]["codigo"] == "99981"
    
    def test_get_subcuentas(self, client, auth_headers):
        """Debe obtener subcuentas de una cuenta padre."""
        # Crear cuenta padre
        padre_data = {
            "codigo": "99983",
            "nombre": "TEST PASIVO",
            "tipo_cuenta": "PASIVO"
        }
        padre_response = client.post("/api/v1/cuentas/", json=padre_data, headers=auth_headers)
        padre_cuenta = padre_response.json()
        
        # Crear subcuenta
        subcuenta_data = {
            "codigo": "99984",
            "nombre": "TEST PASIVO CORRIENTE",
            "tipo_cuenta": "PASIVO",
            "cuenta_padre_id": padre_cuenta["id"]
        }
        client.post("/api/v1/cuentas/", json=subcuenta_data, headers=auth_headers)
        
        # Obtener subcuentas
        response = client.get(f"/api/v1/cuentas/{padre_cuenta['id']}/subcuentas/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["subcuentas"]) == 1
        assert data["subcuentas"][0]["codigo"] == "99984"
        assert data["cuenta_padre_id"] == padre_cuenta["id"]
        assert data["total_subcuentas"] == 1


class TestContabilidadEndpointsSeeding:
    """Pruebas de seeding del plan de cuentas."""
    
    def test_seed_plan_cuentas_colombia(self, client, auth_headers):
        """Debe poblar el plan de cuentas de Colombia."""
        response = client.post("/api/v1/cuentas/seed-colombia/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["cuentas_creadas"] > 0
        assert "Colombia" in data["mensaje"]
        
        # Verificar que se crearon cuentas específicas
        cuenta_activo_response = client.get("/api/v1/cuentas/codigo/1", headers=auth_headers)
        assert cuenta_activo_response.status_code == 200
        
        cuenta_caja_response = client.get("/api/v1/cuentas/codigo/110505", headers=auth_headers)
        assert cuenta_caja_response.status_code == 200
    
    def test_seed_plan_cuentas_idempotent(self, client, auth_headers):
        """El seeding debe ser idempotente (no crear duplicados)."""
        # Primera ejecución
        response1 = client.post("/api/v1/cuentas/seed-colombia/", headers=auth_headers)
        assert response1.status_code == 200
        cuentas_primera = response1.json()["cuentas_creadas"]
        
        # Segunda ejecución
        response2 = client.post("/api/v1/cuentas/seed-colombia/", headers=auth_headers)
        assert response2.status_code == 200
        cuentas_segunda = response2.json()["cuentas_creadas"]
        
        # La segunda vez no debe crear nuevas cuentas
        assert cuentas_segunda == 0
    
    def test_get_plan_cuentas_jerarquico(self, client, auth_headers):
        """Debe obtener el plan de cuentas jerárquico."""
        # Crear algunas cuentas jerárquicas
        client.post("/api/v1/cuentas/seed-colombia/", headers=auth_headers)
        
        response = client.get("/api/v1/cuentas/plan-jerarquico/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "plan_cuentas" in data
        assert isinstance(data["plan_cuentas"], list)


class TestContabilidadEndpointsValidation:
    """Pruebas de validación de datos."""
    
    def test_invalid_uuid_format(self, client, auth_headers):
        """Debe fallar con UUID inválido."""
        response = client.get("/api/v1/cuentas/invalid-uuid", headers=auth_headers)
        assert response.status_code == 422
    
    def test_invalid_tipo_cuenta(self, client, auth_headers):
        """Debe fallar con tipo de cuenta inválido."""
        cuenta_data = {
            "codigo": "99995555",
            "nombre": "Test Efectivo",
            "tipo_cuenta": "INVALIDO"
        }
        
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_codigo_non_numeric(self, client, auth_headers):
        """Debe fallar con código no numérico."""
        cuenta_data = {
            "codigo": "ABC1",
            "nombre": "Test Efectivo",
            "tipo_cuenta": "ACTIVO"
        }
        
        response = client.post("/api/v1/cuentas/", json=cuenta_data, headers=auth_headers)
        assert response.status_code == 422