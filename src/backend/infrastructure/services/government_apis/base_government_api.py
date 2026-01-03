"""
Interface base abstracta para servicios de APIs gubernamentales
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class APIProvider(str, Enum):
    """Proveedores de APIs gubernamentales"""
    RENIEC = "reniec"
    SUNAT = "sunat"
    SUNARP = "sunarp"
    MIGRACIONES = "migraciones"
    ESSALUD = "essalud"


class BaseGovernmentAPI(ABC):
    """Clase base abstracta para todos los servicios de APIs gubernamentales"""
    
    def __init__(self):
        """Inicializar configuración base del servicio"""
        self.provider: APIProvider
        self.api_endpoints: List[str] = []
        self.backup_endpoints: List[str] = []
        self.timeout: int = 10
        self.max_retries: int = 3
        self.cache_ttl: int = 3600  # 1 hora por defecto
        self.headers: Dict[str, str] = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    @abstractmethod
    def validate_document(self, document: str) -> bool:
        """
        Validar formato del documento según las reglas del proveedor
        
        Args:
            document: Número de documento a validar
            
        Returns:
            bool: True si el documento es válido, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def query_document(self, document: str) -> Dict[str, Any]:
        """
        Consultar documento en la API gubernamental
        
        Args:
            document: Número de documento a consultar
            
        Returns:
            Dict con los datos obtenidos de la API
        """
        pass
    
    @abstractmethod
    def normalize_response(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizar respuesta de la API a un formato estándar
        
        Args:
            raw_data: Datos crudos de la API
            
        Returns:
            Dict con datos normalizados
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Verificar estado del servicio y disponibilidad de endpoints
        
        Returns:
            Dict con información del estado del servicio
        """
        pass
    
    def get_provider_name(self) -> str:
        """Obtener nombre del proveedor"""
        return self.provider.value
    
    def get_cache_ttl(self) -> int:
        """Obtener tiempo de vida del caché"""
        return self.cache_ttl
    
    def get_timeout(self) -> int:
        """Obtener timeout configurado"""
        return self.timeout
    
    async def _try_endpoints(self, document: str) -> Optional[Dict[str, Any]]:
        """
        Intentar consulta en todos los endpoints disponibles
        Método auxiliar para implementaciones concretas
        
        Args:
            document: Documento a consultar
            
        Returns:
            Datos si algún endpoint responde exitosamente, None si todos fallan
        """
        pass


class GovernmentAPIException(Exception):
    """Excepción base para errores de APIs gubernamentales"""
    pass


class DocumentValidationException(GovernmentAPIException):
    """Excepción para errores de validación de documentos"""
    pass


class APIUnavailableException(GovernmentAPIException):
    """Excepción cuando la API no está disponible"""
    pass


class RateLimitException(GovernmentAPIException):
    """Excepción cuando se excede el rate limit"""
    pass
