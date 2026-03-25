# Gespro Project - Guía de Configuración

Este proyecto es una aplicación Django que utiliza Tailwind CSS, PostgreSQL y Superset. Sigue estos pasos para configurar tu entorno de desarrollo local.

## Requisitos Previos

* **Conda** (Anaconda o Miniconda) instalado.
* **Python 3.10+** (instalado dentro del entorno de Conda).

---

## Paso 1: Configuración del Entorno Virtual

Si aún no has creado o activado tu entorno, ejecuta:

```bash
conda activate gespro
# Asegúrate de tener pip instalado en el entorno
conda install pip
```

## Paso 2: Configuración de Variables de Entorno

Debes crear un archivo llamado `.env` en la raíz del proyecto y pegar el siguiente contenido:

```env
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
 
# Credenciales admin Superset
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=adminpass123
SUPERSET_ADMIN_FIRSTNAME=Super
SUPERSET_ADMIN_LASTNAME=Admin
SUPERSET_ADMIN_EMAIL=admin@example.com
```

## Paso 3: Instalación de Dependencias

Con el entorno activo, instala todas las librerías necesarias:

```bash
pip install -r requirements.txt
```

## Paso 4: Ejecución del Programa

Navega a la carpeta del servidor y prepara la base de datos y los estilos:

```bash
# Entrar al directorio del backend
cd backend/

# Aplicar las migraciones a la base de datos
python manage.py migrate

# Generar los archivos de estilo de Tailwind
python manage.py tailwind build

# Iniciar el servidor de desarrollo
python manage.py runserver
```

El servidor estará disponible en: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

```