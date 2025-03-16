from src.domain.services.auth_service import AuthService


class LogoutUseCase:
    """
    Caso de uso para cerrar sesión.
    
    Este caso de uso coordina el proceso de cierre de sesión
    revocando el token de acceso.
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service
    
    async def execute(self, access_token: str) -> bool:
        """
        Ejecuta el caso de uso para cerrar sesión.
        
        Args:
            access_token: Token de acceso a revocar
            
        Returns:
            True si se revocó el token, False en caso contrario
        """
        # Validar datos de entrada
        if not access_token:
            raise ValueError("El token de acceso es obligatorio")
        
        # Cerrar sesión
        return await self.auth_service.logout(access_token) 