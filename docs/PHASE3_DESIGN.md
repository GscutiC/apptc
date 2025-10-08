# FASE 3: Diseño de Sistema de Configuración Contextual

## Objetivo
Permitir configuraciones personalizadas por contexto (usuario, rol, organización) con sistema de herencia y prioridades.

## Arquitectura de Contextos

### Jerarquía de Prioridad (mayor a menor):
```
1. Usuario específico (user_id)
2. Rol (role_id)
3. Organización (org_id)
4. Global (default)
```

### Ejemplo de Flujo:
```
Usuario "john@example.com" con rol "editor" en org "CompanyA"

Resolución de configuración:
1. ¿Existe config para user "john@example.com"? → SÍ: usar esa
   NO: continuar
2. ¿Existe config para role "editor"? → SÍ: usar esa
   NO: continuar
3. ¿Existe config para org "CompanyA"? → SÍ: usar esa
   NO: continuar
4. Usar configuración global
```

## Modelo de Datos

### ConfigContext (Value Object)
```python
class ConfigContext:
    """Contexto de aplicación de configuración"""
    context_type: str  # "user" | "role" | "org" | "global"
    context_id: Optional[str]  # user_id, role_id, org_id, o None para global
    priority: int  # 1=usuario, 2=rol, 3=org, 4=global
```

### ContextualConfig (Entity)
```python
class ContextualConfig:
    """Configuración con contexto"""
    id: str
    config: InterfaceConfig  # La configuración en sí
    context: ConfigContext  # A quién aplica
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
```

## Colecciones MongoDB

### contextual_configurations
```json
{
  "_id": ObjectId,
  "contextType": "user" | "role" | "org" | "global",
  "contextId": "user_123" | "role_editor" | "org_abc" | null,
  "priority": 1-4,
  "config": {
    // InterfaceConfig completo
  },
  "isActive": true,
  "createdAt": ISODate,
  "updatedAt": ISODate,
  "createdBy": "user_id"
}
```

**Índices:**
- `{ "contextType": 1, "contextId": 1, "isActive": 1 }`
- `{ "priority": 1, "isActive": 1 }`

## Casos de Uso

### 1. Obtener Configuración Contextual
```python
async def get_config_for_user(
    user_id: str,
    role_id: Optional[str] = None,
    org_id: Optional[str] = None
) -> InterfaceConfig:
    """
    Obtener configuración aplicando jerarquía de prioridades
    """
    # 1. Buscar config de usuario
    user_config = await repo.get_by_context("user", user_id)
    if user_config and user_config.is_active:
        return user_config.config

    # 2. Buscar config de rol
    if role_id:
        role_config = await repo.get_by_context("role", role_id)
        if role_config and role_config.is_active:
            return role_config.config

    # 3. Buscar config de org
    if org_id:
        org_config = await repo.get_by_context("org", org_id)
        if org_config and org_config.is_active:
            return org_config.config

    # 4. Fallback a global
    return await repo.get_global_config()
```

### 2. Guardar Configuración Contextual
```python
async def save_contextual_config(
    config: InterfaceConfig,
    context_type: str,
    context_id: Optional[str],
    user: User
) -> ContextualConfig:
    """
    Guardar configuración con contexto específico
    """
    # Validar permisos según contexto
    validate_permissions(user, context_type, context_id)

    # Crear configuración contextual
    contextual = ContextualConfig(
        config=config,
        context=ConfigContext(
            context_type=context_type,
            context_id=context_id,
            priority=get_priority(context_type)
        ),
        created_by=user.id
    )

    return await repo.save(contextual)
```

### 3. Override Parcial
```python
async def apply_partial_override(
    base_config: InterfaceConfig,
    override_config: Dict[str, Any]
) -> InterfaceConfig:
    """
    Aplicar override parcial sobre configuración base

    Ejemplo:
    - Base: tema azul, logo A, branding X
    - Override: solo tema verde
    - Resultado: tema verde, logo A, branding X
    """
    merged = deep_merge(base_config, override_config)
    return merged
```

## APIs Actualizadas

### GET /api/interface-config/current
**Antes:**
```python
async def get_current_config(user: User):
    return await config_repo.get_current_config()
```

