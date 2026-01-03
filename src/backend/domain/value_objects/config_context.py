"""
Value Objects para contexto de configuración
FASE 3: Sistema de Configuración Contextual
"""

from typing import Optional, Literal
from dataclasses import dataclass


ContextType = Literal["user", "role", "org", "global"]


@dataclass(frozen=True)
class ConfigContext:
    """
    Contexto de aplicación de configuración

    Inmutable value object que representa el contexto donde se aplica una configuración.
    La jerarquía de prioridades es:
    1. user (prioridad 1) - más específico
    2. role (prioridad 2)
    3. org (prioridad 3)
    4. global (prioridad 4) - menos específico
    """

    context_type: ContextType
    context_id: Optional[str] = None  # None solo para 'global'

    def __post_init__(self):
        """Validar consistencia del contexto"""
        # Global no debe tener context_id
        if self.context_type == "global" and self.context_id is not None:
            raise ValueError("Global context must not have context_id")

        # Otros contextos deben tener context_id
        if self.context_type != "global" and not self.context_id:
            raise ValueError(f"{self.context_type} context must have context_id")

    @property
    def priority(self) -> int:
        """
        Obtener prioridad numérica del contexto
        Menor número = mayor prioridad
        """
        priorities = {
            "user": 1,
            "role": 2,
            "org": 3,
            "global": 4
        }
        return priorities[self.context_type]

    @property
    def is_global(self) -> bool:
        """Verificar si es contexto global"""
        return self.context_type == "global"

    @property
    def is_user_specific(self) -> bool:
        """Verificar si es configuración de usuario específico"""
        return self.context_type == "user"

    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "contextType": self.context_type,
            "contextId": self.context_id,
            "priority": self.priority
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigContext":
        """Crear desde diccionario"""
        return cls(
            context_type=data["contextType"],
            context_id=data.get("contextId")
        )

    @classmethod
    def create_global(cls) -> "ConfigContext":
        """Crear contexto global"""
        return cls(context_type="global", context_id=None)

    @classmethod
    def create_user(cls, user_id: str) -> "ConfigContext":
        """Crear contexto de usuario"""
        return cls(context_type="user", context_id=user_id)

    @classmethod
    def create_role(cls, role_id: str) -> "ConfigContext":
        """Crear contexto de rol"""
        return cls(context_type="role", context_id=role_id)

    @classmethod
    def create_org(cls, org_id: str) -> "ConfigContext":
        """Crear contexto de organización"""
        return cls(context_type="org", context_id=org_id)

    def matches(self, user_id: Optional[str] = None,
                role_id: Optional[str] = None,
                org_id: Optional[str] = None) -> bool:
        """
        Verificar si este contexto aplica a un usuario con ciertos atributos

        Args:
            user_id: ID del usuario
            role_id: ID del rol del usuario
            org_id: ID de la organización del usuario

        Returns:
            True si el contexto es aplicable
        """
        if self.is_global:
            return True

        if self.context_type == "user":
            return self.context_id == user_id

        if self.context_type == "role":
            return self.context_id == role_id

        if self.context_type == "org":
            return self.context_id == org_id

        return False

    def __str__(self) -> str:
        """Representación string del contexto"""
        if self.is_global:
            return "ConfigContext(global)"
        return f"ConfigContext({self.context_type}:{self.context_id})"

    def __lt__(self, other: "ConfigContext") -> bool:
        """Comparación para ordenamiento por prioridad"""
        return self.priority < other.priority
