"""
Repositorio abstracto para manejo de archivos
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.file_entity import File


class FileRepository(ABC):
    """Repositorio abstracto para archivos"""
    
    @abstractmethod
    async def save_file(self, file: File) -> File:
        """Guardar archivo en el repositorio"""
        pass
    
    @abstractmethod
    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        """Obtener archivo por ID"""
        pass
    
    @abstractmethod
    async def get_files_by_category(self, category: str) -> List[File]:
        """Obtener archivos por categoría"""
        pass
    
    @abstractmethod
    async def get_files_by_user(self, user_id: str) -> List[File]:
        """Obtener archivos de un usuario"""
        pass
    
    @abstractmethod
    async def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo del repositorio"""
        pass
    
    @abstractmethod
    async def update_file(self, file: File) -> File:
        """Actualizar información del archivo"""
        pass
    
    @abstractmethod
    async def file_exists(self, file_id: str) -> bool:
        """Verificar si un archivo existe"""
        pass
    
    @abstractmethod
    async def get_all_files(self, limit: int = 100, offset: int = 0) -> List[File]:
        """Obtener todos los archivos con paginación"""
        pass
    
    @abstractmethod
    async def cleanup_inactive_files(self) -> int:
        """Limpiar archivos inactivos y retornar cantidad eliminada"""
        pass