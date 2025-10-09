"""
Entidades del dominio para el módulo Techo Propio
Programa Gubernamental de Vivienda - Ministerio de Vivienda
"""

from .base_entity import TechoPropioBaseEntity
from .applicant_entity import Applicant
from .property_entity import PropertyInfo
from .household_entity import HouseholdMember
from .economic_entity import EconomicInfo
from .application_entity import TechoPropioApplication

__all__ = [
    'TechoPropioBaseEntity',
    'Applicant',
    'PropertyInfo', 
    'HouseholdMember',
    'EconomicInfo',
    'TechoPropioApplication'
]