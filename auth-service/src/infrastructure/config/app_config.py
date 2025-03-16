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
    
    # Configuración de seguridad
    jwt_secret: str
    jwt_algorithm: str
    access_token_expires_in: int
    refresh_token_expires_in: int
    allowed_origins: List[str]
    
    # Configuración de logging
    log_level: str
    log_file: Optional[str]


def get_app_config() -> AppConfig:
    """
    Carga la configuración de la aplicación desde variables de entorno.
    
    Returns:
        AppConfig: Configuración de la aplicación
    """
    # Cargar variables de entorno desde .env si existe
    load_dotenv()
    
    # Configuración del servidor
    host = os.getenv("AUTH_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("AUTH_SERVICE_PORT", "8001"))
    
    # Configuración de seguridad
    jwt_secret = os.getenv("AUTH_SERVICE_JWT_SECRET", "your-secret-key")
    jwt_algorithm = os.getenv("AUTH_SERVICE_JWT_ALGORITHM", "HS256")
    access_token_expires_in = int(os.getenv("AUTH_SERVICE_ACCESS_TOKEN_EXPIRES_IN", "3600"))
    refresh_token_expires_in = int(os.getenv("AUTH_SERVICE_REFRESH_TOKEN_EXPIRES_IN", "2592000"))
    allowed_origins = os.getenv("AUTH_SERVICE_ALLOWED_ORIGINS", "*").split(",")
    
    # Configuración de logging
    log_level = os.getenv("AUTH_SERVICE_LOG_LEVEL", "INFO")
    log_file = os.getenv("AUTH_SERVICE_LOG_FILE")
    
    return AppConfig(
        host=host,
        port=port,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_expires_in=access_token_expires_in,
        refresh_token_expires_in=refresh_token_expires_in,
        allowed_origins=allowed_origins,
        log_level=log_level,
        log_file=log_file
    ) 