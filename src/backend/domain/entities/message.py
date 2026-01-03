from typing import Optional
from .base_entity import BaseEntity

class Message(BaseEntity):
    """Entidad Message del dominio"""

    def __init__(
        self,
        content: str,
        message_type: str = "user",  # user, ai, system
        processed_by: str = "human",
        user_id: Optional[str] = None,
        id: Optional[str] = None
    ):
        super().__init__(id)
        self.content = content
        self.message_type = message_type
        self.processed_by = processed_by
        self.user_id = user_id

    def mark_as_ai_processed(self, ai_service: str):
        """Marcar mensaje como procesado por IA"""
        self.processed_by = ai_service
        self.message_type = "ai"
        self.update_timestamp()

    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "content": self.content,
            "message_type": self.message_type,
            "processed_by": self.processed_by,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }