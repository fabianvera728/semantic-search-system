from typing import List, Optional

from src.domain.entities.user import User
from src.domain.services.auth_service import AuthService


class RegisterUserUseCase:
    """
    Caso de uso para registrar un nuevo usuario.
    
    Este caso de uso coordina el registro de un nuevo usuario
    en el sistema.
    """
    
    def __init__(self, auth_service: AuthService):
        """
        Inicializa el caso de uso con los servicios necesarios.
        
        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service
    
    async def execute(
        self,
        name: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None
    ) -> User:
        """
        Ejecuta el caso de uso para registrar un usuario.
        
        Args:
            name: Nombre del usuario
            email: Correo electrónico
            password: Contraseña en texto plano
            roles: Lista de roles del usuario
            
        Returns:
            El usuario registrado
            
        Raises:
            ValueError: Si el nombre o correo ya están en uso
        """
        # Validar datos de entrada
        if not name or not email or not password:
            raise ValueError("Todos los campos son obligatorios")
        
        # Registrar usuario
        user = await self.auth_service.register_user(name, email, password, roles)
        
        return user 