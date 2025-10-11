"""
Base mapper para conversiones de entidades a documentos MongoDB
Proporciona funcionalidad común para todos los mappers específicos
"""

from typing import Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class BaseMapper:
    """Mapper base con utilidades comunes para conversiones"""
    
    @staticmethod
    def safe_decimal_to_float(value: Decimal) -> float:
        """Convertir Decimal a float de forma segura"""
        return float(value) if value is not None else None
    
    @staticmethod
    def safe_float_to_decimal(value: float) -> Decimal:
        """Convertir float a Decimal de forma segura"""
        return Decimal(str(value)) if value is not None else None
    
    @staticmethod
    def safe_date_to_string(value: datetime) -> str:
        """Convertir fecha a string ISO de forma segura"""
        return value.isoformat() if value is not None else None
    
    @staticmethod
    def safe_string_to_date(value: str) -> datetime:
        """Convertir string ISO a fecha de forma segura"""
        return datetime.fromisoformat(value) if value is not None else None
    
    @staticmethod
    def safe_enum_to_value(enum_obj) -> str:
        """Extraer valor de enum de forma segura"""
        return enum_obj.value if enum_obj is not None else None
    
    @staticmethod
    def handle_mapping_error(entity_name: str, operation: str, error: Exception) -> None:
        """Manejo centralizado de errores de mapeo"""
        logger.error(f"Error en {operation} de {entity_name}: {error}")
        raise ValueError(f"Error mapeando {entity_name}: {str(error)}")