"""
Configuración de dependencias para Techo Propio
Maneja dependency injection y configuración de servicios
"""

from functools import lru_cache
from fastapi import Depends

# Importar repositorio MongoDB
from ..persistence.techo_propio import MongoTechoPropioRepository
from ..persistence.mongodb.ubigeo_repository_impl import MongoUbigeoRepository

# Importar casos de uso
from ...application.use_cases.techo_propio import TechoPropioUseCases
from ...application.use_cases.techo_propio.convocation_management_use_cases import ConvocationManagementUseCases

# Importar servicios
from ..services.government_apis.reniec_service import ReniecService
from ..services.government_apis.ubigeo_validation_service import UbigeoValidationService

# Importar configuración de base de datos
from ..config.database import get_database

# Importar repositorio de convocatorias MongoDB
from ..persistence.mongo_convocation_repository import MongoConvocationRepository


def get_mongo_techo_propio_repository() -> MongoTechoPropioRepository:
    """
    Crear instancia del repositorio MongoDB
    NOTA: No usar @lru_cache porque causa problemas con AsyncIOMotorCollection
    en contextos async. Cada llamada crea una nueva instancia.
    """
    return MongoTechoPropioRepository()


def get_mongo_ubigeo_repository() -> MongoUbigeoRepository:
    """
    Crear instancia del repositorio UBIGEO MongoDB
    Inyecta la conexión a la base de datos
    """
    db = get_database()
    return MongoUbigeoRepository(db)


def get_reniec_service() -> ReniecService:
    """
    Obtener instancia del servicio RENIEC
    Reutiliza el servicio existente del sistema
    """
    return ReniecService()


def get_ubigeo_validation_service(
    ubigeo_repository: MongoUbigeoRepository = Depends(get_mongo_ubigeo_repository)
) -> UbigeoValidationService:
    """
    Crear instancia del servicio de validación UBIGEO
    Inyecta el repositorio MongoDB
    """
    return UbigeoValidationService(ubigeo_repository=ubigeo_repository)


def get_convocation_repository() -> MongoConvocationRepository:
    """
    Crear instancia del repositorio de convocatorias
    Usado para operaciones relacionadas con convocatorias
    """
    return MongoConvocationRepository()


def get_techo_propio_use_cases(
    repository: MongoTechoPropioRepository = Depends(get_mongo_techo_propio_repository),
    convocation_repository: MongoConvocationRepository = Depends(get_convocation_repository),
    reniec_service: ReniecService = Depends(get_reniec_service),
    ubigeo_service: UbigeoValidationService = Depends(get_ubigeo_validation_service)
) -> TechoPropioUseCases:
    """
    Crear instancia del orquestador de casos de uso
    Inyecta todas las dependencias necesarias
    """
    return TechoPropioUseCases(
        repository=repository,
        convocation_repository=convocation_repository,
        reniec_service=reniec_service,
        ubigeo_service=ubigeo_service
    )


def get_convocation_use_cases() -> ConvocationManagementUseCases:
    """
    Crear instancia de casos de uso de convocatorias
    Usando MongoDB para persistencia real
    """
    mongo_repo = MongoConvocationRepository()
    return ConvocationManagementUseCases(repository=mongo_repo)


# Función auxiliar para limpiar cache en tests
def clear_dependency_cache():
    """Limpiar cache de dependencias (útil para testing)"""
    get_mongo_techo_propio_repository.cache_clear()
    get_mongo_ubigeo_repository.cache_clear()
    get_reniec_service.cache_clear()