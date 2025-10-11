# 📘 Guía de Uso - Configuración de Zona Horaria

## 🎯 Visión General

Este documento describe cómo usar correctamente el sistema de zona horaria implementado en AppTc Backend. Todas las operaciones de fecha/hora deben usar las funciones del módulo `timezone_config.py` para garantizar consistencia y precisión.

**Zona Horaria del Sistema**: `America/Lima` (Perú, UTC-5)

---

## ⚠️ Reglas de Oro

### 1. **SIEMPRE usar funciones de `timezone_config.py`**
```python
# ❌ MAL - NUNCA hacer esto
from datetime import datetime
now = datetime.now()  # Timezone-naive, INCORRECTO

# ✅ BIEN - Usar funciones helper
from infrastructure.config.timezone_config import lima_now
now = lima_now()  # Timezone-aware, CORRECTO
```

### 2. **Almacenar en UTC, Mostrar en Lima**
```python
# ✅ BIEN - Para almacenar en base de datos
from infrastructure.config.timezone_config import utc_now
created_at = utc_now()  # Guardar en UTC

# ✅ BIEN - Para mostrar al usuario
from infrastructure.config.timezone_config import to_lima_time
display_time = to_lima_time(created_at)  # Convertir a Lima
```

### 3. **NUNCA mezclar naive y aware datetimes**
```python
# ❌ MAL - Causa errores
naive = datetime.now()
aware = lima_now()
diff = aware - naive  # TypeError!

# ✅ BIEN - Todo timezone-aware
time1 = lima_now()
time2 = utc_now()
diff = time2 - time1  # Funciona correctamente
```

---

## 📚 Guía de Funciones

### **Obtener Tiempo Actual**

#### `lima_now()` - Tiempo actual en Lima
**Uso Principal**: Lógica de negocio, validaciones, timestamps locales

```python
from infrastructure.config.timezone_config import lima_now

# Obtener tiempo actual en Lima
current_time = lima_now()
print(current_time)  # 2025-10-11 15:30:00-05:00

# Casos de uso:
# - Fecha límite de convocatorias
# - Validación de DNI con fecha actual
# - Logs para usuarios peruanos
# - Cualquier lógica que requiera hora local
```

#### `utc_now()` - Tiempo actual en UTC
**Uso Principal**: Almacenamiento en base de datos

```python
from infrastructure.config.timezone_config import utc_now

# Obtener tiempo actual en UTC
timestamp = utc_now()
print(timestamp)  # 2025-10-11 20:30:00+00:00

# Casos de uso:
# - created_at en MongoDB
# - updated_at en documentos
# - Timestamps de auditoría
# - Sincronización con APIs externas
```

---

### **Conversión Entre Zonas Horarias**

#### `to_lima_time(dt)` - Convertir a Lima
**Uso Principal**: Preparar fechas para mostrar al usuario

```python
from infrastructure.config.timezone_config import to_lima_time

# Convertir desde UTC (común al leer de MongoDB)
utc_datetime = document['created_at']  # Viene de MongoDB
lima_datetime = to_lima_time(utc_datetime)

# Convertir datetime naive (asume UTC)
naive_dt = datetime(2025, 10, 11, 20, 30)
lima_dt = to_lima_time(naive_dt)  # Asume que naive está en UTC

# Casos de uso:
# - Mostrar fechas en respuestas de API
# - Formatear fechas para frontend
# - Reportes para usuarios peruanos
```

#### `to_utc_time(dt)` - Convertir a UTC
**Uso Principal**: Preparar fechas para almacenar

```python
from infrastructure.config.timezone_config import to_utc_time

# Convertir desde Lima (común al recibir input de usuario)
user_input = "2025-10-11 15:30:00"  # Usuario en Perú
lima_dt = parse_lima_datetime(user_input)
utc_dt = to_utc_time(lima_dt)  # Listo para MongoDB

# Convertir datetime naive (asume Lima)
naive_dt = datetime(2025, 10, 11, 15, 30)
utc_dt = to_utc_time(naive_dt)  # Asume que naive está en Lima

# Casos de uso:
# - Guardar input de usuario en MongoDB
# - Preparar fechas para servicios externos
# - Normalizar fechas para comparaciones
```

