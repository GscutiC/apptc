"""
DTOs para el módulo de configuración de interfaz
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from datetime import datetime


class ColorConfigDTO(BaseModel):
    """DTO para configuración de colores"""
    primary: Dict[str, str]
    secondary: Dict[str, str]
    accent: Dict[str, str]
    neutral: Dict[str, str]

    @validator('primary', 'secondary', 'accent', 'neutral')
    def validate_color_shades(cls, v):
        required_shades = ['50', '100', '200', '300', '400', '500', '600', '700', '800', '900']
        for shade in required_shades:
            if shade not in v:
                raise ValueError(f'Missing color shade: {shade}')
        return v


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