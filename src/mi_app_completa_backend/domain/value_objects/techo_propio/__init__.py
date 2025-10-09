"""
Value Objects para el módulo Techo Propio
"""

from .enums import (
    ApplicationStatus, DocumentType, CivilStatus, EducationLevel,
    EmploymentSituation, WorkCondition, FamilyRelationship, DisabilityType,
    VALIDATION_CONSTANTS, STATUS_LABELS, EDUCATION_LABELS,
    EDITABLE_STATUSES, FINAL_STATUSES
)

__all__ = [
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
    'FINAL_STATUSES'
]