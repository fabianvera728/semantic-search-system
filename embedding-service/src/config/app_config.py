import os
from typing import List
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    host: str
    port: int
    allowed_origins: List[str]
    log_level: str
    
    auth_service_url: str
    data_storage_url: str
    
    embedding_model: str
    
    vector_db_type: str
    
    chromadb_host: str
    chromadb_port: int
    chromadb_persistence_path: str
    
    cache_enabled: bool
    cache_ttl: int
    
    batch_size: int
    request_timeout: int
    
    # Configuración de eventos
    event_consumer_enabled: bool
    event_consumer_type: str  # "rabbitmq" o "http"
    
    # Configuración de RabbitMQ
    rabbitmq_url: str
    rabbitmq_exchange: str
    rabbitmq_queue: str
    
    log_file: str = None
    

def get_app_config() -> AppConfig:
    load_dotenv()

    return AppConfig(
        host=os.getenv("EMBEDDING_SERVICE_HOST", "0.0.0.0"),
        port=int(os.getenv("EMBEDDING_SERVICE_PORT", "8005")),
        allowed_origins=os.getenv("EMBEDDING_SERVICE_ALLOWED_ORIGINS", "*").split(","),
        log_level=os.getenv("EMBEDDING_SERVICE_LOG_LEVEL", "INFO").upper(),
        auth_service_url=os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
        data_storage_url=os.getenv("DATA_STORAGE_URL", "http://data-storage:8003"),
        embedding_model=os.getenv("EMBEDDING_SERVICE_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
        vector_db_type=os.getenv("VECTOR_DB_TYPE", "chromadb"),
        chromadb_host=os.getenv("CHROMADB_HOST", "chromadb"),
        chromadb_port=int(os.getenv("CHROMADB_PORT", "8000")),
        chromadb_persistence_path=os.getenv("CHROMADB_PERSISTENCE_PATH", "/app/storage/chroma"),
        cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
        cache_ttl=int(os.getenv("CACHE_TTL", "3600")),
        batch_size=int(os.getenv("BATCH_SIZE", "32")),
        request_timeout=int(os.getenv("REQUEST_TIMEOUT", "60")),
        
        # Configuración de eventos
        event_consumer_enabled=os.getenv("EVENT_CONSUMER_ENABLED", "true").lower() == "true",
        event_consumer_type=os.getenv("EVENT_CONSUMER_TYPE", "rabbitmq"),
        
        # Configuración de RabbitMQ
        rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/"),
        rabbitmq_exchange=os.getenv("RABBITMQ_EXCHANGE", "semantic_search_events"),
        rabbitmq_queue=os.getenv("RABBITMQ_QUEUE", "embedding_service_events"),
        
        log_file=os.getenv("EMBEDDING_SERVICE_LOG_FILE", None),
    )  

