# GESPRO

Proyecto Django + Superset para gestión de proyectos (GESPRO).

## Índice

- [Descripción breve](#descripción-breve)
- [Archivo `.env`](#archivo-env)
- [Requisitos para ejecutar Docker Compose](#requisitos-para-ejecutar-docker-compose)
- [Pasos para levantar con Docker Compose](#pasos-para-levantar-con-docker-compose)
- [Pruebas básicas de despliegue](#pruebas-básicas-de-despliegue)

## Descripción breve

GESPRO es una aplicación basada en Django que provee funcionalidades para gestionar proyectos, vistas y reportes. Incluye un servicio web principal (Django) y una instancia de Apache Superset para visualización y exploración de datos. La configuración del entorno y los servicios se orquesta mediante Docker Compose.

## Archivo `.env`

El proyecto carga variables de entorno desde un archivo `.env` usando python-dotenv. A continuación se listan las variables relevantes y su propósito.

Variables usadas en el código y ejemplos:

- EMAIL_MODE: Modo de envío de correos. Valores: `dummy` (por defecto), `console`, `smtp`.
  - Ejemplo: `EMAIL_MODE=console`
- SMTP_SERVER: Host del servidor SMTP (solo si `EMAIL_MODE=smtp`).
  - Ejemplo: `SMTP_SERVER=smtp.mail.example`
- EMAIL: Usuario/email para autenticación SMTP (si `EMAIL_MODE=smtp`).
  - Ejemplo: `EMAIL=no-reply@example.com`
- PASSWORD_APP: Contraseña o token de aplicación para SMTP (si `EMAIL_MODE=smtp`).
  - Ejemplo: `PASSWORD_APP=mi_clave_smtp`
 - POSTGRES_DB: Nombre de la base de datos Postgres usada por Docker (default: `gespro`).
   - Ejemplo: `POSTGRES_DB=gespro`
 - POSTGRES_USER: Usuario de la base de datos Postgres (default: `albaca`).
   - Ejemplo: `POSTGRES_USER=albaca`
 - POSTGRES_PASSWORD: Contraseña de Postgres (default incluido en compose). Reemplazar en producción.
   - Ejemplo: `POSTGRES_PASSWORD=secreto_postgres`
 - POSTGRES_PORT: Puerto interno de Postgres (default: `5432`).
   - Ejemplo: `POSTGRES_PORT=5432`
 - DB_HOST: Host del servicio de BD desde Django (default: `db`).
   - Ejemplo: `DB_HOST=db`
 - DJANGO_HOST_PORT: Puerto del host para mapear el servidor Django (host:container). Default `3003`.
   - Ejemplo: `DJANGO_HOST_PORT=3003`
 - SUPERSET_HOST_PORT: Puerto del host para mapear Superset (host:container). Default `4003`.
   - Ejemplo: `SUPERSET_HOST_PORT=4003`
 - SUPERSET_ADMIN_USERNAME: Usuario admin que se creará en Superset (default: `admin`).
   - Ejemplo: `SUPERSET_ADMIN_USERNAME=admin`
 - SUPERSET_ADMIN_PASSWORD: Contraseña del admin de Superset (default: `adminpass123`).
   - Ejemplo: `SUPERSET_ADMIN_PASSWORD=adminpass123`
 - SUPERSET_ADMIN_FIRSTNAME: Nombre del admin (default: `Super`).
   - Ejemplo: `SUPERSET_ADMIN_FIRSTNAME=Super`
 - SUPERSET_ADMIN_LASTNAME: Apellido del admin (default: `Admin`).
   - Ejemplo: `SUPERSET_ADMIN_LASTNAME=Admin`
 - SUPERSET_ADMIN_EMAIL: Email del admin (default: `admin@example.com`).
   - Ejemplo: `SUPERSET_ADMIN_EMAIL=admin@example.com`

Nota: la configuración de la base de datos y credenciales usadas por Docker Compose (usuario `albaca`, contraseña y nombre de BD) están hardcodeadas en `docker-compose.yml` y en los settings de Django. Para producción se recomienda mover esas credenciales al `.env` y modificar `backend/gespro/settings.py` para leerlas desde variables de entorno.

Ejemplo mínimo de `.env` para desarrollo:

```
EMAIL_MODE=console
# Si EMAIL_MODE=smtp
# SMTP_SERVER=smtp.mail.example
# EMAIL=no-reply@example.com
# PASSWORD_APP=secreto_smtp
 
# Variables de base de datos y puertos
POSTGRES_DB=gespro
POSTGRES_USER=albaca
POSTGRES_PASSWORD=9E5Og5yodW6u0S
POSTGRES_PORT=5432
DB_HOST=db

# Puertos en el host
DJANGO_HOST_PORT=3003
SUPERSET_HOST_PORT=4003
 
# Credenciales admin Superset (creadas al iniciar el contenedor)
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=adminpass123
SUPERSET_ADMIN_FIRSTNAME=Super
SUPERSET_ADMIN_LASTNAME=Admin
SUPERSET_ADMIN_EMAIL=admin@example.com
```

Guarda este archivo en la raíz del proyecto como `.env`.

## Requisitos para ejecutar Docker Compose

Asegúrate de tener instaladas las siguientes herramientas en tu máquina:

- Docker (Engine) v20+ compatible con Compose v2.
- Docker Compose (incluido en Docker Desktop o como plugin docker-compose v2).
- Al menos 2-4 GB de memoria disponible para los contenedores; Superset y Postgres requieren memoria.
- Puerto 3003 libre (Django) y 4003 libre (Superset) en la máquina host o ajustar en `docker-compose.yml`.

Recomendación: ejecutar `docker --version` y `docker compose version` antes de comenzar.

## Pasos para levantar con Docker Compose

1. Copia el ejemplo de `.env` y ajústalo si usas SMTP:

   - Crear `.env` en la raíz del repo.

2. Construir y levantar servicios (en la raíz del proyecto):

```
docker compose up --build
```

Esto hará:
- Construir la imagen de la aplicación y de Superset.
- Crear un contenedor para Postgres con la base de datos `gespro`.
- Ejecutar las migraciones de Django y levantar el servidor en `0.0.0.0:3003`.
- Iniciar Superset en el puerto `8088` dentro del contenedor, mapeado al `4003` del host (según `docker-compose.yml`).



3. Acceder a las aplicaciones desde el navegador:

- Aplicación Django: http://localhost:3003/
- Superset: http://localhost:4003/ (usuario admin/adminpass123, creado automáticamente por el comando de arranque de Superset en el compose)

4. Parar y limpiar:

```
docker compose down --volumes --remove-orphans
```

## Pruebas básicas de despliegue

Comprobación mínima solicitada: verificar que los contenedores estén en estado "healthy".

1. Listar contenedores y revisar la columna STATUS/HEALTH:

```
docker ps
```

o usando Docker Compose:

```
docker compose ps
```

2. Para filtrar solo los contenedores que no estén healthy (si tu versión de docker lo muestra en STATUS):

```
docker ps --filter "health=unhealthy"
```

Si todos los servicios relevantes aparecen como healthy, el despliegue básico se considera correcto. 


