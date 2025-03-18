import uvicorn
from sqlalchemy import text

from src.config import create_app, get_app_config
from src.infrastructure.db import db


config = get_app_config()
app = create_app(config)


@app.get("/")
async def root():
    return {
        "service": "Data Storage Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/db-status")
async def db_status():
    """Verificar el estado de la base de datos y las tablas."""
    try:
        # Verificar conexión a la base de datos
        async with db.engine.connect() as conn:
            # Obtener lista de tablas
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            
            # Obtener conteo de registros por tabla
            table_counts = {}
            for table in tables:
                count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                table_counts[table] = count
            
            return {
                "status": "connected",
                "tables": tables,
                "record_counts": table_counts
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True
    ) 