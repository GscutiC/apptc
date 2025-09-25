"""
Entidades del dominio para configuración de interfaz
"""

from typing import Optional, Dict, Any
from datetime import datetime
from .base_entity import BaseEntity


class ColorConfig:
    """Value Object para configuración de colores"""
    def __init__(self, primary: Dict[str, str], secondary: Dict[str, str], 
                 accent: Dict[str, str], neutral: Dict[str, str]):
        self.primary = primary
        self.secondary = secondary
        self.accent = accent
        self.neutral = neutral

    def to_dict(self) -> Dict[str, Any]:
        return {
            'primary': self.primary,
            'secondary': self.secondary,
            'accent': self.accent,
            'neutral': self.neutral
        }


class TypographyConfig:
    """Value Object para configuración de tipografía"""
    def __init__(self, font_family: Dict[str, str], font_size: Dict[str, str], 
                 font_weight: Dict[str, int]):
        self.font_family = font_family
        self.font_size = font_size
        self.font_weight = font_weight

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fontFamily': self.font_family,
            'fontSize': self.font_size,
            'fontWeight': self.font_weight
        }


class LayoutConfig:
    """Value Object para configuración de layout"""
    def __init__(self, border_radius: Dict[str, str], spacing: Dict[str, str], 
                 shadows: Dict[str, str]):
        self.border_radius = border_radius
        self.spacing = spacing
        self.shadows = shadows

    def to_dict(self) -> Dict[str, Any]:
        return {
            'borderRadius': self.border_radius,
            'spacing': self.spacing,
            'shadows': self.shadows
        }


class LogoConfig:
    """Value Object para configuración de logos"""
    def __init__(self, main_logo: Dict[str, Any], favicon: Dict[str, Optional[str]], 
                 sidebar_logo: Dict[str, Any]):
        self.main_logo = main_logo
        self.favicon = favicon
        self.sidebar_logo = sidebar_logo

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mainLogo': self.main_logo,
            'favicon': self.favicon,
            'sidebarLogo': self.sidebar_logo
        }


class BrandingConfig:
    """Value Object para configuración de branding"""
    def __init__(self, app_name: str, app_description: str, welcome_message: str,
                 login_page_title: str, login_page_description: str,
                 tagline: Optional[str] = None, company_name: Optional[str] = None):
        self.app_name = app_name
        self.app_description = app_description
        self.tagline = tagline
        self.company_name = company_name
        self.welcome_message = welcome_message
        self.login_page_title = login_page_title
        self.login_page_description = login_page_description

    def to_dict(self) -> Dict[str, Any]:
        return {
            'appName': self.app_name,
            'appDescription': self.app_description,
            'tagline': self.tagline,
            'companyName': self.company_name,
            'welcomeMessage': self.welcome_message,
            'loginPageTitle': self.login_page_title,
            'loginPageDescription': self.login_page_description
        }


class ThemeConfig:
    """Value Object para configuración de tema"""
    def __init__(self, mode: str, name: str, colors: ColorConfig, 
                 typography: TypographyConfig, layout: LayoutConfig):
        self.mode = mode
        self.name = name
        self.colors = colors
        self.typography = typography
        self.layout = layout

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mode': self.mode,
            'name': self.name,
            'colors': self.colors.to_dict(),
            'typography': self.typography.to_dict(),
            'layout': self.layout.to_dict()
        }


class InterfaceConfig(BaseEntity):
    """Entidad para configuración de interfaz"""
    
    def __init__(self, theme: ThemeConfig, logos: LogoConfig, branding: BrandingConfig,
                 is_active: bool = True, custom_css: Optional[str] = None,
                 created_by: Optional[str] = None, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self.theme = theme
        self.logos = logos
        self.branding = branding
        self.custom_css = custom_css
        self.is_active = is_active
        self.created_by = created_by

    def update_theme(self, theme: ThemeConfig) -> None:
        """Actualizar configuración de tema"""
        self.theme = theme
        self.updated_at = datetime.utcnow()

    def update_logos(self, logos: LogoConfig) -> None:
        """Actualizar configuración de logos"""
        self.logos = logos
        self.updated_at = datetime.utcnow()

    def update_branding(self, branding: BrandingConfig) -> None:
        """Actualizar configuración de branding"""
        self.branding = branding
        self.updated_at = datetime.utcnow()

    def update_custom_css(self, custom_css: Optional[str]) -> None:
        """Actualizar CSS personalizado"""
        self.custom_css = custom_css
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Activar configuración"""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Desactivar configuración"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'theme': self.theme.to_dict(),
            'logos': self.logos.to_dict(),
            'branding': self.branding.to_dict(),
            'customCSS': self.custom_css,
            'isActive': self.is_active,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'createdBy': self.created_by
        }


class PresetConfig(BaseEntity):
    """Entidad para presets de configuración"""
    
    def __init__(self, name: str, description: str, config: InterfaceConfig,
                 is_default: bool = False, is_system: bool = False,
                 created_by: Optional[str] = None, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self.name = name
        self.description = description
        self.config = config
        self.is_default = is_default
        self.is_system = is_system
        self.created_by = created_by

    def update_name(self, name: str) -> None:
        """Actualizar nombre del preset"""
        self.name = name
        self.updated_at = datetime.utcnow()

    def update_description(self, description: str) -> None:
        """Actualizar descripción del preset"""
        self.description = description
        self.updated_at = datetime.utcnow()

    def update_config(self, config: InterfaceConfig) -> None:
        """Actualizar configuración del preset"""
        self.config = config
        self.updated_at = datetime.utcnow()

    def set_as_default(self) -> None:
        """Marcar como preset por defecto"""
        self.is_default = True
        self.updated_at = datetime.utcnow()

    def unset_as_default(self) -> None:
        """Desmarcar como preset por defecto"""
        self.is_default = False
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config': self.config.to_dict(),
            'isDefault': self.is_default,
            'isSystem': self.is_system,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
            'createdBy': self.created_by
        }


class ConfigHistory(BaseEntity):
    """Entidad para historial de configuraciones"""
    
    def __init__(self, config: InterfaceConfig, version: int, changed_by: Optional[str] = None,
                 change_description: Optional[str] = None, entity_id: Optional[str] = None):
        super().__init__(entity_id)
        self.config = config
        self.version = version
        self.changed_by = changed_by
        self.change_description = change_description

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        return {
            'id': self.id,
            'config': self.config.to_dict(),
            'version': self.version,
            'changedBy': self.changed_by,
            'changeDescription': self.change_description,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }