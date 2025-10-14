"""
Rutas API para la configuración visual del módulo Techo Propio
Endpoints protegidos con autenticación JWT de Clerk
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from ....application.use_cases.techo_propio_config_use_cases import TechoPropioConfigUseCases
from ....application.dto.techo_propio_config_dto import (
    TechoPropioConfigCreateDTO,
    TechoPropioConfigResponseDTO,
    TechoPropioConfigUpdateDTO
)
from ....domain.entities.auth_models import User
from .auth_dependencies import get_current_user
from ...config.database import get_database
from ....infrastructure.persistence.mongodb.techo_propio_config_repository_impl import MongoTechoPropioConfigRepository
from ....domain.repositories.techo_propio_config_repository import TechoPropioConfigRepository

router = APIRouter(
    prefix="/api/techo-propio/config",
    tags=["Techo Propio - Configuración Visual"]
)


def get_config_repository(db=Depends(get_database)) -> TechoPropioConfigRepository:
    """Dependencia: Obtener repositorio de configuración"""
    return MongoTechoPropioConfigRepository(db)


def get_use_cases(
    config_repo: TechoPropioConfigRepository = Depends(get_config_repository)
) -> TechoPropioConfigUseCases:
    """Dependencia: Obtener casos de uso"""
    return TechoPropioConfigUseCases(config_repo)


@router.get(
    "",
    response_model=TechoPropioConfigResponseDTO,
    summary="Obtener configuración del usuario actual",
    description="""
    Obtiene la configuración visual del módulo Techo Propio del usuario autenticado.

    - **user_id** se extrae automáticamente del token JWT (no se envía en la petición)
    - Si no existe configuración personalizada, retorna la configuración por defecto
    - Cada usuario solo puede ver su propia configuración

    **Seguridad:** El user_id siempre se toma del token JWT, no del query/body.
    """
)
async def get_my_config(
    current_user: Annotated[User, Depends(get_current_user)],
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
) -> TechoPropioConfigResponseDTO:
    """
    GET /api/techo-propio/config

    Obtiene la configuración del usuario actual
    """
    try:
        config = await use_cases.get_user_config(current_user.clerk_id)

        if not config:
            # No tiene configuración personalizada, retornar default
            return use_cases.get_default_config()

        return config

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener configuración: {str(e)}"
        )


@router.post(
    "",
    response_model=TechoPropioConfigResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Guardar/actualizar configuración del usuario",
    description="""
    Guarda o actualiza la configuración visual del módulo Techo Propio.

    - **user_id** se extrae automáticamente del token JWT (ignorado si viene en el body)
    - Si ya existe configuración, la actualiza
    - Si no existe, crea una nueva
    - Cada usuario solo puede modificar su propia configuración

    **Validaciones:**
    - Colores deben ser hexadecimales válidos (ej: #16A34A)
    - Sidebar icon no puede estar vacío
    - Textos de branding deben tener longitud mínima/máxima

    **Seguridad:** NUNCA se usa el user_id del body, siempre del JWT.
    """
)
async def save_my_config(
    config_data: TechoPropioConfigCreateDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
) -> TechoPropioConfigResponseDTO:
    """
    POST /api/techo-propio/config

    Guarda/actualiza la configuración del usuario actual
    IMPORTANTE: user_id viene del JWT, NO del body
    """
    try:
        # SEGURIDAD: Siempre usar clerk_id del token JWT, no del body
        saved_config = await use_cases.save_user_config(
            user_id=current_user.clerk_id,  # ← Del JWT, no del body
            config_data=config_data
        )

        return saved_config

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar configuración: {str(e)}"
        )


@router.put(
    "",
    response_model=TechoPropioConfigResponseDTO,
    summary="Actualizar parcialmente configuración",
    description="""
    Actualiza parcialmente la configuración del usuario (solo los campos enviados).

    - Solo actualiza los campos que vienen en el body
    - Los campos no enviados mantienen su valor actual
    - user_id se extrae del token JWT

    **Ejemplo:** Si solo envías `colors`, solo se actualizan los colores.
    """
)
async def update_my_config(
    config_data: TechoPropioConfigUpdateDTO,
    current_user: Annotated[User, Depends(get_current_user)],
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
) -> TechoPropioConfigResponseDTO:
    """
    PUT /api/techo-propio/config

    Actualiza parcialmente la configuración del usuario actual
    """
    try:
        updated_config = await use_cases.update_user_config(
            user_id=current_user.clerk_id,
            config_data=config_data
        )

        if not updated_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró configuración para actualizar"
            )

        return updated_config

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar configuración: {str(e)}"
        )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Eliminar configuración (reset a default)",
    description="""
    Elimina la configuración personalizada del usuario (reset a valores por defecto).

    - Elimina la configuración de la base de datos
    - El frontend aplicará automáticamente la configuración por defecto
    - user_id se extrae del token JWT

    **Nota:** Esta acción es reversible (el usuario puede crear una nueva configuración).
    """
)
async def delete_my_config(
    current_user: Annotated[User, Depends(get_current_user)],
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
):
    """
    DELETE /api/techo-propio/config

    Elimina la configuración del usuario actual (reset a default)
    """
    try:
        success = await use_cases.delete_user_config(current_user.clerk_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró configuración para eliminar"
            )

        return {
            "message": "Configuración eliminada exitosamente",
            "detail": "La configuración por defecto se aplicará automáticamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar configuración: {str(e)}"
        )


@router.get(
    "/exists",
    response_model=dict,
    summary="Verificar si existe configuración personalizada",
    description="""
    Verifica si el usuario tiene configuración personalizada.

    - Retorna `{"exists": true}` si tiene configuración
    - Retorna `{"exists": false}` si usa la configuración por defecto
    """
)
async def check_config_exists(
    current_user: Annotated[User, Depends(get_current_user)],
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
):
    """
    GET /api/techo-propio/config/exists

    Verifica si el usuario tiene configuración personalizada
    """
    try:
        exists = await use_cases.config_exists(current_user.clerk_id)
        return {"exists": exists}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar configuración: {str(e)}"
        )


@router.get(
    "/default",
    response_model=TechoPropioConfigResponseDTO,
    summary="Obtener configuración por defecto",
    description="""
    Retorna la configuración por defecto del módulo (sin guardar en BD).

    - Útil para preview o reset temporal
    - No requiere que el usuario tenga configuración guardada
    """
)
async def get_default_config(
    use_cases: Annotated[TechoPropioConfigUseCases, Depends(get_use_cases)]
) -> TechoPropioConfigResponseDTO:
    """
    GET /api/techo-propio/config/default

    Obtiene la configuración por defecto (no requiere autenticación)
    """
    return use_cases.get_default_config()
