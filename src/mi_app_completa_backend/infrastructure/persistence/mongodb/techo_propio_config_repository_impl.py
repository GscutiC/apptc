"""
Implementación del repositorio de configuración Techo Propio para MongoDB
Gestiona la persistencia de configuraciones visuales por usuario
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId

from ....domain.repositories.techo_propio_config_repository import TechoPropioConfigRepository
from ....domain.entities.techo_propio_config import TechoPropioThemeConfig


class MongoTechoPropioConfigRepository(TechoPropioConfigRepository):
    """Implementación MongoDB del repositorio de configuración"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["techo_propio_configs"]
        # Asegurar índice único por user_id
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Crear índices necesarios"""
        try:
            # Índice único para garantizar 1 config por usuario
            self.collection.create_index(
                [("user_id", 1)],
                unique=True,
                background=True
            )
        except Exception as e:
            # Si ya existe, no hacer nada
            pass

    async def find_by_user_id(self, user_id: str) -> Optional[TechoPropioThemeConfig]:
        """Buscar configuración por user_id"""
        try:
            doc = await self.collection.find_one({"user_id": user_id})
            if not doc:
                return None
            return self._to_entity(doc)
        except Exception as e:
            print(f"Error al buscar configuración: {e}")
            return None

    async def save(self, config: TechoPropioThemeConfig) -> TechoPropioThemeConfig:
        """Guardar nueva configuración"""
        try:
            doc = self._to_document(config)

            # Asignar nuevo ID si no existe
            if not config.id:
                config.id = str(ObjectId())

            doc["_id"] = config.id
            doc["created_at"] = datetime.utcnow()
            doc["updated_at"] = datetime.utcnow()

            await self.collection.insert_one(doc)

            # Actualizar entidad con fechas
            config.created_at = doc["created_at"]
            config.updated_at = doc["updated_at"]

            return config
        except Exception as e:
            raise Exception(f"Error al guardar configuración: {e}")

    async def update(self, config_id: str, config: TechoPropioThemeConfig) -> TechoPropioThemeConfig:
        """Actualizar configuración existente"""
        try:
            doc = self._to_document(config)
            doc["updated_at"] = datetime.utcnow()

            # No actualizar created_at
            doc.pop("created_at", None)

            result = await self.collection.update_one(
                {"_id": config_id},
                {"$set": doc}
            )

            if result.matched_count == 0:
                raise Exception(f"Configuración con id {config_id} no encontrada")

            # Obtener documento actualizado
            updated_doc = await self.collection.find_one({"_id": config_id})
            return self._to_entity(updated_doc)
        except Exception as e:
            raise Exception(f"Error al actualizar configuración: {e}")

    async def delete_by_user_id(self, user_id: str) -> bool:
        """Eliminar configuración por user_id"""
        try:
            result = await self.collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error al eliminar configuración: {e}")
            return False

    async def exists_by_user_id(self, user_id: str) -> bool:
        """Verificar si existe configuración para el usuario"""
        try:
            count = await self.collection.count_documents({"user_id": user_id}, limit=1)
            return count > 0
        except Exception as e:
            print(f"Error al verificar existencia: {e}")
            return False

    def _to_entity(self, doc: dict) -> TechoPropioThemeConfig:
        """Convertir documento MongoDB a entidad"""
        config = TechoPropioThemeConfig(
            user_id=doc["user_id"],
            colors=doc["colors"],
            logos=doc["logos"],
            branding=doc["branding"],
            id=str(doc["_id"])
        )

        # Asignar fechas si existen
        if "created_at" in doc:
            config.created_at = doc["created_at"]
        if "updated_at" in doc:
            config.updated_at = doc["updated_at"]

        return config

    def _to_document(self, config: TechoPropioThemeConfig) -> dict:
        """Convertir entidad a documento MongoDB"""
        doc = {
            "user_id": config.user_id,
            "colors": config.colors,
            "logos": config.logos,
            "branding": config.branding
        }

        # Incluir timestamps si existen
        if hasattr(config, 'created_at') and config.created_at:
            doc["created_at"] = config.created_at
        if hasattr(config, 'updated_at') and config.updated_at:
            doc["updated_at"] = config.updated_at

        return doc
