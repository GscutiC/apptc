"""
Rutas de API para gestión de convocatorias Techo Propio
Todos los usuarios autenticados tienen acceso completo (sin restricciones de roles)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
from datetime import datetime

from ......application.dto.techo_propio import (
    ConvocationCreateDTO,
    ConvocationUpdateDTO,
    ConvocationQueryDTO,
    ConvocationResponseDTO,
    ConvocationListResponseDTO,
    ConvocationStatisticsDTO,
    ConvocationGeneralStatsDTO,
    ConvocationOptionDTO,
    ConvExtendDeadlineDTO,
    ConvBulkOperationDTO,
    ConvBulkOperationResultDTO,
)
from ......application.use_cases.techo_propio.convocation_management_use_cases import ConvocationManagementUseCases
from ......domain.entities.auth_models import User
from .....dependencies.techo_propio_dependencies import get_convocation_use_cases
from ...auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/convocations", tags=["Techo Propio - Convocatorias"])


# ==================== HEALTH CHECK ====================

@router.get(
    "/health",
    summary="Health check del módulo de convocatorias",
    description="Verifica el estado del módulo de gestión de convocatorias"
)
async def convocations_health():
    """Endpoint de salud del módulo de convocatorias"""
    return {
        "status": "healthy",
        "module": "techo_propio_convocations",
        "version": "1.0.0",
        "features": {
            "crud": "enabled",
            "bulk_operations": "enabled", 
            "statistics": "enabled",
            "role_restrictions": "disabled"  # Sin restricciones de roles
        }
    }

@router.get(
    "/test",
    summary="Test endpoint sin autenticación"
)
async def test_convocations():
    """Test endpoint súper simple"""
    return {"message": "Test endpoint works", "timestamp": datetime.now().isoformat()}


# ==================== CRUD BÁSICO ====================

@router.post(
    "/",
    response_model=ConvocationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva convocatoria",
    description="Crear nueva convocatoria. Todos los usuarios pueden crear convocatorias."
)
async def create_convocation(
    convocation_data: ConvocationCreateDTO,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Crear nueva convocatoria - Sin restricciones de roles"""
    
    logger.info(f"Usuario {current_user.email} creando convocatoria: {convocation_data.code}")
    logger.info(f"Datos recibidos - start_date type: {type(convocation_data.start_date)}, end_date type: {type(convocation_data.end_date)}")

    try:
        convocation = await use_cases.create_convocation(
            code=convocation_data.code,
            title=convocation_data.title,
            description=convocation_data.description,
            start_date=convocation_data.start_date,
            end_date=convocation_data.end_date,
            user_id=current_user.clerk_id,
            is_active=convocation_data.is_active,
            max_applications=convocation_data.max_applications
        )

        logger.info(f"✅ Convocatoria creada - ID: {convocation.id}, code: {convocation.code}")
        logger.info(f"Convirtiendo a dict...")

        conv_dict = convocation.to_dict()
        logger.info(f"Dict creado exitosamente")

        return ConvocationResponseDTO(**conv_dict)
        
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error interno: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/",
    response_model=ConvocationListResponseDTO,
    summary="Listar convocatorias",
    description="Obtener lista paginada de convocatorias con filtros"
)
async def list_convocations(
    skip: int = Query(default=0, ge=0, description="Registros a omitir"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de registros"),
    include_inactive: bool = Query(default=False, description="Incluir convocatorias inactivas"),
    year: Optional[int] = Query(default=None, ge=2020, le=2030, description="Filtrar por año"),
    search: Optional[str] = Query(default=None, min_length=2, max_length=50, description="Búsqueda por texto"),
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Listar convocatorias - Todos los usuarios pueden ver todas"""
    
    try:
        logger.info(f"Listando convocatorias - user: {current_user.clerk_id}, skip: {skip}, limit: {limit}")
        
        if year:
            logger.info(f"Filtrando por año: {year}")
            convocations = await use_cases.get_convocations_by_year(year)
        else:
            logger.info("Obteniendo todas las convocatorias")
            convocations = await use_cases.get_all_convocations(skip, limit, include_inactive)
        
        # Aplicar filtro de búsqueda si se proporciona
        if search:
            search_lower = search.lower()
            convocations = [
                c for c in convocations
                if search_lower in c.code.lower() or search_lower in c.title.lower()
            ]
        
        # Convertir a DTOs
        convocation_dtos = [
            ConvocationResponseDTO(**conv.to_dict())
            for conv in convocations
        ]
        
        # Calcular paginación
        total = len(convocation_dtos)
        paginated = convocation_dtos[skip:skip + limit] if not year else convocation_dtos
        
        return ConvocationListResponseDTO(
            convocations=paginated,
            total=total,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total,
            has_previous=skip > 0
        )
        
    except Exception as e:
        logger.error(f"Error al listar convocatorias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/active",
    response_model=List[ConvocationOptionDTO],
    summary="Obtener convocatorias activas",
    description="Obtener convocatorias activas para formularios y selects"
)
async def get_active_convocations(
    published_only: bool = Query(default=True, description="Solo convocatorias publicadas"),
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener convocatorias activas para dropdowns"""
    
    try:
        if published_only:
            convocations = await use_cases.get_published_convocations()
        else:
            convocations = await use_cases.get_active_convocations()
        
        return [
            ConvocationOptionDTO.from_convocation(conv)
            for conv in convocations
        ]
        
    except Exception as e:
        logger.error(f"Error al obtener convocatorias activas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get(
    "/{convocation_id}",
    response_model=ConvocationResponseDTO,
    summary="Obtener convocatoria por ID",
    description="Obtener detalles de una convocatoria específica"
)
async def get_convocation(
    convocation_id: str,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener convocatoria por ID"""
    
    try:
        convocation = await use_cases.get_convocation_by_id(convocation_id)
        
        if not convocation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró convocatoria con ID '{convocation_id}'"
            )
        
        return ConvocationResponseDTO(**convocation.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener convocatoria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put(
    "/{convocation_id}",
    response_model=ConvocationResponseDTO,
    summary="Actualizar convocatoria",
    description="Actualizar convocatoria existente. Todos los usuarios pueden actualizar."
)
async def update_convocation(
    convocation_id: str,
    update_data: ConvocationUpdateDTO,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Actualizar convocatoria - Sin restricciones de roles"""
    
    logger.info(f"Usuario {current_user.email} actualizando convocatoria: {convocation_id}")
    
    try:
        # Convertir a dict excluyendo valores None
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
        
        convocation = await use_cases.update_convocation(
            convocation_id=convocation_id,
            user_id=current_user.clerk_id,
            **update_dict
        )
        
        logger.info(f"✅ Convocatoria actualizada: {convocation.code}")
        
        return ConvocationResponseDTO(**convocation.to_dict())
        
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al actualizar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete(
    "/{convocation_id}",
    summary="Eliminar convocatoria",
    description="Eliminar convocatoria (solo si no tiene solicitudes). Todos los usuarios pueden eliminar."
)
async def delete_convocation(
    convocation_id: str,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Eliminar convocatoria - Sin restricciones de roles"""
    
    logger.info(f"Usuario {current_user.email} eliminando convocatoria: {convocation_id}")
    
    try:
        success = await use_cases.delete_convocation(convocation_id, current_user.clerk_id)
        
        if success:
            logger.info(f"✅ Convocatoria eliminada: {convocation_id}")
            return {"message": "Convocatoria eliminada exitosamente"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo eliminar la convocatoria"
            )
            
    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al eliminar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# ==================== OPERACIONES DE ESTADO ====================

@router.patch(
    "/{convocation_id}/activate",
    response_model=ConvocationResponseDTO,
    summary="Activar convocatoria",
    description="Activar una convocatoria específica"
)
async def activate_convocation(
    convocation_id: str,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Activar convocatoria"""
    
    try:
        convocation = await use_cases.activate_convocation(convocation_id, current_user.clerk_id)
        return ConvocationResponseDTO(**convocation.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error al activar convocatoria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.patch(
    "/{convocation_id}/deactivate",
    response_model=ConvocationResponseDTO,
    summary="Desactivar convocatoria",
    description="Desactivar una convocatoria específica"
)
async def deactivate_convocation(
    convocation_id: str,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Desactivar convocatoria"""
    
    try:
        convocation = await use_cases.deactivate_convocation(convocation_id, current_user.clerk_id)
        return ConvocationResponseDTO(**convocation.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error al desactivar convocatoria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.patch(
    "/{convocation_id}/publish",
    response_model=ConvocationResponseDTO,
    summary="Publicar convocatoria",
    description="Publicar convocatoria (hacerla visible en formularios)"
)
async def publish_convocation(
    convocation_id: str,
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Publicar convocatoria"""
    
    try:
        convocation = await use_cases.publish_convocation(convocation_id, current_user.clerk_id)
        return ConvocationResponseDTO(**convocation.to_dict())
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error al publicar convocatoria: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# ==================== UTILIDADES ====================

@router.get(
    "/generate/code",
    summary="Generar código de convocatoria",
    description="Generar automáticamente un código único de convocatoria"
)
async def generate_convocation_code(
    year: Optional[int] = Query(default=None, ge=2020, le=2030, description="Año para el código"),
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Generar código de convocatoria automáticamente"""
    
    try:
        code = await use_cases.generate_convocation_code(year)
        return {"generated_code": code}
        
    except Exception as e:
        logger.error(f"Error al generar código: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


# ==================== ESTADÍSTICAS ====================

@router.get(
    "/stats/general",
    response_model=ConvocationGeneralStatsDTO,
    summary="Estadísticas generales",
    description="Obtener estadísticas generales del módulo de convocatorias"
)
async def get_general_statistics(
    use_cases: ConvocationManagementUseCases = Depends(get_convocation_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas generales"""
    
    try:
        stats = await use_cases.get_general_statistics()
        return ConvocationGeneralStatsDTO(**stats)
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )