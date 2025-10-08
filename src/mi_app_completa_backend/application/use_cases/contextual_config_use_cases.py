"""
Casos de uso para configuraciones contextuales
FASE 3: Sistema de Configuración Contextual con resolución de herencia
"""

from typing import Optional, List
from datetime import datetime

from ..dto.contextual_config_dto import (
    ContextualConfigCreateDTO,
    ContextualConfigUpdateDTO,
    ContextualConfigResponseDTO,
    EffectiveConfigRequestDTO,
    EffectiveConfigResponseDTO,
    ContextualConfigListDTO,
    ContextualConfigSearchDTO,
    UserPreferencesDTO,
    BulkContextualConfigDTO,
    ConfigContextDTO
)
from ..dto.interface_config_dto import InterfaceConfigResponseDTO
from ...domain.entities.contextual_config import ContextualConfig
from ...domain.entities.interface_config import (
    InterfaceConfig, ThemeConfig, ColorConfig, TypographyConfig, 
    LayoutConfig, LogoConfig, BrandingConfig
)
from ...domain.value_objects.config_context import ConfigContext
from ...domain.repositories.contextual_config_repository import ContextualConfigRepository
from ...domain.repositories.interface_config_repository import InterfaceConfigRepository
from ...infrastructure.utils.logger import get_logger

logger = get_logger(__name__)


