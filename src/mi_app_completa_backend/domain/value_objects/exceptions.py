"""
Excepciones personalizadas para el sistema de autorización
"""

class AuthorizationError(Exception):
    """Excepción base para errores de autorización"""
    pass

class InsufficientPermissionsError(AuthorizationError):
    """Error cuando el usuario no tiene permisos suficientes"""
    
    def __init__(self, required_permission: str, user_permissions: list = None):
        self.required_permission = required_permission
        self.user_permissions = user_permissions or []
        super().__init__(
            f"Permission '{required_permission}' required. "
            f"User has: {', '.join(self.user_permissions) if self.user_permissions else 'no permissions'}"
        )

class InvalidRoleError(AuthorizationError):
    """Error cuando se especifica un rol inválido"""
    
    def __init__(self, role_name: str):
        self.role_name = role_name
        super().__init__(f"Invalid role: '{role_name}'")

class RoleNotFoundError(AuthorizationError):
    """Error cuando no se encuentra un rol"""
    
    def __init__(self, role_identifier: str):
        self.role_identifier = role_identifier
        super().__init__(f"Role not found: '{role_identifier}'")

class PermissionNotFoundError(AuthorizationError):
    """Error cuando no se encuentra un permiso"""
    
    def __init__(self, permission: str):
        self.permission = permission
        super().__init__(f"Permission not found: '{permission}'")