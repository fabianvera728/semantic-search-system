import json
import logging
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config import get_app_config

logger = logging.getLogger(__name__)
config = get_app_config()

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependencia para obtener el usuario actual a partir del token JWT.
    
    Args:
        credentials: Credenciales de autorización (Bearer token)
        
    Returns:
        Dict[str, Any]: Datos del usuario
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    token = credentials.credentials
    
    try:
        # Decodificar token
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm]
        )
        
        # Verificar que el payload tenga los campos necesarios
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: falta el ID de usuario"
            )
        
        # Extraer datos del usuario
        user_data = {
            "user_id": payload.get("sub"),
            "name": payload.get("name"),
            "email": payload.get("email"),
            "roles": payload.get("roles", [])
        }
        
        return user_data
    except jwt.PyJWTError as e:
        logger.error(f"Error al decodificar token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependencia para obtener únicamente el ID del usuario actual.
    
    Args:
        credentials: Credenciales de autorización (Bearer token)
        
    Returns:
        str: ID del usuario
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    user_data = await get_current_user(credentials)
    return user_data["user_id"]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware para autenticar solicitudes mediante JWT y establecer
    información del usuario en la solicitud.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Rutas públicas que no requieren autenticación
        PUBLIC_PATHS = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/",
            "/health"
        ]
        
        # Verificar si la ruta es pública
        if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
            return await call_next(request)
        
        # Obtener token de autorización
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "No se proporcionó el token de autenticación"}
            )
        
        try:
            # Extraer token
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token de autenticación inválido"}
                )
            
            # Decodificar token
            payload = jwt.decode(
                token,
                config.jwt_secret,
                algorithms=[config.jwt_algorithm]
            )
            
            # Extraer datos del usuario
            user_data = {
                "user_id": payload.get("sub"),
                "name": payload.get("name"),
                "email": payload.get("email"),
                "roles": payload.get("roles", [])
            }
            
            # Establecer información del usuario en la solicitud
            request.state.user = user_data
            
            # Continuar con la solicitud
            return await call_next(request)
        except (jwt.PyJWTError, ValueError) as e:
            logger.error(f"Error al procesar token: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token inválido o expirado"}
            ) 