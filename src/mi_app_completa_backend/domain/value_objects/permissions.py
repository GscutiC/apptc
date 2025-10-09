"""
Sistema de permisos granulares para la aplicación
"""
from enum import Enum
from typing import List, Set, Dict
from dataclasses import dataclass

class PermissionCategory(Enum):
    """Categorías de permisos del sistema"""
    USERS = "users"
    ROLES = "roles" 
    MESSAGES = "messages"
    AI = "ai"
    ADMIN = "admin"
    AUDIT = "audit"
    MODULES = "modules"

class PermissionAction(Enum):
    """Acciones disponibles para permisos"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    ASSIGN = "assign"
    PROCESS = "process"
    VIEW_LOGS = "view_logs"
    MANAGE_SETTINGS = "manage_settings"
    TECHO_PROPIO = "techo_propio"

@dataclass
class Permission:
    """Clase que representa un permiso específico"""
    category: PermissionCategory
    action: PermissionAction
    description: str
    
    def __str__(self) -> str:
        return f"{self.category.value}.{self.action.value}"
    
    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return str(self) == other
        return isinstance(other, Permission) and str(self) == str(other)
    
    def __hash__(self) -> int:
        return hash(str(self))

class SystemPermissions:
    """Definición de todos los permisos del sistema"""
    
    # Permisos de usuarios
    USERS_CREATE = Permission(PermissionCategory.USERS, PermissionAction.CREATE, "Crear nuevos usuarios")
    USERS_READ = Permission(PermissionCategory.USERS, PermissionAction.READ, "Ver información de usuarios")
    USERS_UPDATE = Permission(PermissionCategory.USERS, PermissionAction.UPDATE, "Editar información de usuarios")
    USERS_DELETE = Permission(PermissionCategory.USERS, PermissionAction.DELETE, "Eliminar usuarios")
    USERS_LIST = Permission(PermissionCategory.USERS, PermissionAction.LIST, "Listar todos los usuarios")
    
    # Permisos de roles
    ROLES_CREATE = Permission(PermissionCategory.ROLES, PermissionAction.CREATE, "Crear nuevos roles")
    ROLES_READ = Permission(PermissionCategory.ROLES, PermissionAction.READ, "Ver información de roles")
    ROLES_UPDATE = Permission(PermissionCategory.ROLES, PermissionAction.UPDATE, "Editar roles existentes")
    ROLES_DELETE = Permission(PermissionCategory.ROLES, PermissionAction.DELETE, "Eliminar roles")
    ROLES_LIST = Permission(PermissionCategory.ROLES, PermissionAction.LIST, "Listar todos los roles")
    ROLES_ASSIGN = Permission(PermissionCategory.ROLES, PermissionAction.ASSIGN, "Asignar roles a usuarios")
    
    # Permisos de mensajes
    MESSAGES_CREATE = Permission(PermissionCategory.MESSAGES, PermissionAction.CREATE, "Crear mensajes")
    MESSAGES_READ = Permission(PermissionCategory.MESSAGES, PermissionAction.READ, "Leer mensajes")
    MESSAGES_UPDATE = Permission(PermissionCategory.MESSAGES, PermissionAction.UPDATE, "Editar mensajes")
    MESSAGES_DELETE = Permission(PermissionCategory.MESSAGES, PermissionAction.DELETE, "Eliminar mensajes")
    MESSAGES_LIST = Permission(PermissionCategory.MESSAGES, PermissionAction.LIST, "Listar mensajes")
    
    # Permisos de IA
    AI_PROCESS = Permission(PermissionCategory.AI, PermissionAction.PROCESS, "Usar servicios de IA")
    
    # Permisos de auditoría
    AUDIT_VIEW_LOGS = Permission(PermissionCategory.AUDIT, PermissionAction.VIEW_LOGS, "Ver logs de auditoría")
    
    # Permisos de administración
    ADMIN_MANAGE_SETTINGS = Permission(PermissionCategory.ADMIN, PermissionAction.MANAGE_SETTINGS, "Gestionar configuración del sistema")
    
    # Permisos de módulos
    MODULES_TECHO_PROPIO = Permission(PermissionCategory.MODULES, PermissionAction.TECHO_PROPIO, "Acceso al módulo Techo Propio")
    
    @classmethod
    def get_all_permissions(cls) -> List[Permission]:
        """Obtener lista de todos los permisos disponibles"""
        permissions = []
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Permission):
                permissions.append(attr)
        return permissions
    
    @classmethod
    def get_permissions_by_category(cls, category: PermissionCategory) -> List[Permission]:
        """Obtener permisos por categoría"""
        all_permissions = cls.get_all_permissions()
        return [p for p in all_permissions if p.category == category]
    
    @classmethod
    def get_permission_by_string(cls, permission_str: str) -> Permission:
        """Obtener permiso por su representación en string"""
        all_permissions = cls.get_all_permissions()
        for permission in all_permissions:
            if str(permission) == permission_str:
                return permission
        raise ValueError(f"Permission '{permission_str}' not found")
    
    @classmethod
    def validate_permissions(cls, permissions: List[str]) -> List[Permission]:
        """Validar que una lista de strings son permisos válidos"""
        validated_permissions = []
        for perm_str in permissions:
            if perm_str == "*":  # Permiso especial para super admin
                return cls.get_all_permissions()
            try:
                permission = cls.get_permission_by_string(perm_str)
                validated_permissions.append(permission)
            except ValueError:
                raise ValueError(f"Invalid permission: {perm_str}")
        return validated_permissions

class DefaultRoles:
    """Definición de roles por defecto del sistema"""
    
    USER_PERMISSIONS = [
        SystemPermissions.MESSAGES_CREATE,
        SystemPermissions.MESSAGES_READ,
        SystemPermissions.AI_PROCESS,
    ]
    
    MODERATOR_PERMISSIONS = [
        *USER_PERMISSIONS,
        SystemPermissions.MESSAGES_UPDATE,
        SystemPermissions.MESSAGES_DELETE,
        SystemPermissions.MESSAGES_LIST,
        SystemPermissions.USERS_READ,
    ]
    
    ADMIN_PERMISSIONS = [
        *MODERATOR_PERMISSIONS,
        SystemPermissions.USERS_CREATE,
        SystemPermissions.USERS_UPDATE,
        SystemPermissions.USERS_DELETE,
        SystemPermissions.USERS_LIST,
        SystemPermissions.ROLES_READ,
        SystemPermissions.ROLES_LIST,
        SystemPermissions.AUDIT_VIEW_LOGS,
    ]
    
    SUPER_ADMIN_PERMISSIONS = [
        *ADMIN_PERMISSIONS,
        SystemPermissions.ROLES_CREATE,
        SystemPermissions.ROLES_UPDATE,
        SystemPermissions.ROLES_DELETE,
        SystemPermissions.ROLES_ASSIGN,
        SystemPermissions.ADMIN_MANAGE_SETTINGS,
        SystemPermissions.MODULES_TECHO_PROPIO,
    ]
    
    ROLES_CONFIG = {
        "user": {
            "display_name": "Usuario Básico",
            "description": "Usuario con permisos básicos para usar la aplicación",
            "permissions": [str(p) for p in USER_PERMISSIONS],
            "is_default": True
        },
        "moderator": {
            "display_name": "Moderador",
            "description": "Usuario con permisos para moderar contenido y ver usuarios",
            "permissions": [str(p) for p in MODERATOR_PERMISSIONS],
            "is_default": False
        },
        "admin": {
            "display_name": "Administrador",
            "description": "Usuario con permisos administrativos completos excepto gestión de roles",
            "permissions": [str(p) for p in ADMIN_PERMISSIONS],
            "is_default": False
        },
        "super_admin": {
            "display_name": "Super Administrador",
            "description": "Usuario con todos los permisos del sistema",
            "permissions": [str(p) for p in SUPER_ADMIN_PERMISSIONS],
            "is_default": False
        }
    }

def has_permission(user_permissions: List[str], required_permission: str) -> bool:
    """Verificar si un usuario tiene un permiso específico"""
    if "*" in user_permissions:  # Super admin tiene todos los permisos
        return True
    
    # Verificar permiso exacto
    if required_permission in user_permissions:
        return True
    
    # Verificar permiso con wildcard (ej: "users.*" incluye "users.create")
    for user_perm in user_permissions:
        if user_perm.endswith(".*"):
            category = user_perm[:-2]  # Remover ".*"
            if required_permission.startswith(f"{category}."):
                return True
    
    return False

def has_any_permission(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """Verificar si un usuario tiene al menos uno de los permisos requeridos"""
    return any(has_permission(user_permissions, perm) for perm in required_permissions)

def has_all_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
    """Verificar si un usuario tiene todos los permisos requeridos"""
    return all(has_permission(user_permissions, perm) for perm in required_permissions)