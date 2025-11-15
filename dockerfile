# Usa Python
FROM python:3.13

# Crea directorio
RUN mkdir /app
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update\
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip
RUN pip install --upgrade pip

# Copiar requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proyecto
COPY . /app/

# Exponer puerto
EXPOSE 3003

# Instalar y compilar Tailwind
RUN python backend/manage.py tailwind install
RUN python backend/manage.py tailwind build
