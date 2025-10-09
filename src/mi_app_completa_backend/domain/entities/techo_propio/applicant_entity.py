"""
Entidad Applicant para el módulo Techo Propio
Representa al solicitante principal o cónyuge/conviviente
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass
from .base_entity import TechoPropioBaseEntity
from ...value_objects.techo_propio import (
    DocumentType, CivilStatus, EducationLevel, 
    DisabilityType, VALIDATION_CONSTANTS
)


@dataclass
class Applicant(TechoPropioBaseEntity):
    """
    Entidad que representa a un solicitante del programa Techo Propio
    Puede ser el jefe de familia o el cónyuge/conviviente
    """
    
    # Campos obligatorios primero
    document_type: DocumentType
    document_number: str
    first_name: str
    paternal_surname: str
    maternal_surname: str
    birth_date: date
    civil_status: CivilStatus
    education_level: EducationLevel
    
    # Campos opcionales después
    occupation: Optional[str] = None
    disability_type: DisabilityType = DisabilityType.NONE
    is_main_applicant: bool = True  # True para jefe de familia, False para cónyuge
    phone_number: Optional[str] = None
    email: Optional[str] = None
    
    # Información de validación RENIEC
    reniec_validated: bool = False
    reniec_validation_date: Optional[datetime] = None
    reniec_full_name: Optional[str] = None  # Nombre completo según RENIEC
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        super().__init__()
        self._validate_document_number()
        self._validate_names()
        self._validate_age()
        self._validate_phone()
        
    def _validate_document_number(self) -> None:
        """Validar número de documento"""
        if not self.document_number:
            raise ValueError("El número de documento es obligatorio")
            
        if self.document_type == DocumentType.DNI:
            if len(self.document_number) != VALIDATION_CONSTANTS["DNI_LENGTH"]:
                raise ValueError(f"El DNI debe tener {VALIDATION_CONSTANTS['DNI_LENGTH']} dígitos")
            if not self.document_number.isdigit():
                raise ValueError("El DNI debe contener solo números")
    
    def _validate_names(self) -> None:
        """Validar nombres y apellidos"""
        min_length = VALIDATION_CONSTANTS["MIN_NAME_LENGTH"]
        max_length = VALIDATION_CONSTANTS["MAX_NAME_LENGTH"]
        
        names = [
            ("nombres", self.first_name),
            ("apellido paterno", self.paternal_surname),
            ("apellido materno", self.maternal_surname)
        ]
        
        for field_name, value in names:
            if not value or not value.strip():
                raise ValueError(f"El campo {field_name} es obligatorio")
            if len(value.strip()) < min_length:
                raise ValueError(f"El {field_name} debe tener al menos {min_length} caracteres")
            if len(value.strip()) > max_length:
                raise ValueError(f"El {field_name} no puede exceder {max_length} caracteres")
    
    def _validate_age(self) -> None:
        """Validar edad del solicitante"""
        if not self.birth_date:
            raise ValueError("La fecha de nacimiento es obligatoria")
            
        today = date.today()
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        
        min_age = VALIDATION_CONSTANTS["MIN_AGE"]
        max_age = VALIDATION_CONSTANTS["MAX_AGE"]
        
        if age < min_age:
            raise ValueError(f"El solicitante debe ser mayor de {min_age} años")
        if age > max_age:
            raise ValueError(f"El solicitante no puede ser mayor de {max_age} años")
    
    def _validate_phone(self) -> None:
        """Validar número de teléfono si se proporciona"""
        if self.phone_number:
            # Remover espacios y caracteres especiales
            clean_phone = ''.join(filter(str.isdigit, self.phone_number))
            if len(clean_phone) < 7 or len(clean_phone) > 15:
                raise ValueError("El número de teléfono debe tener entre 7 y 15 dígitos")
    
    @property
    def full_name(self) -> str:
        """Nombre completo del solicitante"""
        return f"{self.first_name} {self.paternal_surname} {self.maternal_surname}".strip()
    
    @property
    def age(self) -> int:
        """Edad actual del solicitante"""
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def mark_as_reniec_validated(self, validated_name: str) -> None:
        """Marcar como validado por RENIEC"""
        self.reniec_validated = True
        self.reniec_validation_date = datetime.utcnow()
        self.reniec_full_name = validated_name
        self.update_timestamp()
    
    def has_disability(self) -> bool:
        """Verificar si la persona tiene alguna discapacidad"""
        return self.disability_type != DisabilityType.NONE
    
    def is_married_or_cohabiting(self) -> bool:
        """Verificar si está casado o convive"""
        return self.civil_status in [CivilStatus.MARRIED, CivilStatus.COHABITING]
    
    def update_contact_info(self, phone: Optional[str] = None, email: Optional[str] = None) -> None:
        """Actualizar información de contacto"""
        if phone is not None:
            self.phone_number = phone
        if email is not None:
            self.email = email
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "document_type": self.document_type.value,
            "document_number": self.document_number,
            "first_name": self.first_name,
            "paternal_surname": self.paternal_surname,
            "maternal_surname": self.maternal_surname,
            "birth_date": self.birth_date.isoformat(),
            "civil_status": self.civil_status.value,
            "education_level": self.education_level.value,
            "occupation": self.occupation,
            "disability_type": self.disability_type.value,
            "is_main_applicant": self.is_main_applicant,
            "phone_number": self.phone_number,
            "email": self.email,
            "reniec_validated": self.reniec_validated,
            "reniec_validation_date": self.reniec_validation_date.isoformat() if self.reniec_validation_date else None,
            "reniec_full_name": self.reniec_full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Applicant':
        """Crear instancia desde diccionario"""
        return cls(
            document_type=DocumentType(data["document_type"]),
            document_number=data["document_number"],
            first_name=data["first_name"],
            paternal_surname=data["paternal_surname"],
            maternal_surname=data["maternal_surname"],
            birth_date=datetime.fromisoformat(data["birth_date"]).date(),
            civil_status=CivilStatus(data["civil_status"]),
            education_level=EducationLevel(data["education_level"]),
            occupation=data.get("occupation"),
            disability_type=DisabilityType(data.get("disability_type", DisabilityType.NONE.value)),
            is_main_applicant=data.get("is_main_applicant", True),
            phone_number=data.get("phone_number"),
            email=data.get("email"),
            reniec_validated=data.get("reniec_validated", False),
            reniec_validation_date=datetime.fromisoformat(data["reniec_validation_date"]) if data.get("reniec_validation_date") else None,
            reniec_full_name=data.get("reniec_full_name")
        )