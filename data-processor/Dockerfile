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
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port (default to 8004)
EXPOSE 8004

# Set default environment variables
ENV DATA_PROCESSOR_HOST=0.0.0.0
ENV DATA_PROCESSOR_PORT=8004

# Run the application using environment variables
CMD ["python", "main.py"] 