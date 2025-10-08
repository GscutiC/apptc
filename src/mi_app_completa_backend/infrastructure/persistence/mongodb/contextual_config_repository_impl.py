"""
Implementación MongoDB para repositorio de configuración contextual
Sigue el patrón establecido en interface_config_repository_impl.py
FASE 3: Sistema de Configuración Contextual
"""

from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ....domain.repositories.contextual_config_repository import ContextualConfigRepository
from ....domain.entities.contextual_config import ContextualConfig
from ....domain.entities.interface_config import InterfaceConfig
from ....domain.value_objects.config_context import ConfigContext
from ...services.cache_service import interface_config_cache
from ...utils.logger import get_logger

logger = get_logger(__name__)


class MongoContextualConfigRepository(ContextualConfigRepository):
    """
    Implementación MongoDB para repositorio de configuración contextual
    FASE 3: Gestiona configuraciones por usuario, rol, organización y global
    """

    CACHE_KEY_PREFIX = "contextual_config"

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.contextual_configurations
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Crear índices necesarios para optimizar consultas"""
        try:
            # Índice compuesto para búsqueda por contexto
            self.collection.create_index([
                ("context_type", 1),
                ("context_id", 1),
                ("is_active", 1)
            ])
            
            # Índice para búsquedas por usuario específico
            self.collection.create_index([
                ("context_type", 1),
                ("context_id", 1),
                ("created_at", -1)
            ])
            
        except Exception as e:
            logger.warning(f"Error creating contextual config indexes: {e}")

    async def get_config_for_context(
        self,
        context_type: str,
        context_id: Optional[str] = None,
        active_only: bool = True
    ) -> Optional[ContextualConfig]:
        """
        Obtener configuración para un contexto específico
        
        Args:
            context_type: Tipo de contexto ('user', 'role', 'org', 'global')
            context_id: ID del contexto (None para global)
            active_only: Solo configuraciones activas
            
        Returns:
            Configuración contextual o None si no existe
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}:{context_type}:{context_id or 'global'}"
        
        # Intentar obtener del caché
        cached = interface_config_cache.get(cache_key)
        if cached and active_only:
            return cached

        try:
            # Construir filtro de búsqueda
            filter_query = {
                "context_type": context_type
            }
            
            if context_type == "global":
                filter_query["context_id"] = None
            else:
                filter_query["context_id"] = context_id
                
            if active_only:
                filter_query["is_active"] = True

            # Buscar configuración más reciente para el contexto
            doc = await self.collection.find_one(
                filter_query,
                sort=[("created_at", -1)]
            )
            
            if doc:
                config = self._doc_to_entity(doc)
                # Guardar en caché si está activa
                if config.is_active:
                    interface_config_cache.set(cache_key, config)
                return config
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting config for context {context_type}:{context_id}: {e}")
            return None

    async def get_effective_config_for_user(
        self,
        user_id: str,
        user_role: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> Optional[InterfaceConfig]:
        """
        Obtener configuración efectiva para un usuario siguiendo jerarquía de prioridades
        
        Jerarquía: user > role > org > global
        
        Args:
            user_id: ID del usuario
            user_role: Rol del usuario (opcional)
            org_id: ID de organización (opcional)
            
        Returns:
            Configuración de interfaz efectiva
        """
        try:
            # Buscar configuraciones en orden de prioridad
            contexts_to_check = [
                ("user", user_id),
                ("role", user_role) if user_role else None,
                ("org", org_id) if org_id else None,
                ("global", None)
            ]
            
            # Filtrar contextos válidos
            contexts_to_check = [ctx for ctx in contexts_to_check if ctx is not None]
            
            for context_type, context_id in contexts_to_check:
                contextual_config = await self.get_config_for_context(
                    context_type, context_id, active_only=True
                )
                
                if contextual_config:
                    return contextual_config.config
            
            logger.warning(f"No effective config found for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting effective config for user {user_id}: {e}")
            return None

    async def save(self, contextual_config: ContextualConfig) -> ContextualConfig:
        """
        Guardar configuración contextual
        
        Args:
            contextual_config: Configuración contextual a guardar
            
        Returns:
            Configuración guardada con ID actualizado
        """
        try:
            # Si es nueva configuración activa, desactivar otras del mismo contexto
            if contextual_config.is_active:
                await self.collection.update_many(
                    {
                        "context_type": contextual_config.context.context_type,
                        "context_id": contextual_config.context.context_id,
                        "is_active": True
                    },
                    {
                        "$set": {
                            "is_active": False,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )

            # Invalidar caché del contexto
            cache_key = f"{self.CACHE_KEY_PREFIX}:{contextual_config.context.context_type}:{contextual_config.context.context_id or 'global'}"
            interface_config_cache.delete(cache_key)

            # Verificar si existe
            exists = False
            if contextual_config.id and contextual_config.id != 'new':
                try:
                    existing = await self.collection.find_one({"_id": ObjectId(contextual_config.id)})
                    exists = existing is not None
                except:
                    exists = False

            if exists:
                # Actualizar existente
                config_dict = self._entity_to_doc(contextual_config)
                config_dict["updated_at"] = datetime.now(timezone.utc)
                await self.collection.update_one(
                    {"_id": ObjectId(contextual_config.id)},
                    {"$set": config_dict}
                )
            else:
                # Crear nuevo
                config_dict = self._entity_to_doc(contextual_config)
                config_dict["created_at"] = datetime.now(timezone.utc)
                config_dict["updated_at"] = datetime.now(timezone.utc)
                result = await self.collection.insert_one(config_dict)
                contextual_config.id = str(result.inserted_id)

            logger.info(f"Contextual config saved: {contextual_config.context.context_type}:{contextual_config.context.context_id}")
            return contextual_config
            
        except Exception as e:
            logger.error(f"Error saving contextual config: {e}")
            raise

    async def get_configs_for_context_type(
        self,
        context_type: str,
        active_only: bool = True
    ) -> List[ContextualConfig]:
        """
        Obtener todas las configuraciones de un tipo de contexto
        
        Args:
            context_type: Tipo de contexto
            active_only: Solo configuraciones activas
            
        Returns:
            Lista de configuraciones contextuales
        """
        try:
            filter_query = {"context_type": context_type}
            if active_only:
                filter_query["is_active"] = True

            cursor = self.collection.find(filter_query).sort("created_at", -1)
            configs = []
            
            async for doc in cursor:
                configs.append(self._doc_to_entity(doc))
                
            return configs
            
        except Exception as e:
            logger.error(f"Error getting configs for context type {context_type}: {e}")
            return []

    async def list_all(self, active_only: bool = True) -> List[ContextualConfig]:
        """
        Obtener todas las configuraciones contextuales
        
        Args:
            active_only: Solo configuraciones activas
            
        Returns:
            Lista de todas las configuraciones contextuales
        """
        try:
            filter_query = {}
            if active_only:
                filter_query["is_active"] = True

            cursor = self.collection.find(filter_query).sort("created_at", -1)
            configs = []
            
            async for doc in cursor:
                configs.append(self._doc_to_entity(doc))
                
            return configs
            
        except Exception as e:
            logger.error(f"Error listing all contextual configs: {e}")
            return []

    async def get_by_id(self, config_id: str) -> Optional[ContextualConfig]:
        """
        Obtener configuración contextual por ID
        
        Args:
            config_id: ID de la configuración
            
        Returns:
            Configuración contextual o None
        """
        try:
            doc = await self.collection.find_one({"_id": ObjectId(config_id)})
            if doc:
                return self._doc_to_entity(doc)
            return None
            
        except Exception as e:
            logger.error(f"Error getting contextual config by id {config_id}: {e}")
            return None

    async def delete_by_id(self, config_id: str) -> bool:
        """
        Eliminar configuración contextual por ID
        
        Args:
            config_id: ID de la configuración a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(config_id)})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Contextual config deleted: {config_id}")
            else:
                logger.warning(f"Contextual config not found for deletion: {config_id}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error deleting contextual config {config_id}: {e}")
            return False

    def _entity_to_doc(self, contextual_config: ContextualConfig) -> dict:
        """Convertir entidad a documento MongoDB"""
        from ....infrastructure.persistence.mongodb.interface_config_repository_impl import MongoInterfaceConfigRepository
        
        # Usar el método existente para convertir la configuración de interfaz
        interface_repo = MongoInterfaceConfigRepository(self.db)
        interface_doc = interface_repo._entity_to_doc_new(contextual_config.config)
        
        return {
            "config": interface_doc,
            "context_type": contextual_config.context.context_type,
            "context_id": contextual_config.context.context_id,
            "is_active": contextual_config.is_active,
            "created_by": contextual_config.created_by,
            # No incluir _id, created_at, updated_at aquí - se añaden en save()
        }

    def _doc_to_entity(self, doc: dict) -> ContextualConfig:
        """Convertir documento MongoDB a entidad"""
        from ....infrastructure.persistence.mongodb.interface_config_repository_impl import MongoInterfaceConfigRepository
        
        # Usar el método existente para convertir la configuración de interfaz
        interface_repo = MongoInterfaceConfigRepository(self.db)
        interface_config = interface_repo._doc_to_entity(doc["config"])
        
        # Crear contexto
        context = ConfigContext(
            context_type=doc["context_type"],
            context_id=doc.get("context_id")
        )
        
        # Crear configuración contextual
        contextual_config = ContextualConfig(
            config=interface_config,
            context=context,
            is_active=doc.get("is_active", True),
            created_by=doc.get("created_by"),
            entity_id=str(doc["_id"])
        )
        
        # Establecer fechas si existen
        if "created_at" in doc:
            contextual_config.created_at = doc["created_at"]
        if "updated_at" in doc:
            contextual_config.updated_at = doc["updated_at"]
            
        return contextual_config

    async def get_by_context(
        self,
        context_type: str,
        context_id: Optional[str],
        active_only: bool = True
    ) -> List[ContextualConfig]:
        """Obtener configuraciones por contexto específico"""
        try:
            # Construir filtro
            filter_query = {"context_type": context_type}
            
            if context_id is not None:
                filter_query["context_id"] = context_id
                
            if active_only:
                filter_query["is_active"] = True

            # Buscar en la base de datos
            cursor = self.collection.find(filter_query)
            cursor = cursor.sort("created_at", -1)

            # Convertir documentos a entidades
            configs = []
            async for doc in cursor:
                config = self._to_entity(doc)
                if config:
                    configs.append(config)

            # Actualizar caché
            cache_key = f"context_{context_type}_{context_id}_{active_only}"
            self._cache[cache_key] = configs
            
            return configs

        except Exception as e:
            logger.error(f"Error al obtener configuraciones por contexto {context_type}/{context_id}: {e}")
            return []

    async def get_for_user(
        self,
        user_id: str,
        organization_id: Optional[str] = None,
        role_names: Optional[List[str]] = None
    ) -> List[ContextualConfig]:
        """Obtener todas las configuraciones aplicables a un usuario"""
        try:
            all_configs = []

            # 1. Configuraciones de usuario específico
            user_configs = await self.get_by_context("user", user_id, active_only=True)
            all_configs.extend(user_configs)

            # 2. Configuraciones por rol
            if role_names:
                for role_name in role_names:
                    role_configs = await self.get_by_context("role", role_name, active_only=True)
                    all_configs.extend(role_configs)

            # 3. Configuraciones organizacionales
            if organization_id:
                org_configs = await self.get_by_context("organization", organization_id, active_only=True)
                all_configs.extend(org_configs)

            # 4. Configuraciones globales
            global_configs = await self.get_by_context("global", None, active_only=True)
            all_configs.extend(global_configs)

            return all_configs

        except Exception as e:
            logger.error(f"Error al obtener configuraciones para usuario {user_id}: {e}")
            return []

    async def count_by_type(self, context_type: str) -> int:
        """Contar configuraciones por tipo de contexto"""
        try:
            count = await self.collection.count_documents({"context_type": context_type})
            return count
        except Exception as e:
            logger.error(f"Error al contar configuraciones de tipo {context_type}: {e}")
            return 0

    async def deactivate_all_for_context(
        self,
        context_type: str,
        context_id: Optional[str]
    ) -> int:
        """Desactivar todas las configuraciones de un contexto"""
        try:
            # Construir filtro
            filter_query = {"context_type": context_type}
            if context_id is not None:
                filter_query["context_id"] = context_id

            # Actualizar documentos
            result = await self.collection.update_many(
                filter_query,
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Limpiar caché relacionada
            keys_to_remove = [key for key in self._cache.keys() if context_type in key]
            for key in keys_to_remove:
                self._cache.pop(key, None)

            return result.modified_count

        except Exception as e:
            logger.error(f"Error al desactivar configuraciones para {context_type}/{context_id}: {e}")
            return 0

    async def delete(self, config_id: str) -> bool:
        """Eliminar configuración por ID"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(config_id)})
            
            # Limpiar caché
            self._cache.clear()
            
            return result.deleted_count > 0

        except Exception as e:
            logger.error(f"Error al eliminar configuración {config_id}: {e}")
            return False

    async def list_by_type(
        self,
        context_type: str,
        active_only: bool = True
    ) -> List[ContextualConfig]:
        """Listar configuraciones por tipo de contexto"""
        return await self.get_by_context(context_type, None, active_only)

    async def list_all(self, active_only: bool = True) -> List[ContextualConfig]:
        """Listar todas las configuraciones contextuales"""
        try:
            # Construir filtro
            filter_query = {}
            if active_only:
                filter_query["is_active"] = True

            # Buscar en la base de datos
            cursor = self.collection.find(filter_query)
            cursor = cursor.sort("created_at", -1)

            # Convertir documentos a entidades
            configs = []
            async for doc in cursor:
                config = self._to_entity(doc)
                if config:
                    configs.append(config)

            return configs

        except Exception as e:
            logger.error(f"Error al listar todas las configuraciones: {e}")
            return []

    async def get_by_id(self, config_id: str) -> Optional[ContextualConfig]:
        """Obtener configuración contextual por ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(config_id)})
            return self._to_entity(doc) if doc else None
        except Exception as e:
            logger.error(f"Error al obtener configuración por ID {config_id}: {e}")
            return None