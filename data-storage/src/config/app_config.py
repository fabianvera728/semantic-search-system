import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class AppConfig:    
    host: str
    port: int

    allowed_origins: List[str]
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    use_in_memory_db: bool

    # Configuración de JWT
    jwt_secret: str
    jwt_algorithm: str

    # URLs de servicios externos
    embedding_service_url: str
    auth_service_url: str

    # Configuración de eventos
    enable_event_publishing: bool
    event_broker_type: str  # Solo soporta "rabbitmq"
    
    # Configuración de RabbitMQ
    rabbitmq_url: str
    rabbitmq_exchange: str

    log_level: str
    log_file: Optional[str]


def get_app_config() -> AppConfig:
    load_dotenv()
    
    host = os.getenv("DATA_STORAGE_HOST", "0.0.0.0")
    port = int(os.getenv("DATA_STORAGE_PORT", "8003"))
    allowed_origins = os.getenv("DATA_STORAGE_ALLOWED_ORIGINS", "*").split(",")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "password")
    mysql_database = os.getenv("MYSQL_DATABASE", "data_storage")
    use_in_memory_db = os.getenv("USE_IN_MEMORY_DB", "false").lower() == "true"
    
    # Configuración de JWT
    jwt_secret = os.getenv("AUTH_SERVICE_JWT_SECRET", "your-secret-key")
    jwt_algorithm = os.getenv("AUTH_SERVICE_JWT_ALGORITHM", "HS256")
    
    # URLs de servicios externos
    embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://embedding-service:8005")
    auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    
    # Configuración de eventos
    enable_event_publishing = os.getenv("ENABLE_EVENT_PUBLISHING", "true").lower() == "true"
    event_broker_type = os.getenv("EVENT_BROKER_TYPE", "rabbitmq")
    
    # Verificar que el tipo de broker sea válido
    if event_broker_type.lower() != "rabbitmq":
        raise ValueError("EVENT_BROKER_TYPE solo soporta 'rabbitmq'")
    
    # Configuración de RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    rabbitmq_exchange = os.getenv("RABBITMQ_EXCHANGE", "semantic_search_events")
    
    log_level = os.getenv("DATA_STORAGE_LOG_LEVEL", "DEBUG")
    log_file = os.getenv("DATA_STORAGE_LOG_FILE")
    
    return AppConfig(
        host=host,
        port=port,
        allowed_origins=allowed_origins,
        mysql_host=mysql_host,
        mysql_port=mysql_port,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        mysql_database=mysql_database,
        use_in_memory_db=use_in_memory_db,
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        embedding_service_url=embedding_service_url,
        auth_service_url=auth_service_url,
        enable_event_publishing=enable_event_publishing,
        event_broker_type=event_broker_type,
        rabbitmq_url=rabbitmq_url,
        rabbitmq_exchange=rabbitmq_exchange,
        log_level=log_level,
        log_file=log_file
    ) 