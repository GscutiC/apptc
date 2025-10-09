"""
Helper Service para facilitar el uso de APIs Gubernamentales desde cualquier módulo
Proporciona una interfaz simple y conveniente para consultas
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ...application.use_cases.government_queries import (
    GovernmentQueriesUseCase,
    create_government_queries_use_case
)
from ...domain.entities.government_apis import (
    DniConsultaResponse,
    RucConsultaResponse,
    DniData,
    RucData
)
from ...infrastructure.services.government_apis import (
    DocumentValidationException,
    APIUnavailableException
)

logger = logging.getLogger(__name__)


class GovernmentAPIHelper:
    """
    Helper class para simplificar el uso de APIs gubernamentales
    
    Esta clase proporciona métodos convenientes para:
    - Consultar DNI y RUC de manera simple
    - Validar documentos sin hacer consultas
    - Obtener información resumida
    - Manejar errores de forma consistente
    
    Uso:
        helper = GovernmentAPIHelper()
        
        # Consulta simple
        persona = await helper.get_persona_by_dni("12345678")
        
        # Con manejo de errores
        empresa = await helper.get_empresa_by_ruc("20123456789")
        if empresa:
            print(empresa.razon_social)
    """
    
    def __init__(self, cache_service=None, audit_service=None):
        """
        Inicializar helper
        
        Args:
            cache_service: Servicio de caché opcional
            audit_service: Servicio de auditoría opcional
        """
        self.use_case = create_government_queries_use_case(
            cache_service=cache_service,
            audit_service=audit_service
        )
    
    # ============== Métodos Principales ==============
    
    async def get_persona_by_dni(
        self, 
        dni: str, 
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[DniData]:
        """
        Obtener datos de persona por DNI (método simplificado)
        
        Args:
            dni: DNI de 8 dígitos
            user_id: ID del usuario que consulta (opcional)
            use_cache: Usar caché si está disponible
            
        Returns:
            DniData si se encuentra, None si hay error
            
        Example:
            >>> helper = GovernmentAPIHelper()
            >>> persona = await helper.get_persona_by_dni("12345678")
            >>> if persona:
            >>>     print(f"{persona.nombre_completo}")
        """
        try:
            result = await self.use_case.query_dni(dni, user_id, use_cache)
            return result.data if result.success else None
        except Exception as e:
            logger.error(f"Error consultando DNI {dni}: {e}")
            return None
    
    async def get_empresa_by_ruc(
        self,
        ruc: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[RucData]:
        """
        Obtener datos de empresa por RUC (método simplificado)
        
        Args:
            ruc: RUC de 11 dígitos
            user_id: ID del usuario que consulta (opcional)
            use_cache: Usar caché si está disponible
            
        Returns:
            RucData si se encuentra, None si hay error
            
        Example:
            >>> helper = GovernmentAPIHelper()
            >>> empresa = await helper.get_empresa_by_ruc("20123456789")
            >>> if empresa:
            >>>     print(f"{empresa.razon_social} - {empresa.estado}")
        """
        try:
            result = await self.use_case.query_ruc(ruc, user_id, use_cache)
            return result.data if result.success else None
        except Exception as e:
            logger.error(f"Error consultando RUC {ruc}: {e}")
            return None
    
    # ============== Métodos con Response Completo ==============
    
    async def query_dni_full(
        self,
        dni: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> DniConsultaResponse:
        """
        Consultar DNI con respuesta completa (incluye metadatos)
        
        Args:
            dni: DNI de 8 dígitos
            user_id: ID del usuario que consulta
            use_cache: Usar caché
            
        Returns:
            DniConsultaResponse completo con success, message, data, etc.
        """
        return await self.use_case.query_dni(dni, user_id, use_cache)
    
    async def query_ruc_full(
        self,
        ruc: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> RucConsultaResponse:
        """
        Consultar RUC con respuesta completa (incluye metadatos)
        
        Args:
            ruc: RUC de 11 dígitos
            user_id: ID del usuario que consulta
            use_cache: Usar caché
            
        Returns:
            RucConsultaResponse completo con success, message, data, etc.
        """
        return await self.use_case.query_ruc(ruc, user_id, use_cache)
    
    # ============== Métodos de Validación ==============
    
    def validate_dni(self, dni: str) -> bool:
        """
        Validar formato de DNI sin hacer consulta
        
        Args:
            dni: DNI a validar
            
        Returns:
            True si el formato es válido
        """
        if not dni or len(dni) != 8:
            return False
        return dni.isdigit()
    
    def validate_ruc(self, ruc: str) -> bool:
        """
        Validar formato de RUC sin hacer consulta
        
        Args:
            ruc: RUC a validar
            
        Returns:
            True si el formato es válido
        """
        if not ruc or len(ruc) != 11:
            return False
        
        if not ruc.isdigit():
            return False
        
        tipo_contrib = ruc[:2]
        tipos_validos = ["10", "15", "17", "20"]
        return tipo_contrib in tipos_validos
    
    # ============== Métodos de Información ==============
    
    async def get_nombre_completo(
        self,
        dni: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtener solo el nombre completo de una persona
        
        Args:
            dni: DNI de 8 dígitos
            user_id: ID del usuario
            
        Returns:
            Nombre completo o None
        """
        persona = await self.get_persona_by_dni(dni, user_id)
        return persona.nombre_completo if persona else None
    
    async def get_razon_social(
        self,
        ruc: str,
        user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtener solo la razón social de una empresa
        
        Args:
            ruc: RUC de 11 dígitos
            user_id: ID del usuario
            
        Returns:
            Razón social o None
        """
        empresa = await self.get_empresa_by_ruc(ruc, user_id)
        return empresa.razon_social if empresa else None
    
    # ============== Métodos Batch (múltiples consultas) ==============
    
    async def query_multiple_dni(
        self,
        dnis: list[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Optional[DniData]]:
        """
        Consultar múltiples DNIs
        
        Args:
            dnis: Lista de DNIs a consultar
            user_id: ID del usuario
            
        Returns:
            Diccionario con dni como key y DniData como value
        """
        results = {}
        for dni in dnis:
            results[dni] = await self.get_persona_by_dni(dni, user_id)
        return results
    
    async def query_multiple_ruc(
        self,
        rucs: list[str],
        user_id: Optional[str] = None
    ) -> Dict[str, Optional[RucData]]:
        """
        Consultar múltiples RUCs
        
        Args:
            rucs: Lista de RUCs a consultar
            user_id: ID del usuario
            
        Returns:
            Diccionario con ruc como key y RucData como value
        """
        results = {}
        for ruc in rucs:
            results[ruc] = await self.get_empresa_by_ruc(ruc, user_id)
        return results
    
    # ============== Métodos de Utilidad ==============
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar estado de los servicios"""
        return await self.use_case.health_check()
    
    async def get_available_services(self) -> Dict[str, Any]:
        """Obtener servicios disponibles"""
        return await self.use_case.get_available_providers()


# ============== Singleton global (opcional) ==============

_global_helper: Optional[GovernmentAPIHelper] = None


def get_government_helper() -> GovernmentAPIHelper:
    """
    Obtener instancia global del helper (singleton)
    
    Returns:
        Instancia global de GovernmentAPIHelper
        
    Example:
        >>> from infrastructure.services.government_helper import get_government_helper
        >>> helper = get_government_helper()
        >>> persona = await helper.get_persona_by_dni("12345678")
    """
    global _global_helper
    if _global_helper is None:
        _global_helper = GovernmentAPIHelper()
    return _global_helper


# ============== Funciones de conveniencia ==============

async def quick_query_dni(dni: str) -> Optional[DniData]:
    """
    Función de atajo para consultar DNI rápidamente
    
    Example:
        >>> from infrastructure.services.government_helper import quick_query_dni
        >>> persona = await quick_query_dni("12345678")
    """
    helper = get_government_helper()
    return await helper.get_persona_by_dni(dni)


async def quick_query_ruc(ruc: str) -> Optional[RucData]:
    """
    Función de atajo para consultar RUC rápidamente
    
    Example:
        >>> from infrastructure.services.government_helper import quick_query_ruc
        >>> empresa = await quick_query_ruc("20123456789")
    """
    helper = get_government_helper()
    return await helper.get_empresa_by_ruc(ruc)
