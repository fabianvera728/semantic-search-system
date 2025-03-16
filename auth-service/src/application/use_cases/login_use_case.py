from typing import Dict, Any, Tuple

from src.domain.entities.user import User
from src.domain.entities.token import Token
from src.domain.services.auth_service import AuthService


class LoginUseCase:
    """
    Caso de uso para iniciar sesión.
    
    Este caso de uso coordina el proceso de autenticación
    y generación de tokens.
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service
    
    async def execute(self, email: str, password: str) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso para iniciar sesión.
        
        Args:
            email: Correo electrónico o nombre del usuario
            password: Contraseña en texto plano
            
        Returns:
            Diccionario con información del usuario y token
            
        Raises:
            ValueError: Si las credenciales son inválidas
        """
        # Validar datos de entrada
        if not email or not password:
            raise ValueError("Todos los campos son obligatorios")
        
        # Autenticar usuario
        user, token = await self.auth_service.authenticate(email, password)
        
        # Preparar respuesta
        return {
            "user": {
                "id": user.user_id,
                "name": user.name,
                "email": user.email,
                "roles": user.roles
            },
            "token": token.access_token
        } 