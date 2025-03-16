from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import uuid


@dataclass
class Token:
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
        return datetime.utcnow() > self.access_token_expires_at
    
    def is_refresh_token_expired(self) -> bool:
        return datetime.utcnow() > self.refresh_token_expires_at
    
    def revoke(self) -> None:
        self.is_revoked = True 