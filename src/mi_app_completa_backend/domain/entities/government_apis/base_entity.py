"""
Entidad base para respuestas de APIs Gubernamentales
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Tipos de documentos soportados"""
    DNI = "dni"
    RUC = "ruc"
    CE = "carnet_extranjeria"
    PASAPORTE = "pasaporte"
    RUC_NATURAL = "ruc_natural"  # RUC de persona natural (10...)
    RUC_JURIDICO = "ruc_juridico"  # RUC de persona jurídica (20...)


class GovernmentAPIResponse(BaseModel):
    """Respuesta base para todas las APIs gubernamentales"""
    
    success: bool = Field(..., description="Indica si la consulta fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    data: Optional[Any] = Field(None, description="Datos obtenidos de la consulta")
    fuente: Optional[str] = Field(None, description="Fuente de la información (API utilizada)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Momento de la consulta")
    cache_hit: bool = Field(default=False, description="Indica si el resultado proviene del caché")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        from_attributes = True


class APIProviderEnum(str, Enum):
    """Proveedores de APIs disponibles"""
    RENIEC = "reniec"
    SUNAT = "sunat"
    SUNARP = "sunarp"
    MIGRACIONES = "migraciones"
    ESSALUD = "essalud"
