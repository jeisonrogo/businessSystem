"""
Configuración de la sesión de base de datos.
Este módulo maneja la conexión y configuración de SQLModel con PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

# Configuración de la base de datos desde variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/business_system")

# Crear el engine de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Para debugging, cambiar a False en producción
    pool_pre_ping=True,  # Verifica la conexión antes de usarla
    pool_recycle=300,  # Recicla conexiones cada 5 minutos
)


def create_db_and_tables():
    """
    Crea las tablas de la base de datos.
    Se llamará durante la inicialización de la aplicación.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Generador de sesiones de base de datos para inyección de dependencias.
    
    Yields:
        Session: Una sesión de SQLModel para interactuar con la base de datos.
    """
    with Session(engine) as session:
        yield session 