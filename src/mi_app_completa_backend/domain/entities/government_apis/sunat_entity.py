"""
Entidad para datos de SUNAT (RUC)
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RucData(BaseModel):
    """Modelo de datos para información de empresa por RUC"""
    
    ruc: str = Field(..., description="Número de RUC (11 dígitos)", min_length=11, max_length=11)
    razon_social: str = Field(..., description="Razón social o nombre comercial")
    nombre_comercial: Optional[str] = Field(None, description="Nombre comercial alternativo")
    estado: str = Field(default="ACTIVO", description="Estado del contribuyente")
    condicion: Optional[str] = Field(None, description="Condición del contribuyente")
    tipo_empresa: Optional[str] = Field(None, description="Tipo de empresa o contribuyente")
    tipo_contribuyente: Optional[str] = Field(None, description="Tipo específico de contribuyente")
    
    # Ubicación
    direccion: Optional[str] = Field(None, description="Dirección fiscal completa")
    ubigeo: Optional[str] = Field(None, description="Código de ubigeo")
    departamento: Optional[str] = Field(None, description="Departamento")
    provincia: Optional[str] = Field(None, description="Provincia")
    distrito: Optional[str] = Field(None, description="Distrito")
    
    # Información adicional
    fecha_inscripcion: Optional[str] = Field(None, description="Fecha de inscripción en SUNAT")
    fecha_inicio_actividades: Optional[str] = Field(None, description="Fecha de inicio de actividades")
    actividad_economica: Optional[str] = Field(None, description="Actividad económica principal")
    sistema_contabilidad: Optional[str] = Field(None, description="Sistema de contabilidad")
    tipo_facturacion: Optional[str] = Field(None, description="Tipo de facturación electrónica")
    comercio_exterior: Optional[str] = Field(None, description="Condición de comercio exterior")
    
    # Contacto
    telefono: Optional[str] = Field(None, description="Teléfono de contacto")
    email: Optional[str] = Field(None, description="Email de contacto")
    
    # Información legal
    representante_legal: Optional[str] = Field(None, description="Representante legal")
    trabajadores: Optional[int] = Field(default=0, description="Cantidad de trabajadores")
    
    @field_validator('ruc')
    @classmethod
    def validate_ruc(cls, v: str) -> str:
        """Validar formato del RUC"""
        if not v:
            raise ValueError("RUC no puede estar vacío")
        
        # Remover espacios
        v = v.strip()
        
        # Validar longitud
        if len(v) != 11:
            raise ValueError("RUC debe tener exactamente 11 dígitos")
        
        # Validar que sea numérico
        if not v.isdigit():
            raise ValueError("RUC debe contener solo números")
        
        # Validar que comience con dígitos válidos
        tipo_contrib = v[:2]
        tipos_validos = ["10", "15", "17", "20"]
        
        if tipo_contrib not in tipos_validos:
            raise ValueError(
                f"RUC debe comenzar con {', '.join(tipos_validos)}. "
                f"10: Persona Natural, 15: Sujeto no domiciliado, "
                f"17: Gobierno/Entidad pública, 20: Persona Jurídica"
            )
        
        return v
    
    def get_tipo_contribuyente_descripcion(self) -> str:
        """Obtener descripción del tipo de contribuyente según RUC"""
        if len(self.ruc) < 2:
            return "Desconocido"
        
        tipo = self.ruc[:2]
        tipos = {
            "10": "Persona Natural",
            "15": "Sujeto No Domiciliado",
            "17": "Gobierno/Entidad Pública",
            "20": "Persona Jurídica"
        }
        return tipos.get(tipo, "Desconocido")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "ruc": "20123456789",
                "razon_social": "EMPRESA EJEMPLO S.A.C.",
                "nombre_comercial": "EMPRESA EJEMPLO",
                "estado": "ACTIVO",
                "condicion": "HABIDO",
                "tipo_empresa": "SOCIEDAD ANONIMA CERRADA",
                "direccion": "AV. PRINCIPAL 456",
                "departamento": "LIMA",
                "provincia": "LIMA",
                "distrito": "MIRAFLORES",
                "fecha_inscripcion": "01/01/2020",
                "actividad_economica": "COMERCIO AL POR MAYOR",
                "telefono": "987654321",
                "email": "contacto@ejemplo.com",
                "representante_legal": "JUAN PEREZ GARCIA",
                "trabajadores": 50
            }
        }


class RucConsultaResponse(BaseModel):
    """Respuesta de consulta RUC"""
    
    success: bool = Field(..., description="Indica si la consulta fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo del resultado")
    data: Optional[RucData] = Field(None, description="Datos de la empresa")
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
                    "ruc": "20123456789",
                    "razon_social": "EMPRESA EJEMPLO S.A.C.",
                    "estado": "ACTIVO",
                    "condicion": "HABIDO"
                },
                "fuente": "API Real SUNAT",
                "timestamp": "2025-10-08T10:30:00",
                "cache_hit": False
            }
        }
