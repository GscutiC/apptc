"""
Entidad de dominio para la configuración visual del módulo Techo Propio
Cada usuario tiene su propia configuración personalizada
"""
from typing import Dict, Optional
from datetime import datetime
from .base_entity import BaseEntity


class TechoPropioThemeConfig(BaseEntity):
    """
    Configuración visual del módulo Techo Propio por usuario
    Cada usuario personaliza su propia vista (colores, logos, textos)
    """

    def __init__(
        self,
        user_id: str,
        colors: Dict[str, str],
        logos: Dict[str, Optional[str]],
        branding: Dict[str, str],
        id: Optional[str] = None
    ):
        super().__init__(id)
        self.user_id = user_id
        self.colors = colors
        self.logos = logos
        self.branding = branding

    def update_colors(self, primary: Optional[str] = None, secondary: Optional[str] = None, accent: Optional[str] = None):
        """Actualizar colores específicos"""
        if primary:
            self.colors['primary'] = primary
        if secondary:
            self.colors['secondary'] = secondary
        if accent:
            self.colors['accent'] = accent
        self.update_timestamp()

    def update_logos(
        self, 
        sidebar_icon: Optional[str] = None, 
        sidebar_icon_file_id: Optional[str] = None,
        sidebar_icon_url: Optional[str] = None,
        header_logo: Optional[str] = None,
        header_logo_file_id: Optional[str] = None,
        header_logo_url: Optional[str] = None
    ):
        """Actualizar logos (soporta emojis y archivos subidos)"""
        if sidebar_icon is not None:
            self.logos['sidebar_icon'] = sidebar_icon
        if sidebar_icon_file_id is not None:
            self.logos['sidebar_icon_file_id'] = sidebar_icon_file_id
        if sidebar_icon_url is not None:
            self.logos['sidebar_icon_url'] = sidebar_icon_url
        if header_logo is not None:
            self.logos['header_logo'] = header_logo
        if header_logo_file_id is not None:
            self.logos['header_logo_file_id'] = header_logo_file_id
        if header_logo_url is not None:
            self.logos['header_logo_url'] = header_logo_url
        self.update_timestamp()
    
    def get_sidebar_logo_url(self) -> Optional[str]:
        """Obtener URL del logo del sidebar (prioridad: URL > file_id > None)"""
        if self.logos.get('sidebar_icon_url'):
            return self.logos['sidebar_icon_url']
        if self.logos.get('sidebar_icon_file_id'):
            return f"/api/files/{self.logos['sidebar_icon_file_id']}"
        return None
    
    def get_header_logo_url(self) -> Optional[str]:
        """Obtener URL del logo del header (prioridad: URL > file_id > None)"""
        if self.logos.get('header_logo_url'):
            return self.logos['header_logo_url']
        if self.logos.get('header_logo_file_id'):
            return f"/api/files/{self.logos['header_logo_file_id']}"
        return None
    
    def get_sidebar_logo_fallback(self) -> str:
        """Obtener emoji/texto de fallback para sidebar"""
        return self.logos.get('sidebar_icon', '🏠')
    
    def get_header_logo_fallback(self) -> str:
        """Obtener emoji/texto de fallback para header"""
        return self.logos.get('header_logo', '')

    def update_branding(self, module_title: Optional[str] = None, module_description: Optional[str] = None, dashboard_welcome: Optional[str] = None):
        """Actualizar textos de branding"""
        if module_title:
            self.branding['module_title'] = module_title
        if module_description:
            self.branding['module_description'] = module_description
        if dashboard_welcome:
            self.branding['dashboard_welcome'] = dashboard_welcome
        self.update_timestamp()

    def to_dict(self) -> dict:
        """Convertir a diccionario para serialización"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'colors': self.colors,
            'logos': self.logos,
            'branding': self.branding,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TechoPropioThemeConfig':
        """Crear instancia desde diccionario"""
        config = cls(
            user_id=data['user_id'],
            colors=data['colors'],
            logos=data['logos'],
            branding=data['branding'],
            id=data.get('id')
        )
        if 'created_at' in data:
            config.created_at = data['created_at']
        if 'updated_at' in data:
            config.updated_at = data['updated_at']
        return config
