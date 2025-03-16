import aiomysql
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

async def init_db_pool(
    host: str = os.getenv("MYSQL_HOST", "localhost"),
    port: int = int(os.getenv("MYSQL_PORT", "3306")),
    user: str = os.getenv("MYSQL_USER", "root"),
    password: str = os.getenv("MYSQL_PASSWORD", "password"),
    db: str = os.getenv("MYSQL_DATABASE", "data_storage"),
    min_size: int = 1,
    max_size: int = 10
) -> aiomysql.Pool:
    """Initialize the MySQL connection pool"""
    try:
        pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=db,
            minsize=min_size,
            maxsize=max_size,
            autocommit=False
        )
        logger.info(f"Connected to MySQL database at {host}:{port}")
        return pool
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        raise

async def create_tables(pool: aiomysql.Pool) -> None:
    """Create the necessary tables if they don't exist"""
    async with pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # Create datasets table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at VARCHAR(30) NOT NULL,
                    updated_at VARCHAR(30) NOT NULL,
                    user_id VARCHAR(255) NOT NULL,
                    row_count INT NOT NULL DEFAULT 0,
                    column_count INT NOT NULL DEFAULT 0,
                    tags JSON NOT NULL,
                    is_public BOOLEAN NOT NULL DEFAULT FALSE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_is_public (is_public)
                )
            """)
            
            # Create dataset_columns table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS dataset_columns (
                    id VARCHAR(36) PRIMARY KEY,
                    dataset_id VARCHAR(36) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
                    INDEX idx_dataset_id (dataset_id)
                )
            """)
            
            # Create dataset_rows table
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS dataset_rows (
                    id VARCHAR(36) PRIMARY KEY,
                    dataset_id VARCHAR(36) NOT NULL,
                    data JSON NOT NULL,
                    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
                    INDEX idx_dataset_id (dataset_id)
                )
            """)
            
            await conn.commit()
            logger.info("Database tables created successfully")

async def close_db_pool(pool: Optional[aiomysql.Pool]) -> None:
    """Close the MySQL connection pool"""
    if pool:
        pool.close()
        await pool.wait_closed()
        logger.info("MySQL connection pool closed") 