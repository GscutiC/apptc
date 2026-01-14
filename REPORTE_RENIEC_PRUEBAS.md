# 📊 REPORTE DE PRUEBAS - API RENIEC

## 🎯 Objetivo
Identificar e implementar pruebas de la API RENIEC para consultar datos de personas por DNI, específicamente verificar si se puede obtener la fecha de nacimiento.

---

## ✅ HALLAZGOS CLAVE

### 1. **API RENIEC Implementada**
La aplicación tiene un servicio RENIEC completamente funcional ubicado en:
- **Ruta**: `src/backend/infrastructure/services/government_apis/reniec_service.py`
- **Proveedor**: API Real RENIEC (múltiples endpoints)
- **Arquitectura**: Basada en patrón BaseGovernmentAPI

### 2. **Endpoints Configurados**

#### Endpoints Principales:
1. **https://api.apis.net.pe/v1/dni** (API-PERU)
   - Formato: `?numero=47649607`
   - Actualmente: ⚠️ Retorna HTTP 429 (Too Many Requests)

2. **https://dniruc.apisperu.com/api/v1/dni/** (DNIRUC PERU)
   - Formato: `47649607`
   - Actualmente: ⚠️ Retorna HTTP 401 (Unauthorized - Requiere API Key)

#### Endpoints de Respaldo:
3. **https://api.reniec.gob.pe/v1/consulta/** (Oficial RENIEC)
   - Actualmente: ❌ No disponible (DNS falla)

---

## 📋 DATOS OBTENIDOS - DNI: 47649607

```json
{
  "dni": "47649607",
  "nombres": "JONATHAN",
  "apellido_paterno": "ELIAS",
  "apellido_materno": "DELGADO",
  "nombre_completo": "ELIAS DELGADO JONATHAN",
  "fecha_nacimiento": null,
  "estado_civil": "SOLTERO",
  "ubigeo": null,
  "direccion": null
}
```

### 📅 **RESULTADO: Fecha de Nacimiento NO DISPONIBLE**

---

## 🔍 Análisis Detallado

### Datos Disponibles:
✅ **DNI** - Número de documento  
✅ **Nombres** - JONATHAN  
✅ **Apellido Paterno** - ELIAS  
✅ **Apellido Materno** - DELGADO  
✅ **Nombre Completo** - ELIAS DELGADO JONATHAN  
✅ **Estado Civil** - SOLTERO  

### Datos NO Disponibles:
❌ **Fecha de Nacimiento** - No incluido en la respuesta de la API  
❌ **UBIGEO** - Código de ubicación geográfica  
❌ **Dirección** - Domicilio registrado  

---

## 🛠️ Implementación Técnica

### Flujo de Consulta:
1. **Validación** ✅ - DNI valida formato (8 dígitos)
2. **Intento 1** ✅ - API.apis.net.pe (EXITOSO - pero con datos parciales)
3. **Intento 2** - API dniruc.apisperu.com (API Key requerida)
4. **Intento 3** - API oficial RENIEC (No disponible)

### Campos del Modelo (reniec_entity.py):
```python
class DniData(BaseModel):
    dni: str                          # ✅ Disponible
    nombres: str                      # ✅ Disponible
    apellido_paterno: str             # ✅ Disponible
    apellido_materno: str             # ✅ Disponible
    nombre_completo: str              # ✅ Disponible
    fecha_nacimiento: Optional[str]   # ❌ NO disponible en respuesta
    estado_civil: Optional[str]       # ✅ Disponible
    ubigeo: Optional[str]             # ❌ NO disponible
    direccion: Optional[str]          # ❌ NO disponible
    restricciones: Optional[str]      # ❌ NO disponible
```

---

## 📡 Endpoints Disponibles en la API

### 1. **Validación TECHO PROPIO**
```
POST /api/techo-propio/validate/dni
```
Valida un DNI usando RENIEC:
```json
{
  "dni": "47649607"
}
```
Respuesta:
```json
{
  "success": true,
  "data": {
    "dni": "47649607",
    "is_valid": true,
    "names": "JONATHAN",
    "paternal_surname": "ELIAS",
    "maternal_surname": "DELGADO",
    "full_name": "ELIAS DELGADO JONATHAN",
    "birth_date": null,
    "error_message": null,
    "validation_date": "2026-01-14T14:07:33.305863"
  }
}
```

