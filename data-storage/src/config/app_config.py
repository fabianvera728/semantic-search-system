import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv


@dataclass
class AppConfig:    
    host: str
    port: int

    allowed_origins: List[str]
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    use_in_memory_db: bool

    log_level: str
    log_file: Optional[str]


def get_app_config() -> AppConfig:
    load_dotenv()
    
    host = os.getenv("DATA_STORAGE_HOST", "0.0.0.0")
    port = int(os.getenv("DATA_STORAGE_PORT", "8003"))
    allowed_origins = os.getenv("DATA_STORAGE_ALLOWED_ORIGINS", "*").split(",")
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "password")
    mysql_database = os.getenv("MYSQL_DATABASE", "data_storage")
    use_in_memory_db = os.getenv("USE_IN_MEMORY_DB", "false").lower() == "true"
    log_level = os.getenv("DATA_STORAGE_LOG_LEVEL", "INFO")
    log_file = os.getenv("DATA_STORAGE_LOG_FILE")
    
    return AppConfig(
        host=host,
        port=port,
        allowed_origins=allowed_origins,
        mysql_host=mysql_host,
        mysql_port=mysql_port,
        mysql_user=mysql_user,
        mysql_password=mysql_password,
        mysql_database=mysql_database,
        use_in_memory_db=use_in_memory_db,
        log_level=log_level,
        log_file=log_file
    ) 