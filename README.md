# 🚀 AppTc Backend - Sistema Empresarial Integral

**Sistema backend robusto** con arquitectura hexagonal, desarrollado en Python 3.11+ y FastAPI, diseñado para aplicaciones empresariales que requieren **autenticación avanzada**, **consultas gubernamentales** y **gestión de configuraciones dinámicas**.

## 📋 Características Principales

### 🔐 **Autenticación y Autorización**
- **Integración con Clerk** para autenticación externa
- **Sistema de roles y permisos granulares** con control de acceso
- **JWT tokens** para manejo seguro de sesiones
- **Middleware de seguridad** personalizado

### 🏛️ **APIs Gubernamentales Peruanas** (Nuevo Módulo Modular)
- **RENIEC**: Consulta de ciudadanos por DNI con validación robusta
- **SUNAT**: Consulta de empresas por RUC con múltiples endpoints
- **Arquitectura modular**: Fácil agregar nuevas APIs (SUNARP, Migraciones, etc.)
- **Factory Pattern**: Gestión centralizada de servicios
- **Fallback automático**: Múltiples proveedores con respaldo
- **Preparado para caché**: Optimización de consultas frecuentes
- **Sistema de auditoría**: Trazabilidad completa de consultas
- **Validación robusta**: Documentos validados antes de consultar

### 📁 **Gestión Avanzada de Archivos**
- **Subida y almacenamiento** de archivos (logos, imágenes, documentos)
- **Metadatos completos** y categorización inteligente
- **Validación de tipos MIME** y tamaños
- **URLs públicas** para acceso controlado

### 🎨 **Configuración Dinámica de Interfaz**
- **Temas personalizables** (colores, tipografías, layouts)
- **Configuración contextual** por usuario y rol
- **Sistema de respaldo automático** de configuraciones
- **API REST** para modificación en tiempo real

### 🤖 **Sistema de Mensajería con IA**
- **Procesamiento inteligente** de mensajes de usuario
- **Historial conversacional** persistente
- **Respuestas automatizadas** contextuales

### 📊 **Auditoría y Monitoreo**
- **Logs detallados** de todas las acciones del sistema
- **Trazabilidad completa** de cambios y modificaciones
- **Metadatos de usuario** y timestamps precisos

## 🏗️ Arquitectura del Sistema

**Arquitectura Hexagonal (Clean Architecture)** que garantiza:
- ✅ **Separación clara** de responsabilidades
- ✅ **Testabilidad** y mantenibilidad
- ✅ **Flexibilidad** para cambios futuros
- ✅ **Independencia** de frameworks externos

```
src/mi_app_completa_backend/
├── domain/                 # 🎯 Lógica de negocio pura
│   ├── entities/          # User, File, AuditLog, Role, GovernmentAPIs
│   ├── repositories/      # Interfaces abstractas
│   ├── services/          # Servicios de dominio
│   └── value_objects/     # Permisos, roles, excepciones
├── application/           # 📋 Casos de uso
│   ├── use_cases/        # Lógica de aplicación específica
│   └── dto/              # Data Transfer Objects
└── infrastructure/       # 🔧 Adaptadores externos
    ├── persistence/      # Implementaciones MongoDB
    ├── web/             # APIs REST con FastAPI
    ├── services/        # Servicios externos modulares
    │   └── government_apis/  # 🏛️ Módulo APIs Gubernamentales
    │       ├── base_government_api.py
    │       ├── reniec_service.py
    │       ├── sunat_service.py
    │       └── government_factory.py
    └── config/          # Configuración del sistema
```

## 🛠️ Stack Tecnológico

### **Backend Core**
- **FastAPI** - Framework web asíncrono de alto rendimiento
- **Python 3.11+** - Lenguaje principal con typing avanzado
- **MongoDB** - Base de datos NoSQL flexible
- **Motor** - Driver asíncrono para MongoDB
- **Pydantic** - Validación de datos y serialización

### **Autenticación & Seguridad**
- **JWT** - JSON Web Tokens para sesiones
- **Clerk** - Plataforma de autenticación externa
- **bcrypt** - Hashing seguro de contraseñas
- **Cryptography** - Operaciones criptográficas avanzadas

