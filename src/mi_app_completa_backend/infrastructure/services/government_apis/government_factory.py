"""
Factory Pattern para gestión centralizada de APIs Gubernamentales
Permite crear instancias de servicios de manera dinámica y escalable
"""

from typing import Dict, Type, List
import logging

from .base_government_api import BaseGovernmentAPI, APIProvider
from .reniec_service import ReniecService
from .sunat_service import SunatService

logger = logging.getLogger(__name__)


class GovernmentAPIFactory:
    """
    Factory para crear y gestionar instancias de APIs gubernamentales
    
    Esta clase centraliza la creación de servicios, facilitando:
    - Agregar nuevos servicios sin modificar código existente
    - Gestión centralizada de configuraciones
    - Instanciación bajo demanda de servicios
    """
    
    # Registro de servicios disponibles
    _services: Dict[APIProvider, Type[BaseGovernmentAPI]] = {
        APIProvider.RENIEC: ReniecService,
        APIProvider.SUNAT: SunatService,
        # Futuros servicios se registran aquí:
        # APIProvider.SUNARP: SunarpService,
        # APIProvider.MIGRACIONES: MigracionesService,
    }
    
    # Cache de instancias (singleton pattern)
    _instances: Dict[APIProvider, BaseGovernmentAPI] = {}
    
    @classmethod
    def create_service(
        cls, 
        provider: APIProvider, 
        use_cache: bool = True
    ) -> BaseGovernmentAPI:
        """
        Crear instancia del servicio solicitado
        
        Args:
            provider: Proveedor de API a instanciar
            use_cache: Si True, reutiliza instancia existente (singleton)
            
        Returns:
            Instancia del servicio de API
            
        Raises:
            ValueError: Si el proveedor no está soportado
        """
        # Verificar si el proveedor está registrado
        if provider not in cls._services:
            available = ", ".join([p.value for p in cls._services.keys()])
            raise ValueError(
                f"Provider '{provider.value}' no está soportado. "
                f"Proveedores disponibles: {available}"
            )
        
        # Si se usa caché y ya existe una instancia, retornarla
        if use_cache and provider in cls._instances:
            logger.debug(f"📦 [Factory] Reutilizando instancia de {provider.value}")
            return cls._instances[provider]
        
        # Crear nueva instancia
        logger.info(f"🏭 [Factory] Creando nueva instancia de {provider.value}")
        service_class = cls._services[provider]
        instance = service_class()
        
        # Guardar en caché si se solicita
        if use_cache:
            cls._instances[provider] = instance
        
        return instance
    
    @classmethod
    def get_available_providers(cls) -> List[APIProvider]:
        """
        Obtener lista de proveedores disponibles
        
        Returns:
            Lista de proveedores de API registrados
        """
        return list(cls._services.keys())
    
    @classmethod
    def get_available_providers_names(cls) -> List[str]:
        """
        Obtener nombres de proveedores disponibles
        
        Returns:
            Lista de nombres de proveedores
        """
        return [provider.value for provider in cls._services.keys()]
    
    @classmethod
    def register_service(
        cls, 
        provider: APIProvider, 
        service_class: Type[BaseGovernmentAPI]
    ) -> None:
        """
        Registrar un nuevo servicio en el factory
        
        Args:
            provider: Identificador del proveedor
            service_class: Clase del servicio que implementa BaseGovernmentAPI
        """
        if not issubclass(service_class, BaseGovernmentAPI):
            raise TypeError(
                f"La clase {service_class.__name__} debe heredar de BaseGovernmentAPI"
            )
        
        cls._services[provider] = service_class
        logger.info(f"✅ [Factory] Servicio {provider.value} registrado exitosamente")
    
    @classmethod
    def clear_cache(cls) -> None:
        """Limpiar caché de instancias"""
        cls._instances.clear()
        logger.info("🗑️ [Factory] Caché de instancias limpiado")
    
    @classmethod
    def get_service_info(cls, provider: APIProvider) -> Dict[str, any]:
        """
        Obtener información sobre un servicio específico
        
        Args:
            provider: Proveedor del que se quiere información
            
        Returns:
            Diccionario con información del servicio
        """
        if provider not in cls._services:
            return {
                "disponible": False,
                "error": f"Proveedor {provider.value} no registrado"
            }
        
        service_class = cls._services[provider]
        instance = cls.create_service(provider, use_cache=True)
        
        return {
            "disponible": True,
            "provider": provider.value,
            "class_name": service_class.__name__,
            "timeout": instance.get_timeout(),
            "cache_ttl": instance.get_cache_ttl(),
            "endpoints": len(instance.api_endpoints),
            "backup_endpoints": len(instance.backup_endpoints)
        }
    
    @classmethod
    async def health_check_all(cls) -> Dict[str, any]:
        """
        Verificar estado de todos los servicios registrados
        
        Returns:
            Diccionario con el estado de cada servicio
        """
        results = {}
        
        for provider in cls.get_available_providers():
            try:
                service = cls.create_service(provider, use_cache=True)
                health = await service.health_check()
                results[provider.value] = health
            except Exception as e:
                results[provider.value] = {
                    "disponible": False,
                    "error": str(e)
                }
        
        return {
            "total_services": len(cls._services),
            "services": results
        }


# Función auxiliar para facilitar la creación de servicios
def get_government_service(provider_name: str) -> BaseGovernmentAPI:
    """
    Función helper para obtener un servicio por nombre
    
    Args:
        provider_name: Nombre del proveedor (ej: "reniec", "sunat")
        
    Returns:
        Instancia del servicio
        
    Example:
        >>> service = get_government_service("reniec")
        >>> result = await service.query_document("12345678")
    """
    try:
        provider = APIProvider(provider_name.lower())
        return GovernmentAPIFactory.create_service(provider)
    except ValueError as e:
        available = GovernmentAPIFactory.get_available_providers_names()
        raise ValueError(
            f"Proveedor '{provider_name}' no válido. "
            f"Opciones: {', '.join(available)}"
        )
