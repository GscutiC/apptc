# 🔍 Diagnóstico Completo: household_members Vacío en EditApplication

**Fecha:** 12 de Octubre, 2025  
**Problema:** Al editar una solicitud, `household_members` aparece vacío `[]`  
**Impacto:** No se puede ver ni editar el jefe de familia ni otros miembros del hogar

---

## 📋 Resumen Ejecutivo

El problema NO está en el backend guardando mal los datos, sino en **DOS DESCONEXIONES**:

1. **Backend guarda como `main_applicant`** pero **frontend busca `head_of_family`** en la respuesta
2. **Backend NO envía `household_members`** al frontend en el DTO de respuesta (campo faltante)

---

## 🔄 Flujo de Datos Completo

### **1. CREAR Solicitud (NewApplication → Backend → MongoDB)**

#### **Frontend enví a:**
```typescript
// NewApplication.tsx línea ~380
const requestData = {
  convocation_code: "CONV-001",
  user_data: {
    dni: "47649607",
    names: "JONATHAN",
    surnames: "ELIAS DELGADO",
    phone: "975332406",
    email: "asdasd@gmail.com"
  },
  head_of_family: {  // ✅ Envía como head_of_family
    document_number: "47649607",
    first_name: "JONATHAN",
    paternal_surname: "ELIAS",
    maternal_surname: "DELGADO",
    birth_date: "1990-01-01",
    civil_status: "soltero",
    education_level: "universitaria_completa",
    occupation: "Ingeniero",
    phone_number: "975332406",
    email: "asdasd@gmail.com"
  },
  head_of_family_economic: {
    employment_situation: "dependiente",
    monthly_income: 5000,
    work_condition: "formal"
  },
  household_members: [],  // ❌ FRONTEND FILTRA al jefe de familia (línea 351-358)
  property_info: {...}
}
```

#### **Backend procesa (create_application_use_case.py):**
```python
# Líneas 113-130
head_of_family = Applicant(  # ✅ Recibe como head_of_family
    document_number=dto.head_of_family.document_number,
    first_name=dto.head_of_family.first_name,
    # ...
)

head_of_family_economic = EconomicInfo(
    employment_situation=dto.head_of_family_economic.employment_situation,
    # ...
)

# Líneas 195-214
household_members = []
for member_dto in dto.household_members:  # ❌ Lista vacía porque frontend filtró
    member = HouseholdMember(...)
    household_members.append(member)

# Línea 220
application = TechoPropioApplication(
    head_of_family=head_of_family,  # ✅ Asigna correctamente
    head_of_family_economic=head_of_family_economic,
    household_members=household_members,  # ❌ Lista vacía []
    # ...
)
```

#### **Backend guarda en MongoDB (application_mapper.py):**
```python
# Líneas 40-41
document = {
    "main_applicant": ApplicantMapper.to_dict(application.head_of_family),  # ❌ Guarda como main_applicant
    "main_applicant_economic": EconomicMapper.to_dict(application.head_of_family_economic),
    "household_members": [...]  # ❌ Lista vacía
}
```

#### **MongoDB tiene:**
```json
{
  "_id": "68ec37761afb62c361c3fc22",
  "main_applicant": {  // ❌ Nombre antiguo
    "document_number": "47649607",
    "first_name": "JONATHAN",
    "paternal_surname": "ELIAS",
    "maternal_surname": "DELGADO",
    "birth_date": "1990-01-01",
    "civil_status": "soltero",
    "education_level": "universitaria_completa",
    "occupation": "Ingeniero"
  },
  "main_applicant_economic": {
    "employment_situation": "dependiente",
    "monthly_income": 5000,
    "work_condition": "formal"
  },
  "household_members": [],  // ❌ VACÍO
  "status": "draft",
  "user_id": "user_339MX93RuwYOONURelR2HCxBrDU"
}
```

---

### **2. EDITAR Solicitud (EditApplication ← Backend ← MongoDB)**

