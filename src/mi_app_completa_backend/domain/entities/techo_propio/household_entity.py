"""
Entidad HouseholdMember para el módulo Techo Propio  
Representa a los miembros de la carga familiar del solicitante
"""

from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass
from .base_entity import TechoPropioBaseEntity
from ...value_objects.techo_propio import (
    DocumentType, EducationLevel, FamilyRelationship, 
    DisabilityType, VALIDATION_CONSTANTS
)


@dataclass
class HouseholdMember(TechoPropioBaseEntity):
    """
    Entidad que representa un miembro de la carga familiar
    Incluye hijos, padres, hermanos y otros dependientes
    """
    
    # Información personal básica
    first_name: str
    paternal_surname: str
    maternal_surname: str
    document_type: DocumentType
    document_number: str
    birth_date: date
    
    # Relación familiar
    relationship: FamilyRelationship
    
    # Información adicional
    education_level: Optional[EducationLevel] = None
    disability_type: DisabilityType = DisabilityType.NONE
    
    # Metadata
    is_dependent: bool = True  # Si es dependiente económicamente
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        super().__init__()
        self._validate_names()
        self._validate_document_number()
        self._validate_birth_date()
        self._validate_relationship_age_consistency()
    
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
    
    def _validate_document_number(self) -> None:
        """Validar número de documento"""
        if not self.document_number:
            raise ValueError("El número de documento es obligatorio")
            
        if self.document_type == DocumentType.DNI:
            if len(self.document_number) != VALIDATION_CONSTANTS["DNI_LENGTH"]:
                raise ValueError(f"El DNI debe tener {VALIDATION_CONSTANTS['DNI_LENGTH']} dígitos")
            if not self.document_number.isdigit():
                raise ValueError("El DNI debe contener solo números")
    
    def _validate_birth_date(self) -> None:
        """Validar fecha de nacimiento"""
        if not self.birth_date:
            raise ValueError("La fecha de nacimiento es obligatoria")
            
        today = date.today()
        if self.birth_date > today:
            raise ValueError("La fecha de nacimiento no puede ser futura")
            
        # Verificar que no sea muy antigua (más de 100 años)
        age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        if age > 100:
            raise ValueError("La edad no puede ser mayor a 100 años")
    
    def _validate_relationship_age_consistency(self) -> None:
        """Validar consistencia entre relación familiar y edad"""
        age = self.age
        
        # Validaciones específicas por tipo de relación
        if self.relationship == FamilyRelationship.CHILD:
            if age >= 25:  # Hijos dependientes típicamente menores a 25
                # No es error, pero podría necesitar justificación
                pass
        elif self.relationship == FamilyRelationship.PARENT:
            if age < 40:  # Padres típicamente mayores a 40
                # No es error crítico, familias jóvenes pueden existir
                pass
        elif self.relationship == FamilyRelationship.GRANDPARENT:
            if age < 50:
                # Abuelos típicamente mayores a 50
                pass
        elif self.relationship == FamilyRelationship.GRANDCHILD:
            if age > 18:
                # Nietos dependientes típicamente menores a 18
                pass
    
    @property
    def full_name(self) -> str:
        """Nombre completo del miembro familiar"""
        return f"{self.first_name} {self.paternal_surname} {self.maternal_surname}".strip()
    
    @property
    def age(self) -> int:
        """Edad actual del miembro"""
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def is_minor(self) -> bool:
        """Verificar si es menor de edad"""
        return self.age < 18
    
    def is_student_age(self) -> bool:
        """Verificar si está en edad estudiantil (5-25 años)"""
        return 5 <= self.age <= 25
    
    def has_disability(self) -> bool:
        """Verificar si tiene alguna discapacidad"""
        return self.disability_type != DisabilityType.NONE
    
    def is_potential_dependent(self) -> bool:
        """Verificar si podría ser dependiente económico"""
        # Menores de edad, estudiantes, personas con discapacidad, adultos mayores
        return (
            self.is_minor() or 
            (self.is_student_age() and self.education_level in [
                EducationLevel.PRIMARY_INCOMPLETE,
                EducationLevel.PRIMARY_COMPLETE,
                EducationLevel.SECONDARY_INCOMPLETE,
                EducationLevel.SECONDARY_COMPLETE,
                EducationLevel.TECHNICAL_INCOMPLETE,
                EducationLevel.UNIVERSITY_INCOMPLETE
            ]) or
            self.has_disability() or
            self.age >= 65
        )
    
    def update_education_level(self, education_level: EducationLevel) -> None:
        """Actualizar nivel educativo"""
        self.education_level = education_level
        self.update_timestamp()
    
    def set_dependency_status(self, is_dependent: bool) -> None:
        """Establecer estado de dependencia"""
        self.is_dependent = is_dependent
        self.update_timestamp()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "first_name": self.first_name,
            "paternal_surname": self.paternal_surname,
            "maternal_surname": self.maternal_surname,
            "document_type": self.document_type.value,
            "document_number": self.document_number,
            "birth_date": self.birth_date.isoformat(),
            "relationship": self.relationship.value,
            "education_level": self.education_level.value if self.education_level else None,
            "disability_type": self.disability_type.value,
            "is_dependent": self.is_dependent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HouseholdMember':
        """Crear instancia desde diccionario"""
        return cls(
            first_name=data["first_name"],
            paternal_surname=data["paternal_surname"],
            maternal_surname=data["maternal_surname"],
            document_type=DocumentType(data["document_type"]),
            document_number=data["document_number"],
            birth_date=datetime.fromisoformat(data["birth_date"]).date(),
            relationship=FamilyRelationship(data["relationship"]),
            education_level=EducationLevel(data["education_level"]) if data.get("education_level") else None,
            disability_type=DisabilityType(data.get("disability_type", DisabilityType.NONE.value)),
            is_dependent=data.get("is_dependent", True)
        )