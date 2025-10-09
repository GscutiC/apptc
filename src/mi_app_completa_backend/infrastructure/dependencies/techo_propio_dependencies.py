"""
Configuración de dependencias para Techo Propio
Maneja dependency injection y configuración de servicios
"""

from functools import lru_cache
from fastapi import Depends

# Importar repositorio MongoDB
from ..persistence.techo_propio import MongoTechoPropioRepository

# Importar casos de uso
from ...application.use_cases.techo_propio import TechoPropioUseCases

# Importar servicios externos existentes
from ..services.government_apis.reniec_service import ReniecService

# Importar configuración de base de datos
from ..config.database import get_database


@lru_cache()
def get_mongo_techo_propio_repository() -> MongoTechoPropioRepository:
    """
    Crear instancia del repositorio MongoDB
    Se cachea para reutilizar la misma instancia
    """
    return MongoTechoPropioRepository()


@lru_cache()
def get_reniec_service() -> ReniecService:
    """
    Obtener instancia del servicio RENIEC
    Reutiliza el servicio existente del sistema
    """
    return ReniecService()


def get_techo_propio_use_cases(
    repository: MongoTechoPropioRepository = Depends(get_mongo_techo_propio_repository),
    reniec_service: ReniecService = Depends(get_reniec_service)
) -> TechoPropioUseCases:
    """
    Crear instancia del orquestador de casos de uso
    Inyecta todas las dependencias necesarias
    """
    return TechoPropioUseCases(
        repository=repository,
        reniec_service=reniec_service
    )


# Función auxiliar para limpiar cache en tests
def clear_dependency_cache():
    """Limpiar cache de dependencias (útil para testing)"""
    get_mongo_techo_propio_repository.cache_clear()
    get_reniec_service.cache_clear()