import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware import JWTAuthMiddleware
from src.config import AppConfig
from src.apps import EmbeddingController, DatasetController
from src.infrastructure.events import setup_event_consumers
from src.contexts.embedding.infrastructure import (
    create_embedding_repository,
    create_dataset_repository, 
)
from src.contexts.embedding.application import get_service_factory

def setup_logging(config: AppConfig):
    log_level = getattr(logging, config.log_level)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)


def create_app(config: AppConfig) -> FastAPI:
    setup_logging(config)

    app = FastAPI(
        title="Embedding Service",
        description="Service for embedding datasets",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # app.add_middleware(JWTAuthMiddleware)

    embedding_controller = EmbeddingController()
    dataset_controller = DatasetController()

    app.include_router(embedding_controller.router)
    app.include_router(dataset_controller.router)
    
    setup_event_consumers(app)

    @app.on_event("startup")
    async def startup_db_client():
        logger = logging.getLogger(__name__)
        
        try:
            embedding_repo = await create_embedding_repository(config)
            dataset_repo = await create_dataset_repository(config)
            
            service_factory = get_service_factory()
            service_factory.register_embedding_repository(embedding_repo)
            service_factory.register_dataset_repository(dataset_repo)
            
        except Exception as e:
            logger.error(f"Error initializing repositories: {str(e)}")
            raise

    @app.on_event("shutdown")
    async def shutdown_db_client():
        pass

    return app
                
