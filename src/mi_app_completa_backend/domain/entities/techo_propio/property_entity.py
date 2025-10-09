"""
Entidad PropertyInfo para el módulo Techo Propio
Representa la información del predio donde se construirá la vivienda
"""

from typing import Optional
from dataclasses import dataclass
from .base_entity import TechoPropioBaseEntity


@dataclass
class PropertyInfo(TechoPropioBaseEntity):
    """
    Entidad que representa información del predio para Techo Propio
    Incluye ubicación geográfica y características del terreno
    """
    
    # Campos obligatorios primero
    department: str          # Departamento
    province: str           # Provincia  
    district: str           # Distrito
    lote: str               # Lote
    
    # Campos opcionales después
    ubigeo_code: Optional[str] = None  # Código UBIGEO de 6 dígitos
    populated_center: Optional[str] = None    # Centro poblado
    manzana: Optional[str] = None            # Manzana
    sub_lote: Optional[str] = None           # Sub-lote
    reference: Optional[str] = None          # Referencia de ubicación
    
    # Coordenadas geográficas (opcional)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Validación de ubicación
    ubigeo_validated: bool = False
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        super().__init__()
        self._validate_required_fields()
        self._validate_ubigeo_code()
        self._validate_coordinates()
        
    def _validate_required_fields(self) -> None:
        """Validar campos obligatorios"""
        required_fields = [
            ("departamento", self.department),
            ("provincia", self.province),
            ("distrito", self.district),
            ("lote", self.lote)
        ]
        
        for field_name, value in required_fields:
            if not value or not value.strip():
                raise ValueError(f"El campo {field_name} es obligatorio")
    
    def _validate_ubigeo_code(self) -> None:
        """Validar código UBIGEO si se proporciona"""
        if self.ubigeo_code:
            if len(self.ubigeo_code) != 6:
                raise ValueError("El código UBIGEO debe tener 6 dígitos")
            if not self.ubigeo_code.isdigit():
                raise ValueError("El código UBIGEO debe contener solo números")
    
    def _validate_coordinates(self) -> None:
        """Validar coordenadas geográficas si se proporcionan"""
        if self.latitude is not None:
            if not (-90 <= self.latitude <= 90):
                raise ValueError("La latitud debe estar entre -90 y 90 grados")
                
        if self.longitude is not None:
            if not (-180 <= self.longitude <= 180):
                raise ValueError("La longitud debe estar entre -180 y 180 grados")
    
    @property
    def full_address(self) -> str:
        """Dirección completa del predio"""
        address_parts = []
        
        # Agregar lote y sub-lote
        if self.lote:
            lote_part = f"Lote {self.lote}"
            if self.sub_lote:
                lote_part += f", Sub-lote {self.sub_lote}"
            address_parts.append(lote_part)
        
        # Agregar manzana
        if self.manzana:
            address_parts.append(f"Manzana {self.manzana}")
            
        # Agregar centro poblado
        if self.populated_center:
            address_parts.append(self.populated_center)
            
        # Agregar ubicación política
        address_parts.extend([self.district, self.province, self.department])
        
        return ", ".join(filter(None, address_parts))
    
    @property
    def short_address(self) -> str:
        """Dirección corta para mostrar en listas"""
        parts = []
        if self.lote:
            parts.append(f"Lote {self.lote}")
        if self.manzana:
            parts.append(f"Mz. {self.manzana}")
        parts.append(self.district)
        
        return ", ".join(parts)
    
    def set_coordinates(self, latitude: float, longitude: float) -> None:
        """Establecer coordenadas geográficas"""
        self.latitude = latitude
        self.longitude = longitude
        self._validate_coordinates()
        self.update_timestamp()
    
    def set_ubigeo_code(self, ubigeo_code: str) -> None:
        """Establecer y validar código UBIGEO"""
        self.ubigeo_code = ubigeo_code
        self._validate_ubigeo_code()
        self.ubigeo_validated = True
        self.update_timestamp()
    
    def has_coordinates(self) -> bool:
        """Verificar si tiene coordenadas geográficas"""
        return self.latitude is not None and self.longitude is not None
    
    def is_urban_area(self) -> bool:
        """Verificar si está en zona urbana (basado en si tiene manzana)"""
        return bool(self.manzana and self.manzana.strip())
    
    def update_reference(self, reference: str) -> None:
        """Actualizar referencia de ubicación"""
        self.reference = reference
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "department": self.department,
            "province": self.province,
            "district": self.district,
            "ubigeo_code": self.ubigeo_code,
            "populated_center": self.populated_center,
            "manzana": self.manzana,
            "lote": self.lote,
            "sub_lote": self.sub_lote,
            "reference": self.reference,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "ubigeo_validated": self.ubigeo_validated,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PropertyInfo':
        """Crear instancia desde diccionario"""
        return cls(
            department=data["department"],
            province=data["province"],
            district=data["district"],
            lote=data.get("lote", ""),
            ubigeo_code=data.get("ubigeo_code"),
            populated_center=data.get("populated_center"),
            manzana=data.get("manzana"),
            sub_lote=data.get("sub_lote"),
            reference=data.get("reference"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            ubigeo_validated=data.get("ubigeo_validated", False)
        )