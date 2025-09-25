"""
Casos de uso para configuración de interfaz
"""

from typing import Optional, List
from datetime import datetime

from ..dto.interface_config_dto import (
    InterfaceConfigCreateDTO, InterfaceConfigUpdateDTO, InterfaceConfigResponseDTO,
    PresetConfigCreateDTO, PresetConfigResponseDTO, ConfigHistoryResponseDTO
)
from ...domain.entities.interface_config import (
    InterfaceConfig, PresetConfig, ConfigHistory,
    ThemeConfig, ColorConfig, TypographyConfig, LayoutConfig, LogoConfig, BrandingConfig
)
from ...domain.repositories.interface_config_repository import (
    InterfaceConfigRepository, PresetConfigRepository, ConfigHistoryRepository
)


class InterfaceConfigUseCases:
    """Casos de uso para configuración de interfaz"""

    def __init__(
        self,
        config_repo: InterfaceConfigRepository,
        preset_repo: PresetConfigRepository,
        history_repo: ConfigHistoryRepository
    ):
        self.config_repo = config_repo
        self.preset_repo = preset_repo
        self.history_repo = history_repo

    async def get_current_config(self) -> Optional[InterfaceConfigResponseDTO]:
        """Obtener configuración actual"""
        config = await self.config_repo.get_current_config()
        if not config:
            return None
        
        return self._config_to_response_dto(config)

    async def create_config(
        self, 
        config_data: InterfaceConfigCreateDTO, 
        created_by: Optional[str] = None
    ) -> InterfaceConfigResponseDTO:
        """Crear nueva configuración"""
        
        # Crear entidad de configuración
        config = self._create_dto_to_entity(config_data, created_by)
        
        # Si esta configuración se marca como activa, desactivar las demás
        if config.is_active:
            await self._deactivate_all_configs()
        
        # Guardar configuración
        saved_config = await self.config_repo.save_config(config)
        
        # Guardar en historial
        await self._save_to_history(saved_config, 1, created_by, "Configuración creada")
        
        return self._config_to_response_dto(saved_config)

    async def update_config(
        self,
        config_id: str,
        config_data: InterfaceConfigUpdateDTO,
        updated_by: Optional[str] = None
    ) -> Optional[InterfaceConfigResponseDTO]:
        """Actualizar configuración existente"""
        
        # Obtener configuración actual
        existing_config = await self.config_repo.get_config_by_id(config_id)
        if not existing_config:
            return None
        
        # Aplicar actualizaciones
        self._apply_updates_to_config(existing_config, config_data)
        
        # Si se activa esta configuración, desactivar las demás
        if config_data.isActive is True:
            await self._deactivate_all_configs()
        
        # Guardar cambios
        updated_config = await self.config_repo.save_config(existing_config)
        
        # Obtener siguiente versión para el historial
        history = await self.history_repo.get_history_by_config_id(config_id, 1)
        next_version = (history[0].version + 1) if history else 1
        
        # Guardar en historial
        await self._save_to_history(
            updated_config, 
            next_version, 
            updated_by, 
            "Configuración actualizada"
        )
        
        return self._config_to_response_dto(updated_config)

    async def delete_config(self, config_id: str) -> bool:
        """Eliminar configuración"""
        return await self.config_repo.delete_config(config_id)

    async def set_active_config(self, config_id: str) -> bool:
        """Establecer configuración como activa"""
        # Desactivar todas las configuraciones
        await self._deactivate_all_configs()
        
        # Activar la configuración especificada
        return await self.config_repo.set_active_config(config_id)

    async def get_all_presets(self) -> List[PresetConfigResponseDTO]:
        """Obtener todos los presets"""
        presets = await self.preset_repo.get_all_presets()
        return [self._preset_to_response_dto(preset) for preset in presets]

    async def create_preset(
        self,
        preset_data: PresetConfigCreateDTO,
        created_by: Optional[str] = None
    ) -> PresetConfigResponseDTO:
        """Crear nuevo preset"""
        
        # Crear configuración del preset
        config = self._create_dto_to_entity(preset_data.config, created_by)
        
        # Crear preset
        preset = PresetConfig(
            name=preset_data.name,
            description=preset_data.description,
            config=config,
            is_default=preset_data.isDefault,
            is_system=preset_data.isSystem,
            created_by=created_by
        )
        
        # Si es preset por defecto, desmarcar otros
        if preset.is_default:
            await self._unset_all_default_presets()
        
        # Guardar preset
        saved_preset = await self.preset_repo.save_preset(preset)
        
        return self._preset_to_response_dto(saved_preset)

    async def delete_preset(self, preset_id: str) -> bool:
        """Eliminar preset (solo si no es del sistema)"""
        preset = await self.preset_repo.get_preset_by_id(preset_id)
        if preset and preset.is_system:
            raise ValueError("No se pueden eliminar presets del sistema")
        
        return await self.preset_repo.delete_preset(preset_id)

    async def apply_preset(
        self,
        preset_id: str,
        applied_by: Optional[str] = None
    ) -> Optional[InterfaceConfigResponseDTO]:
        """Aplicar preset como configuración activa"""
        
        # Obtener preset
        preset = await self.preset_repo.get_preset_by_id(preset_id)
        if not preset:
            return None
        
        # Crear nueva configuración basada en el preset
        config = InterfaceConfig(
            theme=preset.config.theme,
            logos=preset.config.logos,
            branding=preset.config.branding,
            custom_css=preset.config.custom_css,
            is_active=True,
            created_by=applied_by
        )
        
        # Desactivar configuraciones actuales
        await self._deactivate_all_configs()
        
        # Guardar nueva configuración
        saved_config = await self.config_repo.save_config(config)
        
        # Guardar en historial
        await self._save_to_history(
            saved_config, 
            1, 
            applied_by, 
            f"Preset aplicado: {preset.name}"
        )
        
        return self._config_to_response_dto(saved_config)

    async def get_config_history(self, limit: int = 10) -> List[ConfigHistoryResponseDTO]:
        """Obtener historial de configuraciones"""
        history = await self.history_repo.get_history(limit)
        return [self._history_to_response_dto(entry) for entry in history]

    # Métodos privados

    async def _deactivate_all_configs(self) -> None:
        """Desactivar todas las configuraciones"""
        configs = await self.config_repo.get_all_configs()
        for config in configs:
            if config.is_active:
                config.deactivate()
                await self.config_repo.save_config(config)

    async def _unset_all_default_presets(self) -> None:
        """Desmarcar todos los presets por defecto"""
        presets = await self.preset_repo.get_all_presets()
        for preset in presets:
            if preset.is_default:
                preset.unset_as_default()
                await self.preset_repo.save_preset(preset)

    async def _save_to_history(
        self,
        config: InterfaceConfig,
        version: int,
        changed_by: Optional[str],
        description: str
    ) -> None:
        """Guardar configuración en historial"""
        history_entry = ConfigHistory(
            config=config,
            version=version,
            changed_by=changed_by,
            change_description=description
        )
        await self.history_repo.save_history_entry(history_entry)

    def _create_dto_to_entity(
        self, 
        dto: InterfaceConfigCreateDTO, 
        created_by: Optional[str]
    ) -> InterfaceConfig:
        """Convertir DTO de creación a entidad"""
        
        # Crear configuración de colores
        colors = ColorConfig(
            primary=dto.theme.colors.primary,
            secondary=dto.theme.colors.secondary,
            accent=dto.theme.colors.accent,
            neutral=dto.theme.colors.neutral
        )
        
        # Crear configuración de tipografía
        typography = TypographyConfig(
            font_family=dto.theme.typography.fontFamily,
            font_size=dto.theme.typography.fontSize,
            font_weight=dto.theme.typography.fontWeight
        )
        
        # Crear configuración de layout
        layout = LayoutConfig(
            border_radius=dto.theme.layout.borderRadius,
            spacing=dto.theme.layout.spacing,
            shadows=dto.theme.layout.shadows
        )
        
        # Crear configuración de tema
        theme = ThemeConfig(
            mode=dto.theme.mode,
            name=dto.theme.name,
            colors=colors,
            typography=typography,
            layout=layout
        )
        
        # Crear configuración de logos
        logos = LogoConfig(
            main_logo=dto.logos.mainLogo,
            favicon=dto.logos.favicon,
            sidebar_logo=dto.logos.sidebarLogo
        )
        
        # Crear configuración de branding
        branding = BrandingConfig(
            app_name=dto.branding.appName,
            app_description=dto.branding.appDescription,
            welcome_message=dto.branding.welcomeMessage,
            login_page_title=dto.branding.loginPageTitle,
            login_page_description=dto.branding.loginPageDescription,
            tagline=dto.branding.tagline,
            company_name=dto.branding.companyName
        )
        
        # Crear configuración de interfaz
        return InterfaceConfig(
            theme=theme,
            logos=logos,
            branding=branding,
            custom_css=dto.customCSS,
            is_active=dto.isActive,
            created_by=created_by
        )

    def _apply_updates_to_config(
        self, 
        config: InterfaceConfig, 
        updates: InterfaceConfigUpdateDTO
    ) -> None:
        """Aplicar actualizaciones a configuración existente"""
        
        if updates.theme:
            # Actualizar tema
            colors = ColorConfig(
                primary=updates.theme.colors.primary,
                secondary=updates.theme.colors.secondary,
                accent=updates.theme.colors.accent,
                neutral=updates.theme.colors.neutral
            )
            
            typography = TypographyConfig(
                font_family=updates.theme.typography.fontFamily,
                font_size=updates.theme.typography.fontSize,
                font_weight=updates.theme.typography.fontWeight
            )
            
            layout = LayoutConfig(
                border_radius=updates.theme.layout.borderRadius,
                spacing=updates.theme.layout.spacing,
                shadows=updates.theme.layout.shadows
            )
            
            theme = ThemeConfig(
                mode=updates.theme.mode,
                name=updates.theme.name,
                colors=colors,
                typography=typography,
                layout=layout
            )
            
            config.update_theme(theme)
        
        if updates.logos:
            logos = LogoConfig(
                main_logo=updates.logos.mainLogo,
                favicon=updates.logos.favicon,
                sidebar_logo=updates.logos.sidebarLogo
            )
            config.update_logos(logos)
        
        if updates.branding:
            branding = BrandingConfig(
                app_name=updates.branding.appName,
                app_description=updates.branding.appDescription,
                welcome_message=updates.branding.welcomeMessage,
                login_page_title=updates.branding.loginPageTitle,
                login_page_description=updates.branding.loginPageDescription,
                tagline=updates.branding.tagline,
                company_name=updates.branding.companyName
            )
            config.update_branding(branding)
        
        if updates.customCSS is not None:
            config.update_custom_css(updates.customCSS)
        
        if updates.isActive is not None:
            if updates.isActive:
                config.activate()
            else:
                config.deactivate()

    def _config_to_response_dto(self, config: InterfaceConfig) -> InterfaceConfigResponseDTO:
        """Convertir entidad a DTO de respuesta"""
        return InterfaceConfigResponseDTO(
            id=config.id,
            theme=config.theme.to_dict(),
            logos=config.logos.to_dict(),
            branding=config.branding.to_dict(),
            customCSS=config.custom_css,
            isActive=config.is_active,
            createdAt=config.created_at,
            updatedAt=config.updated_at,
            createdBy=config.created_by
        )

    def _preset_to_response_dto(self, preset: PresetConfig) -> PresetConfigResponseDTO:
        """Convertir preset a DTO de respuesta"""
        return PresetConfigResponseDTO(
            id=preset.id,
            name=preset.name,
            description=preset.description,
            config=self._config_to_response_dto(preset.config),
            isDefault=preset.is_default,
            isSystem=preset.is_system,
            createdAt=preset.created_at,
            updatedAt=preset.updated_at,
            createdBy=preset.created_by
        )

    def _history_to_response_dto(self, history: ConfigHistory) -> ConfigHistoryResponseDTO:
        """Convertir historial a DTO de respuesta"""
        return ConfigHistoryResponseDTO(
            id=history.id,
            config=self._config_to_response_dto(history.config),
            version=history.version,
            changedBy=history.changed_by,
            changeDescription=history.change_description,
            createdAt=history.created_at
        )