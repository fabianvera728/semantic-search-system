FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Exponer el puerto
EXPOSE 8001

# Variables de entorno para la configuración de la aplicación
ENV HOST=0.0.0.0
ENV PORT=8001
ENV ALLOWED_ORIGINS=*
ENV LOG_LEVEL=INFO

# Variables de entorno para la configuración de JWT
ENV JWT_SECRET=your_jwt_secret_key_here
ENV JWT_ALGORITHM=HS256
ENV ACCESS_TOKEN_EXPIRES_IN=3600
ENV REFRESH_TOKEN_EXPIRES_IN=604800

# Variables de entorno para la conexión a MySQL
ENV USE_IN_MEMORY_DB=false
ENV DB_HOST=mysql
ENV DB_PORT=3306
ENV DB_USER=root
ENV DB_PASSWORD=password
ENV DB_DATABASE=auth_service

# Comando para iniciar la aplicación
CMD ["python", "main.py"] 