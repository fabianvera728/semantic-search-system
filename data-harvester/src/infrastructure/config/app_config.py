import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Configuración de la aplicación."""
    
    # Directorios
    upload_dir: str
    data_dir: str
    
    # Configuración del servidor
    host: str
    port: int
    
    # Configuración de seguridad
    api_key: Optional[str]
    allowed_origins: List[str]
    
    # Límites
    max_upload_size_mb: int
    max_concurrent_jobs: int
    job_timeout_seconds: int
    
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
    
    # Directorios
    base_dir = os.getenv("DATA_HARVESTER_BASE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
    upload_dir = os.getenv("DATA_HARVESTER_UPLOAD_DIR", os.path.join(base_dir, "uploads"))
    data_dir = os.getenv("DATA_HARVESTER_DATA_DIR", os.path.join(base_dir, "data"))
    
    # Configuración del servidor
    host = os.getenv("DATA_HARVESTER_HOST", "0.0.0.0")
    port = int(os.getenv("DATA_HARVESTER_PORT", "8000"))
    
    # Configuración de seguridad
    api_key = os.getenv("DATA_HARVESTER_API_KEY")
    allowed_origins = os.getenv("DATA_HARVESTER_ALLOWED_ORIGINS", "*").split(",")
    
    # Límites
    max_upload_size_mb = int(os.getenv("DATA_HARVESTER_MAX_UPLOAD_SIZE_MB", "100"))
    max_concurrent_jobs = int(os.getenv("DATA_HARVESTER_MAX_CONCURRENT_JOBS", "5"))
    job_timeout_seconds = int(os.getenv("DATA_HARVESTER_JOB_TIMEOUT_SECONDS", "3600"))
    
    # Configuración de logging
    log_level = os.getenv("DATA_HARVESTER_LOG_LEVEL", "INFO")
    log_file = os.getenv("DATA_HARVESTER_LOG_FILE")
    
    return AppConfig(
        upload_dir=upload_dir,
        data_dir=data_dir,
        host=host,
        port=port,
        api_key=api_key,
        allowed_origins=allowed_origins,
        max_upload_size_mb=max_upload_size_mb,
        max_concurrent_jobs=max_concurrent_jobs,
        job_timeout_seconds=job_timeout_seconds,
        log_level=log_level,
        log_file=log_file
    ) 