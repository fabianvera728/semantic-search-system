from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from src.application.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.use_cases.login_use_case import LoginUseCase
from src.application.use_cases.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.logout_use_case import LogoutUseCase
from src.application.use_cases.validate_token_use_case import ValidateTokenUseCase
from src.domain.services.auth_service import AuthService
import logging


logger = logging.getLogger(__name__)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    roles: Optional[List[str]] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthController:
    
    def __init__(
        self,
        register_user_use_case: RegisterUserUseCase,
        login_use_case: LoginUseCase,
        refresh_token_use_case: RefreshTokenUseCase,
        logout_use_case: LogoutUseCase,
        validate_token_use_case: ValidateTokenUseCase,
        auth_service: AuthService
    ):
        self.register_user_use_case = register_user_use_case
        self.login_use_case = login_use_case
        self.refresh_token_use_case = refresh_token_use_case
        self.logout_use_case = logout_use_case
        self.validate_token_use_case = validate_token_use_case
        self.auth_service = auth_service
        
        self.router = APIRouter(prefix="", tags=["auth"])
        self._register_routes()
    
    def _register_routes(self):
        @self.router.post("/register")
        async def register(request: RegisterRequest):
            try:
                user = await self.register_user_use_case.execute(
                    name=request.name,
                    email=request.email,
                    password=request.password,
                    roles=request.roles
                )
                
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
            try:
                logger.error(f"Entro a login")

                result = await self.login_use_case.execute(
                    email=request.email,
                    password=request.password
                )

                logger.error(f"Salio de login")

                
                return result
            except ValueError as e:
                raise HTTPException(status_code=401, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
            except e:
                logger.error(f"Error al iniciar sesión: {e}")
        
        @self.router.post("/refresh")
        async def refresh_token(request: RefreshTokenRequest):
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
            try:
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Token no proporcionado")
                
                access_token = authorization.replace("Bearer ", "")
                
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
