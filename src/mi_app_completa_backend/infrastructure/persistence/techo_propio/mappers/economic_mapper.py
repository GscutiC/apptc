"""
Mapper para entidad EconomicInfo
Maneja conversión entre EconomicInfo entity y documento MongoDB
"""

from typing import Dict, Any
from decimal import Decimal
import logging

from .base_mapper import BaseMapper
from .....domain.entities.techo_propio import EconomicInfo
from .....domain.value_objects.techo_propio import (
    EmploymentSituation, WorkCondition
)

logger = logging.getLogger(__name__)


class EconomicMapper(BaseMapper):
    """Mapper especializado para entidades EconomicInfo"""
    
    @classmethod
    def to_dict(cls, economic_info: EconomicInfo) -> Dict[str, Any]:
        """Convertir EconomicInfo a diccionario para MongoDB"""
        try:
            return {
                "id": economic_info.id,
                "employment_situation": cls.safe_enum_to_value(economic_info.employment_situation),
                "monthly_income": cls.safe_decimal_to_float(economic_info.monthly_income),
                "applicant_id": economic_info.applicant_id,
                "work_condition": cls.safe_enum_to_value(economic_info.work_condition) if economic_info.work_condition else None,
                "occupation_detail": economic_info.occupation_detail,
                "employer_name": economic_info.employer_name,
                "has_additional_income": economic_info.has_additional_income,
                "additional_income_amount": cls.safe_decimal_to_float(economic_info.additional_income_amount) if economic_info.additional_income_amount else None,
                "additional_income_source": economic_info.additional_income_source,
                "is_main_applicant": economic_info.is_main_applicant,
                "created_at": economic_info.created_at,
                "updated_at": economic_info.updated_at
            }
        except Exception as e:
            cls.handle_mapping_error("EconomicInfo", "to_dict", e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EconomicInfo:
        """Convertir diccionario MongoDB a entidad EconomicInfo"""
        try:
            # Crear entidad EconomicInfo
            economic_info = EconomicInfo(
                employment_situation=EmploymentSituation(data["employment_situation"]),
                monthly_income=cls.safe_float_to_decimal(data["monthly_income"]),
                applicant_id=data["applicant_id"],
                work_condition=WorkCondition(data["work_condition"]) if data.get("work_condition") else None,
                occupation_detail=data.get("occupation_detail"),
                employer_name=data.get("employer_name"),
                has_additional_income=data.get("has_additional_income", False),
                additional_income_amount=cls.safe_float_to_decimal(data.get("additional_income_amount")) if data.get("additional_income_amount") else None,
                additional_income_source=data.get("additional_income_source"),
                is_main_applicant=data.get("is_main_applicant", False)
            )
            
            # Restaurar metadatos
            economic_info.id = data["id"]
            economic_info.created_at = data["created_at"]
            economic_info.updated_at = data.get("updated_at")
            
            return economic_info
            
        except Exception as e:
            cls.handle_mapping_error("EconomicInfo", "from_dict", e)