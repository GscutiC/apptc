"""
DTOs para consultas gubernamentales
Data Transfer Objects para la capa de aplicación
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# DTOs de Request
class DniQueryRequest(BaseModel):
    """Request para consulta de DNI"""
    dni: str = Field(..., description="DNI de 8 dígitos", min_length=8, max_length=8)
    use_cache: bool = Field(default=True, description="Usar caché si está disponible")
    
    class Config:
        json_schema_extra = {
            "example": {
                "dni": "12345678",
                "use_cache": True
            }
        }


class RucQueryRequest(BaseModel):
    """Request para consulta de RUC"""
    ruc: str = Field(..., description="RUC de 11 dígitos", min_length=11, max_length=11)
    use_cache: bool = Field(default=True, description="Usar caché si está disponible")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ruc": "20123456789",
                "use_cache": True
            }
        }


# DTOs de Response simplificados (para APIs públicas)
class PersonaSummaryDTO(BaseModel):
    """Resumen de datos de persona (para respuestas públicas)"""
    dni: str
    nombre_completo: str
    estado_civil: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmpresaSummaryDTO(BaseModel):
    """Resumen de datos de empresa (para respuestas públicas)"""
    ruc: str
    razon_social: str
    estado: str
    tipo_contribuyente: Optional[str] = None
    
    class Config:
        from_attributes = True


# DTOs de respuesta con metadatos
class QueryMetadata(BaseModel):
    """Metadatos de la consulta"""
    timestamp: datetime
    cache_hit: bool
    fuente: Optional[str] = None
    consulted_by: Optional[str] = None  # Usuario que realizó la consulta
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DniQueryResponseDTO(BaseModel):
    """Response completo de consulta DNI"""
    success: bool
    message: str
    data: Optional[dict] = None  # Puede ser DniData o PersonaSummaryDTO
    metadata: QueryMetadata
    
    class Config:
        from_attributes = True


class RucQueryResponseDTO(BaseModel):
    """Response completo de consulta RUC"""
    success: bool
    message: str
    data: Optional[dict] = None  # Puede ser RucData o EmpresaSummaryDTO
    metadata: QueryMetadata
    
    class Config:
        from_attributes = True


# DTO para historial de consultas
class QueryHistoryDTO(BaseModel):
    """Historial de consultas realizadas"""
    id: str
    document_type: str
    document_number: str
    queried_at: datetime
    queried_by: Optional[str] = None
    success: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# DTO para estadísticas
class QueryStatisticsDTO(BaseModel):
    """Estadísticas de consultas"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cache_hits: int = 0
    cache_hit_rate: float = 0.0
    queries_by_provider: dict = {}
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_queries": 100,
                "successful_queries": 95,
                "failed_queries": 5,
                "cache_hits": 60,
                "cache_hit_rate": 0.6,
                "queries_by_provider": {
                    "reniec": 50,
                    "sunat": 50
                }
            }
        }
