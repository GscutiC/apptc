"""
Casos de uso para crear solicitudes Techo Propio
Orquesta las entidades de dominio y aplica reglas de negocio
"""

import os
import logging
from typing import Optional, List, Tuple
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)

# Importar entidades de dominio
from ....domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo, 
    HouseholdMember, EconomicInfo
)
from ....domain.value_objects.techo_propio import ApplicationStatus
from ....domain.repositories.techo_propio import TechoPropioRepository
from ....domain.repositories.techo_propio import ConvocationRepository
from ....domain.services.techo_propio import TechoPropioBusinessRules

# Importar DTOs
from ...dto.techo_propio import (
    TechoPropioApplicationCreateDTO, TechoPropioApplicationResponseDTO,
    UserDataResponseDTO, ApplicantResponseDTO, PropertyInfoResponseDTO, 
    HouseholdMemberResponseDTO, EconomicInfoResponseDTO
)

# Importar UserData del dominio
from ....domain.entities.techo_propio.application_entity import UserData


class CreateApplicationUseCase:
    """
    Caso de uso para crear nueva solicitud Techo Propio
    Coordina la creación de todas las entidades relacionadas
    """

    def __init__(
        self, 
        repository: TechoPropioRepository,
        convocation_repository: Optional[ConvocationRepository] = None
    ):
        self.repository = repository
        self.convocation_repository = convocation_repository
        self.business_rules = TechoPropioBusinessRules()

        # ✅ MEJORA: Flag de entorno para modo desarrollo
        self.dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        self.skip_dni_validation = os.getenv("SKIP_DNI_VALIDATION", "false").lower() == "true"

        if self.dev_mode:
            logger.warning("⚠️  MODO DESARROLLO ACTIVADO - Validaciones reducidas")
        if self.skip_dni_validation:
            logger.warning("⚠️  VALIDACIÓN DE DNI DESACTIVADA - Solo para desarrollo")
    
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
        
        # 3. Generar código de solicitud con formato convocatoria
        await self._generate_application_number(application)
        
        # 4. Aplicar reglas de negocio
        await self._apply_business_rules(application)
        
        # 5. Persistir la solicitud
        saved_application = await self.repository.create_application(application)
        
        # 6. Convertir a DTO de respuesta
        response_dto = await self._convert_to_response_dto(saved_application)
        
        return response_dto
    
    async def _validate_unique_dnis(self, dto: TechoPropioApplicationCreateDTO) -> None:
        """
        Validar que los DNIs no estén duplicados en el sistema

        ✅ MEJORA: Controlado por flags de entorno
        - PRODUCCIÓN: Validación completa activada
        - DESARROLLO: Puede desactivarse con SKIP_DNI_VALIDATION=true
        """
        # Si está en modo desarrollo y se permite duplicados, salir
        if self.skip_dni_validation:
            logger.warning("⚠️  Saltando validación de DNIs únicos (SKIP_DNI_VALIDATION=true)")
            return

        all_dnis = set()

        # Recopilar todos los DNIs de la solicitud
        all_dnis.add(dto.user_data.dni)  # DNI del usuario (control interno)
        all_dnis.add(dto.head_of_family.document_number)  # DNI del jefe de familia

        if dto.spouse:
            all_dnis.add(dto.spouse.document_number)

        for member in dto.household_members:
            all_dnis.add(member.document_number)

        # ✅ PRODUCCIÓN: Verificar cada DNI en el sistema
        logger.info(f"Validando {len(all_dnis)} DNIs únicos en el sistema")

        for dni in all_dnis:
            exists = await self.repository.check_dni_exists_in_applications(dni)
            if exists:
                logger.error(f"DNI duplicado detectado: {dni}")
                raise ValueError(
                    f"El DNI {dni} ya está registrado en otra solicitud activa. "
                    f"Cada persona solo puede estar en una solicitud a la vez."
                )

        logger.info("✅ Validación de DNIs únicos completada exitosamente")
    
    async def _create_application_entities(
        self, 
        dto: TechoPropioApplicationCreateDTO,
        user_id: str
    ) -> TechoPropioApplication:
        """Crear todas las entidades de dominio desde DTOs"""
        
        # ✅ NUEVA LÓGICA: Crear datos de usuario para control interno
        user_data = UserData(
            dni=dto.user_data.dni,
            names=dto.user_data.names,
            surnames=dto.user_data.surnames,
            phone=dto.user_data.phone,
            email=dto.user_data.email,
            birth_date=dto.user_data.birth_date,
            notes=dto.user_data.notes
        )
        
        # ✅ CAMBIO: Crear jefe de familia (antes era main_applicant)
        head_of_family = Applicant(
            document_type=dto.head_of_family.document_type,
            document_number=dto.head_of_family.document_number,
            first_name=dto.head_of_family.first_name,
            paternal_surname=dto.head_of_family.paternal_surname,
            maternal_surname=dto.head_of_family.maternal_surname,
            birth_date=dto.head_of_family.birth_date,
            civil_status=dto.head_of_family.civil_status,
            education_level=dto.head_of_family.education_level,
            occupation=dto.head_of_family.occupation,
            disability_type=dto.head_of_family.disability_type,
            disability_is_permanent=dto.head_of_family.disability_is_permanent,  # ✅ NUEVO
            disability_is_severe=dto.head_of_family.disability_is_severe,  # ✅ NUEVO
            is_main_applicant=True,
            phone_number=dto.head_of_family.phone_number,
            email=dto.head_of_family.email
        )
        
        # Crear información del predio
        property_info = PropertyInfo(
            department=dto.property_info.department,
            province=dto.property_info.province,
            district=dto.property_info.district,
            lote=dto.property_info.lote,
            address=dto.property_info.address,  # ← CAMPO FALTANTE AGREGADO
            ubigeo_code=dto.property_info.ubigeo_code,
            populated_center=dto.property_info.populated_center,
            manzana=dto.property_info.manzana,
            sub_lote=dto.property_info.sub_lote,
            reference=dto.property_info.reference,
            latitude=dto.property_info.latitude,
            longitude=dto.property_info.longitude
        )
        
        # ✅ CAMBIO: Crear información económica del jefe de familia
        head_of_family_economic = EconomicInfo(
            employment_situation=dto.head_of_family_economic.employment_situation,
            monthly_income=dto.head_of_family_economic.monthly_income,
            applicant_id=head_of_family.id,
            work_condition=dto.head_of_family_economic.work_condition,
            occupation_detail=dto.head_of_family_economic.occupation_detail,
            employer_name=dto.head_of_family_economic.employer_name,
            has_additional_income=dto.head_of_family_economic.has_additional_income,
            additional_income_amount=dto.head_of_family_economic.additional_income_amount,
            additional_income_source=dto.head_of_family_economic.additional_income_source,
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
                disability_is_permanent=dto.spouse.disability_is_permanent,  # ✅ NUEVO
                disability_is_severe=dto.spouse.disability_is_severe,  # ✅ NUEVO
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
                civil_status=member_dto.civil_status,  # ✅ FIX: Campo agregado
                education_level=member_dto.education_level,
                occupation=member_dto.occupation,  # ✅ FIX: Campo agregado
                employment_situation=member_dto.employment_situation,  # ✅ FIX: Campo agregado
                work_condition=member_dto.work_condition,  # ✅ FIX: Campo agregado
                monthly_income=member_dto.monthly_income,  # ✅ FIX: Campo agregado
                disability_type=member_dto.disability_type,
                disability_is_permanent=member_dto.disability_is_permanent,  # ✅ NUEVO
                disability_is_severe=member_dto.disability_is_severe,  # ✅ NUEVO
                relationship=member_dto.relationship,
                is_dependent=member_dto.is_dependent
            )
            household_members.append(member)
        
        # ✅ NUEVA LÓGICA: Crear solicitud principal con separación usuario/jefe de familia
        application = TechoPropioApplication(
            status=ApplicationStatus.DRAFT,
            convocation_code=dto.convocation_code,
            user_data=user_data,  # ✅ NUEVO: Datos de usuario para control interno
            head_of_family=head_of_family,  # ✅ CAMBIO: Jefe de familia (antes main_applicant)
            spouse=spouse,
            property_info=property_info,
            household_members=household_members,
            head_of_family_economic=head_of_family_economic,  # ✅ CAMBIO: Info económica jefe de familia
            spouse_economic=spouse_economic,
            user_id=user_id,
            created_by=user_id,  # Para auditoría
            updated_by=user_id
        )
        
        return application
    
    async def _apply_business_rules(self, application: TechoPropioApplication) -> None:
        """
        Aplicar reglas de negocio y validaciones

        ✅ MEJORA: Controlado por flags de entorno
        - PRODUCCIÓN: Todas las validaciones activas
        - DESARROLLO: Puede desactivarse con DEV_MODE=true
        """
        if self.dev_mode:
            logger.warning("⚠️  Saltando validaciones de negocio (DEV_MODE=true)")
            logger.info("📝 En producción se validarán: elegibilidad, consistencia familiar, puntaje de prioridad")
            return

        logger.info("Aplicando reglas de negocio...")

        # 1. Validar criterios de elegibilidad
        is_eligible, errors = self.business_rules.validate_eligibility_criteria(application)
        if not is_eligible:
            logger.error(f"Solicitud no cumple criterios de elegibilidad: {errors}")
            raise ValueError(f"La solicitud no cumple criterios de elegibilidad: {'; '.join(errors)}")

        logger.info("✅ Criterios de elegibilidad validados")

        # 2. Validar consistencia familiar
        family_errors = self.business_rules.validate_family_consistency(application)
        if family_errors:
            logger.error(f"Inconsistencias familiares: {family_errors}")
            raise ValueError(f"Inconsistencias familiares detectadas: {'; '.join(family_errors)}")

        logger.info("✅ Consistencia familiar validada")

        # 3. Calcular puntaje de prioridad
        priority_score = self.business_rules.calculate_priority_score(application)
        application.priority_score = priority_score

        logger.info(f"✅ Puntaje de prioridad calculado: {priority_score:.2f}")
        logger.info("✅ Todas las reglas de negocio aplicadas correctamente")
    
    async def _generate_application_number(self, application: TechoPropioApplication) -> None:
        """
        Generar código de solicitud con formato convocatoria
        
        Formato:
        - Con convocatoria: CONV-2025-01-015
        - Sin convocatoria: TP-2025-000015
        
        El número es atómico y garantiza no duplicados usando MongoDB findAndModify
        """
        try:
            if application.convocation_code and self.convocation_repository:
                # Obtener siguiente número secuencial de la convocatoria
                logger.info(f"Obteniendo secuencial para convocatoria: {application.convocation_code}")
                
                sequential_number = await self.convocation_repository.get_next_application_sequential(
                    application.convocation_code
                )
                
                logger.info(f"✅ Secuencial obtenido: {sequential_number}")
                
                # Generar código con formato convocatoria
                application.generate_application_number(
                    sequential_number=sequential_number,
                    convocation_code=application.convocation_code
                )
                
                logger.info(f"✅ Código generado: {application.application_number}")
                
            else:
                # Fallback: usar timestamp si no hay convocatoria
                import time
                timestamp_seq = int(time.time()) % 1000000
                application.generate_application_number(
                    sequential_number=timestamp_seq,
                    convocation_code=None
                )
                
                logger.warning(f"⚠️ Código generado sin convocatoria: {application.application_number}")
                
        except Exception as e:
            logger.error(f"Error generando código de solicitud: {e}")
            # Fallback: usar timestamp para garantizar unicidad
            import time
            fallback_seq = int(time.time()) % 1000000
            application.generate_application_number(
                sequential_number=fallback_seq,
                convocation_code=None
            )
            logger.warning(f"⚠️ Usando código fallback: {application.application_number}")
    
    async def _convert_to_response_dto(
        self, 
        application: TechoPropioApplication
    ) -> TechoPropioApplicationResponseDTO:
        """Convertir entidad de dominio a DTO de respuesta"""
        
        # ✅ NUEVA LÓGICA: Convertir datos de usuario
        user_data_dto = None
        if application.user_data:
            user_data_dto = UserDataResponseDTO(
                dni=application.user_data.dni,
                names=application.user_data.names,
                surnames=application.user_data.surnames,
                full_name=application.user_data.full_name,
                phone=application.user_data.phone,
                email=application.user_data.email,
                birth_date=application.user_data.birth_date if application.user_data.birth_date else None,
                notes=application.user_data.notes
            )
        
        # ✅ CAMBIO: Convertir jefe de familia (antes main_applicant)
        head_of_family_dto = ApplicantResponseDTO(
            id=application.head_of_family.id,
            document_type=application.head_of_family.document_type,
            document_number=application.head_of_family.document_number,
            first_name=application.head_of_family.first_name,
            paternal_surname=application.head_of_family.paternal_surname,
            maternal_surname=application.head_of_family.maternal_surname,
            full_name=application.head_of_family.full_name,
            birth_date=application.head_of_family.birth_date,
            age=application.head_of_family.age,
            civil_status=application.head_of_family.civil_status,
            education_level=application.head_of_family.education_level,
            occupation=application.head_of_family.occupation,
            disability_type=application.head_of_family.disability_type,
            disability_is_permanent=application.head_of_family.disability_is_permanent,  # ✅ NUEVO
            disability_is_severe=application.head_of_family.disability_is_severe,  # ✅ NUEVO
            is_main_applicant=application.head_of_family.is_main_applicant,
            phone_number=application.head_of_family.phone_number,
            email=application.head_of_family.email,
            # ✅ NUEVO: Agregar current_address copiando desde property_info para compatibilidad con frontend
            current_address={
                "department": application.property_info.department,
                "province": application.property_info.province,
                "district": application.property_info.district,
                "address": application.property_info.address,
                "reference": application.property_info.reference,
                "ubigeo_code": application.property_info.ubigeo_code
            },
            reniec_validated=application.head_of_family.reniec_validated,
            reniec_validation_date=application.head_of_family.reniec_validation_date
        )
        
        # Convertir información del predio
        property_dto = PropertyInfoResponseDTO(
            id=application.property_info.id,
            department=application.property_info.department,
            province=application.property_info.province,
            district=application.property_info.district,
            lote=application.property_info.lote,
            address=application.property_info.address,  # ✅ FIX: Campo address agregado
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
        
        # ✅ CAMBIO: Convertir información económica del jefe de familia
        head_of_family_economic_dto = EconomicInfoResponseDTO(
            id=application.head_of_family_economic.id,
            employment_situation=application.head_of_family_economic.employment_situation,
            work_condition=application.head_of_family_economic.work_condition,
            occupation_detail=application.head_of_family_economic.occupation_detail,
            employer_name=application.head_of_family_economic.employer_name,
            monthly_income=application.head_of_family_economic.monthly_income,
            has_additional_income=application.head_of_family_economic.has_additional_income,
            additional_income_amount=application.head_of_family_economic.additional_income_amount,
            additional_income_source=application.head_of_family_economic.additional_income_source,
            total_monthly_income=application.head_of_family_economic.total_monthly_income,
            annual_income=application.head_of_family_economic.annual_income,
            is_main_applicant=application.head_of_family_economic.is_main_applicant,
            income_level_category=application.head_of_family_economic.get_income_level_category()
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
                disability_is_permanent=application.spouse.disability_is_permanent,  # ✅ NUEVO
                disability_is_severe=application.spouse.disability_is_severe,  # ✅ NUEVO
                is_main_applicant=application.spouse.is_main_applicant,
                phone_number=application.spouse.phone_number,
                email=application.spouse.email,
                # ✅ NUEVO: Agregar current_address copiando desde property_info para compatibilidad con frontend
                current_address={
                    "department": application.property_info.department,
                    "province": application.property_info.province,
                    "district": application.property_info.district,
                    "address": application.property_info.address,
                    "reference": application.property_info.reference,
                    "ubigeo_code": application.property_info.ubigeo_code
                },
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
                disability_is_permanent=member.disability_is_permanent,  # ✅ NUEVO
                disability_is_severe=member.disability_is_severe,  # ✅ NUEVO
                civil_status=member.civil_status,
                occupation=member.occupation,
                employment_situation=member.employment_situation,
                work_condition=member.work_condition,
                monthly_income=member.monthly_income,
                is_dependent=member.is_dependent
            )
            household_dtos.append(member_dto)
        
        # Crear DTO de respuesta principal
        response_dto = TechoPropioApplicationResponseDTO(
            id=application.id,
            application_number=application.application_number,
            status=application.status,
            
            # ✅ NUEVOS CAMPOS: Información de registro
            registration_date=application.registration_date,
            convocation_code=application.convocation_code,
            registration_year=application.registration_year,
            sequential_number=application.sequential_number,
            
            # ✅ NUEVA LÓGICA: Separación usuario/jefe de familia
            user_data=user_data_dto,
            head_of_family=head_of_family_dto,
            property_info=property_dto,
            head_of_family_economic=head_of_family_economic_dto,
            spouse=spouse_dto,
            spouse_economic=spouse_economic_dto,
            household_members=household_dtos,
            
            # Información calculada
            total_household_size=application.total_household_size,
            total_family_income=application.total_family_income,
            per_capita_income=application.per_capita_income,
            completion_percentage=application.get_completion_percentage(),
            priority_score=0.0,  # TEMPORALMENTE DESHABILITADO - self.business_rules.calculate_priority_score(application),
            
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