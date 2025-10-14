#!/usr/bin/env python3
"""
Script de inicialización completa de la base de datos
Sistema de Gestión Empresarial

Este script:
1. Crea todas las tablas necesarias
2. Popula datos iniciales de contabilidad (Plan de cuentas colombiano)
3. Crea usuarios de prueba con diferentes roles
4. Inserta productos de ejemplo
5. Configura datos iniciales necesarios para el funcionamiento

Uso: python scripts/init_database.py
"""

import os
import sys
import asyncio
from datetime import datetime
from decimal import Decimal

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import SQLModel, create_engine, Session, select
from passlib.context import CryptContext

# Importar todos los modelos para crear las tablas
from app.domain.models.user import User
from app.domain.models.product import Product
from app.domain.models.movimiento_inventario import MovimientoInventario
from app.domain.models.contabilidad import CuentaContable, AsientoContable, DetalleAsiento
from app.domain.models.facturacion import Cliente, Factura, DetalleFactura

# Configuración de la base de datos
#DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://admin:admin@localhost:5432/inventario')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+psycopg://business_admin:pc5dTLr38WkwkGlhq4F5@business-system-dev-db.cqrk2ecg4sic.us-east-1.rds.amazonaws.com:5432/business_system_dev')

# Configurar contexto de encriptación para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashear contraseña"""
    return pwd_context.hash(password)

def create_tables(engine):
    """Crear todas las tablas del sistema"""
    print("🏗️  Creando estructura de tablas...")
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def create_test_users(session: Session):
    """Crear usuarios de prueba con diferentes roles"""
    print("👥 Creando usuarios de prueba...")
    
    usuarios = [
        {
            "email": "admin@empresa.com",
            "nombre": "Administrador Sistema",
            "rol": "administrador",
            "password": "admin123"
        },
        {
            "email": "gerente@empresa.com", 
            "nombre": "Gerente Ventas",
            "rol": "gerente_ventas",
            "password": "gerente123"
        },
        {
            "email": "contador@empresa.com",
            "nombre": "Contador Principal", 
            "rol": "contador",
            "password": "contador123"
        },
        {
            "email": "vendedor@empresa.com",
            "nombre": "Vendedor Principal",
            "rol": "vendedor", 
            "password": "vendedor123"
        },
        {
            "email": "demo@empresa.com",
            "nombre": "Usuario Demo",
            "rol": "administrador",
            "password": "demo123"
        }
    ]
    
    created_count = 0
    for user_data in usuarios:
        try:
            # Verificar si el usuario ya existe
            existing_user = session.exec(select(User).where(User.email == user_data["email"])).first()
            if existing_user:
                print(f"   ⚠️  Usuario {user_data['email']} ya existe, saltando...")
                continue
                
            user = User(
                email=user_data["email"],
                nombre=user_data["nombre"],
                rol=user_data["rol"],
                hashed_password=hash_password(user_data["password"]),
                is_active=True,
                created_at=datetime.now()
            )
            session.add(user)
            created_count += 1
            print(f"   ✅ Usuario creado: {user_data['email']} ({user_data['rol']})")
            
        except Exception as e:
            print(f"   ❌ Error creando usuario {user_data['email']}: {e}")
    
    session.commit()
    print(f"✅ {created_count} usuarios de prueba creados")