class ContextualConfigUseCases:
    """
    Casos de uso para configuración contextual
    Implementa lógica de resolución de herencia y gestión de configuraciones por contexto
    """

    def __init__(
        self,
        contextual_repo: ContextualConfigRepository,
        interface_repo: InterfaceConfigRepository
    ):
        self.contextual_repo = contextual_repo
        self.interface_repo = interface_repo

    async def get_effective_config(
        self, 
        request: EffectiveConfigRequestDTO
    ) -> Optional[EffectiveConfigResponseDTO]:
        """
        Obtener configuración efectiva para un usuario siguiendo la jerarquía
        
        Jerarquía de prioridades:
        1. user (específico del usuario)
        2. role (configuración del rol)  
        3. org (configuración de la organización)
        4. global (configuración global del sistema)
        """
        try:
            # Definir cadena de resolución
            resolution_chain = []
            contexts_to_check = [
                ("user", request.user_id),
                ("role", request.user_role) if request.user_role else None,
                ("org", request.org_id) if request.org_id else None,
                ("global", None)
            ]
            
            # FILTRAR valores None antes del loop para evitar error de unpack
            contexts_to_check = [ctx for ctx in contexts_to_check if ctx is not None]
            
            # Filtrar contextos válidos y crear cadena de resolución
            for context_type, context_id in contexts_to_check:
                if context_type and (context_id or context_type == "global"):
                    context = ConfigContext(context_type=context_type, context_id=context_id)
                    resolution_chain.append(self._context_to_dto(context))

            # Buscar configuración en orden de prioridad
            resolved_from = None
            effective_config = None

            for context_dto in resolution_chain:
                contextual_config = await self.contextual_repo.get_config_for_context(
                    context_dto.context_type,
                    context_dto.context_id,
                    active_only=True
                )
                
                if contextual_config:
                    effective_config = contextual_config.config
                    resolved_from = context_dto
                    break

            if not effective_config:
                # Fallback: usar configuración global del sistema
                effective_config = await self.interface_repo.get_current_config()
                if effective_config:
                    resolved_from = ConfigContextDTO(context_type="global", context_id=None)
                    logger.info(f"Using system default config for user {request.user_id}")

            if not effective_config:
                logger.warning(f"No configuration available for user {request.user_id}")
                return None

            # Convertir a DTO de respuesta
            config_dto = self._interface_config_to_dto(effective_config)
            
            return EffectiveConfigResponseDTO(
                config=config_dto,
                resolved_from=resolved_from,
                resolution_chain=resolution_chain
            )

        except Exception as e:
            logger.error(f"Error getting effective config for user {request.user_id}: {e}")
            return None

    async def create_contextual_config(
        self,
        config_data: ContextualConfigCreateDTO,
        created_by: Optional[str] = None
    ) -> ContextualConfigResponseDTO:
        """Crear nueva configuración contextual"""
        try:
            # Crear contexto
            context = ConfigContext(
                context_type=config_data.context.context_type,
                context_id=config_data.context.context_id
            )

            # Crear configuración de interfaz
            interface_config = self._create_dto_to_interface_entity(config_data.config)
            
            # Crear configuración contextual
            contextual_config = ContextualConfig(
                config=interface_config,
                context=context,
                is_active=config_data.is_active,
                created_by=created_by
            )

            # Guardar
            saved_config = await self.contextual_repo.save(contextual_config)
            
            logger.info(f"Contextual config created for {context.context_type}:{context.context_id}")
            return self._entity_to_response_dto(saved_config)

        except Exception as e:
            logger.error(f"Error creating contextual config: {e}")
            raise

    async def update_contextual_config(
        self,
        config_id: str,
        config_data: ContextualConfigUpdateDTO,
        updated_by: Optional[str] = None
    ) -> Optional[ContextualConfigResponseDTO]:
        """Actualizar configuración contextual existente"""
        try:
            # Obtener configuración existente
            existing_config = await self.contextual_repo.get_by_id(config_id)
            if not existing_config:
                logger.warning(f"Contextual config not found: {config_id}")
                return None

            # Actualizar solo los campos proporcionados
            if config_data.config:
                updated_interface_config = self._create_dto_to_interface_entity(config_data.config)
                existing_config._config = updated_interface_config

            if config_data.is_active is not None:
                existing_config._is_active = config_data.is_active

            # Actualizar timestamp y usuario
            existing_config.updated_at = datetime.utcnow()
            if updated_by:
                existing_config._created_by = updated_by  # Track last updater

            # Guardar cambios
            saved_config = await self.contextual_repo.save(existing_config)
            
            logger.info(f"Contextual config updated: {config_id}")
            return self._entity_to_response_dto(saved_config)

        except Exception as e:
            logger.error(f"Error updating contextual config {config_id}: {e}")
            raise

    async def get_contextual_config_by_id(
        self, 
        config_id: str
    ) -> Optional[ContextualConfigResponseDTO]:
        """Obtener configuración contextual por ID"""
        try:
            config = await self.contextual_repo.get_by_id(config_id)
            if config:
                return self._entity_to_response_dto(config)
            return None

        except Exception as e:
            logger.error(f"Error getting contextual config {config_id}: {e}")
            return None

    async def get_user_config(
        self, 
        user_id: str
    ) -> Optional[ContextualConfigResponseDTO]:
        """Obtener configuración específica de un usuario"""
        try:
            config = await self.contextual_repo.get_config_for_context("user", user_id)
            if config:
                return self._entity_to_response_dto(config)
            return None

        except Exception as e:
            logger.error(f"Error getting user config for {user_id}: {e}")
            return None

    async def get_role_config(
        self, 
        role_name: str
    ) -> Optional[ContextualConfigResponseDTO]:
        """Obtener configuración específica de un rol"""
        try:
            config = await self.contextual_repo.get_config_for_context("role", role_name)
            if config:
                return self._entity_to_response_dto(config)
            return None

        except Exception as e:
            logger.error(f"Error getting role config for {role_name}: {e}")
            return None

    async def search_contextual_configs(
        self,
        search_params: ContextualConfigSearchDTO
    ) -> ContextualConfigListDTO:
        """Buscar configuraciones contextuales con paginación"""
        try:
            # Obtener todas las configuraciones del tipo especificado
            if search_params.context_type:
                configs = await self.contextual_repo.get_configs_for_context_type(
                    search_params.context_type,
                    active_only=search_params.active_only
                )
            else:
                configs = await self.contextual_repo.list_all(
                    active_only=search_params.active_only
                )

            # Filtrar por created_by si se especifica
            if search_params.created_by:
                configs = [c for c in configs if c.created_by == search_params.created_by]

            # Filtrar por context_id si se especifica
            if search_params.context_id:
                configs = [c for c in configs if c.context.context_id == search_params.context_id]

            # Paginación
            total = len(configs)
            start = (search_params.page - 1) * search_params.size
            end = start + search_params.size
            paginated_configs = configs[start:end]

            # Convertir a DTOs
            config_dtos = [self._entity_to_response_dto(config) for config in paginated_configs]

            return ContextualConfigListDTO(
                configs=config_dtos,
                total=total,
                page=search_params.page,
                size=search_params.size,
                has_next=end < total,
                has_prev=search_params.page > 1
            )

        except Exception as e:
            logger.error(f"Error searching contextual configs: {e}")
            raise

    async def delete_contextual_config(self, config_id: str) -> bool:
        """Eliminar configuración contextual"""
        try:
            success = await self.contextual_repo.delete_by_id(config_id)
            if success:
                logger.info(f"Contextual config deleted: {config_id}")
            else:
                logger.warning(f"Contextual config not found for deletion: {config_id}")
            return success

        except Exception as e:
            logger.error(f"Error deleting contextual config {config_id}: {e}")
            return False

    async def save_user_preferences(
        self,
        preferences: UserPreferencesDTO
    ) -> ContextualConfigResponseDTO:
        """
        Guardar preferencias simplificadas de usuario
        Crea o actualiza una configuración contextual basada en preferencias simples
        """
        try:
            # Obtener configuración base (global o la actual del usuario)
            base_config = await self.get_effective_config(
                EffectiveConfigRequestDTO(user_id=preferences.user_id)
            )
            
            if not base_config:
                # Usar configuración por defecto del sistema
                system_config = await self.interface_repo.get_current_config()
                if not system_config:
                    raise ValueError("No base configuration available")
                base_interface_config = system_config
            else:
                base_interface_config = self._dto_to_interface_config_entity(base_config.config)

            # Aplicar preferencias sobre la configuración base
            modified_config = self._apply_user_preferences_to_config(
                base_interface_config, 
                preferences
            )

            # Crear contexto de usuario
            context = ConfigContext(context_type="user", context_id=preferences.user_id)

            # Crear configuración contextual
            contextual_config = ContextualConfig(
                config=modified_config,
                context=context,
                is_active=True,
                created_by=preferences.user_id
            )

            # Guardar
            saved_config = await self.contextual_repo.save(contextual_config)
            
            logger.info(f"User preferences saved for {preferences.user_id}")
            return self._entity_to_response_dto(saved_config)

        except Exception as e:
            logger.error(f"Error saving user preferences for {preferences.user_id}: {e}")
            raise

    # Métodos privados de conversión y utilidad

    def _entity_to_response_dto(self, contextual_config: ContextualConfig) -> ContextualConfigResponseDTO:
        """Convertir entidad a DTO de respuesta"""
        config_dto = self._interface_config_to_dto(contextual_config.config)
        context_dto = self._context_to_dto(contextual_config.context)

        return ContextualConfigResponseDTO(
            id=contextual_config.id,
            config=config_dto,
            context=context_dto,
            is_active=contextual_config.is_active,
            created_by=contextual_config.created_by,
            created_at=contextual_config.created_at or datetime.utcnow(),
            updated_at=contextual_config.updated_at or datetime.utcnow()
        )

    def _context_to_dto(self, context: ConfigContext) -> ConfigContextDTO:
        """Convertir contexto a DTO"""
        return ConfigContextDTO(
            context_type=context.context_type,
            context_id=context.context_id
        )

    def _interface_config_to_dto(self, config: InterfaceConfig) -> InterfaceConfigResponseDTO:
        """Convertir configuración de interfaz a DTO"""
        # Reutilizar la lógica existente de interface_config_use_cases
        # Por ahora, implementación básica
        from ..use_cases.interface_config_use_cases import InterfaceConfigUseCases
        
        # TODO: Refactorizar para evitar dependencia circular
        # Esta lógica debería estar en un servicio compartido
        return InterfaceConfigResponseDTO(
            id=config.id or "new",
            theme=config.theme.to_dict(),
            logos=config.logos.to_dict(),
            branding=config.branding.to_dict(),
            customCSS=config.custom_css,
            isActive=config.is_active,
            createdAt=config.created_at or datetime.utcnow(),
            updatedAt=config.updated_at or datetime.utcnow(),
            createdBy=config.created_by
        )

    def _create_dto_to_interface_entity(self, dto) -> InterfaceConfig:
        """Convertir DTO de creación a entidad de interfaz"""
        # Reutilizar la lógica existente del InterfaceConfigUseCases
        from .interface_config_use_cases import InterfaceConfigUseCases
        
        # Crear una instancia temporal para usar su método de conversión
        temp_use_case = InterfaceConfigUseCases(
            self.interface_repo, 
            None,  # preset_repo no necesario para esta conversión
            None   # history_repo no necesario para esta conversión
        )
        
        return temp_use_case._create_dto_to_entity(dto, None)

    def _dto_to_interface_config_entity(self, dto: InterfaceConfigResponseDTO) -> InterfaceConfig:
        """Convertir DTO de respuesta a entidad"""
        # Crear configuración de colores - acceso directo a atributos DTO
        colors = ColorConfig(
            primary=dto.theme.colors.primary,
            secondary=dto.theme.colors.secondary,
            accent=dto.theme.colors.accent,
            neutral=dto.theme.colors.neutral
        )
        
        # Crear configuración de tipografía - acceso directo a atributos DTO
        typography = TypographyConfig(
            font_family=dto.theme.typography.fontFamily,
            font_size=dto.theme.typography.fontSize,
            font_weight=dto.theme.typography.fontWeight
        )
        
        # Crear configuración de layout - acceso directo a atributos DTO
        layout = LayoutConfig(
            border_radius=dto.theme.layout.borderRadius,
            spacing=dto.theme.layout.spacing,
            shadows=dto.theme.layout.shadows
        )
        
        # Crear configuración de tema - acceso directo a atributos DTO
        theme = ThemeConfig(
            mode=dto.theme.mode,
            name=dto.theme.name,
            colors=colors,
            typography=typography,
            layout=layout
        )
        
        # Crear configuración de logos - acceso directo a atributos DTO
        logos = LogoConfig(
            main_logo=dto.logos.mainLogo,
            favicon=dto.logos.favicon,
            sidebar_logo=dto.logos.sidebarLogo
        )
        
        # Crear configuración de branding - acceso directo a atributos DTO
        branding = BrandingConfig(
            app_name=dto.branding.appName,
            app_description=dto.branding.appDescription,
            welcome_message=dto.branding.welcomeMessage,
            login_page_title=getattr(dto.branding, 'loginPageTitle', ''),
            login_page_description=getattr(dto.branding, 'loginPageDescription', ''),
            tagline=getattr(dto.branding, 'tagline', None),
            company_name=getattr(dto.branding, 'companyName', None),
            footer_text=getattr(dto.branding, 'footerText', None),
            support_email=getattr(dto.branding, 'supportEmail', None)
        )
        
        # Crear configuración completa
        return InterfaceConfig(
            theme=theme,
            logos=logos,
            branding=branding,
            custom_css=dto.customCSS,
            is_active=dto.isActive,
            created_by=dto.createdBy,
            entity_id=dto.id
        )

    def _apply_user_preferences_to_config(
        self, 
        base_config: InterfaceConfig, 
        preferences: UserPreferencesDTO
    ) -> InterfaceConfig:
        """Aplicar preferencias de usuario sobre configuración base"""
        # Crear una copia de la configuración base
        modified_config = InterfaceConfig(
            theme=base_config.theme,
            logos=base_config.logos,
            branding=base_config.branding,
            custom_css=base_config.custom_css,
            is_active=True,
            created_by=preferences.user_id
        )
        
        # Aplicar preferencias de tema
        if preferences.theme_mode:
            modified_config.theme.mode = preferences.theme_mode
        
        # Aplicar color primario personalizado
        if preferences.primary_color:
            # Generar paleta completa basada en el color primario
            primary_shades = self._generate_color_shades(preferences.primary_color)
            modified_config.theme.colors.primary = primary_shades
        
        # Aplicar tamaño de fuente
        if preferences.font_size:
            font_size_mapping = {
                "sm": {"base": "0.875rem", "lg": "1rem", "xl": "1.125rem"},
                "base": {"base": "1rem", "lg": "1.125rem", "xl": "1.25rem"},
                "lg": {"base": "1.125rem", "lg": "1.25rem", "xl": "1.375rem"}
            }
            if preferences.font_size in font_size_mapping:
                modified_config.theme.typography.font_size.update(font_size_mapping[preferences.font_size])
        
        # Aplicar modo compacto (afecta spacing)
        if preferences.compact_mode is not None:
            if preferences.compact_mode:
                # Reducir espaciado para modo compacto
                compact_spacing = {k: f"{float(v.replace('rem', '')) * 0.8}rem" 
                                 for k, v in modified_config.theme.layout.spacing.items() 
                                 if 'rem' in str(v)}
                modified_config.theme.layout.spacing.update(compact_spacing)
        
        return modified_config
    
    def _generate_color_shades(self, base_color: str) -> dict:
        """
        Generar paleta de colores basada en un color base
        Implementación simplificada - en producción usar librería de colores
        """
        # Por ahora, retornar el color base para todas las variaciones
        # En producción, usar una librería como colormath para generar shades
        return {
            "50": self._lighten_color(base_color, 0.9),
            "100": self._lighten_color(base_color, 0.8),
            "200": self._lighten_color(base_color, 0.6),
            "300": self._lighten_color(base_color, 0.4),
            "400": self._lighten_color(base_color, 0.2),
            "500": base_color,  # Color base
            "600": self._darken_color(base_color, 0.1),
            "700": self._darken_color(base_color, 0.2),
            "800": self._darken_color(base_color, 0.3),
            "900": self._darken_color(base_color, 0.4)
        }
    
    def _lighten_color(self, color: str, amount: float) -> str:
        """Aclarar color (implementación simplificada)"""
        # Implementación básica - en producción usar librería de colores
        return color  # Placeholder
    
    def _darken_color(self, color: str, amount: float) -> str:
        """Oscurecer color (implementación simplificada)"""
        # Implementación básica - en producción usar librería de colores
        return color  # Placeholder