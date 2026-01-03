"""
Entidad base para el módulo Techo Propio
Extiende BaseEntity manteniendo consistencia con la arquitectura existente
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from ..base_entity import BaseEntity


class TechoPropioBaseEntity(BaseEntity):
    """Entidad base específica para el módulo Techo Propio"""
    
    def __init__(self, entity_id: Optional[str] = None, created_by: Optional[str] = None):
        super().__init__(entity_id)
        # ✅ FIX: Solo usar "system" si NO se proporciona created_by
        # En producción, created_by SIEMPRE debe ser el user_id real
        self.created_by = created_by  # No usar fallback automático a "system"
        self.module = "techo_propio"  # Identificador del módulo
        
    def get_audit_info(self) -> dict:
        """Información para auditoría del módulo"""
        return {
            "module": self.module,
            "entity_id": self.id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_metadata(self, updated_by: str) -> None:
        """Actualizar metadatos de la entidad"""
        self.update_timestamp()
        self.created_by = updated_by if not self.created_by else self.created_by