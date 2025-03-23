import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware import JWTAuthMiddleware
from src.config import AppConfig
from src.apps import SearchController
from src.contexts.search import (
    SearchService,
    EmbeddingRepositoryImpl,
    SearchRepositoryImpl
)


def setup_logging(config: AppConfig):
    log_level = getattr(logging, config.log_level)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logging.getLogger().addHandler(file_handler)


def create_app(config: AppConfig) -> FastAPI:
    setup_logging(config)

    app = FastAPI(
        title="Search Service",
        description="Service for searching datasets",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # app.add_middleware(JWTAuthMiddleware)

    @app.on_event("startup")
    async def startup_db_client():
        pass

    @app.on_event("shutdown")
    async def shutdown_db_client():
        pass

    embedding_repository = EmbeddingRepositoryImpl()
    search_repository = SearchRepositoryImpl()

    search_service = SearchService(
        embedding_repository=embedding_repository,
        search_repository=search_repository
    )

    search_controller = SearchController(search_service=search_service)

    app.include_router(search_controller.router)

    return app

    
    
    
    
    

