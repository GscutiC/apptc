# 🕐 Plan de Configuración de Zona Horaria - Perú (Lima)

## 📋 Resumen Ejecutivo

**Objetivo**: Implementar una configuración de zona horaria unificada para Perú (America/Lima, UTC-5) en todo el sistema backend para garantizar fechas y horas precisas en todas las operaciones.

**Estado Actual**: ❌ Timezone-naive (sin conciencia de zona horaria)
- Se utiliza `datetime.now()` y `datetime.utcnow()` sin zona horaria
- No hay librería de timezone configurada (pytz o zoneinfo)
- **50+ ocurrencias** de datetime sin timezone en el código
- Riesgo de inconsistencias en fechas críticas (convocatorias, auditorías)

**Estado Objetivo**: ✅ Timezone-aware con America/Lima
- Uso de `zoneinfo.ZoneInfo` (Python 3.9+ estándar)
- Funciones helper centralizadas para obtener tiempo de Lima
- Todas las fechas almacenadas en UTC, convertidas a Lima para display
- Migración completa de todos los módulos

---

## 🎯 Beneficios de la Implementación

### **Para el Negocio**
1. ✅ **Fechas Precisas**: Convocatorias con plazos correctos en hora peruana
2. ✅ **Auditoría Confiable**: Logs con timestamps exactos de Lima
3. ✅ **Sincronización**: Coordinación correcta entre frontend y backend
4. ✅ **Cumplimiento Legal**: Fechas oficiales según zona horaria del Perú

### **Para el Desarrollo**
1. ✅ **Código Estandarizado**: Una sola forma de manejar fechas
2. ✅ **Menos Bugs**: Eliminación de errores de timezone
3. ✅ **Mantenibilidad**: Cambios centralizados en un solo lugar
4. ✅ **Testing Simplificado**: Tests con fechas predecibles

---

## 📊 Análisis de Impacto

### **Módulos Afectados** (50+ archivos)

#### **1. Módulo Techo Propio** (Alta Prioridad - Crítico)
- `convocation_entity.py` - Fechas de inicio/fin de convocatorias
- `mongo_convocation_repository.py` - 12 ocurrencias de datetime
- `convocation_management_use_cases.py` - Lógica de fechas
- `mongo_crud_repository.py` - Timestamps de creación/eliminación
- `mongo_query_repository.py` - Filtros por fecha
- `validate_dni_use_case.py` - 6 ocurrencias de validation_date

**Impacto**: 🔴 CRÍTICO - Fechas incorrectas afectan plazos de convocatorias gubernamentales

#### **2. APIs Gubernamentales** (Prioridad Media)
- `sunat_service.py` - 9 ocurrencias de datetime.utcnow()
- `reniec_service.py` - 5 ocurrencias de datetime.utcnow()
- `government_queries.py` - 2 ocurrencias para timestamps

**Impacto**: 🟡 MEDIO - Afecta logs y auditoría de consultas

#### **3. Sistema de Archivos** (Prioridad Media)
- `file_use_cases.py` - 3 ocurrencias (created_at, updated_at)
- `file_entity.py` - 1 ocurrencia en método update

**Impacto**: 🟡 MEDIO - Afecta metadatos de archivos

#### **4. Configuración de Interfaz** (Prioridad Baja)
- `interface_config.py` - 4 ocurrencias en métodos de actualización

**Impacto**: 🟢 BAJO - Solo metadatos de configuración

#### **5. Rutas/Endpoints** (Prioridad Baja)
- `convocation_routes.py` - 1 ocurrencia en endpoint de test

**Impacto**: 🟢 BAJO - Solo endpoint de prueba

---

## 🏗️ Diseño de la Solución

### **1. Configuración Centralizada**

**Archivo**: `src/mi_app_completa_backend/infrastructure/config/timezone_config.py`

