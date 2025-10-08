# Script de despliegue automatizado para AppTc Backend (Windows PowerShell)
# Uso: .\deploy.ps1 [development|production]

param(
    [Parameter(Position=0)]
    [ValidateSet("development", "production")]
    [string]$Environment = "development"
)

# Funciones para logging con colores
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Green
}

function Write-Warning-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $Message" -ForegroundColor Red
    exit 1
}

Write-Log "🚀 Iniciando despliegue para entorno: $Environment"

# Verificar que estamos en el directorio correcto
if (!(Test-Path "start_server.py")) {
    Write-Error-Log "Este script debe ejecutarse desde el directorio backend/"
}

# Verificar Python
$pythonCmd = $null
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Error-Log "Python no encontrado. Instalar Python 3.8+"
}

$pythonVersion = & $pythonCmd --version
Write-Log "✓ Python encontrado: $pythonVersion"

# Verificar e instalar dependencias
Write-Log "📦 Verificando dependencias..."

if (!(Test-Path "venv")) {
    Write-Warning-Log "Virtual environment no encontrado. Creando..."
    & $pythonCmd -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error-Log "Error creando virtual environment"
    }
}

# Activar virtual environment
$venvActivate = if (Test-Path "venv\Scripts\activate.ps1") { "venv\Scripts\activate.ps1" } else { "venv\Scripts\Activate.ps1" }
if (Test-Path $venvActivate) {
    & $venvActivate
} else {
    Write-Error-Log "No se pudo encontrar el script de activación del virtual environment"
}

# Instalar/actualizar dependencias
Write-Log "📦 Instalando dependencias..."
& python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error-Log "Error actualizando pip"
}

& pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error-Log "Error instalando dependencias"
}

# Verificar archivo de configuración
$envFile = if ($Environment -eq "production") { ".env.production" } else { ".env" }

if (!(Test-Path $envFile)) {
    Write-Error-Log "Archivo de configuración no encontrado: $envFile"
}

Write-Log "✓ Configuración encontrada: $envFile"

# Validar configuración crítica
Write-Log "🔍 Validando configuración..."

# Leer variables del archivo .env
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        $envVars[$matches[1]] = $matches[2]
    }
}

# Verificar variables críticas
if ([string]::IsNullOrEmpty($envVars["CLERK_SECRET_KEY"]) -or $envVars["CLERK_SECRET_KEY"] -eq "tu_clerk_secret_key_aqui") {
    Write-Error-Log "CLERK_SECRET_KEY no configurada correctamente en $envFile"
}

if ($Environment -eq "production") {
    if ($envVars["DEBUG"] -eq "True" -or $envVars["DEBUG"] -eq "true") {
        Write-Error-Log "DEBUG debe ser False en producción"
    }
    
    if ($envVars["CLERK_SECRET_KEY"] -like "*test*") {
        Write-Error-Log "Usando claves de test en producción. Configurar claves live de Clerk"
    }
}

Write-Log "✓ Configuración validada"

# Verificar conectividad a MongoDB (opcional)
Write-Log "🗄️ Verificando conectividad a base de datos..."
$dbTestScript = @"
import sys
sys.path.insert(0, 'src')
try:
    from mi_app_completa_backend.infrastructure.config.database import get_database
    db = get_database()
    print('✓ Conexión a MongoDB exitosa')
except Exception as e:
    print(f'⚠️ No se pudo conectar a MongoDB: {e}')
    print('Continuar de todas formas...')
"@

& python -c $dbTestScript

# Ejecutar tests (si existen)
if ((Test-Path "tests") -and (Test-Path "pytest.ini")) {
    Write-Log "🧪 Ejecutando tests..."
    & pytest tests/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Warning-Log "Algunos tests fallaron, pero continuando..."
    }
} else {
    Write-Warning-Log "No se encontraron tests o pytest.ini"
}

# Backup de base de datos (solo en producción)
if ($Environment -eq "production") {
    Write-Log "💾 Creando backup de base de datos..."
    $backupDir = "backups\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    
    # Hacer backup usando mongodump (si está disponible)
    if (Get-Command "mongodump" -ErrorAction SilentlyContinue) {
        $mongoUrl = $envVars["MONGODB_URL"]
        $dbName = $envVars["DATABASE_NAME"]
        & mongodump --uri $mongoUrl --db $dbName --out $backupDir
        if ($LASTEXITCODE -eq 0) {
            Write-Log "✓ Backup creado en $backupDir"
        } else {
            Write-Warning-Log "Backup falló"
        }
    } else {
        Write-Warning-Log "mongodump no disponible, saltando backup"
    }
}

# Iniciar servidor
Write-Log "🎯 Iniciando servidor en modo $Environment..."

if ($Environment -eq "production") {
    # En producción, iniciar en background
    Write-Log "Iniciando en modo producción..."
    $job = Start-Job -ScriptBlock {
        param($pythonCmd, $workingDir)
        Set-Location $workingDir
        & $pythonCmd start_server.py --env production
    } -ArgumentList $pythonCmd, (Get-Location)
    
    Write-Log "✓ Servidor iniciado en background (Job ID: $($job.Id))"
    Write-Log "Usar 'Get-Job' para ver el estado y 'Stop-Job $($job.Id)' para detener"
} else {
    # En desarrollo
    Write-Log "Iniciando en modo desarrollo..."
    Write-Log "Presiona Ctrl+C para detener el servidor"
    & python start_server.py --env development --reload
}

Write-Log "🎉 Despliegue completado exitosamente!"
Write-Log "🌐 La aplicación debería estar disponible en: http://localhost:8000"
Write-Log "📖 Documentación API: http://localhost:8000/docs"