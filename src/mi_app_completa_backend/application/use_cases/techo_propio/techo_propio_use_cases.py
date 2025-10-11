"""
Orquestador principal de casos de uso para Techo Propio
Coordina todos los casos de uso y proporciona interfaz unificada
"""

from typing import Optional, List, Dict, Any
from datetime import date

# Importar casos de uso
from .create_application_use_case import CreateApplicationUseCase
from .update_application_use_case import UpdateApplicationUseCase
from .query_applications_use_case import QueryApplicationsUseCase
from .validate_dni_use_case import ValidateDniUseCase

# Importar servicios
from ....infrastructure.services.government_apis.ubigeo_validation_service import UbigeoValidationService

# Importar repositorio y servicios de infraestructura
from ....domain.repositories.techo_propio import TechoPropioRepository
from ....infrastructure.services.government_apis.reniec_service import ReniecService

# Importar DTOs
from ...dto.techo_propio import (
    TechoPropioApplicationCreateDTO,
    TechoPropioApplicationUpdateDTO,
    TechoPropioApplicationResponseDTO,
    ApplicationStatusUpdateDTO,
    ApplicationSearchFiltersDTO,
    PaginatedResponseDTO,
    DniValidationRequestDTO,
    DniValidationResponseDTO,
    ApplicantValidationDTO
)
from ...dto.techo_propio.ubigeo_validation_dto import (
    UbigeoValidationRequestDTO,
    UbigeoValidationResponseDTO,
    LocationSearchRequestDTO
)

# Importar value objects
from ....domain.value_objects.techo_propio import ApplicationStatus


