"""
Router de validaciones para Techo Propio
Maneja validación de DNI y disponibilidad
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from ......application.dto.techo_propio.techo_propio_dto import DniValidationRequestDTO
from ......application.use_cases.techo_propio.techo_propio_use_cases import TechoPropioUseCases
from .....dependencies.techo_propio_dependencies import get_techo_propio_use_cases
from ...auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Techo Propio - Validaciones"])


@router.post(
    "/validate/dni",
    summary="Validar DNI con RENIEC",
    description="Valida un DNI consultando el servicio RENIEC"
)
async def validate_dni(
    validation_data: DniValidationRequestDTO,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Validar DNI con RENIEC
    
    Retorna:
    - is_valid: bool - Si el DNI es válido
    - names: str - Nombres completos
    - paternal_surname: str - Apellido paterno
    - maternal_surname: str - Apellido materno
    - full_name: str - Nombre completo
    - birth_date: date - Fecha de nacimiento
    """
    try:
        logger.info(f"Validando DNI: {validation_data.dni}")
        
        result = await use_cases.validate_dni(validation_data)
        
        # Log de confirmación
        if result.is_valid:
            logger.info(f"✅ Validación DNI exitosa: {validation_data.dni} - {result.full_name}")
        else:
            logger.warning(f"⚠️ Validación DNI fallida: {validation_data.dni} - {result.error_message}")
        
        # Formato compatible con frontend
        return {
            "success": result.is_valid,
            "data": {
                "dni": result.dni,
                "is_valid": result.is_valid,
                "names": result.names,
                "paternal_surname": result.paternal_surname,
                "maternal_surname": result.maternal_surname,
                "full_name": result.full_name,
                "birth_date": result.birth_date.isoformat() if result.birth_date else None,
                "error_message": result.error_message,
                "validation_date": result.validation_date.isoformat() if result.validation_date else None
            },
            "message": "Validación completada" if result.is_valid else result.error_message or "DNI no válido"
        }
        
    except Exception as e:
        logger.error(f"❌ Error validando DNI {validation_data.dni}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en validación: {str(e)}"
        )


@router.get(
    "/validate/dni/{document_number}/availability",
    summary="Verificar disponibilidad de DNI",
    description="Verifica si un DNI ya está registrado en una solicitud activa"
)
async def check_dni_availability(
    document_number: str,
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Verificar si un DNI está disponible para una nueva solicitud
    
    Retorna:
    - is_available: bool - Si el DNI está disponible
    - reason: str - Razón si no está disponible
    """
    try:
        logger.info(f"Verificando disponibilidad DNI: {document_number}")
        
        result = await use_cases.check_dni_availability(document_number)
        
        return {
            "success": True,
            "data": {
                "dni": document_number,
                "is_available": result.is_available,
                "reason": result.reason,
                "existing_application_id": result.existing_application_id
            },
            "message": "DNI disponible" if result.is_available else result.reason
        }
        
    except Exception as e:
        logger.error(f"❌ Error verificando disponibilidad DNI {document_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando disponibilidad: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check del módulo de validaciones"
)
async def validations_health():
    """Health check"""
    return {
        "status": "healthy",
        "module": "validations",
        "endpoints": [
            "POST /validate/dni",
            "GET /validate/dni/{document_number}/availability"
        ]
    }
