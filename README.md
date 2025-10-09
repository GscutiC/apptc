# 🚀 AppTc Backend - Sistema Empresarial Integral

**Sistema backend robusto** con arquitectura hexagonal, desarrollado en Python 3.11+ y FastAPI, diseñado para aplicaciones empresariales que requieren **autenticación avanzada**, **consultas gubernamentales** y **gestión de configuraciones dinámicas**.

## 📋 Características Principales

### 🔐 **Autenticación y Autorización**
- **Integración con Clerk** para autenticación externa
- **Sistema de roles y permisos granulares** con control de acceso
- **JWT tokens** para manejo seguro de sesiones
- **Middleware de seguridad** personalizado

### 🏛️ **APIs Gubernamentales Peruanas** (Módulo Modular Completo)
- **RENIEC**: Consulta de ciudadanos por DNI con validación robusta
- **SUNAT**: Consulta de empresas por RUC con múltiples endpoints
- **Arquitectura modular**: Fácil agregar nuevas APIs (SUNARP, Migraciones, etc.)
- **Factory Pattern**: Gestión centralizada con registro dinámico de servicios
- **Fallback automático**: Múltiples proveedores con respaldo transparente
- **Caché inteligente**: Preparado para Redis con TTL configurable
- **Sistema de auditoría**: Trazabilidad completa de todas las consultas
- **Validación robusta**: Documentos validados antes de consultar (ahorra APIs calls)
- **Helper Service**: Interfaz simplificada para uso rápido desde cualquier módulo
- **Integración Frontend**: Documentación completa con TypeScript, hooks y componentes React
- **Quick Functions**: Funciones de una línea para casos de uso simples
- **Batch Queries**: Consultas masivas con manejo automático de errores

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
│   │   └── government_apis/  # 🏛️ Entidades de APIs Gubernamentales
│   │       ├── base_entity.py        # BaseResponse, DocumentType, APIProvider
│   │       ├── reniec_entity.py      # DniData, DniConsultaResponse
│   │       └── sunat_entity.py       # RucData, RucConsultaResponse
│   ├── repositories/      # Interfaces abstractas
│   ├── services/          # Servicios de dominio
│   └── value_objects/     # Permisos, roles, excepciones
├── application/           # 📋 Casos de uso
│   ├── use_cases/        # Lógica de aplicación específica
│   │   └── government_queries.py  # GovernmentQueriesUseCase (orquestador)
│   └── dto/              # Data Transfer Objects
│       └── government_dto.py  # DTOs para requests/responses
└── infrastructure/       # 🔧 Adaptadores externos
    ├── persistence/      # Implementaciones MongoDB
    ├── web/             # APIs REST con FastAPI
    │   └── fastapi/
    │       └── government_routes.py  # Endpoints REST con auth
    ├── services/        # Servicios externos modulares
    │   ├── government_apis/  # 🏛️ Módulo APIs Gubernamentales
    │   │   ├── base_government_api.py   # Abstract base class
    │   │   ├── reniec_service.py        # Implementación RENIEC
    │   │   ├── sunat_service.py         # Implementación SUNAT
    │   │   └── government_factory.py    # Factory para servicios
    │   └── government_helper.py  # 🚀 Helper service (uso simplificado)
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

### **Uso Rápido del Módulo Gubernamental** 🏛️

```python
# Desde cualquier parte del backend
from infrastructure.services.government_helper import quick_query_dni, quick_query_ruc

# Consultar DNI en una línea
persona = await quick_query_dni("12345678")
if persona:
    print(f"Nombre: {persona.nombre_completo}")

# Consultar RUC en una línea
empresa = await quick_query_ruc("20123456789")
if empresa:
    print(f"Empresa: {empresa.razon_social}, Estado: {empresa.estado}")
```

**Más formas de uso:**
- **Helper Service**: Interfaz completa con métodos como `get_persona_by_dni()`, `validate_dni()`, batch queries
- **Use Cases**: Integración en flujos complejos con cache y auditoría
- **Factory Pattern**: Acceso directo a servicios específicos
- **API REST**: Endpoints protegidos para frontend

👉 **Ver ejemplos completos**: `examples/government_apis_usage.py` (12 casos de uso)
👉 **Guía rápida**: `docs/QUICK_START_GOVERNMENT_APIS.md`

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

### **Consultas Gubernamentales** 🏛️ (Requiere Autenticación)
- `GET /api/government/dni/{dni}` - Consultar persona por DNI (RENIEC)
  - Respuesta: `{ success, data: { dni, nombre_completo, ... }, fuente, cache_hit }`
- `GET /api/government/ruc/{ruc}` - Consultar empresa por RUC (SUNAT)
  - Respuesta: `{ success, data: { ruc, razon_social, estado, ... }, fuente }`
- `GET /api/government/providers` - Listar proveedores de APIs disponibles
- `GET /api/government/health` - Estado de salud de servicios

**Documentación Detallada:**
- **Guía Rápida**: `docs/QUICK_START_GOVERNMENT_APIS.md` ⭐ EMPIEZA AQUÍ
- **Módulo Completo**: `docs/GOVERNMENT_APIS_MODULE.md`
- **Frontend**: `docs/FRONTEND_INTEGRATION.md`
- **Ejemplos Python**: `examples/government_apis_usage.py`

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

# APIs Gubernamentales (Opcional - usan endpoints públicos por defecto)
RENIEC_API_KEY=tu_api_key_reniec  # Opcional
SUNAT_API_KEY=tu_api_key_sunat    # Opcional

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

### **Documentación del Proyecto**
- **Swagger UI**: `http://localhost:8000/docs` - Documentación interactiva de API
- **ReDoc**: `http://localhost:8000/redoc` - Documentación alternativa

### **Módulo APIs Gubernamentales** 🏛️
- **🚀 EMPIEZA AQUÍ**: `docs/QUICK_START_GOVERNMENT_APIS.md` - Guía rápida
- **📖 Documentación Técnica**: `docs/GOVERNMENT_APIS_MODULE.md`
- **🌐 Integración Frontend**: `docs/FRONTEND_INTEGRATION.md`
- **💻 Ejemplos Python**: `examples/government_apis_usage.py`

### **Contacto**
- **Issues**: Crear issue en el repositorio
- **Email**: [tu-email@empresa.com]

---

**Desarrollado con ❤️ usando Python, FastAPI y Arquitectura Hexagonal**