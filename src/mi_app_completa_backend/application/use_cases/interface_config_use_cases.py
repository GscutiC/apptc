"""
Casos de uso para configuración de interfaz
"""

from typing import Optional, List
from datetime import datetime

from ..dto.interface_config_dto import (
    InterfaceConfigCreateDTO, InterfaceConfigUpdateDTO, InterfaceConfigResponseDTO,
    PresetConfigCreateDTO, PresetConfigResponseDTO, ConfigHistoryResponseDTO,
    PartialInterfaceConfigUpdateDTO, ThemeUpdateDTO, ThemeColorUpdateDTO,
    LogoUpdateDTO, BrandingUpdateDTO
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

    async def update_preset(
        self,
        preset_id: str,
        preset_data: PresetConfigCreateDTO,
        updated_by: Optional[str] = None
    ) -> Optional[PresetConfigResponseDTO]:
        """
        Actualizar preset existente (nombre, descripción, configuración)
        No permite editar presets del sistema
        """
        # Obtener preset existente
        existing_preset = await self.preset_repo.get_preset_by_id(preset_id)
        if not existing_preset:
            return None
        
        # Validar que no sea preset del sistema
        if existing_preset.is_system:
            raise ValueError("No se pueden editar presets del sistema")
        
        # Actualizar campos básicos
        existing_preset.update_name(preset_data.name)
        existing_preset.update_description(preset_data.description)
        
        # Actualizar configuración completa
        updated_config = self._create_dto_to_entity(preset_data.config, updated_by)
        existing_preset.update_config(updated_config)
        
        # Si se marca como default, desmarcar otros
        if preset_data.isDefault and not existing_preset.is_default:
            await self._unset_all_default_presets()
            existing_preset.set_as_default()
        elif not preset_data.isDefault and existing_preset.is_default:
            existing_preset.unset_as_default()
        
        # Guardar cambios
        updated_preset = await self.preset_repo.save_preset(existing_preset)
        
        return self._preset_to_response_dto(updated_preset)

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

    async def update_config_partial(
        self,
        config_id: str,
        partial_updates: PartialInterfaceConfigUpdateDTO,
        updated_by: Optional[str] = None
    ) -> Optional[InterfaceConfigResponseDTO]:
        """
        Actualizar configuración con merge inteligente de cambios parciales.
        Solo actualiza los campos especificados, manteniendo el resto intactos.
        
        Args:
            config_id: ID de la configuración a actualizar
            partial_updates: DTO con actualizaciones parciales
            updated_by: Usuario que realiza la actualización
            
        Returns:
            Configuración actualizada o None si no existe
        """
        # Obtener configuración actual
        existing_config = await self.config_repo.get_config_by_id(config_id)
        if not existing_config:
            return None
        
        # Aplicar actualizaciones parciales con merge inteligente
        self._apply_partial_updates_to_config(existing_config, partial_updates)
        
        # Si se activa esta configuración, desactivar las demás
        if partial_updates.isActive is True:
            await self._deactivate_all_configs()
        
        # Guardar cambios
        updated_config = await self.config_repo.save_config(existing_config)
        
        # Obtener siguiente versión para el historial
        history = await self.history_repo.get_history_by_config_id(config_id, 1)
        next_version = (history[0].version + 1) if history else 1
        
        # Determinar descripción del cambio
        change_parts = []
        if partial_updates.theme:
            change_parts.append("tema")
        if partial_updates.logos:
            change_parts.append("logos")
        if partial_updates.branding:
            change_parts.append("branding")
        change_description = f"Actualización parcial: {', '.join(change_parts)}" if change_parts else "Actualización parcial"
        
        # Guardar en historial
        await self._save_to_history(
            updated_config, 
            next_version, 
            updated_by, 
            change_description
        )
        
        return self._config_to_response_dto(updated_config)

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
            company_name=dto.branding.companyName,
            footer_text=getattr(dto.branding, 'footerText', None),
            support_email=getattr(dto.branding, 'supportEmail', None)
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
                company_name=updates.branding.companyName,
                footer_text=getattr(updates.branding, 'footerText', None),
                support_email=getattr(updates.branding, 'supportEmail', None)
            )
            config.update_branding(branding)
        
        if updates.customCSS is not None:
            config.update_custom_css(updates.customCSS)
        
        if updates.isActive is not None:
            if updates.isActive:
                config.activate()
            else:
                config.deactivate()

    def _apply_partial_updates_to_config(
        self,
        config: InterfaceConfig,
        updates: PartialInterfaceConfigUpdateDTO
    ) -> None:
        """
        Aplicar actualizaciones parciales con merge inteligente.
        Solo actualiza los campos especificados, manteniendo el resto intactos.
        """
        
        # Actualizar tema (merge inteligente)
        if updates.theme:
            # Mantener el tema actual y solo actualizar lo especificado
            current_theme_dict = config.theme.to_dict()
            
            # Actualizar mode si se especificó
            if updates.theme.mode is not None:
                current_theme_dict['mode'] = updates.theme.mode
            
            # Actualizar name si se especificó
            if updates.theme.name is not None:
                current_theme_dict['name'] = updates.theme.name
            
            # Merge inteligente de colores
            if updates.theme.colors:
                # Mantener colores actuales
                current_colors = current_theme_dict['colors']
                
                # Actualizar solo los sets de colores especificados
                if updates.theme.colors.primary is not None:
                    # Merge de shades individuales
                    current_colors['primary'].update(updates.theme.colors.primary)
                
                if updates.theme.colors.secondary is not None:
                    current_colors['secondary'].update(updates.theme.colors.secondary)
                
                if updates.theme.colors.accent is not None:
                    current_colors['accent'].update(updates.theme.colors.accent)
                
                if updates.theme.colors.neutral is not None:
                    current_colors['neutral'].update(updates.theme.colors.neutral)
            
            # Merge de tipografía
            if updates.theme.typography:
                current_typo = current_theme_dict['typography']
                if updates.theme.typography.fontFamily is not None:
                    current_typo['fontFamily'].update(updates.theme.typography.fontFamily)
                if updates.theme.typography.fontSize is not None:
                    current_typo['fontSize'].update(updates.theme.typography.fontSize)
                if updates.theme.typography.fontWeight is not None:
                    current_typo['fontWeight'].update(updates.theme.typography.fontWeight)
            
            # Merge de layout
            if updates.theme.layout:
                current_layout = current_theme_dict['layout']
                if updates.theme.layout.borderRadius is not None:
                    current_layout['borderRadius'].update(updates.theme.layout.borderRadius)
                if updates.theme.layout.spacing is not None:
                    current_layout['spacing'].update(updates.theme.layout.spacing)
                if updates.theme.layout.shadows is not None:
                    current_layout['shadows'].update(updates.theme.layout.shadows)
            
            # Reconstruir entidades de tema
            colors = ColorConfig(
                primary=current_theme_dict['colors']['primary'],
                secondary=current_theme_dict['colors']['secondary'],
                accent=current_theme_dict['colors']['accent'],
                neutral=current_theme_dict['colors']['neutral']
            )
            
            typography = TypographyConfig(
                font_family=current_theme_dict['typography']['fontFamily'],
                font_size=current_theme_dict['typography']['fontSize'],
                font_weight=current_theme_dict['typography']['fontWeight']
            )
            
            layout = LayoutConfig(
                border_radius=current_theme_dict['layout']['borderRadius'],
                spacing=current_theme_dict['layout']['spacing'],
                shadows=current_theme_dict['layout']['shadows']
            )
            
            theme = ThemeConfig(
                mode=current_theme_dict['mode'],
                name=current_theme_dict['name'],
                colors=colors,
                typography=typography,
                layout=layout
            )
            
            config.update_theme(theme)
        
        # Actualizar logos (merge parcial)
        if updates.logos:
            current_logos = config.logos.to_dict()
            
            # Helper para hacer merge inteligente que elimina valores None
            def merge_with_none_deletion(target_dict: dict, updates_dict: dict) -> None:
                """
                Merge que elimina claves cuando el valor es None (undefined en JS)
                Esto permite eliminar logos correctamente desde el frontend.
                """
                for key, value in updates_dict.items():
                    if value is None:
                        # Si el valor es None, eliminarlo del diccionario
                        target_dict.pop(key, None)
                    else:
                        # Si el valor no es None, actualizarlo
                        target_dict[key] = value
            
            if updates.logos.mainLogo is not None:
                merge_with_none_deletion(current_logos['mainLogo'], updates.logos.mainLogo)
            if updates.logos.favicon is not None:
                merge_with_none_deletion(current_logos['favicon'], updates.logos.favicon)
            if updates.logos.sidebarLogo is not None:
                merge_with_none_deletion(current_logos['sidebarLogo'], updates.logos.sidebarLogo)
            
            logos = LogoConfig(
                main_logo=current_logos['mainLogo'],
                favicon=current_logos['favicon'],
                sidebar_logo=current_logos['sidebarLogo']
            )
            config.update_logos(logos)
        
        # Actualizar branding (merge parcial)
        if updates.branding:
            current_branding = config.branding.to_dict()
            
            # Solo actualizar campos especificados
            if updates.branding.appName is not None:
                current_branding['appName'] = updates.branding.appName
            if updates.branding.appDescription is not None:
                current_branding['appDescription'] = updates.branding.appDescription
            if updates.branding.welcomeMessage is not None:
                current_branding['welcomeMessage'] = updates.branding.welcomeMessage
            if updates.branding.loginPageTitle is not None:
                current_branding['loginPageTitle'] = updates.branding.loginPageTitle
            if updates.branding.loginPageDescription is not None:
                current_branding['loginPageDescription'] = updates.branding.loginPageDescription
            if updates.branding.tagline is not None:
                current_branding['tagline'] = updates.branding.tagline
            if updates.branding.companyName is not None:
                current_branding['companyName'] = updates.branding.companyName
            if updates.branding.footerText is not None:
                current_branding['footerText'] = updates.branding.footerText
            if updates.branding.supportEmail is not None:
                current_branding['supportEmail'] = updates.branding.supportEmail
            
            branding = BrandingConfig(
                app_name=current_branding['appName'],
                app_description=current_branding['appDescription'],
                welcome_message=current_branding['welcomeMessage'],
                login_page_title=current_branding['loginPageTitle'],
                login_page_description=current_branding['loginPageDescription'],
                tagline=current_branding.get('tagline'),
                company_name=current_branding.get('companyName'),
                footer_text=current_branding.get('footerText'),
                support_email=current_branding.get('supportEmail')
            )
            config.update_branding(branding)
        
        # Actualizar CSS personalizado
        if updates.customCSS is not None:
            config.update_custom_css(updates.customCSS)
        
        # Actualizar estado activo
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

    async def create_default_config(self) -> InterfaceConfigResponseDTO:
        """
        🆕 Crear configuración por defecto basada en interface_config.json del backend
        Se usa cuando no hay configuración en BD
        """
        import json
        import os
        from pathlib import Path
        
        try:
            # Intentar cargar desde interface_config.json del root del proyecto
            backend_config_path = Path(__file__).parent.parent.parent.parent.parent / "interface_config.json"
            
            if backend_config_path.exists():
                with open(backend_config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Convertir a entidad usando el formato del archivo
                config = self._create_config_from_file_data(config_data)
                
                # Guardar en BD como activa
                saved_config = await self.config_repo.save_config(config)
                
                return self._config_to_response_dto(saved_config)
            
        except Exception as e:
            print(f"⚠️ Error cargando config desde archivo: {e}")
        
        # Fallback: crear configuración mínima hardcodeada
        theme = ThemeConfig(
            mode="light",
            name="Configuración por Defecto",
            colors=ColorConfig(
                primary={"500": "#10b981", "600": "#059669", "700": "#047857"},
                secondary={"500": "#6b7280", "600": "#4b5563", "700": "#374151"},
                accent={"500": "#10b981", "600": "#059669", "700": "#047857"},
                neutral={"500": "#6b7280", "600": "#4b5563", "700": "#374151"}
            ),
            typography=TypographyConfig(
                font_family={"primary": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"},
                font_size={"base": "1rem", "lg": "1.125rem"},
                font_weight={"normal": 400, "medium": 500, "bold": 700}
            ),
            layout=LayoutConfig(
                border_radius={"base": "0.25rem", "lg": "0.5rem"},
                spacing={"base": "1rem"},
                shadows={"base": "0 1px 3px 0 rgb(0 0 0 / 0.1)"}
            )
        )
        
        logos = LogoConfig(
            main_logo={"text": "WorkTecApp", "showText": True, "showImage": False},
            favicon={},
            sidebar_logo={"text": "WorkTecApp", "showText": True, "showImage": False, "collapsedText": "WT"}
        )
        
        branding = BrandingConfig(
            app_name="WorkTecApp",
            app_description="Soluciones empresariales sostenibles",
            tagline="Soluciones empresariales sostenibles",
            company_name="WorkTec Solutions",
            welcome_message="Bienvenido a WorkTecApp"
        )
        
        config = InterfaceConfig(
            theme=theme,
            logos=logos,
            branding=branding,
            is_active=True,
            created_by="system"
        )
        
        # Guardar en BD
        saved_config = await self.config_repo.save_config(config)
        
        return self._config_to_response_dto(saved_config)

    def _create_config_from_file_data(self, data: dict) -> InterfaceConfig:
        """Crear configuración desde datos del archivo JSON"""
        
        # Usar la configuración anidada si existe
        config_data = data.get('config', data)
        theme_data = config_data.get('theme', data.get('theme', {}))
        
        theme = ThemeConfig(
            mode=theme_data.get('mode', 'light'),
            name=theme_data.get('name', 'Tema desde Archivo'),
            colors=ColorConfig(
                primary=theme_data.get('colors', {}).get('primary', {"500": "#10b981"}),
                secondary=theme_data.get('colors', {}).get('secondary', {"500": "#6b7280"}),
                accent=theme_data.get('colors', {}).get('accent', {"500": "#10b981"}),
                neutral=theme_data.get('colors', {}).get('neutral', {"500": "#6b7280"})
            ),
            typography=TypographyConfig(
                font_family=theme_data.get('typography', {}).get('fontFamily', {"primary": "system-ui"}),
                font_size=theme_data.get('typography', {}).get('fontSize', {"base": "1rem"}),
                font_weight=theme_data.get('typography', {}).get('fontWeight', {"normal": 400})
            ),
            layout=LayoutConfig(
                border_radius=theme_data.get('layout', {}).get('borderRadius', {"base": "0.25rem"}),
                spacing=theme_data.get('layout', {}).get('spacing', {"base": "1rem"}),
                shadows=theme_data.get('layout', {}).get('shadows', {"base": "0 1px 3px rgba(0,0,0,0.1)"})
            )
        )
        
        logos_data = config_data.get('logos', data.get('logos', {}))
        logos = LogoConfig(
            main_logo=logos_data.get('mainLogo', {"text": "App", "showText": True, "showImage": False}),
            favicon=logos_data.get('favicon', {}),
            sidebar_logo=logos_data.get('sidebarLogo', {"text": "App", "showText": True, "showImage": False})
        )
        
        branding_data = config_data.get('branding', data.get('branding', {}))
        branding = BrandingConfig(
            app_name=branding_data.get('appName', 'Aplicación'),
            app_description=branding_data.get('appDescription', 'Sistema de gestión'),
            tagline=branding_data.get('tagline', ''),
            company_name=branding_data.get('companyName', ''),
            welcome_message=branding_data.get('welcomeMessage', 'Bienvenido')
        )
        
        return InterfaceConfig(
            theme=theme,
            logos=logos,
            branding=branding,
            custom_css=config_data.get('customCSS'),
            is_active=True,
            created_by="system-default"
        )