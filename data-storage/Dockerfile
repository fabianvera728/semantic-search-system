FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    default-libmysqlclient-dev \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Set environment variables
ENV PYTHONPATH=/app
ENV MYSQL_HOST=mysql
ENV MYSQL_PORT=3306
ENV MYSQL_USER=root
ENV MYSQL_PASSWORD=password
ENV MYSQL_DATABASE=data_storage
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 