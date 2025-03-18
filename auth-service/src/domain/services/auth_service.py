import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from src.domain.entities.user import User
from src.domain.entities.token import Token
from src.domain.ports.user_repository_port import UserRepositoryPort
from src.domain.ports.token_repository_port import TokenRepositoryPort


class AuthService:
    
    def __init__(
        self,
        user_repository: UserRepositoryPort,
        token_repository: TokenRepositoryPort,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        access_token_expires_in: int = 3600,  # 1 hora
        refresh_token_expires_in: int = 2592000  # 30 días
    ):
        self.user_repository = user_repository
        self.token_repository = token_repository
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expires_in = access_token_expires_in
        self.refresh_token_expires_in = refresh_token_expires_in
    
    async def register_user(self, name: str, email: str, password: str, roles: list[str] = None) -> User:
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise ValueError(f"El correo '{email}' ya está en uso")
        
        user = User.create(name, email, password, roles)
        saved_user = await self.user_repository.save(user)
        
        return saved_user
    
    async def authenticate(self, email_or_name: str, password: str) -> Tuple[User, Token]:
        user = await self.user_repository.find_by_name(email_or_name)
        import logging

        logger = logging.getLogger(__name__)


        if not user:
            user = await self.user_repository.find_by_email(email_or_name)

        logger.error(f"User: {user}")
        
        if not user or not user.verify_password(password):
            raise ValueError("Credenciales inválidas")
        
        if not user.is_active:
            raise ValueError("Usuario inactivo")
        
        access_token, refresh_token = self._generate_tokens(user)
        logger.error(f"Access token: {access_token}")
        logger.error(f"Refresh token: {refresh_token}")

        token = Token.create(
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in=self.access_token_expires_in,
            refresh_token_expires_in=self.refresh_token_expires_in
        )

        saved_token = await self.token_repository.save(token)

        logger.error(f"Saved token: {saved_token} emoji 🔑")
        
        user.record_login()
        await self.user_repository.update(user)
        
        return user, saved_token
    
    async def refresh_token(self, refresh_token: str) -> Token:
        token = await self.token_repository.find_by_refresh_token(refresh_token)
        if not token:
            raise ValueError("Token de refresco inválido")
        
        if token.is_revoked:
            raise ValueError("Token revocado")
        
        if token.is_refresh_token_expired():
            raise ValueError("Token de refresco expirado")
        
        user = await self.user_repository.find_by_id(token.user_id)
        if not user:
            raise ValueError("Usuario no encontrado")
        
        if not user.is_active:
            raise ValueError("Usuario inactivo")
        
        token.revoke()
        await self.token_repository.update(token)
        
        access_token, refresh_token = self._generate_tokens(user)
        
        # Crear y guardar el nuevo token
        new_token = Token.create(
            user_id=user.user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_in=self.access_token_expires_in,
            refresh_token_expires_in=self.refresh_token_expires_in
        )
        saved_token = await self.token_repository.save(new_token)
        
        return saved_token
    
    async def validate_token(self, access_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        token = await self.token_repository.find_by_access_token(access_token)
        if not token:
            return False, None
        
        # Verificar si el token está revocado
        if token.is_revoked:
            return False, None
        
        # Verificar si el token ha expirado
        if token.is_access_token_expired():
            return False, None
        
        try:
            # Decodificar token
            payload = jwt.decode(
                access_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            return True, payload
        except jwt.PyJWTError:
            return False, None
    
    async def logout(self, access_token: str) -> bool:
        token = await self.token_repository.find_by_access_token(access_token)
        if not token:
            return False
        
        token.revoke()
        await self.token_repository.update(token)
        
        return True
    
    async def logout_all(self, user_id: str) -> None:
        await self.token_repository.delete_by_user_id(user_id)
    
    async def get_current_user(self, access_token: str) -> Optional[User]:
        is_valid, payload = await self.validate_token(access_token)
        
        if not is_valid or not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await self.user_repository.find_by_id(user_id)
    
    def _generate_tokens(self, user: User) -> Tuple[str, str]:
        access_payload = {
            "sub": user.user_id,
            "name": user.name,
            "email": user.email,
            "roles": user.roles,
            "exp": datetime.utcnow() + timedelta(seconds=self.access_token_expires_in)
        }
        
        access_token = jwt.encode(
            access_payload,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        refresh_token = secrets.token_urlsafe(64)
        
        return access_token, refresh_token 