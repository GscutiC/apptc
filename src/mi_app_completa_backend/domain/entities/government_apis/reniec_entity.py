"""
Entidad para datos de RENIEC (DNI)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class DniData(BaseModel):
    """Modelo de datos para información de persona por DNI"""
    
    dni: str = Field(..., description="Número de DNI (8 dígitos)", min_length=8, max_length=8)
    nombres: str = Field(..., description="Nombres de la persona")
    apellido_paterno: str = Field(..., description="Apellido paterno")
    apellido_materno: str = Field(..., description="Apellido materno")
    apellidos: str = Field(..., description="Apellidos completos")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo (generado)")
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento")
    estado_civil: Optional[str] = Field(default="SOLTERO", description="Estado civil")
    ubigeo: Optional[str] = Field(None, description="Código de ubigeo")
    direccion: Optional[str] = Field(None, description="Dirección de domicilio")
    restricciones: Optional[str] = Field(None, description="Restricciones del documento")
    
    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v: str) -> str:
        """Validar formato del DNI"""
        if not v:
            raise ValueError("DNI no puede estar vacío")
        
        # Remover espacios
        v = v.strip()
        
        # Validar longitud
        if len(v) != 8:
            raise ValueError("DNI debe tener exactamente 8 dígitos")
        
        # Validar que sea numérico
        if not v.isdigit():
            raise ValueError("DNI debe contener solo números")
        
        return v
    
    @field_validator('apellidos', mode='before')
    @classmethod
    def generate_apellidos(cls, v, info):
        """Generar apellidos completos si no se proporciona"""
        if v:
            return v
        
        # Obtener datos del contexto
        data = info.data
        paterno = data.get('apellido_paterno', '')
        materno = data.get('apellido_materno', '')
        
        return f"{paterno} {materno}".strip()
    
    def model_post_init(self, __context):
        """Generar campos derivados después de la inicialización"""
        if not self.nombre_completo:
            self.nombre_completo = f"{self.apellidos} {self.nombres}".strip()
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "dni": "12345678",
                "nombres": "JUAN CARLOS",
                "apellido_paterno": "PEREZ",
                "apellido_materno": "GARCIA",
                "apellidos": "PEREZ GARCIA",
                "nombre_completo": "PEREZ GARCIA JUAN CARLOS",
                "fecha_nacimiento": "01/01/1990",
                "estado_civil": "SOLTERO",
                "ubigeo": "150101",
                "direccion": "AV. EJEMPLO 123",
                "restricciones": None
            }
        }


class DniConsultaResponse(BaseModel):
    """Respuesta de consulta DNI"""
    
    success: bool = Field(..., description="Indica si la consulta fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    data: Optional[DniData] = Field(None, description="Datos de la persona")
    fuente: Optional[str] = Field(None, description="Fuente de la información")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Momento de la consulta")
    cache_hit: bool = Field(default=False, description="Si proviene del caché")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Consulta exitosa",
                "data": {
                    "dni": "12345678",
                    "nombres": "JUAN CARLOS",
                    "apellido_paterno": "PEREZ",
                    "apellido_materno": "GARCIA",
                    "apellidos": "PEREZ GARCIA",
                    "nombre_completo": "PEREZ GARCIA JUAN CARLOS"
                },
                "fuente": "API Real RENIEC",
                "timestamp": "2025-10-08T10:30:00",
                "cache_hit": False
            }
        }
