"""
techo_propio_routes.py - Versión refactorizada
REEMPLAZA el archivo original de 858 líneas

Este archivo importa el router modular desde el directorio techo_propio/
manteniendo compatibilidad completa con el sistema existente
"""

from fastapi import APIRouter

# Importar router modular refactorizado  
from .techo_propio import router as techo_propio_module_router

# Crear router principal que incluye todos los sub-módulos  
router = APIRouter(prefix="/api/techo-propio", tags=["Techo Propio"])

# Endpoint de salud del módulo principal
@router.get("/health")
async def health_check():
    """Estado de salud del módulo principal"""
    return {
        "status": "healthy",
        "module": "techo_propio",
        "version": "2.0.0-refactored", 
        "message": "Módulo refactorizado funcionando correctamente",
        "integration": "active",
        "sub_modules": {
            "applications": "active",
            "queries": "active", 
            "validations": "active",
            "statistics": "active"
        }
    }

# Incluir el router modular refactorizado
router.include_router(techo_propio_module_router)