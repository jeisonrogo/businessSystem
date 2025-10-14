#!/usr/bin/env python3
"""
Script para crear usuario administrador inicial.
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlmodel import Session, create_engine, select
from app.domain.models.user import User
from app.infrastructure.database.session import get_engine
from passlib.context import CryptContext
from uuid import uuid4

# Configuración para hashear contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    """Crear usuario administrador inicial."""
    print("👤 Creando usuario administrador...")
    
    # Conectar a la base de datos
    engine = get_engine()
    
    with Session(engine) as session:
        # Verificar si ya existe el admin
        admin_exists = session.exec(
            select(User).where(User.email == "admin@empresa.com")
        ).first()
        
        if admin_exists:
            print("⚠️ Usuario admin@empresa.com ya existe")
            return admin_exists
        
        # Crear nuevo usuario admin
        hashed_password = pwd_context.hash("admin12345")
        
        admin_user = User(
            id=uuid4(),
            email="admin@empresa.com",
            nombre="Administrador Sistema",
            rol="administrador",
            hashed_password=hashed_password,
            is_active=True
        )
        
        session.add(admin_user)
        session.commit()
        session.refresh(admin_user)
        
        print("✅ Usuario administrador creado:")
        print(f"   Email: {admin_user.email}")
        print(f"   Nombre: {admin_user.nombre}")
        print(f"   Rol: {admin_user.rol}")
        print(f"   ID: {admin_user.id}")
        
        return admin_user

if __name__ == "__main__":
    try:
        admin = create_admin()
        print("\n🎉 Usuario administrador listo para usar")
        print("📱 Credenciales: admin@empresa.com / admin12345")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)