#### **Backend lee de MongoDB (application_mapper.py):**
```python
# Líneas 80-93
@classmethod
def from_dict(cls, document: Dict[str, Any]) -> TechoPropioApplication:
    # Lee main_applicant de MongoDB
    head_of_family = ApplicantMapper.from_dict(document["main_applicant"])  # ✅ Convierte correctamente
    property_info = PropertyMapper.from_dict(document["property_info"])
    head_of_family_economic = EconomicMapper.from_dict(document["main_applicant_economic"])
    
    application = TechoPropioApplication(
        head_of_family=head_of_family,  # ✅ Asigna correctamente como head_of_family
        property_info=property_info,
        head_of_family_economic=head_of_family_economic
    )
    
    application.id = str(document["_id"])
    application.user_id = document.get("user_id")
    application.status = ApplicationStatus(document["status"])
    
    # ❌ FALTA: Restaurar household_members desde document["household_members"]
```

#### **Backend responde (create_application_use_case._convert_to_response_dto):**
```python
# Líneas 250-290
head_of_family_dto = ApplicantResponseDTO(
    id=application.head_of_family.id,
    document_number=application.head_of_family.document_number,
    first_name=application.head_of_family.first_name,
    # ... ✅ Todos los campos del jefe de familia
)

# Líneas 397-415
household_dtos = []
for member in application.household_members:  # ❌ Lista vacía porque no se restauró
    member_dto = HouseholdMemberResponseDTO(...)
    household_dtos.append(member_dto)

# Líneas 430-445
response_dto = TechoPropioApplicationResponseDTO(
    id=application.id,
    head_of_family=head_of_family_dto,  # ✅ Envía head_of_family
    head_of_family_economic=head_of_family_economic_dto,
    household_members=household_dtos,  # ❌ Lista vacía []
    # ...
)
```

#### **Frontend recibe (TechoPropioApplication interface):**
```typescript
// application.types.ts línea 268
export interface TechoPropioApplication {
  id?: string;
  code: string;
  status: ApplicationStatus;
  applicant: Applicant;  // ❌ Frontend espera "applicant", backend envía "head_of_family"
  household_members: HouseholdMember[];  // ❌ Recibe lista vacía []
  economic_info: EconomicInfo;
  property_info: PropertyInfo;
  // ...
}
```

#### **EditApplication mapea (líneas 38-90):**
```typescript
useEffect(() => {
  if (selectedApplication) {
    console.log('🔍 selectedApplication:', selectedApplication);
    
    // Busca jefe de familia en household_members
    const realHeadOfFamily = selectedApplication.household_members?.find(
      member => member.member_type === 'JEFE_FAMILIA'
    );  // ❌ NO LO ENCUENTRA porque household_members está vacío []
    
    console.log('👨‍💼 Jefe de Familia Real:', realHeadOfFamily);  // undefined
    
    const mappedData: ApplicationFormData = {
      head_of_family: {
        dni: selectedApplication.applicant?.dni || realHeadOfFamily?.dni || '',  // ❌ Ambos vacíos
        first_name: selectedApplication.applicant?.first_name || '',  // ❌ Vacío
        // ...
      },
      household_members: selectedApplication.household_members || []  // ❌ []
    };
    
    console.log('📦 Mapped formData:', mappedData);
    setFormData(mappedData);
  }
}, [selectedApplication]);
```

---

## 🎯 Problemas Identificados

### **Problema 1: Desconexión de Nomenclatura**

| Ubicación | Nombre del Campo | Estado |
|-----------|------------------|--------|
| Frontend envía | `head_of_family` | ✅ Correcto |
| Backend procesa | `head_of_family` | ✅ Correcto |
| MongoDB guarda | `main_applicant` | ❌ Nombre antiguo |
| Backend lee MongoDB | `main_applicant` → `head_of_family` | ✅ Convierte correctamente |
| Backend responde | `head_of_family` | ✅ Correcto |
| Frontend espera | `applicant` | ❌ Nombre diferente |

**Consecuencia:**  
Frontend busca `selectedApplication.applicant` pero backend envía `selectedApplication.head_of_family`

---

### **Problema 2: household_members No Se Restaura**

#### **En `application_mapper.py` líneas 80-125:**

```python
@classmethod
def from_dict(cls, document: Dict[str, Any]) -> TechoPropioApplication:
    head_of_family = ApplicantMapper.from_dict(document["main_applicant"])
    property_info = PropertyMapper.from_dict(document["property_info"])
    head_of_family_economic = EconomicMapper.from_dict(document["main_applicant_economic"])
    
    application = TechoPropioApplication(
        head_of_family=head_of_family,
        property_info=property_info,
        head_of_family_economic=head_of_family_economic
        # ❌ FALTA: household_members NO se pasa al constructor
    )
    
    # ... asignaciones de metadata
    
    # ❌ FALTA: 
    # if "household_members" in document:
    #     application.household_members = [
    #         HouseholdMemberMapper.from_dict(m) for m in document["household_members"]
    #     ]
    
    return application
```

