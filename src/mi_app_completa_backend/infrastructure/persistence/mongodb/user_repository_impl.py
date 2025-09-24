from typing import List, Optional
from pymongo.database import Database
from ....domain.entities.user import User
from ....domain.repositories.user_repository import UserRepository

class MongoUserRepository(UserRepository):
    """Implementación MongoDB del repositorio de usuarios"""

    def __init__(self, database: Database):
        self.database = database
        self.collection = database.users

    async def save(self, user: User) -> User:
        """Guardar usuario en MongoDB"""
        user_dict = user.to_dict()

        # Si el usuario ya existe, actualizar
        if await self.find_by_id(user.id):
            await self.collection.update_one(
                {"id": user.id},
                {"$set": user_dict}
            )
        else:
            await self.collection.insert_one(user_dict)

        return user

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Buscar usuario por ID en MongoDB"""
        user_doc = await self.collection.find_one({"id": user_id})
        if user_doc:
            return self._document_to_entity(user_doc)
        return None

    async def find_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email en MongoDB"""
        user_doc = await self.collection.find_one({"email": email})
        if user_doc:
            return self._document_to_entity(user_doc)
        return None

    async def find_all(self) -> List[User]:
        """Obtener todos los usuarios de MongoDB"""
        users = []
        async for user_doc in self.collection.find():
            users.append(self._document_to_entity(user_doc))
        return users

    async def delete(self, user_id: str) -> bool:
        """Eliminar usuario de MongoDB"""
        result = await self.collection.delete_one({"id": user_id})
        return result.deleted_count > 0

    def _document_to_entity(self, doc: dict) -> User:
        """Convertir documento MongoDB a entidad User"""
        user = User(
            name=doc["name"],
            email=doc["email"],
            id=doc["id"]
        )
        user.created_at = doc.get("created_at", user.created_at)
        user.updated_at = doc.get("updated_at", user.updated_at)
        return user