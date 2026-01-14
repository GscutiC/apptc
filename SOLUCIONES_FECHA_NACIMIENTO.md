# 🔧 SOLUCIONES PARA OBTENER FECHA DE NACIMIENTO EN RENIEC

## Problema Identificado
La API RENIEC actual (api.apis.net.pe) **NO retorna la fecha de nacimiento**, campo que es importante para validaciones en el módulo de Techo Propio.

---

## 🎯 Soluciones Propuestas

### **Solución 1: Solicitar Dato Adicional en Formulario** ✅ RECOMENDADA
**Complejidad**: ⭐ (Muy Simple)  
**Costo**: $0  
**Tiempo Implementación**: 30 minutos

#### Ventajas:
- ✅ No depende de APIs externas
- ✅ Datos más precisos (el usuario conoce su fecha exacta)
- ✅ Compatible con todas las APIs actuales
- ✅ Mejora UX (usuario completa perfil)

#### Implementación:
1. Agregar campo `fecha_nacimiento` en el formulario de solicitante
2. Validar que sea mayor de edad (18+) para Techo Propio
3. Almacenar en la BD

```typescript
// DniValidator.tsx - Agregar campo
<DateInput
  label="Fecha de Nacimiento"
  value={birthDate}
  onChange={setBirthDate}
  required
  minDate={new Date(1930, 0, 1)}
  maxDate={new Date().setFullYear(new Date().getFullYear() - 18)}
/>
```

```python
# ApplicantValidationDTO - Backend
class ApplicantValidationDTO(BaseModel):
    dni: str
    fecha_nacimiento: date  # Nuevo campo
    # ... otros campos
```

---

### **Solución 2: Integrar DNIRUC Peru Con API Key** ⚡ ALTERNATIVA
**Complejidad**: ⭐⭐ (Moderada)  
**Costo**: Variable (API de pago)  
**Tiempo Implementación**: 2-3 horas

#### Ventajas:
- ✅ Algunos endpoints incluyen fecha nacimiento
- ⚠️ Requiere API Key (costo)
- ⚠️ Mejor calidad de datos que apis.net.pe

#### Implementación:

```python
# 1. En requirements.txt
# (ya está: httpx>=0.24.0)

# 2. Agregar endpoint backup mejorado
class ReniecService:
    def __init__(self):
        # ... código existente ...
        self.api_key = os.getenv("DNIRUC_API_KEY", "")
        
        # Actualizar endpoints
        self.api_endpoints = [
            "https://api.apis.net.pe/v1/dni",  # Mantener como principal
            "https://dniruc.apisperu.com/api/v1/dni/",  # Mejorado
        ]
    
    async def _consultar_api_reniec(self, dni: str, endpoint: str) -> DniConsultaResponse:
        """Intenta consultar una API real de RENIEC usando httpx async"""
        try:
            # Headers con autenticación si es DNIRUC
            headers = self.headers.copy()
            if "dniruc" in endpoint and self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Construcción URL...
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
            
            # ... resto del código ...
```

#### Registrarse:
1. Ir a https://dniruc.apisperu.com
2. Crear cuenta y obtener API Key
3. Agregar en variables de entorno:
```bash
DNIRUC_API_KEY="tu_api_key_aqui"
```

---

### **Solución 3: Usar API RENIEC Oficial (Pago)** 💰 MEJOR CALIDAD
**Complejidad**: ⭐⭐⭐ (Compleja)  
**Costo**: $$ (contactar RENIEC)  
**Tiempo Implementación**: 1-2 semanas

#### Ventajas:
- ✅ Datos completos y oficiales
- ✅ Incluye fecha nacimiento, dirección, foto
- ✅ Más confiable y legal
- ❌ Costo y proceso burocrático

#### Pasos:
1. Contactar RENIEC (Ministerio del Interior)
2. Solicitar acceso a API con credenciales OAuth 2.0
3. Implementar autenticación OAuth:

```python
# Implementación OAuth 2.0
from authlib.integrations.httpx_client import AsyncOAuth2Client

class ReniecOAuthService(ReniecService):
    async def authenticate(self):
        """Autenticar con RENIEC usando OAuth 2.0"""
        client = AsyncOAuth2Client(
            client_id=os.getenv("RENIEC_CLIENT_ID"),
            client_secret=os.getenv("RENIEC_CLIENT_SECRET")
        )
        
        token = await client.fetch_token(
            "https://api.reniec.gob.pe/oauth/token"
        )
        return token
    
    async def query_document(self, document: str) -> DniConsultaResponse:
        """Consulta con token OAuth"""
        token = await self.authenticate()
        # ... usar token en headers ...
```

---

### **Solución 4: Caché Local + Validación Manual** 🔄 HÍBRIDA
**Complejidad**: ⭐⭐ (Moderada)  
**Costo**: $0  
**Tiempo Implementación**: 1 hora

#### Concepto:
Mantener una base de datos local de fechas de nacimiento de ciudadanos o solicitar que el usuario la proporcione.

```python
# Entidad para almacenar DNI + Fecha Nacimiento
class PersonaRegistro(BaseModel):
    dni: str
    fecha_nacimiento: date
    nombres: str
    apellidos: str
    
# Antes de consultar RENIEC
async def get_person_data(dni: str):
    # 1. Buscar en BD local primero
    local_record = await PersonaRepository.get_by_dni(dni)
    if local_record:
        return local_record
    
    # 2. Si no existe, consultar RENIEC
    reniec_data = await reniec_service.query_document(dni)
    
    # 3. Solicitar fecha de nacimiento al usuario si no la tiene
    if not reniec_data.data.fecha_nacimiento:
        # Retornar indicador para frontend
        return {
            "reniec_data": reniec_data,
            "missing_birth_date": True
        }
```

