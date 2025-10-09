# 🚀 Guía Rápida - Usar APIs Gubernamentales

Guía rápida para desarrolladores que necesitan usar el módulo de APIs gubernamentales.

## 📖 ¿Qué puedes hacer?

- ✅ Consultar DNI en RENIEC
- ✅ Consultar RUC en SUNAT
- ✅ Validar documentos antes de consultar
- ✅ Obtener datos completos o resumidos
- ✅ Consultas con caché automático
- ✅ Auditoría de consultas

---

## 🎯 Uso Rápido (3 opciones)

### Opción 1: Helper Service (Recomendado) ⭐

```python
from infrastructure.services.government_helper import get_government_helper

# Obtener helper
helper = get_government_helper()

# Consultar DNI
persona = await helper.get_persona_by_dni("12345678")
if persona:
    print(f"Nombre: {persona.nombre_completo}")

# Consultar RUC
empresa = await helper.get_empresa_by_ruc("20123456789")
if empresa:
    print(f"Empresa: {empresa.razon_social}")
```

### Opción 2: Quick Functions

```python
from infrastructure.services.government_helper import quick_query_dni, quick_query_ruc

# Más rápido aún
persona = await quick_query_dni("12345678")
empresa = await quick_query_ruc("20123456789")
```

### Opción 3: API REST (desde Frontend)

```bash
# Con tu token de autenticación
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/government/dni/12345678

curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/government/ruc/20123456789
```

---

## 📚 Casos de Uso Comunes

### Validar Usuario al Registrar

```python
from infrastructure.services.government_helper import get_government_helper

async def registrar_usuario(dni: str, nombre: str):
    helper = get_government_helper()
    
    # Validar DNI en RENIEC
    persona = await helper.get_persona_by_dni(dni)
    
    if not persona:
        raise ValueError("DNI no encontrado en RENIEC")
    
    if persona.nombre_completo.lower() != nombre.lower():
        print("⚠️ El nombre no coincide con RENIEC")
    
    # Continuar con registro...
```

### Validar Empresa Activa

```python
async def validar_proveedor(ruc: str):
    helper = get_government_helper()
    
    empresa = await helper.get_empresa_by_ruc(ruc)
    
    if not empresa:
        return False, "RUC no encontrado"
    
    if empresa.estado != "ACTIVO":
        return False, f"Empresa {empresa.estado}"
    
    return True, empresa.razon_social
```

### Solo Validar Formato (sin consultar)

```python
from infrastructure.services.government_helper import GovernmentAPIHelper

# Validar sin hacer consulta HTTP
es_valido_dni = GovernmentAPIHelper.validate_dni("12345678")  # True/False
es_valido_ruc = GovernmentAPIHelper.validate_ruc("20123456789")  # True/False
```

### Consultar con Respuesta Completa

```python
helper = get_government_helper()

# Obtener respuesta completa (con metadatos)
response = await helper.query_dni_full("12345678", user_id="user123")

print(f"Success: {response.success}")
print(f"Message: {response.message}")
print(f"Fuente: {response.fuente}")
print(f"Cache: {response.cache_hit}")

if response.data:
    print(f"Nombre: {response.data.nombre_completo}")
```

---

## 🌐 Desde Frontend (React/Next.js)

### Setup Rápido

```typescript
// services/governmentApi.ts
import { getGovernmentApi } from '@/services/governmentApi';
import { useAuth } from '@clerk/nextjs';

export function useQueryDni() {
  const { getToken } = useAuth();
  
  const queryDni = async (dni: string) => {
    const token = await getToken();
    const api = getGovernmentApi(token);
    return await api.queryDni(dni);
  };
  
  return { queryDni };
}
```

### Componente React

```tsx
'use client';

import { useState } from 'react';
import { useQueryDni } from '@/hooks/useQueryDni';

export default function DniSearch() {
  const [dni, setDni] = useState('');
  const { queryDni, loading, data } = useQueryDni();

  const handleSearch = async () => {
    await queryDni(dni);
  };

  return (
    <div>
      <input value={dni} onChange={(e) => setDni(e.target.value)} />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? 'Buscando...' : 'Buscar'}
      </button>
      
      {data && <div>Nombre: {data.nombre_completo}</div>}
    </div>
  );
}
```

---

## 📖 Documentación Completa

- **Módulo General**: `docs/GOVERNMENT_APIS_MODULE.md`
- **Integración Frontend**: `docs/FRONTEND_INTEGRATION.md`
- **Ejemplos Python**: `examples/government_apis_usage.py`
- **API Swagger**: `http://localhost:8000/docs`

---

## 🔧 Autenticación

**Todos los endpoints requieren autenticación** con token JWT de Clerk.

```python
# En Python (automático con dependency injection)
from infrastructure.web.fastapi.auth_dependencies import get_current_user

# En Frontend
const token = await getToken(); // Clerk
headers: { 'Authorization': `Bearer ${token}` }
```

---

## 💡 Tips

1. **Usa caché**: Por defecto está activado, ahorra consultas
2. **Valida primero**: Usa `validate_dni()` antes de consultar
3. **Maneja errores**: Pueden fallar las APIs externas
4. **Batch queries**: Usa `query_multiple_*` para consultas masivas

---

## ⚡ Rendimiento

- **Caché automático**: 1 hora para DNI, 2 horas para RUC
- **Fallback**: Múltiples endpoints de respaldo
- **Timeout**: 8-10 segundos por consulta
- **Retry**: 3 intentos automáticos

---

## 🆘 Soporte

- **Ejemplos completos**: `examples/government_apis_usage.py`
- **Swagger UI**: `http://localhost:8000/docs`
- **Logs**: Busca `[RENIEC]` o `[SUNAT]` en logs

---

**¿Preguntas?** Revisa la documentación completa en `docs/` 📚
