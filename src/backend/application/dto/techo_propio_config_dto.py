"""
DTOs para la configuración visual del módulo Techo Propio
Define la estructura de datos para entrada/salida de la API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re


class ColorsDTO(BaseModel):
    """Esquema de colores del módulo"""
    primary: str = Field(..., description="Color primario (hex)", pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary: str = Field(..., description="Color secundario (hex)", pattern=r'^#[0-9A-Fa-f]{6}$')
    accent: str = Field(..., description="Color de acento (hex)", pattern=r'^#[0-9A-Fa-f]{6}$')

    @field_validator('primary', 'secondary', 'accent')
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        """Validar que sea un color hexadecimal válido"""
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError(f'Debe ser un color hexadecimal válido (ej: #16a34a), recibido: {v}')
        return v.upper()  # Normalizar a mayúsculas


class LogosDTO(BaseModel):
    """Logos del módulo - Soporta emojis/texto Y archivos subidos"""
    
    # Sidebar (siempre presente como fallback)
    sidebar_icon: str = Field(
        default="🏠", 
        description="Ícono del sidebar (emoji o texto como fallback)", 
        min_length=1
    )
    sidebar_icon_file_id: Optional[str] = Field(
        None, 
        description="ID del archivo de logo subido para sidebar"
    )
    sidebar_icon_url: Optional[str] = Field(
        None, 
        description="URL del logo del sidebar (generada automáticamente)"
    )
    
    # Header (opcional)
    header_logo: Optional[str] = Field(
        None, 
        description="Logo del header (emoji o texto como fallback)"
    )
    header_logo_file_id: Optional[str] = Field(
        None, 
        description="ID del archivo de logo subido para header"
    )
    header_logo_url: Optional[str] = Field(
        None, 
        description="URL del logo del header (generada automáticamente)"
    )

    @field_validator('sidebar_icon')
    @classmethod
    def validate_sidebar_icon(cls, v: str) -> str:
        """Validar que el ícono no esté vacío"""
        if not v or not v.strip():
            raise ValueError('El ícono del sidebar no puede estar vacío')
        return v.strip()
    
    @field_validator('sidebar_icon_url', 'header_logo_url')
    @classmethod
    def generate_url_from_file_id(cls, v: Optional[str], info) -> Optional[str]:
        """Generar URL automáticamente si hay file_id pero no URL"""
        if v:
            return v
        
        # Determinar cuál file_id usar
        field_name = info.field_name
        if field_name == 'sidebar_icon_url' and info.data.get('sidebar_icon_file_id'):
            return f"/api/files/{info.data['sidebar_icon_file_id']}"
        elif field_name == 'header_logo_url' and info.data.get('header_logo_file_id'):
            return f"/api/files/{info.data['header_logo_file_id']}"
        
        return None


class BrandingDTO(BaseModel):
    """Textos de branding del módulo"""
    module_title: str = Field(..., description="Título del módulo", min_length=3, max_length=50)
    module_description: str = Field(..., description="Descripción del módulo", min_length=5, max_length=200)
    dashboard_welcome: str = Field(..., description="Mensaje de bienvenida", min_length=5, max_length=100)

    @field_validator('module_title', 'module_description', 'dashboard_welcome')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validar que los textos no estén vacíos"""
        if not v or not v.strip():
            raise ValueError('Este campo no puede estar vacío')
        return v.strip()


class TechoPropioConfigCreateDTO(BaseModel):
    """DTO para crear/actualizar configuración"""
    colors: ColorsDTO
    logos: LogosDTO
    branding: BrandingDTO

    class Config:
        json_schema_extra = {
            "example": {
                "colors": {
                    "primary": "#16A34A",
                    "secondary": "#2563EB",
                    "accent": "#DC2626"
                },
                "logos": {
                    "sidebar_icon": "🏠",
                    "sidebar_icon_file_id": None,
                    "sidebar_icon_url": None,
                    "header_logo": None,
                    "header_logo_file_id": None,
                    "header_logo_url": None
                },
                "branding": {
                    "module_title": "Techo Propio",
                    "module_description": "Gestión de Solicitudes",
                    "dashboard_welcome": "Bienvenido al sistema"
                }
            }
        }


class TechoPropioConfigResponseDTO(BaseModel):
    """DTO para respuesta de configuración"""
    id: Optional[str] = None
    user_id: str
    colors: ColorsDTO
    logos: LogosDTO
    branding: BrandingDTO
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "67abc123def456...",
                "user_id": "user_abc123",
                "colors": {
                    "primary": "#16A34A",
                    "secondary": "#2563EB",
                    "accent": "#DC2626"
                },
                "logos": {
                    "sidebar_icon": "🏠",
                    "header_logo": None
                },
                "branding": {
                    "module_title": "Techo Propio",
                    "module_description": "Gestión de Solicitudes",
                    "dashboard_welcome": "Bienvenido Juan Pérez"
                },
                "created_at": "2025-10-13T10:00:00Z",
                "updated_at": "2025-10-13T10:00:00Z"
            }
        }


class TechoPropioConfigUpdateDTO(BaseModel):
    """DTO para actualización parcial de configuración"""
    colors: Optional[ColorsDTO] = None
    logos: Optional[LogosDTO] = None
    branding: Optional[BrandingDTO] = None

    class Config:
        json_schema_extra = {
            "example": {
                "colors": {
                    "primary": "#16A34A",
                    "secondary": "#2563EB",
                    "accent": "#DC2626"
                }
            }
        }
