"""
Casos de uso para actualizar solicitudes Techo Propio
Maneja actualizaciones parciales y completas con validaciones
"""

from typing import Optional, List
from datetime import datetime

# Importar entidades de dominio
from ....domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, 
    HouseholdMember, EconomicInfo
)
from ....domain.value_objects.techo_propio import ApplicationStatus, EDITABLE_STATUSES
from ....domain.repositories.techo_propio import TechoPropioRepository
from ....domain.services.techo_propio import TechoPropioBusinessRules

# Importar DTOs
from ...dto.techo_propio import (
    TechoPropioApplicationUpdateDTO, TechoPropioApplicationResponseDTO,
    ApplicationStatusUpdateDTO
)

# Importar caso de uso de creación para reutilizar conversión
from .create_application_use_case import CreateApplicationUseCase


class UpdateApplicationUseCase:
    """
    Caso de uso para actualizar solicitudes Techo Propio existentes
    Maneja actualizaciones parciales respetando el estado de la solicitud
    """
    
    def __init__(self, repository: TechoPropioRepository):
        self.repository = repository
        self.business_rules = TechoPropioBusinessRules()
        self.create_use_case = CreateApplicationUseCase(repository)
    
    async def execute(
        self,
        application_id: str,
        dto: TechoPropioApplicationUpdateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """
        Actualizar solicitud existente
        
        Args:
            application_id: ID de la solicitud a actualizar
            dto: Datos de actualización
            user_id: ID del usuario que actualiza
            
        Returns:
            TechoPropioApplicationResponseDTO: Solicitud actualizada
            
        Raises:
            ValueError: Si la solicitud no existe o no puede ser editada
        """
        
        # 1. Obtener solicitud existente
        application = await self._get_existing_application(application_id)
        
        # 2. Verificar que puede ser editada
        self._validate_can_be_edited(application)
        
        # 3. Validar DNIs únicos si se actualizan
        await self._validate_unique_dnis_for_update(dto, application_id)
        
        # 4. Aplicar actualizaciones
        updated_application = await self._apply_updates(application, dto, user_id)
        
        # 5. Aplicar reglas de negocio
        await self._apply_business_rules(updated_application)
        
        # 6. Persistir cambios
        saved_application = await self.repository.update_application(updated_application)
        
        # 7. Convertir a DTO de respuesta
        response_dto = await self.create_use_case._convert_to_response_dto(saved_application)
        
        return response_dto
    
    async def update_status(
        self,
        application_id: str,
        dto: ApplicationStatusUpdateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """
        Actualizar estado de solicitud
        
        Args:
            application_id: ID de la solicitud
            dto: Datos del cambio de estado
            user_id: ID del usuario que cambia el estado
            
        Returns:
            TechoPropioApplicationResponseDTO: Solicitud actualizada
        """
        
        # 1. Obtener solicitud existente
        application = await self._get_existing_application(application_id)
        
        # 2. Aplicar cambio de estado
        self._apply_status_change(application, dto, user_id)
        
        # 3. Persistir cambios
        saved_application = await self.repository.update_application(application)
        
        # 4. Convertir a DTO de respuesta
        response_dto = await self.create_use_case._convert_to_response_dto(saved_application)
        
        return response_dto
    
    async def submit_application(
        self,
        application_id: str,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """
        Enviar solicitud para revisión
        
        Args:
            application_id: ID de la solicitud
            user_id: ID del usuario que envía
            
        Returns:
            TechoPropioApplicationResponseDTO: Solicitud enviada
        """
        
        # 1. Obtener solicitud existente
        application = await self._get_existing_application(application_id)
        
        # 2. Validar que puede ser enviada
        if not application.can_be_submitted:
            completion = application.get_completion_percentage()
            raise ValueError(f"La solicitud no está completa para envío (completitud: {completion:.1f}%)")
        
        # 3. Enviar solicitud
        application.submit_application(user_id)
        
        # 4. Persistir cambios
        saved_application = await self.repository.update_application(application)
        
        # 5. Convertir a DTO de respuesta
        response_dto = await self.create_use_case._convert_to_response_dto(saved_application)
        
        return response_dto
    
    async def _get_existing_application(self, application_id: str) -> TechoPropioApplication:
        """Obtener solicitud existente con validación"""
        application = await self.repository.get_application_by_id(application_id)
        if not application:
            raise ValueError(f"Solicitud no encontrada: {application_id}")
        return application
    
    def _validate_can_be_edited(self, application: TechoPropioApplication) -> None:
        """Validar que la solicitud puede ser editada"""
        if not application.is_editable:
            raise ValueError(f"La solicitud en estado '{application.status.value}' no puede ser editada")
    
    async def _validate_unique_dnis_for_update(
        self, 
        dto: TechoPropioApplicationUpdateDTO,
        application_id: str
    ) -> None:
        """Validar DNIs únicos para actualización"""
        dnis_to_check = set()
        
        # Recopilar DNIs que se van a actualizar
        if dto.main_applicant:
            dnis_to_check.add(dto.main_applicant.document_number)
        if dto.spouse:
            dnis_to_check.add(dto.spouse.document_number)
        if dto.household_members:
            for member in dto.household_members:
                dnis_to_check.add(member.document_number)
        
        # Verificar cada DNI en el sistema (excluyendo la solicitud actual)
        for dni in dnis_to_check:
            exists = await self.repository.check_dni_exists_in_applications(
                dni, 
                exclude_application_id=application_id
            )
            if exists:
                raise ValueError(f"El DNI {dni} ya está registrado en otra solicitud activa")
    
    async def _apply_updates(
        self,
        application: TechoPropioApplication,
        dto: TechoPropioApplicationUpdateDTO,
        user_id: str
    ) -> TechoPropioApplication:
        """Aplicar actualizaciones a la solicitud"""
        
        # Actualizar solicitante principal
        if dto.main_applicant:
            application.main_applicant = Applicant(
                document_type=dto.main_applicant.document_type,
                document_number=dto.main_applicant.document_number,
                first_name=dto.main_applicant.first_name,
                paternal_surname=dto.main_applicant.paternal_surname,
                maternal_surname=dto.main_applicant.maternal_surname,
                birth_date=dto.main_applicant.birth_date,
                civil_status=dto.main_applicant.civil_status,
                education_level=dto.main_applicant.education_level,
                occupation=dto.main_applicant.occupation,
                disability_type=dto.main_applicant.disability_type,
                is_main_applicant=True,
                phone_number=dto.main_applicant.phone_number,
                email=dto.main_applicant.email
            )
        
        # Actualizar información del predio
        if dto.property_info:
            application.property_info = PropertyInfo(
                department=dto.property_info.department,
                province=dto.property_info.province,
                district=dto.property_info.district,
                lote=dto.property_info.lote,
                ubigeo_code=dto.property_info.ubigeo_code,
                populated_center=dto.property_info.populated_center,
                manzana=dto.property_info.manzana,
                sub_lote=dto.property_info.sub_lote,
                reference=dto.property_info.reference,
                latitude=dto.property_info.latitude,
                longitude=dto.property_info.longitude
            )
        
        # Actualizar información económica principal
        if dto.main_applicant_economic:
            application.main_applicant_economic = EconomicInfo(
                employment_situation=dto.main_applicant_economic.employment_situation,
                monthly_income=dto.main_applicant_economic.monthly_income,
                applicant_id=application.main_applicant.id,
                work_condition=dto.main_applicant_economic.work_condition,
                occupation_detail=dto.main_applicant_economic.occupation_detail,
                employer_name=dto.main_applicant_economic.employer_name,
                has_additional_income=dto.main_applicant_economic.has_additional_income,
                additional_income_amount=dto.main_applicant_economic.additional_income_amount,
                additional_income_source=dto.main_applicant_economic.additional_income_source,
                is_main_applicant=True
            )
        
        # Actualizar cónyuge
        if dto.spouse is not None:
            if dto.spouse:  # Si viene con datos, actualizar
                spouse = Applicant(
                    document_type=dto.spouse.document_type,
                    document_number=dto.spouse.document_number,
                    first_name=dto.spouse.first_name,
                    paternal_surname=dto.spouse.paternal_surname,
                    maternal_surname=dto.spouse.maternal_surname,
                    birth_date=dto.spouse.birth_date,
                    civil_status=dto.spouse.civil_status,
                    education_level=dto.spouse.education_level,
                    occupation=dto.spouse.occupation,
                    disability_type=dto.spouse.disability_type,
                    is_main_applicant=False,
                    phone_number=dto.spouse.phone_number,
                    email=dto.spouse.email
                )
                application.set_spouse(spouse)
            else:  # Si viene None/vacío, remover cónyuge
                application.remove_spouse()
        
        # Actualizar información económica del cónyuge
        if dto.spouse_economic is not None:
            if dto.spouse_economic and application.spouse:
                application.spouse_economic = EconomicInfo(
                    employment_situation=dto.spouse_economic.employment_situation,
                    monthly_income=dto.spouse_economic.monthly_income,
                    applicant_id=application.spouse.id,
                    work_condition=dto.spouse_economic.work_condition,
                    occupation_detail=dto.spouse_economic.occupation_detail,
                    employer_name=dto.spouse_economic.employer_name,
                    has_additional_income=dto.spouse_economic.has_additional_income,
                    additional_income_amount=dto.spouse_economic.additional_income_amount,
                    additional_income_source=dto.spouse_economic.additional_income_source,
                    is_main_applicant=False
                )
            else:
                application.spouse_economic = None
        
        # Actualizar miembros de carga familiar
        if dto.household_members is not None:
            # Limpiar miembros existentes
            application.household_members = []
            
            # Agregar nuevos miembros
            for member_dto in dto.household_members:
                member = HouseholdMember(
                    first_name=member_dto.first_name,
                    paternal_surname=member_dto.paternal_surname,
                    maternal_surname=member_dto.maternal_surname,
                    document_type=member_dto.document_type,
                    document_number=member_dto.document_number,
                    birth_date=member_dto.birth_date,
                    relationship=member_dto.relationship,
                    education_level=member_dto.education_level,
                    disability_type=member_dto.disability_type,
                    is_dependent=member_dto.is_dependent
                )
                application.household_members.append(member)
        
        # Actualizar metadata
        application.update_metadata(user_id)
        application.version += 1
        
        return application
    
    def _apply_status_change(
        self,
        application: TechoPropioApplication,
        dto: ApplicationStatusUpdateDTO,
        user_id: str
    ) -> None:
        """Aplicar cambio de estado"""
        
        current_status = application.status
        new_status = dto.new_status
        
        # Validar transiciones de estado válidas
        valid_transitions = self._get_valid_status_transitions(current_status)
        if new_status not in valid_transitions:
            raise ValueError(f"Transición de estado inválida: {current_status.value} -> {new_status.value}")
        
        # Aplicar cambio según el nuevo estado
        if new_status == ApplicationStatus.SUBMITTED:
            if current_status == ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
                application.resubmit_after_additional_info()
            else:
                application.submit_application(user_id)
        
        elif new_status == ApplicationStatus.UNDER_REVIEW:
            application.start_review(dto.reviewer_id)
        
        elif new_status == ApplicationStatus.APPROVED:
            application.approve_application(dto.reviewer_id, dto.comments)
        
        elif new_status == ApplicationStatus.REJECTED:
            application.reject_application(dto.reviewer_id, dto.reason, dto.comments)
        
        elif new_status == ApplicationStatus.ADDITIONAL_INFO_REQUIRED:
            application.request_additional_info(dto.reviewer_id, dto.comments)
        
        elif new_status == ApplicationStatus.CANCELLED:
            application.cancel_application(user_id)
    
    def _get_valid_status_transitions(self, current_status: ApplicationStatus) -> List[ApplicationStatus]:
        """Obtener transiciones de estado válidas"""
        transitions = {
            ApplicationStatus.DRAFT: [
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.CANCELLED
            ],
            ApplicationStatus.SUBMITTED: [
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.CANCELLED
            ],
            ApplicationStatus.UNDER_REVIEW: [
                ApplicationStatus.APPROVED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.ADDITIONAL_INFO_REQUIRED
            ],
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED: [
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.CANCELLED
            ],
            ApplicationStatus.APPROVED: [
                ApplicationStatus.REJECTED  # ✅ Permitir revertir aprobación a rechazado
            ],
            ApplicationStatus.REJECTED: [],  # Estado final
            ApplicationStatus.CANCELLED: [] # Estado final
        }
        
        return transitions.get(current_status, [])
    
    async def _apply_business_rules(self, application: TechoPropioApplication) -> None:
        """Aplicar reglas de negocio para actualización"""
        
        # Solo aplicar reglas de negocio si la solicitud va a ser enviada
        if application.status in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
            # Validar criterios de elegibilidad
            is_eligible, errors = self.business_rules.validate_eligibility_criteria(application)
            if not is_eligible:
                raise ValueError(f"La solicitud no cumple criterios de elegibilidad: {'; '.join(errors)}")
            
            # Validar consistencia familiar
            family_errors = self.business_rules.validate_family_consistency(application)
            if family_errors:
                raise ValueError(f"Inconsistencias familiares detectadas: {'; '.join(family_errors)}")