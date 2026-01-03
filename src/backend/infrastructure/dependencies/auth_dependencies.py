"""
Dependencias de autenticación para Techo Propio
Integra con el sistema de autenticación existente
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# TODO: Importar desde el sistema de autenticación existente
# from ...auth.auth_service import verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Obtener usuario actual desde token de autenticación
    
    Returns:
        Dict con información del usuario: user_id, email, role, etc.
    """
    try:
        token = credentials.credentials
        
        # TODO: Implementar verificación real del token
        # user_data = await verify_token(token)
        
        # Por ahora, retornar datos de prueba
        # En producción, esto debe venir del sistema de autenticación
        user_data = {
            "user_id": "test_user_123",
            "email": "test@example.com",
            "role": "user",
            "permissions": ["techo_propio:read", "techo_propio:write"]
        }
        
        return user_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verificar que el usuario actual tiene permisos administrativos
    
    Returns:
        Dict con información del usuario administrador
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos administrativos"
        )
    
    return current_user


def require_permission(permission: str):
    """
    Decorator para requerir permisos específicos
    
    Args:
        permission: Permiso requerido (ej: "techo_propio:write")
    """
    def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_permissions = current_user.get("permissions", [])
        
        if permission not in user_permissions and current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere el permiso: {permission}"
            )
        
        return current_user
    
    return permission_checker


# Dependencias específicas para operaciones de Techo Propio
require_techo_propio_read = require_permission("techo_propio:read")
require_techo_propio_write = require_permission("techo_propio:write")
require_techo_propio_admin = require_permission("techo_propio:admin")