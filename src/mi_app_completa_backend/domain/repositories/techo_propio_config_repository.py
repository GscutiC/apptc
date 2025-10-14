"""
Repositorio abstracto para la configuración visual del módulo Techo Propio
Define la interfaz que debe implementar cualquier repositorio
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..entities.techo_propio_config import TechoPropioThemeConfig


class TechoPropioConfigRepository(ABC):
    """Interfaz del repositorio para configuración de Techo Propio"""

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[TechoPropioThemeConfig]:
        """
        Buscar configuración por user_id
        Retorna None si no existe configuración para el usuario
        """
        pass

    @abstractmethod
    async def save(self, config: TechoPropioThemeConfig) -> TechoPropioThemeConfig:
        """
        Guardar nueva configuración
        Retorna la configuración guardada con id asignado
        """
        pass

    @abstractmethod
    async def update(self, config_id: str, config: TechoPropioThemeConfig) -> TechoPropioThemeConfig:
        """
        Actualizar configuración existente
        Retorna la configuración actualizada
        """
        pass

    @abstractmethod
    async def delete_by_user_id(self, user_id: str) -> bool:
        """
        Eliminar configuración por user_id (reset a default)
        Retorna True si se eliminó, False si no existía
        """
        pass

    @abstractmethod
    async def exists_by_user_id(self, user_id: str) -> bool:
        """
        Verificar si existe configuración para el usuario
        Retorna True si existe, False si no
        """
        pass
