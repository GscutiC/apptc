"""
Adaptadores de persistencia para Techo Propio
"""

# Usar el repositorio REFACTORIZADO con arquitectura modular
from .mongo_techo_propio_repository import MongoTechoPropioRepository

__all__ = [
    'MongoTechoPropioRepository'
]