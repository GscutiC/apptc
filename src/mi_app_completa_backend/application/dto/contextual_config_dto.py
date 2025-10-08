"""
DTOs para configuraciones contextuales
FASE 3: Sistema de Configuración Contextual
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, validator
from datetime import datetime
from .interface_config_dto import InterfaceConfigResponseDTO, InterfaceConfigCreateDTO


# Tipos de contexto permitidos
ContextType = Literal["user", "role", "org", "global"]


class ConfigContextDTO(BaseModel):
    """DTO para contexto de configuración"""
    context_type: ContextType
    context_id: Optional[str] = None

    @validator('context_id')
    def validate_context_id(cls, v, values):
        context_type = values.get('context_type')
        
        # Global no debe tener context_id
        if context_type == "global" and v is not None:
            raise ValueError("Global context must not have context_id")
        
        # Otros contextos deben tener context_id
        if context_type != "global" and not v:
            raise ValueError(f"{context_type} context must have context_id")
            
        return v

    class Config:
        schema_extra = {
            "example": {
                "context_type": "user",
                "context_id": "user_12345"
            }
        }


class ContextualConfigCreateDTO(BaseModel):
    """DTO para crear configuración contextual"""
    config: InterfaceConfigCreateDTO
    context: ConfigContextDTO
    is_active: bool = True

    class Config:
        schema_extra = {
            "example": {
                "config": {
                    "theme": {
                        "mode": "light",
                        "name": "Mi Tema Personal"
                        # ... resto de la configuración
                    }
                },
                "context": {
                    "context_type": "user",
                    "context_id": "user_12345"
                },
                "is_active": True
            }
        }


class ContextualConfigUpdateDTO(BaseModel):
    """DTO para actualizar configuración contextual"""
    config: Optional[InterfaceConfigCreateDTO] = None
    is_active: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "config": {
                    "theme": {
                        "mode": "dark",
                        "name": "Mi Tema Oscuro Actualizado"
                    }
                },
                "is_active": True
            }
        }


class ContextualConfigResponseDTO(BaseModel):
    """DTO para respuesta de configuración contextual"""
    id: str
    config: InterfaceConfigResponseDTO
    context: ConfigContextDTO
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "6507f1234567890123456789",
                "config": {
                    "id": "6507f1234567890123456788",
                    "theme": {
                        "mode": "light",
                        "name": "Tema Personal de Juan"
                        # ... resto de configuración
                    }
                },
                "context": {
                    "context_type": "user",
                    "context_id": "user_juan_12345"
                },
                "is_active": True,
                "created_by": "user_juan_12345",
                "created_at": "2025-10-07T10:00:00Z",
                "updated_at": "2025-10-07T10:00:00Z"
            }
        }


class EffectiveConfigRequestDTO(BaseModel):
    """DTO para solicitar configuración efectiva"""
    user_id: str
    user_role: Optional[str] = None
    org_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "user_role": "admin",
                "org_id": "org_corp123"
            }
        }


class EffectiveConfigResponseDTO(BaseModel):
    """DTO para respuesta de configuración efectiva"""
    config: InterfaceConfigResponseDTO
    resolved_from: ConfigContextDTO
    resolution_chain: List[ConfigContextDTO]

    class Config:
        schema_extra = {
            "example": {
                "config": {
                    # Configuración de interfaz resuelta
                },
                "resolved_from": {
                    "context_type": "user",
                    "context_id": "user_12345"
                },
                "resolution_chain": [
                    {"context_type": "user", "context_id": "user_12345"},
                    {"context_type": "role", "context_id": "admin"},
                    {"context_type": "org", "context_id": "org_corp123"},
                    {"context_type": "global", "context_id": None}
                ]
            }
        }


class ContextualConfigListDTO(BaseModel):
    """DTO para lista paginada de configuraciones contextuales"""
    configs: List[ContextualConfigResponseDTO]
    total: int
    page: int
    size: int
    has_next: bool
    has_prev: bool

    class Config:
        schema_extra = {
            "example": {
                "configs": [
                    # Lista de configuraciones
                ],
                "total": 25,
                "page": 1,
                "size": 10,
                "has_next": True,
                "has_prev": False
            }
        }


class ContextualConfigSearchDTO(BaseModel):
    """DTO para búsqueda de configuraciones contextuales"""
    context_type: Optional[ContextType] = None
    context_id: Optional[str] = None
    active_only: bool = True
    created_by: Optional[str] = None
    page: int = 1
    size: int = 10

    @validator('size')
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError('Page size cannot exceed 100')
        return v

    class Config:
        schema_extra = {
            "example": {
                "context_type": "user",
                "active_only": True,
                "page": 1,
                "size": 10
            }
        }


class UserPreferencesDTO(BaseModel):
    """DTO simplificado para preferencias de usuario"""
    user_id: str
    theme_mode: Optional[Literal["light", "dark"]] = None
    primary_color: Optional[str] = None
    font_size: Optional[Literal["sm", "base", "lg"]] = None
    compact_mode: Optional[bool] = None

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user_12345",
                "theme_mode": "dark",
                "primary_color": "#3b82f6",
                "font_size": "base",
                "compact_mode": False
            }
        }


class BulkContextualConfigDTO(BaseModel):
    """DTO para operaciones masivas con configuraciones contextuales"""
    action: Literal["activate", "deactivate", "delete"]
    config_ids: List[str]
    
    @validator('config_ids')
    def validate_config_ids(cls, v):
        if len(v) == 0:
            raise ValueError("At least one config_id is required")
        if len(v) > 50:
            raise ValueError("Cannot process more than 50 configs at once")
        return v

    class Config:
        schema_extra = {
            "example": {
                "action": "deactivate",
                "config_ids": [
                    "6507f1234567890123456789",
                    "6507f1234567890123456790"
                ]
            }
        }