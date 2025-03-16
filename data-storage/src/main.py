import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .contexts.dataset.application import DatasetService
from .contexts.dataset.infrastructure import MySQLDatasetRepository, InMemoryDatasetRepository
from .apps.api import DatasetController
from .infrastructure.db import init_db_pool, create_tables, close_db_pool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Environment variables
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "data_storage")
USE_IN_MEMORY_DB = os.getenv("USE_IN_MEMORY_DB", "false").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


# Create FastAPI app
app = FastAPI(
    title="Data Storage Service",
    description="Service for storing and retrieving datasets",
    version="1.0.0"
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_db_client():
    if not USE_IN_MEMORY_DB:
        # Initialize MySQL connection pool
        app.db_pool = await init_db_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DATABASE
        )
        
        # Create tables if they don't exist
        await create_tables(app.db_pool)
        
        # Create dataset repository
        dataset_repository = MySQLDatasetRepository(app.db_pool)
    else:
        # Use in-memory repository for testing
        dataset_repository = InMemoryDatasetRepository()
    
    # Create dataset service
    dataset_service = DatasetService(dataset_repository)
    
    # Create and register controllers
    dataset_controller = DatasetController(dataset_service)
    app.include_router(dataset_controller.router)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_db_client():
    if not USE_IN_MEMORY_DB and hasattr(app, "db_pool"):
        await close_db_pool(app.db_pool)


# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Data Storage Service",
        "version": "1.0.0",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run("src.main:app", host=host, port=port, reload=True) 