FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "-m", "src.{{PROJECT_NAME}}.infrastructure.web.fastapi.main"]