---

### **Formateo y Parseo de Strings**

#### `format_lima_datetime(dt, format_str)` - Datetime → String
**Uso Principal**: Generar strings legibles para humanos

```python
from infrastructure.config.timezone_config import (
    format_lima_datetime, 
    FORMAT_DATETIME_ES,
    FORMAT_FILENAME
)

# Formato por defecto (ISO-like)
formatted = format_lima_datetime(utc_dt)
print(formatted)  # "2025-10-11 15:30:00"

# Formato español para UI
formatted_es = format_lima_datetime(utc_dt, FORMAT_DATETIME_ES)
print(formatted_es)  # "11/10/2025 15:30"

# Formato para nombres de archivo
filename = f"reporte_{format_lima_datetime(utc_dt, FORMAT_FILENAME)}.pdf"
print(filename)  # "reporte_20251011_153000.pdf"

# Casos de uso:
# - Respuestas de API legibles
# - Logs para humanos
# - Nombres de archivo con timestamp
# - Exportar datos
```

#### `parse_lima_datetime(date_str, format_str)` - String → Datetime
**Uso Principal**: Procesar input de usuario

```python
from infrastructure.config.timezone_config import (
    parse_lima_datetime,
    FORMAT_DATETIME_ES
)

# Parsear formato estándar
user_input = "2025-10-11 15:30:00"
dt = parse_lima_datetime(user_input)

# Parsear formato español
user_input_es = "11/10/2025 15:30"
dt_es = parse_lima_datetime(user_input_es, FORMAT_DATETIME_ES)

# Casos de uso:
# - Procesar formularios de frontend
# - Leer fechas de archivos CSV/JSON
# - Parsear configuración
```

---

### **Funciones Utilitarias**

#### `get_lima_date_range(start, end)` - Rango de fechas
**Uso Principal**: Filtros de consultas

```python
from infrastructure.config.timezone_config import get_lima_date_range

# Obtener rango en Lima (útil para filtros)
start_utc = document['start_date']
end_utc = document['end_date']
start_lima, end_lima = get_lima_date_range(start_utc, end_utc)

# Casos de uso:
# - Filtros de convocatorias por fecha
# - Reportes mensuales/anuales
# - Consultas de auditoría
```

#### `is_timezone_aware(dt)` - Verificar si es aware
**Uso Principal**: Validaciones y debugging

```python
from infrastructure.config.timezone_config import is_timezone_aware

# Verificar antes de operaciones
if not is_timezone_aware(some_datetime):
    raise ValueError("Datetime debe ser timezone-aware")

# Casos de uso:
# - Validaciones defensivas
# - Tests unitarios
# - Debugging
```

#### `ensure_timezone_aware(dt, assume_tz)` - Asegurar aware
**Uso Principal**: Procesar datos de fuentes externas

```python
from infrastructure.config.timezone_config import ensure_timezone_aware

# Asegurar que sea aware (asume UTC por defecto)
safe_dt = ensure_timezone_aware(external_datetime)

# Asegurar aware asumiendo Lima
safe_dt_lima = ensure_timezone_aware(user_datetime, "Lima")

# Casos de uso:
# - Migración de código legacy
# - Procesar datos externos
# - Defensive programming
```

---

## 🎯 Casos de Uso Comunes

### **Caso 1: Crear Convocatoria con Fecha Límite**

```python
from infrastructure.config.timezone_config import parse_lima_datetime, utc_now

# 1. Usuario ingresa fecha límite (en hora de Lima)
deadline_input = "2025-12-31 23:59:59"
deadline_lima = parse_lima_datetime(deadline_input)

# 2. Crear convocatoria con timestamps
convocation = Convocation(
    title="Nueva Convocatoria",
    deadline=deadline_lima,  # Se puede guardar en Lima
    created_at=utc_now(),    # Mejor práctica: guardar en UTC
    updated_at=utc_now()
)

# 3. Guardar en MongoDB (convierte automáticamente a UTC)
await repository.create(convocation)
```

### **Caso 2: Verificar si Convocatoria está Vigente**

