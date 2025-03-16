from typing import List, Optional

from src.domain.entities.user import User
from src.domain.services.auth_service import AuthService


class RegisterUserUseCase:

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def execute(
        self,
        name: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None
    ) -> User:
        if not name or not email or not password:
            raise ValueError("Todos los campos son obligatorios")

        user = await self.auth_service.register_user(name, email, password, roles)
        return user
