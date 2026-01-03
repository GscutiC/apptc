"""
Data Transfer Objects para gestión de roles
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RoleCreateDTO(BaseModel):
    """DTO para crear un nuevo rol"""
    name: str = Field(..., min_length=1, max_length=50, description="Nombre único del rol")
    display_name: str = Field(..., min_length=1, max_length=100, description="Nombre visible del rol")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del rol")
    permissions: List[str] = Field(default_factory=list, description="Lista de permisos del rol")
    is_active: bool = Field(default=True, description="Si el rol está activo")

class RoleUpdateDTO(BaseModel):
    """DTO para actualizar un rol existente"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre visible del rol")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del rol")
    permissions: Optional[List[str]] = Field(None, description="Lista de permisos del rol")
    is_active: Optional[bool] = Field(None, description="Si el rol está activo")

class RoleResponseDTO(BaseModel):
    """DTO de respuesta para roles"""
    id: str = Field(..., description="ID único del rol")
    name: str = Field(..., description="Nombre único del rol")
    display_name: str = Field(..., description="Nombre visible del rol")
    description: Optional[str] = Field(None, description="Descripción del rol")
    permissions: List[str] = Field(default_factory=list, description="Lista de permisos del rol")
    is_active: bool = Field(default=True, description="Si el rol está activo")
    is_system_role: bool = Field(default=False, description="Si es un rol del sistema")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

class RoleWithStatsDTO(RoleResponseDTO):
    """DTO de rol con estadísticas de uso"""
    user_count: int = Field(default=0, description="Número de usuarios con este rol")
    permission_count: int = Field(default=0, description="Número de permisos del rol")

class PermissionDTO(BaseModel):
    """DTO para información de permisos"""
    name: str = Field(..., description="Nombre del permiso (ej: users.create)")
    category: str = Field(..., description="Categoría del permiso")
    action: str = Field(..., description="Acción del permiso")
    description: str = Field(..., description="Descripción del permiso")

class PermissionCategoryDTO(BaseModel):
    """DTO para categorías de permisos"""
    name: str = Field(..., description="Nombre de la categoría")
    permissions: List[PermissionDTO] = Field(default_factory=list, description="Permisos de la categoría")

class RoleAssignmentDTO(BaseModel):
    """DTO para asignar rol a usuario"""
    clerk_id: str = Field(..., description="ID de Clerk del usuario")
    role_name: str = Field(..., description="Nombre del rol a asignar")

class UserRoleDTO(BaseModel):
    """DTO para mostrar información de rol de usuario"""
    user_id: str = Field(..., description="ID del usuario")
    clerk_id: str = Field(..., description="ID de Clerk del usuario")
    email: str = Field(..., description="Email del usuario")
    full_name: Optional[str] = Field(None, description="Nombre completo del usuario")
    current_role: Optional[str] = Field(None, description="Rol actual del usuario")
    role_display_name: Optional[str] = Field(None, description="Nombre visible del rol actual")
    permissions: List[str] = Field(default_factory=list, description="Permisos del usuario")
    is_active: bool = Field(default=True, description="Si el usuario está activo")