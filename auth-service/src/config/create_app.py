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
    MySQLUserRepository, MySQLTokenRepository,
    create_pool, init_db
)
from src.infrastructure.adapters.controllers.auth_controller import AuthController


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
        if not config.use_in_memory_db:
            # Crear pool de conexiones
            logging.info(f"Creando pool de conexiones a MySQL en {config.mysql_host}:{config.mysql_port}")
            app.db_pool = await create_pool(
                host=config.mysql_host,
                port=config.mysql_port,
                user=config.mysql_user,
                password=config.mysql_password,
                database=config.mysql_database
            )
            
            # Inicializar base de datos
            logging.info("Inicializando base de datos...")
            await init_db(app.db_pool)
            
            # Crear repositorios MySQL
            logging.info("Creando repositorios MySQL...")
            user_repository = MySQLUserRepository(app.db_pool)
            token_repository = MySQLTokenRepository(app.db_pool)
        else:
            # Crear repositorios en memoria
            logging.info("Creando repositorios en memoria...")
            user_repository = InMemoryUserRepository()
            token_repository = InMemoryTokenRepository()
        
        # Crear servicio de autenticación
        auth_service = AuthService(
            user_repository=user_repository,
            token_repository=token_repository,
            jwt_secret=config.jwt_secret,
            jwt_algorithm=config.jwt_algorithm,
            access_token_expires_in=config.access_token_expires_in,
            refresh_token_expires_in=config.refresh_token_expires_in
        )
        
        # Crear casos de uso
        register_user_use_case = RegisterUserUseCase(auth_service)
        login_use_case = LoginUseCase(auth_service)
        refresh_token_use_case = RefreshTokenUseCase(auth_service)
        logout_use_case = LogoutUseCase(auth_service)
        validate_token_use_case = ValidateTokenUseCase(auth_service)
        
        # Crear controlador
        auth_controller = AuthController(
            register_user_use_case=register_user_use_case,
            login_use_case=login_use_case,
            refresh_token_use_case=refresh_token_use_case,
            logout_use_case=logout_use_case,
            validate_token_use_case=validate_token_use_case
        )
        
        # Asignar el servicio de autenticación al controlador para el endpoint /auth/me
        auth_controller.auth_service = auth_service
        
        # Incluir router
        app.include_router(auth_controller.router)
    
    # Evento de cierre
    @app.on_event("shutdown")
    async def shutdown_db_client():
        if not config.use_in_memory_db and hasattr(app, "db_pool"):
            # Cerrar pool de conexiones
            logging.info("Cerrando pool de conexiones a MySQL...")
            app.db_pool.close()
            await app.db_pool.wait_closed()
    
    # Endpoints básicos
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