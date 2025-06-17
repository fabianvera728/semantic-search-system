import os
from dataclasses import dataclass
from typing import List


@dataclass
class AppConfig:
    """Configuración de la aplicación Data Harvester."""
    
    # Configuración del servidor
    host: str
    port: int
    debug: bool
    
    # Configuración de CORS
    allowed_origins: List[str]
    
    # URLs de servicios externos
    auth_service_url: str
    data_storage_url: str
    data_processor_url: str
    orchestrator_url: str
    
    # Configuración de JWT para comunicación entre servicios
    jwt_secret: str
    jwt_algorithm: str
    
    # Configuración de logging
    log_level: str
    
    # Configuración de almacenamiento
    upload_dir: str
    data_dir: str


def get_app_config() -> AppConfig:
    """Obtiene la configuración de la aplicación desde variables de entorno."""
    
    return AppConfig(
        # Servidor
        host=os.getenv("DATA_HARVESTER_HOST", "0.0.0.0"),
        port=int(os.getenv("DATA_HARVESTER_PORT", "8002")),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        
        # CORS
        allowed_origins=os.getenv("DATA_HARVESTER_ALLOWED_ORIGINS", "*").split(","),
        
        # Servicios externos
        auth_service_url=os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
        data_storage_url=os.getenv("DATA_STORAGE_URL", "http://data-storage:8003"),
        data_processor_url=os.getenv("DATA_PROCESSOR_URL", "http://data-processor:8004"),
        orchestrator_url=os.getenv("ORCHESTRATOR_URL", "http://orchestrator:8000"),
        
        # JWT para comunicación entre servicios
        jwt_secret=os.getenv("AUTH_SERVICE_JWT_SECRET", "your-secret-key"),
        jwt_algorithm=os.getenv("AUTH_SERVICE_JWT_ALGORITHM", "HS256"),
        
        # Logging
        log_level=os.getenv("DATA_HARVESTER_LOG_LEVEL", "INFO"),
        
        # Almacenamiento
        upload_dir=os.getenv("UPLOAD_DIR", "/app/uploads"),
        data_dir=os.getenv("DATA_DIR", "/app/data")
    ) 