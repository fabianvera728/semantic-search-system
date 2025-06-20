import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import asyncio

from .models import Base


logger = logging.getLogger(__name__)


class Database:
    
    def __init__(self):
        self.engine = None
        self.async_session_factory = None
        self.host = None
        self.port = None
        self.user = None
        self.password = None
        self.database = None
    
    async def connect(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        use_connection_pool: bool = True
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
        await self._connect_with_retry(
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            use_connection_pool=use_connection_pool
        )
    
    async def _connect_with_retry(
        self,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        use_connection_pool: bool = True,
        max_retries: int = 5,
        retry_interval: int = 3
    ):
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                await self._create_database_if_not_exists()
                
                connection_url = f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
                logger.info(f"Conectando a la base de datos MySQL en {self.host}:{self.port}")
                
                if use_connection_pool:
                    self.engine = create_async_engine(
                        connection_url,
                        echo=echo,
                        pool_size=pool_size,
                        max_overflow=max_overflow,
                        pool_recycle=pool_recycle,
                        pool_pre_ping=pool_pre_ping
                    )
                else:
                    self.engine = create_async_engine(
                        connection_url,
                        echo=echo,
                        poolclass=NullPool
                    )
                
                self.async_session_factory = async_sessionmaker(
                    bind=self.engine,
                    expire_on_commit=False,
                    class_=AsyncSession
                )
                
                logger.info("Conexión a la base de datos MySQL establecida")
                return
            except Exception as e:
                last_error = e
                logger.warning(f"Error al conectar a la base de datos: {e}. Reintentando en {retry_interval} segundos...")
                retries += 1
                await asyncio.sleep(retry_interval)
        
        logger.error(f"No se pudo conectar a la base de datos después de {max_retries} intentos: {last_error}")
        raise last_error
    
    async def _create_database_if_not_exists(self):
        try:
            connection_url = f"mysql+asyncmy://{self.user}:{self.password}@{self.host}:{self.port}/"
            temp_engine = create_async_engine(
                connection_url
            )
            
            async with temp_engine.connect() as conn:
                create_db_sql = text(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                await conn.execute(create_db_sql)
                await conn.commit()
                logger.info(f"Base de datos {self.database} creada o verificada")
            
            # Cerrar la conexión temporal
            await temp_engine.dispose()
        except Exception as e:
            logger.error(f"Error al crear la base de datos: {e}")
            raise
    
    async def create_tables(self):
        """Crea las tablas en la base de datos."""
        logger.info("Creando tablas en la base de datos")
        
        async with self.engine.begin() as conn:
            # Primero eliminar las tablas existentes para aplicar cambios en el esquema
            # logger.info("Eliminando tablas existentes para aplicar cambios en el esquema")
            # await conn.run_sync(Base.metadata.drop_all)
            
            logger.info("Creando tablas con el esquema actualizado")
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Tablas creadas exitosamente")
    
    async def get_session(self) -> AsyncSession:
        return self.async_session_factory()
    
    async def close(self):
        if self.engine:
            logger.info("Cerrando conexión a la base de datos MySQL")
            await self.engine.dispose()
            logger.info("Conexión a la base de datos MySQL cerrada")


db = Database() 