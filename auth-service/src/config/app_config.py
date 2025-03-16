import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Configuración de la aplicación."""
    
    # Configuración del servidor
    host: str
    port: int
    allowed_origins: List[str]
    log_level: str
    log_file: Optional[str]
    
    # Configuración de JWT
    jwt_secret: str
    jwt_algorithm: str
    access_token_expires_in: int
    refresh_token_expires_in: int
    
    # Configuración de la base de datos
    use_in_memory_db: bool
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str


def get_app_config() -> AppConfig:
    """
    Carga la configuración de la aplicación desde variables de entorno.
    
    Returns:
        AppConfig: Configuración de la aplicación
    """
    # Cargar variables de entorno desde .env si existe
    load_dotenv()
    
    # Configuración del servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", None)
    
    # Configuración de JWT
    jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expires_in = int(os.getenv("ACCESS_TOKEN_EXPIRES_IN", "3600"))
    refresh_token_expires_in = int(os.getenv("REFRESH_TOKEN_EXPIRES_IN", "2592000"))
    
    # Configuración de la base de datos
    use_in_memory_db = os.getenv("USE_IN_MEMORY_DB", "false").lower() == "true"
    mysql_host = os.getenv("DB_HOST", "mysql")
    mysql_port = int(os.getenv("DB_PORT", "3306"))
    mysql_user = os.getenv("DB_USER", "root")
    mysql_password = os.getenv("DB_PASSWORD", "password")
    mysql_database = os.getenv("DB_DATABASE", "auth_service")
    
    return AppConfig(
        host=host,
        port=port,
        allowed_origins=allowed_origins,
        log_level=log_level,
        log_file=log_file,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_expires_in=access_token_expires_in,
        refresh_token_expires_in=refresh_token_expires_in,
        use_in_memory_db=use_in_memory_db,
        mysql_host=mysql_host,
        mysql_port=mysql_port,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        mysql_database=mysql_database
    ) 