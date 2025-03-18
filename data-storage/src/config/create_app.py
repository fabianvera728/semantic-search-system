import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app_config import AppConfig
from src.apps.api import DatasetController
from src.contexts.dataset.application import DatasetService 
from src.contexts.dataset.infrastructure import SQLAlchemyDatasetRepository, InMemoryDatasetRepository
from src.infrastructure.db import db
from src.middleware import JWTAuthMiddleware

def setup_logging(config):
    log_level = getattr(logging, config.log_level)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)


def create_app(config: AppConfig) -> FastAPI:
    setup_logging(config)
    
    app = FastAPI(
        title="Data Storage Service",
        description="Service for storing and retrieving datasets",
        version="1.0.0"
    )  

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(JWTAuthMiddleware)

    @app.on_event("startup")
    async def startup_db_client():
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
            
            dataset_repository = SQLAlchemyDatasetRepository()
        else:
            dataset_repository = InMemoryDatasetRepository()
        
        dataset_service = DatasetService(dataset_repository)        
        dataset_controller = DatasetController(dataset_service)
        app.include_router(dataset_controller.router)


    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_db_client():
        if not config.use_in_memory_db:
            await db.close()
    
    return app
    
