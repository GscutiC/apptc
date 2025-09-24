from typing import Optional
from ..dto.user_dto import CreateUserDTO, UserResponseDTO
from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository

class CreateUserUseCase:
    """Caso de uso para crear usuario"""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_data: CreateUserDTO) -> UserResponseDTO:
        """Ejecutar caso de uso de creación de usuario"""

        # Verificar que el email no esté en uso
        existing_user = await self.user_repository.find_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"Ya existe un usuario con el email {user_data.email}")

        # Crear nueva entidad de usuario
        user = User(
            name=user_data.name,
            email=user_data.email
        )

        # Guardar usuario
        saved_user = await self.user_repository.save(user)

        # Retornar DTO de respuesta
        return UserResponseDTO(
            id=saved_user.id,
            name=saved_user.name,
            email=saved_user.email,
            created_at=saved_user.created_at
        )