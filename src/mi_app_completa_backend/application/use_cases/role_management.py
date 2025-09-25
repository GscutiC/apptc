"""
Casos de uso para gestión avanzada de roles y permisos
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from ..dto.role_dto import RoleCreateDTO, RoleUpdateDTO, RoleResponseDTO, RoleWithStatsDTO
from ...domain.entities.auth_models import Role, RoleCreate, RoleUpdate, RoleWithStats
from ...domain.repositories.auth_repository import RoleRepository, UserRepository
from ...domain.value_objects.permissions import SystemPermissions, DefaultRoles
from ...domain.value_objects.exceptions import RoleNotFoundError, InvalidRoleError

class CreateRoleUseCase:
    """Caso de uso para crear nuevos roles"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    async def execute(self, role_data: RoleCreateDTO) -> RoleResponseDTO:
        """Crear un nuevo rol"""
        
        # Verificar que el rol no exista
        existing_role = await self.role_repository.get_role_by_name(role_data.name)
        if existing_role:
            raise InvalidRoleError(f"Role '{role_data.name}' already exists")
        
        # Validar permisos
        if role_data.permissions:
            SystemPermissions.validate_permissions(role_data.permissions)
        
        # Crear entidad de rol
        role_create = RoleCreate(
            name=role_data.name,
            display_name=role_data.display_name,
            description=role_data.description,
            permissions=role_data.permissions or [],
            is_active=role_data.is_active
        )
        
        # Guardar rol
        created_role = await self.role_repository.create_role(Role(**role_create.dict()))
        
        return RoleResponseDTO(
            id=str(created_role.id),
            name=created_role.name,
            display_name=created_role.display_name,
            description=created_role.description,
            permissions=created_role.permissions,
            is_active=created_role.is_active,
            is_system_role=created_role.is_system_role,
            created_at=created_role.created_at,
            updated_at=created_role.updated_at
        )

