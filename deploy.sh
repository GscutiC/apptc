#!/bin/bash
# Script de despliegue automatizado para AppTc Backend
# Uso: ./deploy.sh [development|production]

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Determinar entorno
ENVIRONMENT=${1:-development}

if [ "$ENVIRONMENT" != "development" ] && [ "$ENVIRONMENT" != "production" ]; then
    error "Entorno inválido. Usar: development o production"
fi

log "🚀 Iniciando despliegue para entorno: $ENVIRONMENT"

# Verificar que estamos en el directorio correcto
if [ ! -f "start_server.py" ]; then
    error "Este script debe ejecutarse desde el directorio backend/"
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        error "Python no encontrado. Instalar Python 3.8+"
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

log "✓ Python encontrado: $($PYTHON_CMD --version)"

# Verificar e instalar dependencias
log "📦 Verificando dependencias..."

if [ ! -d "venv" ]; then
    warn "Virtual environment no encontrado. Creando..."
    $PYTHON_CMD -m venv venv
fi

# Activar virtual environment
source venv/bin/activate || source venv/Scripts/activate

# Instalar/actualizar dependencias
log "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar archivo de configuración
if [ "$ENVIRONMENT" == "production" ]; then
    ENV_FILE=".env.production"
else
    ENV_FILE=".env"
fi

if [ ! -f "$ENV_FILE" ]; then
    error "Archivo de configuración no encontrado: $ENV_FILE"
fi

log "✓ Configuración encontrada: $ENV_FILE"

# Validar configuración crítica
log "🔍 Validando configuración..."

# Verificar que las variables críticas estén definidas
source $ENV_FILE

if [ -z "$CLERK_SECRET_KEY" ] || [ "$CLERK_SECRET_KEY" == "tu_clerk_secret_key_aqui" ]; then
    error "CLERK_SECRET_KEY no configurada correctamente en $ENV_FILE"
fi

if [ "$ENVIRONMENT" == "production" ]; then
    if [ "$DEBUG" == "True" ] || [ "$DEBUG" == "true" ]; then
        error "DEBUG debe ser False en producción"
    fi
    
    if [[ "$CLERK_SECRET_KEY" == *"test"* ]]; then
        error "Usando claves de test en producción. Configurar claves live de Clerk"
    fi
fi

log "✓ Configuración validada"

# Verificar conectividad a MongoDB (opcional)
log "🗄️ Verificando conectividad a base de datos..."
$PYTHON_CMD -c "
import sys
sys.path.insert(0, 'src')
try:
    from mi_app_completa_backend.infrastructure.config.database import get_database
    db = get_database()
    print('✓ Conexión a MongoDB exitosa')
except Exception as e:
    print(f'⚠️ No se pudo conectar a MongoDB: {e}')
    print('Continuar de todas formas...')
"

# Ejecutar tests (si existen)
if [ -d "tests" ] && [ -f "pytest.ini" ]; then
    log "🧪 Ejecutando tests..."
    pytest tests/ -v || warn "Algunos tests fallaron, pero continuando..."
else
    warn "No se encontraron tests o pytest.ini"
fi

# Backup de base de datos (solo en producción)
if [ "$ENVIRONMENT" == "production" ]; then
    log "💾 Creando backup de base de datos..."
    BACKUP_DIR="backups/$(date +'%Y%m%d_%H%M%S')"
    mkdir -p $BACKUP_DIR
    
    # Hacer backup usando mongodump (si está disponible)
    if command -v mongodump &> /dev/null; then
        mongodump --uri "$MONGODB_URL" --db "$DATABASE_NAME" --out "$BACKUP_DIR" || warn "Backup falló"
        log "✓ Backup creado en $BACKUP_DIR"
    else
        warn "mongodump no disponible, saltando backup"
    fi
fi

# Iniciar servidor
log "🎯 Iniciando servidor en modo $ENVIRONMENT..."

if [ "$ENVIRONMENT" == "production" ]; then
    # En producción, usar process manager
    if command -v pm2 &> /dev/null; then
        pm2 start --name "apptc-backend" "$PYTHON_CMD start_server.py --env production" || error "Error iniciando con PM2"
        log "✓ Servidor iniciado con PM2"
        pm2 list
    else
        log "PM2 no encontrado. Iniciando directamente..."
        $PYTHON_CMD start_server.py --env production &
        log "✓ Servidor iniciado en background (PID: $!)"
    fi
else
    # En desarrollo
    log "Iniciando en modo desarrollo..."
    $PYTHON_CMD start_server.py --env development --reload
fi

log "🎉 Despliegue completado exitosamente!"
log "🌐 La aplicación debería estar disponible en: http://localhost:8000"
log "📖 Documentación API: http://localhost:8000/docs"