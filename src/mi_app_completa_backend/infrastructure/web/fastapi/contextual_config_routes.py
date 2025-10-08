"""
Rutas para configuraciones contextuales
FASE 3: Endpoints para configuración por usuario, rol, org y contexto
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional

from ....domain.entities.auth_models import User
from ....application.use_cases.contextual_config_use_cases import ContextualConfigUseCases
from ....application.dto.contextual_config_dto import (
    ContextualConfigCreateDTO,
    ContextualConfigUpdateDTO,
    ContextualConfigResponseDTO,
    EffectiveConfigRequestDTO,
    EffectiveConfigResponseDTO,
    ContextualConfigSearchDTO,
    ContextualConfigListDTO,
    UserPreferencesDTO
)
from ....infrastructure.persistence.mongodb.contextual_config_repository_impl import MongoContextualConfigRepository
from ....infrastructure.persistence.mongodb.interface_config_repository_impl import MongoInterfaceConfigRepository
from ....infrastructure.config.database import get_database
from .auth_dependencies import get_current_user
from ...utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/contextual-config", tags=["Contextual Config"])

# Dependency para obtener instancia de use cases
def get_contextual_config_use_cases() -> ContextualConfigUseCases:
    """Dependency para obtener instancia de use cases contextuales"""
    db = get_database()
    contextual_repo = MongoContextualConfigRepository(db)
    interface_repo = MongoInterfaceConfigRepository(db)
    return ContextualConfigUseCases(contextual_repo, interface_repo)

@router.get("/effective/{user_id}")
async def get_effective_config(
    user_id: str,
    user_role: Optional[str] = Query(None, description="Rol del usuario"),
    org_id: Optional[str] = Query(None, description="ID de la organización"),
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Obtener configuración efectiva para un usuario siguiendo la jerarquía de contextos
    
    Jerarquía: user > role > org > global
    
    Requiere: Usuario autenticado (puede ver su propia config o admin puede ver cualquiera)
    """
    try:
        # Validar permisos: admin puede ver cualquier config, usuario solo la suya
        user_role_name = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role_name not in ["admin", "super_admin"] and current_user.clerk_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propia configuración"
            )

        request = EffectiveConfigRequestDTO(
            user_id=user_id,
            user_role=user_role,
            org_id=org_id
        )

        effective_config = await use_cases.get_effective_config(request)
        
        if not effective_config:
            raise HTTPException(
                status_code=404,
                detail="No se encontró configuración efectiva para el usuario"
            )

        return effective_config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective config for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user_config(
    user_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Obtener configuración específica de un usuario (no resuelve herencia)
    
    Requiere: Usuario autenticado (puede ver su propia config o admin puede ver cualquiera)
    """
    try:
        # Validar permisos
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role not in ["admin", "super_admin"] and current_user.clerk_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes acceder a tu propia configuración"
            )

        config = await use_cases.get_user_config(user_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="No se encontró configuración específica para el usuario"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user config for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/{user_id}")
async def create_or_update_user_config(
    user_id: str,
    config_data: ContextualConfigCreateDTO,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Crear o actualizar configuración específica de un usuario
    
    Requiere: Usuario autenticado (puede modificar su propia config o admin puede modificar cualquiera)
    """
    try:
        # Validar permisos
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role not in ["admin", "super_admin"] and current_user.clerk_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes modificar tu propia configuración"
            )

        # Validar que el contexto sea de usuario y coincida con el user_id
        if config_data.context.context_type != "user" or config_data.context.context_id != user_id:
            raise HTTPException(
                status_code=400,
                detail="El contexto debe ser de tipo 'user' y coincidir con el user_id"
            )

        logger.info(f"User config creation/update for {user_id} by {current_user.email}")

        # Verificar si ya existe configuración para el usuario
        existing_config = await use_cases.get_user_config(user_id)
        
        if existing_config:
            # Actualizar existente
            update_dto = ContextualConfigUpdateDTO(
                config=config_data.config,
                is_active=config_data.is_active
            )
            result = await use_cases.update_contextual_config(
                existing_config.id,
                update_dto,
                updated_by=current_user.clerk_id
            )
        else:
            # Crear nueva
            result = await use_cases.create_contextual_config(
                config_data,
                created_by=current_user.clerk_id
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating user config for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/role/{role_name}")
async def get_role_config(
    role_name: str,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Obtener configuración específica de un rol
    
    Requiere: Usuario autenticado con rol de administrador
    """
    try:
        # Validar permisos de admin
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )

        config = await use_cases.get_role_config(role_name)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró configuración para el rol {role_name}"
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role config for {role_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_contextual_config(
    config_data: ContextualConfigCreateDTO,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Crear nueva configuración contextual
    
    Requiere: Usuario autenticado con permisos según el tipo de contexto
    """
    try:
        # Validar permisos según el tipo de contexto
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        
        if config_data.context.context_type in ["role", "org", "global"]:
            # Solo admins pueden crear configs de role, org o global
            if user_role not in ["admin", "super_admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Se requieren permisos de administrador para este tipo de contexto"
                )
        elif config_data.context.context_type == "user":
            # Usuario puede crear su propia config, admin puede crear cualquiera
            if user_role not in ["admin", "super_admin"] and current_user.clerk_id != config_data.context.context_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes crear configuración para tu propio usuario"
                )

        logger.info(f"Contextual config creation: {config_data.context.context_type}:{config_data.context.context_id} by {current_user.email}")

        result = await use_cases.create_contextual_config(
            config_data,
            created_by=current_user.clerk_id
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contextual config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_contextual_configs(
    context_type: Optional[str] = Query(None, description="Tipo de contexto"),
    context_id: Optional[str] = Query(None, description="ID del contexto"),
    active_only: bool = Query(True, description="Solo configuraciones activas"),
    created_by: Optional[str] = Query(None, description="Creado por usuario"),
    page: int = Query(1, ge=1, description="Página"),
    size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Buscar configuraciones contextuales con filtros y paginación
    
    Requiere: Usuario autenticado (admin ve todo, usuario solo sus propias configs)
    """
    try:
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        
        # Si no es admin, solo puede ver sus propias configuraciones de usuario
        if user_role not in ["admin", "super_admin"]:
            context_type = "user"
            context_id = current_user.clerk_id

        search_params = ContextualConfigSearchDTO(
            context_type=context_type,
            context_id=context_id,
            active_only=active_only,
            created_by=created_by,
            page=page,
            size=size
        )

        result = await use_cases.search_contextual_configs(search_params)
        return result

    except Exception as e:
        logger.error(f"Error searching contextual configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{config_id}")
async def get_contextual_config_by_id(
    config_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Obtener configuración contextual por ID
    
    Requiere: Usuario autenticado con permisos apropiados
    """
    try:
        config = await use_cases.get_contextual_config_by_id(config_id)
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail="Configuración no encontrada"
            )

        # Validar permisos: admin ve todo, usuario solo su propia config
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role not in ["admin", "super_admin"]:
            if config.context.context_type == "user" and config.context.context_id != current_user.clerk_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver esta configuración"
                )
            elif config.context.context_type != "user":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver configuraciones de este tipo"
                )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting contextual config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{config_id}")
async def update_contextual_config(
    config_id: str,
    config_data: ContextualConfigUpdateDTO,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Actualizar configuración contextual existente
    
    Requiere: Usuario autenticado con permisos apropiados
    """
    try:
        # Obtener configuración existente para validar permisos
        existing_config = await use_cases.get_contextual_config_by_id(config_id)
        
        if not existing_config:
            raise HTTPException(
                status_code=404,
                detail="Configuración no encontrada"
            )

        # Validar permisos
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        
        if existing_config.context.context_type in ["role", "org", "global"]:
            if user_role not in ["admin", "super_admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Se requieren permisos de administrador"
                )
        elif existing_config.context.context_type == "user":
            if user_role not in ["admin", "super_admin"] and current_user.clerk_id != existing_config.context.context_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes modificar tu propia configuración"
                )

        logger.info(f"Contextual config update: {config_id} by {current_user.email}")

        result = await use_cases.update_contextual_config(
            config_id,
            config_data,
            updated_by=current_user.clerk_id
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail="Configuración no encontrada"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contextual config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{config_id}")
async def delete_contextual_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Eliminar configuración contextual
    
    Requiere: Usuario autenticado con permisos apropiados
    """
    try:
        # Obtener configuración para validar permisos
        existing_config = await use_cases.get_contextual_config_by_id(config_id)
        
        if not existing_config:
            raise HTTPException(
                status_code=404,
                detail="Configuración no encontrada"
            )

        # Validar permisos
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        
        if existing_config.context.context_type in ["role", "org", "global"]:
            if user_role not in ["admin", "super_admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Se requieren permisos de administrador"
                )
        elif existing_config.context.context_type == "user":
            if user_role not in ["admin", "super_admin"] and current_user.clerk_id != existing_config.context.context_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo puedes eliminar tu propia configuración"
                )

        logger.info(f"Contextual config deletion: {config_id} by {current_user.email}")

        success = await use_cases.delete_contextual_config(config_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Configuración no encontrada"
            )

        return {"message": "Configuración eliminada correctamente", "config_id": config_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contextual config {config_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/{user_id}/preferences")
async def save_user_preferences(
    user_id: str,
    preferences: UserPreferencesDTO,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Guardar preferencias simplificadas de usuario
    
    Endpoint simplificado para configuraciones rápidas de usuario
    """
    try:
        # Validar permisos
        user_role = current_user.role.get("name") if current_user.role else current_user.role_name
        if user_role not in ["admin", "super_admin"] and current_user.clerk_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes modificar tus propias preferencias"
            )

        # Validar que el user_id coincida
        if preferences.user_id != user_id:
            preferences.user_id = user_id

        logger.info(f"User preferences update for {user_id} by {current_user.email}")

        result = await use_cases.save_user_preferences(preferences)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user preferences for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ENDPOINTS ADICIONALES PARA FRONTEND
# ========================================

@router.get("/permissions/global")
async def check_global_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    Verificar si el usuario actual puede modificar configuraciones globales
    Frontend endpoint para detectar permisos de admin global
    """
    try:
        logger.info(f"Checking global permissions for {current_user.email}")
        
        # Verificar si el usuario tiene permisos de super_admin
        user_role_name = current_user.role.get("name") if current_user.role else current_user.role_name
        can_modify = (
            user_role_name in ["super_admin", "admin"] and
            current_user.is_active
        )
        
        return {"can_modify": can_modify}
        
    except Exception as e:
        logger.error(f"Error checking global permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def save_user_preferences_simple(
    preferences: UserPreferencesDTO,
    current_user: User = Depends(get_current_user),
    use_cases: ContextualConfigUseCases = Depends(get_contextual_config_use_cases)
):
    """
    Endpoint simplificado para guardar preferencias del usuario actual
    Compatible con frontend que envía POST /preferences
    """
    try:
        # Usar el ID del usuario actual autenticado
        preferences.user_id = current_user.clerk_id
        
        logger.info(f"User preferences update for current user {current_user.email}")
        
        result = await use_cases.save_user_preferences(preferences)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))