**Resultado:**  
`application.household_members` queda como lista vacía `[]` incluso si MongoDB tiene datos.

---

### **Problema 3: Frontend Filtra el Jefe de Familia**

#### **En `NewApplication.tsx` líneas 351-358:**

```typescript
// Transformar household_members: EXCLUIR jefe de familia para evitar DNI duplicado
const transformedHouseholdMembers = (formData.household_members || [])
  .filter(member => 
    // Filtrar el jefe de familia basado en DNI
    member.dni !== formData.head_of_family?.dni &&
    member.dni !== formData.head_of_family?.document_number
  )
  .map(member => ({...}));
```

**Intención:** Evitar duplicar el jefe de familia (se envía por separado en `head_of_family`)  
**Problema:** MongoDB termina sin el jefe de familia en `household_members`

---

## ✅ Soluciones Propuestas

### **Solución 1: Corregir Mapper - Restaurar household_members**

**Archivo:** `backend/src/mi_app_completa_backend/infrastructure/persistence/techo_propio/mappers/application_mapper.py`

**Líneas a modificar:** ~80-125

```python
@classmethod
def from_dict(cls, document: Dict[str, Any]) -> TechoPropioApplication:
    """Convertir documento MongoDB a entidad TechoPropioApplication"""
    try:
        # Usar mappers específicos
        head_of_family = ApplicantMapper.from_dict(document["main_applicant"])
        property_info = PropertyMapper.from_dict(document["property_info"])
        head_of_family_economic = EconomicMapper.from_dict(document["main_applicant_economic"])
        
        # ✅ CORREGIDO: Restaurar household_members desde MongoDB
        household_members = []
        if "household_members" in document and document["household_members"]:
            household_members = [
                HouseholdMemberMapper.from_dict(member_data)
                for member_data in document["household_members"]
            ]
        
        # Crear solicitud con todos los datos
        application = TechoPropioApplication(
            head_of_family=head_of_family,
            property_info=property_info,
            head_of_family_economic=head_of_family_economic,
            household_members=household_members  # ✅ AGREGAR
        )
        
        # ... resto del código
```

---

### **Solución 2: Corregir Frontend - Mapeo de Respuesta**

**Archivo:** `frontend/src/modules/techo-propio/pages/EditApplication.tsx`

**Líneas a modificar:** ~38-90

```typescript
useEffect(() => {
  if (selectedApplication) {
    console.log('🔍 selectedApplication:', selectedApplication);
    
    // ✅ CORREGIDO: Buscar jefe de familia en TODOS los campos posibles
    const headOfFamily = 
      selectedApplication.head_of_family ||  // Backend nuevo
      selectedApplication.applicant ||  // Frontend espera
      selectedApplication.main_applicant;  // MongoDB antiguo
    
    console.log('👨‍💼 Jefe de Familia:', headOfFamily);
    
    // ✅ CORREGIDO: Buscar en household_members como fallback
    let realHeadOfFamily = selectedApplication.household_members?.find(
      member => 
        member.member_type === 'JEFE_FAMILIA' ||
        member.relationship === 'jefe_familia' ||
        member.document_number === headOfFamily?.document_number
    );
    
    // Si no está en household_members, usar headOfFamily directamente
    if (!realHeadOfFamily && headOfFamily) {
      realHeadOfFamily = headOfFamily;
    }
    
    console.log('👨‍💼 Jefe de Familia Real:', realHeadOfFamily);
    
    const mappedData: ApplicationFormData = {
      head_of_family: {
        dni: realHeadOfFamily?.document_number || realHeadOfFamily?.dni || '',
        document_number: realHeadOfFamily?.document_number || realHeadOfFamily?.dni || '',
        first_name: realHeadOfFamily?.first_name || '',
        paternal_surname: realHeadOfFamily?.paternal_surname || '',
        maternal_surname: realHeadOfFamily?.maternal_surname || '',
        phone_number: realHeadOfFamily?.phone_number || '',
        email: realHeadOfFamily?.email || '',
        birth_date: realHeadOfFamily?.birth_date || '',
        civil_status: realHeadOfFamily?.civil_status || 'soltero',
        education_level: realHeadOfFamily?.education_level || 'secundaria_completa',
        occupation: realHeadOfFamily?.occupation || ''
      },
      household_members: selectedApplication.household_members || [],
      property_info: selectedApplication.property_info,
      comments: selectedApplication.comments || ''
    };
    
    console.log('📦 Mapped formData:', mappedData);
    setFormData(mappedData);
  }
}, [selectedApplication]);
```

