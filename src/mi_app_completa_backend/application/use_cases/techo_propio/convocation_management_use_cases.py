"""
Casos de uso para gestión de convocatorias Techo Propio
Todos los usuarios con acceso al módulo tienen permisos completos
"""

from typing import List, Optional
from datetime import date, datetime
from ....domain.entities.techo_propio import Convocation
from ....domain.repositories.techo_propio import ConvocationRepository
from ....infrastructure.config.timezone_config import lima_now


class ConvocationManagementUseCases:
    """
    Casos de uso para gestión de convocatorias
    Nota: Sin restricciones de roles - todos los usuarios tienen acceso completo
    """
    
    def __init__(self, repository: ConvocationRepository):
        self.repository = repository
    
    # ==================== CRUD BÁSICO ====================
    
    async def create_convocation(
        self,
        code: str,
        title: str,
        description: str,
        start_date: date,
        end_date: date,
        user_id: str,
        is_active: bool = True,
        max_applications: Optional[int] = None
    ) -> Convocation:
        """
        Crear nueva convocatoria
        Cualquier usuario puede crear convocatorias
        """
        
        # Validar que el código no exista
        existing = await self.repository.get_convocation_by_code(code)
        if existing:
            raise ValueError(f"Ya existe una convocatoria con el código '{code}'")
        
        # Crear entidad
        convocation = Convocation(
            code=code,
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            max_applications=max_applications
        )
        # Asignar created_by después de la creación
        convocation.created_by = user_id

        # Extraer número secuencial del código si existe (formato CONV-YYYY-XX)
        try:
            parts = code.split("-")
            if len(parts) == 3:
                convocation.sequential_number = int(parts[2])
        except (IndexError, ValueError):
            # Si no se puede extraer, dejarlo en None
            pass

        return await self.repository.create_convocation(convocation)
    
    async def get_convocation_by_id(self, convocation_id: str) -> Optional[Convocation]:
        """Obtener convocatoria por ID"""
        return await self.repository.get_convocation_by_id(convocation_id)
    
    async def get_convocation_by_code(self, code: str) -> Optional[Convocation]:
        """Obtener convocatoria por código"""
        return await self.repository.get_convocation_by_code(code)
    
    async def update_convocation(
        self,
        convocation_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = None,
        is_published: Optional[bool] = None,
        max_applications: Optional[int] = None,
        user_id: str = None
    ) -> Convocation:
        """
        Actualizar convocatoria existente
        Cualquier usuario puede actualizar
        """
        
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        # Actualizar campos proporcionados
        if title is not None:
            convocation.title = title
        if description is not None:
            convocation.description = description
        if start_date is not None:
            convocation.start_date = start_date
        if end_date is not None:
            convocation.end_date = end_date
        if is_active is not None:
            convocation.is_active = is_active
        if is_published is not None:
            convocation.is_published = is_published
        if max_applications is not None:
            convocation.max_applications = max_applications
        
        # Actualizar metadatos
        convocation.update_timestamp()
        
        return await self.repository.update_convocation(convocation)
    
    async def delete_convocation(self, convocation_id: str, user_id: str) -> bool:
        """
        Eliminar convocatoria
        Cualquier usuario puede eliminar (verificar si tiene solicitudes)
        """
        
        # Verificar que existe
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        # Verificar si tiene solicitudes asociadas
        applications_count = await self.repository.count_applications_by_convocation(convocation.code)
        if applications_count > 0:
            raise ValueError(
                f"No se puede eliminar la convocatoria '{convocation.code}' "
                f"porque tiene {applications_count} solicitudes asociadas"
            )
        
        return await self.repository.delete_convocation(convocation_id)
    
    # ==================== CONSULTAS Y LISTADOS ====================
    
    async def get_all_convocations(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = True
    ) -> List[Convocation]:
        """Obtener todas las convocatorias con paginación"""
        return await self.repository.get_all_convocations(skip, limit, include_inactive)
    
    async def get_active_convocations(self) -> List[Convocation]:
        """Obtener solo convocatorias activas"""
        return await self.repository.get_active_convocations()
    
    async def get_current_convocations(self) -> List[Convocation]:
        """Obtener convocatorias vigentes (en período actual)"""
        return await self.repository.get_current_convocations()
    
    async def get_published_convocations(self) -> List[Convocation]:
        """Obtener convocatorias publicadas (para formulario)"""
        return await self.repository.get_published_convocations()
    
    async def get_convocations_by_year(self, year: int) -> List[Convocation]:
        """Obtener convocatorias de un año específico"""
        return await self.repository.get_convocations_by_year(year)
    
    # ==================== OPERACIONES DE ESTADO ====================
    
    async def activate_convocation(self, convocation_id: str, user_id: str) -> Convocation:
        """Activar convocatoria"""
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        convocation.activate()
        return await self.repository.update_convocation(convocation)
    
    async def deactivate_convocation(self, convocation_id: str, user_id: str) -> Convocation:
        """Desactivar convocatoria"""
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        convocation.deactivate()
        return await self.repository.update_convocation(convocation)
    
    async def publish_convocation(self, convocation_id: str, user_id: str) -> Convocation:
        """Publicar convocatoria (hacerla visible en formularios)"""
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        convocation.publish()
        return await self.repository.update_convocation(convocation)
    
    async def unpublish_convocation(self, convocation_id: str, user_id: str) -> Convocation:
        """Despublicar convocatoria"""
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        convocation.unpublish()
        return await self.repository.update_convocation(convocation)
    
    async def extend_convocation_deadline(
        self, 
        convocation_id: str, 
        new_end_date: date,
        user_id: str
    ) -> Convocation:
        """Extender fecha límite de convocatoria"""
        convocation = await self.repository.get_convocation_by_id(convocation_id)
        if not convocation:
            raise ValueError(f"No se encontró convocatoria con ID '{convocation_id}'")
        
        convocation.extend_deadline(new_end_date)
        return await self.repository.update_convocation(convocation)
    
    # ==================== UTILIDADES Y VALIDACIONES ====================
    
    async def generate_convocation_code(self, year: Optional[int] = None) -> str:
        """
        Generar automáticamente un código de convocatoria único
        """
        if year is None:
            year = lima_now().year
        
        next_seq = await self.repository.get_next_sequential_number(year)
        return Convocation.generate_code(year, next_seq)
    
    async def validate_convocation_code(self, code: str, exclude_id: Optional[str] = None) -> bool:
        """Validar que un código de convocatoria sea válido y único"""
        
        # Validar formato
        try:
            Convocation(
                code=code,
                title="Test",
                start_date=date.today(),
                end_date=date.today()
            )
        except ValueError as e:
            raise ValueError(f"Formato de código inválido: {e}")
        
        # Validar unicidad
        exists = await self.repository.code_exists(code, exclude_id)
        if exists:
            raise ValueError(f"El código '{code}' ya está en uso")
        
        return True
    
    # ==================== ESTADÍSTICAS ====================
    
    async def get_convocation_statistics(self, convocation_code: str) -> dict:
        """Obtener estadísticas de una convocatoria específica"""
        return await self.repository.get_convocation_statistics(convocation_code)
    
    async def get_general_statistics(self) -> dict:
        """Obtener estadísticas generales del módulo"""
        stats = await self.repository.get_general_statistics()
        
        # Agregar estadísticas adicionales
        all_convocations = await self.get_all_convocations(include_inactive=True)
        current_convocations = await self.get_current_convocations()
        
        stats.update({
            "total_convocations": len(all_convocations),
            "current_convocations": len(current_convocations),
            "active_convocations": len([c for c in all_convocations if c.is_active]),
            "published_convocations": len([c for c in all_convocations if c.is_published])
        })
        
        return stats
    
    # ==================== OPERACIONES MASIVAS ====================
    
    async def bulk_activate_convocations(self, convocation_ids: List[str], user_id: str) -> int:
        """Activar múltiples convocatorias"""
        count = 0
        for conv_id in convocation_ids:
            try:
                await self.activate_convocation(conv_id, user_id)
                count += 1
            except Exception:
                continue  # Continuar con las siguientes
        return count
    
    async def bulk_deactivate_convocations(self, convocation_ids: List[str], user_id: str) -> int:
        """Desactivar múltiples convocatorias"""
        count = 0
        for conv_id in convocation_ids:
            try:
                await self.deactivate_convocation(conv_id, user_id)
                count += 1
            except Exception:
                continue
        return count