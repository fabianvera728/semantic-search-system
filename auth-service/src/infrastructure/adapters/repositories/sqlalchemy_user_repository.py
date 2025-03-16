import json
import logging
import copy
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User as UserEntity
from src.domain.ports.user_repository_port import UserRepositoryPort
from src.infrastructure.db.models import User as UserModel
from src.infrastructure.db.database import db


logger = logging.getLogger(__name__)


class SQLAlchemyUserRepository(UserRepositoryPort):
    """
    Adaptador que implementa el repositorio de usuarios con SQLAlchemy.
    
    Esta implementación proporciona persistencia de usuarios en una base de datos MySQL
    utilizando SQLAlchemy como ORM.
    """
    
    def __init__(self):
        """Inicializa el repositorio."""
        logger.info("Repositorio SQLAlchemy de usuarios inicializado")
    
    async def _get_session(self) -> AsyncSession:
        """
        Obtiene una sesión de la base de datos.
        
        Returns:
            AsyncSession: Sesión de la base de datos
        """
        return await db.get_session()
    
    def _entity_to_model(self, user: UserEntity) -> UserModel:
        """
        Convierte una entidad de usuario a un modelo de SQLAlchemy.
        
        Args:
            user: Entidad de usuario
            
        Returns:
            Modelo de usuario de SQLAlchemy
        """
        return UserModel(
            user_id=user.user_id,
            name=user.name,
            email=user.email,
            password_hash=user.password_hash,
            roles=json.dumps(user.roles),
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    def _model_to_entity(self, model: UserModel) -> UserEntity:
        """
        Convierte un modelo de SQLAlchemy a una entidad de usuario.
        
        Args:
            model: Modelo de usuario de SQLAlchemy
            
        Returns:
            Entidad de usuario
        """
        return UserEntity(
            user_id=model.user_id,
            name=model.name,
            email=model.email,
            password_hash=model.password_hash,
            roles=json.loads(model.roles),
            is_active=model.is_active,
            created_at=model.created_at,
            last_login=model.last_login
        )
    
    async def save(self, user: UserEntity) -> UserEntity:
        """
        Guarda un usuario en la base de datos.
        
        Args:
            user: El usuario a guardar
            
        Returns:
            El usuario guardado
        """
        async with await self._get_session() as session:
            # Convertir entidad a modelo
            user_model = self._entity_to_model(user)
            
            # Guardar en la base de datos
            session.add(user_model)
            await session.commit()
            await session.refresh(user_model)
            
            # Convertir modelo a entidad
            saved_user = self._model_to_entity(user_model)
            
            # Crear una copia para evitar modificaciones externas
            return copy.deepcopy(saved_user)
    
    async def find_by_id(self, user_id: str) -> Optional[UserEntity]:
        """
        Busca un usuario por su ID.
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(user_model)
    
    async def find_by_name(self, name: str) -> Optional[UserEntity]:
        """
        Busca un usuario por su nombre.
        
        Args:
            name: Nombre del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel).where(UserModel.name == name)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(user_model)
    
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        """
        Busca un usuario por su email.
        
        Args:
            email: Email del usuario a buscar
            
        Returns:
            El usuario encontrado o None si no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            # Convertir modelo a entidad
            return self._model_to_entity(user_model)
    
    async def find_all(self) -> List[UserEntity]:
        """
        Busca todos los usuarios.
        
        Returns:
            Lista de usuarios
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel)
            result = await session.execute(stmt)
            user_models = result.scalars().all()
            
            # Convertir modelos a entidades
            return [self._model_to_entity(user_model) for user_model in user_models]
    
    async def update(self, user: UserEntity) -> UserEntity:
        """
        Actualiza un usuario existente.
        
        Args:
            user: El usuario con los datos actualizados
            
        Returns:
            El usuario actualizado
            
        Raises:
            ValueError: Si el usuario no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel).where(UserModel.user_id == user.user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise ValueError(f"Usuario no encontrado: {user.user_id}")
            
            # Actualizar campos
            user_model.name = user.name
            user_model.email = user.email
            user_model.password_hash = user.password_hash
            user_model.roles = json.dumps(user.roles)
            user_model.is_active = user.is_active
            user_model.last_login = user.last_login
            
            # Guardar cambios
            await session.commit()
            await session.refresh(user_model)
            
            # Convertir modelo a entidad
            updated_user = self._model_to_entity(user_model)
            
            # Crear una copia para evitar modificaciones externas
            return copy.deepcopy(updated_user)
    
    async def delete(self, user_id: str) -> None:
        """
        Elimina un usuario.
        
        Args:
            user_id: ID del usuario a eliminar
            
        Raises:
            ValueError: Si el usuario no existe
        """
        async with await self._get_session() as session:
            # Buscar en la base de datos
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise ValueError(f"Usuario no encontrado: {user_id}")
            
            # Eliminar usuario
            await session.delete(user_model)
            await session.commit() 