```python
"""
Configuración centralizada de zona horaria para el sistema
Zona horaria oficial: America/Lima (Perú) - UTC-5
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

# Zona horaria de Perú
LIMA_TZ = ZoneInfo("America/Lima")
UTC_TZ = timezone.utc


def get_lima_timezone() -> ZoneInfo:
    """
    Obtener el objeto ZoneInfo para Lima, Perú
    
    Returns:
        ZoneInfo: Zona horaria de Lima (UTC-5)
    """
    return LIMA_TZ


def lima_now() -> datetime:
    """
    Obtener la fecha y hora actual en zona horaria de Lima
    
    Returns:
        datetime: Datetime actual con timezone de Lima
        
    Example:
        >>> now = lima_now()
        >>> print(now)  # 2025-01-06 15:30:00-05:00
    """
    return datetime.now(LIMA_TZ)


def utc_now() -> datetime:
    """
    Obtener la fecha y hora actual en UTC (timezone-aware)
    
    Returns:
        datetime: Datetime actual en UTC
        
    Example:
        >>> now = utc_now()
        >>> print(now)  # 2025-01-06 20:30:00+00:00
    """
    return datetime.now(UTC_TZ)


def to_lima_time(dt: datetime) -> datetime:
    """
    Convertir un datetime a zona horaria de Lima
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
        
    Returns:
        datetime: Datetime en zona horaria de Lima
        
    Example:
        >>> utc_dt = datetime(2025, 1, 6, 20, 30, tzinfo=timezone.utc)
        >>> lima_dt = to_lima_time(utc_dt)
        >>> print(lima_dt)  # 2025-01-06 15:30:00-05:00
    """
    if dt.tzinfo is None:
        # Si es naive, asumimos UTC
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(LIMA_TZ)


def to_utc_time(dt: datetime) -> datetime:
    """
    Convertir un datetime a UTC
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
        
    Returns:
        datetime: Datetime en UTC
        
    Example:
        >>> lima_dt = datetime(2025, 1, 6, 15, 30, tzinfo=ZoneInfo("America/Lima"))
        >>> utc_dt = to_utc_time(lima_dt)
        >>> print(utc_dt)  # 2025-01-06 20:30:00+00:00
    """
    if dt.tzinfo is None:
        # Si es naive, asumimos Lima
        dt = dt.replace(tzinfo=LIMA_TZ)
    return dt.astimezone(UTC_TZ)


def format_lima_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Formatear un datetime en zona horaria de Lima
    
    Args:
        dt: Datetime a formatear
        format_str: Formato de salida (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        str: Datetime formateado en zona horaria de Lima
        
    Example:
        >>> utc_dt = datetime(2025, 1, 6, 20, 30, tzinfo=timezone.utc)
        >>> formatted = format_lima_datetime(utc_dt)
        >>> print(formatted)  # "2025-01-06 15:30:00"
    """
    lima_dt = to_lima_time(dt)
    return lima_dt.strftime(format_str)


def parse_lima_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    Parsear un string de fecha asumiendo zona horaria de Lima
    
    Args:
        date_str: String con la fecha
        format_str: Formato del string (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        datetime: Datetime con timezone de Lima
        
    Example:
        >>> dt = parse_lima_datetime("2025-01-06 15:30:00")
        >>> print(dt)  # 2025-01-06 15:30:00-05:00
    """
    naive_dt = datetime.strptime(date_str, format_str)
    return naive_dt.replace(tzinfo=LIMA_TZ)


def get_lima_date_range(start_date: datetime, end_date: datetime) -> tuple[datetime, datetime]:
    """
    Obtener rango de fechas en zona horaria de Lima
    Útil para filtros de consultas
    
    Args:
        start_date: Fecha de inicio
        end_date: Fecha de fin
        
    Returns:
        tuple: (start_date_lima, end_date_lima)
    """
    return to_lima_time(start_date), to_lima_time(end_date)


# Alias para compatibilidad con código existente
def get_current_time() -> datetime:
    """Alias de lima_now() para compatibilidad"""
    return lima_now()
```

---

### **2. Actualización de Settings.py**

**Archivo**: `src/mi_app_completa_backend/infrastructure/config/settings.py`

