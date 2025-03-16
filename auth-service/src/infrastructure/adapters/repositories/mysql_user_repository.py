import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import copy

from aiomysql import Pool

from src.domain.entities.user import User
from src.domain.ports.user_repository_port import UserRepositoryPort


logger = logging.getLogger(__name__)


class MySQLUserRepository(UserRepositoryPort):
    """
    Adaptador que implementa el repositorio de usuarios en MySQL.
    
    Esta implementación proporciona persistencia de usuarios en una base de datos MySQL.
    """
    
    def __init__(self, pool: Pool):
        """
        Inicializa el repositorio con un pool de conexiones a MySQL.
        
        Args:
            pool: Pool de conexiones a MySQL
        """
        self.pool = pool
        logger.info("Repositorio MySQL de usuarios inicializado")
    
    async def save(self, user: User) -> User:
        """
        Guarda un usuario en la base de datos.
        
        Args:
            user: El usuario a guardar
            
        Returns:
            El usuario guardado
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Insertar usuario
                await cursor.execute(
                    """
                    INSERT INTO users (
                        user_id, name, email, password_hash, roles,
                        is_active, created_at, last_login
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user.user_id, user.name, user.email, user.password_hash,
                        json.dumps(user.roles), user.is_active,
                        user.created_at.isoformat(),
                        user.last_login.isoformat() if user.last_login else None
                    )
                )
                
                await conn.commit()
                
                # Crear una copia para evitar modificaciones externas
                return copy.deepcopy(user)
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Busca un usuario por su ID.
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT user_id, name, email, password_hash, roles,
                           is_active, created_at, last_login
                    FROM users
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                
                user_row = await cursor.fetchone()
                if not user_row:
                    return None
                
                # Crear usuario
                return User(
                    user_id=user_row[0],
                    name=user_row[1],
                    email=user_row[2],
                    password_hash=user_row[3],
                    roles=json.loads(user_row[4]),
                    is_active=bool(user_row[5]),
                    created_at=datetime.fromisoformat(user_row[6]),
                    last_login=datetime.fromisoformat(user_row[7]) if user_row[7] else None
                )
    
    async def find_by_name(self, name: str) -> Optional[User]:
        """
        Busca un usuario por su nombre.
        
        Args:
            name: Nombre del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT user_id, name, email, password_hash, roles,
                           is_active, created_at, last_login
                    FROM users
                    WHERE name = %s
                    """,
                    (name,)
                )
                
                user_row = await cursor.fetchone()
                if not user_row:
                    return None
                
                # Crear usuario
                return User(
                    user_id=user_row[0],
                    name=user_row[1],
                    email=user_row[2],
                    password_hash=user_row[3],
                    roles=json.loads(user_row[4]),
                    is_active=bool(user_row[5]),
                    created_at=datetime.fromisoformat(user_row[6]),
                    last_login=datetime.fromisoformat(user_row[7]) if user_row[7] else None
                )
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su correo electrónico.
        
        Args:
            email: Correo electrónico a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT user_id, name, email, password_hash, roles,
                           is_active, created_at, last_login
                    FROM users
                    WHERE email = %s
                    """,
                    (email,)
                )
                
                user_row = await cursor.fetchone()
                if not user_row:
                    return None
                
                # Crear usuario
                return User(
                    user_id=user_row[0],
                    name=user_row[1],
                    email=user_row[2],
                    password_hash=user_row[3],
                    roles=json.loads(user_row[4]),
                    is_active=bool(user_row[5]),
                    created_at=datetime.fromisoformat(user_row[6]),
                    last_login=datetime.fromisoformat(user_row[7]) if user_row[7] else None
                )
    
    async def find_all(self) -> List[User]:
        """
        Recupera todos los usuarios.
        
        Returns:
            Lista de todos los usuarios
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT user_id, name, email, password_hash, roles,
                           is_active, created_at, last_login
                    FROM users
                    """
                )
                
                users = []
                user_rows = await cursor.fetchall()
                
                for user_row in user_rows:
                    user = User(
                        user_id=user_row[0],
                        name=user_row[1],
                        email=user_row[2],
                        password_hash=user_row[3],
                        roles=json.loads(user_row[4]),
                        is_active=bool(user_row[5]),
                        created_at=datetime.fromisoformat(user_row[6]),
                        last_login=datetime.fromisoformat(user_row[7]) if user_row[7] else None
                    )
                    users.append(user)
                
                return users
    
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
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Verificar si el usuario existe
                await cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE user_id = %s",
                    (user.user_id,)
                )
                
                count = await cursor.fetchone()
                if count[0] == 0:
                    raise ValueError(f"Usuario no encontrado: {user.user_id}")
                
                # Actualizar usuario
                await cursor.execute(
                    """
                    UPDATE users
                    SET name = %s, email = %s, password_hash = %s, roles = %s,
                        is_active = %s, last_login = %s
                    WHERE user_id = %s
                    """,
                    (
                        user.name, user.email, user.password_hash, json.dumps(user.roles),
                        user.is_active,
                        user.last_login.isoformat() if user.last_login else None,
                        user.user_id
                    )
                )
                
                await conn.commit()
                
                # Crear una copia para evitar modificaciones externas
                return copy.deepcopy(user)
    
    async def delete(self, user_id: str) -> None:
        """
        Elimina un usuario.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Raises:
            ValueError: Si el usuario no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Verificar si el usuario existe
                await cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE user_id = %s",
                    (user_id,)
                )
                
                count = await cursor.fetchone()
                if count[0] == 0:
                    raise ValueError(f"Usuario no encontrado: {user_id}")
                
                # Eliminar usuario
                await cursor.execute(
                    "DELETE FROM users WHERE user_id = %s",
                    (user_id,)
                )
                
                await conn.commit() 