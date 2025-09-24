"""
Dependencias de autorización para endpoints de FastAPI
Enfoque simplificado que evita importaciones circulares
"""
from fastapi import HTTPException, Depends, status
from typing import Callable
from ..entities.auth_models import User
from .permissions import has_permission


def verify_active_user():
    """Factory que crea una dependencia para verificar usuario activo"""
    from ...infrastructure.web.fastapi.auth_dependencies import get_current_user
    return Depends(get_current_user)


def verify_permission(permission: str):
    """Factory que crea una dependencia para verificar permisos específicos"""
    from ...infrastructure.web.fastapi.auth_dependencies import get_current_user
    
    def check_permission(current_user: User = Depends(get_current_user)):
        user_permissions = current_user.role.get("permissions", []) if current_user.role else []
        
        if not has_permission(user_permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para realizar esta acción. Permiso requerido: {permission}"
            )
        return current_user
    
    return check_permission


def verify_role(role_name: str):
    """Factory que crea una dependencia para verificar roles específicos"""
    from ...infrastructure.web.fastapi.auth_dependencies import get_current_user
    
    def check_role(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.get("name") if current_user.role else None
        
        if user_role != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Rol requerido: {role_name}"
            )
        return current_user
    
    return check_role


# Mantenemos aliases para compatibilidad con código existente
requires_active_user = verify_active_user
requires_permission = verify_permission  
requires_role = verify_role