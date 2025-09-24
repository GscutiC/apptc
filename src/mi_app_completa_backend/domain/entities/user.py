from typing import Optional
from .base_entity import BaseEntity

class User(BaseEntity):
    """Entidad User del dominio"""

    def __init__(
        self,
        name: str,
        email: str,
        id: Optional[str] = None
    ):
        super().__init__(id)
        self.name = name
        self.email = email

    def change_name(self, new_name: str):
        """Cambiar nombre del usuario"""
        if not new_name or not new_name.strip():
            raise ValueError("El nombre no puede estar vacío")

        self.name = new_name.strip()
        self.update_timestamp()

    def change_email(self, new_email: str):
        """Cambiar email del usuario"""
        if not new_email or "@" not in new_email:
            raise ValueError("Email inválido")

        self.email = new_email.lower().strip()
        self.update_timestamp()

    def to_dict(self) -> dict:
        """Convertir a diccionario para persistencia"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }