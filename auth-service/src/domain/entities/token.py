from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid


@dataclass
class Token:
    """
    Entidad que representa un token de autenticación.
    
    Esta entidad contiene la información de un token de acceso
    y un token de refresco para la autenticación de usuarios.
    """
    token_id: str
    user_id: str
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_revoked: bool = False
    
    @staticmethod
    def create(
        user_id: str,
        access_token: str,
        refresh_token: str,
        access_token_expires_in: int = 3600,  # 1 hora
        refresh_token_expires_in: int = 2592000  # 30 días
    ) -> 'Token':
        """
        Crea una nueva instancia de Token.
        
        Args:
            user_id: ID del usuario
            access_token: Token de acceso
            refresh_token: Token de refresco
            access_token_expires_in: Tiempo de expiración del token de acceso en segundos
            refresh_token_expires_in: Tiempo de expiración del token de refresco en segundos
            
        Returns:
            Una nueva instancia de Token
        """
        now = datetime.utcnow()
        
        return Token(
            token_id=str(uuid.uuid4()),
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=now + timedelta(seconds=access_token_expires_in),
            refresh_token_expires_at=now + timedelta(seconds=refresh_token_expires_in)
        )
    
    def is_access_token_expired(self) -> bool:
        """
        Verifica si el token de acceso ha expirado.
        
        Returns:
            True si el token ha expirado, False en caso contrario
        """
        return datetime.utcnow() > self.access_token_expires_at
    
    def is_refresh_token_expired(self) -> bool:
        """
        Verifica si el token de refresco ha expirado.
        
        Returns:
            True si el token ha expirado, False en caso contrario
        """
        return datetime.utcnow() > self.refresh_token_expires_at
    
    def revoke(self) -> None:
        """Revoca el token."""
        self.is_revoked = True 