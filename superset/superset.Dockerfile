FROM apache/superset:latest

# 1. Copiar el archivo de configuración al contenedor
COPY superset/superset_config.py /app/pythonpath/superset_config.py

# 2. Configurar la variable de entorno para que Superset sepa dónde está su configuración
ENV SUPERSET_CONFIG_PATH /app/pythonpath/superset_config.py

# Cambiamos a root para tener permisos sobre el venv
USER root

# Instalamos pip dentro del venv y luego psycopg2-binary
RUN /app/.venv/bin/python -m ensurepip && \
    /app/.venv/bin/python -m pip install --upgrade pip && \
    /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary && \
    /app/.venv/bin/python -m pip install --no-cache-dir flask-cors


# Volvemos al usuario superset
USER superset
