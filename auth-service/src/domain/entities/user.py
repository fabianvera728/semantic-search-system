from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import bcrypt


@dataclass
class User:
    """
    Entidad que representa un usuario del sistema.
    
    Esta entidad contiene la información básica de un usuario
    y métodos para gestionar su autenticación.
    """
    user_id: str
    name: str
    email: str
    password_hash: str
    roles: List[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    @staticmethod
    def create(name: str, email: str, password: str, roles: List[str] = None) -> 'User':
        """
        Crea una nueva instancia de User con un ID generado y contraseña hasheada.
        
        Args:
            name: Nombre del usuario
            email: Correo electrónico
            password: Contraseña en texto plano
            roles: Lista de roles del usuario
            
        Returns:
            Una nueva instancia de User
        """
        # Generar hash de la contraseña
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        return User(
            user_id=str(uuid.uuid4()),
            name=name,
            email=email,
            password_hash=password_hash,
            roles=roles or ["user"]
        )
    
    def verify_password(self, password: str) -> bool:
        """
        Verifica si la contraseña proporcionada coincide con el hash almacenado.
        
        Args:
            password: Contraseña en texto plano a verificar
            
        Returns:
            True si la contraseña es correcta, False en caso contrario
        """
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    def update_password(self, new_password: str) -> None:
        """
        Actualiza la contraseña del usuario.
        
        Args:
            new_password: Nueva contraseña en texto plano
        """
        password_bytes = new_password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def has_role(self, role: str) -> bool:
        """
        Verifica si el usuario tiene un rol específico.
        
        Args:
            role: Rol a verificar
            
        Returns:
            True si el usuario tiene el rol, False en caso contrario
        """
        return role in self.roles
    
    def record_login(self) -> None:
        """Registra el momento del último inicio de sesión."""
        self.last_login = datetime.utcnow() 