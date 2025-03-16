from typing import Dict, Any, Optional, Tuple

from src.domain.services.auth_service import AuthService


class ValidateTokenUseCase:
    """
    Caso de uso para validar un token.
    
    Este caso de uso coordina el proceso de validación de tokens
    de acceso.
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service
    
    async def execute(self, access_token: str) -> Dict[str, Any]:
        """
        Ejecuta el caso de uso para validar un token.
        
        Args:
            access_token: Token de acceso a validar
            
        Returns:
            Diccionario con información sobre la validez del token
            
        Raises:
            ValueError: Si el token de acceso es obligatorio
        """
        # Validar datos de entrada
        if not access_token:
            raise ValueError("El token de acceso es obligatorio")
        
        # Validar token
        is_valid, payload = await self.auth_service.validate_token(access_token)
        
        # Preparar respuesta
        response = {
            "valid": is_valid
        }
        
        if is_valid and payload:
            response["user_id"] = payload.get("sub")
            response["name"] = payload.get("name")
            response["email"] = payload.get("email")
            response["roles"] = payload.get("roles", [])
        
        return response 