"""
Endpoints FastAPI para el módulo Techo Propio
Maneja todas las operaciones HTTP con documentación OpenAPI
"""

from typing import Optional, List, Dict, Any
from datetime import date
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Request
from fastapi.responses import JSONResponse

# Configurar logger
logger = logging.getLogger(__name__)

# Importar DTOs
from .....application.dto.techo_propio import (
    TechoPropioApplicationCreateDTO,
    TechoPropioApplicationUpdateDTO,
    TechoPropioApplicationResponseDTO,
    ApplicationStatusUpdateDTO,
    ApplicationSearchFiltersDTO,
    PaginatedResponseDTO,
    DniValidationRequestDTO,
    DniValidationResponseDTO,
    ApplicantValidationDTO,
    UbigeoValidationRequestDTO,
    UbigeoValidationResponseDTO,
    LocationSearchRequestDTO
)

# Importar casos de uso
from .....application.use_cases.techo_propio import TechoPropioUseCases

# Importar value objects
from .....domain.value_objects.techo_propio import ApplicationStatus

# Importar dependencias
from ....dependencies.techo_propio_dependencies import get_techo_propio_use_cases
from ..auth_dependencies import get_current_user

# Importar entidades de auth
from .....domain.entities.auth_models import User


# Crear router
router = APIRouter(
    prefix="/api/techo-propio",
    tags=["Techo Propio"],
    responses={
        404: {"description": "Recurso no encontrado"},
        422: {"description": "Error de validación"},
        500: {"description": "Error interno del servidor"}
    }
)


# ==================== ENDPOINTS DE SOLICITUDES ====================

