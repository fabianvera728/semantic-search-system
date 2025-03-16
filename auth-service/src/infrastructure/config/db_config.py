import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


@dataclass
class DBConfig:
    """Configuración de la base de datos."""
    
    # Configuración de MySQL
    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int
    pool_recycle: int
    
    # Configuración de conexión
    connect_timeout: int
    charset: str


def get_db_config() -> DBConfig:
    """
    Carga la configuración de la base de datos desde variables de entorno.
    
    Returns:
        DBConfig: Configuración de la base de datos
    """
    # Cargar variables de entorno desde .env si existe
    load_dotenv()
    
    # Configuración de MySQL
    host = os.getenv("AUTH_DB_HOST", "mysql")
    port = int(os.getenv("AUTH_DB_PORT", "3306"))
    user = os.getenv("AUTH_DB_USER", "root")
    password = os.getenv("AUTH_DB_PASSWORD", "password")
    database = os.getenv("AUTH_DB_DATABASE", "auth_service")
    pool_size = int(os.getenv("AUTH_DB_POOL_SIZE", "5"))
    pool_recycle = int(os.getenv("AUTH_DB_POOL_RECYCLE", "3600"))
    
    # Configuración de conexión
    connect_timeout = int(os.getenv("AUTH_DB_CONNECT_TIMEOUT", "10"))
    charset = os.getenv("AUTH_DB_CHARSET", "utf8mb4")
    
    return DBConfig(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        pool_size=pool_size,
        pool_recycle=pool_recycle,
        connect_timeout=connect_timeout,
        charset=charset
    ) 