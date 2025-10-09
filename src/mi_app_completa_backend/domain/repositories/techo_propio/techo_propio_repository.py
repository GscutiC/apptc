"""
Repositorios abstractos para el módulo Techo Propio
Define interfaces para persistencia de datos siguiendo arquitectura hexagonal
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...entities.techo_propio import TechoPropioApplication
from ...value_objects.techo_propio import ApplicationStatus


class TechoPropioRepository(ABC):
    """Repositorio abstracto para solicitudes Techo Propio"""
    
    # ===== OPERACIONES CRUD BÁSICAS =====
    
    @abstractmethod
    async def create_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Crear nueva solicitud"""
        pass
    
    @abstractmethod
    async def get_application_by_id(self, application_id: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por ID"""
        pass
    
    @abstractmethod
    async def get_application_by_number(self, application_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por número de solicitud"""
        pass
    
    @abstractmethod
    async def update_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Actualizar solicitud existente"""
        pass
    
    @abstractmethod
    async def delete_application(self, application_id: str) -> bool:
        """Eliminar solicitud (soft delete recomendado)"""
        pass
    
    # ===== CONSULTAS POR USUARIO =====
    
    @abstractmethod
    async def get_applications_by_user(
        self, 
        user_id: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes de un usuario específico"""
        pass
    
    @abstractmethod
    async def count_applications_by_user(
        self, 
        user_id: str,
        status: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de un usuario"""
        pass
    
    # ===== CONSULTAS POR ESTADO =====
    
    @abstractmethod
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por estado"""
        pass
    
    @abstractmethod
    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado"""
        pass
    
    @abstractmethod
    async def get_pending_review_applications(
        self,
        reviewer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes pendientes de revisión"""
        pass
    
    # ===== CONSULTAS POR FECHAS =====
    
    @abstractmethod
    async def get_applications_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes en rango de fechas"""
        pass
    
    @abstractmethod
    async def get_applications_submitted_today(self) -> List[TechoPropioApplication]:
        """Obtener solicitudes enviadas hoy"""
        pass
    
    # ===== CONSULTAS POR UBICACIÓN =====
    
    @abstractmethod
    async def get_applications_by_department(
        self,
        department: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por departamento"""
        pass
    
    @abstractmethod
    async def get_applications_by_district(
        self,
        department: str,
        province: str,
        district: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por distrito específico"""
        pass
    
    # ===== CONSULTAS DE VALIDACIÓN =====
    
    @abstractmethod
    async def check_dni_exists_in_applications(
        self, 
        dni: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Verificar si un DNI ya existe en otras solicitudes activas"""
        pass
    
    @abstractmethod
    async def get_applications_by_dni(self, dni: str) -> List[TechoPropioApplication]:
        """Obtener todas las solicitudes que incluyen un DNI específico"""
        pass
    
    @abstractmethod
    async def check_application_number_exists(self, application_number: str) -> bool:
        """Verificar si un número de solicitud ya existe"""
        pass
    
    # ===== ESTADÍSTICAS Y REPORTES =====
    
    @abstractmethod
    async def get_application_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas de solicitudes"""
        pass
    
    @abstractmethod
    async def get_applications_by_income_range(
        self,
        min_income: float,
        max_income: float,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por rango de ingresos familiares"""
        pass
    
    @abstractmethod
    async def get_applications_by_household_size(
        self,
        min_size: int,
        max_size: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por tamaño de familia"""
        pass
    
    # ===== OPERACIONES DE AUDITORÍA =====
    
    @abstractmethod
    async def get_application_history(self, application_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de cambios de una solicitud"""
        pass
    
    @abstractmethod
    async def log_application_change(
        self,
        application_id: str,
        user_id: str,
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar cambio en solicitud para auditoría"""
        pass
    
    # ===== OPERACIONES MASIVAS =====
    
    @abstractmethod
    async def bulk_update_status(
        self,
        application_ids: List[str],
        new_status: ApplicationStatus,
        updated_by: str,
        reason: Optional[str] = None
    ) -> int:
        """Actualizar estado de múltiples solicitudes"""
        pass
    
    @abstractmethod
    async def get_expired_draft_applications(
        self,
        days_threshold: int = 30
    ) -> List[TechoPropioApplication]:
        """Obtener borradores expirados para limpieza"""
        pass
    
    # ===== BÚSQUEDA AVANZADA =====
    
    @abstractmethod
    async def search_applications(
        self,
        filters: Dict[str, Any],
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Búsqueda avanzada con múltiples filtros"""
        pass
    
    @abstractmethod
    async def count_search_results(self, filters: Dict[str, Any]) -> int:
        """Contar resultados de búsqueda avanzada"""
        pass