@router.post(
    "/applications",
    response_model=TechoPropioApplicationResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva solicitud",
    description="Crea una nueva solicitud para el programa Techo Propio"
)
async def create_application(
    request: Request,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    # TEMPORALMENTE DESHABILITADO PARA DIAGNÓSTICO
    # current_user = Depends(get_current_user)  # Remover tipo dict, es un objeto User
):
    """Crear nueva solicitud Techo Propio"""
    try:
        # Obtener datos raw del request
        raw_data = await request.json()
        logger.info(f"🔍 Datos recibidos en el backend: {raw_data}")
        
        # Intentar parsear el DTO
        try:
            application_data = TechoPropioApplicationCreateDTO(**raw_data)
            logger.info("✅ DTO parseado correctamente")
        except Exception as parse_error:
            logger.error(f"❌ Error parseando DTO: {parse_error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Error de validación: {str(parse_error)}"
            )
        result = await use_cases.create_application(
            dto=application_data,
            user_id="test_user_temp"  # TEMPORAL para diagnóstico
        )
        
        # Log de respuesta exitosa
        logger.info(f"✅ Solicitud creada exitosamente - ID: {result.id}")
        logger.info(f"📋 Respuesta completa: {result.model_dump() if hasattr(result, 'model_dump') else str(result)}")
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/applications/{application_id}",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Obtener solicitud por ID",
    description="Obtiene los detalles de una solicitud específica"
)
async def get_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener solicitud por ID"""
    result = await use_cases.get_application_by_id(
        application_id=application_id,
        user_id=current_user.clerk_id  # Usar clerk_id, no user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    return result


@router.put(
    "/applications/{application_id}",
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
    """Actualizar solicitud existente"""
    try:
        result = await use_cases.update_application(
            application_id=application_id,
            dto=application_data,
            user_id=current_user.clerk_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.patch(
    "/applications/{application_id}/status",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Actualizar estado de solicitud",
    description="Actualiza el estado de una solicitud (requiere permisos administrativos)"
)
async def update_application_status(
    application_id: str = Path(..., description="ID de la solicitud"),
    status_data: ApplicationStatusUpdateDTO = None,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Actualizar estado de solicitud"""
    try:
        # TODO: Validar permisos administrativos
        result = await use_cases.update_application_status(
            application_id=application_id,
            dto=status_data,
            user_id=current_user.clerk_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post(
    "/applications/{application_id}/submit",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Enviar solicitud",
    description="Envía una solicitud para revisión"
)
async def submit_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Enviar solicitud para revisión"""
    try:
        result = await use_cases.submit_application(
            application_id=application_id,
            user_id=current_user.clerk_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.delete(
    "/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar solicitud",
    description="Elimina una solicitud en borrador"
)
async def delete_application(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Eliminar solicitud (solo borradores)"""
    try:
        success = await use_cases.delete_application(
            application_id=application_id,
            user_id=current_user.clerk_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
        
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# ==================== ENDPOINTS DE CONSULTA ====================

@router.get(
    "/applications/user/{user_id}",
    response_model=PaginatedResponseDTO[TechoPropioApplicationResponseDTO],
    summary="Obtener solicitudes de usuario",
    description="Obtiene todas las solicitudes de un usuario específico"
)
async def get_user_applications(
    user_id: str = Path(..., description="ID del usuario"),
    status_filter: Optional[ApplicationStatus] = Query(None, description="Filtrar por estado"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener solicitudes de un usuario"""
    try:
        result = await use_cases.get_applications_by_user(
            user_id=user_id,
            status_filter=status_filter,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/applications/search",
    response_model=PaginatedResponseDTO[TechoPropioApplicationResponseDTO],
    summary="Búsqueda avanzada de solicitudes",
    description="Realiza búsqueda avanzada con múltiples filtros"
)
async def search_applications(
    search_term: Optional[str] = Query(None, description="Término de búsqueda"),
    status: Optional[ApplicationStatus] = Query(None, description="Filtrar por estado"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    province: Optional[str] = Query(None, description="Filtrar por provincia"),
    district: Optional[str] = Query(None, description="Filtrar por distrito"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    min_monthly_income: Optional[float] = Query(None, description="Ingreso mínimo"),
    max_monthly_income: Optional[float] = Query(None, description="Ingreso máximo"),
    has_spouse: Optional[bool] = Query(None, description="Tiene cónyuge"),
    has_disability: Optional[bool] = Query(None, description="Tiene discapacidad"),
    sort_by: Optional[str] = Query("created_at", description="Campo de ordenamiento"),
    sort_order: Optional[str] = Query("desc", description="Orden (asc/desc)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Búsqueda avanzada de solicitudes"""
    try:
        filters = ApplicationSearchFiltersDTO(
            search_term=search_term,
            status=status,
            department=department,
            province=province,
            district=district,
            date_from=date_from,
            date_to=date_to,
            min_monthly_income=min_monthly_income,
            max_monthly_income=max_monthly_income,
            has_spouse=has_spouse,
            has_disability=has_disability,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        result = await use_cases.search_applications(
            filters=filters,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/applications/dni/{document_number}",
    response_model=TechoPropioApplicationResponseDTO,
    summary="Obtener solicitud por DNI",
    description="Busca una solicitud por el DNI del solicitante principal"
)
async def get_application_by_dni(
    document_number: str = Path(..., description="Número de DNI"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener solicitud por DNI"""
    result = await use_cases.get_application_by_dni(document_number)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró solicitud para el DNI especificado"
        )
    
    return result


@router.get(
    "/applications/status/{status}",
    response_model=PaginatedResponseDTO[TechoPropioApplicationResponseDTO],
    summary="Obtener solicitudes por estado",
    description="Obtiene todas las solicitudes con un estado específico"
)
async def get_applications_by_status(
    status: ApplicationStatus = Path(..., description="Estado de las solicitudes"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    sort_by: str = Query("created_at", description="Campo de ordenamiento"),
    sort_order: str = Query("desc", description="Orden (asc/desc)"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """Obtener solicitudes por estado"""
    try:
        result = await use_cases.get_applications_by_status(
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/applications/priority",
    response_model=PaginatedResponseDTO[TechoPropioApplicationResponseDTO],
    summary="Obtener solicitudes prioritarias",
    description="Obtiene solicitudes ordenadas por puntaje de prioridad"
)
async def get_priority_applications(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
    min_priority_score: Optional[float] = Query(None, description="Puntaje mínimo de prioridad"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Obtener solicitudes prioritarias"""
    try:
        result = await use_cases.get_priority_applications(
            page=page,
            page_size=page_size,
            min_priority_score=min_priority_score
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# ==================== ENDPOINTS DE ESTADÍSTICAS ====================

@router.get(
    "/statistics",
    summary="Obtener estadísticas",
    description="Obtiene estadísticas detalladas de las solicitudes"
)
async def get_statistics(
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    date_from: Optional[date] = Query(None, description="Fecha desde"),
    date_to: Optional[date] = Query(None, description="Fecha hasta"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Obtener estadísticas"""
    try:
        result = await use_cases.get_application_statistics(
            department=department,
            date_from=date_from,
            date_to=date_to
        )
        
        # ✅ DEVOLVER ESTADÍSTICAS O VALORES POR DEFECTO
        return {
            "success": True,
            "data": result or {
                "total_applications": 0,
                "status_breakdown": {},
                "avg_priority_score": 0.0,
                "total_income": 0.0,
                "unique_departments": 0
            }
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return {
            "success": False,
            "data": {
                "total_applications": 0,
                "status_breakdown": {},
                "avg_priority_score": 0.0,
                "total_income": 0.0,
                "unique_departments": 0
            },
            "error": f"Error interno: {str(e)}"
        }


@router.get(
    "/dashboard",
    response_model=Dict[str, Any],
    summary="Obtener resumen de dashboard",
    description="Obtiene resumen para dashboard de usuario o administrador"
)
async def get_dashboard_summary(
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Obtener resumen de dashboard"""
    try:
        # TODO: Determinar si el usuario es administrador
        is_admin = current_user.get("role") == "admin"
        
        result = await use_cases.get_dashboard_summary(
            user_id=current_user["user_id"],
            is_admin=is_admin
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# ==================== ENDPOINTS DE VALIDACIÓN ====================

@router.post(
    "/validate/dni",
    summary="Validar DNI",
    description="Valida un DNI con el servicio RENIEC"
)
async def validate_dni(
    validation_data: DniValidationRequestDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Validar DNI con RENIEC"""
    try:
        result = await use_cases.validate_dni(validation_data)
        
        # Log de confirmación de funcionamiento
        if result.is_valid:
            logger.info(f"Validación DNI exitosa: {validation_data.dni}")
        
        # Formato compatible con frontend
        response = {
            "success": result.is_valid,
            "data": {
                "dni": result.dni,
                "is_valid": result.is_valid,
                "names": result.names,
                "paternal_surname": result.paternal_surname,
                "maternal_surname": result.maternal_surname,
                "full_name": result.full_name,
                "birth_date": result.birth_date,
                "error_message": result.error_message,
                "validation_date": result.validation_date.isoformat() if result.validation_date else None
            },
            "error": result.error_message if not result.is_valid else None
        }
        
        return response
    except Exception as e:
        logger.error(f"Error validando DNI: {str(e)}")
        return {
            "success": False,
            "error": f"Error validando DNI: {str(e)}"
        }


@router.post(
    "/validate/applicant",
    response_model=DniValidationResponseDTO,
    summary="Validar datos de solicitante",
    description="Valida datos completos de un solicitante"
)
async def validate_applicant(
    validation_data: ApplicantValidationDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Validar datos de solicitante"""
    try:
        result = await use_cases.validate_applicant_data(validation_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando solicitante: {str(e)}"
        )


@router.post(
    "/validate/ubigeo",
    response_model=UbigeoValidationResponseDTO,
    summary="Validar código UBIGEO",
    description="Valida un código UBIGEO"
)
async def validate_ubigeo(
    validation_data: UbigeoValidationRequestDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Validar código UBIGEO"""
    try:
        result = await use_cases.validate_ubigeo_code(validation_data.ubigeo_code)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando UBIGEO: {str(e)}"
        )


@router.get(
    "/validate/dni/{document_number}/availability",
    response_model=Dict[str, bool],
    summary="Verificar disponibilidad de DNI",
    description="Verifica si un DNI está disponible para registro"
)
async def check_dni_availability(
    document_number: str = Path(..., description="Número de DNI"),
    exclude_application_id: Optional[str] = Query(None, description="ID de solicitud a excluir"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Verificar disponibilidad de DNI"""
    try:
        is_available = await use_cases.check_dni_availability(
            document_number=document_number,
            exclude_application_id=exclude_application_id
        )
        return {"is_available": is_available}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando DNI: {str(e)}"
        )


# ==================== ENDPOINTS DE UBICACIÓN ====================

@router.get(
    "/locations/departments",
    response_model=List[Dict[str, str]],
    summary="Obtener departamentos",
    description="Obtiene lista de departamentos disponibles con códigos"
)
async def get_departments(
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases)
):
    """Obtener lista de departamentos con códigos"""
    try:
        result = await use_cases.get_departments_with_codes()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo departamentos: {str(e)}"
        )


@router.get(
    "/locations/provinces/{department}",
    response_model=List[Dict[str, str]],
    summary="Obtener provincias",
    description="Obtiene provincias de un departamento con códigos"
)
async def get_provinces(
    department: str = Path(..., description="Nombre del departamento"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases)
):
    """Obtener provincias de un departamento con códigos"""
    try:
        print(f"🔍 [PROVINCES] Solicitud recibida para departamento: '{department}'")
        result = await use_cases.get_provinces_with_codes(department)
        print(f"✅ [PROVINCES] Resultado obtenido: {len(result)} provincias para '{department}'")
        print(f"📊 [PROVINCES] Datos: {result}")
        return result
    except Exception as e:
        print(f"❌ [PROVINCES] Error para departamento '{department}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo provincias: {str(e)}"
        )


@router.get(
    "/locations/districts/{department}/{province}",
    response_model=List[Dict[str, str]],
    summary="Obtener distritos",
    description="Obtiene distritos de una provincia con códigos"
)
async def get_districts(
    department: str = Path(..., description="Nombre del departamento"),
    province: str = Path(..., description="Nombre de la provincia"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases)
):
    """Obtener distritos de una provincia con códigos"""
    try:
        print(f"🔍 [DISTRICTS] Solicitud recibida para: '{department}' > '{province}'")
        result = await use_cases.get_districts_with_codes(department, province)
        print(f"✅ [DISTRICTS] Resultado obtenido: {len(result)} distritos para '{department}' > '{province}'")
        print(f"📊 [DISTRICTS] Datos: {result}")
        return result
    except Exception as e:
        print(f"❌ [DISTRICTS] Error para '{department}' > '{province}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo distritos: {str(e)}"
        )


@router.get(
    "/locations/search",
    response_model=List[Dict[str, Any]],
    summary="Buscar ubicaciones",
    description="Busca ubicaciones por término"
)
async def search_locations(
    search_term: str = Query(..., description="Término de búsqueda"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases)
):
    """Buscar ubicaciones"""
    try:
        result = await use_cases.search_locations(search_term, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buscando ubicaciones: {str(e)}"
        )


# ==================== ENDPOINTS AUXILIARES ====================

@router.get(
    "/applications/{application_id}/completion",
    response_model=Dict[str, Any],
    summary="Obtener estado de completitud",
    description="Obtiene el estado de completitud de una solicitud"
)
async def get_application_completion(
    application_id: str = Path(..., description="ID de la solicitud"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """Obtener estado de completitud de solicitud"""
    try:
        result = await use_cases.get_application_completion_status(application_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


# ==================== ENDPOINTS FALTANTES ====================

@router.get(
    "/applications",
    summary="Obtener lista de solicitudes",
    description="Obtiene lista paginada de solicitudes con filtros opcionales"
)
async def get_applications(
    # Filtros opcionales
    status: Optional[List[ApplicationStatus]] = Query(None, description="Filtrar por estado(s)"),
    department: Optional[str] = Query(None, description="Filtrar por departamento"),
    province: Optional[str] = Query(None, description="Filtrar por provincia"),
    district: Optional[str] = Query(None, description="Filtrar por distrito"),
    priority_min: Optional[float] = Query(None, description="Puntaje mínimo de prioridad"),
    priority_max: Optional[float] = Query(None, description="Puntaje máximo de prioridad"),
    created_from: Optional[date] = Query(None, description="Fecha de creación desde"),
    created_to: Optional[date] = Query(None, description="Fecha de creación hasta"),

    # Paginación
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros"),

    # Autenticación
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de solicitudes con filtros opcionales

    Este endpoint permite:
    - Filtrar por estado, ubicación, prioridad y fechas
    - Paginación mediante skip y limit
    - Obtener todas las solicitudes (admin) o solo las del usuario

    Returns:
        Formato frontend-compatible: { success: true, data: { items, total_count, ... } }
    """
    try:
        # Calcular página y tamaño de página desde skip/limit
        page = (skip // limit) + 1 if limit > 0 else 1
        page_size = limit

        logger.info(f"📥 Solicitud GET /applications - Usuario: {current_user.clerk_id}")
        logger.info(f"   Filtros: status={status}, dept={department}, prov={province}, dist={district}")
        logger.info(f"   Paginación: page={page}, page_size={page_size}")

        # Construir filtros para búsqueda avanzada
        filters = ApplicationSearchFiltersDTO(
            status=status[0] if status and len(status) > 0 else None,  # Tomar primer estado si hay múltiples
            department=department,
            province=province,
            district=district,
            min_priority_score=priority_min,
            max_priority_score=priority_max,
            date_from=created_from,
            date_to=created_to,
            sort_by="created_at",
            sort_order="desc"
        )

        # TODO: Verificar permisos - si es admin puede ver todas, sino solo las propias
        # Por ahora, devolver todas las solicitudes
        result = await use_cases.search_applications(
            filters=filters,
            page=page,
            page_size=page_size
        )

        logger.info(f"✅ Solicitudes encontradas: {result.total_count} (página {result.page}/{result.total_pages})")

        # ✅ Retornar formato compatible con frontend
        return {
            "success": True,
            "data": {
                "items": result.items,
                "total_count": result.total_count,
                "page": result.page,
                "page_size": result.page_size,
                "total_pages": result.total_pages
            }
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo solicitudes: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Error obteniendo solicitudes: {str(e)}",
            "data": {
                "items": [],
                "total_count": 0,
                "page": 1,
                "page_size": limit,
                "total_pages": 0
            }
        }


# ENDPOINTS DUPLICADOS ELIMINADOS
# Los endpoints de ubicaciones (/locations/departments, /locations/provinces, /locations/districts)
# ya están definidos en la sección "ENDPOINTS DE UBICACIÓN" (líneas 612-702)
# El endpoint de estadísticas (/statistics) ya está definido en la sección
# "ENDPOINTS DE ESTADÍSTICAS" (líneas 421-464)