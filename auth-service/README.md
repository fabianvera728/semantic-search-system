# Authentication Service

Este servicio proporciona funcionalidades de autenticación y autorización para el sistema de búsqueda semántica.

## Características

- Registro de usuarios
- Inicio de sesión con generación de tokens JWT
- Refresco de tokens
- Validación de tokens
- Cierre de sesión

## Arquitectura

El servicio sigue una arquitectura hexagonal (puertos y adaptadores) con las siguientes capas:

- **Domain**: Contiene las entidades del dominio, puertos y servicios.
- **Application**: Contiene los casos de uso que orquestan la lógica de negocio.
- **Infrastructure**: Contiene los adaptadores que implementan los puertos y la configuración.

## Endpoints

- `POST /auth/register`: Registra un nuevo usuario.
- `POST /auth/login`: Inicia sesión y genera tokens.
- `POST /auth/refresh`: Refresca un token de acceso utilizando un token de refresco.
- `POST /auth/logout`: Cierra sesión revocando el token.
- `GET /auth/me`: Obtiene la información del usuario actual.
- `GET /auth/validate`: Valida un token de acceso.

## Configuración

La configuración se realiza mediante variables de entorno:

- `AUTH_SERVICE_HOST`: Host del servidor (por defecto: "0.0.0.0").
- `AUTH_SERVICE_PORT`: Puerto del servidor (por defecto: 8001).
- `AUTH_SERVICE_JWT_SECRET`: Clave secreta para firmar los tokens JWT.
- `AUTH_SERVICE_JWT_ALGORITHM`: Algoritmo para firmar los tokens JWT (por defecto: "HS256").
- `AUTH_SERVICE_ACCESS_TOKEN_EXPIRES_IN`: Tiempo de expiración del token de acceso en segundos (por defecto: 3600).
- `AUTH_SERVICE_REFRESH_TOKEN_EXPIRES_IN`: Tiempo de expiración del token de refresco en segundos (por defecto: 2592000).
- `AUTH_SERVICE_ALLOWED_ORIGINS`: Orígenes permitidos para CORS (por defecto: "*").
- `AUTH_SERVICE_LOG_LEVEL`: Nivel de logging (por defecto: "INFO").
- `AUTH_SERVICE_LOG_FILE`: Archivo de log (opcional).

## Ejecución

### Con Docker

```bash
docker build -t auth-service .
docker run -p 8001:8001 auth-service
```

### Sin Docker

```bash
pip install -r requirements.txt
python main.py
``` 