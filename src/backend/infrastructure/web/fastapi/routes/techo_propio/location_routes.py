"""
Router de ubicaciones para Techo Propio
Maneja departamentos, provincias y distritos (Ubigeo)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
import logging

from ......application.use_cases.techo_propio.techo_propio_use_cases import TechoPropioUseCases
from .....dependencies.techo_propio_dependencies import get_techo_propio_use_cases
from ...auth_dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Techo Propio - Ubicaciones"])


@router.get(
    "/locations/departments",
    summary="Listar departamentos",
    description="Obtiene la lista completa de departamentos del Perú"
)
async def get_departments(
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar todos los departamentos
    
    Retorna:
    - Lista de departamentos con código y nombre
    """
    try:
        logger.info("Obteniendo lista de departamentos")
        
        # Usar get_departments_with_codes para obtener código y nombre
        departments = await use_cases.get_departments_with_codes()
        
        logger.info(f"{len(departments)} departamentos encontrados")
        
        return {
            "success": True,
            "data": departments,
            "message": f"{len(departments)} departamentos disponibles"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo departamentos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo departamentos: {str(e)}"
        )


@router.get(
    "/locations/provinces",
    summary="Listar provincias",
    description="Obtiene las provincias de un departamento específico"
)
async def get_provinces(
    department_code: str = Query(..., description="Código del departamento (2 dígitos)"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar provincias de un departamento
    
    Parámetros:
    - department_code: Código del departamento (ej: "15" para Lima)
    
    Retorna:
    - Lista de provincias con código y nombre
    """
    try:
        logger.info(f"Obteniendo provincias del departamento: {department_code}")
        
        # Usar get_provinces_with_codes para obtener código y nombre
        provinces = await use_cases.get_provinces_with_codes(department_code)
        
        logger.info(f"{len(provinces)} provincias encontradas para departamento {department_code}")
        
        return {
            "success": True,
            "data": provinces,
            "message": f"{len(provinces)} provincias disponibles"
        }
        
    except ValueError as e:
        logger.warning(f"Departamento no válido: {department_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo provincias: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo provincias: {str(e)}"
        )


@router.get(
    "/locations/districts",
    summary="Listar distritos",
    description="Obtiene los distritos de una provincia específica"
)
async def get_districts(
    department_code: str = Query(..., description="Código del departamento (2 dígitos)"),
    province_code: str = Query(..., description="Código de la provincia (2 dígitos)"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Listar distritos de una provincia
    
    Parámetros:
    - department_code: Código del departamento (ej: "15")
    - province_code: Código de la provincia (ej: "01")
    
    Retorna:
    - Lista de distritos con código y nombre
    """
    try:
        logger.info(f"Obteniendo distritos: departamento={department_code}, provincia={province_code}")
        
        # Usar get_districts_with_codes para obtener código y nombre
        districts = await use_cases.get_districts_with_codes(department_code, province_code)
        
        logger.info(f"{len(districts)} distritos encontrados")
        
        return {
            "success": True,
            "data": districts,
            "message": f"{len(districts)} distritos disponibles"
        }
        
    except ValueError as e:
        logger.warning(f"Ubicación no válida: dept={department_code}, prov={province_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error obteniendo distritos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo distritos: {str(e)}"
        )


@router.get(
    "/locations/validate-ubigeo",
    summary="Validar código Ubigeo",
    description="Valida si un código Ubigeo (6 dígitos) es válido"
)
async def validate_ubigeo(
    ubigeo_code: str = Query(..., min_length=6, max_length=6, description="Código Ubigeo (6 dígitos)"),
    use_cases: TechoPropioUseCases = Depends(get_techo_propio_use_cases),
    current_user: dict = Depends(get_current_user)
):
    """
    Validar código Ubigeo
    
    Parámetros:
    - ubigeo_code: Código Ubigeo de 6 dígitos (DDPPDD)
    
    Retorna:
    - is_valid: bool
    - location_name: str - Nombre completo de la ubicación
    """
    try:
        logger.info(f"Validando ubigeo: {ubigeo_code}")
        
        # Usar validate_ubigeo_code
        result = await use_cases.validate_ubigeo_code(ubigeo_code)
        
        return {
            "success": True,
            "data": {
                "ubigeo_code": ubigeo_code,
                "is_valid": result.is_valid,
                "department": result.department,
                "province": result.province,
                "district": result.district,
                "location_name": result.location_name
            },
            "message": "Ubigeo válido" if result.is_valid else "Ubigeo no válido"
        }
        
    except Exception as e:
        logger.error(f"Error validando ubigeo {ubigeo_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validando ubigeo: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check del módulo de ubicaciones"
)
async def locations_health():
    """Health check"""
    return {
        "status": "healthy",
        "module": "locations",
        "endpoints": [
            "GET /locations/departments",
            "GET /locations/provinces",
            "GET /locations/districts",
            "GET /locations/validate-ubigeo"
        ]
    }
