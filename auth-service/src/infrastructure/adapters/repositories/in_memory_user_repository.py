from typing import Dict, List, Optional
import copy

from src.domain.entities.user import User
from src.domain.ports.user_repository_port import UserRepositoryPort


class InMemoryUserRepository(UserRepositoryPort):
    """
    Adaptador que implementa el repositorio de usuarios en memoria.
    
    Este adaptador es útil para pruebas y desarrollo, pero no es adecuado
    para producción ya que los datos se pierden al reiniciar la aplicación.
    """
    
    def __init__(self):
        """Inicializa el repositorio con un diccionario vacío."""
        self.users: Dict[str, User] = {}
        self.name_index: Dict[str, str] = {}  # name -> user_id
        self.email_index: Dict[str, str] = {}  # email -> user_id
    
    async def save(self, user: User) -> User:
        """
        Guarda un usuario en el repositorio.
        
        Args:
            user: El usuario a guardar
            
        Returns:
            El usuario guardado
        """
        # Crear una copia para evitar modificaciones externas
        user_copy = copy.deepcopy(user)
        
        # Guardar usuario
        self.users[user.user_id] = user_copy
        
        # Actualizar índices
        self.name_index[user.name] = user.user_id
        self.email_index[user.email] = user.user_id
        
        return user_copy
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Busca un usuario por su ID.
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        user = self.users.get(user_id)
        if user:
            # Retornar una copia para evitar modificaciones externas
            return copy.deepcopy(user)
        return None
    
    async def find_by_name(self, name: str) -> Optional[User]:
        """
        Busca un usuario por su nombre.
        
        Args:
            name: Nombre del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        user_id = self.name_index.get(name)
        if user_id:
            return await self.find_by_id(user_id)
        return None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su correo electrónico.
        
        Args:
            email: Correo electrónico a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        user_id = self.email_index.get(email)
        if user_id:
            return await self.find_by_id(user_id)
        return None
    
    async def find_all(self) -> List[User]:
        """
        Recupera todos los usuarios.
        
        Returns:
            Lista de todos los usuarios
        """
        # Retornar copias para evitar modificaciones externas
        return [copy.deepcopy(user) for user in self.users.values()]
    
    async def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.
        
        Args:
            user: El usuario con los datos actualizados
            
        Returns:
            El usuario actualizado
            
        Raises:
            ValueError: Si el usuario no existe
        """
        if user.user_id not in self.users:
            raise ValueError(f"Usuario no encontrado: {user.user_id}")
        
        # Obtener usuario actual
        current_user = self.users[user.user_id]
        
        # Actualizar índices si es necesario
        if current_user.name != user.name:
            del self.name_index[current_user.name]
            self.name_index[user.name] = user.user_id
        
        if current_user.email != user.email:
            del self.email_index[current_user.email]
            self.email_index[user.email] = user.user_id
        
        # Crear una copia para evitar modificaciones externas
        user_copy = copy.deepcopy(user)
        
        # Guardar usuario actualizado
        self.users[user.user_id] = user_copy
        
        return user_copy
    
    async def delete(self, user_id: str) -> None:
        """
        Elimina un usuario.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Raises:
            ValueError: Si el usuario no existe
        """
        if user_id not in self.users:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        # Obtener usuario
        user = self.users[user_id]
        
        # Eliminar índices
        del self.name_index[user.name]
        del self.email_index[user.email]
        
        # Eliminar usuario
        del self.users[user_id] 