```python
# Agregar al final de la clase Settings

# Configuración de Zona Horaria
timezone: str = Field(
    default="America/Lima",
    description="Zona horaria del sistema (Perú)"
)

def get_timezone(self) -> ZoneInfo:
    """Obtener objeto ZoneInfo de la configuración"""
    from zoneinfo import ZoneInfo
    return ZoneInfo(self.timezone)
```

---

### **3. Patrón de Migración**

#### **Antes (Timezone-naive)**
```python
from datetime import datetime

# ❌ MAL - Sin timezone
created_at = datetime.now()
updated_at = datetime.utcnow()
```

#### **Después (Timezone-aware)**
```python
from infrastructure.config.timezone_config import lima_now, utc_now, to_lima_time

# ✅ BIEN - Con timezone de Lima
created_at = lima_now()

# ✅ BIEN - Almacenar en UTC (mejor práctica)
updated_at = utc_now()

# ✅ BIEN - Convertir UTC a Lima para display
display_time = to_lima_time(updated_at)
```

---

## 🔄 Plan de Migración por Fases

### **FASE 1: Preparación** (1 día)

#### Tareas:
1. ✅ Crear `timezone_config.py` con funciones helper
2. ✅ Agregar configuración en `settings.py`
3. ✅ Crear tests unitarios para funciones de timezone
4. ✅ Documentar patrones de uso

#### Entregables:
- `infrastructure/config/timezone_config.py` (completo)
- `tests/unit/test_timezone_config.py` (10+ tests)
- `docs/TIMEZONE_USAGE_GUIDE.md` (guía de uso)

---

### **FASE 2: Migración Crítica - Techo Propio** (2 días)

#### **Priority 1: Convocation Repository**

**Archivo**: `mongo_convocation_repository.py`

Cambios:
```python
# ANTES
"created_at": convocation.created_at or datetime.utcnow()

# DESPUÉS
from infrastructure.config.timezone_config import utc_now
"created_at": convocation.created_at or utc_now()
```

**12 ocurrencias** a actualizar:
- Líneas 55, 56, 89, 90, 101, 102, 136, 266, 274, 282, 290, 307

#### **Priority 2: Convocation Use Cases**

**Archivo**: `convocation_management_use_cases.py`

Cambios:
```python
# ANTES
year = datetime.now().year

# DESPUÉS
from infrastructure.config.timezone_config import lima_now
year = lima_now().year
```

#### **Priority 3: CRUD Repository**

**Archivo**: `mongo_crud_repository.py`

Cambios:
```python
# ANTES
document["created_at"] = datetime.now()

# DESPUÉS
from infrastructure.config.timezone_config import utc_now
document["created_at"] = utc_now()
```

#### **Priority 4: Query Repository**

**Archivo**: `mongo_query_repository.py`

Cambios:
```python
# ANTES
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# DESPUÉS
from infrastructure.config.timezone_config import lima_now
today = lima_now().replace(hour=0, minute=0, second=0, microsecond=0)
```

#### **Priority 5: Validate DNI Use Case**

**Archivo**: `validate_dni_use_case.py`

Cambios:
```python
# ANTES
validation_date=datetime.now()

# DESPUÉS
from infrastructure.config.timezone_config import lima_now
validation_date=lima_now()
```

**6 ocurrencias** a actualizar: líneas 66, 85, 101, 114, 127, 182, 225

---

### **FASE 3: Migración Secundaria - APIs Gubernamentales** (1 día)

#### **SUNAT Service** (9 ocurrencias)
**Archivo**: `sunat_service.py`

```python
# ANTES
timestamp=datetime.utcnow()

# DESPUÉS
from infrastructure.config.timezone_config import utc_now
timestamp=utc_now()
```

Líneas: 135, 144, 153, 171, 180, 189, 235, 244

#### **RENIEC Service** (5 ocurrencias)
**Archivo**: `reniec_service.py`

Líneas: 130, 140, 153, 190, 199

