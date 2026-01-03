"""
Mappers para convertir entre entidades de dominio y documentos MongoDB
Maneja la conversión bidireccional de datos
"""

from typing import Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import (
    ApplicationStatus,
    FamilyMember,
    PersonalInformation,
    ContactInformation,
    HouseholdInformation,
    EconomicInformation,
    DocumentData
)


class ApplicationMapper:
    """Mapper para solicitudes de Techo Propio"""
    
    @staticmethod
    def to_dict(application: TechoPropioApplication) -> Dict[str, Any]:
        """
        Convierte entidad TechoPropioApplication a documento MongoDB
        
        Args:
            application: Entidad de solicitud
            
        Returns:
            Diccionario para MongoDB
        """
        document = {
            "application_number": application.application_number,
            "convocation_code": application.convocation_code,
            "registration_year": application.registration_year,
            "sequential_number": application.sequential_number,
            "registration_date": application.registration_date,
            "status": application.status.value,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "submitted_at": application.submitted_at,
            "reviewed_at": application.reviewed_at,
            "approved_at": application.approved_at,
            "rejected_at": application.rejected_at,
            
            # Información personal
            "personal_information": {
                "dni": application.personal_information.dni,
                "first_name": application.personal_information.first_name,
                "last_name": application.personal_information.last_name,
                "birth_date": application.personal_information.birth_date,
                "marital_status": application.personal_information.marital_status,
                "nationality": application.personal_information.nationality
            },
            
            # Información de contacto
            "contact_information": {
                "phone": application.contact_information.phone,
                "email": application.contact_information.email,
                "address": application.contact_information.address,
                "district": application.contact_information.district,
                "province": application.contact_information.province,
                "department": application.contact_information.department
            },
            
            # Información del hogar
            "household_information": {
                "household_size": application.household_information.household_size,
                "dependents": application.household_information.dependents,
                "family_members": [
                    ApplicationMapper._family_member_to_dict(member)
                    for member in application.household_information.family_members
                ]
            },
            
            # Información económica
            "economic_information": {
                "monthly_income": application.economic_information.monthly_income,
                "employment_status": application.economic_information.employment_status,
                "employer": application.economic_information.employer,
                "other_income": application.economic_information.other_income,
                "expenses": application.economic_information.expenses
            },
            
            # Documentos
            "documents": [
                ApplicationMapper._document_to_dict(doc)
                for doc in application.documents
            ],
            
            # Campos adicionales
            "notes": application.notes,
            "priority_score": application.priority_score
        }
        
        # Solo incluir ID si existe
        if application.id:
            document["_id"] = ObjectId(application.id)
            
        return document
    
    @staticmethod
    def from_dict(document: Dict[str, Any]) -> TechoPropioApplication:
        """
        Convierte documento MongoDB a entidad TechoPropioApplication
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Entidad de solicitud
        """
        # Convertir ObjectId a string
        application_id = str(document["_id"]) if "_id" in document else None
        
        # Mapear información personal
        personal_info = PersonalInformation(
            dni=document["personal_information"]["dni"],
            first_name=document["personal_information"]["first_name"],
            last_name=document["personal_information"]["last_name"],
            birth_date=document["personal_information"]["birth_date"],
            marital_status=document["personal_information"]["marital_status"],
            nationality=document["personal_information"]["nationality"]
        )
        
        # Mapear información de contacto
        contact_info = ContactInformation(
            phone=document["contact_information"]["phone"],
            email=document["contact_information"]["email"],
            address=document["contact_information"]["address"],
            district=document["contact_information"]["district"],
            province=document["contact_information"]["province"],
            department=document["contact_information"]["department"]
        )
        
        # Mapear miembros de familia
        family_members = [
            ApplicationMapper._dict_to_family_member(member_dict)
            for member_dict in document["household_information"]["family_members"]
        ]
        
        # Mapear información del hogar
        household_info = HouseholdInformation(
            household_size=document["household_information"]["household_size"],
            dependents=document["household_information"]["dependents"],
            family_members=family_members
        )
        
        # Mapear información económica
        economic_info = EconomicInformation(
            monthly_income=document["economic_information"]["monthly_income"],
            employment_status=document["economic_information"]["employment_status"],
            employer=document["economic_information"]["employer"],
            other_income=document["economic_information"]["other_income"],
            expenses=document["economic_information"]["expenses"]
        )
        
        # Mapear documentos
        documents = [
            ApplicationMapper._dict_to_document(doc_dict)
            for doc_dict in document["documents"]
        ]
        
        # Crear entidad
        application = TechoPropioApplication(
            application_number=document.get("application_number"),
            convocation_code=document.get("convocation_code"),
            registration_year=document.get("registration_year"),
            sequential_number=document.get("sequential_number"),
            registration_date=document.get("registration_date"),
            status=ApplicationStatus(document["status"]),
            personal_information=personal_info,
            contact_information=contact_info,
            household_information=household_info,
            economic_information=economic_info,
            documents=documents,
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            submitted_at=document.get("submitted_at"),
            reviewed_at=document.get("reviewed_at"),
            approved_at=document.get("approved_at"),
            rejected_at=document.get("rejected_at"),
            notes=document.get("notes", ""),
            priority_score=document.get("priority_score", 0)
        )
        
        # Asignar ID
        application.id = application_id
        
        return application
    
    @staticmethod
    def _family_member_to_dict(member: FamilyMember) -> Dict[str, Any]:
        """Convierte FamilyMember a diccionario"""
        return {
            "dni": member.dni,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "birth_date": member.birth_date,
            "relationship": member.relationship,
            "occupation": member.occupation,
            "monthly_income": member.monthly_income
        }
    
    @staticmethod
    def _dict_to_family_member(member_dict: Dict[str, Any]) -> FamilyMember:
        """Convierte diccionario a FamilyMember"""
        return FamilyMember(
            dni=member_dict["dni"],
            first_name=member_dict["first_name"],
            last_name=member_dict["last_name"],
            birth_date=member_dict["birth_date"],
            relationship=member_dict["relationship"],
            occupation=member_dict["occupation"],
            monthly_income=member_dict["monthly_income"]
        )
    
    @staticmethod
    def _document_to_dict(document: DocumentData) -> Dict[str, Any]:
        """Convierte DocumentData a diccionario"""
        return {
            "document_type": document.document_type,
            "file_path": document.file_path,
            "uploaded_at": document.uploaded_at,
            "file_size": document.file_size,
            "mime_type": document.mime_type
        }
    
    @staticmethod
    def _dict_to_document(doc_dict: Dict[str, Any]) -> DocumentData:
        """Convierte diccionario a DocumentData"""
        return DocumentData(
            document_type=doc_dict["document_type"],
            file_path=doc_dict["file_path"],
            uploaded_at=doc_dict["uploaded_at"],
            file_size=doc_dict["file_size"],
            mime_type=doc_dict["mime_type"]
        )