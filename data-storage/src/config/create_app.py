import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app_config import get_app_config, AppConfig
from src.apps.api import DatasetController
from src.contexts.dataset.application import DatasetService 
from src.contexts.dataset.infrastructure import MySQLDatasetRepository, InMemoryDatasetRepository
from src.infrastructure.db import init_db_pool, create_tables, close_db_pool

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

    @app.on_event("startup")
    async def startup_db_client():
        if not config.use_in_memory_db:
            app.db_pool = await init_db_pool(
                host=config.mysql_host,
                port=config.mysql_port,
                user=config.mysql_user,
                password=config.mysql_password,
                db=config.mysql_database
            )
            
            await create_tables(app.db_pool)
            
            dataset_repository = MySQLDatasetRepository(app.db_pool)
        else:
            dataset_repository = InMemoryDatasetRepository()
        
        dataset_service = DatasetService(dataset_repository)        
        dataset_controller = DatasetController(dataset_service)
        app.include_router(dataset_controller.router)


    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_db_client():
        if not config.use_in_memory_db and hasattr(app, "db_pool"):
            await close_db_pool(app.db_pool)
    
    return app
    
