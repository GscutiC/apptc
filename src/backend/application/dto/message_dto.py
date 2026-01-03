from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class CreateMessageDTO(BaseModel):
    """DTO para crear mensaje"""
    content: str
    user_id: Optional[str] = None

class MessageResponseDTO(BaseModel):
    """DTO de respuesta de mensaje procesado por IA"""
    id: str
    response: str
    processed_by: str
    timestamp: datetime

    class Config:
        from_attributes = True

class MessageHistoryDTO(BaseModel):
    """DTO para historial de mensajes"""
    id: str
    content: str
    message_type: str
    processed_by: str
    created_at: datetime

    class Config:
        from_attributes = True