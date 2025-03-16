from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_use_case import LoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.logout_use_case import LogoutUseCase
from src.application.use_cases.validate_token_use_case import ValidateTokenUseCase
from src.domain.services.auth_service import AuthService


class RegisterRequest(BaseModel):
    """Modelo para solicitudes de registro."""
    name: str
    email: str
    password: str
    roles: Optional[List[str]] = None


class LoginRequest(BaseModel):
    """Modelo para solicitudes de inicio de sesión."""
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Modelo para solicitudes de refresco de token."""
    refresh_token: str


class AuthController:
    """
    Controlador que implementa la API REST para autenticación.
    
    Este controlador expone los endpoints para interactuar con el servicio
    de autenticación.
    """
    
    def __init__(
        self,
        register_user_use_case: RegisterUserUseCase,
        login_use_case: LoginUseCase,
        refresh_token_use_case: RefreshTokenUseCase,
        logout_use_case: LogoutUseCase,
        validate_token_use_case: ValidateTokenUseCase
    ):
        """
        Inicializa el controlador con los casos de uso necesarios.
        
        Args:
            register_user_use_case: Caso de uso para registrar usuarios
            login_use_case: Caso de uso para iniciar sesión
            refresh_token_use_case: Caso de uso para refrescar tokens
            logout_use_case: Caso de uso para cerrar sesión
            validate_token_use_case: Caso de uso para validar tokens
        """
        self.register_user_use_case = register_user_use_case
        self.login_use_case = login_use_case
        self.refresh_token_use_case = refresh_token_use_case
        self.logout_use_case = logout_use_case
        self.validate_token_use_case = validate_token_use_case
        self.auth_service = None  # Se asignará externamente
        
        # Crear router
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self._register_routes()
    
    def _register_routes(self):
        """Registra las rutas de la API."""
        
        @self.router.post("/register")
        async def register(request: RegisterRequest):
            """
            Registra un nuevo usuario.
            
            Args:
                request: Solicitud de registro
                
            Returns:
                Información del usuario registrado y token
            """
            try:
                user = await self.register_user_use_case.execute(
                    name=request.name,
                    email=request.email,
                    password=request.password,
                    roles=request.roles
                )
                
                # Autenticar al usuario después del registro
                login_result = await self.login_use_case.execute(
                    email=request.email,
                    password=request.password
                )
                
                return login_result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.router.post("/login")
        async def login(request: LoginRequest):
            """
            Inicia sesión.
            
            Args:
                request: Solicitud de inicio de sesión
                
            Returns:
                Información del usuario y token
            """
            try:
                result = await self.login_use_case.execute(
                    email=request.email,
                    password=request.password
                )
                
                return result
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.router.post("/refresh")
        async def refresh_token(request: RefreshTokenRequest):
            """
            Refresca un token.
            
            Args:
                request: Solicitud de refresco de token
                
            Returns:
                Nuevo token
            """
            try:
                result = await self.refresh_token_use_case.execute(
                    refresh_token=request.refresh_token
                )
                
                return result
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.router.post("/logout")
        async def logout(authorization: Optional[str] = Header(None)):
            """
            Cierra sesión.
            
            Args:
                authorization: Cabecera de autorización
                
            Returns:
                Mensaje de confirmación
            """
            try:
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Token no proporcionado")
                
                access_token = authorization.replace("Bearer ", "")
                
                result = await self.logout_use_case.execute(
                    access_token=access_token
                )
                
                if result:
                    return {"message": "Sesión cerrada correctamente"}
                else:
                    raise HTTPException(status_code=401, detail="Token inválido")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.router.get("/me")
        async def get_current_user(authorization: Optional[str] = Header(None)):
            """
            Obtiene el usuario actual.
            
            Args:
                authorization: Cabecera de autorización
                
            Returns:
                Información del usuario actual
            """
            try:
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Token no proporcionado")
                
                access_token = authorization.replace("Bearer ", "")
                
                # Obtener usuario actual
                user = await self.auth_service.get_current_user(access_token)
                
                if not user:
                    raise HTTPException(status_code=401, detail="Token inválido o expirado")
                
                return {
                    "id": user.user_id,
                    "name": user.name,
                    "email": user.email,
                    "roles": user.roles
                }
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
        
        @self.router.get("/validate")
        async def validate_token(authorization: Optional[str] = Header(None)):
            """
            Valida un token.
            
            Args:
                authorization: Cabecera de autorización
                
            Returns:
                Información sobre la validez del token
            """
            try:
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Token no proporcionado")
                
                access_token = authorization.replace("Bearer ", "")
                
                result = await self.validate_token_use_case.execute(
                    access_token=access_token
                )
                
                return result
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}") 