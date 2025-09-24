from typing import List, Optional
from pymongo.database import Database
from ....domain.entities.message import Message
from ....domain.repositories.message_repository import MessageRepository

class MongoMessageRepository(MessageRepository):
    """Implementación MongoDB del repositorio de mensajes"""

    def __init__(self, database: Database):
        self.database = database
        self.collection = database.messages

    async def save(self, message: Message) -> Message:
        """Guardar mensaje en MongoDB"""
        message_dict = message.to_dict()

        # Si el mensaje ya existe, actualizar
        if await self.find_by_id(message.id):
            await self.collection.update_one(
                {"id": message.id},
                {"$set": message_dict}
            )
        else:
            await self.collection.insert_one(message_dict)

        return message

    async def find_by_id(self, message_id: str) -> Optional[Message]:
        """Buscar mensaje por ID en MongoDB"""
        message_doc = await self.collection.find_one({"id": message_id})
        if message_doc:
            return self._document_to_entity(message_doc)
        return None

    async def find_by_user_id(self, user_id: str) -> List[Message]:
        """Buscar mensajes por usuario en MongoDB"""
        messages = []
        async for message_doc in self.collection.find({"user_id": user_id}).sort("created_at", -1):
            messages.append(self._document_to_entity(message_doc))
        return messages

    async def find_recent_messages(self, limit: int = 10) -> List[Message]:
        """Obtener mensajes recientes de MongoDB"""
        messages = []
        async for message_doc in self.collection.find().sort("created_at", -1).limit(limit):
            messages.append(self._document_to_entity(message_doc))
        return messages

    async def delete(self, message_id: str) -> bool:
        """Eliminar mensaje de MongoDB"""
        result = await self.collection.delete_one({"id": message_id})
        return result.deleted_count > 0

    def _document_to_entity(self, doc: dict) -> Message:
        """Convertir documento MongoDB a entidad Message"""
        message = Message(
            content=doc["content"],
            message_type=doc.get("message_type", "user"),
            processed_by=doc.get("processed_by", "human"),
            user_id=doc.get("user_id"),
            id=doc["id"]
        )
        message.created_at = doc.get("created_at", message.created_at)
        message.updated_at = doc.get("updated_at", message.updated_at)
        return message