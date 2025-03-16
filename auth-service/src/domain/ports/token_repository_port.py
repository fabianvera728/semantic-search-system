from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.token import Token


class TokenRepositoryPort(ABC):
    """
    Puerto que define la interfaz para el repositorio de tokens.
    
    Esta interfaz debe ser implementada por todos los adaptadores
    que proporcionan acceso a la persistencia de los tokens.
    """
    
    @abstractmethod
    async def save(self, token: Token) -> Token:
        """
        Guarda un token en el repositorio.
        
        Args:
            token: El token a guardar
            
        Returns:
            El token guardado (posiblemente con ID actualizado)
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, token_id: str) -> Optional[Token]:
        """
        Busca un token por su ID.
        
        Args:
            token_id: ID del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """
        Busca un token por su token de acceso.
        
        Args:
            access_token: Token de acceso a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_by_refresh_token(self, refresh_token: str) -> Optional[Token]:
        """
        Busca un token por su token de refresco.
        
        Args:
            refresh_token: Token de refresco a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Token]:
        """
        Busca todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de tokens del usuario
        """
        pass
    
    @abstractmethod
    async def update(self, token: Token) -> Token:
        """
        Actualiza un token existente.
        
        Args:
            token: El token con los datos actualizados
            
        Returns:
            El token actualizado
            
        Raises:
            ValueError: Si el token no existe
        """
        pass
    
    @abstractmethod
    async def delete(self, token_id: str) -> None:
        """
        Elimina un token.
        
        Args:
            token_id: ID del token a eliminar
            
        Raises:
            ValueError: Si el token no existe
        """
        pass
    
    @abstractmethod
    async def delete_by_user_id(self, user_id: str) -> None:
        """
        Elimina todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        pass 