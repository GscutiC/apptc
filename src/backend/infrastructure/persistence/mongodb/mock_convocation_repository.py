"""
Repositorio Mock para convocatorias (temporal)
Se reemplazará por implementación MongoDB real
"""

from typing import List, Optional
from datetime import date, datetime
from ....domain.entities.techo_propio import Convocation
from ....domain.repositories.techo_propio import ConvocationRepository


class MockConvocationRepository(ConvocationRepository):
    """
    Implementación mock para testing y desarrollo inicial
    """
    
    def __init__(self):
        self._convocations = {}
        self._counter = 0
        # ✅ SIN DATOS MOCK - Repositorio vacío para testing real
    
    # ==================== CRUD BÁSICO ====================
    
    async def create_convocation(self, convocation: Convocation) -> Convocation:
        """Crear nueva convocatoria"""
        self._counter += 1
        convocation.id = f"conv_{self._counter}"
        self._convocations[convocation.id] = convocation
        return convocation
    
    async def get_convocation_by_id(self, convocation_id: str) -> Optional[Convocation]:
        """Obtener convocatoria por ID"""
        return self._convocations.get(convocation_id)
    
    async def get_convocation_by_code(self, code: str) -> Optional[Convocation]:
        """Obtener convocatoria por código único"""
        for conv in self._convocations.values():
            if conv.code == code:
                return conv
        return None
    
    async def update_convocation(self, convocation: Convocation) -> Convocation:
        """Actualizar convocatoria existente"""
        if convocation.id in self._convocations:
            self._convocations[convocation.id] = convocation
            return convocation
        raise ValueError(f"Convocatoria con ID {convocation.id} no existe")
    
    async def delete_convocation(self, convocation_id: str) -> bool:
        """Eliminar convocatoria"""
        if convocation_id in self._convocations:
            del self._convocations[convocation_id]
            return True
        return False
    
    # ==================== CONSULTAS ESPECIALIZADAS ====================
    
    async def get_all_convocations(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Convocation]:
        """Obtener todas las convocatorias con paginación"""
        convocations = list(self._convocations.values())
        
        if not include_inactive:
            convocations = [c for c in convocations if c.is_active]
        
        return convocations[skip:skip + limit]
    
    async def get_active_convocations(self) -> List[Convocation]:
        """Obtener solo convocatorias activas"""
        return [c for c in self._convocations.values() if c.is_active]
    
    async def get_current_convocations(self) -> List[Convocation]:
        """Obtener convocatorias vigentes"""
        return [c for c in self._convocations.values() if c.is_current]
    
    async def get_published_convocations(self) -> List[Convocation]:
        """Obtener convocatorias publicadas"""
        return [c for c in self._convocations.values() if c.is_published and c.is_active]
    
    async def get_convocations_by_year(self, year: int) -> List[Convocation]:
        """Obtener convocatorias de un año específico"""
        return [c for c in self._convocations.values() if c.year == year]
    
    async def get_upcoming_convocations(self) -> List[Convocation]:
        """Obtener convocatorias futuras"""
        return [c for c in self._convocations.values() if c.is_upcoming]
    
    async def get_expired_convocations(self) -> List[Convocation]:
        """Obtener convocatorias expiradas"""
        return [c for c in self._convocations.values() if c.is_expired]
    
    # ==================== VALIDACIONES Y UTILIDADES ====================
    
    async def code_exists(self, code: str, exclude_id: Optional[str] = None) -> bool:
        """Verificar si un código de convocatoria ya existe"""
        for conv in self._convocations.values():
            if conv.code == code and (exclude_id is None or conv.id != exclude_id):
                return True
        return False
    
    async def get_next_sequential_number(self, year: int) -> int:
        """Obtener el siguiente número secuencial para un año"""
        year_convocations = await self.get_convocations_by_year(year)
        if not year_convocations:
            return 1

        # Filtrar convocatorias con sequential_number válido
        valid_numbers = [c.sequential_number for c in year_convocations if c.sequential_number]
        if not valid_numbers:
            return 1

        return max(valid_numbers) + 1
    
    async def count_applications_by_convocation(self, convocation_code: str) -> int:
        """Contar solicitudes asociadas a una convocatoria"""
        # Mock: siempre retorna 0 para permitir eliminaciones
        return 0
    
    # ==================== OPERACIONES MASIVAS ====================
    
    async def activate_convocation(self, convocation_id: str) -> bool:
        """Activar una convocatoria"""
        conv = await self.get_convocation_by_id(convocation_id)
        if conv:
            conv.activate()
            return True
        return False
    
    async def deactivate_convocation(self, convocation_id: str) -> bool:
        """Desactivar una convocatoria"""
        conv = await self.get_convocation_by_id(convocation_id)
        if conv:
            conv.deactivate()
            return True
        return False
    
    async def publish_convocation(self, convocation_id: str) -> bool:
        """Publicar una convocatoria"""
        conv = await self.get_convocation_by_id(convocation_id)
        if conv:
            conv.publish()
            return True
        return False
    
    async def unpublish_convocation(self, convocation_id: str) -> bool:
        """Despublicar una convocatoria"""
        conv = await self.get_convocation_by_id(convocation_id)
        if conv:
            conv.unpublish()
            return True
        return False
    
    async def extend_convocation_deadline(
        self, 
        convocation_id: str, 
        new_end_date: date
    ) -> bool:
        """Extender fecha límite de una convocatoria"""
        conv = await self.get_convocation_by_id(convocation_id)
        if conv:
            conv.extend_deadline(new_end_date)
            return True
        return False
    
    # ==================== ESTADÍSTICAS ====================
    
    async def get_convocation_statistics(self, convocation_code: str) -> dict:
        """Obtener estadísticas de una convocatoria"""
        return {
            "convocation_code": convocation_code,
            "total_applications": 0,
            "applications_by_status": {},
            "average_priority_score": 0.0,
            "completion_rate": 0.0,
            "applications_per_day": {}
        }
    
    async def get_general_statistics(self) -> dict:
        """Obtener estadísticas generales"""
        all_convs = await self.get_all_convocations(include_inactive=True)
        active_convs = await self.get_active_convocations()
        current_convs = await self.get_current_convocations()
        
        return {
            "total_convocations": len(all_convs),
            "active_convocations": len(active_convs),
            "current_convocations": len(current_convs),
            "published_convocations": len([c for c in all_convs if c.is_published]),
            "total_applications_all_convocations": 0,
            "convocations_by_year": {},
            "applications_by_year": {},
            "most_active_convocation": None,
            "latest_convocation": all_convs[-1] if all_convs else None
        }