```python
from infrastructure.config.timezone_config import lima_now, to_lima_time

# 1. Obtener convocatoria de MongoDB
convocation = await repository.get_by_id(convocation_id)

# 2. Convertir deadline a Lima para comparación
deadline_lima = to_lima_time(convocation.deadline)

# 3. Comparar con tiempo actual en Lima
current_time = lima_now()
is_active = current_time <= deadline_lima

if is_active:
    print("Convocatoria vigente")
else:
    print("Convocatoria cerrada")
```

### **Caso 3: Respuesta de API con Fecha Formateada**

```python
from infrastructure.config.timezone_config import (
    to_lima_time, 
    format_lima_datetime,
    FORMAT_DATETIME_ES
)

# 1. Obtener datos de MongoDB
convocation = await repository.get_by_id(convocation_id)

# 2. Preparar respuesta con fechas en Lima
response = {
    "id": convocation.id,
    "title": convocation.title,
    "deadline": to_lima_time(convocation.deadline).isoformat(),  # ISO para JS
    "deadline_formatted": format_lima_datetime(
        convocation.deadline, 
        FORMAT_DATETIME_ES
    ),  # Legible para humanos
    "created_at": to_lima_time(convocation.created_at).isoformat()
}

return response
```

### **Caso 4: Filtrar Convocatorias por Mes**

```python
from infrastructure.config.timezone_config import parse_lima_datetime, to_utc_time

# 1. Usuario selecciona mes (Octubre 2025)
start_str = "2025-10-01 00:00:00"
end_str = "2025-10-31 23:59:59"

# 2. Parsear en Lima
start_lima = parse_lima_datetime(start_str)
end_lima = parse_lima_datetime(end_str)

# 3. Convertir a UTC para consultar MongoDB
start_utc = to_utc_time(start_lima)
end_utc = to_utc_time(end_lima)

# 4. Consultar
convocations = await repository.find_by_date_range(start_utc, end_utc)
```

### **Caso 5: Auditoría con Timestamp Preciso**

```python
from infrastructure.config.timezone_config import utc_now, format_lima_datetime

# 1. Registrar evento en auditoría (guardar en UTC)
audit_log = AuditLog(
    user_id=user.id,
    action="UPDATE_CONVOCATION",
    timestamp=utc_now(),  # UTC para almacenamiento
    details=changes
)

# 2. Mostrar en log para admin (mostrar en Lima)
log_message = (
    f"[{format_lima_datetime(audit_log.timestamp)}] "
    f"Usuario {user.name} actualizó convocatoria"
)
logger.info(log_message)
```

---

## 🏗️ Patrones de Migración

### **Patrón 1: Repositorio MongoDB**

#### ANTES (Timezone-naive)
```python
from datetime import datetime

class ConvocationRepository:
    async def create(self, convocation):
        doc = {
            "title": convocation.title,
            "created_at": datetime.utcnow(),  # ❌ Naive
            "updated_at": datetime.utcnow()   # ❌ Naive
        }
        await self.collection.insert_one(doc)
```

#### DESPUÉS (Timezone-aware)
```python
from infrastructure.config.timezone_config import utc_now

class ConvocationRepository:
    async def create(self, convocation):
        doc = {
            "title": convocation.title,
            "created_at": utc_now(),  # ✅ Aware (UTC)
            "updated_at": utc_now()   # ✅ Aware (UTC)
        }
        await self.collection.insert_one(doc)
```

---

### **Patrón 2: Use Case con Lógica de Negocio**

#### ANTES (Timezone-naive)
```python
from datetime import datetime

class ValidateDNIUseCase:
    async def execute(self, dni: str):
        validation = DNIValidation(
            dni=dni,
            validation_date=datetime.now(),  # ❌ Naive
            is_valid=True
        )
        return validation
```

#### DESPUÉS (Timezone-aware)
```python
from infrastructure.config.timezone_config import lima_now

class ValidateDNIUseCase:
    async def execute(self, dni: str):
        validation = DNIValidation(
            dni=dni,
            validation_date=lima_now(),  # ✅ Aware (Lima)
            is_valid=True
        )
        return validation
```

---

### **Patrón 3: Comparación de Fechas**

#### ANTES (Timezone-naive)
```python
from datetime import datetime

# ❌ Puede fallar si convocation.end_date es aware
if datetime.now() > convocation.end_date:
    print("Convocatoria cerrada")
```

