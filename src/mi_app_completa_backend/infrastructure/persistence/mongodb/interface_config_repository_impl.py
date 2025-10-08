"""
Implementación MongoDB para repositorio de configuración de interfaz
Sigue el patrón establecido en auth_repository_impl.py
FASE 2.2: Con sistema de caché integrado
"""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ....domain.repositories.interface_config_repository import (
    InterfaceConfigRepository,
    PresetConfigRepository,
    ConfigHistoryRepository
)
from ....domain.entities.interface_config import (
    InterfaceConfig,
    PresetConfig,
    ConfigHistory,
    ThemeConfig,
    ColorConfig,
    TypographyConfig,
    LayoutConfig,
    LogoConfig,
    BrandingConfig
)
from ...services.cache_service import interface_config_cache, preset_cache
from ...utils.logger import get_logger

logger = get_logger(__name__)


class MongoInterfaceConfigRepository(InterfaceConfigRepository):
    """
    Implementación MongoDB para repositorio de configuración de interfaz
    FASE 2.2: Con caché integrado para mejorar rendimiento
    """

    CACHE_KEY_CURRENT = "interface_config:current"
    CACHE_KEY_ALL = "interface_config:all"

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.interface_configurations

    async def get_current_config(self) -> Optional[InterfaceConfig]:
        """
        Obtener la configuración actual activa
        FASE 2.2: Con caché integrado
        """
        # Intentar obtener del caché primero
        cached = interface_config_cache.get(self.CACHE_KEY_CURRENT)
        if cached:
            return cached

        # Si no está en caché, obtener de MongoDB
        try:
            doc = await self.collection.find_one({"isActive": True})
            if doc:
                config = self._doc_to_entity(doc)
                # Guardar en caché
                interface_config_cache.set(self.CACHE_KEY_CURRENT, config)
                return config
            return None
        except Exception as e:
            logger.error(f"Error getting current config: {e}")
            return None

    async def save_config(self, config: InterfaceConfig) -> InterfaceConfig:
        """
        Guardar configuración con versionado automático
        FASE 2.2: Invalida caché al guardar
        """
        try:
            # Si la configuración es nueva y está marcada como activa,
            # desactivar todas las demás configuraciones
            if config.is_active:
                await self.collection.update_many(
                    {"isActive": True},
                    {"$set": {"isActive": False, "updatedAt": datetime.now(timezone.utc)}}
                )

            # Invalidar caché antes de guardar
            interface_config_cache.delete(self.CACHE_KEY_CURRENT)
            interface_config_cache.delete(self.CACHE_KEY_ALL)

            # Verificar si el documento existe en la BD
            exists = False
            if config.id and config.id != 'new' and config.id != 'None':
                try:
                    existing = await self.collection.find_one({"_id": ObjectId(config.id)})
                    exists = existing is not None
                except:
                    exists = False

            if exists:
                # Actualizar existente
                config_dict = self._entity_to_doc_new(config)  # Sin _id
                config_dict["updatedAt"] = datetime.now(timezone.utc)
                await self.collection.update_one(
                    {"_id": ObjectId(config.id)},
                    {"$set": config_dict}
                )
            else:
                # Crear nuevo
                config_dict = self._entity_to_doc_new(config)
                config_dict["createdAt"] = datetime.now(timezone.utc)
                config_dict["updatedAt"] = datetime.now(timezone.utc)
                result = await self.collection.insert_one(config_dict)
                config.id = str(result.inserted_id)

            return config
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise

    async def get_config_by_id(self, config_id: str) -> Optional[InterfaceConfig]:
        """Obtener configuración por ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(config_id)})
            if doc:
                return self._doc_to_entity(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting config by id {config_id}: {e}")
            return None

    async def get_all_configs(self) -> List[InterfaceConfig]:
        """Obtener todas las configuraciones"""
        try:
            cursor = self.collection.find().sort("updatedAt", -1)
            configs = []
            async for doc in cursor:
                configs.append(self._doc_to_entity(doc))
            return configs
        except Exception as e:
            logger.error(f"Error getting all configs: {e}")
            return []

    async def delete_config(self, config_id: str) -> bool:
        """Eliminar configuración (solo si no está activa)"""
        try:
            # Verificar que no esté activa
            config = await self.get_config_by_id(config_id)
            if config and config.is_active:
                logger.warning(f"Cannot delete active config {config_id}")
                return False

            result = await self.collection.delete_one({"_id": ObjectId(config_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting config {config_id}: {e}")
            return False

    async def set_active_config(self, config_id: str) -> bool:
        """Establecer configuración como activa"""
        try:
            # Desactivar todas las configuraciones
            await self.collection.update_many(
                {"isActive": True},
                {"$set": {"isActive": False, "updatedAt": datetime.now(timezone.utc)}}
            )

            # Activar la configuración solicitada
            result = await self.collection.update_one(
                {"_id": ObjectId(config_id)},
                {"$set": {"isActive": True, "updatedAt": datetime.now(timezone.utc)}}
            )

            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error setting active config {config_id}: {e}")
            return False

    def _doc_to_entity(self, doc: dict) -> InterfaceConfig:
        """Convertir documento MongoDB a entidad"""
        # Parsear theme
        theme_data = doc.get("theme", {})
        colors = ColorConfig(
            primary=theme_data.get("colors", {}).get("primary", {}),
            secondary=theme_data.get("colors", {}).get("secondary", {}),
            accent=theme_data.get("colors", {}).get("accent", {}),
            neutral=theme_data.get("colors", {}).get("neutral", {})
        )

        typography = TypographyConfig(
            font_family=theme_data.get("typography", {}).get("fontFamily", {}),
            font_size=theme_data.get("typography", {}).get("fontSize", {}),
            font_weight=theme_data.get("typography", {}).get("fontWeight", {})
        )

        layout = LayoutConfig(
            border_radius=theme_data.get("layout", {}).get("borderRadius", {}),
            spacing=theme_data.get("layout", {}).get("spacing", {}),
            shadows=theme_data.get("layout", {}).get("shadows", {})
        )

        theme = ThemeConfig(
            mode=theme_data.get("mode", "light"),
            name=theme_data.get("name", "Default Theme"),
            colors=colors,
            typography=typography,
            layout=layout
        )

        # Parsear logos
        logos_data = doc.get("logos", {})
        logos = LogoConfig(
            main_logo=logos_data.get("mainLogo", {}),
            favicon=logos_data.get("favicon", {}),
            sidebar_logo=logos_data.get("sidebarLogo", {})
        )

        # Parsear branding
        branding_data = doc.get("branding", {})
        branding = BrandingConfig(
            app_name=branding_data.get("appName", "App"),
            app_description=branding_data.get("appDescription", ""),
            welcome_message=branding_data.get("welcomeMessage", ""),
            login_page_title=branding_data.get("loginPageTitle", ""),
            login_page_description=branding_data.get("loginPageDescription", ""),
            tagline=branding_data.get("tagline"),
            company_name=branding_data.get("companyName"),
            footer_text=branding_data.get("footerText"),
            support_email=branding_data.get("supportEmail")
        )

        # Crear entidad
        config = InterfaceConfig(
            theme=theme,
            logos=logos,
            branding=branding,
            is_active=doc.get("isActive", False),
            custom_css=doc.get("customCSS"),
            created_by=doc.get("createdBy"),
            entity_id=str(doc["_id"]) if "_id" in doc else None
        )

        # Asignar timestamps
        if "createdAt" in doc:
            config.created_at = doc["createdAt"]
        if "updatedAt" in doc:
            config.updated_at = doc["updatedAt"]

        return config

    def _entity_to_doc(self, entity: InterfaceConfig) -> dict:
        """Convertir entidad a documento MongoDB (con _id si existe)"""
        doc = {
            "theme": entity.theme.to_dict(),
            "logos": entity.logos.to_dict(),
            "branding": entity.branding.to_dict(),
            "customCSS": entity.custom_css,
            "isActive": entity.is_active,
            "createdBy": entity.created_by
        }

        # Incluir _id solo si es válido
        if entity.id and entity.id != 'new' and entity.id != 'None':
            doc["_id"] = ObjectId(entity.id)

        return doc

    def _entity_to_doc_new(self, entity: InterfaceConfig) -> dict:
        """Convertir entidad a documento MongoDB (sin _id para inserción)"""
        return {
            "theme": entity.theme.to_dict(),
            "logos": entity.logos.to_dict(),
            "branding": entity.branding.to_dict(),
            "customCSS": entity.custom_css,
            "isActive": entity.is_active,
            "createdBy": entity.created_by
        }


class MongoPresetConfigRepository(PresetConfigRepository):
    """
    Implementación MongoDB para repositorio de presets de configuración
    FASE 2.2: Con caché integrado
    """

    CACHE_KEY_ALL = "presets:all"
    CACHE_KEY_SYSTEM = "presets:system"
    CACHE_KEY_CUSTOM = "presets:custom"
    CACHE_KEY_PREFIX = "preset:"

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.preset_configurations

    async def get_all_presets(self) -> List[PresetConfig]:
        """
        Obtener todos los presets
        FASE 2.2: Con caché
        """
        # Intentar desde caché
        cached = preset_cache.get(self.CACHE_KEY_ALL)
        if cached:
            return cached

        # Obtener de MongoDB
        try:
            cursor = self.collection.find().sort("name", 1)
            presets = []
            async for doc in cursor:
                presets.append(self._doc_to_entity(doc))

            # Cachear resultado
            preset_cache.set(self.CACHE_KEY_ALL, presets)
            return presets
        except Exception as e:
            logger.error(f"Error getting all presets: {e}")
            return []

    async def get_preset_by_id(self, preset_id: str) -> Optional[PresetConfig]:
        """
        Obtener preset por ID
        FASE 2.2: Con caché individual
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}{preset_id}"

        # Intentar desde caché
        cached = preset_cache.get(cache_key)
        if cached:
            return cached

        # Obtener de MongoDB
        try:
            doc = await self.collection.find_one({"_id": ObjectId(preset_id)})
            if doc:
                preset = self._doc_to_entity(doc)
                preset_cache.set(cache_key, preset)
                return preset
            return None
        except Exception as e:
            logger.error(f"Error getting preset by id {preset_id}: {e}")
            return None

    async def get_system_presets(self) -> List[PresetConfig]:
        """Obtener presets del sistema"""
        try:
            cursor = self.collection.find({"isSystem": True}).sort("name", 1)
            presets = []
            async for doc in cursor:
                presets.append(self._doc_to_entity(doc))
            return presets
        except Exception as e:
            logger.error(f"Error getting system presets: {e}")
            return []

    async def get_custom_presets(self) -> List[PresetConfig]:
        """Obtener presets personalizados"""
        try:
            cursor = self.collection.find({"isSystem": False}).sort("name", 1)
            presets = []
            async for doc in cursor:
                presets.append(self._doc_to_entity(doc))
            return presets
        except Exception as e:
            logger.error(f"Error getting custom presets: {e}")
            return []

    async def get_default_preset(self) -> Optional[PresetConfig]:
        """Obtener preset por defecto"""
        try:
            doc = await self.collection.find_one({"isDefault": True})
            if doc:
                return self._doc_to_entity(doc)
            return None
        except Exception as e:
            logger.error(f"Error getting default preset: {e}")
            return None

    async def save_preset(self, preset: PresetConfig) -> PresetConfig:
        """Guardar preset"""
        try:
            # Si es marcado como default, desmarcar otros defaults
            if preset.is_default:
                await self.collection.update_many(
                    {"isDefault": True},
                    {"$set": {"isDefault": False, "updatedAt": datetime.now(timezone.utc)}}
                )

            # Verificar si el documento existe en la BD
            exists = False
            if preset.id and preset.id != 'new' and preset.id != 'None':
                try:
                    existing = await self.collection.find_one({"_id": ObjectId(preset.id)})
                    exists = existing is not None
                except:
                    exists = False

            if exists:
                # Actualizar existente
                preset_dict = self._entity_to_doc_new(preset)  # Sin _id
                preset_dict["updatedAt"] = datetime.now(timezone.utc)
                await self.collection.update_one(
                    {"_id": ObjectId(preset.id)},
                    {"$set": preset_dict}
                )
            else:
                # Crear nuevo
                preset_dict = self._entity_to_doc_new(preset)
                preset_dict["createdAt"] = datetime.now(timezone.utc)
                preset_dict["updatedAt"] = datetime.now(timezone.utc)
                result = await self.collection.insert_one(preset_dict)
                preset.id = str(result.inserted_id)

            return preset
        except Exception as e:
            logger.error(f"Error saving preset: {e}")
            raise

    async def delete_preset(self, preset_id: str) -> bool:
        """Eliminar preset (solo si no es del sistema)"""
        try:
            # Verificar que no sea del sistema
            preset = await self.get_preset_by_id(preset_id)
            if preset and preset.is_system:
                logger.warning(f"Cannot delete system preset {preset_id}")
                return False

            result = await self.collection.delete_one({"_id": ObjectId(preset_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting preset {preset_id}: {e}")
            return False

    async def set_default_preset(self, preset_id: str) -> bool:
        """Establecer preset como por defecto"""
        try:
            # Desmarcar todos los defaults
            await self.collection.update_many(
                {"isDefault": True},
                {"$set": {"isDefault": False, "updatedAt": datetime.now(timezone.utc)}}
            )

            # Marcar el nuevo default
            result = await self.collection.update_one(
                {"_id": ObjectId(preset_id)},
                {"$set": {"isDefault": True, "updatedAt": datetime.now(timezone.utc)}}
            )

            return result.matched_count > 0
        except Exception as e:
            logger.error(f"Error setting default preset {preset_id}: {e}")
            return False

    def _doc_to_entity(self, doc: dict) -> PresetConfig:
        """Convertir documento MongoDB a entidad"""
        # Parsear config (reutilizar lógica de MongoInterfaceConfigRepository)
        config_repo = MongoInterfaceConfigRepository(self.db)
        config_data = doc.get("config", {})
        # Crear documento temporal para parsear
        temp_doc = {**config_data, "_id": ObjectId()}
        config = config_repo._doc_to_entity(temp_doc)

        # Crear preset
        preset = PresetConfig(
            name=doc.get("name", ""),
            description=doc.get("description", ""),
            config=config,
            is_default=doc.get("isDefault", False),
            is_system=doc.get("isSystem", False),
            created_by=doc.get("createdBy"),
            entity_id=str(doc["_id"])
        )

        # Asignar timestamps
        if "createdAt" in doc:
            preset.created_at = doc["createdAt"]
        if "updatedAt" in doc:
            preset.updated_at = doc["updatedAt"]

        return preset

    def _entity_to_doc(self, entity: PresetConfig) -> dict:
        """Convertir entidad a documento MongoDB (con _id si existe)"""
        doc = {
            "name": entity.name,
            "description": entity.description,
            "config": entity.config.to_dict(),
            "isDefault": entity.is_default,
            "isSystem": entity.is_system,
            "createdBy": entity.created_by
        }

        # Incluir _id solo si es válido
        if entity.id and entity.id != 'new' and entity.id != 'None':
            doc["_id"] = ObjectId(entity.id)

        return doc

    def _entity_to_doc_new(self, entity: PresetConfig) -> dict:
        """Convertir entidad a documento MongoDB (sin _id para inserción)"""
        return {
            "name": entity.name,
            "description": entity.description,
            "config": entity.config.to_dict(),
            "isDefault": entity.is_default,
            "isSystem": entity.is_system,
            "createdBy": entity.created_by
        }


class MongoConfigHistoryRepository(ConfigHistoryRepository):
    """Implementación MongoDB para repositorio de historial de configuraciones"""

    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.configuration_history

    async def save_history_entry(self, history: ConfigHistory) -> ConfigHistory:
        """Guardar entrada en el historial"""
        try:
            history_dict = self._entity_to_doc(history)
            history_dict["createdAt"] = datetime.now(timezone.utc)

            result = await self.collection.insert_one(history_dict)
            history.id = str(result.inserted_id)

            return history
        except Exception as e:
            logger.error(f"Error saving history entry: {e}")
            raise

    async def get_history(self, limit: int = 10) -> List[ConfigHistory]:
        """Obtener historial de configuraciones"""
        try:
            cursor = self.collection.find().sort("createdAt", -1).limit(limit)
            history_list = []
            async for doc in cursor:
                history_list.append(self._doc_to_entity(doc))
            return history_list
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []

    async def get_history_by_config_id(self, config_id: str, limit: int = 10) -> List[ConfigHistory]:
        """Obtener historial de una configuración específica"""
        try:
            cursor = self.collection.find(
                {"config.id": config_id}
            ).sort("createdAt", -1).limit(limit)

            history_list = []
            async for doc in cursor:
                history_list.append(self._doc_to_entity(doc))
            return history_list
        except Exception as e:
            logger.error(f"Error getting history for config {config_id}: {e}")
            return []

    async def clear_old_history(self, days: int = 30) -> int:
        """Limpiar historial antiguo"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            result = await self.collection.delete_many(
                {"createdAt": {"$lt": cutoff_date}}
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error clearing old history: {e}")
            return 0

    def _doc_to_entity(self, doc: dict) -> ConfigHistory:
        """Convertir documento MongoDB a entidad"""
        # Parsear config
        config_repo = MongoInterfaceConfigRepository(self.db)
        config_data = doc.get("config", {})
        temp_doc = {**config_data, "_id": ObjectId()}
        config = config_repo._doc_to_entity(temp_doc)

        # Crear historia
        history = ConfigHistory(
            config=config,
            version=doc.get("version", 1),
            changed_by=doc.get("changedBy"),
            change_description=doc.get("changeDescription"),
            entity_id=str(doc["_id"])
        )

        if "createdAt" in doc:
            history.created_at = doc["createdAt"]

        return history

    def _entity_to_doc(self, entity: ConfigHistory) -> dict:
        """Convertir entidad a documento MongoDB"""
        doc = {
            "config": entity.config.to_dict(),
            "version": entity.version,
            "changedBy": entity.changed_by,
            "changeDescription": entity.change_description
        }

        if entity.id and entity.id != 'new':
            doc["_id"] = ObjectId(entity.id)

        return doc
