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
    PresetConfigResponseDTO,
    PresetConfigCreateDTO
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


# Configuración por defecto completa
DEFAULT_CONFIG = {
    "id": "default-config",
    "theme": {
        "mode": "light",
        "name": "Configuración por Defecto",
        "colors": {
            "primary": {
                "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0",
                "300": "#6ee7b7", "400": "#34d399", "500": "#10b981",
                "600": "#059669", "700": "#047857", "800": "#065f46", "900": "#064e3b"
            },
            "secondary": {
                "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb",
                "300": "#d1d5db", "400": "#9ca3af", "500": "#6b7280",
                "600": "#4b5563", "700": "#374151", "800": "#1f2937", "900": "#111827"
            },
            "accent": {
                "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0",
                "300": "#6ee7b7", "400": "#34d399", "500": "#10b981",
                "600": "#059669", "700": "#047857", "800": "#065f46", "900": "#064e3b"
            },
            "neutral": {
                "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb",
                "300": "#d1d5db", "400": "#9ca3af", "500": "#6b7280",
                "600": "#4b5563", "700": "#374151", "800": "#1f2937", "900": "#111827"
            }
        },
        "typography": {
            "fontFamily": {
                "primary": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                "secondary": "Georgia, 'Times New Roman', serif",
                "mono": "Monaco, Consolas, 'Courier New', monospace"
            },
            "fontSize": {
                "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
                "3xl": "1.875rem", "4xl": "2.25rem"
            },
            "fontWeight": {
                "light": 300, "normal": 400, "medium": 500,
                "semibold": 600, "bold": 700
            }
        },
        "layout": {
            "borderRadius": {
                "none": "0", "sm": "0.125rem", "base": "0.25rem",
                "md": "0.375rem", "lg": "0.5rem", "xl": "0.75rem",
                "2xl": "1rem", "full": "9999px"
            },
            "spacing": {
                "0": "0", "1": "0.25rem", "2": "0.5rem", "3": "0.75rem",
                "4": "1rem", "5": "1.25rem", "6": "1.5rem", "8": "2rem"
            },
            "shadows": {
                "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                "base": "0 1px 3px 0 rgb(0 0 0 / 0.1)",
                "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)"
            }
        }
    },
    "logos": {
        "mainLogo": {"text": "ScutiTec", "showText": True, "showImage": False},
        "favicon": {"url": None},
        "sidebarLogo": {"text": "ScutiTec", "showText": True, "showImage": False, "collapsedText": "ST"}
    },
    "branding": {
        "appName": "ScutiTec",
        "appDescription": "Soluciones empresariales inteligentes",
        "tagline": "Tu plataforma de gestión empresarial",
        "companyName": "ScutiTec",
        "welcomeMessage": "¡Bienvenido!",
        "loginPageTitle": "Iniciar Sesión",
        "loginPageDescription": "Accede a tu cuenta para continuar",
        "footerText": "© 2024 ScutiTec. Todos los derechos reservados.",
        "supportEmail": "soporte@scutitec.com"
    },
    "customCSS": None,
    "isActive": True,
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
}


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
    Siempre devuelve una configuración válida (fallback graceful)
    ENDPOINT PÚBLICO - No requiere autenticación
    
    🆕 MEJORADO: Siempre devuelve configuración en formato correcto
    """
    try:
        config = await use_cases.get_current_config()

        # Si hay configuración en BD, devolverla
        if config:
            return config

        # FALLBACK: Devolver configuración por defecto
        logger.warn("No hay configuración en BD, usando configuración por defecto")
        return DEFAULT_CONFIG

    except Exception as e:
        logger.error(f"Error getting safe config: {e}")
        
        # ÚLTIMO RECURSO: Devolver configuración por defecto
        return DEFAULT_CONFIG


@router.patch("/partial")
async def update_partial_config(
    updates: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Actualizar configuración actual con merge inteligente de cambios parciales.
    Solo actualiza los campos especificados, manteniendo el resto intactos.
    
    Requiere: Usuario autenticado con rol de administrador
    
    Ejemplo de body:
    {
        "theme": {
            "colors": {
                "primary": {
                    "500": "#3b82f6",
                    "600": "#2563eb"
                }
            }
        },
        "branding": {
            "appName": "Nueva App"
        }
    }
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para modificar la configuración global"
        )

    try:
        # Obtener configuración actual
        current_config_dto = await use_cases.get_current_config()
        if not current_config_dto:
            raise HTTPException(status_code=404, detail="No hay configuración activa")

        # Importar DTO para actualizaciones parciales
        from ....application.dto.interface_config_dto import PartialInterfaceConfigUpdateDTO

        # Convertir updates a DTO con validación fuerte
        try:
            partial_dto = PartialInterfaceConfigUpdateDTO(**updates)
        except Exception as validation_error:
            logger.error(f"Validation error: {validation_error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error de validación: {str(validation_error)}"
            )

        # Aplicar actualizaciones parciales con merge inteligente
        updated_config = await use_cases.update_config_partial(
            config_id=current_config_dto.id,
            partial_updates=partial_dto,
            updated_by=current_user.email
        )

        if not updated_config:
            raise HTTPException(status_code=404, detail="Error actualizando configuración")

        return updated_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# === ENDPOINTS PARA PRESETS ===

@router.post("/presets", response_model=PresetConfigResponseDTO)
async def create_preset(
    preset_data: PresetConfigCreateDTO,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Crear nuevo preset personalizado
    Requiere: Usuario autenticado con rol de administrador
    
    Args:
        preset_data: Datos del preset (name, description, config)
        current_user: Usuario autenticado (inyectado por dependencia)
        use_cases: Casos de uso de configuración (inyectado)
        
    Returns:
        PresetConfigResponseDTO: Preset creado con su ID
        
    Raises:
        403: Si el usuario no tiene permisos de administrador
        400: Si los datos son inválidos o intenta marcar como preset del sistema
        500: Error interno del servidor
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para crear presets"
        )

    try:
        logger.info(f"Creating preset '{preset_data.name}' by admin: {current_user.email}")

        # Los presets personalizados NUNCA deben ser del sistema
        if preset_data.isSystem:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los presets creados por usuarios no pueden marcarse como presets del sistema"
            )

        # Crear preset usando el caso de uso
        new_preset = await use_cases.create_preset(
            preset_data=preset_data,
            created_by=current_user.email
        )

        logger.info(f"✅ Preset '{new_preset.name}' created successfully with ID: {new_preset.id}")
        return new_preset

    except HTTPException:
        raise
    except ValueError as e:
        # Errores de validación del use case
        logger.warning(f"Validation error creating preset: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating preset: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando preset: {str(e)}"
        )


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


@router.put("/presets/{preset_id}", response_model=PresetConfigResponseDTO)
async def update_preset(
    preset_id: str,
    preset_data: PresetConfigCreateDTO,
    current_user: User = Depends(get_current_user),
    use_cases: InterfaceConfigUseCases = Depends(get_interface_config_use_cases)
):
    """
    Actualizar preset existente (nombre, descripción, colores)
    No permite editar presets del sistema
    Requiere: Usuario autenticado con rol de administrador
    
    Args:
        preset_id: ID del preset a actualizar
        preset_data: Nuevos datos del preset (name, description, config)
        current_user: Usuario autenticado (inyectado por dependencia)
        use_cases: Casos de uso de configuración (inyectado)
        
    Returns:
        PresetConfigResponseDTO: Preset actualizado
        
    Raises:
        403: Si el usuario no tiene permisos de administrador
        404: Si el preset no existe
        400: Si intenta editar un preset del sistema
        500: Error interno del servidor
    """
    # Validar permisos de admin
    user_role = current_user.role.get("name") if current_user.role else current_user.role_name
    if user_role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para editar presets"
        )

    try:
        logger.info(f"Updating preset {preset_id} by admin: {current_user.email}")

        # Actualizar preset usando el caso de uso
        updated_preset = await use_cases.update_preset(
            preset_id=preset_id,
            preset_data=preset_data,
            updated_by=current_user.email
        )

        if not updated_preset:
            raise HTTPException(status_code=404, detail="Preset no encontrado")

        logger.info(f"✅ Preset '{updated_preset.name}' updated successfully")
        return updated_preset

    except ValueError as e:
        # Error de validación (ej: intento de editar preset del sistema)
        logger.warning(f"Validation error updating preset: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preset {preset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando preset: {str(e)}"
        )


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