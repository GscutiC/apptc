"""
Rutas de API para solicitudes Techo Propio - Versión Producción
Implementación limpia sin código híbrido/fallback
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Optional, List
import logging

from ......application.dto.techo_propio import (
    TechoPropioApplicationCreateDTO,
    TechoPropioApplicationUpdateDTO,
    TechoPropioApplicationResponseDTO,
    ApplicationStatusUpdateDTO,
    ApplicationSearchFiltersDTO,
    PaginatedResponseDTO
)
from ......application.use_cases.techo_propio import TechoPropioUseCases
from ......domain.entities.auth_models import User
from ......domain.value_objects.techo_propio import ApplicationStatus
from .....dependencies.techo_propio_dependencies import get_techo_propio_use_cases
from ...auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["Techo Propio - Aplicaciones"])


# ==================== HEALTH CHECK ====================

@router.get(
    "/health",
    summary="Health check del módulo",
    description="Verifica el estado del módulo Techo Propio"
)
async def applications_health():
    """Endpoint de salud del módulo de aplicaciones"""
    return {
        "status": "healthy",
        "module": "techo_propio_applications",
        "version": "1.0.0-production",
        "mode": "production",
        "capabilities": {
            "crud": "enabled",
            "reniec_validation": "enabled",
            "ubigeo_validation": "enabled",
            "statistics": "enabled",
            "export": "enabled"
        }
    }


# ==================== CREATE ====================

@router.post(
    "/",
    response_model=TechoPropioApplicationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva solicitud",
    description="Crea una nueva solicitud Techo Propio con validaciones completas"
)
async def create_application(
    application_data: TechoPropioApplicationCreateDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """
    Crear nueva solicitud Techo Propio

    - Valida DNI con RENIEC
    - Valida UBIGEO
    - Aplica reglas de negocio
    - Persiste en MongoDB
    """
    logger.info(f"[API] Usuario {current_user.email} (ID: {current_user.clerk_id}) creando solicitud")
    
    # 🐛 DEBUG: Mostrar datos recibidos
    logger.info(f"📥 Datos recibidos:")
    logger.info(f"  - convocation_code: {application_data.convocation_code}")
    logger.info(f"  - main_applicant DNI: {application_data.main_applicant.document_number}")
    logger.info(f"  - property_info distrito: {application_data.property_info.district}")
    logger.info(f"  - household_members: {len(application_data.household_members) if application_data.household_members else 0} miembros")

    try:
        response = await use_cases.create_application(
            dto=application_data,
            user_id=current_user.clerk_id
        )

        logger.info(f"✅ Solicitud creada exitosamente: {response.id} por usuario {current_user.clerk_id}")
        return response

    except ValueError as e:
        logger.warning(f"Validación fallida: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Error creando solicitud: {e}", exc_info=True)
        logger.error(f"Tipo de error: {type(e).__name__}")
        logger.error(f"Detalles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al crear solicitud: {str(e)}"
        )


# ==================== READ ====================

@router.get(
    "/",
    response_model=PaginatedResponseDTO,
    summary="Listar solicitudes",
    description="Lista solicitudes con filtros y paginación"
)
async def list_applications(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    status_filter: Optional[ApplicationStatus] = Query(None, description="Filtrar por estado"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    province: Optional[str] = Query(None, description="Filtrar por provincia"),
    district: Optional[str] = Query(None, description="Filtrar por distrito"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Lista solicitudes del usuario con filtros opcionales"""
    logger.info(f"[API] Usuario {current_user.email} listando solicitudes (página {page})")

    try:
        # Obtener solicitudes
        offset = (page - 1) * page_size
        response = await use_cases.get_applications_by_user(
            user_id=current_user.clerk_id,
            status=status_filter,
            limit=page_size,
            offset=offset
        )

        logger.info(f"✅ {response.total_count} solicitudes encontradas")
        return response

    except Exception as e:
        logger.error(f"Error listando solicitudes: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al listar solicitudes"
        )


