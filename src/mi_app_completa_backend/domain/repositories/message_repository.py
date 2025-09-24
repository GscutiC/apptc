from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.message import Message

class MessageRepository(ABC):
    """Interface del repositorio de mensajes"""

    @abstractmethod
    async def save(self, message: Message) -> Message:
        """Guardar mensaje"""
        pass

    @abstractmethod
    async def find_by_id(self, message_id: str) -> Optional[Message]:
        """Buscar mensaje por ID"""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Message]:
        """Buscar mensajes por usuario"""
        pass

    @abstractmethod
    async def find_recent_messages(self, limit: int = 10) -> List[Message]:
        """Obtener mensajes recientes"""
        pass

    @abstractmethod
    async def delete(self, message_id: str) -> bool:
        """Eliminar mensaje"""
        pass