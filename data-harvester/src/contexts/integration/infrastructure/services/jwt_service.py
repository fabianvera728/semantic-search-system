import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

from src.config import get_app_config


class JWTService:
    """Servicio para generar tokens JWT para comunicación entre servicios."""
    
    def __init__(self):
        self.config = get_app_config()
    
    def generate_service_token(self, service_name: str = "data-harvester", expires_in_minutes: int = 60) -> str:
        """
        Genera un token JWT para comunicación entre servicios.
        
        Args:
            service_name: Nombre del servicio que genera el token
            expires_in_minutes: Tiempo de expiración en minutos
            
        Returns:
            Token JWT como string
        """
        payload = {
            "sub": "system",  # Usuario del sistema
            "name": f"Service {service_name}",
            "email": f"{service_name}@system.local",
            "roles": ["service", "system"],
            "service": service_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )
        
        return token
    
    def get_auth_headers(self, service_name: str = "data-harvester") -> Dict[str, str]:
        """
        Genera headers de autorización para peticiones HTTP.
        
        Args:
            service_name: Nombre del servicio
            
        Returns:
            Diccionario con headers de autorización
        """
        token = self.generate_service_token(service_name)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        } 