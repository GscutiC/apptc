from datetime import datetime, timezone
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                str,
                return_schema=core_schema.str_schema(),
                when_used='json',
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class Role(BaseModel):
    """Modelo para roles del sistema con permisos granulares"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=50, description="Identificador único del rol")
    display_name: str = Field(..., min_length=1, max_length=100, description="Nombre visible del rol")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del rol")
    permissions: List[str] = Field(default_factory=list, description="Lista de permisos del rol")
    is_active: bool = Field(default=True, description="Si el rol está activo")
    is_system_role: bool = Field(default=False, description="Si es un rol del sistema (no se puede eliminar)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('name')
    @classmethod
    def validate_role_name(cls, v):
        """Validar que el nombre del rol sea válido"""
        if not v or not v.strip():
            raise ValueError("Role name cannot be empty")
        
        # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
        import re
        if not re.match(r'^[a-z0-9_-]+$', v.lower()):
            raise ValueError("Role name can only contain lowercase letters, numbers, hyphens and underscores")
        
        return v.lower().strip()
    
    @field_validator('permissions')
    @classmethod
    def validate_permissions(cls, v):
        """Validar que los permisos sean válidos"""
        if not isinstance(v, list):
            raise ValueError("Permissions must be a list")
        
        # Importar aquí para evitar imports circulares
        from ..value_objects.permissions import SystemPermissions
        
        # Validar cada permiso
        valid_permissions = [str(p) for p in SystemPermissions.get_all_permissions()]
        valid_permissions.append("*")  # Permiso especial para super admin
        
        for permission in v:
            if permission not in valid_permissions and not permission.endswith(".*"):
                raise ValueError(f"Invalid permission: {permission}")
        
        return list(set(v))  # Eliminar duplicados
    
    def has_permission(self, permission: str) -> bool:
        """Verificar si el rol tiene un permiso específico"""
        from ..value_objects.permissions import has_permission
        return has_permission(self.permissions, permission)
    
    def add_permission(self, permission: str) -> None:
        """Agregar un permiso al rol"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_permission(self, permission: str) -> None:
        """Remover un permiso del rol"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.now(timezone.utc)
    
    def get_permission_count(self) -> int:
        """Obtener número de permisos"""
        return len(self.permissions)
    
    def is_super_admin(self) -> bool:
        """Verificar si es el rol de super administrador"""
        return "*" in self.permissions or self.name == "super_admin"

class RoleCreate(BaseModel):
    """Modelo para crear nuevos roles"""
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    
    @field_validator('name')
    @classmethod
    def validate_role_name(cls, v):
        """Validar que el nombre del rol sea válido"""
        if not v or not v.strip():
            raise ValueError("Role name cannot be empty")
        
        import re
        if not re.match(r'^[a-z0-9_-]+$', v.lower()):
            raise ValueError("Role name can only contain lowercase letters, numbers, hyphens and underscores")
        
        return v.lower().strip()

class RoleUpdate(BaseModel):
    """Modelo para actualizar roles existentes"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[List[str]] = Field(None)
    is_active: Optional[bool] = Field(None)

class RoleWithStats(BaseModel):
    """Modelo de rol con estadísticas"""
    id: str
    name: str
    display_name: str
    description: Optional[str]
    permissions: List[str]
    is_active: bool
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    user_count: int = Field(default=0, description="Número de usuarios con este rol")
    permission_count: int = Field(default=0, description="Número de permisos del rol")

class PermissionInfo(BaseModel):
    """Información de un permiso del sistema"""
    name: str = Field(..., description="Nombre del permiso (ej: users.create)")
    category: str = Field(..., description="Categoría del permiso")
    action: str = Field(..., description="Acción del permiso")
    description: str = Field(..., description="Descripción del permiso")

class User(BaseModel):
    """Modelo para usuarios sincronizados desde Clerk"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    clerk_id: str = Field(..., unique=True)  # ID de Clerk
    email: str = Field(...)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    full_name: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    role_id: Optional[PyObjectId] = Field(None)  # Referencia al rol
    role_name: str = Field(default="user")  # Nombre del rol para fácil acceso
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    """Modelo para crear usuarios desde webhooks de Clerk"""
    clerk_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    image_url: Optional[str] = None
    phone_number: Optional[str] = None

class UserUpdate(BaseModel):
    """Modelo para actualizar usuarios"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    image_url: Optional[str] = None
    phone_number: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserWithRole(BaseModel):
    """Modelo de usuario con información completa del rol"""
    id: str
    clerk_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    image_url: Optional[str]
    phone_number: Optional[str]
    role: Optional[dict] = None  # Información completa del rol
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}