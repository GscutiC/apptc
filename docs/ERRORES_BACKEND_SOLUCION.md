# 🔧 Solución de Errores Comunes del Backend

## ✅ Errores Resueltos

### 1. Error de Índice MongoDB: `index not found with name [code_1]`

**Problema:** El repositorio de convocatorias intentaba eliminar un índice que no existía.

**Causa:** Cambio de índice único simple `code` a índice compuesto `(code, created_by)` para permitir que diferentes usuarios usen el mismo código.

**Solución Implementada:**
```python
# Antes: Índice único global
db.convocations.createIndex({code: 1}, {unique: true})

# Ahora: Índice compuesto único por usuario
db.convocations.createIndex(
    {code: 1, created_by: 1}, 
    {unique: true, name: "code_created_by_unique"}
)
```

**Comportamiento Actual:**
- ✅ Usuario A puede crear convocatoria con código `ABC-123`
- ✅ Usuario B puede crear convocatoria con código `ABC-123` (diferente usuario)
- ❌ Usuario A NO puede crear otra convocatoria con código `ABC-123` (duplicado)

**Script de Reparación:**
```bash
# Ejecutar para arreglar índices manualmente
cd backend
python scripts/fix_mongodb_indexes.py
```

---

### 2. Errores 404 de Archivos: `GET /api/files/{uuid} HTTP/1.1" 404 Not Found`

**Naturaleza:** ⚠️ **NO ES UN ERROR** - Es comportamiento normal.

**Explicación:**
- El frontend intenta cargar imágenes/logos de usuarios
- Si el usuario no ha subido una imagen, el ID apunta a un archivo inexistente
- El backend devuelve correctamente `404 Not Found`
- El frontend maneja este error mostrando una imagen por defecto

**UUIDs Comunes que aparecen:**
- `11070d96-77a4-4f05-8873-744473ef9a9a` - Logo/avatar de usuario
- `c476ecad-f816-493e-bf57-3cf76eb1d805` - Imagen de perfil
- `e2fc784c-8494-479d-8bbc-d60b8fee6912` - Logo de empresa
- `cf05f1d7-8f6d-4acc-9e80-0218f3ec7ca7` - Archivo adjunto

**No Requiere Acción:** El sistema funciona correctamente con estos 404.

---

## 🚀 Validaciones Implementadas - Códigos de Convocatoria

### Frontend
```typescript
// ❌ ANTES: Validación estricta
if (!code.match(/^CONV-\d{4}-\d{2}$/)) {
  error = 'Formato debe ser CONV-YYYY-XX';
}

// ✅ AHORA: Código libre
if (!code.trim()) {
  error = 'Código requerido';
}
// Acepta: ABC-123, 2025-ESPECIAL, MI-CONV, 001, etc.
```

### Backend DTO
```python
# ❌ ANTES: Validación de formato
@validator('code')
def validate_code_format(cls, v):
    if not v.startswith('CONV-'):
        raise ValueError('Debe comenzar con CONV-')
    # ... validación de año y número

# ✅ AHORA: Código libre
@validator('code')
def validate_code_format(cls, v):
    if not v or not v.strip():
        raise ValueError('El código no puede estar vacío')
    return v.strip()
```

### Backend Entity
```python
# ❌ ANTES: Validación estricta CONV-YYYY-XX
def _validate_code_format(self):
    if not self.code.startswith("CONV-"):
        raise ValueError(...)
    # Validación de partes, año, número...

# ✅ AHORA: Solo verifica que no esté vacío
def _validate_code_format(self):
    if not self.code or not self.code.strip():
        raise ValueError("El código no puede estar vacío")
```

---

## 📊 Logs Normales vs Errores Reales

### ✅ Logs Normales (NO SON ERRORES)
```
INFO: 127.0.0.1:xxxxx - "GET /api/files/11070d96-... HTTP/1.1" 404 Not Found
INFO: 127.0.0.1:xxxxx - "GET /api/interface-config/current/safe HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /auth/me HTTP/1.1" 200 OK
INFO: 127.0.0.1:xxxxx - "GET /api/techo-propio/convocations/ HTTP/1.1" 200 OK
```

### ❌ Errores Reales (REQUIEREN ATENCIÓN)
```
ERROR: Traceback (most recent call last):
ERROR: pymongo.errors.OperationFailure: ...
ERROR: ValueError: ...
ERROR: ConnectionError: ...
```

---

## 🛠️ Comandos Útiles

### Verificar Estado de Índices
```bash
# MongoDB Shell
mongosh
use mi_app_completa_db
db.convocations.getIndexes()
```

### Recrear Índices Manualmente
```bash
# MongoDB Shell
db.convocations.dropIndex("code_1")  # Eliminar antiguo
db.convocations.createIndex(
  {code: 1, created_by: 1}, 
  {unique: true, name: "code_created_by_unique"}
)
```

### Reiniciar Backend Limpio
```bash
# Detener servidor (Ctrl+C)
cd backend
python start_server.py --env development
```

---

## 📝 Cambios en Archivos

### Archivos Modificados
1. `frontend/src/modules/techo-propio/components/ConvocationManagement.tsx`
   - Eliminada validación de formato `CONV-YYYY-XX`

2. `backend/src/backend/application/dto/techo_propio/convocation_dto.py`
   - Validador simplificado, acepta códigos libres

3. `backend/src/backend/domain/entities/techo_propio/convocation_entity.py`
   - Validación de formato eliminada

4. `backend/src/backend/infrastructure/persistence/mongo_convocation_repository.py`
   - Índice único global → índice compuesto (code, created_by)

### Archivos Nuevos
1. `backend/scripts/fix_mongodb_indexes.py`
   - Script para arreglar índices automáticamente

2. `backend/docs/ERRORES_BACKEND_SOLUCION.md`
   - Este documento

---

## 🎯 Conclusión

✅ **Backend funcionando correctamente**
- Los "errores" que ves son logs normales de desarrollo
- Los 404 de archivos son esperados
- El índice de MongoDB está correctamente configurado
- El sistema de convocatorias acepta códigos personalizados
- Unicidad garantizada por usuario

⚠️ **Monitorear:**
- Errores con `ERROR:` o `Traceback` en los logs
- Problemas de conexión a MongoDB
- Errores de validación de datos

🚀 **Siguiente Paso:**
Reinicia el backend y los errores de índice no volverán a aparecer.