---

### **Solución 3: Corregir Interface TypeScript**

**Archivo:** `frontend/src/modules/techo-propio/types/application.types.ts`

**Líneas a modificar:** ~268-290

```typescript
export interface TechoPropioApplication {
  id?: string;
  code: string;
  status: ApplicationStatus;
  
  // ✅ CORREGIDO: Soportar ambos nombres para compatibilidad
  applicant?: Applicant;  // Frontend antiguo
  head_of_family?: Applicant;  // Backend nuevo
  main_applicant?: Applicant;  // MongoDB antiguo
  
  household_members: HouseholdMember[];
  household_size: number;
  economic_info: EconomicInfo;
  head_of_family_economic?: EconomicInfo;  // ✅ AGREGAR
  property_info: PropertyInfo;
  priority_score: number;
  documents: Document[];
  state_history: StateHistory[];
  comments?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
  
  // ✅ AGREGAR: Campos de registro
  registration_date?: string;
  convocation_code?: string;
  registration_year?: number;
  sequential_number?: number;
  application_number?: string | null;
}
```

---

## 📊 Plan de Implementación

### **Paso 1: Corregir Backend (Mapper)**
1. Editar `application_mapper.py`
2. Agregar restauración de `household_members` en `from_dict()`
3. Probar lectura de aplicaciones existentes

### **Paso 2: Corregir Frontend (EditApplication)**
1. Editar `EditApplication.tsx`
2. Agregar mapeo flexible de `head_of_family` / `applicant` / `main_applicant`
3. Usar `head_of_family` directamente si `household_members` está vacío

### **Paso 3: Actualizar Interface TypeScript**
1. Editar `application.types.ts`
2. Agregar campos opcionales para compatibilidad
3. Documentar diferencias entre versiones

### **Paso 4: Migrar Datos Existentes (Opcional)**
1. Script de migración para agregar jefe de familia a `household_members`
2. Renombrar `main_applicant` → `head_of_family` en MongoDB

---

## 🧪 Casos de Prueba

### **Test 1: Leer Aplicación Existente**
```python
# backend/tests/test_edit_application.py
async def test_read_application_with_household():
    application = await repository.get_application_by_id("68ec37761afb62c361c3fc22")
    assert application.head_of_family is not None
    assert len(application.household_members) >= 0  # Puede estar vacío en datos antiguos
```

### **Test 2: Frontend Carga Datos**
```typescript
// frontend/src/modules/techo-propio/__tests__/EditApplication.test.tsx
it('should load head_of_family from different field names', () => {
  const app1 = { head_of_family: { dni: '12345678' } };
  const app2 = { applicant: { dni: '87654321' } };
  const app3 = { main_applicant: { dni: '11111111' } };
  
  expect(getHeadOfFamily(app1).dni).toBe('12345678');
  expect(getHeadOfFamily(app2).dni).toBe('87654321');
  expect(getHeadOfFamily(app3).dni).toBe('11111111');
});
```

---

## 📝 Conclusiones

### **Root Cause:**
1. ❌ **Mapper no restaura `household_members`** desde MongoDB
2. ❌ **Frontend busca `applicant`** pero backend envía `head_of_family`
3. ❌ **Frontend filtra jefe de familia** de `household_members` al crear, pero no se reinserta

### **Impacto:**
- Al editar solicitudes, no aparecen miembros del hogar
- Jefe de familia no se puede editar
- Paso 2 y Paso 5 muestran datos vacíos

### **Solución Recomendada:**
1. **Prioridad ALTA:** Corregir `application_mapper.py` para restaurar `household_members`
2. **Prioridad MEDIA:** Actualizar `EditApplication.tsx` para mapeo flexible
3. **Prioridad BAJA:** Actualizar interface TypeScript para claridad

---

**Estado:** 🔍 Diagnóstico Completo  
**Próximo Paso:** Implementar Solución 1 (Corregir Mapper)