@router.get(
    "/{application_id}",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Obtener solicitud por ID",
    description="Obtiene una solicitud específica por su ID"
)
async def get_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtiene una solicitud específica por ID"""
    logger.info(f"[API] Usuario {current_user.email} consultando solicitud: {application_id}")

    try:
        response = await use_cases.get_application_by_id(
            application_id=application_id,
            user_id=current_user.clerk_id
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud {application_id} no encontrada"
            )

        logger.info(f"✅ Solicitud {application_id} encontrada")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo solicitud: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener solicitud"
        )


# ==================== UPDATE ====================

@router.put(
    "/{application_id}",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Actualizar solicitud",
    description="Actualiza una solicitud existente"
)
async def update_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    application_data: TechoPropioApplicationUpdateDTO = None,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Actualiza una solicitud existente"""
    logger.info(f"[API] Usuario {current_user.email} actualizando solicitud: {application_id}")

    try:
        response = await use_cases.update_application(
            application_id=application_id,
            dto=application_data,
            user_id=current_user.clerk_id
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud {application_id} no encontrada"
            )

        logger.info(f"✅ Solicitud {application_id} actualizada")
        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validación fallida: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error actualizando solicitud: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar solicitud"
        )


# ==================== DELETE ====================

@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar solicitud",
    description="Elimina (soft delete) una solicitud"
)
async def delete_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Elimina una solicitud (soft delete)"""
    logger.info(f"[API] Usuario {current_user.email} eliminando solicitud: {application_id}")

    try:
        success = await use_cases.delete_application(
            application_id=application_id,
            user_id=current_user.clerk_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud {application_id} no encontrada"
            )

        logger.info(f"✅ Solicitud {application_id} eliminada")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando solicitud: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar solicitud"
        )


# ==================== STATUS MANAGEMENT ====================

@router.patch(
    "/{application_id}/status",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Cambiar estado de solicitud",
    description="Cambia el estado de una solicitud"
)
async def change_application_status(
    application_id: str = Path(..., description="ID de la solicitud"),
    status_update: ApplicationStatusUpdateDTO = None,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Cambia el estado de una solicitud"""
    logger.info(f"[API] Usuario {current_user.email} cambiando estado de solicitud: {application_id}")

    try:
        response = await use_cases.change_application_status(
            application_id=application_id,
            new_status=status_update.new_status,
            comment=status_update.comment,
            user_id=current_user.clerk_id
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud {application_id} no encontrada"
            )

        logger.info(f"✅ Estado de solicitud {application_id} cambiado a {status_update.new_status}")
        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Cambio de estado inválido: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cambiando estado: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al cambiar estado"
        )


# ==================== SEARCH ====================

@router.get(
    "/search/",
    response_model=PaginatedResponseDTO,
    summary="Búsqueda avanzada",
    description="Busca solicitudes con múltiples criterios"
)
async def search_applications(
    query: Optional[str] = Query(None, description="Texto de búsqueda"),
    status_filter: Optional[ApplicationStatus] = Query(None, description="Estado"),
    department: Optional[str] = Query(None, description="Departamento"),
    province: Optional[str] = Query(None, description="Provincia"),
    district: Optional[str] = Query(None, description="Distrito"),
    min_priority: Optional[int] = Query(None, ge=0, le=100, description="Prioridad mínima"),
    max_priority: Optional[int] = Query(None, ge=0, le=100, description="Prioridad máxima"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Búsqueda avanzada de solicitudes"""
    logger.info(f"[API] Usuario {current_user.email} realizando búsqueda: {query}")

    try:
        filters = ApplicationSearchFiltersDTO(
            search_text=query,
            status=status_filter,
            department=department,
            province=province,
            district=district,
            priority_min=min_priority,
            priority_max=max_priority,
            page=page,
            page_size=page_size
        )

        offset = (page - 1) * page_size
        response = await use_cases.search_applications(
            filters=filters,
            user_id=current_user.clerk_id,
            limit=page_size,
            offset=offset
        )

        logger.info(f"✅ Búsqueda completada: {response.total_count} resultados")
        return response

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en búsqueda"
        )


# ==================== STATISTICS ====================

@router.get(
    "/statistics/summary",
    summary="Estadísticas de solicitudes",
    description="Obtiene estadísticas agregadas de solicitudes"
)
async def get_statistics(
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtiene estadísticas de solicitudes"""
    logger.info(f"[API] Usuario {current_user.email} consultando estadísticas")

    try:
        stats = await use_cases.get_statistics(
            user_id=current_user.clerk_id,
            department=department
        )

        logger.info("✅ Estadísticas obtenidas")
        return stats

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al obtener estadísticas"
        )
