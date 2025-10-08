"""
Entidad para configuración contextual
FASE 3: Sistema de Configuración Contextual
"""

from typing import Optional
from datetime import datetime, timezone
from .base_entity import BaseEntity
from .interface_config import InterfaceConfig
from ..value_objects.config_context import ConfigContext


class ContextualConfig(BaseEntity):
    """
    Configuración de interfaz con contexto de aplicación

    Representa una configuración que se aplica en un contexto específico
    (usuario, rol, organización o global) siguiendo una jerarquía de prioridades.
    """

    def __init__(
        self,
        config: InterfaceConfig,
        context: ConfigContext,
        is_active: bool = True,
        created_by: Optional[str] = None,
        entity_id: Optional[str] = None
    ):
        """
        Inicializar configuración contextual

        Args:
            config: Configuración de interfaz a aplicar
            context: Contexto donde se aplica la configuración
            is_active: Si la configuración está activa
            created_by: ID del usuario que creó la configuración
            entity_id: ID de la entidad (para persistencia)
        """
        super().__init__(entity_id)
        self._config = config
        self._context = context
        self._is_active = is_active
        self._created_by = created_by

    @property
    def config(self) -> InterfaceConfig:
        """Obtener configuración de interfaz"""
        return self._config

    @property
    def context(self) -> ConfigContext:
        """Obtener contexto de aplicación"""
        return self._context

    @property
    def is_active(self) -> bool:
        """Verificar si la configuración está activa"""
        return self._is_active

    @property
    def created_by(self) -> Optional[str]:
        """Obtener ID del creador"""
        return self._created_by

    @property
    def priority(self) -> int:
        """Obtener prioridad del contexto (para ordenamiento)"""
        return self._context.priority

    @property
    def is_global(self) -> bool:
        """Verificar si es configuración global"""
        return self._context.is_global

    @property
    def is_user_specific(self) -> bool:
        """Verificar si es configuración de usuario específico"""
        return self._context.is_user_specific

    def activate(self) -> None:
        """Activar la configuración"""
        self._is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Desactivar la configuración"""
        self._is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def update_config(self, new_config: InterfaceConfig) -> None:
        """
        Actualizar la configuración de interfaz

        Args:
            new_config: Nueva configuración a aplicar
        """
        self._config = new_config
        self.updated_at = datetime.now(timezone.utc)

    def applies_to(
        self,
        user_id: Optional[str] = None,
        role_id: Optional[str] = None,
        org_id: Optional[str] = None
    ) -> bool:
        """
        Verificar si esta configuración aplica a un usuario con ciertos atributos

        Args:
            user_id: ID del usuario
            role_id: ID del rol del usuario
            org_id: ID de la organización del usuario

        Returns:
            True si la configuración es aplicable
        """
        if not self._is_active:
            return False

        return self._context.matches(user_id, role_id, org_id)

    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "config": self._config.to_dict() if hasattr(self._config, 'to_dict') else vars(self._config),
            "context": self._context.to_dict(),
            "isActive": self._is_active,
            "createdBy": self._created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None
        }

    def __str__(self) -> str:
        """Representación string"""
        status = "active" if self._is_active else "inactive"
        return f"ContextualConfig({self._context}, {status})"

    def __lt__(self, other: "ContextualConfig") -> bool:
        """Comparación para ordenamiento por prioridad"""
        return self.priority < other.priority