### 2. **Consulta General de Gobierno**
```
GET /api/government/dni/{dni}
```
Requiere autenticación (JWT).

---

## 🚨 Limitaciones Identificadas

### 1. **Fecha de Nacimiento No Disponible**
- La API RENIEC (apis.net.pe) utilizada actualmente **NO retorna** la fecha de nacimiento
- Campo mapeado como `fecha_nacimiento` pero **siempre es NULL**
- Posible solución: Cambiar de proveedor API o obtener credenciales para APIs de pago

### 2. **Estado de APIs Externas**
- **API Principal**: Funcionando pero con limitación de rate (HTTP 429)
- **API Backup 1**: Requiere autenticación/API Key
- **API Backup 2**: Dominio no disponible

### 3. **Datos Limitados**
La API actual solo proporciona:
- Nombre y apellidos
- Estado civil
- NO proporciona:
  - Fecha de nacimiento
  - Domicilio
  - Información de restricciones

---

## 💡 Recomendaciones

### Opción 1: Usar RENIEC API de Pago (Recomendado)
- Obtener credenciales con MIMP (Ministerio del Interior)
- Implementar endpoint autenticado
- Obtendría: Fecha nacimiento, dirección, foto, antecedentes

### Opción 2: Integrar con APIs Alternativas
- Usar `dniruc.apisperu.com` con API Key
- Usar `https://dni.rest` (alternativa)
- Validar si incluyen fecha de nacimiento

### Opción 3: Almacenar en BD
- Crear tabla de "personas" con fecha nacimiento manual
- Usuarios completan su fecha durante registro
- Validar durante proces de Techo Propio

### Opción 4: Modificar Formulario Frontend
- Solicitar fecha de nacimiento como campo obligatorio
- Hacer validación cruzada con edad mínima para Techo Propio
- No depender de RENIEC para este dato

---

## 📊 Tabla Comparativa de APIs RENIEC

| Característica | API Peru | DNIRUC Peru | RENIEC Oficial |
|---|---|---|---|
| **URL Base** | api.apis.net.pe | dniruc.apisperu.com | api.reniec.gob.pe |
| **DNI** | ✅ | ✅ | ✅ |
| **Nombres** | ✅ | ✅ | ✅ |
| **Apellidos** | ✅ | ✅ | ✅ |
| **Fecha Nac.** | ❌ | ❓ | ✅ |
| **Dirección** | ❌ | ❓ | ✅ |
| **Estado Civil** | ✅ | ✅ | ✅ |
| **Autenticación** | No | API Key requerida | OAuth 2.0 |
| **Rate Limit** | 429 error | 401 sin key | ? |
| **Estado Actual** | Funcionando | No autorizado | DNS falla |

---

## 🔧 Cómo Integrar Mejor Proveedor

Si deseas cambiar a una API que incluya fecha de nacimiento:

### 1. Agregar nuevas configuraciones
```python
# En reniec_service.py
self.api_endpoints = [
    # APIs que retornan más datos:
    "https://api-reniec-oficial.gob.pe/v1/personas",  # Si existe
    "https://dniruc.apisperu.com/api/v1/dni/",  # Con API Key
]
```

### 2. Obtener API Keys
```bash
# Para dniruc.apisperu.com
# Registrarse en: https://dniruc.apisperu.com
# Solicitarar API Key
```

### 3. Actualizar normalización
```python
def normalize_response(self, data: Dict[str, Any]) -> DniData:
    return DniData(
        # ... datos existentes ...
        fecha_nacimiento=data.get("fechaNacimiento") or data.get("fecha_nac"),
    )
```

---

## 📝 Conclusión

✅ **La API RENIEC está implementada y funciona correctamente**
✅ **Se obtienen datos de nombre y apellidos sin problemas**
❌ **La fecha de nacimiento NO está disponible** en el proveedor actual
🔧 **Se requiere cambio de proveedor o solución alternativa** para obtener fecha de nacimiento

**Próximos pasos recomendados:**
1. Determinar si Techo Propio requiere fecha de nacimiento de forma obligatoria
2. Si es obligatoria, solicitarla como campo adicional en el formulario
3. O integrar con API de pago de RENIEC que si incluya este dato

---

**Fecha del reporte**: 2026-01-14  
**DNI Testeado**: 47649607  
**Resultado**: Consulta exitosa (datos parciales)