class TechoPropioUseCases:
    """
    Orquestador principal de casos de uso para Techo Propio
    Proporciona interfaz unificada para todas las operaciones del módulo
    """
    
    def __init__(
        self,
        repository: TechoPropioRepository,
        reniec_service: ReniecService,
        ubigeo_service: UbigeoValidationService
    ):
        self.repository = repository
        self.reniec_service = reniec_service
        self.ubigeo_service = ubigeo_service
        
        # Inicializar casos de uso
        self.create_use_case = CreateApplicationUseCase(repository)
        self.update_use_case = UpdateApplicationUseCase(repository)
        self.query_use_case = QueryApplicationsUseCase(repository)
        self.validate_dni_use_case = ValidateDniUseCase(reniec_service)
    
    # ==================== OPERACIONES DE SOLICITUD ====================
    
    async def create_application(
        self,
        dto: TechoPropioApplicationCreateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """Crear nueva solicitud Techo Propio"""
        return await self.create_use_case.execute(dto, user_id)
    
    async def update_application(
        self,
        application_id: str,
        dto: TechoPropioApplicationUpdateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """Actualizar solicitud existente"""
        return await self.update_use_case.execute(application_id, dto, user_id)
    
    async def update_application_status(
        self,
        application_id: str,
        dto: ApplicationStatusUpdateDTO,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """Actualizar estado de solicitud"""
        return await self.update_use_case.update_status(application_id, dto, user_id)
    
    async def submit_application(
        self,
        application_id: str,
        user_id: str
    ) -> TechoPropioApplicationResponseDTO:
        """Enviar solicitud para revisión"""
        return await self.update_use_case.submit_application(application_id, user_id)
    
    async def delete_application(
        self,
        application_id: str,
        user_id: str
    ) -> bool:
        """Eliminar solicitud (solo borradores)"""
        # Verificar que existe y está en borrador
        application = await self.repository.get_application_by_id(application_id)
        if not application:
            raise ValueError(f"Solicitud no encontrada: {application_id}")
        
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("Solo se pueden eliminar solicitudes en borrador")
        
        if application.created_by != user_id:
            raise ValueError("Solo el creador puede eliminar la solicitud")
        
        return await self.repository.delete_application(application_id)
    
    # ==================== CONSULTAS DE SOLICITUDES ====================
    
    async def get_application_by_id(
        self,
        application_id: str,
        user_id: Optional[str] = None
    ) -> Optional[TechoPropioApplicationResponseDTO]:
        """Obtener solicitud por ID"""
        return await self.query_use_case.get_application_by_id(application_id, user_id)
    
    async def get_applications_by_user(
        self,
        user_id: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """Obtener solicitudes de un usuario"""
        return await self.query_use_case.get_applications_by_user(
            user_id, status, limit, offset
        )
    
    async def search_applications(
        self,
        filters: ApplicationSearchFiltersDTO,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """Búsqueda avanzada de solicitudes"""
        return await self.query_use_case.search_applications(filters, page, page_size)
    
    async def get_application_by_dni(
        self,
        document_number: str
    ) -> Optional[TechoPropioApplicationResponseDTO]:
        """Obtener solicitud por DNI"""
        return await self.query_use_case.get_application_by_dni(document_number)
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """Obtener solicitudes por estado"""
        return await self.query_use_case.get_applications_by_status(
            status, page, page_size, sort_by, sort_order
        )
    
    async def get_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """Obtener solicitudes por ubicación"""
        return await self.query_use_case.get_applications_by_location(
            department, province, district, page, page_size
        )
    
    async def get_priority_applications(
        self,
        page: int = 1,
        page_size: int = 20,
        min_priority_score: Optional[float] = None
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """Obtener solicitudes por prioridad"""
        return await self.query_use_case.get_priority_applications(
            page, page_size, min_priority_score
        )
    
    # ==================== ESTADÍSTICAS Y REPORTES ====================
    
    async def get_application_statistics(
        self,
        department: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas de solicitudes"""
        return await self.query_use_case.get_application_statistics(
            department, date_from, date_to
        )
    
    async def get_dashboard_summary(
        self,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """Obtener resumen para dashboard"""
        summary = {}
        
        if is_admin:
            # Estadísticas globales para administradores
            summary["total_applications"] = await self.repository.count_all_applications()
            summary["applications_by_status"] = {}
            
            for status in ApplicationStatus:
                count = await self.repository.count_applications_by_status(status)
                summary["applications_by_status"][status.value] = count
            
            # Aplicaciones recientes
            recent_apps = await self.query_use_case.search_applications(
                ApplicationSearchFiltersDTO(sort_by="created_at", sort_order="desc"),
                page=1,
                page_size=5
            )
            summary["recent_applications"] = recent_apps.items
            
            # Aplicaciones prioritarias
            priority_apps = await self.get_priority_applications(page=1, page_size=5)
            summary["priority_applications"] = priority_apps.items
            
        else:
            # Estadísticas de usuario
            if user_id:
                user_apps = await self.get_applications_by_user(user_id, limit=100)
                summary["user_total_applications"] = user_apps.total_count
                
                # Contar por estado
                summary["user_applications_by_status"] = {}
                for app in user_apps.items:
                    status = app.status
                    if status not in summary["user_applications_by_status"]:
                        summary["user_applications_by_status"][status] = 0
                    summary["user_applications_by_status"][status] += 1
                
                # Aplicaciones recientes del usuario
                recent_user_apps = await self.get_applications_by_user(
                    user_id, limit=3
                )
                summary["user_recent_applications"] = recent_user_apps.items
        
        return summary
    
    # ==================== VALIDACIONES ====================
    
    async def validate_dni(
        self,
        dto: DniValidationRequestDTO
    ) -> DniValidationResponseDTO:
        """Validar DNI con RENIEC"""
        return await self.validate_dni_use_case.validate_dni(dto)
    
    async def validate_applicant_data(
        self,
        dto: ApplicantValidationDTO
    ) -> DniValidationResponseDTO:
        """Validar datos completos de solicitante"""
        return await self.validate_dni_use_case.validate_applicant_data(dto)
    
    async def batch_validate_dnis(
        self,
        document_numbers: List[str]
    ) -> Dict[str, DniValidationResponseDTO]:
        """Validar múltiples DNIs"""
        return await self.validate_dni_use_case.batch_validate_dnis(document_numbers)
    
    async def validate_ubigeo_code(
        self,
        ubigeo_code: str
    ) -> UbigeoValidationResponseDTO:
        """Validar código UBIGEO"""
        result = await self.ubigeo_service.validate_ubigeo_code(ubigeo_code)
        
        return UbigeoValidationResponseDTO(
            is_valid=result.is_valid,
            ubigeo_code=result.ubigeo_code,
            department=result.department,
            province=result.province,
            district=result.district,
            validation_errors=result.validation_errors,
            geographic_data=result.geographic_data
        )
    
    async def validate_location_names(
        self,
        department: str,
        province: str,
        district: str
    ) -> UbigeoValidationResponseDTO:
        """Validar nombres de ubicación"""
        result = await self.ubigeo_service.validate_location_names(
            department, province, district
        )
        
        return UbigeoValidationResponseDTO(
            is_valid=result.is_valid,
            ubigeo_code=result.ubigeo_code,
            department=result.department,
            province=result.province,
            district=result.district,
            validation_errors=result.validation_errors,
            geographic_data=result.geographic_data
        )
    
    # ==================== SERVICIOS AUXILIARES ====================
    
    async def get_departments(self) -> List[str]:
        """Obtener lista de departamentos"""
        return await self.ubigeo_service.get_departments()
    
    async def get_departments_with_codes(self) -> List[Dict[str, str]]:
        """Obtener lista de departamentos con códigos"""
        return await self.ubigeo_service.get_departments_with_codes()
    
    async def get_provinces(self, department: str) -> List[str]:
        """Obtener provincias de un departamento"""
        return await self.ubigeo_service.get_provinces(department)
    
    async def get_provinces_with_codes(self, department: str) -> List[Dict[str, str]]:
        """Obtener provincias de un departamento con códigos"""
        return await self.ubigeo_service.get_provinces_with_codes(department)
    
    async def get_districts(self, department: str, province: str) -> List[str]:
        """Obtener distritos de una provincia"""
        return await self.ubigeo_service.get_districts(department, province)
    
    async def get_districts_with_codes(self, department: str, province: str) -> List[Dict[str, str]]:
        """Obtener distritos de una provincia con códigos"""
        return await self.ubigeo_service.get_districts_with_codes(department, province)
    
    async def search_locations(
        self,
        search_term: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar ubicaciones por término"""
        results = await self.ubigeo_service.search_locations(search_term, limit)
        
        return [
            {
                "ubigeo_code": result.ubigeo_code,
                "department": result.department,
                "province": result.province,
                "district": result.district,
                "geographic_data": result.geographic_data
            }
            for result in results
        ]
    
    async def check_dni_availability(
        self,
        document_number: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Verificar disponibilidad de DNI"""
        return not await self.repository.check_dni_exists_in_applications(
            document_number, exclude_application_id
        )
    
    async def get_application_completion_status(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """Obtener estado de completitud de solicitud"""
        application = await self.repository.get_application_by_id(application_id)
        if not application:
            raise ValueError(f"Solicitud no encontrada: {application_id}")
        
        return {
            "application_id": application_id,
            "completion_percentage": application.get_completion_percentage(),
            "can_be_submitted": application.can_be_submitted,
            "missing_fields": application.get_missing_required_fields(),
            "status": application.status.value,
            "is_editable": application.is_editable
        }