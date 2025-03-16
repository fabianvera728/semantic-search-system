import uvicorn

from src.config import create_app, get_app_config


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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True
    ) 