#### DESPUÉS (Timezone-aware)
```python
from infrastructure.config.timezone_config import lima_now, to_lima_time

# ✅ Correcto - ambos son aware
current_time = lima_now()
end_time = to_lima_time(convocation.end_date)

if current_time > end_time:
    print("Convocatoria cerrada")
```

---

## 🔧 Constantes de Formato Disponibles

```python
from infrastructure.config.timezone_config import (
    FORMAT_ISO,          # "%Y-%m-%dT%H:%M:%S" -> "2025-10-11T15:30:00"
    FORMAT_DATE,         # "%Y-%m-%d" -> "2025-10-11"
    FORMAT_TIME,         # "%H:%M:%S" -> "15:30:00"
    FORMAT_DATETIME,     # "%Y-%m-%d %H:%M:%S" -> "2025-10-11 15:30:00"
    FORMAT_DATE_ES,      # "%d/%m/%Y" -> "11/10/2025"
    FORMAT_DATETIME_ES,  # "%d/%m/%Y %H:%M" -> "11/10/2025 15:30"
    FORMAT_FILENAME,     # "%Y%m%d_%H%M%S" -> "20251011_153000"
)
```

---

## ❌ Errores Comunes y Soluciones

### Error 1: TypeError al comparar datetimes
```python
# ❌ Error
naive = datetime.now()
aware = lima_now()
diff = aware - naive  # TypeError: can't subtract offset-naive and offset-aware

# ✅ Solución
time1 = lima_now()
time2 = utc_now()
diff = time2 - time1  # Funciona
```

### Error 2: Fechas incorrectas en frontend
```python
# ❌ Problema: Enviar UTC sin indicar timezone
response = {"deadline": document['deadline'].isoformat()}
# Frontend lo interpreta como hora local

# ✅ Solución: Convertir a Lima y enviar con timezone
from infrastructure.config.timezone_config import to_lima_time
lima_deadline = to_lima_time(document['deadline'])
response = {"deadline": lima_deadline.isoformat()}  # Incluye -05:00
```

### Error 3: Usar datetime.now() directamente
```python
# ❌ MAL
from datetime import datetime
now = datetime.now()  # Naive, depende del sistema

# ✅ BIEN
from infrastructure.config.timezone_config import lima_now
now = lima_now()  # Aware, siempre Lima
```

---

## 📊 Checklist de Integración

Al trabajar con fechas en tu código, verifica:

- [ ] **Importé** funciones de `timezone_config.py`
- [ ] **No uso** `datetime.now()` o `datetime.utcnow()` directamente
- [ ] **Almaceno** en UTC con `utc_now()`
- [ ] **Muestro** en Lima con `to_lima_time()` o `format_lima_datetime()`
- [ ] **Parseo** input de usuario con `parse_lima_datetime()`
- [ ] **Comparo** solo datetimes timezone-aware
- [ ] **Verifico** con `is_timezone_aware()` en validaciones
- [ ] **Testé** con datos de diferentes timezones

---

## 🧪 Testing con Timezone

```python
import pytest
from infrastructure.config.timezone_config import lima_now, utc_now, to_lima_time

def test_convocation_deadline():
    # Crear datetime conocido para test
    deadline = parse_lima_datetime("2025-12-31 23:59:59")
    
    # Verificar que es timezone-aware
    assert deadline.tzinfo is not None
    
    # Verificar conversión
    deadline_utc = to_utc_time(deadline)
    assert deadline_utc.hour == 4  # 23:59 Lima + 5 = 04:59 UTC (día siguiente)
```

---

## 📞 Soporte

**¿Dudas sobre timezone?**
- Revisar ejemplos en: `tests/unit/test_timezone_config.py`
- Consultar plan completo: `docs/PLAN_TIMEZONE_CONFIGURATION.md`
- Revisar implementación: `src/mi_app_completa_backend/infrastructure/config/timezone_config.py`

**Reportar problemas:**
- Crear issue con tag `timezone`
- Incluir código problemático y error

---

**Última Actualización**: 2025-10-11  
**Versión**: 1.0  
**Autor**: Sistema Backend AppTc
