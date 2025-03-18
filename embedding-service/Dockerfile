FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create storage directory for ChromaDB
RUN mkdir -p /app/storage/chroma

# Expose port
EXPOSE 8005

# Variable de entorno para evitar problemas con UTF-8
ENV PYTHONUNBUFFERED=1

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"] 