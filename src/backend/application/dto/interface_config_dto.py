"""
DTOs para el módulo de configuración de interfaz
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from datetime import datetime


def complete_color_shades(color_dict: Dict[str, str]) -> Dict[str, str]:
    """
    Completa los tonos de color faltantes interpolando o usando valores por defecto.
    Esto permite que configuraciones guardadas con menos tonos sigan funcionando.
    """
    # Colores base por defecto (gris neutro)
    default_shades = {
        '50': '#f9fafb', '100': '#f3f4f6', '200': '#e5e7eb',
        '300': '#d1d5db', '400': '#9ca3af', '500': '#6b7280',
        '600': '#4b5563', '700': '#374151', '800': '#1f2937', '900': '#111827'
    }
    
    required_shades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900']
    completed = {}
    
    # Encontrar el color base (preferiblemente 500)
    base_color = color_dict.get('500', color_dict.get('600', color_dict.get('700', '#6b7280')))
    
    for shade in required_shades:
        if shade in color_dict:
            completed[shade] = color_dict[shade]
        else:
            # Usar el default o intentar derivar del color base
            completed[shade] = default_shades.get(shade, base_color)
    
    return completed


class ColorConfigDTO(BaseModel):
    """DTO para configuración de colores"""
    primary: Dict[str, str]
    secondary: Dict[str, str]
    accent: Dict[str, str]
    neutral: Dict[str, str]

    @validator('primary', 'secondary', 'accent', 'neutral', pre=True)
    def validate_and_complete_color_shades(cls, v):
        """Valida y completa los tonos de color faltantes"""
        if not isinstance(v, dict):
            raise ValueError('Color config must be a dictionary')
        
        # Completar tonos faltantes automáticamente
        return complete_color_shades(v)


class TypographyConfigDTO(BaseModel):
    """DTO para configuración de tipografía"""
    fontFamily: Dict[str, str]
    fontSize: Dict[str, str]
    fontWeight: Dict[str, int]


class LayoutConfigDTO(BaseModel):
    """DTO para configuración de layout"""
    borderRadius: Dict[str, str]
    spacing: Dict[str, str]
    shadows: Dict[str, str]


class LogoConfigDTO(BaseModel):
    """DTO para configuración de logos"""
    mainLogo: Dict[str, Any]
    favicon: Dict[str, Any]
    sidebarLogo: Dict[str, Any]


class BrandingConfigDTO(BaseModel):
    """DTO para configuración de branding"""
    appName: str
    appDescription: str
    tagline: Optional[str] = None
    companyName: Optional[str] = None
    welcomeMessage: str
    loginPageTitle: str = ""
    loginPageDescription: str = ""
    footerText: Optional[str] = None
    supportEmail: Optional[str] = None

    @validator('appName', 'appDescription', 'welcomeMessage')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class ThemeConfigDTO(BaseModel):
    """DTO para configuración de tema"""
    mode: str
    name: str
    colors: ColorConfigDTO
    typography: TypographyConfigDTO
    layout: LayoutConfigDTO

    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['light', 'dark']:
            raise ValueError('Mode must be either "light" or "dark"')
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Theme name cannot be empty')
        return v.strip()


class InterfaceConfigCreateDTO(BaseModel):
    """DTO para crear configuración de interfaz"""
    theme: ThemeConfigDTO
    logos: LogoConfigDTO
    branding: BrandingConfigDTO
    customCSS: Optional[str] = None
    isActive: bool = True


class InterfaceConfigUpdateDTO(BaseModel):
    """DTO para actualizar configuración de interfaz"""
    theme: Optional[ThemeConfigDTO] = None
    logos: Optional[LogoConfigDTO] = None
    branding: Optional[BrandingConfigDTO] = None
    customCSS: Optional[str] = None
    isActive: Optional[bool] = None


class InterfaceConfigResponseDTO(BaseModel):
    """DTO para respuesta de configuración de interfaz"""
    id: str
    theme: ThemeConfigDTO
    logos: LogoConfigDTO
    branding: BrandingConfigDTO
    customCSS: Optional[str] = None
    isActive: bool
    createdAt: datetime
    updatedAt: datetime
    createdBy: Optional[str] = None

    class Config:
        from_attributes = True


class PresetConfigCreateDTO(BaseModel):
    """DTO para crear preset de configuración"""
    name: str
    description: str
    config: InterfaceConfigCreateDTO
    isDefault: bool = False
    isSystem: bool = False

    @validator('name', 'description')
    def validate_required_strings(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()


class PresetConfigResponseDTO(BaseModel):
    """DTO para respuesta de preset de configuración"""
    id: str
    name: str
    description: str
    config: InterfaceConfigResponseDTO
    isDefault: bool
    isSystem: bool
    createdAt: datetime
    updatedAt: datetime
    createdBy: Optional[str] = None

    class Config:
        from_attributes = True


class ConfigHistoryResponseDTO(BaseModel):
    """DTO para historial de configuraciones"""
    id: str
    config: InterfaceConfigResponseDTO
    version: int
    changedBy: Optional[str] = None
    changeDescription: Optional[str] = None
    createdAt: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DTOs ESPECÍFICOS PARA ACTUALIZACIONES PARCIALES DE TEMA
# Permiten validación fuerte y merge inteligente de cambios
# ============================================================================

class ColorShadesUpdateDTO(BaseModel):
    """DTO para actualización parcial de tonos de color"""
    # Cada shade es opcional para permitir actualizaciones parciales
    shade_50: Optional[str] = None
    shade_100: Optional[str] = None
    shade_200: Optional[str] = None
    shade_300: Optional[str] = None
    shade_400: Optional[str] = None
    shade_500: Optional[str] = None
    shade_600: Optional[str] = None
    shade_700: Optional[str] = None
    shade_800: Optional[str] = None
    shade_900: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convertir a diccionario excluyendo valores None"""
        result = {}
        for field_name, field_value in self.model_dump().items():
            if field_value is not None:
                # Convertir shade_50 -> 50, shade_100 -> 100, etc.
                shade_key = field_name.replace('shade_', '')
                result[shade_key] = field_value
        return result


