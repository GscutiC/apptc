"""
Entidad principal TechoPropioApplication para el módulo Techo Propio
Representa una solicitud completa del programa gubernamental de vivienda
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from decimal import Decimal
from .base_entity import TechoPropioBaseEntity
from .applicant_entity import Applicant
from .property_entity import PropertyInfo
from .household_entity import HouseholdMember
from .economic_entity import EconomicInfo
from ...value_objects.techo_propio import (
    ApplicationStatus, VALIDATION_CONSTANTS, 
    EDITABLE_STATUSES, FINAL_STATUSES
)

# ✅ NUEVO: Datos de usuario para control interno
@dataclass
class UserData:
    """Datos del usuario para control interno - NO van en la solicitud oficial"""
    dni: str
    names: str
    surnames: str
    phone: Optional[str] = None
    email: Optional[str] = None
    birth_date: Optional[datetime] = None
    notes: Optional[str] = None  # Notas internas
    
    @property
    def full_name(self) -> str:
        return f"{self.names} {self.surnames}".strip()


@dataclass
class TechoPropioApplication(TechoPropioBaseEntity):
    """
    Entidad principal que representa una solicitud completa del programa Techo Propio
    Agrupa toda la información necesaria para la postulación
    """
    
    # Información básica de la solicitud
    application_number: Optional[str] = None  # Número de solicitud generado automáticamente
    status: ApplicationStatus = ApplicationStatus.DRAFT
    
    # ✅ NUEVOS CAMPOS: Información de registro y seguimiento
    registration_date: Optional[datetime] = None  # Fecha de registro de la solicitud
    convocation_code: Optional[str] = None  # Código de convocatoria (ej: "CONV-2025-01")
    registration_year: Optional[int] = None  # Año de registro (derivado de registration_date)
    sequential_number: Optional[int] = None  # Número secuencial dentro del año
    
    # ✅ NUEVA LÓGICA: Separación de datos de usuario vs solicitud
    user_data: Optional[UserData] = None  # Datos del usuario (CONTROL INTERNO)
    
    # Entidades de la solicitud oficial
    head_of_family: Applicant = None  # ✅ CAMBIO: Jefe de familia (antes main_applicant)
    spouse: Optional[Applicant] = None  # Cónyuge/conviviente
    property_info: PropertyInfo = None  # Información del predio
    household_members: List[HouseholdMember] = field(default_factory=list)  # Carga familiar
    
    # Información económica
    head_of_family_economic: Optional[EconomicInfo] = None  # ✅ CAMBIO: Info económica jefe de familia
    spouse_economic: Optional[EconomicInfo] = None
    
    # Fechas importantes
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    decision_date: Optional[datetime] = None
    
    # Información de procesamiento
    reviewer_id: Optional[str] = None  # ID del funcionario que revisa
    reviewer_comments: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Metadata adicional
    user_id: str = None  # ID del usuario que creó la solicitud (Clerk ID)
    created_by: Optional[str] = None  # ✅ ID del usuario que creó la entidad (para auditoría)
    updated_by: Optional[str] = None  # ID del usuario que actualizó por última vez
    version: int = 1  # Control de versiones
    priority_score: float = 0.0  # ✅ Puntaje de priorización calculado
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        super().__init__()
        
        # ✅ NUEVA LÓGICA: Auto-generar campos de registro si no existen
        if not self.registration_date:
            self.registration_date = datetime.now()
        
        if not self.registration_year:
            self.registration_year = self.registration_date.year if self.registration_date else datetime.now().year
            
        # ✅ NUEVAS VALIDACIONES: Validar datos de usuario y jefe de familia
        if self.user_data:
            self._validate_user_data()
        if self.head_of_family:
            self._validate_head_of_family()
        if self.spouse:
            self._validate_spouse_consistency()
        if self.household_members:
            self._validate_household_members()
        self._validate_economic_info_consistency()
    
    def _validate_user_data(self) -> None:
        """Validar datos de usuario para control interno"""
        if not self.user_data:
            return
            
        if not self.user_data.dni or len(self.user_data.dni) != 8:
            raise ValueError("DNI del usuario debe tener 8 dígitos")
            
        if not self.user_data.names or not self.user_data.surnames:
            raise ValueError("Nombres y apellidos del usuario son obligatorios")
    
    def _validate_head_of_family(self) -> None:
        """Validar jefe de familia"""
        if not self.head_of_family:
            raise ValueError("El jefe de familia es obligatorio")
        
        if not self.head_of_family.is_main_applicant:
            raise ValueError("El jefe de familia debe estar marcado como solicitante principal")
    
    def _validate_spouse_consistency(self) -> None:
        """Validar consistencia del cónyuge"""
        if not self.spouse:
            return
            
        if self.spouse.is_main_applicant:
            raise ValueError("El cónyuge no puede estar marcado como jefe de familia")
        
        # Verificar que el jefe de familia esté casado o conviviendo
        if self.head_of_family and not self.head_of_family.is_married_or_cohabiting():
            raise ValueError("Solo pueden incluir cónyuge los jefes de familia casados o convivientes")
        
        # No pueden tener el mismo DNI
        if (self.head_of_family and 
            self.head_of_family.document_number == self.spouse.document_number):
            raise ValueError("El jefe de familia y cónyuge no pueden tener el mismo documento")
        
        # ✅ NUEVA VALIDACIÓN: Tampoco puede tener el mismo DNI que el usuario
        if (self.user_data and 
            self.user_data.dni == self.spouse.document_number):
            raise ValueError("El cónyuge no puede tener el mismo DNI que el usuario registrado")
    
    def _validate_household_members(self) -> None:
        """Validar miembros de la carga familiar"""
        if not self.household_members:
            return
            
        max_members = VALIDATION_CONSTANTS["MAX_HOUSEHOLD_MEMBERS"]
        if len(self.household_members) > max_members:
            raise ValueError(f"No se pueden registrar más de {max_members} miembros familiares")
        
        # ✅ NUEVA VALIDACIÓN: DNIs únicos incluyendo usuario, jefe de familia, cónyuge y carga familiar
        all_dnis = []
        
        # DNI del usuario (control interno)
        if self.user_data:
            all_dnis.append(self.user_data.dni)
            
        # DNI del jefe de familia
        if self.head_of_family:
            all_dnis.append(self.head_of_family.document_number)
            
        # DNI del cónyuge
        if self.spouse:
            all_dnis.append(self.spouse.document_number)
            
        # DNIs de carga familiar
        for member in self.household_members:
            if member.document_number in all_dnis:
                raise ValueError(f"DNI duplicado encontrado: {member.document_number}")
            all_dnis.append(member.document_number)
    
    def _validate_economic_info_consistency(self) -> None:
        """Validar consistencia de información económica"""
        if self.head_of_family_economic and self.head_of_family:
            if self.head_of_family_economic.applicant_id != self.head_of_family.id:
                raise ValueError("La información económica del jefe de familia no coincide")
        
        if self.spouse_economic and self.spouse:
            if self.spouse_economic.applicant_id != self.spouse.id:
                raise ValueError("La información económica del cónyuge no coincide")
        elif self.spouse_economic and not self.spouse:
            raise ValueError("No se puede tener información económica del cónyuge sin cónyuge")
    
    @property
    def total_household_size(self) -> int:
        """Tamaño total del grupo familiar"""
        size = 1  # Solicitante principal
        if self.spouse:
            size += 1
        size += len(self.household_members)
        return size
    
    @property
    def total_family_income(self) -> Decimal:
        """Ingreso total familiar mensual"""
        total = Decimal('0')
        
        if self.head_of_family_economic:
            total += self.head_of_family_economic.total_monthly_income
        
        if self.spouse_economic:
            total += self.spouse_economic.total_monthly_income
            
        return total
    
    @property
    def per_capita_income(self) -> Decimal:
        """Ingreso per cápita familiar"""
        total_income = self.total_family_income
        household_size = self.total_household_size
        
        if household_size == 0:
            return Decimal('0')
        
        return total_income / household_size
    
    @property
    def is_editable(self) -> bool:
        """Verificar si la solicitud puede ser editada"""
        return self.status in EDITABLE_STATUSES
    
    @property
    def is_final_status(self) -> bool:
        """Verificar si está en estado final"""
        return self.status in FINAL_STATUSES
    
    @property
    def can_be_submitted(self) -> bool:
        """Verificar si puede ser enviada para revisión"""
        return (
            self.status == ApplicationStatus.DRAFT and
            self.head_of_family is not None and
            self.property_info is not None and
            self.head_of_family_economic is not None
        )
    
    def generate_application_number(self, sequential_number: Optional[int] = None) -> str:
        """
        Generar número de solicitud único
        Formato: TP-YYYY-XXXXXX (TP = Techo Propio, YYYY = año, XXXXXX = secuencial)
        """
        if self.application_number:
            return self.application_number
        
        year = self.registration_year or datetime.now().year
        
        # Si no se proporciona número secuencial, usar timestamp
        if sequential_number is None:
            # Usar timestamp como fallback (últimos 6 dígitos)
            timestamp = int(datetime.now().timestamp())
            sequential_number = timestamp % 1000000
            
        self.sequential_number = sequential_number
        self.application_number = f"TP-{year}-{sequential_number:06d}"
        
        return self.application_number
        now = datetime.utcnow()
        prefix = f"TP-{now.year}-{now.month:02d}"
        
        # En implementación real, esto debería ser un contador incremental
        # Por ahora usamos timestamp para unicidad
        suffix = f"{now.day:02d}{now.hour:02d}{now.minute:02d}{now.second:02d}"
        
        self.application_number = f"{prefix}-{suffix}"
        return self.application_number
    
    def add_household_member(self, member: HouseholdMember) -> None:
        """Agregar miembro a la carga familiar"""
        if not self.is_editable:
            raise ValueError("No se puede modificar una solicitud en este estado")
            
        # Validar DNI único
        existing_dnis = [m.document_number for m in self.household_members]
        if self.main_applicant:
            existing_dnis.append(self.main_applicant.document_number)
        if self.spouse:
            existing_dnis.append(self.spouse.document_number)
            
        if member.document_number in existing_dnis:
            raise ValueError(f"Ya existe una persona con DNI {member.document_number}")
        
        self.household_members.append(member)
        self.update_timestamp()
    
    def remove_household_member(self, member_id: str) -> bool:
        """Remover miembro de la carga familiar"""
        if not self.is_editable:
            raise ValueError("No se puede modificar una solicitud en este estado")
            
        initial_count = len(self.household_members)
        self.household_members = [m for m in self.household_members if m.id != member_id]
        
        if len(self.household_members) < initial_count:
            self.update_timestamp()
            return True
        return False
    
    def set_spouse(self, spouse: Applicant) -> None:
        """Establecer cónyuge/conviviente"""
        if not self.is_editable:
            raise ValueError("No se puede modificar una solicitud en este estado")
            
        spouse.is_main_applicant = False
        self.spouse = spouse
        self._validate_spouse_consistency()
        self.update_timestamp()
    
    def remove_spouse(self) -> None:
        """Remover cónyuge/conviviente"""
        if not self.is_editable:
            raise ValueError("No se puede modificar una solicitud en este estado")
            
        self.spouse = None
        self.spouse_economic = None
        self.update_timestamp()
    
    def submit_application(self, user_id: str) -> None:
        """Enviar solicitud para revisión"""
        if not self.can_be_submitted:
            raise ValueError("La solicitud no está completa para ser enviada")
        
        self.status = ApplicationStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()
        self.user_id = user_id
        
        if not self.application_number:
            self.generate_application_number()
            
        self.update_timestamp()
    
    def start_review(self, reviewer_id: str) -> None:
        """Iniciar proceso de revisión"""
        if self.status != ApplicationStatus.SUBMITTED:
            raise ValueError("Solo se pueden revisar solicitudes enviadas")
            
        self.status = ApplicationStatus.UNDER_REVIEW
        self.reviewer_id = reviewer_id
        self.reviewed_at = datetime.utcnow()
        self.update_timestamp()
    
    def approve_application(self, reviewer_id: str, comments: Optional[str] = None) -> None:
        """Aprobar solicitud"""
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden aprobar solicitudes en revisión")
            
        self.status = ApplicationStatus.APPROVED
        self.reviewer_id = reviewer_id
        self.reviewer_comments = comments
        self.decision_date = datetime.utcnow()
        self.update_timestamp()
    
    def reject_application(self, reviewer_id: str, reason: str, comments: Optional[str] = None) -> None:
        """Rechazar solicitud"""
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se pueden rechazar solicitudes en revisión")
            
        if not reason or not reason.strip():
            raise ValueError("La razón de rechazo es obligatoria")
            
        self.status = ApplicationStatus.REJECTED
        self.reviewer_id = reviewer_id
        self.rejection_reason = reason
        self.reviewer_comments = comments
        self.decision_date = datetime.utcnow()
        self.update_timestamp()
    
    def request_additional_info(self, reviewer_id: str, comments: str) -> None:
        """Solicitar información adicional"""
        if self.status != ApplicationStatus.UNDER_REVIEW:
            raise ValueError("Solo se puede solicitar información adicional en solicitudes en revisión")
            
        if not comments or not comments.strip():
            raise ValueError("Los comentarios son obligatorios al solicitar información adicional")
            
        self.status = ApplicationStatus.ADDITIONAL_INFO_REQUIRED
        self.reviewer_id = reviewer_id
        self.reviewer_comments = comments
        self.update_timestamp()
    
    def resubmit_after_additional_info(self) -> None:
        """Reenviar después de proporcionar información adicional"""
        if self.status != ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
            raise ValueError("Solo se pueden reenviar solicitudes que requieren información adicional")
            
        self.status = ApplicationStatus.SUBMITTED
        self.reviewer_comments = None  # Limpiar comentarios anteriores
        self.update_timestamp()
    
    def cancel_application(self, user_id: str) -> None:
        """Cancelar solicitud"""
        if self.is_final_status:
            raise ValueError("No se puede cancelar una solicitud en estado final")
            
        self.status = ApplicationStatus.CANCELLED
        self.decision_date = datetime.utcnow()
        self.update_timestamp()
    
    def get_completion_percentage(self) -> float:
        """Obtener porcentaje de completitud de la solicitud"""
        total_sections = 4  # Usuario, jefe de familia, propiedad, económica, (cónyuge opcional)
        completed_sections = 0
        
        # ✅ NUEVA LÓGICA: Incluir datos de usuario
        if self.user_data:
            completed_sections += 1
            
        if self.head_of_family:
            completed_sections += 1
            
        if self.property_info:
            completed_sections += 1
            
        if self.head_of_family_economic:
            completed_sections += 1
            
        # Si tiene cónyuge, debe tener información económica del cónyuge
        if self.spouse:
            total_sections += 1
            if self.spouse_economic:
                completed_sections += 1
        else:
            completed_sections += 1  # No requiere cónyuge
            
        return (completed_sections / total_sections) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para persistencia"""
        user_data_dict = None
        if self.user_data:
            user_data_dict = {
                "dni": self.user_data.dni,
                "names": self.user_data.names,
                "surnames": self.user_data.surnames,
                "phone": self.user_data.phone,
                "email": self.user_data.email,
                "birth_date": self.user_data.birth_date.isoformat() if self.user_data.birth_date else None,
                "notes": self.user_data.notes
            }
        
        return {
            "id": self.id,
            "application_number": self.application_number,
            "status": self.status.value,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "convocation_code": self.convocation_code,
            "registration_year": self.registration_year,
            "sequential_number": self.sequential_number,
            "user_data": user_data_dict,
            "head_of_family": self.head_of_family.to_dict() if self.head_of_family else None,
            "spouse": self.spouse.to_dict() if self.spouse else None,
            "property_info": self.property_info.to_dict() if self.property_info else None,
            "household_members": [member.to_dict() for member in self.household_members],
            "head_of_family_economic": self.head_of_family_economic.to_dict() if self.head_of_family_economic else None,
            "spouse_economic": self.spouse_economic.to_dict() if self.spouse_economic else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "decision_date": self.decision_date.isoformat() if self.decision_date else None,
            "reviewer_id": self.reviewer_id,
            "reviewer_comments": self.reviewer_comments,
            "rejection_reason": self.rejection_reason,
            "user_id": self.user_id,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TechoPropioApplication':
        """Crear instancia desde diccionario"""
        # Crear instancia básica
        application = cls()
        
        # Campos básicos
        application.id = data.get("id")
        application.application_number = data.get("application_number")
        application.status = ApplicationStatus(data.get("status", ApplicationStatus.DRAFT.value))
        
        # ✅ NUEVOS CAMPOS: Información de registro
        if data.get("registration_date"):
            application.registration_date = datetime.fromisoformat(data["registration_date"])
        application.convocation_code = data.get("convocation_code")
        application.registration_year = data.get("registration_year")
        application.sequential_number = data.get("sequential_number")
        
        # ✅ NUEVA LÓGICA: Datos de usuario separados
        if data.get("user_data"):
            user_data_dict = data["user_data"]
            application.user_data = UserData(
                dni=user_data_dict["dni"],
                names=user_data_dict["names"],
                surnames=user_data_dict["surnames"],
                phone=user_data_dict.get("phone"),
                email=user_data_dict.get("email"),
                birth_date=datetime.fromisoformat(user_data_dict["birth_date"]) if user_data_dict.get("birth_date") else None,
                notes=user_data_dict.get("notes")
            )
        
        # Entidades relacionadas
        if data.get("head_of_family"):
            application.head_of_family = Applicant.from_dict(data["head_of_family"])
        elif data.get("main_applicant"):  # ✅ RETROCOMPATIBILIDAD
            application.head_of_family = Applicant.from_dict(data["main_applicant"])
            
        if data.get("spouse"):
            application.spouse = Applicant.from_dict(data["spouse"])
            
        if data.get("property_info"):
            application.property_info = PropertyInfo.from_dict(data["property_info"])
            
        if data.get("household_members"):
            application.household_members = [
                HouseholdMember.from_dict(member_data) 
                for member_data in data["household_members"]
            ]
            
        if data.get("head_of_family_economic"):
            application.head_of_family_economic = EconomicInfo.from_dict(data["head_of_family_economic"])
        elif data.get("main_applicant_economic"):  # ✅ RETROCOMPATIBILIDAD
            application.head_of_family_economic = EconomicInfo.from_dict(data["main_applicant_economic"])
            
        if data.get("spouse_economic"):
            application.spouse_economic = EconomicInfo.from_dict(data["spouse_economic"])
        
        # Fechas
        if data.get("submitted_at"):
            application.submitted_at = datetime.fromisoformat(data["submitted_at"])
        if data.get("reviewed_at"):
            application.reviewed_at = datetime.fromisoformat(data["reviewed_at"])
        if data.get("decision_date"):
            application.decision_date = datetime.fromisoformat(data["decision_date"])
            
        # Metadata
        application.reviewer_id = data.get("reviewer_id")
        application.reviewer_comments = data.get("reviewer_comments")
        application.rejection_reason = data.get("rejection_reason")
        application.user_id = data.get("user_id")
        application.version = data.get("version", 1)
        application.created_by = data.get("created_by")
        
        return application