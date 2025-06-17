import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.app_config import AppConfig
from src.contexts.harvest.infrastructure.api.harvest_router import harvest_router
from src.contexts.integration.infrastructure.api.integration_router import integration_router


def create_app(config: AppConfig) -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Crear aplicación
    app = FastAPI(
        title="Data Harvester Service",
        description="Servicio para cosecha de datos e integraciones",
        version="2.0.0",
        debug=config.debug
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Registrar routers
    app.include_router(harvest_router, prefix="/api/harvest", tags=["harvest"])
    app.include_router(integration_router, prefix="/api", tags=["integrations"])
    
    # Endpoints legacy para compatibilidad
    app.include_router(harvest_router, prefix="", tags=["harvest-legacy"])
    
    return app 