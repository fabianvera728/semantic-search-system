import uvicorn

from src.config import create_app, get_app_config


config = get_app_config()
app = create_app(config)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=False
    ) 