"""
Use Cases for the application layer
"""
from .create_user import CreateUserUseCase
from .process_ai_message import ProcessAIMessageUseCase, GetWelcomeMessageUseCase
from .role_management import (
    CreateRoleUseCase,
    UpdateRoleUseCase,
    DeleteRoleUseCase,
    GetRoleWithStatsUseCase,
    ListRolesWithStatsUseCase,
    GetAvailablePermissionsUseCase,
    InitializeDefaultRolesUseCase,
    AssignRoleToUserUseCase
)

__all__ = [
    'CreateUserUseCase',
    'ProcessAIMessageUseCase',
    'GetWelcomeMessageUseCase',
    'CreateRoleUseCase',
    'UpdateRoleUseCase',
    'DeleteRoleUseCase',
    'GetRoleWithStatsUseCase',
    'ListRolesWithStatsUseCase',
    'GetAvailablePermissionsUseCase',
    'InitializeDefaultRolesUseCase',
    'AssignRoleToUserUseCase'
]