**Después (contextual):**
```python
async def get_current_config(user: User):
    return await contextual_service.get_config_for_user(
        user_id=user.id,
        role_id=user.role_id,
        org_id=user.org_id
    )
```

### POST /api/interface-config/contextual
**Nuevo endpoint:**
```python
async def save_contextual_config(
    config: InterfaceConfigDTO,
    context_type: str,  # query param
    context_id: Optional[str],  # query param
    user: User
):
    """
    Guardar config para contexto específico

    Ejemplos:
    - POST ?context_type=user&context_id=user_123
    - POST ?context_type=role&context_id=role_editor
    - POST ?context_type=org&context_id=org_abc
    - POST ?context_type=global (sin context_id)
    """
    return await contextual_service.save_contextual_config(
        config, context_type, context_id, user
    )
```

### GET /api/interface-config/contexts/{context_type}/{context_id}
**Nuevo endpoint:**
```python
async def get_config_by_context(
    context_type: str,
    context_id: str,
    user: User
):
    """
    Obtener config específica de un contexto (sin resolver herencia)
    """
    validate_read_permission(user, context_type, context_id)
    return await repo.get_by_context(context_type, context_id)
```

## Sistema de Permisos

### Reglas:
1. **Usuario puede:**
   - Ver/editar su propia configuración de usuario
   - Ver configuración de su rol (solo lectura)
   - Ver configuración de su org (solo lectura)

2. **Admin puede:**
   - Ver/editar configuraciones de cualquier usuario
   - Ver/editar configuraciones de roles
   - Ver/editar configuraciones de organizaciones
   - Ver/editar configuración global

3. **Super Admin puede:**
   - Todo lo anterior
   - Eliminar configuraciones contextuales
   - Resetear a defaults

## Caché Contextual

### Estrategia:
```python
# Keys de caché
cache_key = f"config:context:{context_type}:{context_id}"

# Ejemplo:
"config:context:user:user_123"
"config:context:role:role_editor"
"config:context:org:org_abc"
"config:context:global:default"
```

### Invalidación:
- Invalidar solo el contexto modificado
- Invalidar "resolved config" del usuario afectado
- TTL: 5 minutos (igual que configuración global)

## Migración de Datos Existentes

### Script de migración:
```python
async def migrate_to_contextual():
    """
    Migrar configuraciones actuales a sistema contextual
    """
    # 1. Obtener config global actual
    current_config = await old_repo.get_current_config()

    # 2. Crear configuración global contextual
    global_context = ContextualConfig(
        config=current_config,
        context=ConfigContext(
            context_type="global",
            context_id=None,
            priority=4
        ),
        created_by="migration_script"
    )

    await contextual_repo.save(global_context)

    # 3. Los presets se mantienen igual (son plantillas, no contextos)
```

## Ejemplo de Uso Completo

### Escenario:
- **Global**: Tema azul corporativo
- **Org "CompanyA"**: Override con logo personalizado
- **Role "editor"**: Override con colores naranja
- **User "john"**: Sin override personal

### Resolución para John:
```python
user_config = get_config_for_user(
    user_id="john",
    role_id="editor",
    org_id="CompanyA"
)

# Resultado: Colores naranja (del rol) + Logo CompanyA (de org) + resto de global
```

### Resolución para Mary (role: viewer, org: CompanyA):
```python
user_config = get_config_for_user(
    user_id="mary",
    role_id="viewer",
    org_id="CompanyA"
)

# Resultado: Logo CompanyA (de org) + resto de global (viewer no tiene override)
```

## Ventajas del Diseño

1. ✅ **Flexible**: Permite personalización a múltiples niveles
2. ✅ **Performante**: Caché por contexto
3. ✅ **Escalable**: Soporta multi-tenancy fácilmente
4. ✅ **Predecible**: Jerarquía clara de prioridades
5. ✅ **Mantenible**: Separación de concerns
6. ✅ **Backwards compatible**: No rompe funcionalidad existente

## Próximos Pasos

1. Implementar entidades y value objects
2. Crear repositorio contextual
3. Implementar service layer
4. Actualizar APIs
5. Migrar datos existentes
6. Actualizar frontend para soportar contextos
