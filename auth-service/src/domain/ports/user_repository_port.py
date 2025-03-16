from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.user import User


class UserRepositoryPort(ABC):
    """
    Puerto que define la interfaz para el repositorio de usuarios.
    
    Esta interfaz debe ser implementada por todos los adaptadores
    que proporcionan acceso a la persistencia de los usuarios.
    """
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Guarda un usuario en el repositorio.
        
        Args:
            user: El usuario a guardar
            
        Returns:
            El usuario guardado (posiblemente con ID actualizado)
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Busca un usuario por su ID.
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[User]:
        """
        Busca un usuario por su nombre.
        
        Args:
            name: Nombre del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su correo electrónico.
        
        Args:
            email: Correo electrónico a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[User]:
        """
        Recupera todos los usuarios.
        
        Returns:
            Lista de todos los usuarios
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> None:
        """
        Elimina un usuario.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Raises:
            ValueError: Si el usuario no existe
        """
        pass 