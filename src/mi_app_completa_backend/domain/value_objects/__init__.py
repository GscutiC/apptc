"""
Value Objects del dominio
"""
from .permissions import SystemPermissions, DefaultRoles, Permission, has_permission, has_any_permission, has_all_permissions
from .exceptions import AuthorizationError, InsufficientPermissionsError, InvalidRoleError, RoleNotFoundError, PermissionNotFoundError

__all__ = [
    'SystemPermissions',
    'DefaultRoles', 
    'Permission',
    'has_permission',
    'has_any_permission',
    'has_all_permissions',
    'AuthorizationError',
    'InsufficientPermissionsError',
    'InvalidRoleError',
    'RoleNotFoundError',
    'PermissionNotFoundError'
]