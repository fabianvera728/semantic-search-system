# Base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create required directories
RUN mkdir -p /app/storage/logs

# Copy application code
COPY . .

# Expose port
EXPOSE 8003

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"] 