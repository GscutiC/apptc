"""
Casos de uso unificados para consultas gubernamentales
Orquesta las consultas a diferentes APIs gubernamentales con caché y auditoría
"""

import logging
from datetime import datetime
from typing import Optional

from ..dto.government_dto import (
    DniQueryRequest,
    RucQueryRequest,
    QueryMetadata
)
from ...domain.entities.government_apis import (
    DniConsultaResponse,
    RucConsultaResponse
)
from ...infrastructure.services.government_apis import (
    GovernmentAPIFactory,
    APIProvider,
    DocumentValidationException,
    APIUnavailableException
)

logger = logging.getLogger(__name__)


class GovernmentQueriesUseCase:
    """
    Caso de uso unificado para consultas gubernamentales
    
    Responsabilidades:
    - Orquestar consultas a diferentes APIs
    - Gestionar caché de consultas
    - Auditar todas las consultas
    - Manejar errores de forma consistente
    """
    
    def __init__(
        self,
        cache_service=None,  # Opcional: servicio de caché (Redis, Memcached, etc.)
        audit_service=None   # Opcional: servicio de auditoría
    ):
        """
        Inicializar caso de uso
        
        Args:
            cache_service: Servicio de caché (opcional)
            audit_service: Servicio de auditoría (opcional)
        """
        self.factory = GovernmentAPIFactory()
        self.cache = cache_service
        self.audit = audit_service
    
    async def query_dni(
        self,
        dni: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> DniConsultaResponse:
        """
        Consultar DNI con caché y auditoría
        
        Args:
            dni: DNI de 8 dígitos
            user_id: ID del usuario que realiza la consulta (opcional)
            use_cache: Si usar caché (default: True)
            
        Returns:
            DniConsultaResponse con los datos de la persona
        """
        cache_key = f"dni:{dni}"
        
        try:
            logger.info(f"🔍 [UseCase] Consultando DNI: {dni}")
            
            # 1. Verificar caché si está habilitado
            if use_cache and self.cache:
                cached = await self._get_from_cache(cache_key)
                if cached:
                    logger.info(f"✅ [UseCase] DNI {dni} encontrado en caché")
                    cached.cache_hit = True
                    await self._audit_query("DNI", dni, user_id, True, "cache")
                    return cached
            
            # 2. Consultar API
            service = self.factory.create_service(APIProvider.RENIEC)
            result = await service.query_document(dni)
            
            # 3. Guardar en caché si la consulta fue exitosa
            if result.success and use_cache and self.cache:
                await self._save_to_cache(
                    cache_key,
                    result,
                    ttl=service.get_cache_ttl()
                )
                logger.info(f"💾 [UseCase] DNI {dni} guardado en caché")
            
            # 4. Auditar consulta
            await self._audit_query("DNI", dni, user_id, result.success, result.fuente)
            
            logger.info(f"✅ [UseCase] Consulta DNI {dni} completada: {result.success}")
            return result
            
        except DocumentValidationException as e:
            logger.error(f"❌ [UseCase] Validación fallida DNI {dni}: {e}")
            await self._audit_query("DNI", dni, user_id, False, "validation_error")
            raise
            
        except APIUnavailableException as e:
            logger.error(f"❌ [UseCase] API no disponible para DNI {dni}: {e}")
            await self._audit_query("DNI", dni, user_id, False, "api_unavailable")
            raise
            
        except Exception as e:
            logger.error(f"❌ [UseCase] Error consultando DNI {dni}: {e}")
            await self._audit_query("DNI", dni, user_id, False, "error")
            raise
    
    async def query_ruc(
        self,
        ruc: str,
        user_id: Optional[str] = None,
        use_cache: bool = True
    ) -> RucConsultaResponse:
        """
        Consultar RUC con caché y auditoría
        
        Args:
            ruc: RUC de 11 dígitos
            user_id: ID del usuario que realiza la consulta (opcional)
            use_cache: Si usar caché (default: True)
            
        Returns:
            RucConsultaResponse con los datos de la empresa
        """
        cache_key = f"ruc:{ruc}"
        
        try:
            logger.info(f"🔍 [UseCase] Consultando RUC: {ruc}")
            
            # 1. Verificar caché si está habilitado
            if use_cache and self.cache:
                cached = await self._get_from_cache(cache_key)
                if cached:
                    logger.info(f"✅ [UseCase] RUC {ruc} encontrado en caché")
                    cached.cache_hit = True
                    await self._audit_query("RUC", ruc, user_id, True, "cache")
                    return cached
            
            # 2. Consultar API
            service = self.factory.create_service(APIProvider.SUNAT)
            result = await service.query_document(ruc)
            
            # 3. Guardar en caché si la consulta fue exitosa
            if result.success and use_cache and self.cache:
                await self._save_to_cache(
                    cache_key,
                    result,
                    ttl=service.get_cache_ttl()
                )
                logger.info(f"💾 [UseCase] RUC {ruc} guardado en caché")
            
            # 4. Auditar consulta
            await self._audit_query("RUC", ruc, user_id, result.success, result.fuente)
            
            logger.info(f"✅ [UseCase] Consulta RUC {ruc} completada: {result.success}")
            return result
            
        except DocumentValidationException as e:
            logger.error(f"❌ [UseCase] Validación fallida RUC {ruc}: {e}")
            await self._audit_query("RUC", ruc, user_id, False, "validation_error")
            raise
            
        except APIUnavailableException as e:
            logger.error(f"❌ [UseCase] API no disponible para RUC {ruc}: {e}")
            await self._audit_query("RUC", ruc, user_id, False, "api_unavailable")
            raise
            
        except Exception as e:
            logger.error(f"❌ [UseCase] Error consultando RUC {ruc}: {e}")
            await self._audit_query("RUC", ruc, user_id, False, "error")
            raise
    
    async def get_available_providers(self) -> dict:
        """
        Obtener lista de proveedores disponibles
        
        Returns:
            Diccionario con información de proveedores
        """
        providers = self.factory.get_available_providers_names()
        
        return {
            "total": len(providers),
            "providers": providers,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> dict:
        """
        Verificar estado de todos los servicios
        
        Returns:
            Estado de salud de todos los servicios
        """
        return await self.factory.health_check_all()
    
    # Métodos auxiliares privados
    
    async def _get_from_cache(self, key: str):
        """Obtener valor del caché"""
        if not self.cache:
            return None
        
        try:
            return await self.cache.get(key)
        except Exception as e:
            logger.warning(f"⚠️ [UseCase] Error obteniendo caché {key}: {e}")
            return None
    
    async def _save_to_cache(self, key: str, value: any, ttl: int):
        """Guardar valor en caché"""
        if not self.cache:
            return
        
        try:
            await self.cache.set(key, value, ttl=ttl)
        except Exception as e:
            logger.warning(f"⚠️ [UseCase] Error guardando caché {key}: {e}")
    
    async def _audit_query(
        self,
        document_type: str,
        document_number: str,
        user_id: Optional[str],
        success: bool,
        source: Optional[str]
    ):
        """Auditar consulta"""
        if not self.audit:
            return
        
        try:
            await self.audit.log_query(
                document_type=document_type,
                document_number=document_number,
                user_id=user_id,
                success=success,
                source=source,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.warning(f"⚠️ [UseCase] Error auditando consulta: {e}")


# Función helper para crear instancia del caso de uso
def create_government_queries_use_case(
    cache_service=None,
    audit_service=None
) -> GovernmentQueriesUseCase:
    """
    Factory function para crear instancia del caso de uso
    
    Args:
        cache_service: Servicio de caché opcional
        audit_service: Servicio de auditoría opcional
        
    Returns:
        Instancia de GovernmentQueriesUseCase
    """
    return GovernmentQueriesUseCase(
        cache_service=cache_service,
        audit_service=audit_service
    )
