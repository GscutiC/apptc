"""
Value Objects y Enums para el módulo Techo Propio
Define estados, tipos y constantes utilizadas en el dominio
"""

from enum import Enum
from typing import Dict, List


class ApplicationStatus(str, Enum):
    """Estados de la solicitud Techo Propio"""
    DRAFT = "draft"                    # Borrador (guardado temporal)
    SUBMITTED = "submitted"            # Enviada para revisión
    UNDER_REVIEW = "under_review"      # En proceso de revisión
    ADDITIONAL_INFO_REQUIRED = "additional_info_required"  # Requiere información adicional
    APPROVED = "approved"              # Aprobada
    REJECTED = "rejected"              # Rechazada
    CANCELLED = "cancelled"            # Cancelada por el usuario


class DocumentType(str, Enum):
    """Tipos de documento de identidad"""
    DNI = "dni"                        # Documento Nacional de Identidad
    CE = "ce"                          # Carnet de Extranjería
    PASSPORT = "passport"              # Pasaporte


class CivilStatus(str, Enum):
    """Estado civil del solicitante"""
    SINGLE = "soltero"                 # Soltero(a)
    MARRIED = "casado"                 # Casado(a)
    DIVORCED = "divorciado"            # Divorciado(a)
    WIDOWED = "viudo"                  # Viudo(a)
    COHABITING = "conviviente"         # Conviviente


class EducationLevel(str, Enum):
    """Grado de instrucción"""
    NO_EDUCATION = "sin_estudios"      # Sin estudios
    PRIMARY_INCOMPLETE = "primaria_incompleta"
    PRIMARY_COMPLETE = "primaria_completa"
    SECONDARY_INCOMPLETE = "secundaria_incompleta"
    SECONDARY_COMPLETE = "secundaria_completa"
    TECHNICAL_INCOMPLETE = "tecnico_incompleto"
    TECHNICAL_COMPLETE = "tecnico_completo"
    UNIVERSITY_INCOMPLETE = "universitario_incompleto"
    UNIVERSITY_COMPLETE = "universitario_completo"
    POSTGRADUATE = "postgrado"


class EmploymentSituation(str, Enum):
    """Situación laboral"""
    DEPENDENT = "dependiente"          # Trabajador dependiente
    INDEPENDENT = "independiente"      # Trabajador independiente
    UNEMPLOYED = "desempleado"         # Desempleado
    RETIRED = "jubilado"               # Jubilado
    STUDENT = "estudiante"             # Estudiante


class WorkCondition(str, Enum):
    """Condición de trabajo"""
    FORMAL = "formal"                  # Trabajo formal
    INFORMAL = "informal"              # Trabajo informal


class FamilyRelationship(str, Enum):
    """Relación de parentesco con el jefe de familia"""
    SPOUSE = "conyuge"                 # Cónyuge
    PARTNER = "conviviente"            # Conviviente
    CHILD = "hijo"                     # Hijo(a)
    PARENT = "padre"                   # Padre/Madre
    SIBLING = "hermano"                # Hermano(a)
    GRANDPARENT = "abuelo"             # Abuelo(a)
    GRANDCHILD = "nieto"               # Nieto(a)
    OTHER = "otro"                     # Otro parentesco


class DisabilityType(str, Enum):
    """Tipos de discapacidad"""
    NONE = "ninguna"                   # Sin discapacidad
    PHYSICAL = "fisica"                # Discapacidad física
    VISUAL = "visual"                  # Discapacidad visual
    HEARING = "auditiva"               # Discapacidad auditiva
    INTELLECTUAL = "intelectual"       # Discapacidad intelectual
    PSYCHOSOCIAL = "psicosocial"       # Discapacidad psicosocial
    MULTIPLE = "multiple"              # Discapacidad múltiple


# Constantes útiles para validaciones
VALIDATION_CONSTANTS = {
    "MIN_AGE": 18,                     # Edad mínima del solicitante
    "MAX_AGE": 80,                     # Edad máxima del solicitante
    "MIN_HOUSEHOLD_MEMBERS": 0,        # Mínimo miembros de familia
    "MAX_HOUSEHOLD_MEMBERS": 15,       # Máximo miembros de familia
    "DNI_LENGTH": 8,                   # Longitud del DNI
    "MIN_INCOME": 0,                   # Ingreso mínimo
    "MAX_INCOME": 50000,               # Ingreso máximo permitido
    "MIN_NAME_LENGTH": 2,              # Longitud mínima de nombres
    "MAX_NAME_LENGTH": 100,            # Longitud máxima de nombres
}

# Mapeo de etiquetas para mostrar en frontend
STATUS_LABELS: Dict[ApplicationStatus, str] = {
    ApplicationStatus.DRAFT: "Borrador",
    ApplicationStatus.SUBMITTED: "Enviada",
    ApplicationStatus.UNDER_REVIEW: "En Revisión",
    ApplicationStatus.ADDITIONAL_INFO_REQUIRED: "Información Adicional Requerida",
    ApplicationStatus.APPROVED: "Aprobada",
    ApplicationStatus.REJECTED: "Rechazada",
    ApplicationStatus.CANCELLED: "Cancelada",
}

EDUCATION_LABELS: Dict[EducationLevel, str] = {
    EducationLevel.NO_EDUCATION: "Sin estudios",
    EducationLevel.PRIMARY_INCOMPLETE: "Primaria incompleta",
    EducationLevel.PRIMARY_COMPLETE: "Primaria completa",
    EducationLevel.SECONDARY_INCOMPLETE: "Secundaria incompleta",
    EducationLevel.SECONDARY_COMPLETE: "Secundaria completa",
    EducationLevel.TECHNICAL_INCOMPLETE: "Técnico incompleto",
    EducationLevel.TECHNICAL_COMPLETE: "Técnico completo",
    EducationLevel.UNIVERSITY_INCOMPLETE: "Universitario incompleto",
    EducationLevel.UNIVERSITY_COMPLETE: "Universitario completo",
    EducationLevel.POSTGRADUATE: "Postgrado",
}

# Estados que permiten edición
EDITABLE_STATUSES: List[ApplicationStatus] = [
    ApplicationStatus.DRAFT,
    ApplicationStatus.ADDITIONAL_INFO_REQUIRED
]

# Estados finales (no se pueden cambiar)
FINAL_STATUSES: List[ApplicationStatus] = [
    ApplicationStatus.APPROVED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.CANCELLED
]