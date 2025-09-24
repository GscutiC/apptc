"""
Decoradores para autorización y control de acceso
"""
from functools import wraps
from typing import List, Union, Callable, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..value_objects.permissions import has_permission, has_any_permission, has_all_permissions
from ..value_objects.exceptions import InsufficientPermissionsError, InvalidRoleError
from ...domain.entities.auth_models import UserWithRole

security = HTTPBearer()

def requires_permission(
    permission: str, 
    allow_super_admin: bool = True
) -> Callable:
    """
    Decorador que requiere un permiso específico para acceder al endpoint
    
    Args:
        permission: Permiso requerido (ej: "users.create")
        allow_super_admin: Si True, permite acceso automático a super_admin
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar el parámetro current_user en los kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserWithRole):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            # Obtener permisos del usuario
            user_permissions = []
            if current_user.role and current_user.role.get("permissions"):
                user_permissions = current_user.role["permissions"]
            
            # Verificar si es super_admin (acceso total)
            if allow_super_admin and current_user.role and current_user.role.get("name") == "super_admin":
                return await func(*args, **kwargs)
            
            # Verificar permiso específico
            if not has_permission(user_permissions, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required. Current permissions: {', '.join(user_permissions) if user_permissions else 'none'}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def requires_any_permission(
    permissions: List[str], 
    allow_super_admin: bool = True
) -> Callable:
    """
    Decorador que requiere al menos uno de los permisos especificados
    
    Args:
        permissions: Lista de permisos (el usuario necesita al menos uno)
        allow_super_admin: Si True, permite acceso automático a super_admin
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar el parámetro current_user en los kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserWithRole):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            # Obtener permisos del usuario
            user_permissions = []
            if current_user.role and current_user.role.get("permissions"):
                user_permissions = current_user.role["permissions"]
            
            # Verificar si es super_admin (acceso total)
            if allow_super_admin and current_user.role and current_user.role.get("name") == "super_admin":
                return await func(*args, **kwargs)
            
            # Verificar si tiene al menos uno de los permisos
            if not has_any_permission(user_permissions, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permissions)}. Current permissions: {', '.join(user_permissions) if user_permissions else 'none'}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def requires_all_permissions(
    permissions: List[str], 
    allow_super_admin: bool = True
) -> Callable:
    """
    Decorador que requiere todos los permisos especificados
    
    Args:
        permissions: Lista de permisos (el usuario necesita todos)
        allow_super_admin: Si True, permite acceso automático a super_admin
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar el parámetro current_user en los kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserWithRole):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            # Obtener permisos del usuario
            user_permissions = []
            if current_user.role and current_user.role.get("permissions"):
                user_permissions = current_user.role["permissions"]
            
            # Verificar si es super_admin (acceso total)
            if allow_super_admin and current_user.role and current_user.role.get("name") == "super_admin":
                return await func(*args, **kwargs)
            
            # Verificar si tiene todos los permisos
            if not has_all_permissions(user_permissions, permissions):
                missing_permissions = [p for p in permissions if not has_permission(user_permissions, p)]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(missing_permissions)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def requires_role(
    *roles: str,
    allow_super_admin: bool = True
) -> Callable:
    """
    Decorador que requiere uno de los roles especificados
    
    Args:
        roles: Roles permitidos (ej: "admin", "moderator")
        allow_super_admin: Si True, permite acceso automático a super_admin
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar el parámetro current_user en los kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserWithRole):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            user_role = current_user.role.get("name") if current_user.role else None
            
            # Verificar si es super_admin (acceso total)
            if allow_super_admin and user_role == "super_admin":
                return await func(*args, **kwargs)
            
            # Verificar si tiene uno de los roles requeridos
            if user_role not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {', '.join(roles)}. Current role: {user_role or 'none'}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def requires_active_user() -> Callable:
    """
    Decorador que requiere que el usuario esté activo
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Buscar el parámetro current_user en los kwargs
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserWithRole):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User authentication required"
                )
            
            if not current_user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is deactivated"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Decorador compuesto para casos comunes
def admin_required() -> Callable:
    """Decorador de conveniencia para endpoints que requieren admin o super_admin"""
    return requires_role("admin", "super_admin")

def super_admin_required() -> Callable:
    """Decorador de conveniencia para endpoints que requieren solo super_admin"""
    return requires_role("super_admin", allow_super_admin=False)

def user_management_required() -> Callable:
    """Decorador de conveniencia para gestión de usuarios"""
    return requires_any_permission(["users.create", "users.update", "users.delete"])

def role_management_required() -> Callable:
    """Decorador de conveniencia para gestión de roles"""
    return requires_any_permission(["roles.create", "roles.update", "roles.delete"])