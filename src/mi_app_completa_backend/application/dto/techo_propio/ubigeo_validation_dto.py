"""
DTOs para validación UBIGEO y ubicaciones geográficas
Maneja entrada y salida de datos para servicios de ubicación
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class UbigeoValidationRequestDTO(BaseModel):
    """DTO para solicitud de validación UBIGEO"""
    ubigeo_code: str = Field(
        ...,
        description="Código UBIGEO de 6 dígitos",
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )
    
    @validator('ubigeo_code')
    def validate_ubigeo_format(cls, v):
        if not v.isdigit():
            raise ValueError('El código UBIGEO debe contener solo números')
        if len(v) != 6:
            raise ValueError('El código UBIGEO debe tener exactamente 6 dígitos')
        return v


class LocationNamesValidationRequestDTO(BaseModel):
    """DTO para validación por nombres de ubicación"""
    department: str = Field(
        ...,
        description="Nombre del departamento",
        min_length=2,
        max_length=50
    )
    province: str = Field(
        ...,
        description="Nombre de la provincia",
        min_length=2,
        max_length=50
    )
    district: str = Field(
        ...,
        description="Nombre del distrito",
        min_length=2,
        max_length=50
    )
    
    @validator('department', 'province', 'district')
    def validate_names(cls, v):
        if not v or not v.strip():
            raise ValueError('Los nombres de ubicación no pueden estar vacíos')
        return v.strip().upper()


class CoordinatesValidationRequestDTO(BaseModel):
    """DTO para validación por coordenadas"""
    latitude: float = Field(
        ...,
        description="Latitud",
        ge=-90.0,
        le=90.0
    )
    longitude: float = Field(
        ...,
        description="Longitud",
        ge=-180.0,
        le=180.0
    )
    max_distance_km: Optional[float] = Field(
        5.0,
        description="Distancia máxima de búsqueda en kilómetros",
        ge=0.1,
        le=50.0
    )


class LocationSearchRequestDTO(BaseModel):
    """DTO para búsqueda de ubicaciones"""
    search_term: str = Field(
        ...,
        description="Término de búsqueda",
        min_length=2,
        max_length=100
    )
    limit: Optional[int] = Field(
        10,
        description="Límite de resultados",
        ge=1,
        le=50
    )
    
    @validator('search_term')
    def validate_search_term(cls, v):
        if not v or not v.strip():
            raise ValueError('El término de búsqueda no puede estar vacío')
        return v.strip()


class GeographicDataDTO(BaseModel):
    """DTO para datos geográficos detallados"""
    department_code: Optional[str] = Field(None, description="Código del departamento")
    province_code: Optional[str] = Field(None, description="Código de la provincia")
    district_code: Optional[str] = Field(None, description="Código del distrito")
    altitude: Optional[float] = Field(None, description="Altitud en metros")
    latitude: Optional[float] = Field(None, description="Latitud")
    longitude: Optional[float] = Field(None, description="Longitud")
    surface_km2: Optional[float] = Field(None, description="Superficie en km²")
    population: Optional[int] = Field(None, description="Población estimada")
    distance_km: Optional[float] = Field(None, description="Distancia en km (para búsquedas por coordenadas)")


class UbigeoValidationResponseDTO(BaseModel):
    """DTO para respuesta de validación UBIGEO"""
    is_valid: bool = Field(..., description="Indica si el UBIGEO es válido")
    ubigeo_code: Optional[str] = Field(None, description="Código UBIGEO validado")
    department: Optional[str] = Field(None, description="Nombre del departamento")
    province: Optional[str] = Field(None, description="Nombre de la provincia")
    district: Optional[str] = Field(None, description="Nombre del distrito")
    validation_errors: Optional[List[str]] = Field(None, description="Lista de errores de validación")
    geographic_data: Optional[GeographicDataDTO] = Field(None, description="Datos geográficos adicionales")
    validated_at: datetime = Field(default_factory=datetime.now, description="Timestamp de validación")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LocationHierarchyDTO(BaseModel):
    """DTO para jerarquía de ubicaciones"""
    ubigeo_code: str = Field(..., description="Código UBIGEO")
    department: str = Field(..., description="Departamento")
    province: str = Field(..., description="Provincia")
    district: str = Field(..., description="Distrito")
    full_name: str = Field(..., description="Nombre completo de la ubicación")
    geographic_data: Optional[GeographicDataDTO] = Field(None, description="Datos geográficos")


class DepartmentListDTO(BaseModel):
    """DTO para lista de departamentos"""
    departments: List[str] = Field(..., description="Lista de departamentos")
    total_count: int = Field(..., description="Total de departamentos")


class ProvinceListDTO(BaseModel):
    """DTO para lista de provincias"""
    department: str = Field(..., description="Departamento padre")
    provinces: List[str] = Field(..., description="Lista de provincias")
    total_count: int = Field(..., description="Total de provincias")


class DistrictListDTO(BaseModel):
    """DTO para lista de distritos"""
    department: str = Field(..., description="Departamento padre")
    province: str = Field(..., description="Provincia padre")
    districts: List[str] = Field(..., description="Lista de distritos")
    total_count: int = Field(..., description="Total de distritos")


class LocationSearchResultDTO(BaseModel):
    """DTO para resultado de búsqueda de ubicaciones"""
    results: List[LocationHierarchyDTO] = Field(..., description="Resultados de búsqueda")
    search_term: str = Field(..., description="Término de búsqueda usado")
    total_found: int = Field(..., description="Total de resultados encontrados")
    search_performed_at: datetime = Field(default_factory=datetime.now, description="Timestamp de búsqueda")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UbigeoStatisticsDTO(BaseModel):
    """DTO para estadísticas de UBIGEO"""
    total_departments: int = Field(..., description="Total de departamentos")
    total_provinces: int = Field(..., description="Total de provincias")
    total_districts: int = Field(..., description="Total de distritos")
    most_used_departments: List[Dict[str, Any]] = Field(..., description="Departamentos más utilizados")
    geographic_coverage: Dict[str, Any] = Field(..., description="Cobertura geográfica")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp de generación")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkUbigeoValidationRequestDTO(BaseModel):
    """DTO para validación de múltiples UBIGEOs"""
    ubigeo_codes: List[str] = Field(
        ...,
        description="Lista de códigos UBIGEO para validar",
        min_items=1,
        max_items=100
    )
    include_geographic_data: Optional[bool] = Field(
        True,
        description="Incluir datos geográficos en la respuesta"
    )
    
    @validator('ubigeo_codes')
    def validate_ubigeo_codes(cls, v):
        for code in v:
            if not code or len(code) != 6 or not code.isdigit():
                raise ValueError(f'Código UBIGEO inválido: {code}')
        return v


class BulkUbigeoValidationResponseDTO(BaseModel):
    """DTO para respuesta de validación múltiple"""
    results: Dict[str, UbigeoValidationResponseDTO] = Field(
        ...,
        description="Resultados de validación por código UBIGEO"
    )
    total_processed: int = Field(..., description="Total de códigos procesados")
    total_valid: int = Field(..., description="Total de códigos válidos")
    total_invalid: int = Field(..., description="Total de códigos inválidos")
    processing_time_ms: Optional[float] = Field(None, description="Tiempo de procesamiento en milisegundos")
    processed_at: datetime = Field(default_factory=datetime.now, description="Timestamp de procesamiento")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }