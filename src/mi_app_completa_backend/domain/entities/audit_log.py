"""
Entidad para auditoría de acciones del sistema
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
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

class AuditLog(BaseModel):
    """Modelo para logs de auditoría del sistema"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: Optional[str] = Field(None, description="ID del usuario que realizó la acción")
    clerk_id: Optional[str] = Field(None, description="ID de Clerk del usuario")
    user_email: Optional[str] = Field(None, description="Email del usuario")
    action: str = Field(..., description="Acción realizada")
    resource_type: str = Field(..., description="Tipo de recurso afectado")
    resource_id: Optional[str] = Field(None, description="ID del recurso afectado")
    old_values: Optional[Dict[str, Any]] = Field(None, description="Valores anteriores")
    new_values: Optional[Dict[str, Any]] = Field(None, description="Valores nuevos")
    ip_address: Optional[str] = Field(None, description="Dirección IP del usuario")
    user_agent: Optional[str] = Field(None, description="User Agent del navegador")
    success: bool = Field(default=True, description="Si la acción fue exitosa")
    error_message: Optional[str] = Field(None, description="Mensaje de error si falló")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "user_id": self.user_id,
            "clerk_id": self.clerk_id,
            "user_email": self.user_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }

class AuditLogCreate(BaseModel):
    """Modelo para crear logs de auditoría"""
    user_id: Optional[str] = None
    clerk_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

class AuditLogFilter(BaseModel):
    """Filtros para búsqueda de logs de auditoría"""
    user_id: Optional[str] = None
    clerk_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    skip: int = Field(default=0, ge=0)

# Constantes para acciones de auditoría
class AuditActions:
    """Constantes para acciones auditables"""
    
    # Acciones de usuarios
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_ROLE_CHANGED = "user.role_changed"
    
    # Acciones de roles
    ROLE_CREATED = "role.created"
    ROLE_UPDATED = "role.updated"
    ROLE_DELETED = "role.deleted"
    ROLE_ASSIGNED = "role.assigned"
    ROLE_UNASSIGNED = "role.unassigned"
    
    # Acciones de permisos
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    
    # Acciones administrativas
    SYSTEM_SETTINGS_CHANGED = "system.settings_changed"
    DEFAULT_ROLES_INITIALIZED = "system.default_roles_initialized"
    
    # Acciones de seguridad
    UNAUTHORIZED_ACCESS_ATTEMPT = "security.unauthorized_access"
    PERMISSION_DENIED = "security.permission_denied"
    
    @classmethod
    def get_all_actions(cls) -> list:
        """Obtener todas las acciones auditables"""
        return [
            cls.USER_CREATED, cls.USER_UPDATED, cls.USER_DELETED,
            cls.USER_LOGIN, cls.USER_LOGOUT, cls.USER_ROLE_CHANGED,
            cls.ROLE_CREATED, cls.ROLE_UPDATED, cls.ROLE_DELETED,
            cls.ROLE_ASSIGNED, cls.ROLE_UNASSIGNED,
            cls.PERMISSION_GRANTED, cls.PERMISSION_REVOKED,
            cls.SYSTEM_SETTINGS_CHANGED, cls.DEFAULT_ROLES_INITIALIZED,
            cls.UNAUTHORIZED_ACCESS_ATTEMPT, cls.PERMISSION_DENIED
        ]

# Constantes para tipos de recursos
class ResourceTypes:
    """Constantes para tipos de recursos auditables"""
    USER = "user"
    ROLE = "role"
    PERMISSION = "permission"
    SYSTEM = "system"
    AUTH = "auth"