"""
Tests unitarios para el sistema de permisos y roles
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.mi_app_completa_backend.domain.value_objects.permissions import (
    SystemPermissions, DefaultRoles, has_permission, has_any_permission, has_all_permissions
)
from src.mi_app_completa_backend.domain.value_objects.exceptions import (
    InsufficientPermissionsError, InvalidRoleError, RoleNotFoundError
)
from src.mi_app_completa_backend.domain.entities.auth_models import Role, RoleCreate
from src.mi_app_completa_backend.application.dto.role_dto import RoleCreateDTO, RoleUpdateDTO
from src.mi_app_completa_backend.application.use_cases.role_management import (
    CreateRoleUseCase, UpdateRoleUseCase, DeleteRoleUseCase
)

class TestPermissions:
    """Tests para el sistema de permisos"""
    
    def test_system_permissions_exist(self):
        """Verificar que existen permisos del sistema"""
        permissions = SystemPermissions.get_all_permissions()
        assert len(permissions) > 0
        assert any(str(p) == "users.create" for p in permissions)
        assert any(str(p) == "roles.create" for p in permissions)
    
    def test_permissions_by_category(self):
        """Verificar permisos por categoría"""
        from src.mi_app_completa_backend.domain.value_objects.permissions import PermissionCategory
        
        user_permissions = SystemPermissions.get_permissions_by_category(PermissionCategory.USERS)
        assert len(user_permissions) > 0
        assert all(p.category == PermissionCategory.USERS for p in user_permissions)
    
    def test_permission_validation(self):
        """Verificar validación de permisos"""
        valid_permissions = ["users.create", "users.read", "roles.create"]
        validated = SystemPermissions.validate_permissions(valid_permissions)
        assert len(validated) == len(valid_permissions)
        
        # Test permiso inválido
        with pytest.raises(ValueError):
            SystemPermissions.validate_permissions(["invalid.permission"])
    
    def test_has_permission_function(self):
        """Verificar función has_permission"""
        user_permissions = ["users.create", "users.read", "messages.create"]
        
        assert has_permission(user_permissions, "users.create") == True
        assert has_permission(user_permissions, "users.delete") == False
        assert has_permission(["*"], "any.permission") == True
        assert has_permission(["users.*"], "users.create") == True
        assert has_permission(["users.*"], "roles.create") == False
    
    def test_has_any_permission_function(self):
        """Verificar función has_any_permission"""
        user_permissions = ["users.create", "messages.read"]
        required_permissions = ["users.create", "users.update"]
        
        assert has_any_permission(user_permissions, required_permissions) == True
        
        required_permissions = ["roles.create", "admin.settings"]
        assert has_any_permission(user_permissions, required_permissions) == False
    
    def test_has_all_permissions_function(self):
        """Verificar función has_all_permissions"""
        user_permissions = ["users.create", "users.read", "users.update"]
        required_permissions = ["users.create", "users.read"]
        
        assert has_all_permissions(user_permissions, required_permissions) == True
        
        required_permissions = ["users.create", "roles.create"]
        assert has_all_permissions(user_permissions, required_permissions) == False

class TestDefaultRoles:
    """Tests para roles por defecto"""
    
    def test_default_roles_exist(self):
        """Verificar que existen roles por defecto"""
        assert "user" in DefaultRoles.ROLES_CONFIG
        assert "admin" in DefaultRoles.ROLES_CONFIG
        assert "super_admin" in DefaultRoles.ROLES_CONFIG
    
    def test_role_permissions_valid(self):
        """Verificar que los permisos de roles por defecto son válidos"""
        for role_name, config in DefaultRoles.ROLES_CONFIG.items():
            permissions = config["permissions"]
            # No debe fallar la validación
            SystemPermissions.validate_permissions(permissions)
    
    def test_role_hierarchy(self):
        """Verificar jerarquía de roles"""
        user_perms = set(DefaultRoles.ROLES_CONFIG["user"]["permissions"])
        admin_perms = set(DefaultRoles.ROLES_CONFIG["admin"]["permissions"])
        super_admin_perms = set(DefaultRoles.ROLES_CONFIG["super_admin"]["permissions"])
        
        # User permissions should be subset of admin permissions
        assert user_perms.issubset(admin_perms)
        # Admin permissions should be subset of super_admin permissions
        assert admin_perms.issubset(super_admin_perms)

class TestRoleModel:
    """Tests para el modelo Role"""
    
    def test_role_creation(self):
        """Verificar creación de rol"""
        role = Role(
            name="test_role",
            display_name="Test Role",
            description="A test role",
            permissions=["users.read", "messages.create"],
            is_active=True
        )
        
        assert role.name == "test_role"
        assert role.display_name == "Test Role"
        assert len(role.permissions) == 2
        assert role.is_active == True
    
    def test_role_name_validation(self):
        """Verificar validación del nombre de rol"""
        # Nombre válido
        role_data = {
            "name": "valid_role",
            "display_name": "Valid Role",
            "permissions": ["users.read"]
        }
        role = Role(**role_data)
        assert role.name == "valid_role"
        
        # Nombre inválido debería fallar en validación
        with pytest.raises(ValueError):
            Role(
                name="Invalid Role Name!",
                display_name="Invalid Role",
                permissions=["users.read"]
            )
    
    def test_role_methods(self):
        """Verificar métodos del rol"""
        role = Role(
            name="test_role",
            display_name="Test Role",
            permissions=["users.read", "users.create"],
            is_active=True
        )
        
        assert role.has_permission("users.read") == True
        assert role.has_permission("users.delete") == False
        assert role.get_permission_count() == 2
        assert role.is_super_admin() == False
        
        # Test add/remove permissions
        role.add_permission("users.update")
        assert "users.update" in role.permissions
        assert role.get_permission_count() == 3
        
        role.remove_permission("users.read")
        assert "users.read" not in role.permissions
        assert role.get_permission_count() == 2

@pytest.mark.asyncio
class TestRoleUseCases:
    """Tests para casos de uso de roles"""
    
    async def test_create_role_use_case(self):
        """Test crear rol"""
        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get_role_by_name.return_value = None  # Rol no existe
        mock_repo.create_role.return_value = Role(
            name="new_role",
            display_name="New Role",
            permissions=["users.read"],
            is_active=True
        )
        
        use_case = CreateRoleUseCase(mock_repo)
        
        role_data = RoleCreateDTO(
            name="new_role",
            display_name="New Role",
            permissions=["users.read"],
            is_active=True
        )
        
        result = await use_case.execute(role_data)
        
        assert result.name == "new_role"
        assert result.display_name == "New Role"
        mock_repo.get_role_by_name.assert_called_once_with("new_role")
        mock_repo.create_role.assert_called_once()
    
    async def test_create_role_already_exists(self):
        """Test crear rol que ya existe"""
        # Mock repository - rol ya existe
        mock_repo = AsyncMock()
        mock_repo.get_role_by_name.return_value = Role(
            name="existing_role",
            display_name="Existing Role",
            permissions=[],
            is_active=True
        )
        
        use_case = CreateRoleUseCase(mock_repo)
        
        role_data = RoleCreateDTO(
            name="existing_role",
            display_name="Existing Role",
            permissions=["users.read"],
            is_active=True
        )
        
        with pytest.raises(InvalidRoleError):
            await use_case.execute(role_data)
    
    async def test_update_role_use_case(self):
        """Test actualizar rol"""
        existing_role = Role(
            name="test_role",
            display_name="Test Role",
            permissions=["users.read"],
            is_active=True,
            is_system_role=False
        )
        
        updated_role = Role(
            name="test_role",
            display_name="Updated Test Role",
            permissions=["users.read", "users.update"],
            is_active=True,
            is_system_role=False
        )
        
        mock_repo = AsyncMock()
        mock_repo.get_role_by_id.return_value = existing_role
        mock_repo.update_role.return_value = updated_role
        
        use_case = UpdateRoleUseCase(mock_repo)
        
        update_data = RoleUpdateDTO(
            display_name="Updated Test Role",
            permissions=["users.read", "users.update"]
        )
        
        result = await use_case.execute("role_id", update_data)
        
        assert result.display_name == "Updated Test Role"
        assert len(result.permissions) == 2
        mock_repo.get_role_by_id.assert_called_once_with("role_id")
        mock_repo.update_role.assert_called_once()
    
    async def test_update_system_role_fails(self):
        """Test que no se puede actualizar rol del sistema"""
        system_role = Role(
            name="super_admin",
            display_name="Super Admin",
            permissions=["*"],
            is_active=True,
            is_system_role=True  # Es rol del sistema
        )
        
        mock_repo = AsyncMock()
        mock_repo.get_role_by_id.return_value = system_role
        
        use_case = UpdateRoleUseCase(mock_repo)
        
        update_data = RoleUpdateDTO(display_name="Modified Super Admin")
        
        with pytest.raises(InvalidRoleError):
            await use_case.execute("role_id", update_data)
    
    async def test_delete_role_use_case(self):
        """Test eliminar rol"""
        role_to_delete = Role(
            name="deletable_role",
            display_name="Deletable Role",
            permissions=["users.read"],
            is_active=True,
            is_system_role=False
        )
        
        mock_role_repo = AsyncMock()
        mock_user_repo = AsyncMock()
        
        mock_role_repo.get_role_by_id.return_value = role_to_delete
        mock_user_repo.list_users.return_value = []  # No hay usuarios con este rol
        mock_role_repo.delete_role.return_value = True
        
        use_case = DeleteRoleUseCase(mock_role_repo, mock_user_repo)
        
        result = await use_case.execute("role_id")
        
        assert result == True
        mock_role_repo.get_role_by_id.assert_called_once_with("role_id")
        mock_user_repo.list_users.assert_called_once()
        mock_role_repo.delete_role.assert_called_once_with("role_id")

class TestExceptions:
    """Tests para excepciones personalizadas"""
    
    def test_insufficient_permissions_error(self):
        """Test InsufficientPermissionsError"""
        error = InsufficientPermissionsError("users.create", ["users.read"])
        assert "users.create" in str(error)
        assert "users.read" in str(error)
    
    def test_invalid_role_error(self):
        """Test InvalidRoleError"""
        error = InvalidRoleError("invalid_role")
        assert "invalid_role" in str(error)
    
    def test_role_not_found_error(self):
        """Test RoleNotFoundError"""
        error = RoleNotFoundError("nonexistent_role")
        assert "nonexistent_role" in str(error)

if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])