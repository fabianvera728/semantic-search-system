import logging
import aiomysql
from aiomysql import Pool


logger = logging.getLogger(__name__)


async def create_pool(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    maxsize: int = 10,
    autocommit: bool = True,
    connect_timeout: int = 10,
    charset: str = "utf8mb4"
) -> Pool:
    """
    Crea un pool de conexiones a MySQL.
    
    Args:
        host: Host de MySQL
        port: Puerto de MySQL
        user: Usuario de MySQL
        password: Contraseña de MySQL
        database: Base de datos de MySQL
        maxsize: Tamaño máximo del pool
        autocommit: Si se debe hacer autocommit
        connect_timeout: Tiempo de espera para la conexión
        charset: Charset de la conexión
        
    Returns:
        Pool: Pool de conexiones a MySQL
    """
    logger.info(f"Creando pool de conexiones a MySQL en {host}:{port}")
    
    pool = await aiomysql.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        db=database,
        maxsize=maxsize,
        autocommit=autocommit,
        connect_timeout=connect_timeout,
        charset=charset
    )
    
    logger.info("Pool de conexiones a MySQL creado exitosamente")
    
    return pool


async def init_db(pool: Pool) -> None:
    """
    Inicializa la base de datos creando las tablas necesarias si no existen.
    
    Args:
        pool: Pool de conexiones a MySQL
    """
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Crear tabla de usuarios
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id VARCHAR(36) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        roles JSON NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at DATETIME NOT NULL,
                        last_login DATETIME NULL
                    )
                """)
                
                # Crear índices
                await cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_name ON users (name)
                """)
                
                await cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)
                """)
                
                # Crear tabla de tokens
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tokens (
                        token_id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        token_type VARCHAR(20) NOT NULL,
                        token_value VARCHAR(255) NOT NULL,
                        expires_at DATETIME NOT NULL,
                        created_at DATETIME NOT NULL,
                        is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                    )
                """)
                
                # Crear índices
                await cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens (user_id)
                """)
                
                await cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tokens_token_value ON tokens (token_value)
                """)
                
                await conn.commit()
                
                logger.info("Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise 