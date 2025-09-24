from typing import List, Optional
from abc import ABC, abstractmethod
from ..entities.auth_models import User, Role, UserCreate, UserUpdate, UserWithRole

class UserRepository(ABC):
    """Repositorio abstracto para usuarios"""
    
    @abstractmethod
    async def create_user(self, user_data: UserCreate) -> User:
        """Crear un nuevo usuario"""
        pass
    
    @abstractmethod
    async def get_user_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        """Obtener usuario por ID de Clerk"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        pass
    
    @abstractmethod
    async def get_user_with_role(self, clerk_id: str) -> Optional[UserWithRole]:
        """Obtener usuario con información completa del rol"""
        pass
    
    @abstractmethod
    async def update_user(self, clerk_id: str, user_data: UserUpdate) -> Optional[User]:
        """Actualizar usuario"""
        pass
    
    @abstractmethod
    async def delete_user(self, clerk_id: str) -> bool:
        """Eliminar usuario"""
        pass
    
    @abstractmethod
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserWithRole]:
        """Listar usuarios con paginación"""
        pass
    
    @abstractmethod
    async def update_last_login(self, clerk_id: str) -> bool:
        """Actualizar última fecha de login"""
        pass

class RoleRepository(ABC):
    """Repositorio abstracto para roles"""
    
    @abstractmethod
    async def create_role(self, role: Role) -> Role:
        """Crear un nuevo rol"""
        pass
    
    @abstractmethod
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Obtener rol por nombre"""
        pass
    
    @abstractmethod
    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Obtener rol por ID"""
        pass
    
    @abstractmethod
    async def list_roles(self) -> List[Role]:
        """Listar todos los roles activos"""
        pass
    
    @abstractmethod
    async def update_role(self, role_id: str, role_data: dict) -> Optional[Role]:
        """Actualizar rol"""
        pass
    
    @abstractmethod
    async def delete_role(self, role_id: str) -> bool:
        """Eliminar rol"""
        pass