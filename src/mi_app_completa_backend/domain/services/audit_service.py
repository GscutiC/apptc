"""
Servicio de auditoría para registrar acciones del sistema
"""
from typing import Optional, Dict, Any
from fastapi import Request

from ...domain.entities.audit_log import AuditLogCreate, AuditActions, ResourceTypes
from ...domain.repositories.audit_repository import AuditLogRepository
from ...domain.entities.auth_models import UserWithRole

class AuditService:
    """Servicio para gestionar auditoría del sistema"""
    
    def __init__(self, audit_repository: AuditLogRepository):
        self.audit_repository = audit_repository
    
    async def log_action(
        self,
        action: str,
        resource_type: str,
        user: Optional[UserWithRole] = None,
        resource_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Registrar una acción en el log de auditoría
        
        Args:
            action: Acción realizada (usar constantes de AuditActions)
            resource_type: Tipo de recurso afectado (usar constantes de ResourceTypes)
            user: Usuario que realizó la acción
            resource_id: ID del recurso afectado
            old_values: Valores anteriores (para updates)
            new_values: Valores nuevos (para creates/updates)
            request: Request HTTP para obtener IP y User-Agent
            success: Si la acción fue exitosa
            error_message: Mensaje de error si falló
        """
        try:
            # Extraer información del usuario
            user_id = user.id if user else None
            clerk_id = user.clerk_id if user else None
            user_email = user.email if user else None
            
            # Extraer información de la request
            ip_address = None
            user_agent = None
            if request:
                # Obtener IP real considerando proxies
                ip_address = (
                    request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
                    request.headers.get("X-Real-IP") or
                    request.client.host if request.client else None
                )
                user_agent = request.headers.get("User-Agent")
            
            # Crear log de auditoría
            log_data = AuditLogCreate(
                user_id=user_id,
                clerk_id=clerk_id,
                user_email=user_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message
            )
            
            await self.audit_repository.create_log(log_data)
            
        except Exception as e:
            # No queremos que errores en auditoría afecten la funcionalidad principal
            print(f"Error logging audit action: {e}")
    
    # Métodos de conveniencia para acciones comunes
    
    async def log_user_created(
        self, 
        created_user_data: dict, 
        creator: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de creación de usuario"""
        await self.log_action(
            action=AuditActions.USER_CREATED,
            resource_type=ResourceTypes.USER,
            user=creator,
            resource_id=created_user_data.get("id"),
            new_values=created_user_data,
            request=request
        )
    
    async def log_user_updated(
        self,
        user_id: str,
        old_data: dict,
        new_data: dict,
        updater: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de actualización de usuario"""
        await self.log_action(
            action=AuditActions.USER_UPDATED,
            resource_type=ResourceTypes.USER,
            user=updater,
            resource_id=user_id,
            old_values=old_data,
            new_values=new_data,
            request=request
        )
    
    async def log_user_deleted(
        self,
        deleted_user_data: dict,
        deleter: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de eliminación de usuario"""
        await self.log_action(
            action=AuditActions.USER_DELETED,
            resource_type=ResourceTypes.USER,
            user=deleter,
            resource_id=deleted_user_data.get("id"),
            old_values=deleted_user_data,
            request=request
        )
    
    async def log_role_created(
        self,
        created_role_data: dict,
        creator: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de creación de rol"""
        await self.log_action(
            action=AuditActions.ROLE_CREATED,
            resource_type=ResourceTypes.ROLE,
            user=creator,
            resource_id=created_role_data.get("id"),
            new_values=created_role_data,
            request=request
        )
    
    async def log_role_updated(
        self,
        role_id: str,
        old_data: dict,
        new_data: dict,
        updater: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de actualización de rol"""
        await self.log_action(
            action=AuditActions.ROLE_UPDATED,
            resource_type=ResourceTypes.ROLE,
            user=updater,
            resource_id=role_id,
            old_values=old_data,
            new_values=new_data,
            request=request
        )
    
    async def log_role_deleted(
        self,
        deleted_role_data: dict,
        deleter: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de eliminación de rol"""
        await self.log_action(
            action=AuditActions.ROLE_DELETED,
            resource_type=ResourceTypes.ROLE,
            user=deleter,
            resource_id=deleted_role_data.get("id"),
            old_values=deleted_role_data,
            request=request
        )
    
    async def log_role_assigned(
        self,
        user_id: str,
        role_name: str,
        assigner: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de asignación de rol"""
        await self.log_action(
            action=AuditActions.ROLE_ASSIGNED,
            resource_type=ResourceTypes.USER,
            user=assigner,
            resource_id=user_id,
            new_values={"role_name": role_name},
            request=request
        )
    
    async def log_user_login(
        self,
        user: UserWithRole,
        request: Optional[Request] = None
    ):
        """Log de login de usuario"""
        await self.log_action(
            action=AuditActions.USER_LOGIN,
            resource_type=ResourceTypes.AUTH,
            user=user,
            resource_id=user.clerk_id,
            request=request
        )
    
    async def log_unauthorized_access(
        self,
        attempted_action: str,
        resource_type: str,
        user: Optional[UserWithRole] = None,
        request: Optional[Request] = None,
        error_message: Optional[str] = None
    ):
        """Log de intento de acceso no autorizado"""
        await self.log_action(
            action=AuditActions.UNAUTHORIZED_ACCESS_ATTEMPT,
            resource_type=resource_type,
            user=user,
            new_values={"attempted_action": attempted_action},
            request=request,
            success=False,
            error_message=error_message
        )
    
    async def log_permission_denied(
        self,
        required_permission: str,
        user: Optional[UserWithRole] = None,
        request: Optional[Request] = None
    ):
        """Log de permiso denegado"""
        user_permissions = []
        if user and user.role:
            user_permissions = user.role.get("permissions", [])
        
        await self.log_action(
            action=AuditActions.PERMISSION_DENIED,
            resource_type=ResourceTypes.AUTH,
            user=user,
            new_values={
                "required_permission": required_permission,
                "user_permissions": user_permissions
            },
            request=request,
            success=False,
            error_message=f"Permission '{required_permission}' required"
        )
    
    async def log_system_action(
        self,
        action: str,
        description: str,
        user: Optional[UserWithRole] = None,
        request: Optional[Request] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log de acción del sistema"""
        await self.log_action(
            action=action,
            resource_type=ResourceTypes.SYSTEM,
            user=user,
            new_values={
                "description": description,
                **(additional_data or {})
            },
            request=request
        )