class ThemeColorUpdateDTO(BaseModel):
    """DTO para actualización parcial de colores del tema"""
    primary: Optional[Dict[str, str]] = None
    secondary: Optional[Dict[str, str]] = None
    accent: Optional[Dict[str, str]] = None
    neutral: Optional[Dict[str, str]] = None

    @validator('primary', 'secondary', 'accent', 'neutral')
    def validate_color_values(cls, v):
        """Validar que los colores sean códigos hex válidos"""
        if v is not None:
            for shade, color in v.items():
                if not color.startswith('#') or len(color) not in [4, 7]:
                    raise ValueError(f'Invalid color format: {color}. Must be hex color (e.g., #fff or #ffffff)')
        return v


class ThemeTypographyUpdateDTO(BaseModel):
    """DTO para actualización parcial de tipografía"""
    fontFamily: Optional[Dict[str, str]] = None
    fontSize: Optional[Dict[str, str]] = None
    fontWeight: Optional[Dict[str, int]] = None


class ThemeLayoutUpdateDTO(BaseModel):
    """DTO para actualización parcial de layout"""
    borderRadius: Optional[Dict[str, str]] = None
    spacing: Optional[Dict[str, str]] = None
    shadows: Optional[Dict[str, str]] = None


class ThemeUpdateDTO(BaseModel):
    """DTO para actualización parcial de tema completo"""
    mode: Optional[str] = None
    name: Optional[str] = None
    colors: Optional[ThemeColorUpdateDTO] = None
    typography: Optional[ThemeTypographyUpdateDTO] = None
    layout: Optional[ThemeLayoutUpdateDTO] = None

    @validator('mode')
    def validate_mode(cls, v):
        if v is not None and v not in ['light', 'dark']:
            raise ValueError('Mode must be either "light" or "dark"')
        return v


class LogoUpdateDTO(BaseModel):
    """DTO para actualización parcial de logos"""
    mainLogo: Optional[Dict[str, Any]] = None
    favicon: Optional[Dict[str, Any]] = None
    sidebarLogo: Optional[Dict[str, Any]] = None


class BrandingUpdateDTO(BaseModel):
    """DTO para actualización parcial de branding"""
    appName: Optional[str] = None
    appDescription: Optional[str] = None
    tagline: Optional[str] = None
    companyName: Optional[str] = None
    welcomeMessage: Optional[str] = None
    loginPageTitle: Optional[str] = None
    loginPageDescription: Optional[str] = None
    footerText: Optional[str] = None
    supportEmail: Optional[str] = None

    @validator('appName', 'appDescription', 'welcomeMessage')
    def validate_non_empty_strings(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Field cannot be empty')
        return v.strip() if v else v


class PartialInterfaceConfigUpdateDTO(BaseModel):
    """
    DTO para actualizaciones parciales con validación fuerte.
    Permite actualizar solo las propiedades especificadas.
    Soporta merge inteligente de cambios.
    """
    theme: Optional[ThemeUpdateDTO] = None
    logos: Optional[LogoUpdateDTO] = None
    branding: Optional[BrandingUpdateDTO] = None
    customCSS: Optional[str] = None
    isActive: Optional[bool] = None

    class Config:
        # Ejemplo de uso en la documentación (Pydantic V2)
        json_schema_extra = {
            "example": {
                "theme": {
                    "colors": {
                        "primary": {
                            "500": "#3b82f6",
                            "600": "#2563eb"
                        }
                    }
                },
                "branding": {
                    "appName": "Mi Aplicación"
                }
            }
        }