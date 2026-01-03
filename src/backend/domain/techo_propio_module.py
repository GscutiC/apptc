"""
Módulo Techo Propio - Programa Gubernamental de Vivienda
Arquitectura hexagonal completa: Domain → Application → Infrastructure

Este módulo implementa el sistema de postulación para el programa Techo Propio
del Ministerio de Vivienda, Construcción y Saneamiento.

Componentes principales:
- Entities: Modelos de dominio con lógica de negocio
- Value Objects: Enums, constantes y objetos de valor
- Repositories: Interfaces abstractas para persistencia
- Services: Lógica de negocio compleja del dominio

Uso:
    from .entities.techo_propio import TechoPropioApplication, Applicant
    from .value_objects.techo_propio import ApplicationStatus
    from .repositories.techo_propio import TechoPropioRepository
    from .services.techo_propio import TechoPropioBusinessRules
"""

# Entidades principales
from .entities.techo_propio import (
    TechoPropioBaseEntity,
    TechoPropioApplication,
    Applicant,
    PropertyInfo,
    HouseholdMember,
    EconomicInfo
)

# Value Objects y Enums
from .value_objects.techo_propio import (
    ApplicationStatus,
    DocumentType,
    CivilStatus,
    EducationLevel,
    EmploymentSituation,
    WorkCondition,
    FamilyRelationship,
    DisabilityType,
    VALIDATION_CONSTANTS,
    STATUS_LABELS,
    EDUCATION_LABELS,
    EDITABLE_STATUSES,
    FINAL_STATUSES
)

# Repositorios
from .repositories.techo_propio import TechoPropioRepository

# Servicios de dominio
from .services.techo_propio import (
    TechoPropioBusinessRules,
    TechoPropioStatisticsService
)

__all__ = [
    # Entidades
    'TechoPropioBaseEntity',
    'TechoPropioApplication',
    'Applicant',
    'PropertyInfo', 
    'HouseholdMember',
    'EconomicInfo',
    
    # Value Objects
    'ApplicationStatus',
    'DocumentType',
    'CivilStatus',
    'EducationLevel',
    'EmploymentSituation',
    'WorkCondition',
    'FamilyRelationship',
    'DisabilityType',
    'VALIDATION_CONSTANTS',
    'STATUS_LABELS',
    'EDUCATION_LABELS',
    'EDITABLE_STATUSES',
    'FINAL_STATUSES',
    
    # Repositorios
    'TechoPropioRepository',
    
    # Servicios
    'TechoPropioBusinessRules',
    'TechoPropioStatisticsService'
]

# Información del módulo
__version__ = "1.0.0"
__author__ = "AppTc Development Team"
__description__ = "Módulo Techo Propio - Programa Gubernamental de Vivienda"