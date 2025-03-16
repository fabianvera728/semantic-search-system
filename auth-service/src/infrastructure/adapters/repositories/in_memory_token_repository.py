from typing import Dict, List, Optional
import copy

from src.domain.entities.token import Token
from src.domain.ports.token_repository_port import TokenRepositoryPort


class InMemoryTokenRepository(TokenRepositoryPort):
    """
    Adaptador que implementa el repositorio de tokens en memoria.
    
    Este adaptador es útil para pruebas y desarrollo, pero no es adecuado
    para producción ya que los datos se pierden al reiniciar la aplicación.
    """
    
    def __init__(self):
        """Inicializa el repositorio con un diccionario vacío."""
        self.tokens: Dict[str, Token] = {}
        self.access_token_index: Dict[str, str] = {}  # access_token -> token_id
        self.refresh_token_index: Dict[str, str] = {}  # refresh_token -> token_id
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> [token_id]
    
    async def save(self, token: Token) -> Token:
        """
        Guarda un token en el repositorio.
        
        Args:
            token: El token a guardar
            
        Returns:
            El token guardado
        """
        # Crear una copia para evitar modificaciones externas
        token_copy = copy.deepcopy(token)
        
        # Guardar token
        self.tokens[token.token_id] = token_copy
        
        # Actualizar índices
        self.access_token_index[token.access_token] = token.token_id
        self.refresh_token_index[token.refresh_token] = token.token_id
        
        # Actualizar índice de usuario
        if token.user_id not in self.user_tokens:
            self.user_tokens[token.user_id] = []
        self.user_tokens[token.user_id].append(token.token_id)
        
        return token_copy
    
    async def find_by_id(self, token_id: str) -> Optional[Token]:
        """
        Busca un token por su ID.
        
        Args:
            token_id: ID del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        token = self.tokens.get(token_id)
        if token:
            # Retornar una copia para evitar modificaciones externas
            return copy.deepcopy(token)
        return None
    
    async def find_by_access_token(self, access_token: str) -> Optional[Token]:
        """
        Busca un token por su token de acceso.
        
        Args:
            access_token: Token de acceso a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        token_id = self.access_token_index.get(access_token)
        if token_id:
            return await self.find_by_id(token_id)
        return None
    
    async def find_by_refresh_token(self, refresh_token: str) -> Optional[Token]:
        """
        Busca un token por su token de refresco.
        
        Args:
            refresh_token: Token de refresco a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        token_id = self.refresh_token_index.get(refresh_token)
        if token_id:
            return await self.find_by_id(token_id)
        return None
    
    async def find_by_user_id(self, user_id: str) -> List[Token]:
        """
        Busca todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de tokens del usuario
        """
        token_ids = self.user_tokens.get(user_id, [])
        tokens = []
        
        for token_id in token_ids:
            token = await self.find_by_id(token_id)
            if token:
                tokens.append(token)
        
        return tokens
    
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
        if token.token_id not in self.tokens:
            raise ValueError(f"Token no encontrado: {token.token_id}")
        
        # Obtener token actual
        current_token = self.tokens[token.token_id]
        
        # Actualizar índices si es necesario
        if current_token.access_token != token.access_token:
            del self.access_token_index[current_token.access_token]
            self.access_token_index[token.access_token] = token.token_id
        
        if current_token.refresh_token != token.refresh_token:
            del self.refresh_token_index[current_token.refresh_token]
            self.refresh_token_index[token.refresh_token] = token.token_id
        
        # Crear una copia para evitar modificaciones externas
        token_copy = copy.deepcopy(token)
        
        # Guardar token actualizado
        self.tokens[token.token_id] = token_copy
        
        return token_copy
    
    async def delete(self, token_id: str) -> None:
        """
        Elimina un token.
        
        Args:
            token_id: ID del token a eliminar
            
        Raises:
            ValueError: Si el token no existe
        """
        if token_id not in self.tokens:
            raise ValueError(f"Token no encontrado: {token_id}")
        
        # Obtener token
        token = self.tokens[token_id]
        
        # Eliminar índices
        del self.access_token_index[token.access_token]
        del self.refresh_token_index[token.refresh_token]
        
        # Actualizar índice de usuario
        if token.user_id in self.user_tokens:
            self.user_tokens[token.user_id].remove(token_id)
        
        # Eliminar token
        del self.tokens[token_id]
    
    async def delete_by_user_id(self, user_id: str) -> None:
        """
        Elimina todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        token_ids = self.user_tokens.get(user_id, []).copy()
        
        for token_id in token_ids:
            try:
                await self.delete(token_id)
            except ValueError:
                # Ignorar si el token ya no existe
                pass
        
        # Limpiar índice de usuario
        self.user_tokens[user_id] = [] 