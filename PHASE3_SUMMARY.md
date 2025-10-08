# FASE 3: Sistema de Configuración Contextual - Resumen

## Estado: 🟡 EN PROGRESO (40% completado)

## ✅ Completado

### 3.1 Diseño del Sistema
**Documento:** `backend/docs/PHASE3_DESIGN.md`

**Características diseñadas:**
- ✅ Jerarquía de prioridades (User > Role > Org > Global)
- ✅ Sistema de resolución de configuración
- ✅ Modelo de datos contextual
- ✅ APIs contextuales
- ✅ Sistema de permisos
- ✅ Estrategia de caché contextual
- ✅ Plan de migración

### 3.2 Entidades y Value Objects
**Archivos creados:**

#### `domain/value_objects/config_context.py`
```python
@dataclass(frozen=True)
class ConfigContext:
    context_type: ContextType  # "user" | "role" | "org" | "global"
    context_id: Optional[str]   # ID del contexto
    priority: int               # 1-4 (calculado automáticamente)
```

**Métodos principales:**
- `create_global()` - Crear contexto global
- `create_user(user_id)` - Crear contexto de usuario
- `create_role(role_id)` - Crear contexto de rol
- `create_org(org_id)` - Crear contexto de organización
- `matches(user_id, role_id, org_id)` - Verificar aplicabilidad
- `to_dict()` / `from_dict()` - Serialización

#### `domain/entities/contextual_config.py`
```python
class ContextualConfig(BaseEntity):
    config: InterfaceConfig  # Configuración de interfaz
    context: ConfigContext   # Contexto de aplicación
    is_active: bool         # Estado activo/inactivo
    created_by: str         # Auditoría
```

**Métodos principales:**
- `activate()` / `deactivate()` - Control de estado
- `update_config(new_config)` - Actualizar configuración
- `applies_to(user_id, role_id, org_id)` - Verificar aplicabilidad
- `to_dict()` - Serialización

**Características:**
- ✅ Inmutabilidad del contexto (frozen dataclass)
- ✅ Validación automática de consistencia
- ✅ Comparación por prioridad (sorting)
- ✅ Auditoría integrada

## 🔄 En Progreso

### 3.3 Repositorios Contextuales
**Pendiente crear:**
- `ContextualConfigRepository` (interface)
- `MongoContextualConfigRepository` (implementación)

**Métodos requeridos:**
```python
class ContextualConfigRepository:
    async def get_by_context(context_type, context_id) -> ContextualConfig
    async def get_for_user(user_id, role_id, org_id) -> InterfaceConfig
    async def save(contextual_config) -> ContextualConfig
    async def delete(config_id) -> bool
    async def list_by_type(context_type) -> List[ContextualConfig]
```

## ⏳ Pendiente

### 3.4 Use Cases Contextuales
- [ ] `GetContextualConfigUseCase` - Obtener config con resolución de contexto
- [ ] `SaveContextualConfigUseCase` - Guardar config contextual
- [ ] `DeleteContextualConfigUseCase` - Eliminar config contextual
- [ ] `ListContextualConfigsUseCase` - Listar configs por contexto

### 3.5 APIs Contextuales
**Endpoints a crear:**
- [ ] `GET /api/interface-config/contextual/current` - Config del usuario actual
- [ ] `GET /api/interface-config/contextual/{type}/{id}` - Config específica
- [ ] `POST /api/interface-config/contextual` - Crear config contextual
- [ ] `PUT /api/interface-config/contextual/{id}` - Actualizar config contextual
- [ ] `DELETE /api/interface-config/contextual/{id}` - Eliminar config contextual

### 3.6 Migración de Datos
- [ ] Script para migrar config global actual a sistema contextual
- [ ] Mantener backwards compatibility con endpoints existentes

### 3.7 Frontend
- [ ] UI para seleccionar contexto (admin panel)
- [ ] Selector de contexto en configuración
- [ ] Indicador visual de configuración heredada

## 📊 Ejemplos de Uso

### Ejemplo 1: Usuario sin override personal
```python
# Usuario: john, Role: editor, Org: CompanyA
config = await contextual_service.get_config_for_user(
    user_id="john",
    role_id="editor",
    org_id="CompanyA"
)
# Resultado: Config de rol "editor" (si existe)
#            o Config de org "CompanyA" (si existe)
#            o Config global
```

### Ejemplo 2: Usuario con override personal
```python
# Usuario: mary (con config personal), Role: viewer, Org: CompanyB
config = await contextual_service.get_config_for_user(
    user_id="mary",
    role_id="viewer",
    org_id="CompanyB"
)
# Resultado: Config personal de "mary" (ignora role y org)
```

### Ejemplo 3: Guardar config de rol
```python
# Admin guarda configuración para rol "editor"
contextual_config = ContextualConfig(
    config=custom_interface_config,
    context=ConfigContext.create_role("editor"),
    created_by="admin_user_id"
)
await contextual_repo.save(contextual_config)
```

## 🗄️ Modelo de Datos MongoDB

### Colección: `contextual_configurations`
```json
{
  "_id": ObjectId("..."),
  "contextType": "role",
  "contextId": "editor",
  "priority": 2,
  "config": {
    "theme": { ... },
    "logos": { ... },
    "branding": { ... },
    ...
  },
  "isActive": true,
  "createdBy": "admin_123",
  "createdAt": "2025-10-07T10:00:00Z",
  "updatedAt": "2025-10-07T10:00:00Z"
}
```

**Índices:**
```javascript
db.contextual_configurations.createIndex({ "contextType": 1, "contextId": 1, "isActive": 1 })
db.contextual_configurations.createIndex({ "priority": 1, "isActive": 1 })
db.contextual_configurations.createIndex({ "createdBy": 1 })
```

## 🎯 Casos de Uso Reales

### Caso 1: Multi-tenancy SaaS
```
Org "CompanyA": Logo y colores corporativos
Org "CompanyB": Logo y colores diferentes
Global: Diseño base
```

### Caso 2: Roles con UI específica
```
Role "admin": UI con todas las herramientas visibles
Role "viewer": UI simplificada, opciones limitadas
Role "editor": UI intermedia
Global: UI estándar
```

### Caso 3: Usuarios VIP
```
User "ceo": Tema personalizado dorado
User "cto": Tema tech oscuro
Role "executive": Tema premium
Global: Tema estándar
```

## 🔐 Sistema de Permisos

### Matriz de permisos:
| Acción | Usuario | Admin | Super Admin |
|--------|---------|-------|-------------|
| Ver config propia (user) | ✅ | ✅ | ✅ |
| Editar config propia | ✅ | ✅ | ✅ |
| Ver config de rol | 🔍 | ✅ | ✅ |
| Editar config de rol | ❌ | ✅ | ✅ |
| Ver config de org | 🔍 | ✅ | ✅ |
| Editar config de org | ❌ | ❌ | ✅ |
| Ver config global | 🔍 | ✅ | ✅ |
| Editar config global | ❌ | ❌ | ✅ |
| Eliminar configs | ❌ | ⚠️ | ✅ |

🔍 = Solo lectura / ⚠️ = Solo no-sistema

## 🚀 Próximos Pasos

1. **Inmediato:**
   - Crear repositorio contextual con MongoDB
   - Implementar casos de uso básicos
   - Crear endpoints API

2. **Corto plazo:**
   - Script de migración
   - Tests unitarios e integración
   - Documentación de API

3. **Mediano plazo:**
   - Frontend para gestión contextual
   - UI para preview de configuraciones
   - Analytics de uso por contexto

---

*Documento actualizado: 2025-10-07*
