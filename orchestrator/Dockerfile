FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Variables de entorno
ENV API_GATEWAY_HOST=0.0.0.0
ENV API_GATEWAY_PORT=8000
ENV AUTH_SERVICE_URL=http://auth-service:8001
ENV DATA_HARVESTER_URL=http://data-harvester:8002
ENV DATA_PROCESSOR_URL=http://data-processor:8003
ENV EMBEDDING_SERVICE_URL=http://embedding-service:8004
ENV SEARCH_SERVICE_URL=http://search-service:8005

# Comando para iniciar la aplicación
CMD ["python", "main.py"] 