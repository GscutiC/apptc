"""
DTOs (Data Transfer Objects) para el módulo Techo Propio
Manejan la transferencia de datos entre las capas con validaciones Pydantic
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator, model_validator
from enum import Enum

# Importar enums del dominio
from ....domain.value_objects.techo_propio import (
    ApplicationStatus, DocumentType, CivilStatus, EducationLevel,
    EmploymentSituation, WorkCondition, FamilyRelationship, DisabilityType,
    VALIDATION_CONSTANTS
)


# ===== DTOs BÁSICOS =====

class ApplicantCreateDTO(BaseModel):
    """DTO para crear un solicitante"""
    document_type: DocumentType
    document_number: str = Field(..., min_length=8, max_length=12)
    first_name: str = Field(..., min_length=2, max_length=100)
    paternal_surname: str = Field(..., min_length=2, max_length=100)
    maternal_surname: str = Field(..., min_length=2, max_length=100)
    birth_date: date
    civil_status: CivilStatus
    education_level: EducationLevel
    occupation: Optional[str] = Field(None, max_length=200)
    disability_type: DisabilityType = DisabilityType.NONE
    disability_is_permanent: bool = False  # ✅ NUEVO: ¿La discapacidad es permanente?
    disability_is_severe: bool = False  # ✅ NUEVO: ¿La discapacidad es severa?
    is_main_applicant: bool = True
    phone_number: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @validator('document_number')
    def validate_document_number(cls, v, values):
        if values.get('document_type') == DocumentType.DNI:
            if len(v) != 8 or not v.isdigit():
                raise ValueError('DNI debe tener exactamente 8 dígitos')
        return v

    @validator('birth_date')
    def validate_birth_date(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        
        min_age = VALIDATION_CONSTANTS["MIN_AGE"]
        max_age = VALIDATION_CONSTANTS["MAX_AGE"]
        
        if age < min_age:
            raise ValueError(f'El solicitante debe tener al menos {min_age} años')
        if age > max_age:
            raise ValueError(f'El solicitante no puede tener más de {max_age} años')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v:
            # Remover espacios y caracteres especiales para validación
            clean_phone = ''.join(filter(str.isdigit, v))
            if len(clean_phone) < 7 or len(clean_phone) > 15:
                raise ValueError('Número de teléfono debe tener entre 7 y 15 dígitos')
        return v


class PropertyInfoCreateDTO(BaseModel):
    """DTO para crear información del predio"""
    department: str = Field(..., min_length=2, max_length=50)
    province: str = Field(..., min_length=2, max_length=50)
    district: str = Field(..., min_length=2, max_length=50)
    lote: str = Field(..., min_length=1, max_length=20)
    address: str = Field(..., min_length=5, max_length=200)
    ubigeo_code: Optional[str] = Field(None, min_length=6, max_length=6)
    populated_center: Optional[str] = Field(None, max_length=100)
    manzana: Optional[str] = Field(None, max_length=20)
    sub_lote: Optional[str] = Field(None, max_length=20)
    reference: Optional[str] = Field(None, max_length=300)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

    @validator('ubigeo_code')
    def validate_ubigeo_code(cls, v):
        if v and (len(v) != 6 or not v.isdigit()):
            raise ValueError('Código UBIGEO debe tener exactamente 6 dígitos')
        return v


class HouseholdMemberCreateDTO(BaseModel):
    """DTO para crear miembro de carga familiar"""
    first_name: str = Field(..., min_length=2, max_length=100)
    paternal_surname: str = Field(..., min_length=2, max_length=100)
    maternal_surname: str = Field(..., min_length=2, max_length=100)
    document_type: DocumentType
    document_number: str = Field(..., min_length=8, max_length=12)
    birth_date: date
    civil_status: CivilStatus  # ✅ NUEVO - Estado civil
    education_level: EducationLevel  # ✅ MODIFICADO - Ahora requerido
    occupation: str = Field(..., min_length=2, max_length=200)  # ✅ NUEVO - Ocupación
    employment_situation: EmploymentSituation  # ✅ NUEVO - Dependiente/Independiente
    work_condition: WorkCondition  # ✅ NUEVO - Formal/Informal (era employment_condition en frontend)
    monthly_income: Decimal = Field(..., ge=0, le=50000)  # ✅ NUEVO - Ingreso mensual (permite 0)
    disability_type: DisabilityType = DisabilityType.NONE
    disability_is_permanent: bool = False  # ✅ NUEVO: ¿La discapacidad es permanente?
    disability_is_severe: bool = False  # ✅ NUEVO: ¿La discapacidad es severa?
    relationship: Optional[FamilyRelationship] = None  # ✅ MODIFICADO - Ahora opcional
    is_dependent: bool = True

    @validator('document_number')
    def validate_document_number(cls, v, values):
        if values.get('document_type') == DocumentType.DNI:
            if len(v) != 8 or not v.isdigit():
                raise ValueError('DNI debe tener exactamente 8 dígitos')
        return v

    @validator('birth_date')
    def validate_birth_date(cls, v):
        today = date.today()
        if v > today:
            raise ValueError('La fecha de nacimiento no puede ser futura')
        
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age > 100:
            raise ValueError('La edad no puede ser mayor a 100 años')
        return v

    @validator('work_condition', pre=True)
    def normalize_work_condition(cls, v):
        """Normalizar work_condition para aceptar mayúsculas y minúsculas"""
        if isinstance(v, str):
            v_lower = v.lower()
            # Mapear valores conocidos
            if v_lower in ['formal', 'informal']:
                return v_lower
            # Si viene en mayúsculas, convertir a minúsculas
            if v.upper() in ['FORMAL', 'INFORMAL']:
                return v.lower()
        return v

    @validator('civil_status', pre=True)
    def normalize_civil_status(cls, v):
        """Normalizar civil_status para aceptar variaciones"""
        if isinstance(v, str):
            v_lower = v.lower()
            # Mapear valores conocidos
            valid_values = ['soltero', 'casado', 'divorciado', 'viudo', 'conviviente']
            if v_lower in valid_values:
                return v_lower
        return v

    @validator('employment_situation', pre=True)
    def normalize_employment_situation(cls, v):
        """Normalizar employment_situation para aceptar variaciones"""
        if isinstance(v, str):
            v_lower = v.lower()
            # Mapear valores conocidos
            valid_values = ['dependiente', 'independiente', 'desempleado', 'jubilado', 'estudiante']
            if v_lower in valid_values:
                return v_lower
        return v


class EconomicInfoCreateDTO(BaseModel):
    """DTO para crear información económica"""
    employment_situation: EmploymentSituation
    monthly_income: Decimal = Field(..., ge=0, le=50000)
    work_condition: Optional[WorkCondition] = None
    occupation_detail: Optional[str] = Field(None, max_length=200)
    employer_name: Optional[str] = Field(None, max_length=150)
    has_additional_income: bool = False
    additional_income_amount: Optional[Decimal] = Field(None, gt=0, le=50000)
    additional_income_source: Optional[str] = Field(None, max_length=200)
    is_main_applicant: bool = True

    @model_validator(mode='before')
    @classmethod
    def validate_employment_consistency(cls, values):
        employment_situation = values.get('employment_situation')
        work_condition = values.get('work_condition')
        occupation_detail = values.get('occupation_detail')
        
        if employment_situation in [EmploymentSituation.DEPENDENT, EmploymentSituation.INDEPENDENT]:
            if not work_condition:
                raise ValueError('La condición de trabajo es obligatoria para empleados')
            if not occupation_detail:
                raise ValueError('El detalle de ocupación es obligatorio para empleados')
        
        has_additional_income = values.get('has_additional_income', False)
        additional_income_amount = values.get('additional_income_amount')
        additional_income_source = values.get('additional_income_source')
        
        if has_additional_income:
            if not additional_income_amount:
                raise ValueError('El monto de ingreso adicional es obligatorio')
            if not additional_income_source:
                raise ValueError('La fuente de ingreso adicional es obligatoria')
        
        return values


# ===== DTO PARA DATOS DE USUARIO (CONTROL INTERNO) =====

class UserDataDTO(BaseModel):
    """DTO para datos de usuario - Solo para control interno, NO va en la solicitud"""
    dni: str = Field(..., min_length=8, max_length=8)
    names: str = Field(..., min_length=2, max_length=100)  
    surnames: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    birth_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)  # Notas internas

    @validator('dni')
    def validate_dni(cls, v):
        if not v.isdigit() or len(v) != 8:
            raise ValueError('DNI debe tener exactamente 8 dígitos')
        return v

# ===== DTOs DE SOLICITUD COMPLETA =====

class TechoPropioApplicationCreateDTO(BaseModel):
    """DTO para crear solicitud completa Techo Propio"""
    
    # ✅ NUEVOS CAMPOS: Información de registro
    convocation_code: str = Field(..., min_length=5, max_length=50, description="Código de convocatoria")
    
    # ✅ NUEVA LÓGICA: Datos de usuario separados (control interno)
    user_data: UserDataDTO = Field(..., description="Datos del usuario para control interno")
    
    # ✅ CAMBIO: main_applicant ahora es head_of_family (jefe de familia real)
    head_of_family: ApplicantCreateDTO = Field(..., description="Jefe de familia (va en la solicitud)")
    property_info: PropertyInfoCreateDTO
    head_of_family_economic: EconomicInfoCreateDTO = Field(..., description="Info económica del jefe de familia")
    spouse: Optional[ApplicantCreateDTO] = None
    spouse_economic: Optional[EconomicInfoCreateDTO] = None
    household_members: List[HouseholdMemberCreateDTO] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def validate_application_consistency(cls, values):
        head_of_family = values.get('head_of_family')
        spouse = values.get('spouse')
        spouse_economic = values.get('spouse_economic')
        household_members = values.get('household_members', [])
        user_data = values.get('user_data')
        
        # ✅ VALIDACIÓN: Debe tener jefe de familia
        if not head_of_family:
            raise ValueError('El jefe de familia es obligatorio')
        
        # ✅ VALIDACIÓN: Debe tener datos de usuario
        if not user_data:
            raise ValueError('Los datos del usuario son obligatorios')
        
        # Validar consistencia de cónyuge
        if spouse:
            if spouse.get('is_main_applicant', False):
                raise ValueError('El cónyuge no puede ser marcado como jefe de familia')
            
            # Verificar que el jefe de familia esté casado o conviviendo
            if head_of_family and head_of_family.get('civil_status') not in [CivilStatus.MARRIED, CivilStatus.COHABITING]:
                raise ValueError('Solo jefes de familia casados o convivientes pueden incluir cónyuge')
        
        # Si tiene cónyuge, debe tener información económica del cónyuge
        if spouse and not spouse_economic:
            raise ValueError('La información económica del cónyuge es obligatoria')
        
        if spouse_economic and not spouse:
            raise ValueError('No puede tener información económica del cónyuge sin cónyuge')
        
        # Validar límite de miembros familiares
        max_members = VALIDATION_CONSTANTS["MAX_HOUSEHOLD_MEMBERS"]
        if len(household_members) > max_members:
            raise ValueError(f'No se pueden registrar más de {max_members} miembros familiares')
        
        # ✅ VALIDAR DNIs ÚNICOS: Incluir datos de usuario, jefe de familia, cónyuge y carga familiar
        # ✅ PERMITIR duplicación entre user_data y head_of_family (mismo solicitante)
        all_dnis = set()
        head_family_dni = None
        
        # DNI del usuario (control interno) 
        if user_data and user_data.get('dni'):
            user_dni = user_data['dni']
            all_dnis.add(user_dni)
        
        # DNI del jefe de familia (head_of_family)
        head_family_dni = None
        if head_of_family and head_of_family.get('document_number'):
            head_family_dni = head_of_family['document_number']
            # ✅ PERMITIR que user_data y head_of_family tengan el mismo DNI (mismo solicitante)
            if head_family_dni in all_dnis:
                # Solo es error si NO es el mismo DNI del usuario
                if user_data and user_data.get('dni') != head_family_dni:
                    raise ValueError(f'DNI duplicado: {head_family_dni}')
            all_dnis.add(head_family_dni)
        
        # DNI del cónyuge
        if spouse:
            spouse_dni = spouse.get('document_number') if isinstance(spouse, dict) else spouse.document_number
            if spouse_dni in all_dnis:
                raise ValueError(f'DNI duplicado: {spouse_dni}')
            all_dnis.add(spouse_dni)
        
        # DNIs de carga familiar
        for member in household_members:
            member_dni = member.get('document_number') if isinstance(member, dict) else member.document_number
            if member_dni in all_dnis:
                # ✅ PERMITIR que el jefe de familia aparezca también en household_members
                if head_family_dni and member_dni == head_family_dni:
                    continue  # Permitir duplicación del jefe de familia
                # ✅ PERMITIR que el usuario (control interno) aparezca en household_members 
                if user_data and user_data.get('dni') == member_dni:
                    continue  # Permitir duplicación del usuario
                raise ValueError(f'DNI duplicado: {member_dni}')
            all_dnis.add(member_dni)
        
        return values


class TechoPropioApplicationUpdateDTO(BaseModel):
    """DTO para actualizar solicitud existente"""
    user_data: Optional[UserDataDTO] = None
    head_of_family: Optional[ApplicantCreateDTO] = None
    property_info: Optional[PropertyInfoCreateDTO] = None
    head_of_family_economic: Optional[EconomicInfoCreateDTO] = None
    spouse: Optional[ApplicantCreateDTO] = None
    spouse_economic: Optional[EconomicInfoCreateDTO] = None
    household_members: Optional[List[HouseholdMemberCreateDTO]] = None

    @model_validator(mode='before')
    @classmethod
    def validate_at_least_one_field(cls, values):
        if not any(values.values()):
            raise ValueError('Debe proporcionar al menos un campo para actualizar')
        return values


# ===== DTOs DE RESPUESTA =====

class UserDataResponseDTO(BaseModel):
    """DTO de respuesta para datos de usuario - Solo para control interno"""
    dni: str
    names: str
    surnames: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[date] = None
    notes: Optional[str] = None

class ApplicantResponseDTO(BaseModel):
    """DTO de respuesta para solicitante"""
    id: str
    document_type: DocumentType
    document_number: str
    first_name: str
    paternal_surname: str
    maternal_surname: str
    full_name: str
    birth_date: date
    age: int
    civil_status: CivilStatus
    education_level: EducationLevel
    occupation: Optional[str]
    disability_type: DisabilityType
    disability_is_permanent: bool = False  # ✅ NUEVO: ¿La discapacidad es permanente?
    disability_is_severe: bool = False  # ✅ NUEVO: ¿La discapacidad es severa?
    is_main_applicant: bool
    phone_number: Optional[str]
    email: Optional[str]

    # ✅ NUEVO: Dirección actual (se copia desde property_info para compatibilidad con frontend)
    current_address: Optional[Dict[str, Any]] = None

    reniec_validated: bool
    reniec_validation_date: Optional[datetime]

    class Config:
        from_attributes = True


class PropertyInfoResponseDTO(BaseModel):
    """DTO de respuesta para información del predio"""
    id: str
    department: str
    province: str
    district: str
    lote: str
    address: str
    ubigeo_code: Optional[str]
    populated_center: Optional[str]
    manzana: Optional[str]
    sub_lote: Optional[str]
    reference: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    ubigeo_validated: bool
    full_address: str
    short_address: str

    class Config:
        from_attributes = True


class HouseholdMemberResponseDTO(BaseModel):
    """DTO de respuesta para miembro de carga familiar"""
    id: str
    first_name: str
    paternal_surname: str
    maternal_surname: str
    full_name: str
    document_type: DocumentType
    document_number: str
    birth_date: date
    age: int
    relationship: FamilyRelationship
    education_level: Optional[EducationLevel]
    disability_type: DisabilityType
    disability_is_permanent: bool = False  # ✅ NUEVO: ¿La discapacidad es permanente?
    disability_is_severe: bool = False  # ✅ NUEVO: ¿La discapacidad es severa?
    civil_status: CivilStatus
    occupation: Optional[str]
    employment_situation: EmploymentSituation
    work_condition: WorkCondition
    monthly_income: float
    is_dependent: bool

    class Config:
        from_attributes = True


class EconomicInfoResponseDTO(BaseModel):
    """DTO de respuesta para información económica"""
    id: str
    employment_situation: EmploymentSituation
    work_condition: Optional[WorkCondition]
    occupation_detail: Optional[str]
    employer_name: Optional[str]
    monthly_income: Decimal
    has_additional_income: bool
    additional_income_amount: Optional[Decimal]
    additional_income_source: Optional[str]
    total_monthly_income: Decimal
    annual_income: Decimal
    is_main_applicant: bool
    income_level_category: str

    class Config:
        from_attributes = True


class TechoPropioApplicationResponseDTO(BaseModel):
    """DTO de respuesta para solicitud completa"""
    id: str
    application_number: Optional[str]
    status: ApplicationStatus
    
    # ✅ NUEVOS CAMPOS: Información de registro
    registration_date: Optional[datetime] = Field(description="Fecha de registro de la solicitud")
    convocation_code: Optional[str] = Field(description="Código de convocatoria")
    registration_year: Optional[int] = Field(description="Año de registro")
    sequential_number: Optional[int] = Field(description="Número secuencial")
    
    # ✅ NUEVA LÓGICA: Datos de usuario separados
    user_data: Optional[UserDataResponseDTO] = Field(description="Datos del usuario para control interno")
    
    # ✅ CAMBIO: main_applicant ahora es head_of_family
    head_of_family: ApplicantResponseDTO = Field(description="Jefe de familia")
    property_info: PropertyInfoResponseDTO
    head_of_family_economic: EconomicInfoResponseDTO = Field(description="Info económica del jefe de familia")
    spouse: Optional[ApplicantResponseDTO]
    spouse_economic: Optional[EconomicInfoResponseDTO]
    household_members: List[HouseholdMemberResponseDTO]
    
    # Información calculada
    total_household_size: int
    total_family_income: Decimal
    per_capita_income: Decimal
    completion_percentage: float
    priority_score: int
    
    # Fechas importantes
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    decision_date: Optional[datetime]
    
    # Información de procesamiento
    reviewer_id: Optional[str]
    reviewer_comments: Optional[str]
    rejection_reason: Optional[str]
    
    # Metadata
    user_id: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    # Estados de la solicitud
    is_editable: bool
    is_final_status: bool
    can_be_submitted: bool

    class Config:
        from_attributes = True


# ===== DTOs PARA OPERACIONES ESPECÍFICAS =====

class ApplicationStatusUpdateDTO(BaseModel):
    """DTO para cambiar estado de solicitud"""
    new_status: ApplicationStatus
    reviewer_id: Optional[str] = None
    comments: Optional[str] = None
    reason: Optional[str] = None  # Para rechazos

    @model_validator(mode='before')
    @classmethod
    def validate_status_change(cls, values):
        new_status = values.get('new_status')
        reason = values.get('reason')
        reviewer_id = values.get('reviewer_id')
        
        if new_status == ApplicationStatus.REJECTED:
            if not reason:
                raise ValueError('La razón de rechazo es obligatoria')
            if not reviewer_id:
                raise ValueError('El ID del revisor es obligatorio para rechazar')
        
        if new_status in [ApplicationStatus.APPROVED, ApplicationStatus.UNDER_REVIEW]:
            if not reviewer_id:
                raise ValueError('El ID del revisor es obligatorio para esta operación')
        
        return values


class DniValidationRequestDTO(BaseModel):
    """DTO para solicitar validación de DNI"""
    dni: str = Field(..., min_length=8, max_length=8)
    
    @validator('dni')
    def validate_dni_format(cls, v):
        if not v.isdigit():
            raise ValueError('DNI debe contener solo números')
        return v


class DniValidationResponseDTO(BaseModel):
    """DTO de respuesta para validación DNI"""
    dni: str
    is_valid: bool
    full_name: Optional[str] = None
    names: Optional[str] = None
    paternal_surname: Optional[str] = None
    maternal_surname: Optional[str] = None
    birth_date: Optional[str] = None
    error_message: Optional[str] = None
    validation_date: datetime

    class Config:
        from_attributes = True


class ApplicationSearchFiltersDTO(BaseModel):
    """DTO para filtros de búsqueda de solicitudes"""
    search_term: Optional[str] = None  # Búsqueda por texto libre
    status: Optional[ApplicationStatus] = None
    department: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    user_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    application_number: Optional[str] = None
    dni: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_income: Optional[Decimal] = None
    max_income: Optional[Decimal] = None
    min_monthly_income: Optional[Decimal] = None  # Alias para compatibilidad
    max_monthly_income: Optional[Decimal] = None  # Alias para compatibilidad
    min_household_size: Optional[int] = None
    max_household_size: Optional[int] = None
    min_household_members: Optional[int] = None  # Alias para compatibilidad
    max_household_members: Optional[int] = None  # Alias para compatibilidad
    has_spouse: Optional[bool] = None
    has_disability: Optional[bool] = None
    priority_level: Optional[str] = None  # 'high', 'medium', 'low'
    min_priority_score: Optional[float] = None
    max_priority_score: Optional[float] = None

    # Paginación
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field('created_at', pattern=r'^(created_at|updated_at|submitted_at|priority_score|total_income)$')
    sort_order: str = Field('desc', pattern=r'^(asc|desc)$')

    @validator('dni')
    def validate_dni_search(cls, v):
        if v and (len(v) != 8 or not v.isdigit()):
            raise ValueError('DNI debe tener exactamente 8 dígitos')
        return v


class ApplicationListResponseDTO(BaseModel):
    """DTO de respuesta para lista paginada de solicitudes"""
    applications: List[TechoPropioApplicationResponseDTO]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    class Config:
        from_attributes = True


class ApplicantValidationDTO(BaseModel):
    """DTO para validación completa de datos de solicitante"""
    document_number: str = Field(..., min_length=8, max_length=12)
    first_name: str = Field(..., min_length=2, max_length=50)
    paternal_surname: str = Field(..., min_length=2, max_length=50)
    maternal_surname: Optional[str] = Field(None, min_length=2, max_length=50)
    birth_date: Optional[date] = None
    
    @validator('document_number')
    def validate_document_number(cls, v):
        if not v.isdigit():
            raise ValueError('El número de documento debe contener solo dígitos')
        return v


# DTO genérico para respuestas paginadas
from typing import TypeVar, Generic
T = TypeVar('T')

class PaginatedResponseDTO(BaseModel, Generic[T]):
    """DTO genérico para respuestas paginadas"""
    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    @validator('total_pages', pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        total_count = values.get('total_count', 0)
        page_size = values.get('page_size', 1)
        return (total_count + page_size - 1) // page_size if page_size > 0 else 0
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        return self.page > 1