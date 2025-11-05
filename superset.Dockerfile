FROM apache/superset:latest

# Cambiamos a root para tener permisos sobre el venv
USER root

# Instalamos pip dentro del venv y luego psycopg2-binary
RUN /app/.venv/bin/python -m ensurepip && \
    /app/.venv/bin/python -m pip install --upgrade pip && \
    /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary

# Volvemos al usuario superset
USER superset
