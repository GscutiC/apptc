# Documentación de Configuración y Despliegue - AppTc Backend

## 📋 Resumen de Mejoras Implementadas

Se ha implementado un sistema de configuración profesional que elimina la duplicación de configuración y prepara la aplicación para producción.

### ✅ Cambios Realizados

1. **Limpieza de start_server.py**: Eliminada configuración hardcodeada
2. **Sistema de configuración centralizada**: Implementado con Pydantic Settings
3. **Configuración de producción**: Archivo .env.production optimizado
4. **Script de inicio mejorado**: Soporte para múltiples entornos

## 🏗️ Arquitectura de Configuración

```
backend/
├── .env                    # Configuración de desarrollo
├── .env.production         # Configuración de producción
├── start_server.py         # Script de inicio con argumentos CLI
└── src/
    └── mi_app_completa_backend/
        └── infrastructure/
            └── config/
                ├── settings.py     # Configuración centralizada
                └── database.py     # Config DB actualizada
```

## 🔧 Uso del Sistema de Configuración

### Desarrollo (por defecto)
```bash
python start_server.py
# o
python start_server.py --env development
```

### Producción
```bash
python start_server.py --env production
```

### Opciones Avanzadas
```bash
# Usar archivo .env personalizado
python start_server.py --env-file .env.custom

# Sobrescribir host y puerto
python start_server.py --host 127.0.0.1 --port 9000

# Activar reload en desarrollo
python start_server.py --reload
```

## 📁 Archivos de Configuración

### .env (Desarrollo)
```bash
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=apptc
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_WEBHOOK_SECRET=whsec_test_...
```

### .env.production (Producción)
```bash
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=apptc
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
CLERK_SECRET_KEY=sk_live_...
CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_WEBHOOK_SECRET=whsec_...
LOG_LEVEL=WARNING
MAX_UPLOAD_SIZE=10485760
RATE_LIMIT_PER_MINUTE=100
```

## 🚀 Guía de Despliegue

### Requisitos Previos
1. Python 3.8+
2. MongoDB configurado
3. Claves de Clerk de producción
4. Dominio configurado (para CORS)

### Pasos de Despliegue

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de producción**:
   ```bash
   # Copiar y editar archivo de producción
   cp .env .env.production
   # Editar .env.production con valores reales
   ```

3. **Ejecutar en producción**:
   ```bash
   python start_server.py --env production
   ```

### Despliegue con Docker

1. **Actualizar Dockerfile** (ver siguiente sección)
2. **Construir imagen**:
   ```bash
   docker build -t apptc-backend .
   ```
3. **Ejecutar contenedor**:
   ```bash
   docker run -p 8000:8000 --env-file .env.production apptc-backend
   ```

## 📋 Variables de Entorno Disponibles

| Variable | Descripción | Desarrollo | Producción |
|----------|-------------|------------|------------|
| `MONGODB_URL` | URL de MongoDB | `mongodb://localhost:27017` | Configurar según servidor |
| `DATABASE_NAME` | Nombre de BD | `apptc` | `apptc` |
| `API_HOST` | Host de la API | `0.0.0.0` | `0.0.0.0` |
| `API_PORT` | Puerto de la API | `8000` | `8000` |
| `DEBUG` | Modo debug | `True` | `False` |
| `CORS_ORIGINS` | Orígenes CORS | `localhost:3000` | Tu dominio real |
| `CLERK_SECRET_KEY` | Clave Clerk | Test key | Production key |
| `LOG_LEVEL` | Nivel de logs | `INFO` | `WARNING` |
| `MAX_UPLOAD_SIZE` | Tamaño max archivo | `10485760` | `10485760` |
| `RATE_LIMIT_PER_MINUTE` | Límite requests | `100` | `100` |

## 🔒 Seguridad en Producción

### Configuraciones Importantes
- `DEBUG=False` en producción
- CORS restrictivo a tu dominio
- Usar claves Clerk de producción (sk_live_, pk_live_)
- Configurar rate limiting apropiado
- Logs nivel WARNING o ERROR

### Variables Sensibles
- Mantener `CLERK_SECRET_KEY` segura
- No commitear archivos .env al repositorio
- Usar gestores de secretos en producción (AWS Secrets Manager, etc.)

## 🐛 Troubleshooting

### Error de importación de pydantic-settings
```bash
pip install pydantic-settings>=2.0.0
```

### Variables no cargadas
- Verificar que el archivo .env existe
- Comprobar nombres de variables (case insensitive)
- Usar --env-file para archivos personalizados

### Problemas de CORS
- Actualizar CORS_ORIGINS con tu dominio real
- Verificar protocolo (http vs https)
- Incluir subdominios si es necesario

## 📚 Próximos Pasos

1. ✅ Configurar MongoDB en producción
2. ✅ Obtener claves Clerk de producción  
3. ✅ Configurar dominio y SSL
4. ✅ Implementar monitoring y logs
5. ✅ Configurar backup de base de datos
6. ✅ Implementar CI/CD pipeline