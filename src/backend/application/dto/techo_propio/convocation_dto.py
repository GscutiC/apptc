"""
DTOs para gestión de convocatorias Techo Propio
"""

from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# ==================== ENUMS ====================

class ConvocationStatus(str, Enum):
    """Estados de convocatoria"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UPCOMING = "upcoming"
    CURRENT = "current"
    EXPIRED = "expired"


# ==================== REQUEST DTOs ====================

class ConvocationCreateDTO(BaseModel):
    """DTO para crear nueva convocatoria"""
    code: str = Field(..., min_length=10, max_length=20, description="Código único de convocatoria")
    title: str = Field(..., min_length=5, max_length=200, description="Título descriptivo")
    description: Optional[str] = Field(None, max_length=1000, description="Descripción detallada")
    start_date: date = Field(..., description="Fecha de inicio")
    end_date: date = Field(..., description="Fecha de fin")
    is_active: bool = Field(default=True, description="Si está activa")
    is_published: bool = Field(default=False, description="Si está publicada")
    max_applications: Optional[int] = Field(None, gt=0, description="Límite de solicitudes")
    
    @validator('code')
    def validate_code_format(cls, v):
        """Validar formato del código"""
        if not v.startswith('CONV-'):
            raise ValueError('El código debe comenzar con "CONV-"')
        
        parts = v.split('-')
        if len(parts) != 3:
            raise ValueError('Formato debe ser CONV-YYYY-XX')
        
        try:
            year = int(parts[1])
            seq = int(parts[2])
            if year < 2020 or year > 2030:
                raise ValueError('Año debe estar entre 2020 y 2030')
            if seq < 1 or seq > 99:
                raise ValueError('Número secuencial debe estar entre 01 y 99')
        except ValueError:
            raise ValueError('Formato de código inválido')
        
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validar que end_date sea posterior a start_date"""
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('La fecha de fin debe ser posterior a la de inicio')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validar título"""
        if not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v.strip()


class ConvocationUpdateDTO(BaseModel):
    """DTO para actualizar convocatoria existente"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    max_applications: Optional[int] = Field(None, gt=0)
    
    @validator('title')
    def validate_title(cls, v):
        """Validar título si se proporciona"""
        if v is not None and not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v.strip() if v else v


class ConvocationQueryDTO(BaseModel):
    """DTO para consultas de convocatorias"""
    skip: int = Field(default=0, ge=0, description="Registros a omitir")
    limit: int = Field(default=50, ge=1, le=100, description="Límite de registros")
    include_inactive: bool = Field(default=False, description="Incluir inactivas")
    year: Optional[int] = Field(None, ge=2020, le=2030, description="Filtrar por año")
    status: Optional[ConvocationStatus] = Field(None, description="Filtrar por estado")
    search: Optional[str] = Field(None, min_length=2, max_length=50, description="Búsqueda por texto")


class ConvExtendDeadlineDTO(BaseModel):
    """DTO para extender fecha límite"""
    new_end_date: date = Field(..., description="Nueva fecha de fin")
    
    @validator('new_end_date')
    def validate_future_date(cls, v):
        """Validar que sea fecha futura"""
        if v <= date.today():
            raise ValueError('La nueva fecha debe ser futura')
        return v


# ==================== RESPONSE DTOs ====================

class ConvocationResponseDTO(BaseModel):
    """DTO de respuesta para convocatoria"""
    id: str
    code: str
    title: str
    description: Optional[str]
    start_date: date
    end_date: date
    is_active: bool
    is_published: bool
    max_applications: Optional[int]
    year: int
    sequential_number: Optional[int]
    
    # Estados calculados
    status_display: str
    is_current: bool
    is_upcoming: bool
    is_expired: bool
    days_remaining: Optional[int]
    
    # Estadísticas (opcional)
    applications_count: Optional[int] = None
    
    # Metadatos
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: str
    
    class Config:
        from_attributes = True


class ConvocationListResponseDTO(BaseModel):
    """DTO de respuesta para lista paginada"""
    convocations: List[ConvocationResponseDTO]
    total: int
    skip: int
    limit: int
    has_next: bool
    has_previous: bool


class ConvocationStatisticsDTO(BaseModel):
    """DTO para estadísticas de convocatoria"""
    convocation_code: str
    total_applications: int
    applications_by_status: dict
    average_priority_score: Optional[float]
    completion_rate: float
    applications_per_day: dict
    
    # Información adicional
    start_date: date
    end_date: date
    days_active: int
    days_remaining: Optional[int]


class ConvocationGeneralStatsDTO(BaseModel):
    """DTO para estadísticas generales"""
    total_convocations: int
    active_convocations: int
    current_convocations: int
    published_convocations: int
    total_applications_all_convocations: int
    
    # Por año
    convocations_by_year: dict
    applications_by_year: dict
    
    # Tendencias
    most_active_convocation: Optional[str]
    latest_convocation: Optional[ConvocationResponseDTO]


# ==================== UTILITY DTOs ====================

class ConvocationOptionDTO(BaseModel):
    """DTO simplificado para dropdowns y selects"""
    value: str  # código de convocatoria
    label: str  # título para mostrar
    is_active: bool
    is_current: bool
    description: Optional[str] = None
    
    @classmethod
    def from_convocation(cls, convocation) -> 'ConvocationOptionDTO':
        """Crear desde entidad Convocation"""
        return cls(
            value=convocation.code,
            label=f"{convocation.code} - {convocation.title}",
            is_active=convocation.is_active,
            is_current=convocation.is_current,
            description=convocation.description
        )


class ConvBulkOperationDTO(BaseModel):
    """DTO para operaciones masivas"""
    convocation_ids: List[str] = Field(..., min_items=1, description="IDs de convocatorias")
    operation: str = Field(..., description="Operación a realizar")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validar operación"""
        allowed = ['activate', 'deactivate', 'publish', 'unpublish', 'delete']
        if v not in allowed:
            raise ValueError(f'Operación debe ser una de: {", ".join(allowed)}')
        return v


class ConvBulkOperationResultDTO(BaseModel):
    """DTO de resultado de operación masiva"""
    operation: str
    total_requested: int
    successful: int
    failed: int
    errors: List[str] = []