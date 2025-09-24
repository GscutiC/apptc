"""
Repositorio abstracto para logs de auditoría
"""
from typing import List, Optional
from abc import ABC, abstractmethod
from ..entities.audit_log import AuditLog, AuditLogCreate, AuditLogFilter

class AuditLogRepository(ABC):
    """Repositorio abstracto para logs de auditoría"""
    
    @abstractmethod
    async def create_log(self, log_data: AuditLogCreate) -> AuditLog:
        """Crear un nuevo log de auditoría"""
        pass
    
    @abstractmethod
    async def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Obtener log por ID"""
        pass
    
    @abstractmethod
    async def list_logs(self, filters: AuditLogFilter) -> List[AuditLog]:
        """Listar logs de auditoría con filtros"""
        pass
    
    @abstractmethod
    async def count_logs(self, filters: AuditLogFilter) -> int:
        """Contar logs que coinciden con los filtros"""
        pass
    
    @abstractmethod
    async def delete_old_logs(self, days_to_keep: int = 90) -> int:
        """Eliminar logs antiguos (para mantenimiento)"""
        pass
    
    @abstractmethod
    async def get_user_activity_summary(self, clerk_id: str, days: int = 30) -> dict:
        """Obtener resumen de actividad de un usuario"""
        pass
    
    @abstractmethod
    async def get_action_statistics(self, days: int = 30) -> dict:
        """Obtener estadísticas de acciones en el período especificado"""
        pass