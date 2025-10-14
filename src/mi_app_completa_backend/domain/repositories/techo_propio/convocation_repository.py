"""
Repositorio abstracto para gestión de convocatorias
Define contratos para operaciones CRUD de convocatorias
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from ...entities.techo_propio import Convocation


class ConvocationRepository(ABC):
    """
    Repositorio abstracto para operaciones de convocatorias
    Define el contrato que deben implementar los repositorios concretos
    """
    
    # ==================== CRUD BÁSICO ====================
    
    @abstractmethod
    async def create_convocation(self, convocation: Convocation) -> Convocation:
        """Crear nueva convocatoria"""
        pass
    
    @abstractmethod
    async def get_convocation_by_id(self, convocation_id: str) -> Optional[Convocation]:
        """Obtener convocatoria por ID"""
        pass
    
    @abstractmethod
    async def get_convocation_by_code(self, code: str) -> Optional[Convocation]:
        """Obtener convocatoria por código único"""
        pass
    
    @abstractmethod
    async def update_convocation(self, convocation: Convocation) -> Convocation:
        """Actualizar convocatoria existente"""
        pass
    
    @abstractmethod
    async def delete_convocation(self, convocation_id: str) -> bool:
        """Eliminar convocatoria (soft delete recomendado)"""
        pass
    
    # ==================== CONSULTAS ESPECIALIZADAS ====================
    
    @abstractmethod
    async def get_all_convocations(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Convocation]:
        """Obtener todas las convocatorias con paginación"""
        pass
    
    @abstractmethod
    async def get_active_convocations(self) -> List[Convocation]:
        """Obtener solo convocatorias activas"""
        pass
    
    @abstractmethod
    async def get_current_convocations(self) -> List[Convocation]:
        """Obtener convocatorias vigentes (en período actual)"""
        pass
    
    @abstractmethod
    async def get_published_convocations(self) -> List[Convocation]:
        """Obtener convocatorias publicadas y visibles"""
        pass
    
    @abstractmethod
    async def get_convocations_by_year(self, year: int) -> List[Convocation]:
        """Obtener convocatorias de un año específico"""
        pass
    
    @abstractmethod
    async def get_upcoming_convocations(self) -> List[Convocation]:
        """Obtener convocatorias futuras"""
        pass
    
    @abstractmethod
    async def get_expired_convocations(self) -> List[Convocation]:
        """Obtener convocatorias expiradas"""
        pass
    
    # ==================== VALIDACIONES Y UTILIDADES ====================
    
    @abstractmethod
    async def code_exists(self, code: str, exclude_id: Optional[str] = None) -> bool:
        """Verificar si un código de convocatoria ya existe"""
        pass
    
    @abstractmethod
    async def get_next_sequential_number(self, year: int) -> int:
        """Obtener el siguiente número secuencial para un año"""
        pass
    
    @abstractmethod
    async def count_applications_by_convocation(self, convocation_code: str) -> int:
        """Contar solicitudes asociadas a una convocatoria"""
        pass
    
    @abstractmethod
    async def get_next_application_sequential(self, convocation_code: str) -> int:
        """
        Obtener el siguiente número secuencial de solicitud para una convocatoria
        Usa findAndModify atómico para garantizar unicidad
        """
        pass
    
    # ==================== OPERACIONES MASIVAS ====================
    
    @abstractmethod
    async def activate_convocation(self, convocation_id: str) -> bool:
        """Activar una convocatoria"""
        pass
    
    @abstractmethod
    async def deactivate_convocation(self, convocation_id: str) -> bool:
        """Desactivar una convocatoria"""
        pass
    
    @abstractmethod
    async def publish_convocation(self, convocation_id: str) -> bool:
        """Publicar una convocatoria"""
        pass
    
    @abstractmethod
    async def unpublish_convocation(self, convocation_id: str) -> bool:
        """Despublicar una convocatoria"""
        pass
    
    @abstractmethod
    async def extend_convocation_deadline(
        self, 
        convocation_id: str, 
        new_end_date: date
    ) -> bool:
        """Extender fecha límite de una convocatoria"""
        pass
    
    # ==================== ESTADÍSTICAS ====================
    
    @abstractmethod
    async def get_convocation_statistics(self, convocation_code: str) -> dict:
        """
        Obtener estadísticas de una convocatoria:
        - Total de solicitudes
        - Solicitudes por estado
        - Promedio de puntaje
        - etc.
        """
        pass
    
    @abstractmethod
    async def get_general_statistics(self) -> dict:
        """
        Obtener estadísticas generales:
        - Total de convocatorias activas
        - Convocatorias vigentes
        - Total de solicitudes por convocatoria
        """
        pass