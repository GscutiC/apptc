"""
Casos de uso para consultar solicitudes Techo Propio
Maneja búsquedas, filtros, paginación y obtención de datos específicos
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass

# Importar entidades de dominio
from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import ApplicationStatus
from ....domain.repositories.techo_propio import TechoPropioRepository

# Importar DTOs
from ...dto.techo_propio import (
    TechoPropioApplicationResponseDTO, 
    ApplicationSearchFiltersDTO,
    PaginatedResponseDTO
)

# Importar caso de uso de creación para reutilizar conversión
from .create_application_use_case import CreateApplicationUseCase


@dataclass
class ApplicationListQuery:
    """Parámetros para listado de solicitudes"""
    page: int = 1
    page_size: int = 20
    search_term: Optional[str] = None
    status_filter: Optional[ApplicationStatus] = None
    department_filter: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    user_id_filter: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"


class QueryApplicationsUseCase:
    """
    Caso de uso para consultar y buscar solicitudes Techo Propio
    Proporciona funcionalidades de búsqueda, filtrado y paginación
    """
    
    def __init__(self, repository: TechoPropioRepository):
        self.repository = repository
        self.create_use_case = CreateApplicationUseCase(repository)
    
    async def get_application_by_id(
        self,
        application_id: str,
        user_id: Optional[str] = None
    ) -> Optional[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitud específica por ID
        
        Args:
            application_id: ID de la solicitud
            user_id: ID del usuario (para validaciones de permisos)
            
        Returns:
            TechoPropioApplicationResponseDTO o None si no existe
        """
        
        application = await self.repository.get_application_by_id(application_id)
        if not application:
            return None
        
        # Convertir a DTO de respuesta
        response_dto = await self.create_use_case._convert_to_response_dto(application)
        return response_dto
    
    async def get_applications_by_user(
        self,
        user_id: str,
        status_filter: Optional[ApplicationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitudes de un usuario específico
        
        Args:
            user_id: ID del usuario
            status_filter: Filtro por estado (opcional)
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            PaginatedResponseDTO con las solicitudes del usuario
        """
        
        # Obtener aplicaciones del usuario
        applications = await self.repository.get_applications_by_user(
            user_id=user_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size
        )
        
        # Contar total
        total_count = await self.repository.count_applications_by_user(
            user_id=user_id,
            status_filter=status_filter
        )
        
        # Convertir a DTOs
        items = []
        for application in applications:
            dto = await self.create_use_case._convert_to_response_dto(application)
            items.append(dto)
        
        return PaginatedResponseDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    async def search_applications(
        self,
        filters: ApplicationSearchFiltersDTO,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """
        Búsqueda avanzada de solicitudes
        
        Args:
            filters: Filtros de búsqueda
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            PaginatedResponseDTO con resultados de búsqueda
        """
        
        # Construir query de búsqueda
        search_query = self._build_search_query(filters)
        
        # Ejecutar búsqueda
        applications = await self.repository.search_applications(
            search_query=search_query,
            page=page,
            page_size=page_size
        )
        
        # Contar total de resultados
        total_count = await self.repository.count_search_results(search_query)
        
        # Convertir a DTOs
        items = []
        for application in applications:
            dto = await self.create_use_case._convert_to_response_dto(application)
            items.append(dto)
        
        return PaginatedResponseDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    async def get_application_by_dni(
        self,
        document_number: str
    ) -> Optional[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitud por DNI del solicitante principal
        
        Args:
            document_number: Número de documento del solicitante
            
        Returns:
            TechoPropioApplicationResponseDTO o None si no existe
        """
        
        application = await self.repository.get_application_by_dni(document_number)
        if not application:
            return None
        
        response_dto = await self.create_use_case._convert_to_response_dto(application)
        return response_dto
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitudes por estado
        
        Args:
            status: Estado de las solicitudes
            page: Número de página
            page_size: Tamaño de página
            sort_by: Campo de ordenamiento
            sort_order: Orden (asc/desc)
            
        Returns:
            PaginatedResponseDTO con solicitudes del estado especificado
        """
        
        applications = await self.repository.get_applications_by_status(
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total_count = await self.repository.count_applications_by_status(status)
        
        # Convertir a DTOs
        items = []
        for application in applications:
            dto = await self.create_use_case._convert_to_response_dto(application)
            items.append(dto)
        
        return PaginatedResponseDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    async def get_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitudes por ubicación geográfica
        
        Args:
            department: Departamento (opcional)
            province: Provincia (opcional)
            district: Distrito (opcional)
            page: Número de página
            page_size: Tamaño de página
            
        Returns:
            PaginatedResponseDTO con solicitudes de la ubicación especificada
        """
        
        applications = await self.repository.get_applications_by_location(
            department=department,
            province=province,
            district=district,
            page=page,
            page_size=page_size
        )
        
        total_count = await self.repository.count_applications_by_location(
            department=department,
            province=province,
            district=district
        )
        
        # Convertir a DTOs
        items = []
        for application in applications:
            dto = await self.create_use_case._convert_to_response_dto(application)
            items.append(dto)
        
        return PaginatedResponseDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    async def get_application_statistics(
        self,
        department: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de solicitudes
        
        Args:
            department: Filtro por departamento (opcional)
            date_from: Fecha desde (opcional)
            date_to: Fecha hasta (opcional)
            
        Returns:
            Dict con estadísticas detalladas
        """
        
        return await self.repository.get_application_statistics(
            department=department,
            date_from=date_from,
            date_to=date_to
        )
    
    async def get_priority_applications(
        self,
        page: int = 1,
        page_size: int = 20,
        min_priority_score: Optional[float] = None
    ) -> PaginatedResponseDTO[TechoPropioApplicationResponseDTO]:
        """
        Obtener solicitudes ordenadas por prioridad
        
        Args:
            page: Número de página
            page_size: Tamaño de página
            min_priority_score: Puntaje mínimo de prioridad
            
        Returns:
            PaginatedResponseDTO con solicitudes ordenadas por prioridad
        """
        
        applications = await self.repository.get_applications_by_priority(
            page=page,
            page_size=page_size,
            min_priority_score=min_priority_score
        )
        
        total_count = await self.repository.count_priority_applications(min_priority_score)
        
        # Convertir a DTOs
        items = []
        for application in applications:
            dto = await self.create_use_case._convert_to_response_dto(application)
            items.append(dto)
        
        return PaginatedResponseDTO(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=(total_count + page_size - 1) // page_size
        )
    
    def _build_search_query(self, filters: ApplicationSearchFiltersDTO) -> Dict[str, Any]:
        """Construir query de búsqueda a partir de filtros"""
        query = {}
        
        # Filtro por término de búsqueda
        if filters.search_term:
            query["search_term"] = filters.search_term
        
        # Filtro por estado
        if filters.status:
            query["status"] = filters.status
        
        # Filtro por usuario
        if filters.user_id:
            query["user_id"] = filters.user_id
        
        # Filtros por ubicación
        if filters.department:
            query["department"] = filters.department
        if filters.province:
            query["province"] = filters.province
        if filters.district:
            query["district"] = filters.district
        
        # Filtros por fecha
        if filters.date_from:
            query["date_from"] = filters.date_from
        if filters.date_to:
            query["date_to"] = filters.date_to
        
        # Filtros por datos económicos
        if filters.min_monthly_income:
            query["min_monthly_income"] = filters.min_monthly_income
        if filters.max_monthly_income:
            query["max_monthly_income"] = filters.max_monthly_income
        
        # Filtros por características familiares
        if filters.has_spouse is not None:
            query["has_spouse"] = filters.has_spouse
        if filters.min_household_members:
            query["min_household_members"] = filters.min_household_members
        if filters.max_household_members:
            query["max_household_members"] = filters.max_household_members
        
        # Filtros por discapacidad
        if filters.has_disability is not None:
            query["has_disability"] = filters.has_disability
        
        # Filtros por puntaje de prioridad
        if filters.min_priority_score:
            query["min_priority_score"] = filters.min_priority_score
        if filters.max_priority_score:
            query["max_priority_score"] = filters.max_priority_score
        
        # Ordenamiento
        query["sort_by"] = filters.sort_by or "created_at"
        query["sort_order"] = filters.sort_order or "desc"
        
        return query