### **Desarrollo & Testing**
- **pytest** - Framework de testing con soporte async
- **black** - Formateo automático de código
- **flake8** - Linting y análisis de código
- **mypy** - Type checking estático

### **Despliegue & DevOps**
- **Docker** - Containerización completa
- **uvicorn** - Servidor ASGI de producción
- **Scripts PowerShell/Bash** - Automatización de despliegue

## 🚀 Instalación y Configuración

### **Prerrequisitos**
```bash
# Python 3.11 o superior
python --version

# MongoDB (local o remoto)
# Docker (opcional, para containerización)
```

### **Instalación Local**
```bash
# 1. Clonar el repositorio
git clone [tu-repositorio]
cd backend

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt
```

### **Configuración de Variables de Entorno**
```bash
# Crear archivo .env
cp .env.example .env

# Configurar variables esenciales:
MONGODB_URI=mongodb://localhost:27017/apptc
CLERK_SECRET_KEY=tu_clerk_secret_key
JWT_SECRET_KEY=tu_jwt_secret_super_seguro
ENVIRONMENT=development
DEBUG=true
```

## 🎯 Uso y Ejecución

### **Desarrollo Local**
```bash
# Opción 1: Script personalizado (recomendado)
python start_server.py --env development

# Opción 2: Directamente con uvicorn
python -m uvicorn src.mi_app_completa_backend.infrastructure.web.fastapi.main:app --reload --host 0.0.0.0 --port 8000
```

### **Producción con Docker**
```bash
# Construir imagen
docker build -t apptc-backend .

# Ejecutar contenedor
docker run -p 8000:8000 -e ENVIRONMENT=production apptc-backend
```

### **Despliegue Automatizado**
```bash
# Windows
.\deploy.ps1 production

# Linux/Mac
./deploy.sh production
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Tests con cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/unit/test_user_entity.py
pytest tests/integration/
```

## 📡 API Endpoints Principales

### **Autenticación**
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/refresh` - Renovar token
- `GET /api/auth/profile` - Perfil de usuario

### **Consultas Gubernamentales**
- `GET /api/government/dni/{dni}` - Consultar persona por DNI (RENIEC)
- `GET /api/government/ruc/{ruc}` - Consultar empresa por RUC (SUNAT)
- `GET /api/government/providers` - Listar proveedores de APIs disponibles
- `GET /api/government/health` - Estado de salud de servicios

### **Gestión de Archivos**
- `POST /api/files/upload` - Subir archivo
- `GET /api/files/{file_id}` - Obtener archivo
- `DELETE /api/files/{file_id}` - Eliminar archivo

### **Configuración**
- `GET /api/config/interface` - Obtener configuración de interfaz
- `PUT /api/config/interface` - Actualizar configuración
- `GET /api/config/contextual` - Configuración contextual

## 🔧 Configuración Avanzada

### **Variables de Entorno Completas**
```env
# Base de datos
MONGODB_URI=mongodb://localhost:27017/apptc
MONGODB_DB_NAME=apptc

# Autenticación
CLERK_SECRET_KEY=tu_clerk_secret_key
JWT_SECRET_KEY=tu_jwt_secret_super_seguro
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# APIs Externas
RENIEC_API_KEY=tu_api_key_reniec
SUNAT_API_KEY=tu_api_key_sunat

# Aplicación
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
UPLOAD_MAX_SIZE=10485760  # 10MB
```

### **Estructura de Logs**
```
logs/
├── app.log          # Logs generales
├── auth.log         # Logs de autenticación
├── api.log          # Logs de APIs externas
└── error.log        # Logs de errores
```

## 🤝 Contribución

1. **Fork** el proyecto
2. Crear **feature branch** (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** cambios (`git commit -m 'Add: nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear **Pull Request**

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Documentación**: `/docs` (Swagger UI automático)
- **Issues**: Crear issue en el repositorio
- **Email**: [tu-email@empresa.com]

---

**Desarrollado con ❤️ usando Python, FastAPI y Arquitectura Hexagonal**