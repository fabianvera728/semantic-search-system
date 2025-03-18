from typing import Dict, Any, Tuple

from src.domain.entities.user import User
from src.domain.entities.token import Token
from src.domain.services.auth_service import AuthService


class LoginUseCase:
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def execute(self, email: str, password: str) -> Dict[str, Any]:
        if not email or not password:
            raise ValueError("Todos los campos son obligatorios")
        
        user, token = await self.auth_service.authenticate(email, password)
        
        return {
            "user": {
                "id": user.user_id,
                "name": user.name,
                "email": user.email,
                "roles": user.roles
            },
            "token": token.access_token
        } 