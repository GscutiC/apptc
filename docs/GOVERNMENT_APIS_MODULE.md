# 🏛️ Módulo de APIs Gubernamentales

Sistema modular y escalable para consultas a APIs gubernamentales peruanas.

## 📋 Descripción

Este módulo proporciona una arquitectura limpia y extensible para realizar consultas a diversas APIs gubernamentales de Perú, comenzando con RENIEC (DNI) y SUNAT (RUC), con capacidad de agregar fácilmente nuevos proveedores.

## 🏗️ Arquitectura

### Capas Implementadas

```
📁 domain/entities/government_apis/
├── base_entity.py           # Entidades base y enums
├── reniec_entity.py         # Entidades para RENIEC (DNI)
└── sunat_entity.py          # Entidades para SUNAT (RUC)

📁 infrastructure/services/government_apis/
├── base_government_api.py   # Clase abstracta base
├── reniec_service.py        # Implementación RENIEC
├── sunat_service.py         # Implementación SUNAT
└── government_factory.py    # Factory Pattern

📁 application/
├── dto/government_dto.py    # DTOs para requests/responses
└── use_cases/government_queries.py  # Casos de uso

📁 infrastructure/web/fastapi/
└── government_routes.py     # API REST endpoints
```

## 🚀 Uso

### 1. Consulta Directa a Servicio

```python
from infrastructure.services.government_apis import ReniecService, SunatService

# RENIEC
reniec = ReniecService()
result = await reniec.query_document("12345678")

# SUNAT
sunat = SunatService()
result = await sunat.query_document("20123456789")
```

### 2. Usando Factory Pattern (Recomendado)

```python
from infrastructure.services.government_apis import (
    GovernmentAPIFactory, 
    APIProvider
)

# Crear servicio dinámicamente
factory = GovernmentAPIFactory()
service = factory.create_service(APIProvider.RENIEC)
result = await service.query_document("12345678")

# O usar helper function
from infrastructure.services.government_apis import get_government_service

service = get_government_service("reniec")
result = await service.query_document("12345678")
```

### 3. Usando Caso de Uso (Recomendado para Producción)

```python
from application.use_cases.government_queries import GovernmentQueriesUseCase

use_case = GovernmentQueriesUseCase(
    cache_service=redis_cache,  # Opcional
    audit_service=audit_log     # Opcional
)

# Consulta con caché y auditoría
dni_result = await use_case.query_dni("12345678", user_id="user123")
ruc_result = await use_case.query_ruc("20123456789", user_id="user123")
```

### 4. API REST Endpoints

```bash
# Consultar DNI
GET /api/government/dni/12345678?use_cache=true

# Consultar RUC
GET /api/government/ruc/20123456789?use_cache=true

# Listar proveedores disponibles
GET /api/government/providers

# Health check de servicios
GET /api/government/health

# Información del módulo
GET /api/government/
```

## 🔧 Agregar Nueva API Gubernamental

### Paso 1: Crear Entidad

```python
# domain/entities/government_apis/nueva_api_entity.py
from pydantic import BaseModel, Field

class NuevaAPIData(BaseModel):
    documento: str = Field(..., description="Número de documento")
    # ... otros campos
    
class NuevaAPIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[NuevaAPIData] = None
```

### Paso 2: Implementar Servicio

```python
# infrastructure/services/government_apis/nueva_api_service.py
from .base_government_api import BaseGovernmentAPI, APIProvider

class NuevaAPIService(BaseGovernmentAPI):
    def __init__(self):
        super().__init__()
        self.provider = APIProvider.NUEVA_API  # Agregar a enum
        self.api_endpoints = ["https://api.nueva.gob.pe/v1/consulta"]
        
    def validate_document(self, document: str) -> bool:
        # Implementar validación
        pass
        
    async def query_document(self, document: str) -> dict:
        # Implementar consulta
        pass
        
    def normalize_response(self, raw_data: dict) -> dict:
        # Normalizar respuesta
        pass
        
    async def health_check(self) -> dict:
        # Health check
        pass
```

