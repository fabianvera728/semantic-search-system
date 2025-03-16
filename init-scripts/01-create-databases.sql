-- Crear base de datos para el servicio de autenticación si no existe
CREATE DATABASE IF NOT EXISTS auth_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear base de datos para el servicio de almacenamiento de datos si no existe
CREATE DATABASE IF NOT EXISTS data_storage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Asegurar que el usuario root tenga todos los privilegios en ambas bases de datos
GRANT ALL PRIVILEGES ON auth_service.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON data_storage.* TO 'root'@'%';

-- Aplicar los cambios
FLUSH PRIVILEGES; 