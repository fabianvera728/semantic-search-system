FROM python:3.9-slim

WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias
RUN pip install -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p uploads data

# Exponer puerto
EXPOSE 8002

# Variables de entorno
ENV DATA_HARVESTER_PORT=8002

# Comando para iniciar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 