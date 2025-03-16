import logging
from typing import Dict, List, Optional
from datetime import datetime
import copy

from aiomysql import Pool

from src.domain.entities.token import Token
from src.domain.ports.token_repository_port import TokenRepositoryPort


logger = logging.getLogger(__name__)


class MySQLTokenRepository(TokenRepositoryPort):
    """
    Adaptador que implementa el repositorio de tokens en MySQL.
    
    Esta implementación proporciona persistencia de tokens en una base de datos MySQL.
    """
    
    def __init__(self, pool: Pool):
        """
        Inicializa el repositorio con un pool de conexiones a MySQL.
        
        Args:
            pool: Pool de conexiones a MySQL
        """
        self.pool = pool
        logger.info("Repositorio MySQL de tokens inicializado")
    
    async def save(self, token: Token) -> Token:
        """
        Guarda un token en la base de datos.
        
        Args:
            token: El token a guardar
            
        Returns:
            El token guardado
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Insertar token
                await cursor.execute(
                    """
                    INSERT INTO tokens (
                        token_id, user_id, token_type, token_value,
                        expires_at, created_at, is_revoked
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        token.token_id, token.user_id, token.token_type, token.token_value,
                        token.expires_at.isoformat(), token.created_at.isoformat(),
                        token.is_revoked
                    )
                )
                
                await conn.commit()
                
                # Crear una copia para evitar modificaciones externas
                return copy.deepcopy(token)
    
    async def find_by_id(self, token_id: str) -> Optional[Token]:
        """
        Busca un token por su ID.
        
        Args:
            token_id: ID del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT token_id, user_id, token_type, token_value,
                           expires_at, created_at, is_revoked
                    FROM tokens
                    WHERE token_id = %s
                    """,
                    (token_id,)
                )
                
                token_row = await cursor.fetchone()
                if not token_row:
                    return None
                
                # Crear token
                return Token(
                    token_id=token_row[0],
                    user_id=token_row[1],
                    token_type=token_row[2],
                    token_value=token_row[3],
                    expires_at=datetime.fromisoformat(token_row[4]),
                    created_at=datetime.fromisoformat(token_row[5]),
                    is_revoked=bool(token_row[6])
                )
    
    async def find_by_value(self, token_value: str) -> Optional[Token]:
        """
        Busca un token por su valor.
        
        Args:
            token_value: Valor del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    SELECT token_id, user_id, token_type, token_value,
                           expires_at, created_at, is_revoked
                    FROM tokens
                    WHERE token_value = %s
                    """,
                    (token_value,)
                )
                
                token_row = await cursor.fetchone()
                if not token_row:
                    return None
                
                # Crear token
                return Token(
                    token_id=token_row[0],
                    user_id=token_row[1],
                    token_type=token_row[2],
                    token_value=token_row[3],
                    expires_at=datetime.fromisoformat(token_row[4]),
                    created_at=datetime.fromisoformat(token_row[5]),
                    is_revoked=bool(token_row[6])
                )
    
    async def find_by_user_id(self, user_id: str, token_type: Optional[str] = None) -> List[Token]:
        """
        Busca tokens por ID de usuario y opcionalmente por tipo.
        
        Args:
            user_id: ID del usuario
            token_type: Tipo de token (opcional)
            
        Returns:
            Lista de tokens encontrados
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if token_type:
                    await cursor.execute(
                        """
                        SELECT token_id, user_id, token_type, token_value,
                               expires_at, created_at, is_revoked
                        FROM tokens
                        WHERE user_id = %s AND token_type = %s
                        """,
                        (user_id, token_type)
                    )
                else:
                    await cursor.execute(
                        """
                        SELECT token_id, user_id, token_type, token_value,
                               expires_at, created_at, is_revoked
                        FROM tokens
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )
                
                tokens = []
                token_rows = await cursor.fetchall()
                
                for token_row in token_rows:
                    token = Token(
                        token_id=token_row[0],
                        user_id=token_row[1],
                        token_type=token_row[2],
                        token_value=token_row[3],
                        expires_at=datetime.fromisoformat(token_row[4]),
                        created_at=datetime.fromisoformat(token_row[5]),
                        is_revoked=bool(token_row[6])
                    )
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
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Verificar si el token existe
                await cursor.execute(
                    "SELECT COUNT(*) FROM tokens WHERE token_id = %s",
                    (token.token_id,)
                )
                
                count = await cursor.fetchone()
                if count[0] == 0:
                    raise ValueError(f"Token no encontrado: {token.token_id}")
                
                # Actualizar token
                await cursor.execute(
                    """
                    UPDATE tokens
                    SET user_id = %s, token_type = %s, token_value = %s,
                        expires_at = %s, is_revoked = %s
                    WHERE token_id = %s
                    """,
                    (
                        token.user_id, token.token_type, token.token_value,
                        token.expires_at.isoformat(), token.is_revoked,
                        token.token_id
                    )
                )
                
                await conn.commit()
                
                # Crear una copia para evitar modificaciones externas
                return copy.deepcopy(token)
    
    async def delete(self, token_id: str) -> None:
        """
        Elimina un token.
        
        Args:
            token_id: ID del token a eliminar
            
        Raises:
            ValueError: Si el token no existe
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Verificar si el token existe
                await cursor.execute(
                    "SELECT COUNT(*) FROM tokens WHERE token_id = %s",
                    (token_id,)
                )
                
                count = await cursor.fetchone()
                if count[0] == 0:
                    raise ValueError(f"Token no encontrado: {token_id}")
                
                # Eliminar token
                await cursor.execute(
                    "DELETE FROM tokens WHERE token_id = %s",
                    (token_id,)
                )
                
                await conn.commit()
    
    async def delete_expired(self) -> int:
        """
        Elimina todos los tokens expirados.
        
        Returns:
            Número de tokens eliminados
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Eliminar tokens expirados
                await cursor.execute(
                    """
                    DELETE FROM tokens
                    WHERE expires_at < %s
                    """,
                    (datetime.utcnow().isoformat(),)
                )
                
                await conn.commit()
                
                return cursor.rowcount
    
    async def revoke_all_for_user(self, user_id: str, token_type: Optional[str] = None) -> int:
        """
        Revoca todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
            token_type: Tipo de token (opcional)
            
        Returns:
            Número de tokens revocados
        """
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if token_type:
                    await cursor.execute(
                        """
                        UPDATE tokens
                        SET is_revoked = TRUE
                        WHERE user_id = %s AND token_type = %s
                        """,
                        (user_id, token_type)
                    )
                else:
                    await cursor.execute(
                        """
                        UPDATE tokens
                        SET is_revoked = TRUE
                        WHERE user_id = %s
                        """,
                        (user_id,)
                    )
                
                await conn.commit()
                
                return cursor.rowcount 