---

## 📊 Tabla Comparativa de Soluciones

| Solución | Costo | Tiempo | Confiabilidad | Automatización | Recomendación |
|----------|-------|--------|---|---|---|
| **1. Campo en Formulario** | $0 | 30m | ⭐⭐⭐⭐⭐ | Manual | ✅✅✅ MEJOR |
| **2. DNIRUC Con API Key** | $$ | 2-3h | ⭐⭐⭐⭐ | Alta | ✅✅ BUENA |
| **3. RENIEC Oficial OAuth** | $$$ | 1-2w | ⭐⭐⭐⭐⭐ | Alta | ✅ EXCELENTE |
| **4. Caché Local Híbrida** | $0 | 1h | ⭐⭐⭐ | Media | ✅ ALTERNATIVA |

---

## 🚀 IMPLEMENTACIÓN RECOMENDADA

### Fase 1: Corto Plazo (Ahora)
```
✅ Solución 1: Agregar campo de fecha de nacimiento en formulario
   - No tiene costo
   - Funciona inmediatamente
   - Datos más precisos
```

### Fase 2: Mediano Plazo (1-2 meses)
```
✅ Solución 2 O 4: Mejorar con DNIRUC o caché local
   - Opcional según presupuesto
   - Mejora experiencia usuario
```

### Fase 3: Largo Plazo (3-6 meses)
```
✅ Solución 3: Integrar RENIEC Oficial
   - Si requiere máxima confiabilidad
   - Una vez que tramite esté completo
```

---

## 📝 Código Rápido - Solución 1 (Recomendada)

### Frontend (TypeScript/React)

```typescript
// DniValidator.tsx modificado
interface DniValidationResult {
  dni: string;
  nombres: string;
  paternal_surname: string;
  maternal_surname: string;
  full_name: string;
  birth_date?: string; // Ahora opcional, usuario lo completa
  from_reniec: boolean;
  missing_birth_date?: boolean;
}

export function DniValidator() {
  const [dni, setDni] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [validationResult, setValidationResult] = useState<DniValidationResult | null>(null);

  const handleValidate = async () => {
    try {
      // Validar DNI con RENIEC
      const reniecResult = await validateDni(dni);
      
      if (reniecResult.success) {
        // Marcar que falta fecha de nacimiento
        setValidationResult({
          ...reniecResult.data,
          missing_birth_date: !birthDate
        });
      }
    } catch (error) {
      console.error("Error validando DNI:", error);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="DNI (8 dígitos)"
        value={dni}
        onChange={(e) => setDni(e.target.value)}
        maxLength={8}
      />
      
      <input
        type="date"
        value={birthDate}
        onChange={(e) => setBirthDate(e.target.value)}
        max={new Date().toISOString().split("T")[0]} // No futuro
        required
      />
      
      <button onClick={handleValidate}>
        Validar con RENIEC
      </button>

      {validationResult && (
        <div>
          <p>✅ {validationResult.full_name}</p>
          <p>DNI: {validationResult.dni}</p>
          {!validationResult.from_reniec && (
            <p>📅 Fecha nacimiento (completada por usuario): {birthDate}</p>
          )}
        </div>
      )}
    </div>
  );
}
```

### Backend (Python)

```python
# En ApplicantValidationDTO
from datetime import date

class ApplicantValidationDTO(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    fecha_nacimiento: date = Field(..., description="Fecha de nacimiento del solicitante")
    nombres: str
    apellido_paterno: str
    apellido_materno: str

# En validate_applicant endpoint
@router.post("/validate/applicant")
async def validate_applicant(
    data: ApplicantValidationDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases)
):
    """Validar datos completos de solicitante incluyendo fecha de nacimiento"""
    
    # 1. Validar DNI con RENIEC
    dni_result = await use_cases.validate_dni(
        DniValidationRequestDTO(dni=data.dni)
    )
    
    if not dni_result.is_valid:
        raise HTTPException(status_code=400, detail="DNI no válido")
    
    # 2. Validar edad (Techo Propio requiere 18+)
    today = datetime.now().date()
    age = (today - data.fecha_nacimiento).days // 365
    
    if age < 18:
        raise HTTPException(
            status_code=400,
            detail="Debe ser mayor de 18 años para acceder a Techo Propio"
        )
    
    # 3. Validar que datos coincidan
    if (data.nombres.upper() not in dni_result.names.upper() or
        data.apellido_paterno.upper() != dni_result.paternal_surname.upper()):
        raise HTTPException(
            status_code=400,
            detail="Los datos no coinciden con RENIEC"
        )
    
    # 4. Retornar datos completos
    return {
        "success": True,
        "data": {
            "dni": data.dni,
            "nombres": dni_result.names,
            "apellido_paterno": dni_result.paternal_surname,
            "apellido_materno": dni_result.maternal_surname,
            "full_name": dni_result.full_name,
            "fecha_nacimiento": data.fecha_nacimiento.isoformat(),
            "edad": age,
            "validado": True
        }
    }
```

---

## ✅ Conclusión

**La solución recomendada es la #1**: Agregar un campo de fecha de nacimiento en el formulario frontend.

- **Costo**: $0
- **Implementación**: 30 minutos
- **Beneficio**: Datos más precisos y control del usuario

Luego, en futuras iteraciones, pueden integrar APIs de pago si necesitan mayor automatización.

---

**Última actualización**: 2026-01-14
