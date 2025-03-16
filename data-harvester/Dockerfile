FROM python:3.9-slim

WORKDIR /app

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p uploads data

# Exponer puerto
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["python", "-m", "src.main"] 