class UpdateRoleUseCase:
    """Caso de uso para actualizar roles existentes"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    async def execute(self, role_id: str, role_data: RoleUpdateDTO) -> RoleResponseDTO:
        """Actualizar un rol existente"""
        
        # Verificar que el rol existe
        existing_role = await self.role_repository.get_role_by_id(role_id)
        if not existing_role:
            raise RoleNotFoundError(role_id)
        
        # No permitir editar roles del sistema
        if existing_role.is_system_role:
            raise InvalidRoleError(f"System role '{existing_role.name}' cannot be modified")
        
        # Validar permisos si se proporcionan
        if role_data.permissions is not None:
            SystemPermissions.validate_permissions(role_data.permissions)
        
        # Preparar datos de actualización
        update_data = {}
        if role_data.display_name is not None:
            update_data["display_name"] = role_data.display_name
        if role_data.description is not None:
            update_data["description"] = role_data.description
        if role_data.permissions is not None:
            update_data["permissions"] = role_data.permissions
        if role_data.is_active is not None:
            update_data["is_active"] = role_data.is_active
        
        update_data["updated_at"] = datetime.now(timezone.utc)
        
        # Actualizar rol
        updated_role = await self.role_repository.update_role(role_id, update_data)
        if not updated_role:
            raise RoleNotFoundError(role_id)
        
        return RoleResponseDTO(
            id=str(updated_role.id),
            name=updated_role.name,
            display_name=updated_role.display_name,
            description=updated_role.description,
            permissions=updated_role.permissions,
            is_active=updated_role.is_active,
            is_system_role=updated_role.is_system_role,
            created_at=updated_role.created_at,
            updated_at=updated_role.updated_at
        )

class DeleteRoleUseCase:
    """Caso de uso para eliminar roles"""

    def __init__(self, role_repository: RoleRepository, user_repository: UserRepository):
        self.role_repository = role_repository
        self.user_repository = user_repository

    async def execute(self, role_id: str) -> bool:
        """Eliminar un rol"""
        
        # Verificar que el rol existe
        role = await self.role_repository.get_role_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id)
        
        # No permitir eliminar roles del sistema
        if role.is_system_role:
            raise InvalidRoleError(f"System role '{role.name}' cannot be deleted")
        
        # Verificar que no hay usuarios con este rol
        users_with_role = await self.user_repository.list_users()
        users_count = len([u for u in users_with_role if u.role and u.role.get("id") == role_id])
        
        if users_count > 0:
            raise InvalidRoleError(f"Cannot delete role '{role.name}' because {users_count} users have this role")
        
        # Eliminar rol
        return await self.role_repository.delete_role(role_id)

class GetRoleWithStatsUseCase:
    """Caso de uso para obtener rol con estadísticas"""

    def __init__(self, role_repository: RoleRepository, user_repository: UserRepository):
        self.role_repository = role_repository
        self.user_repository = user_repository

    async def execute(self, role_id: str) -> RoleWithStatsDTO:
        """Obtener rol con estadísticas de uso"""
        
        # Obtener rol
        role = await self.role_repository.get_role_by_id(role_id)
        if not role:
            raise RoleNotFoundError(role_id)
        
        # Contar usuarios con este rol
        users = await self.user_repository.list_users()
        user_count = len([u for u in users if u.role and u.role.get("id") == role_id])
        
        return RoleWithStatsDTO(
            id=str(role.id),
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            created_at=role.created_at,
            updated_at=role.updated_at,
            user_count=user_count,
            permission_count=len(role.permissions)
        )

class ListRolesWithStatsUseCase:
    """Caso de uso para listar roles con estadísticas"""

    def __init__(self, role_repository: RoleRepository, user_repository: UserRepository):
        self.role_repository = role_repository
        self.user_repository = user_repository

    async def execute(self, include_inactive: bool = False) -> List[RoleWithStatsDTO]:
        """Listar todos los roles con estadísticas"""
        
        # Obtener roles
        roles = await self.role_repository.list_roles()
        
        if not include_inactive:
            roles = [r for r in roles if r.is_active]
        
        # Obtener usuarios para contar
        users = await self.user_repository.list_users()
        
        # Crear lista con estadísticas
        roles_with_stats = []
        for role in roles:
            user_count = len([u for u in users if u.role and u.role.get("id") == str(role.id)])
            
            role_dto = RoleWithStatsDTO(
                id=str(role.id),
                name=role.name,
                display_name=role.display_name,
                description=role.description,
                permissions=role.permissions,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                created_at=role.created_at,
                updated_at=role.updated_at,
                user_count=user_count,
                permission_count=len(role.permissions)
            )
            roles_with_stats.append(role_dto)
        
        return roles_with_stats

class GetAvailablePermissionsUseCase:
    """Caso de uso para obtener todos los permisos disponibles"""

    def __init__(self):
        pass

    async def execute(self) -> Dict[str, List[Dict[str, str]]]:
        """Obtener todos los permisos disponibles organizados por categoría"""
        
        permissions = SystemPermissions.get_all_permissions()
        
        # Organizar por categorías
        categories = {}
        for permission in permissions:
            category_name = permission.category.value
            if category_name not in categories:
                categories[category_name] = []
            
            categories[category_name].append({
                "name": str(permission),
                "action": permission.action.value,
                "description": permission.description
            })
        
        return categories

class InitializeDefaultRolesUseCase:
    """Caso de uso para inicializar roles por defecto del sistema"""

    def __init__(self, role_repository: RoleRepository):
        self.role_repository = role_repository

    async def execute(self) -> List[RoleResponseDTO]:
        """Crear roles por defecto si no existen"""
        
        created_roles = []
        
        for role_name, role_config in DefaultRoles.ROLES_CONFIG.items():
            # Verificar si el rol ya existe
            existing_role = await self.role_repository.get_role_by_name(role_name)
            
            if not existing_role:
                # Crear rol por defecto
                role_data = Role(
                    name=role_name,
                    display_name=role_config["display_name"],
                    description=role_config["description"],
                    permissions=role_config["permissions"],
                    is_active=True,
                    is_system_role=True  # Los roles por defecto son del sistema
                )
                
                created_role = await self.role_repository.create_role(role_data)
                created_roles.append(RoleResponseDTO(
                    id=str(created_role.id),
                    name=created_role.name,
                    display_name=created_role.display_name,
                    description=created_role.description,
                    permissions=created_role.permissions,
                    is_active=created_role.is_active,
                    is_system_role=created_role.is_system_role,
                    created_at=created_role.created_at,
                    updated_at=created_role.updated_at
                ))
        
        return created_roles

class AssignRoleToUserUseCase:
    """Caso de uso para asignar rol a usuario"""

    def __init__(self, user_repository: UserRepository, role_repository: RoleRepository):
        self.user_repository = user_repository
        self.role_repository = role_repository

    async def execute(self, clerk_id: str, role_name: str) -> bool:
        """Asignar un rol a un usuario"""
        
        # Verificar que el usuario existe
        user = await self.user_repository.get_user_by_clerk_id(clerk_id)
        if not user:
            raise ValueError(f"User with clerk_id '{clerk_id}' not found")
        
        # Verificar que el rol existe y está activo
        role = await self.role_repository.get_role_by_name(role_name)
        if not role:
            raise RoleNotFoundError(role_name)
        
        if not role.is_active:
            raise InvalidRoleError(f"Role '{role_name}' is not active")
        
        # Asignar rol al usuario
        from ...domain.entities.auth_models import UserUpdate
        user_update = UserUpdate(role_name=role_name)
        updated_user = await self.user_repository.update_user(clerk_id, user_update)
        
        return updated_user is not None