"""
Casos de uso para crear solicitudes Techo Propio
Orquesta las entidades de dominio y aplica reglas de negocio
"""

from typing import Optional, List, Tuple
from datetime import datetime
from decimal import Decimal

# Importar entidades de dominio
from ....domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, 
    HouseholdMember, EconomicInfo
)
from ....domain.value_objects.techo_propio import ApplicationStatus
from ....domain.repositories.techo_propio import TechoPropioRepository
from ....domain.services.techo_propio import TechoPropioBusinessRules

# Importar DTOs
from ...dto.techo_propio import (
    TechoPropioApplicationCreateDTO, TechoPropioApplicationResponseDTO,
    ApplicantResponseDTO, PropertyInfoResponseDTO, HouseholdMemberResponseDTO,
    EconomicInfoResponseDTO
)


class CreateApplicationUseCase:
    """
    Caso de uso para crear nueva solicitud Techo Propio
    Coordina la creación de todas las entidades relacionadas
    """
    
    def __init__(self, repository: TechoPropioRepository):
        self.repository = repository
        self.business_rules = TechoPropioBusinessRules()
    
    async def execute(
        self, 
        dto: TechoPropioApplicationCreateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """
        Crear nueva solicitud Techo Propio
        
        Args:
            dto: Datos de la solicitud
            user_id: ID del usuario que crea la solicitud (Clerk ID)
            
        Returns:
            TechoPropioApplicationResponseDTO: Solicitud creada
            
        Raises:
            ValueError: Si los datos no son válidos o fallan las reglas de negocio
        """
        
        # 1. Verificar DNIs únicos en el sistema
        await self._validate_unique_dnis(dto)
        
        # 2. Crear entidades de dominio
        application = await self._create_application_entities(dto, user_id)
        
        # 3. Aplicar reglas de negocio
        await self._apply_business_rules(application)
        
        # 4. Persistir la solicitud
        saved_application = await self.repository.create_application(application)
        
        # 5. Convertir a DTO de respuesta
        response_dto = await self._convert_to_response_dto(saved_application)
        
        return response_dto
    
    async def _validate_unique_dnis(self, dto: TechoPropioApplicationCreateDTO) -> None:
        """Validar que los DNIs no estén duplicados en el sistema"""
        all_dnis = set()
        
        # Recopilar DNIs de la solicitud
        all_dnis.add(dto.main_applicant.document_number)
        if dto.spouse:
            all_dnis.add(dto.spouse.document_number)
        for member in dto.household_members:
            all_dnis.add(member.document_number)
        
        # Verificar cada DNI en el sistema
        for dni in all_dnis:
            exists = await self.repository.check_dni_exists_in_applications(dni)
            if exists:
                raise ValueError(f"El DNI {dni} ya está registrado en otra solicitud activa")
    
    async def _create_application_entities(
        self, 
        dto: TechoPropioApplicationCreateDTO,
        user_id: str
    ) -> TechoPropioApplication:
        """Crear todas las entidades de dominio desde DTOs"""
        
        # Crear solicitante principal
        main_applicant = Applicant(
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
        
        # Crear información del predio
        property_info = PropertyInfo(
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
        
        # Crear información económica del solicitante principal
        main_economic = EconomicInfo(
            employment_situation=dto.main_applicant_economic.employment_situation,
            monthly_income=dto.main_applicant_economic.monthly_income,
            applicant_id=main_applicant.id,
            work_condition=dto.main_applicant_economic.work_condition,
            occupation_detail=dto.main_applicant_economic.occupation_detail,
            employer_name=dto.main_applicant_economic.employer_name,
            has_additional_income=dto.main_applicant_economic.has_additional_income,
            additional_income_amount=dto.main_applicant_economic.additional_income_amount,
            additional_income_source=dto.main_applicant_economic.additional_income_source,
            is_main_applicant=True
        )
        
        # Crear cónyuge si existe
        spouse = None
        spouse_economic = None
        if dto.spouse:
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
            
            if dto.spouse_economic:
                spouse_economic = EconomicInfo(
                    employment_situation=dto.spouse_economic.employment_situation,
                    monthly_income=dto.spouse_economic.monthly_income,
                    applicant_id=spouse.id,
                    work_condition=dto.spouse_economic.work_condition,
                    occupation_detail=dto.spouse_economic.occupation_detail,
                    employer_name=dto.spouse_economic.employer_name,
                    has_additional_income=dto.spouse_economic.has_additional_income,
                    additional_income_amount=dto.spouse_economic.additional_income_amount,
                    additional_income_source=dto.spouse_economic.additional_income_source,
                    is_main_applicant=False
                )
        
        # Crear miembros de carga familiar
        household_members = []
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
            household_members.append(member)
        
        # Crear solicitud principal
        application = TechoPropioApplication(
            status=ApplicationStatus.DRAFT,
            main_applicant=main_applicant,
            spouse=spouse,
            property_info=property_info,
            household_members=household_members,
            main_applicant_economic=main_economic,
            spouse_economic=spouse_economic,
            user_id=user_id,
            created_by=user_id
        )
        
        return application
    
    async def _apply_business_rules(self, application: TechoPropioApplication) -> None:
        """Aplicar reglas de negocio y validaciones"""
        
        # 1. Validar criterios de elegibilidad
        is_eligible, errors = self.business_rules.validate_eligibility_criteria(application)
        if not is_eligible:
            raise ValueError(f"La solicitud no cumple criterios de elegibilidad: {'; '.join(errors)}")
        
        # 2. Validar consistencia familiar
        family_errors = self.business_rules.validate_family_consistency(application)
        if family_errors:
            raise ValueError(f"Inconsistencias familiares detectadas: {'; '.join(family_errors)}")
        
        # 3. Calcular puntaje de prioridad
        priority_score = self.business_rules.calculate_priority_score(application)
        # Nota: El puntaje se calcula pero no se almacena en la entidad directamente
        # Se puede usar para logs o análisis posterior
    
    async def _convert_to_response_dto(
        self, 
        application: TechoPropioApplication
    ) -> TechoPropioApplicationResponseDTO:
        """Convertir entidad de dominio a DTO de respuesta"""
        
        # Convertir solicitante principal
        main_applicant_dto = ApplicantResponseDTO(
            id=application.main_applicant.id,
            document_type=application.main_applicant.document_type,
            document_number=application.main_applicant.document_number,
            first_name=application.main_applicant.first_name,
            paternal_surname=application.main_applicant.paternal_surname,
            maternal_surname=application.main_applicant.maternal_surname,
            full_name=application.main_applicant.full_name,
            birth_date=application.main_applicant.birth_date,
            age=application.main_applicant.age,
            civil_status=application.main_applicant.civil_status,
            education_level=application.main_applicant.education_level,
            occupation=application.main_applicant.occupation,
            disability_type=application.main_applicant.disability_type,
            is_main_applicant=application.main_applicant.is_main_applicant,
            phone_number=application.main_applicant.phone_number,
            email=application.main_applicant.email,
            reniec_validated=application.main_applicant.reniec_validated,
            reniec_validation_date=application.main_applicant.reniec_validation_date
        )
        
        # Convertir información del predio
        property_dto = PropertyInfoResponseDTO(
            id=application.property_info.id,
            department=application.property_info.department,
            province=application.property_info.province,
            district=application.property_info.district,
            lote=application.property_info.lote,
            ubigeo_code=application.property_info.ubigeo_code,
            populated_center=application.property_info.populated_center,
            manzana=application.property_info.manzana,
            sub_lote=application.property_info.sub_lote,
            reference=application.property_info.reference,
            latitude=application.property_info.latitude,
            longitude=application.property_info.longitude,
            ubigeo_validated=application.property_info.ubigeo_validated,
            full_address=application.property_info.full_address,
            short_address=application.property_info.short_address
        )
        
        # Convertir información económica principal
        main_economic_dto = EconomicInfoResponseDTO(
            id=application.main_applicant_economic.id,
            employment_situation=application.main_applicant_economic.employment_situation,
            work_condition=application.main_applicant_economic.work_condition,
            occupation_detail=application.main_applicant_economic.occupation_detail,
            employer_name=application.main_applicant_economic.employer_name,
            monthly_income=application.main_applicant_economic.monthly_income,
            has_additional_income=application.main_applicant_economic.has_additional_income,
            additional_income_amount=application.main_applicant_economic.additional_income_amount,
            additional_income_source=application.main_applicant_economic.additional_income_source,
            total_monthly_income=application.main_applicant_economic.total_monthly_income,
            annual_income=application.main_applicant_economic.annual_income,
            is_main_applicant=application.main_applicant_economic.is_main_applicant,
            income_level_category=application.main_applicant_economic.get_income_level_category()
        )
        
        # Convertir cónyuge si existe
        spouse_dto = None
        spouse_economic_dto = None
        if application.spouse:
            spouse_dto = ApplicantResponseDTO(
                id=application.spouse.id,
                document_type=application.spouse.document_type,
                document_number=application.spouse.document_number,
                first_name=application.spouse.first_name,
                paternal_surname=application.spouse.paternal_surname,
                maternal_surname=application.spouse.maternal_surname,
                full_name=application.spouse.full_name,
                birth_date=application.spouse.birth_date,
                age=application.spouse.age,
                civil_status=application.spouse.civil_status,
                education_level=application.spouse.education_level,
                occupation=application.spouse.occupation,
                disability_type=application.spouse.disability_type,
                is_main_applicant=application.spouse.is_main_applicant,
                phone_number=application.spouse.phone_number,
                email=application.spouse.email,
                reniec_validated=application.spouse.reniec_validated,
                reniec_validation_date=application.spouse.reniec_validation_date
            )
        
        if application.spouse_economic:
            spouse_economic_dto = EconomicInfoResponseDTO(
                id=application.spouse_economic.id,
                employment_situation=application.spouse_economic.employment_situation,
                work_condition=application.spouse_economic.work_condition,
                occupation_detail=application.spouse_economic.occupation_detail,
                employer_name=application.spouse_economic.employer_name,
                monthly_income=application.spouse_economic.monthly_income,
                has_additional_income=application.spouse_economic.has_additional_income,
                additional_income_amount=application.spouse_economic.additional_income_amount,
                additional_income_source=application.spouse_economic.additional_income_source,
                total_monthly_income=application.spouse_economic.total_monthly_income,
                annual_income=application.spouse_economic.annual_income,
                is_main_applicant=application.spouse_economic.is_main_applicant,
                income_level_category=application.spouse_economic.get_income_level_category()
            )
        
        # Convertir miembros de carga familiar
        household_dtos = []
        for member in application.household_members:
            member_dto = HouseholdMemberResponseDTO(
                id=member.id,
                first_name=member.first_name,
                paternal_surname=member.paternal_surname,
                maternal_surname=member.maternal_surname,
                full_name=member.full_name,
                document_type=member.document_type,
                document_number=member.document_number,
                birth_date=member.birth_date,
                age=member.age,
                relationship=member.relationship,
                education_level=member.education_level,
                disability_type=member.disability_type,
                is_dependent=member.is_dependent
            )
            household_dtos.append(member_dto)
        
        # Crear DTO de respuesta principal
        response_dto = TechoPropioApplicationResponseDTO(
            id=application.id,
            application_number=application.application_number,
            status=application.status,
            main_applicant=main_applicant_dto,
            property_info=property_dto,
            main_applicant_economic=main_economic_dto,
            spouse=spouse_dto,
            spouse_economic=spouse_economic_dto,
            household_members=household_dtos,
            
            # Información calculada
            total_household_size=application.total_household_size,
            total_family_income=application.total_family_income,
            per_capita_income=application.per_capita_income,
            completion_percentage=application.get_completion_percentage(),
            priority_score=self.business_rules.calculate_priority_score(application),
            
            # Fechas
            submitted_at=application.submitted_at,
            reviewed_at=application.reviewed_at,
            decision_date=application.decision_date,
            
            # Información de procesamiento
            reviewer_id=application.reviewer_id,
            reviewer_comments=application.reviewer_comments,
            rejection_reason=application.rejection_reason,
            
            # Metadata
            user_id=application.user_id,
            version=application.version,
            created_at=application.created_at,
            updated_at=application.updated_at,
            created_by=application.created_by,
            
            # Estados
            is_editable=application.is_editable,
            is_final_status=application.is_final_status,
            can_be_submitted=application.can_be_submitted
        )
        
        return response_dto