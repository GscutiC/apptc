"""
Mappers para entidades del módulo Techo Propio
Manejan la conversión entre entidades de dominio y documentos MongoDB
"""

from .base_mapper import BaseMapper
from .applicant_mapper import ApplicantMapper
from .property_mapper import PropertyMapper
from .economic_mapper import EconomicMapper
from .household_member_mapper import HouseholdMemberMapper
from .application_mapper import ApplicationMapper

__all__ = [
    "BaseMapper",
    "ApplicantMapper",
    "PropertyMapper", 
    "EconomicMapper",
    "HouseholdMemberMapper",
    "ApplicationMapper"
]