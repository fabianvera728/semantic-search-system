import logging
import copy
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.token import Token as TokenEntity
from src.domain.ports.token_repository_port import TokenRepositoryPort
from src.infrastructure.db.models import Token as TokenModel
from src.infrastructure.db.database import db


logger = logging.getLogger(__name__)


class SQLAlchemyTokenRepository(TokenRepositoryPort):
    """
    Adaptador que implementa el repositorio de tokens con SQLAlchemy.
    
    Esta implementación proporciona persistencia de tokens en una base de datos MySQL
    utilizando SQLAlchemy como ORM.
    """
    
    def __init__(self):
        """Inicializa el repositorio."""
        logger.info("Repositorio SQLAlchemy de tokens inicializado")
    
    async def _get_session(self) -> AsyncSession:
        """
        Obtiene una sesión de la base de datos.
        
        Returns:
            AsyncSession: Sesión de la base de datos
        """
        return await db.get_session()
    
    def _entity_to_model(self, token: TokenEntity) -> TokenModel:
        return TokenModel(
            token_id=token.token_id,
            user_id=token.user_id,
            token_type='access',
            token_value=token.access_token,
            expires_at=token.access_token_expires_at,
            created_at=token.created_at,
            is_revoked=token.is_revoked
        )
    
    def _model_to_entity(self, model: TokenModel) -> TokenEntity:
        return TokenEntity(
            token_id=model.token_id,
            user_id=model.user_id,
            access_token=model.token_value,
            access_token_expires_at=model.expires_at,
            refresh_token=model.token_value,
            refresh_token_expires_at=model.expires_at,
            created_at=model.created_at,
            is_revoked=model.is_revoked
        )
    
    async def save(self, token: TokenEntity) -> TokenEntity:
        async with await self._get_session() as session:
            try:
                token_model = self._entity_to_model(token)
                
                # Guardar en la base de datos
                session.add(token_model)
                await session.commit()
                await session.refresh(token_model)
                
                # Convertir modelo a entidad
                saved_token = self._model_to_entity(token_model)
                
                # Crear una copia para evitar modificaciones externas
                return copy.deepcopy(saved_token)
            except Exception as e:
                logger.error(f"Error al guardar el token: {e}")
                raise e
    
    async def find_by_id(self, token_id: str) -> Optional[TokenEntity]:
        """
        Busca un token por su ID.
        
        Args:
            token_id: ID del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(TokenModel.token_id == token_id)
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(token_model)
    
    async def find_by_value(self, token_value: str) -> Optional[TokenEntity]:
        """
        Busca un token por su valor.
        
        Args:
            token_value: Valor del token a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(TokenModel.token_value == token_value)
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(token_model)
    
    async def find_by_access_token(self, access_token: str) -> Optional[TokenEntity]:
        """
        Busca un token por su token de acceso.
        
        Args:
            access_token: Token de acceso a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(
                TokenModel.token_value == access_token,
                TokenModel.token_type == "access"
            )
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(token_model)
    
    async def find_by_refresh_token(self, refresh_token: str) -> Optional[TokenEntity]:
        """
        Busca un token por su token de refresco.
        
        Args:
            refresh_token: Token de refresco a buscar
            
        Returns:
            El token encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(
                TokenModel.token_value == refresh_token,
                TokenModel.token_type == "refresh"
            )
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(token_model)
    
    async def find_by_user_id(self, user_id: str, token_type: Optional[str] = None) -> List[TokenEntity]:
        """
        Busca tokens por ID de usuario y opcionalmente por tipo.
        
        Args:
            user_id: ID del usuario
            token_type: Tipo de token (opcional)
            
        Returns:
            Lista de tokens encontrados
        """
        async with await self._get_session() as session:
            # Construir consulta
            if token_type:
                stmt = select(TokenModel).where(
                    TokenModel.user_id == user_id,
                    TokenModel.token_type == token_type
                )
            else:
                stmt = select(TokenModel).where(TokenModel.user_id == user_id)
            
            # Ejecutar consulta
            result = await session.execute(stmt)
            token_models = result.scalars().all()
            
            # Convertir modelos a entidades
            return [self._model_to_entity(token_model) for token_model in token_models]
    
    async def update(self, token: TokenEntity) -> TokenEntity:
        """
        Actualiza un token existente.
        
        Args:
            token: El token con los datos actualizados
            
        Returns:
            El token actualizado
            
        Raises:
            ValueError: Si el token no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(TokenModel.token_id == token.token_id)
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                raise ValueError(f"Token no encontrado: {token.token_id}")
            
            # Actualizar campos
            token_model.user_id = token.user_id
            token_model.token_type = token.token_type
            token_model.token_value = token.token_value
            token_model.expires_at = token.expires_at
            token_model.is_revoked = token.is_revoked
            
            # Guardar cambios
            await session.commit()
            await session.refresh(token_model)
            
            # Convertir modelo a entidad
            updated_token = self._model_to_entity(token_model)
            
            # Crear una copia para evitar modificaciones externas
            return copy.deepcopy(updated_token)
    
    async def delete(self, token_id: str) -> None:
        """
        Elimina un token.
        
        Args:
            token_id: ID del token a eliminar
            
        Raises:
            ValueError: Si el token no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(TokenModel).where(TokenModel.token_id == token_id)
            result = await session.execute(stmt)
            token_model = result.scalar_one_or_none()
            
            if not token_model:
                raise ValueError(f"Token no encontrado: {token_id}")
            
            # Eliminar token
            await session.delete(token_model)
            await session.commit()
    
    async def delete_by_user_id(self, user_id: str) -> None:
        """
        Elimina todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
        """
        async with await self._get_session() as session:
            # Eliminar tokens del usuario
            stmt = delete(TokenModel).where(TokenModel.user_id == user_id)
            await session.execute(stmt)
            await session.commit()
    
    async def delete_expired(self) -> int:
        """
        Elimina todos los tokens expirados.
        
        Returns:
            Número de tokens eliminados
        """
        async with await self._get_session() as session:
            # Eliminar tokens expirados
            stmt = delete(TokenModel).where(TokenModel.expires_at < datetime.utcnow())
            result = await session.execute(stmt)
            await session.commit()
            
            # Devolver número de filas afectadas
            return result.rowcount
    
    async def revoke_all_for_user(self, user_id: str, token_type: Optional[str] = None) -> int:
        """
        Revoca todos los tokens de un usuario.
        
        Args:
            user_id: ID del usuario
            token_type: Tipo de token (opcional)
            
        Returns:
            Número de tokens revocados
        """
        async with await self._get_session() as session:
            # Construir consulta
            if token_type:
                stmt = update(TokenModel).where(
                    TokenModel.user_id == user_id,
                    TokenModel.token_type == token_type
                ).values(is_revoked=True)
            else:
                stmt = update(TokenModel).where(
                    TokenModel.user_id == user_id
                ).values(is_revoked=True)
            
            # Ejecutar consulta
            result = await session.execute(stmt)
            await session.commit()
            
            # Devolver número de filas afectadas
            return result.rowcount 