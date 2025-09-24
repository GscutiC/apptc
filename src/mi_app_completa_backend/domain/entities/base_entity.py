from abc import ABC
from typing import Optional
from datetime import datetime
from bson import ObjectId

class BaseEntity(ABC):
    """Entidad base para el dominio"""

    def __init__(self, id: Optional[str] = None):
        self.id = id or str(ObjectId())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_timestamp(self):
        """Actualizar timestamp de modificación"""
        self.updated_at = datetime.utcnow()

    def __eq__(self, other) -> bool:
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)