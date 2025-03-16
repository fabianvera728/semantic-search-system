import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .app_config import AppConfig
from src.domain.services.auth_service import AuthService
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_use_case import LoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.logout_use_case import LogoutUseCase
from src.application.use_cases.validate_token_use_case import ValidateTokenUseCase
from src.infrastructure.adapters.repositories import (
    InMemoryUserRepository, InMemoryTokenRepository,
    SQLAlchemyUserRepository, SQLAlchemyTokenRepository
)
from src.infrastructure.adapters.controllers.auth_controller import AuthController
from src.infrastructure.db.database import db


def setup_logging(config):
    """Configura el sistema de logging."""
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
    """
    Crea y configura la aplicación FastAPI.
    
    Args:
        config: Configuración de la aplicación
        
    Returns:
        La aplicación FastAPI configurada
    """
    # Configurar logging
    setup_logging(config)
    
    # Crear aplicación FastAPI
    app = FastAPI(
        title="Authentication Service",
        description="Servicio de autenticación para el sistema de búsqueda semántica",
        version="1.0.0"
    )
    
    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # Evento de inicio
    @app.on_event("startup")
    async def startup_db_client():
        # Crear repositorios
        if config.use_in_memory_db:
            # Crear repositorios en memoria
            logging.info("Creando repositorios en memoria...")
            user_repository = InMemoryUserRepository()
            token_repository = InMemoryTokenRepository()
        else:
            logging.info(f"Conectando a la base de datos MySQL en {config.mysql_host}:{config.mysql_port}")
            await db.connect(
                host=config.mysql_host,
                port=config.mysql_port,
                user=config.mysql_user,
                password=config.mysql_password,
                database=config.mysql_database
            )
            
            logging.info("Creando tablas en la base de datos...")
            await db.create_tables()
            
            logging.info("Creando repositorios SQLAlchemy...")
            user_repository = SQLAlchemyUserRepository()
            token_repository = SQLAlchemyTokenRepository()
        
        auth_service = AuthService(
            user_repository=user_repository,
            token_repository=token_repository,
            jwt_secret=config.jwt_secret,
            jwt_algorithm=config.jwt_algorithm,
            access_token_expires_in=config.access_token_expires_in,
            refresh_token_expires_in=config.refresh_token_expires_in
        )
        
        register_user_use_case = RegisterUserUseCase(auth_service)
        login_use_case = LoginUseCase(auth_service)
        refresh_token_use_case = RefreshTokenUseCase(auth_service)
        logout_use_case = LogoutUseCase(auth_service)
        validate_token_use_case = ValidateTokenUseCase(auth_service)
        
        auth_controller = AuthController(
            register_user_use_case=register_user_use_case,
            login_use_case=login_use_case,
            refresh_token_use_case=refresh_token_use_case,
            logout_use_case=logout_use_case,
            validate_token_use_case=validate_token_use_case,
            auth_service=auth_service
        )
        
        auth_controller.auth_service = auth_service

        app.include_router(auth_controller.router)
    
    @app.on_event("shutdown")
    async def shutdown_db_client():
        if not config.use_in_memory_db:
            logging.info("Cerrando conexión a la base de datos MySQL...")
            await db.close()
    
    @app.get("/")
    async def root():
        """Endpoint raíz para verificar que el servicio está funcionando."""
        return {
            "service": "Authentication Service",
            "version": "1.0.0",
            "status": "running"
        }
    
    @app.get("/health")
    async def health():
        """Endpoint para verificar la salud del servicio."""
        return {"status": "healthy"}
    
    return app 