#### **Government Queries** (2 ocurrencias)
**Archivo**: `government_queries.py`

Líneas: 198, 252

---

### **FASE 4: Migración Terciaria - Sistema de Archivos** (0.5 día)

#### **File Use Cases** (3 ocurrencias)
**Archivo**: `file_use_cases.py`
Líneas: 77, 156, 243

#### **File Entity** (1 ocurrencia)
**Archivo**: `file_entity.py`
Línea: 59

---

### **FASE 5: Migración Final - Configuración** (0.5 día)

#### **Interface Config** (4 ocurrencias)
**Archivo**: `interface_config.py`
Líneas: 143, 148, 153, 158

#### **Convocation Routes** (1 ocurrencia)
**Archivo**: `convocation_routes.py`
Línea: 61 (endpoint de test)

---

## ✅ Checklist de Testing

### **Tests Unitarios**
- [ ] `test_timezone_config.py` - Funciones helper
  - [ ] `test_lima_now()` - Retorna timezone de Lima
  - [ ] `test_utc_now()` - Retorna timezone UTC
  - [ ] `test_to_lima_time()` - Conversión correcta
  - [ ] `test_to_utc_time()` - Conversión correcta
  - [ ] `test_format_lima_datetime()` - Formato correcto
  - [ ] `test_parse_lima_datetime()` - Parseo correcto
  - [ ] `test_timezone_aware()` - Todos retornan timezone-aware
  - [ ] `test_naive_datetime_handling()` - Manejo de naive datetimes

### **Tests de Integración**
- [ ] `test_convocation_with_timezone.py` - Convocatorias
  - [ ] Test crear convocatoria con fechas en Lima
  - [ ] Test actualizar convocatoria preserva timezone
  - [ ] Test filtros de fecha respetan timezone
  - [ ] Test activación actualiza timestamp en UTC

### **Tests de Regresión**
- [ ] Ejecutar suite completa de tests existente
- [ ] Verificar que `test_convocation_crud.ps1` pasa (11 tests)
- [ ] Verificar que tests de APIs gubernamentales pasan

---

## 📝 Documentación Requerida

### **1. Guía de Uso** (`docs/TIMEZONE_USAGE_GUIDE.md`)

```markdown
# Guía de Uso - Zona Horaria

## Reglas de Oro

1. **Siempre usar funciones de timezone_config.py**
2. **Almacenar en UTC, mostrar en Lima**
3. **Nunca usar datetime.now() o datetime.utcnow() directamente**

## Casos de Uso

### Crear timestamp actual
```python
from infrastructure.config.timezone_config import lima_now, utc_now

# Para display o lógica de negocio
current_time = lima_now()

# Para almacenar en base de datos (recomendado)
timestamp = utc_now()
```

### Convertir entre timezones
```python
from infrastructure.config.timezone_config import to_lima_time, to_utc_time

# UTC -> Lima (para display)
lima_time = to_lima_time(utc_datetime)

# Lima -> UTC (para almacenar)
utc_time = to_utc_time(lima_datetime)
```

### Formatear para frontend
```python
from infrastructure.config.timezone_config import format_lima_datetime

# Formatear en Lima
formatted = format_lima_datetime(datetime_obj, "%d/%m/%Y %H:%M")
```
```

### **2. Actualizar README Principal**
- Agregar sección "🕐 Configuración de Zona Horaria"
- Documentar variable de entorno `TIMEZONE=America/Lima`

### **3. Comentarios en Código**
```python
# UTC para almacenamiento (mejor práctica internacional)
created_at = utc_now()

# Lima para lógica de negocio (convocatorias en hora peruana)
deadline = lima_now() + timedelta(days=30)
```

---

## 🚨 Consideraciones Importantes

### **Mejores Prácticas**

1. **Almacenar en UTC**: 
   - Todas las fechas en MongoDB en UTC
   - Facilita migraciones futuras y multi-timezone

2. **Mostrar en Lima**:
   - Convertir a Lima solo para display
   - Usar `to_lima_time()` en DTOs y responses

