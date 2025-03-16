from typing import Dict, Any

from src.domain.services.auth_service import AuthService


class RefreshTokenUseCase:
    """
    Caso de uso para refrescar un token.
    
    Este caso de uso coordina el proceso de refresco de tokens
    utilizando un token de refresco.
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service
    
    async def execute(self, refresh_token: str) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso para refrescar un token.
        
        Args:
            refresh_token: Token de refresco
            
        Returns:
            Diccionario con el nuevo token
            
        Raises:
            ValueError: Si el token de refresco es inválido o ha expirado
        """
        # Validar datos de entrada
        if not refresh_token:
            raise ValueError("El token de refresco es obligatorio")
        
        # Refrescar token
        token = await self.auth_service.refresh_token(refresh_token)
        
        # Preparar respuesta
        return {
            "token": token.access_token
        } 