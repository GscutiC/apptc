from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User

class UserRepository(ABC):
    """Interface del repositorio de usuarios"""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Guardar usuario"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Buscar usuario por ID"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Buscar usuario por email"""
        pass

    @abstractmethod
    async def find_all(self) -> List[User]:
        """Obtener todos los usuarios"""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Eliminar usuario"""
        pass