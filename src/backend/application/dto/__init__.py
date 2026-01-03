"""
Data Transfer Objects (DTOs) for the application layer
"""
from .message_dto import CreateMessageDTO, MessageResponseDTO
from .user_dto import CreateUserDTO, UserResponseDTO
from .role_dto import (
    RoleCreateDTO, 
    RoleUpdateDTO, 
    RoleResponseDTO, 
    RoleWithStatsDTO,
    PermissionDTO,
    PermissionCategoryDTO,
    RoleAssignmentDTO,
    UserRoleDTO
)

__all__ = [
    'CreateMessageDTO',
    'MessageResponseDTO',
    'CreateUserDTO', 
    'UserResponseDTO',
    'RoleCreateDTO',
    'RoleUpdateDTO',
    'RoleResponseDTO',
    'RoleWithStatsDTO',
    'PermissionDTO',
    'PermissionCategoryDTO',
    'RoleAssignmentDTO',
    'UserRoleDTO'
]