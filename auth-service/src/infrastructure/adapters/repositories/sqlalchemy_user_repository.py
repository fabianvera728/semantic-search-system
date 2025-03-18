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
    
    def __init__(self):
        logger.info("Repositorio SQLAlchemy de usuarios inicializado")
    
    async def _get_session(self) -> AsyncSession:
        return await db.get_session()
    
    def _entity_to_model(self, user: UserEntity) -> UserModel:
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
        async with await self._get_session() as session:
            user_model = self._entity_to_model(user)
            
            session.add(user_model)
            await session.commit()
            await session.refresh(user_model)
            
            saved_user = self._model_to_entity(user_model)
            
            return copy.deepcopy(saved_user)
    
    async def find_by_id(self, user_id: str) -> Optional[UserEntity]:
        async with await self._get_session() as session:
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
    
    async def find_by_name(self, name: str) -> Optional[UserEntity]:
        async with await self._get_session() as session:
            stmt = select(UserModel).where(UserModel.name == name)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
    
    async def find_by_email(self, email: str) -> Optional[UserEntity]:
        async with await self._get_session() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                return None
            
            return self._model_to_entity(user_model)
    
    async def find_all(self) -> List[UserEntity]:
        async with await self._get_session() as session:
            stmt = select(UserModel)
            result = await session.execute(stmt)
            user_models = result.scalars().all()
            
            return [self._model_to_entity(user_model) for user_model in user_models]
    
    async def update(self, user: UserEntity) -> UserEntity:
        async with await self._get_session() as session:
            stmt = select(UserModel).where(UserModel.user_id == user.user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise ValueError(f"Usuario no encontrado: {user.user_id}")
            
            user_model.name = user.name
            user_model.email = user.email
            user_model.password_hash = user.password_hash
            user_model.roles = json.dumps(user.roles)
            user_model.is_active = user.is_active
            user_model.last_login = user.last_login
            
            await session.commit()
            await session.refresh(user_model)
            
            updated_user = self._model_to_entity(user_model)
            
            return copy.deepcopy(updated_user)
    
    async def delete(self, user_id: str) -> None:
        async with await self._get_session() as session:
            stmt = select(UserModel).where(UserModel.user_id == user_id)
            result = await session.execute(stmt)
            user_model = result.scalar_one_or_none()
            
            if not user_model:
                raise ValueError(f"Usuario no encontrado: {user_id}")
            
            await session.delete(user_model)
            await session.commit() 