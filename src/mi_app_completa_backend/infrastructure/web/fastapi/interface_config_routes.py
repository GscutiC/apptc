"""
Rutas para configuración de interfaz
Protegidas con autenticación JWT de Clerk
Refactorizado para usar repositorios MongoDB
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from ....domain.entities.auth_models import User
from ....application.use_cases.interface_config_use_cases import InterfaceConfigUseCases
from ....application.dto.interface_config_dto import (
    InterfaceConfigResponseDTO,
    PresetConfigResponseDTO
)
from ....infrastructure.persistence.mongodb.interface_config_repository_impl import (
    MongoInterfaceConfigRepository,
    MongoPresetConfigRepository,
    MongoConfigHistoryRepository
)
from ....infrastructure.config.database import get_database
from .auth_dependencies import get_current_user
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/interface-config", tags=["Interface Config"])

# Inicializar repositorios y use case
def get_interface_config_use_cases() -> InterfaceConfigUseCases:
    """Dependency para obtener instancia de use cases"""
    db = get_database()
    config_repo = MongoInterfaceConfigRepository(db)
    preset_repo = MongoPresetConfigRepository(db)
    history_repo = MongoConfigHistoryRepository(db)
    return InterfaceConfigUseCases(config_repo, preset_repo, history_repo)

@router.get("/current")
async def get_current_config(
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Obtener la configuración actual de interfaz desde MongoDB
    ENDPOINT PÚBLICO - No requiere autenticación
    """
    try:
        config = await use_cases.get_current_config()

        if not config:
            raise HTTPException(
                status_code=404,
                detail="No hay configuración activa. Use GET /api/interface-config/presets para ver presets disponibles."
            )

        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current/safe")
async def get_current_config_safe(
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Obtener la configuración actual de interfaz - versión segura
    Fallback graceful si no hay configuración
    ENDPOINT PÚBLICO - No requiere autenticación
    """
    try:
        config = await use_cases.get_current_config()

        # Si no hay configuración, retornar configuración por defecto
        if not config:
            return {
                "id": "default-config",
                "theme": {
                    "primary": {"500": "#3b82f6"},
                    "secondary": {"500": "#64748b"},
                    "accent": {"500": "#06b6d4"},
                    "neutral": {"500": "#6b7280"}
                },
                "branding": {
                    "title": "WorkTecApp",
                    "tagline": "Tu plataforma de trabajo",
                    "description": "Sistema completo de gestión"
                },
                "logos": {
                    "primary": None,
                    "secondary": None,
                    "favicon": None
                },
                "isActive": True,
                "createdAt": "2024-01-01T00:00:00.000Z",
                "updatedAt": "2024-01-01T00:00:00.000Z"
            }

        return config
    except Exception as e:
        logger.error(f"Error getting safe config: {e}")
        # En caso de error, retornar configuración mínima
        return {
            "id": "fallback-config",
            "theme": {
                "primary": {"500": "#3b82f6"}
            },
            "branding": {
                "title": "WorkTecApp"
            },
            "isActive": True
        }

@router.patch("/partial")
async def update_partial_config(
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Actualizar configuración actual (parcial)
    Requiere: Usuario autenticado con rol de administrador
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para modificar la configuración global"
        )

    try:
        logger.info(f"Config updated by admin: {current_user.email}")

        # Obtener configuración actual
        current_config = await use_cases.get_current_config()
        if not current_config:
            raise HTTPException(status_code=404, detail="No hay configuración activa")

        # Importar DTO y convertir updates
        from ....application.dto.interface_config_dto import InterfaceConfigUpdateDTO

        # Por ahora aplicamos updates directamente (TODO: mejorar validación con DTO)
        updated_config = await use_cases.update_config(
            config_id=current_config.id,
            config_data=InterfaceConfigUpdateDTO(**updates),
            updated_by=current_user.email
        )

        if not updated_config:
            raise HTTPException(status_code=404, detail="Error actualizando configuración")

        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === ENDPOINTS PARA PRESETS ===

@router.get("/presets")
async def get_presets(
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Obtener todos los presets disponibles desde MongoDB
    Requiere: Usuario autenticado
    """
    try:
        presets = await use_cases.get_all_presets()
        return presets
    except Exception as e:
        logger.error(f"Error getting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{preset_id}")
async def get_preset_by_id(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Obtener preset específico por ID desde MongoDB
    Requiere: Usuario autenticado
    """
    try:
        preset = await use_cases.preset_repo.get_preset_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset no encontrado")

        # Convertir a DTO
        return use_cases._preset_to_response_dto(preset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presets/{preset_id}/apply")
async def apply_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Aplicar un preset específico como configuración activa
    Requiere: Usuario autenticado con rol de administrador
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para aplicar presets"
        )

    try:
        logger.info(f"Preset {preset_id} applied by admin: {current_user.email}")

        # Aplicar preset usando el caso de uso
        applied_config = await use_cases.apply_preset(
            preset_id=preset_id,
            applied_by=current_user.email
        )

        if not applied_config:
            raise HTTPException(status_code=404, detail="Preset no encontrado")

        # Obtener nombre del preset
        preset = await use_cases.preset_repo.get_preset_by_id(preset_id)
        preset_name = preset.name if preset else "Unknown"

        return {
            "message": f"Preset '{preset_name}' aplicado correctamente",
            "preset_id": preset_id,
            "config": applied_config
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error aplicando preset: {str(e)}")

@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Eliminar preset personalizado (no permite eliminar presets del sistema)
    Requiere: Usuario autenticado con rol de administrador
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para eliminar presets"
        )

    try:
        logger.info(f"Preset {preset_id} deletion attempted by admin: {current_user.email}")

        # El caso de uso ya valida que no sea preset del sistema
        success = await use_cases.delete_preset(preset_id)

        if not success:
            raise HTTPException(status_code=404, detail="Preset no encontrado")

        return {"message": "Preset eliminado correctamente", "preset_id": preset_id}
    except ValueError as e:
        # Error de validación (ej: intento de eliminar preset del sistema)
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_config_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Obtener historial de cambios de configuración
    Requiere: Usuario autenticado con rol de administrador
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para ver el historial"
        )

    try:
        history = await use_cases.get_config_history(limit=limit)
        return history
    except Exception as e:
        logger.error(f"Error getting config history: {e}")
        raise HTTPException(status_code=500, detail=str(e))