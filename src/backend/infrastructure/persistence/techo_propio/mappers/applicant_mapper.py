"""
Mapper para entidad Applicant
Maneja conversión entre Applicant entity y documento MongoDB
"""

from typing import Dict, Any
from datetime import datetime
import logging

from .base_mapper import BaseMapper
from .....domain.entities.techo_propio import Applicant
from .....domain.value_objects.techo_propio import (
    DocumentType, CivilStatus, EducationLevel, DisabilityType
)

logger = logging.getLogger(__name__)


class ApplicantMapper(BaseMapper):
    """Mapper especializado para entidades Applicant"""
    
    @classmethod
    def to_dict(cls, applicant: Applicant) -> Dict[str, Any]:
        """Convertir Applicant a diccionario para MongoDB"""
        try:
            return {
                "id": applicant.id,
                "document_type": cls.safe_enum_to_value(applicant.document_type),
                "document_number": applicant.document_number,
                "first_name": applicant.first_name,
                "paternal_surname": applicant.paternal_surname,
                "maternal_surname": applicant.maternal_surname,
                "birth_date": cls.safe_date_to_string(applicant.birth_date),
                "civil_status": cls.safe_enum_to_value(applicant.civil_status),
                "education_level": cls.safe_enum_to_value(applicant.education_level),
                "occupation": applicant.occupation,
                "disability_type": cls.safe_enum_to_value(applicant.disability_type) if applicant.disability_type else None,
                "disability_is_permanent": applicant.disability_is_permanent,  # ✅ NUEVO
                "disability_is_severe": applicant.disability_is_severe,  # ✅ NUEVO
                "is_main_applicant": applicant.is_main_applicant,
                "phone_number": applicant.phone_number,
                "email": applicant.email,
                "created_at": applicant.created_at,
                "updated_at": applicant.updated_at
            }
        except Exception as e:
            cls.handle_mapping_error("Applicant", "to_dict", e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Applicant:
        """Convertir diccionario MongoDB a entidad Applicant"""
        try:
            # Crear entidad Applicant
            applicant = Applicant(
                document_type=DocumentType(data["document_type"]),
                document_number=data["document_number"],
                first_name=data["first_name"],
                paternal_surname=data["paternal_surname"],
                maternal_surname=data["maternal_surname"],
                birth_date=datetime.fromisoformat(data["birth_date"]).date(),
                civil_status=CivilStatus(data["civil_status"]),
                education_level=EducationLevel(data["education_level"]),
                occupation=data.get("occupation"),
                disability_type=DisabilityType(data["disability_type"]) if data.get("disability_type") else None,
                disability_is_permanent=data.get("disability_is_permanent", False),  # ✅ NUEVO
                disability_is_severe=data.get("disability_is_severe", False),  # ✅ NUEVO
                is_main_applicant=data["is_main_applicant"],
                phone_number=data.get("phone_number"),
                email=data.get("email")
            )

            # Restaurar metadatos
            applicant.id = data["id"]
            applicant.created_at = data["created_at"]
            applicant.updated_at = data.get("updated_at")

            return applicant

        except Exception as e:
            cls.handle_mapping_error("Applicant", "from_dict", e)