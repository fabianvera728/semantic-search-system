import uvicorn

from src.config import get_app_config, create_app


config = get_app_config()
app = create_app(config)


@app.get("/")
async def root():
    return {
        "service": "Data Harvester Service",
        "version": "2.0.0",
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