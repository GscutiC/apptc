"""
Use Cases (Casos de Uso) para la configuración visual del módulo Techo Propio
Contiene la lógica de negocio para gestionar configuraciones
"""
from typing import Optional
from datetime import datetime

from ...domain.repositories.techo_propio_config_repository import TechoPropioConfigRepository
from ...domain.entities.techo_propio_config import TechoPropioThemeConfig
from ..dto.techo_propio_config_dto import (
    TechoPropioConfigCreateDTO,
    TechoPropioConfigResponseDTO,
    TechoPropioConfigUpdateDTO,
    ColorsDTO,
    LogosDTO,
    BrandingDTO
)


class TechoPropioConfigUseCases:
    """Casos de uso para gestión de configuración del módulo Techo Propio"""

    def __init__(self, config_repo: TechoPropioConfigRepository):
        self.config_repo = config_repo

    async def get_user_config(self, user_id: str) -> Optional[TechoPropioConfigResponseDTO]:
        """
        Obtener configuración del usuario
        Si no existe, retorna None (frontend usará default)
        """
        config = await self.config_repo.find_by_user_id(user_id)

        if not config:
            return None

        return self._to_response_dto(config)

    async def save_user_config(
        self,
        user_id: str,
        config_data: TechoPropioConfigCreateDTO
    ) -> TechoPropioConfigResponseDTO:
        """
        Guardar o actualizar la configuración del usuario
        Si ya existe, actualiza. Si no existe, crea nueva.
        """
        # Buscar configuración existente
        existing = await self.config_repo.find_by_user_id(user_id)

        if existing:
            # Actualizar existente
            existing.colors = config_data.colors.model_dump()
            existing.logos = config_data.logos.model_dump()
            existing.branding = config_data.branding.model_dump()
            existing.update_timestamp()

            updated = await self.config_repo.update(existing.id, existing)
            return self._to_response_dto(updated)
        else:
            # Crear nueva
            new_config = TechoPropioThemeConfig(
                user_id=user_id,
                colors=config_data.colors.model_dump(),
                logos=config_data.logos.model_dump(),
                branding=config_data.branding.model_dump()
            )

            saved = await self.config_repo.save(new_config)
            return self._to_response_dto(saved)

    async def update_user_config(
        self,
        user_id: str,
        config_data: TechoPropioConfigUpdateDTO
    ) -> Optional[TechoPropioConfigResponseDTO]:
        """
        Actualizar parcialmente la configuración del usuario
        Solo actualiza los campos que vienen en el DTO
        """
        # Buscar configuración existente
        existing = await self.config_repo.find_by_user_id(user_id)

        if not existing:
            return None

        # Actualizar solo los campos que vienen en el DTO
        if config_data.colors:
            existing.colors = config_data.colors.model_dump()

        if config_data.logos:
            existing.logos = config_data.logos.model_dump()

        if config_data.branding:
            existing.branding = config_data.branding.model_dump()

        existing.update_timestamp()

        updated = await self.config_repo.update(existing.id, existing)
        return self._to_response_dto(updated)

    async def delete_user_config(self, user_id: str) -> bool:
        """
        Eliminar la configuración del usuario (reset a default)
        Retorna True si se eliminó, False si no existía
        """
        return await self.config_repo.delete_by_user_id(user_id)

    def get_default_config(self) -> TechoPropioConfigResponseDTO:
        """
        Retorna la configuración por defecto
        Usada cuando el usuario no ha personalizado su vista
        """
        return TechoPropioConfigResponseDTO(
            id=None,
            user_id="",
            colors=ColorsDTO(
                primary="#16A34A",
                secondary="#2563EB",
                accent="#DC2626"
            ),
            logos=LogosDTO(
                sidebar_icon="🏠",
                sidebar_icon_file_id=None,
                sidebar_icon_url=None,
                header_logo=None,
                header_logo_file_id=None,
                header_logo_url=None
            ),
            branding=BrandingDTO(
                module_title="Techo Propio",
                module_description="Gestión de Solicitudes",
                dashboard_welcome="Bienvenido al sistema"
            ),
            created_at=None,
            updated_at=None
        )

    async def config_exists(self, user_id: str) -> bool:
        """Verificar si el usuario tiene configuración personalizada"""
        return await self.config_repo.exists_by_user_id(user_id)

    def _to_response_dto(self, config: TechoPropioThemeConfig) -> TechoPropioConfigResponseDTO:
        """Convertir entidad a DTO de respuesta"""
        return TechoPropioConfigResponseDTO(
            id=config.id,
            user_id=config.user_id,
            colors=ColorsDTO(**config.colors),
            logos=LogosDTO(**config.logos),
            branding=BrandingDTO(**config.branding),
            created_at=config.created_at.isoformat() if config.created_at else None,
            updated_at=config.updated_at.isoformat() if config.updated_at else None
        )
