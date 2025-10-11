"""
Mapper principal para entidad TechoPropioApplication
Orquesta todos los mappers específicos para crear la aplicación completa
"""

from typing import Dict, Any, List
import logging

from .base_mapper import BaseMapper
from .applicant_mapper import ApplicantMapper
from .property_mapper import PropertyMapper
from .economic_mapper import EconomicMapper
from .household_member_mapper import HouseholdMemberMapper

from .....domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, EconomicInfo, HouseholdMember
)
from .....domain.value_objects.techo_propio import ApplicationStatus

logger = logging.getLogger(__name__)


class ApplicationMapper(BaseMapper):
    """Mapper principal para entidad TechoPropioApplication"""
    
    @classmethod
    def to_dict(cls, application: TechoPropioApplication) -> Dict[str, Any]:
        """Convertir TechoPropioApplication a documento MongoDB"""
        try:
            document = {
                "status": cls.safe_enum_to_value(application.status),
                "priority_score": float(application.priority_score),
                "created_by": application.created_by,
                "created_at": application.created_at,
                "updated_at": application.updated_at,
                "updated_by": application.updated_by,
                "version": application.version,
                
                # Usar mappers específicos
                "main_applicant": ApplicantMapper.to_dict(application.main_applicant),
                "property_info": PropertyMapper.to_dict(application.property_info),
                "main_applicant_economic": EconomicMapper.to_dict(application.main_applicant_economic),
            }
            
            # Cónyuge (opcional)
            if application.spouse:
                document["spouse"] = ApplicantMapper.to_dict(application.spouse)
            
            # Información económica del cónyuge (opcional)
            if application.spouse_economic:
                document["spouse_economic"] = EconomicMapper.to_dict(application.spouse_economic)
            
            # Miembros de carga familiar
            if application.household_members:
                document["household_members"] = [
                    HouseholdMemberMapper.to_dict(member) 
                    for member in application.household_members
                ]
            
            # Datos de auditoría adicionales
            if hasattr(application, 'submitted_at') and application.submitted_at:
                document["submitted_at"] = application.submitted_at
            
            if hasattr(application, 'reviewed_at') and application.reviewed_at:
                document["reviewed_at"] = application.reviewed_at
            
            if hasattr(application, 'reviewer_id') and application.reviewer_id:
                document["reviewer_id"] = application.reviewer_id
            
            return document
            
        except Exception as e:
            cls.handle_mapping_error("TechoPropioApplication", "to_dict", e)
    
    @classmethod
    def from_dict(cls, document: Dict[str, Any]) -> TechoPropioApplication:
        """Convertir documento MongoDB a entidad TechoPropioApplication"""
        try:
            # Usar mappers específicos para crear componentes
            main_applicant = ApplicantMapper.from_dict(document["main_applicant"])
            property_info = PropertyMapper.from_dict(document["property_info"])
            main_applicant_economic = EconomicMapper.from_dict(document["main_applicant_economic"])
            
            # Crear solicitud
            application = TechoPropioApplication(
                main_applicant=main_applicant,
                property_info=property_info,
                main_applicant_economic=main_applicant_economic
            )
            
            # Asignar ID y metadatos
            application.id = str(document["_id"])
            application.created_by = document.get("created_by", "system")
            
            # Restaurar metadatos
            application.status = ApplicationStatus(document["status"])
            application.priority_score = document.get("priority_score", 0.0)
            application.created_at = document["created_at"]
            application.updated_at = document.get("updated_at")
            application.updated_by = document.get("updated_by")
            application.version = document.get("version", 1)
            
            # Restaurar cónyuge si existe
            if "spouse" in document:
                spouse = ApplicantMapper.from_dict(document["spouse"])
                application.set_spouse(spouse)
            
            # Restaurar información económica del cónyuge
            if "spouse_economic" in document:
                application.spouse_economic = EconomicMapper.from_dict(document["spouse_economic"])
            
            # Restaurar miembros de carga familiar
            if "household_members" in document:
                application.household_members = [
                    HouseholdMemberMapper.from_dict(member_dict)
                    for member_dict in document["household_members"]
                ]
            
            # Restaurar datos de auditoría adicionales
            if "submitted_at" in document:
                application.submitted_at = document["submitted_at"]
            
            if "reviewed_at" in document:
                application.reviewed_at = document["reviewed_at"]
            
            if "reviewer_id" in document:
                application.reviewer_id = document["reviewer_id"]
            
            return application
            
        except Exception as e:
            cls.handle_mapping_error("TechoPropioApplication", "from_dict", e)