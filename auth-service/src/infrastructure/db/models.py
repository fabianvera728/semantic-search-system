import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    """Clase base para todos los modelos de SQLAlchemy."""
    pass


class User(Base):
    """Modelo de usuario para SQLAlchemy."""
    __tablename__ = "users"
    
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[str] = mapped_column(Text, nullable=False)  # JSON almacenado como texto
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relación con tokens
    tokens: Mapped[List["Token"]] = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, name={self.name}, email={self.email})>"


class Token(Base):
    """Modelo de token para SQLAlchemy."""
    __tablename__ = "tokens"
    
    token_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    token_value: Mapped[str] = mapped_column(String(1024), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relación con usuario
    user: Mapped[User] = relationship("User", back_populates="tokens")
    
    def __repr__(self) -> str:
        return f"<Token(token_id={self.token_id}, user_id={self.user_id}, token_type={self.token_type})>" 