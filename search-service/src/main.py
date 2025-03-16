import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Search Service API",
    description="API para el servicio de búsqueda semántica",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar los repositorios y servicios
from .contexts.search import (
    SearchService,
    EmbeddingRepositoryImpl,
    SearchRepositoryImpl
)

# Importar el controlador
from .apps.api.search_controller import SearchController

# Inicializar repositorios
embedding_repository = EmbeddingRepositoryImpl()
search_repository = SearchRepositoryImpl()

# Inicializar servicio
search_service = SearchService(
    embedding_repository=embedding_repository,
    search_repository=search_repository
)

# Inicializar controlador
search_controller = SearchController(search_service=search_service)

# Registrar rutas
app.include_router(search_controller.router)

# Ruta de estado
@app.get("/health")
async def health_check():
    """Verifica el estado del servicio"""
    return {"status": "ok"}

# Ruta principal
@app.get("/")
async def root():
    """Ruta principal"""
    return {
        "service": "Search Service",
        "version": "1.0.0",
        "status": "running"
    }

# Registrar eventos de inicio y apagado
@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("Iniciando servicio de búsqueda")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de apagado de la aplicación"""
    logger.info("Deteniendo servicio de búsqueda")

# Punto de entrada para uvicorn cuando se ejecuta como módulo
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "False").lower() == "true"
    
    logger.info(f"Iniciando servidor en {host}:{port} (reload={reload})")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