3. **Consistencia**:
   - Un solo import: `from infrastructure.config.timezone_config import ...`
   - No mezclar `datetime.now()` con funciones helper

4. **Validación**:
   - Verificar que todos los datetime tienen `tzinfo`
   - Usar `dt.tzinfo is not None` en validaciones

### **Errores Comunes a Evitar**

❌ **MAL: Mezclar naive y aware datetimes**
```python
naive = datetime.now()
aware = lima_now()
diff = aware - naive  # ❌ TypeError!
```

✅ **BIEN: Todo timezone-aware**
```python
dt1 = lima_now()
dt2 = utc_now()
diff = dt2 - dt1  # ✅ Funciona correctamente
```

❌ **MAL: Comparar naive con aware**
```python
if datetime.now() > convocation.end_date:  # ❌ Error si end_date es aware
```

✅ **BIEN: Comparar aware con aware**
```python
if lima_now() > convocation.end_date:  # ✅ Correcto
```

### **Impacto en MongoDB**

- MongoDB almacena todas las fechas en UTC internamente
- Las funciones helper garantizan conversión correcta
- No se requieren cambios en índices o esquemas

### **Impacto en Frontend**

- API devuelve fechas en ISO 8601 con timezone: `2025-01-06T15:30:00-05:00`
- JavaScript parsea automáticamente: `new Date(isoString)`
- Frontend debe respetar timezone del servidor

---

## 📊 Métricas de Éxito

### **Objetivos Cuantitativos**
- ✅ 100% de ocurrencias de datetime migradas
- ✅ 0 errores de timezone en tests
- ✅ Cobertura de tests >= 90% en timezone_config.py
- ✅ 0 warnings de datetime naive en logs

### **Objetivos Cualitativos**
- ✅ Todas las convocatorias muestran fechas correctas en Lima
- ✅ Auditorías con timestamps precisos de Perú
- ✅ Código más mantenible y legible
- ✅ Documentación clara para nuevos desarrolladores

---

## 🗓️ Timeline Estimado

| Fase | Duración | Archivos | Tests |
|------|----------|----------|-------|
| **Fase 1**: Preparación | 1 día | 2 nuevos | 10 tests |
| **Fase 2**: Techo Propio (crítico) | 2 días | 6 archivos | 15 tests |
| **Fase 3**: APIs Gubernamentales | 1 día | 3 archivos | 5 tests |
| **Fase 4**: Sistema de Archivos | 0.5 día | 2 archivos | 3 tests |
| **Fase 5**: Configuración | 0.5 día | 2 archivos | 2 tests |
| **Testing Final** | 1 día | - | Suite completa |
| **Documentación** | 0.5 día | 2 docs | - |
| **TOTAL** | **6.5 días** | **17 archivos** | **35+ tests** |

---

## 🎯 Próximos Pasos

### **Inmediatos**
1. ✅ Revisar y aprobar este plan
2. ⏳ Crear rama Git: `feature/timezone-lima-configuration`
3. ⏳ Implementar Fase 1 (timezone_config.py)
4. ⏳ Crear tests unitarios
5. ⏳ Revisar con equipo

### **Corto Plazo**
1. ⏳ Migrar módulo Techo Propio (Fase 2)
2. ⏳ Ejecutar tests de regresión
3. ⏳ Code review

### **Mediano Plazo**
1. ⏳ Migrar APIs Gubernamentales (Fase 3)
2. ⏳ Migrar resto de módulos (Fases 4-5)
3. ⏳ Documentación final
4. ⏳ Merge a main

---

## 📞 Contacto y Soporte

**Para preguntas sobre la migración:**
- Crear issue en el repositorio con tag `timezone`
- Consultar documentación: `docs/TIMEZONE_USAGE_GUIDE.md`
- Revisar ejemplos en tests: `tests/unit/test_timezone_config.py`

---

**Última Actualización**: 2025-01-06  
**Autor**: Sistema Backend AppTc  
**Versión**: 1.0