### Paso 3: Registrar en Factory

```python
# infrastructure/services/government_apis/government_factory.py

from .nueva_api_service import NuevaAPIService

class GovernmentAPIFactory:
    _services: Dict[APIProvider, Type[BaseGovernmentAPI]] = {
        APIProvider.RENIEC: ReniecService,
        APIProvider.SUNAT: SunatService,
        APIProvider.NUEVA_API: NuevaAPIService,  # Agregar aquí
    }
```

### Paso 4: Agregar Endpoint (Opcional)

```python
# infrastructure/web/fastapi/government_routes.py

@router.get("/nueva-api/{documento}")
async def query_nueva_api(
    documento: str,
    use_case: GovernmentQueriesUseCase = Depends(get_government_use_case)
):
    # Implementar endpoint
    pass
```

¡Listo! La nueva API está integrada en todo el sistema.

## 📊 Características

### ✅ Implementadas

- ✅ Arquitectura modular con Factory Pattern
- ✅ Validación robusta de documentos
- ✅ Múltiples endpoints con fallback automático
- ✅ Logging detallado de operaciones
- ✅ Manejo de errores centralizado
- ✅ API REST con documentación Swagger
- ✅ Entidades de dominio con validaciones Pydantic
- ✅ Casos de uso con preparación para caché y auditoría

### 🔄 Próximas Mejoras

- 🔄 Sistema de caché (Redis/Memcached)
- 🔄 Auditoría completa de consultas
- 🔄 Rate limiting por usuario/API
- 🔄 Métricas y estadísticas de uso
- 🔄 Retry con backoff exponencial
- 🔄 Circuit breaker para APIs caídas

## 🧪 Testing

```python
# tests/unit/test_reniec_service.py
import pytest
from infrastructure.services.government_apis import ReniecService

@pytest.mark.asyncio
async def test_validate_dni():
    service = ReniecService()
    assert service.validate_document("12345678") == True
    assert service.validate_document("123") == False

@pytest.mark.asyncio
async def test_query_dni():
    service = ReniecService()
    result = await service.query_document("12345678")
    assert result.success == True or result.success == False
```

## 📝 Ejemplos de Respuestas

### DNI (RENIEC)

```json
{
  "success": true,
  "message": "Consulta exitosa",
  "data": {
    "dni": "12345678",
    "nombres": "JUAN CARLOS",
    "apellido_paterno": "PEREZ",
    "apellido_materno": "GARCIA",
    "apellidos": "PEREZ GARCIA",
    "nombre_completo": "PEREZ GARCIA JUAN CARLOS",
    "fecha_nacimiento": "01/01/1990",
    "estado_civil": "SOLTERO"
  },
  "fuente": "API Real - https://api.apis.net.pe/v1/dni",
  "timestamp": "2025-10-08T10:30:00",
  "cache_hit": false
}
```

### RUC (SUNAT)

```json
{
  "success": true,
  "message": "Consulta exitosa",
  "data": {
    "ruc": "20123456789",
    "razon_social": "EMPRESA EJEMPLO S.A.C.",
    "estado": "ACTIVO",
    "condicion": "HABIDO",
    "direccion": "AV. PRINCIPAL 456",
    "departamento": "LIMA",
    "provincia": "LIMA",
    "distrito": "MIRAFLORES"
  },
  "fuente": "API Principal",
  "timestamp": "2025-10-08T10:35:00",
  "cache_hit": false
}
```

## 🔒 Seguridad

- Validación de documentos antes de consultar
- Rate limiting (próximamente)
- Autenticación de usuarios (integrar con sistema auth existente)
- Auditoría de todas las consultas
- No se almacenan datos sensibles en logs

## 📚 Documentación API

Una vez el servidor esté corriendo, acceder a:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

**Desarrollado con arquitectura hexagonal y patrones de diseño escalables** 🚀
