"""
Rutas de API REST para consultas gubernamentales
Endpoints modulares y escalables para RENIEC, SUNAT y futuros servicios
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Optional
import logging

from ....application.use_cases.government_queries import (
    GovernmentQueriesUseCase,
    create_government_queries_use_case
)
from ....application.dto.government_dto import (
    DniQueryRequest,
    RucQueryRequest
)
from ....infrastructure.services.government_apis import (
    DocumentValidationException,
    APIUnavailableException,
    GovernmentAPIException
)
from ....domain.entities.auth_models import User
from .auth_dependencies import get_current_user_optional, get_current_user
from ....domain.value_objects.auth_decorators import requires_active_user

logger = logging.getLogger(__name__)

# Router para APIs gubernamentales
router = APIRouter(
    prefix="/api/government",
    tags=["Government APIs"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


# Dependency injection
def get_government_use_case() -> GovernmentQueriesUseCase:
    """
    Dependency para obtener el caso de uso de consultas gubernamentales
    
    TODO: Inyectar servicios de caché y auditoría cuando estén disponibles
    """
    return create_government_queries_use_case(
        cache_service=None,  # TODO: Inyectar servicio de caché
        audit_service=None   # TODO: Inyectar servicio de auditoría
    )


# Endpoints de consulta

@router.get(
    "/dni/{dni}",
    summary="Consultar DNI en RENIEC",
    description="Consulta información de una persona por su número de DNI. Requiere autenticación.",
    response_description="Datos de la persona consultada"
)
async def query_dni(
    dni: str,
    use_cache: bool = Query(default=True, description="Usar caché si está disponible"),
    use_case: GovernmentQueriesUseCase = Depends(get_government_use_case),
    current_user: User = Depends(get_current_user)  # ✅ Autenticación requerida
):
    """
    Consultar información de persona por DNI
    
    **Requiere autenticación**: Sí
    
    - **dni**: DNI de 8 dígitos numéricos
    - **use_cache**: Si usar caché (default: true)
    
    Returns:
        Información completa de la persona si se encuentra
    """
    try:
        logger.info(f"📡 [API] Usuario {current_user.email} consultando DNI: {dni}")
        
        result = await use_case.query_dni(
            dni=dni,
            user_id=current_user.clerk_id,
            use_cache=use_cache
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        return result
        
    except DocumentValidationException as e:
        logger.warning(f"⚠️ [API] Validación fallida DNI {dni}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except APIUnavailableException as e:
        logger.error(f"❌ [API] Servicio no disponible para DNI {dni}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Error consultando DNI {dni}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al consultar DNI"
        )


@router.get(
    "/ruc/{ruc}",
    summary="Consultar RUC en SUNAT",
    description="Consulta información de una empresa por su número de RUC. Requiere autenticación.",
    response_description="Datos de la empresa consultada"
)
async def query_ruc(
    ruc: str,
    use_cache: bool = Query(default=True, description="Usar caché si está disponible"),
    use_case: GovernmentQueriesUseCase = Depends(get_government_use_case),
    current_user: User = Depends(get_current_user)  # ✅ Autenticación requerida
):
    """
    Consultar información de empresa por RUC
    
    **Requiere autenticación**: Sí
    
    - **ruc**: RUC de 11 dígitos numéricos
    - **use_cache**: Si usar caché (default: true)
    
    Returns:
        Información completa de la empresa si se encuentra
    """
    try:
        logger.info(f"📡 [API] Usuario {current_user.email} consultando RUC: {ruc}")
        
        result = await use_case.query_ruc(
            ruc=ruc,
            user_id=current_user.clerk_id,
            use_cache=use_cache
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        return result
        
    except DocumentValidationException as e:
        logger.warning(f"⚠️ [API] Validación fallida RUC {ruc}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except APIUnavailableException as e:
        logger.error(f"❌ [API] Servicio no disponible para RUC {ruc}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"❌ [API] Error consultando RUC {ruc}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al consultar RUC"
        )


# Endpoints de información y estado

@router.get(
    "/providers",
    summary="Listar proveedores disponibles",
    description="Obtiene la lista de APIs gubernamentales disponibles"
)
async def get_providers(
    use_case: GovernmentQueriesUseCase = Depends(get_government_use_case)
):
    """
    Listar todos los proveedores de APIs gubernamentales disponibles
    
    Returns:
        Lista de proveedores registrados (RENIEC, SUNAT, etc.)
    """
    try:
        return await use_case.get_available_providers()
    except Exception as e:
        logger.error(f"❌ [API] Error listando proveedores: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener lista de proveedores"
        )


@router.get(
    "/health",
    summary="Estado de los servicios",
    description="Verifica el estado de salud de todos los servicios de APIs gubernamentales"
)
async def health_check(
    use_case: GovernmentQueriesUseCase = Depends(get_government_use_case)
):
    """
    Verificar estado de salud de todos los servicios
    
    Returns:
        Estado de cada servicio de API gubernamental
    """
    try:
        return await use_case.health_check()
    except Exception as e:
        logger.error(f"❌ [API] Error en health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar estado de servicios"
        )


# Endpoint raíz informativo
@router.get(
    "/",
    summary="Información del módulo",
    description="Información general sobre el módulo de APIs gubernamentales"
)
async def root():
    """
    Información general del módulo de APIs gubernamentales
    """
    return {
        "module": "Government APIs",
        "version": "1.0.0",
        "description": "Módulo modular y escalable para consultas a APIs gubernamentales peruanas",
        "providers": ["RENIEC", "SUNAT"],
        "features": [
            "Consultas con múltiples endpoints de respaldo",
            "Sistema de caché integrado",
            "Auditoría de consultas",
            "Validación robusta de documentos",
            "Arquitectura extensible para nuevas APIs"
        ],
        "endpoints": {
            "dni": "/api/government/dni/{dni}",
            "ruc": "/api/government/ruc/{ruc}",
            "providers": "/api/government/providers",
            "health": "/api/government/health"
        }
    }
