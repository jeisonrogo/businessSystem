"""
Configuración de la sesión de base de datos.
Este módulo maneja la conexión y configuración de SQLModel con PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

# Importar todos los modelos para que estén disponibles para Alembic
from app.domain.models.user import User  # noqa: F401
from app.domain.models.product import Product

# Configuración de la base de datos desde variables de entorno
# Usar postgresql+psycopg para especificar el dialecto de psycopg3
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://admin:admin@localhost:5432/inventario")

# Crear el engine de SQLAlchemy usando psycopg3
def create_db_engine():
    """
    Crea y retorna el engine de base de datos.
    Se separa en una función para evitar errores de conexión durante imports.
    """
    return create_engine(
        DATABASE_URL,
        echo=True,  # Para debugging, cambiar a False en producción
        pool_pre_ping=True,  # Verifica la conexión antes de usarla
        pool_recycle=300,  # Recicla conexiones cada 5 minutos
    )


# Engine global que se inicializa cuando se necesita
engine = None


def get_engine():
    """
    Obtiene el engine de base de datos, creándolo si es necesario.
    """
    global engine
    if engine is None:
        engine = create_db_engine()
    return engine


def create_db_and_tables():
    """
    Crea las tablas de la base de datos.
    Se llamará durante la inicialización de la aplicación.
    """
    SQLModel.metadata.create_all(get_engine())


def get_session():
    """
    Generador de sesiones de base de datos para inyección de dependencias.
    
    Yields:
        Session: Una sesión de SQLModel para interactuar con la base de datos.
    """
    with Session(get_engine()) as session:
        yield session 