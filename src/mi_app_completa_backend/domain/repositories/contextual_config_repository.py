"""
Repository interface para configuraciones contextuales
FASE 3: Sistema de Configuración Contextual
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.contextual_config import ContextualConfig
from ..entities.interface_config import InterfaceConfig


class ContextualConfigRepository(ABC):
    """
    Repositorio para gestionar configuraciones contextuales

    Permite guardar y recuperar configuraciones específicas para
    usuarios, roles, organizaciones o global.
    """

    @abstractmethod
    async def get_by_context(
        self,
        context_type: str,
        context_id: Optional[str]
    ) -> Optional[ContextualConfig]:
        """
        Obtener configuración por contexto específico

        Args:
            context_type: Tipo de contexto ("user", "role", "org", "global")
            context_id: ID del contexto (None para global)

        Returns:
            Configuración contextual o None si no existe
        """
        pass

    @abstractmethod
    async def get_for_user(
        self,
        user_id: str,
        role_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> InterfaceConfig:
        """
        Obtener configuración aplicable a un usuario usando jerarquía

        Resuelve la configuración siguiendo la jerarquía de prioridades:
        1. Usuario específico
        2. Rol
        3. Organización
        4. Global

        Args:
            user_id: ID del usuario
            role_id: ID del rol del usuario
            org_id: ID de la organización del usuario

        Returns:
            Configuración de interfaz aplicable
        """
        pass

    @abstractmethod
    async def save(self, contextual_config: ContextualConfig) -> ContextualConfig:
        """
        Guardar configuración contextual

        Args:
            contextual_config: Configuración contextual a guardar

        Returns:
            Configuración guardada con ID actualizado
        """
        pass

    @abstractmethod
    async def delete(self, config_id: str) -> bool:
        """
        Eliminar configuración contextual

        Args:
            config_id: ID de la configuración

        Returns:
            True si se eliminó, False si no existía
        """
        pass

    @abstractmethod
    async def list_by_type(
        self,
        context_type: str,
        active_only: bool = True
    ) -> List[ContextualConfig]:
        """
        Listar configuraciones por tipo de contexto

        Args:
            context_type: Tipo de contexto a filtrar
            active_only: Si True, solo retorna configuraciones activas

        Returns:
            Lista de configuraciones contextuales
        """
        pass

    @abstractmethod
    async def list_all(self, active_only: bool = True) -> List[ContextualConfig]:
        """
        Listar todas las configuraciones contextuales

        Args:
            active_only: Si True, solo retorna configuraciones activas

        Returns:
            Lista de todas las configuraciones contextuales
        """
        pass

    @abstractmethod
    async def get_by_id(self, config_id: str) -> Optional[ContextualConfig]:
        """
        Obtener configuración contextual por ID

        Args:
            config_id: ID de la configuración

        Returns:
            Configuración contextual o None si no existe
        """
        pass

    @abstractmethod
    async def deactivate_all_for_context(
        self,
        context_type: str,
        context_id: Optional[str]
    ) -> int:
        """
        Desactivar todas las configuraciones de un contexto

        Útil cuando se quiere establecer una nueva configuración como única activa
        para un contexto.

        Args:
            context_type: Tipo de contexto
            context_id: ID del contexto

        Returns:
            Número de configuraciones desactivadas
        """
        pass

    @abstractmethod
    async def count_by_type(self, context_type: str) -> int:
        """
        Contar configuraciones por tipo

        Args:
            context_type: Tipo de contexto

        Returns:
            Número total de configuraciones de ese tipo
        """
        pass
