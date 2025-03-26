import logging
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import get_app_config

config = get_app_config()

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm]
        )
        
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta el ID de usuario"
            )
        
        user_data = {
            "user_id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "roles": payload.get("roles", [])
        }
        
        return user_data
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    user_data = await get_current_user(credentials)
    return user_data["user_id"]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    
    async def dispatch(self, request: Request, call_next: Callable):
        PUBLIC_PATHS = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/health"
        ]
        
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)
        
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "No se proporcionó el token de autenticación"}
            )
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token de autenticación inválido"}
                )
            
            payload = jwt.decode(
                token,
                config.jwt_secret,
                algorithms=[config.jwt_algorithm]
            )
            
            user_data = {
                "user_id": payload.get("sub"),
                "name": payload.get("name"),
                "email": payload.get("email"),
                "roles": payload.get("roles", [])
            }
            
            request.state.user = user_data
            
            return await call_next(request)
        except (jwt.PyJWTError, ValueError) as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token inválido o expirado"}
            ) 