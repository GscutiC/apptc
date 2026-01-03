"""
Mapper para entidad HouseholdMember
Maneja conversión entre HouseholdMember entity y documento MongoDB
"""

from typing import Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

from .base_mapper import BaseMapper
from .....domain.entities.techo_propio import HouseholdMember
from .....domain.value_objects.techo_propio import (
    DocumentType, FamilyRelationship, EducationLevel, DisabilityType,
    CivilStatus, EmploymentSituation, WorkCondition
)

logger = logging.getLogger(__name__)


class HouseholdMemberMapper(BaseMapper):
    """Mapper especializado para entidades HouseholdMember"""
    
    @classmethod
    def to_dict(cls, member: HouseholdMember) -> Dict[str, Any]:
        """Convertir HouseholdMember a diccionario para MongoDB"""
        try:
            return {
                "id": member.id,
                "first_name": member.first_name,
                "paternal_surname": member.paternal_surname,
                "maternal_surname": member.maternal_surname,
                "document_type": cls.safe_enum_to_value(member.document_type),
                "document_number": member.document_number,
                "birth_date": cls.safe_date_to_string(member.birth_date),
                "civil_status": cls.safe_enum_to_value(member.civil_status),
                "education_level": cls.safe_enum_to_value(member.education_level),
                "occupation": member.occupation,
                "employment_situation": cls.safe_enum_to_value(member.employment_situation),
                "work_condition": cls.safe_enum_to_value(member.work_condition),
                "monthly_income": cls.safe_decimal_to_float(member.monthly_income),
                "disability_type": cls.safe_enum_to_value(member.disability_type),
                "relationship": cls.safe_enum_to_value(member.relationship) if member.relationship else None,
                "is_dependent": member.is_dependent,
                "created_at": member.created_at,
                "updated_at": member.updated_at
            }
        except Exception as e:
            cls.handle_mapping_error("HouseholdMember", "to_dict", e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HouseholdMember:
        """Convertir diccionario MongoDB a entidad HouseholdMember"""
        try:
            # Crear entidad HouseholdMember
            member = HouseholdMember(
                first_name=data["first_name"],
                paternal_surname=data["paternal_surname"],
                maternal_surname=data["maternal_surname"],
                document_type=DocumentType(data["document_type"]),
                document_number=data["document_number"],
                birth_date=datetime.fromisoformat(data["birth_date"]).date(),
                civil_status=CivilStatus(data["civil_status"]),
                education_level=EducationLevel(data["education_level"]),
                occupation=data["occupation"],
                employment_situation=EmploymentSituation(data["employment_situation"]),
                work_condition=WorkCondition(data["work_condition"]),
                monthly_income=cls.safe_float_to_decimal(data["monthly_income"]),
                disability_type=DisabilityType(data.get("disability_type", "NONE")),
                relationship=FamilyRelationship(data["relationship"]) if data.get("relationship") else None,
                is_dependent=data.get("is_dependent", True)
            )
            
            # Restaurar metadatos
            member.id = data["id"]
            member.created_at = data["created_at"]
            member.updated_at = data.get("updated_at")
            
            return member
            
        except Exception as e:
            cls.handle_mapping_error("HouseholdMember", "from_dict", e)