def create_chart_of_accounts(session: Session):
    """Crear plan de cuentas colombiano básico"""
    print("📊 Creando plan de cuentas colombiano...")
    
    cuentas = [
        # ACTIVOS (1)
        {"codigo": "1", "nombre": "ACTIVO", "tipo_cuenta": "ACTIVO", "cuenta_padre": None},
        {"codigo": "11", "nombre": "DISPONIBLE", "tipo_cuenta": "ACTIVO", "cuenta_padre": "1"},
        {"codigo": "1105", "nombre": "Caja", "tipo_cuenta": "ACTIVO", "cuenta_padre": "11"},
        {"codigo": "1110", "nombre": "Bancos", "tipo_cuenta": "ACTIVO", "cuenta_padre": "11"},
        {"codigo": "12", "nombre": "INVERSIONES", "tipo_cuenta": "ACTIVO", "cuenta_padre": "1"},
        {"codigo": "13", "nombre": "DEUDORES", "tipo_cuenta": "ACTIVO", "cuenta_padre": "1"},
        {"codigo": "1305", "nombre": "Clientes", "tipo_cuenta": "ACTIVO", "cuenta_padre": "13"},
        {"codigo": "1355", "nombre": "Anticipo de Impuestos", "tipo_cuenta": "ACTIVO", "cuenta_padre": "13"},
        {"codigo": "14", "nombre": "INVENTARIOS", "tipo_cuenta": "ACTIVO", "cuenta_padre": "1"},
        {"codigo": "1435", "nombre": "Mercancías no Fabricadas por la Empresa", "tipo_cuenta": "ACTIVO", "cuenta_padre": "14"},
        {"codigo": "15", "nombre": "PROPIEDADES PLANTA Y EQUIPO", "tipo_cuenta": "ACTIVO", "cuenta_padre": "1"},
        {"codigo": "1540", "nombre": "Terrenos", "tipo_cuenta": "ACTIVO", "cuenta_padre": "15"},
        {"codigo": "1548", "nombre": "Edificaciones", "tipo_cuenta": "ACTIVO", "cuenta_padre": "15"},
        {"codigo": "1592", "nombre": "Depreciación Acumulada", "tipo_cuenta": "ACTIVO", "cuenta_padre": "15"},
        
        # PASIVOS (2)
        {"codigo": "2", "nombre": "PASIVO", "tipo_cuenta": "PASIVO", "cuenta_padre": None},
        {"codigo": "21", "nombre": "OBLIGACIONES FINANCIERAS", "tipo_cuenta": "PASIVO", "cuenta_padre": "2"},
        {"codigo": "22", "nombre": "PROVEEDORES", "tipo_cuenta": "PASIVO", "cuenta_padre": "2"},
        {"codigo": "2205", "nombre": "Proveedores Nacionales", "tipo_cuenta": "PASIVO", "cuenta_padre": "22"},
        {"codigo": "23", "nombre": "CUENTAS POR PAGAR", "tipo_cuenta": "PASIVO", "cuenta_padre": "2"},
        {"codigo": "24", "nombre": "IMPUESTOS GRAVÁMENES Y TASAS", "tipo_cuenta": "PASIVO", "cuenta_padre": "2"},
        {"codigo": "2408", "nombre": "Impuesto sobre las Ventas por Pagar", "tipo_cuenta": "PASIVO", "cuenta_padre": "24"},
        {"codigo": "25", "nombre": "OBLIGACIONES LABORALES", "tipo_cuenta": "PASIVO", "cuenta_padre": "2"},
        
        # PATRIMONIO (3)
        {"codigo": "3", "nombre": "PATRIMONIO", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": None},
        {"codigo": "31", "nombre": "CAPITAL SOCIAL", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "3"},
        {"codigo": "3105", "nombre": "Capital Suscrito y Pagado", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "31"},
        {"codigo": "32", "nombre": "RESERVAS", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "3"},
        {"codigo": "33", "nombre": "REVALORIZACION DEL PATRIMONIO", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "3"},
        {"codigo": "36", "nombre": "RESULTADOS DEL EJERCICIO", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "3"},
        {"codigo": "3605", "nombre": "Utilidades o Excedentes Acumulados", "tipo_cuenta": "PATRIMONIO", "cuenta_padre": "36"},
        
        # INGRESOS (4)
        {"codigo": "4", "nombre": "INGRESOS", "tipo_cuenta": "INGRESO", "cuenta_padre": None},
        {"codigo": "41", "nombre": "OPERACIONALES", "tipo_cuenta": "INGRESO", "cuenta_padre": "4"},
        {"codigo": "4135", "nombre": "Comercio al por Mayor y al por Menor", "tipo_cuenta": "INGRESO", "cuenta_padre": "41"},
        {"codigo": "42", "nombre": "NO OPERACIONALES", "tipo_cuenta": "INGRESO", "cuenta_padre": "4"},
        
        # GASTOS (5)
        {"codigo": "5", "nombre": "GASTOS", "tipo_cuenta": "EGRESO", "cuenta_padre": None},
        {"codigo": "51", "nombre": "OPERACIONALES DE ADMINISTRACIÓN", "tipo_cuenta": "EGRESO", "cuenta_padre": "5"},
        {"codigo": "5105", "nombre": "Gastos de Personal", "tipo_cuenta": "EGRESO", "cuenta_padre": "51"},
        {"codigo": "5115", "nombre": "Gastos Generales", "tipo_cuenta": "EGRESO", "cuenta_padre": "51"},
        {"codigo": "52", "nombre": "OPERACIONALES DE VENTAS", "tipo_cuenta": "EGRESO", "cuenta_padre": "5"},
        {"codigo": "53", "nombre": "NO OPERACIONALES", "tipo_cuenta": "EGRESO", "cuenta_padre": "5"},
        
        # COSTOS (6)
        {"codigo": "6", "nombre": "COSTOS DE VENTAS", "tipo_cuenta": "EGRESO", "cuenta_padre": None},
        {"codigo": "61", "nombre": "COSTO DE VENTAS Y DE PRESTACIÓN DE SERVICIOS", "tipo_cuenta": "EGRESO", "cuenta_padre": "6"},
        {"codigo": "6135", "nombre": "Comercio al por Mayor y al por Menor", "tipo_cuenta": "EGRESO", "cuenta_padre": "61"}
    ]
    
    created_count = 0
    cuenta_objects = {}  # Para mantener referencia de cuentas padre
    
    # Crear cuentas en orden jerárquico
    for cuenta_data in cuentas:
        try:
            # Verificar si la cuenta ya existe
            existing_cuenta = session.exec(select(CuentaContable).where(
                CuentaContable.codigo == cuenta_data["codigo"]
            )).first()
            
            if existing_cuenta:
                cuenta_objects[cuenta_data["codigo"]] = existing_cuenta
                continue
            
            # Determinar cuenta padre
            cuenta_padre_id = None
            if cuenta_data["cuenta_padre"]:
                cuenta_padre = cuenta_objects.get(cuenta_data["cuenta_padre"])
                if cuenta_padre:
                    cuenta_padre_id = cuenta_padre.id
            
            cuenta = CuentaContable(
                codigo=cuenta_data["codigo"],
                nombre=cuenta_data["nombre"],
                tipo_cuenta=cuenta_data["tipo_cuenta"],
                cuenta_padre_id=cuenta_padre_id,
                is_active=True,
                created_at=datetime.now()
            )
            
            session.add(cuenta)
            session.flush()  # Para obtener el ID
            cuenta_objects[cuenta_data["codigo"]] = cuenta
            created_count += 1
            print(f"   ✅ Cuenta creada: {cuenta_data['codigo']} - {cuenta_data['nombre']}")
            
        except Exception as e:
            print(f"   ❌ Error creando cuenta {cuenta_data['codigo']}: {e}")
    
    session.commit()
    print(f"✅ {created_count} cuentas contables creadas")

def create_sample_products(session: Session):
    """Crear productos de ejemplo"""
    print("📦 Creando productos de ejemplo...")
    
    productos = [
        {
            "sku": "PROD001",
            "nombre": "Producto Demo 1",
            "descripcion": "Producto de demostración para pruebas",
            "precio_base": Decimal("50000.00"),
            "precio_publico": Decimal("65000.00"),
            "stock": 100
        },
        {
            "sku": "PROD002", 
            "nombre": "Producto Demo 2",
            "descripcion": "Segundo producto de demostración",
            "precio_base": Decimal("75000.00"),
            "precio_publico": Decimal("97500.00"),
            "stock": 50
        },
        {
            "sku": "SERV001",
            "nombre": "Servicio Demo 1", 
            "descripcion": "Servicio de demostración",
            "precio_base": Decimal("100000.00"),
            "precio_publico": Decimal("120000.00"),
            "stock": 0
        }
    ]
    
    created_count = 0
    for prod_data in productos:
        try:
            # Verificar si el producto ya existe
            existing_product = session.exec(select(Product).where(Product.sku == prod_data["sku"])).first()
            if existing_product:
                print(f"   ⚠️  Producto {prod_data['sku']} ya existe, saltando...")
                continue
            
            producto = Product(
                sku=prod_data["sku"],
                nombre=prod_data["nombre"],
                descripcion=prod_data["descripcion"],
                precio_base=prod_data["precio_base"],
                precio_publico=prod_data["precio_publico"],
                stock=prod_data["stock"],
                is_active=True,
                created_at=datetime.now()
            )
            
            session.add(producto)
            created_count += 1
            print(f"   ✅ Producto creado: {prod_data['sku']} - {prod_data['nombre']}")
            
        except Exception as e:
            print(f"   ❌ Error creando producto {prod_data['sku']}: {e}")
    
    session.commit()
    print(f"✅ {created_count} productos de ejemplo creados")

def create_sample_clients(session: Session):
    """Crear clientes de ejemplo"""
    print("👥 Creando clientes de ejemplo...")
    
    clientes = [
        {
            "numero_documento": "12345678",
            "tipo_documento": "CEDULA",
            "nombre_completo": "Cliente Demo Uno",
            "email": "cliente1@demo.com",
            "telefono": "3001234567",
            "direccion": "Calle 123 #45-67",
            "ciudad": "Bogotá",
            "tipo_cliente": "PERSONA_NATURAL"
        },
        {
            "numero_documento": "900123456",
            "tipo_documento": "NIT", 
            "nombre_completo": "Empresa Demo S.A.S",
            "email": "contacto@empresademo.com",
            "telefono": "6012345678",
            "direccion": "Carrera 98 #76-54",
            "ciudad": "Medellín", 
            "tipo_cliente": "EMPRESA"
        }
    ]
    
    created_count = 0
    for cliente_data in clientes:
        try:
            # Verificar si el cliente ya existe
            existing_client = session.exec(select(Cliente).where(
                Cliente.numero_documento == cliente_data["numero_documento"]
            )).first()
            if existing_client:
                print(f"   ⚠️  Cliente {cliente_data['numero_documento']} ya existe, saltando...")
                continue
            
            cliente = Cliente(
                numero_documento=cliente_data["numero_documento"],
                tipo_documento=cliente_data["tipo_documento"],
                nombre_completo=cliente_data["nombre_completo"],
                email=cliente_data["email"],
                telefono=cliente_data["telefono"],
                direccion=cliente_data["direccion"],
                ciudad=cliente_data["ciudad"],
                tipo_cliente=cliente_data["tipo_cliente"],
                is_active=True,
                created_at=datetime.now()
            )
            
            session.add(cliente)
            created_count += 1
            print(f"   ✅ Cliente creado: {cliente_data['numero_documento']} - {cliente_data['nombre_completo']}")
            
        except Exception as e:
            print(f"   ❌ Error creando cliente {cliente_data['numero_documento']}: {e}")
    
    session.commit()
    print(f"✅ {created_count} clientes de ejemplo creados")

def main():
    """Función principal del script de inicialización"""
    print("🚀 Iniciando configuración completa de la base de datos")
    print("=" * 60)
    
    try:
        # Crear engine de conexión
        print(f"🔌 Conectando a la base de datos...")
        print(f"   URL: {DATABASE_URL}")
        engine = create_engine(DATABASE_URL)
        
        # Probar conexión
        with engine.connect() as conn:
            print("✅ Conexión a la base de datos exitosa")
        
        # Crear todas las tablas
        if not create_tables(engine):
            print("❌ Error en la creación de tablas. Abortando.")
            return False
        
        # Crear sesión para operaciones de datos
        with Session(engine) as session:
            # Crear datos iniciales
            create_test_users(session)
            create_chart_of_accounts(session)
            create_sample_products(session)
            create_sample_clients(session)
        
        print("\n" + "=" * 60)
        print("🎉 Inicialización de base de datos completada exitosamente")
        print("\n📋 Datos creados:")
        print("   👥 5 usuarios de prueba (admin, gerente, contador, vendedor, demo)")
        print("   📊 35+ cuentas contables (plan colombiano)")
        print("   📦 3 productos de ejemplo")
        print("   🙋‍♂️ 2 clientes de ejemplo")
        print("\n🔑 Credenciales de acceso:")
        print("   Admin: admin@empresa.com / admin123")
        print("   Gerente: gerente@empresa.com / gerente123") 
        print("   Contador: contador@empresa.com / contador123")
        print("   Vendedor: vendedor@empresa.com / vendedor123")
        print("   Demo: demo@empresa.com / demo123")
        print("\n🌐 Acceso a la aplicación:")
        print("   Frontend: http://localhost:3000")
        print("   Backend: http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la inicialización: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)