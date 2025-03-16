import uvicorn
import logging
from fastapi import FastAPI

from src.domain.services.auth_service import AuthService
from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_use_case import LoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.logout_use_case import LogoutUseCase
from src.application.use_cases.validate_token_use_case import ValidateTokenUseCase
from src.infrastructure.adapters.repositories.in_memory_user_repository import InMemoryUserRepository
from src.infrastructure.adapters.repositories.in_memory_token_repository import InMemoryTokenRepository
from src.infrastructure.adapters.controllers.fastapi_controller import FastAPIController
from src.infrastructure.config.app_config import get_app_config


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


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    # Cargar configuración
    config = get_app_config()
    
    # Configurar logging
    setup_logging(config)
    
    # Crear repositorios
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
    controller = FastAPIController(
        register_user_use_case=register_user_use_case,
        login_use_case=login_use_case,
        refresh_token_use_case=refresh_token_use_case,
        logout_use_case=logout_use_case,
        validate_token_use_case=validate_token_use_case
    )
    
    # Asignar el servicio de autenticación al controlador para el endpoint /auth/me
    controller.auth_service = auth_service
    
    return controller.get_app()


app = create_app()

if __name__ == "__main__":
    # Cargar configuración
    config = get_app_config()
    
    # Iniciar servidor
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=False
    ) 