"""
Entidades del dominio para APIs Gubernamentales
"""
from .reniec_entity import DniData, DniConsultaResponse
from .sunat_entity import RucData, RucConsultaResponse
from .base_entity import GovernmentAPIResponse, DocumentType

__all__ = [
    'DniData',
    'DniConsultaResponse',
    'RucData',
    'RucConsultaResponse',
    'GovernmentAPIResponse',
    'DocumentType'
]
