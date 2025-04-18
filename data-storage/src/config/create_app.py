import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app_config import AppConfig
from src.contexts.dataset.infrastructure import SQLAlchemyDatasetRepository, InMemoryDatasetRepository
from src.infrastructure.db import db
from src.apps.api import DatasetController


from src.infrastructure.events import get_event_bus
from src.middleware import JWTAuthMiddleware

def setup_logging(config: AppConfig) -> None:
    log_level = getattr(logging, config.log_level.upper())
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)


def setup_event_bus(config: AppConfig) -> None:
    if config.enable_event_publishing:
        from src.infrastructure.events import create_message_broker
        
        event_bus = get_event_bus()
        
        # Crear el message broker de RabbitMQ
        message_broker = create_message_broker(config)
        event_bus.set_message_broker(message_broker)
        
        logging.info("Event bus initialized with RabbitMQ message broker")
    else:
        logging.info("Event publishing is disabled")


def create_app(config: AppConfig) -> FastAPI:
    """Crea y configura la aplicación FastAPI"""
    setup_logging(config)
    
    app = FastAPI(
        title="Data Storage Service",
        description="Service for managing datasets and their data",
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # app.add_middleware(JWTAuthMiddleware)
    
    # Inicializar el bus de eventos
    setup_event_bus(config)
    
    # Eventos del ciclo de vida
    @app.on_event("startup")
    async def startup_db_client():
        from ..contexts.dataset.application import DatasetService
        
        if not config.use_in_memory_db:
            await db.connect(
                host=config.mysql_host,
                port=config.mysql_port,
                user=config.mysql_user,
                password=config.mysql_password,
                database=config.mysql_database,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_recycle=3600,
                pool_pre_ping=True,
                use_connection_pool=True
            )
            
            await db.create_tables()
            
            repository = SQLAlchemyDatasetRepository()
        else:
            repository = InMemoryDatasetRepository()
            logging.info("Using in-memory database")
        
        dataset_service = DatasetService(repository)
        dataset_controller = DatasetController(dataset_service)
        
        app.include_router(dataset_controller.router)


    @app.on_event("shutdown")
    async def shutdown_db_client():        
        if not config.use_in_memory_db:
            await db.disconnect()
            logging.info("Database disconnected")
    
    return app
    
