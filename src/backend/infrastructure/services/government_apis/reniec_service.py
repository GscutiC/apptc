"""
Servicio RENIEC para consultas DNI - Arquitectura Modular
Implementa BaseGovernmentAPI para consultas a RENIEC
"""

import httpx
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .base_government_api import (
    BaseGovernmentAPI, 
    APIProvider,
    DocumentValidationException,
    APIUnavailableException
)
from ....domain.entities.government_apis import DniData, DniConsultaResponse

logger = logging.getLogger(__name__)


class ReniecService(BaseGovernmentAPI):
    """Servicio para consultas reales a RENIEC"""
    
    def __init__(self):
        super().__init__()
        self.provider = APIProvider.RENIEC
        self.api_endpoints = [
            "https://api.apis.net.pe/v1/dni",
            "https://dniruc.apisperu.com/api/v1/dni/",
        ]
        self.backup_endpoints = [
            "https://api.reniec.gob.pe/v1/consulta/",  # Endpoint oficial (si existe)
        ]
        self.timeout = 8
        self.max_retries = 3
        self.cache_ttl = 3600  # 1 hora
    
    def validate_document(self, document: str) -> bool:
        """
        Validar que el DNI tenga el formato correcto
        
        Args:
            document: DNI de 8 dígitos
            
        Returns:
            bool: True si es válido
        """
        if not document or len(document) != 8:
            return False
        
        return document.isdigit()
    
    async def query_document(self, document: str) -> DniConsultaResponse:
        """
        Consulta información de persona por DNI
        
        Args:
            document: DNI de 8 dígitos
            
        Returns:
            DniConsultaResponse: Datos de la persona
        """
        try:
            # Validar DNI
            if not self.validate_document(document):
                logger.error(f"DNI inválido: {document}")
                raise DocumentValidationException(
                    "DNI inválido. Debe tener 8 dígitos numéricos."
                )
            
            # Intentar APIs principales
            for endpoint in self.api_endpoints:
                try:
                    resultado = await self._consultar_api_reniec(document, endpoint)
                    if resultado.success:
                        logger.info(f"Consulta RENIEC exitosa para DNI: {document}")
                        return resultado
                except Exception as e:
                    logger.warning(f"API {endpoint} falló: {str(e)}")
                    continue
            
            # Intentar endpoints de respaldo
            for endpoint in self.backup_endpoints:
                try:
                    resultado = await self._consultar_api_reniec(document, endpoint)
                    if resultado.success:
                        logger.info(f"Consulta RENIEC exitosa para DNI: {document}")
                        return resultado
                except Exception as e:
                    logger.warning(f"API backup {endpoint} falló: {str(e)}")
                    continue
            
            # Si todas las APIs fallan
            logger.error(f"Todas las APIs RENIEC fallaron para DNI: {document}")
            raise APIUnavailableException(
                "No se pudo obtener información del DNI. Servicio RENIEC no disponible."
            )
            
        except DocumentValidationException:
            raise
        except APIUnavailableException:
            raise
        except Exception as e:
            logger.error(f"❌ [RENIEC] Error general para DNI {document}: {e}")
            raise Exception(f"Error en consulta RENIEC: {str(e)}")
    
    async def _consultar_api_reniec(self, dni: str, endpoint: str) -> DniConsultaResponse:
        """Intenta consultar una API real de RENIEC usando httpx async"""
        try:
            # Construir URL según el endpoint
            if "apis.net.pe" in endpoint:
                url = f"{endpoint}?numero={dni}"
            else:
                url = f"{endpoint}{dni}"
            
            # Usar httpx.AsyncClient para requests verdaderamente asíncronos
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                dni_data = self.normalize_response(data)
                
                return DniConsultaResponse(
                    success=True,
                    message="Consulta exitosa",
                    data=dni_data,
                    fuente=f"API Real - {endpoint}",
                    timestamp=datetime.utcnow(),
                    cache_hit=False
                )
            else:
                logger.warning(f"API RENIEC HTTP {response.status_code}")
                return DniConsultaResponse(
                    success=False,
                    message=f"API no disponible - HTTP {response.status_code}",
                    data=None,
                    fuente=endpoint,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"❌ [RENIEC] Excepción en _consultar_api_reniec: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return DniConsultaResponse(
                success=False,
                message=f"Error API: {str(e)}",
                data=None,
                fuente=endpoint,
                timestamp=datetime.utcnow()
            )
    
    def normalize_response(self, data: Dict[str, Any]) -> DniData:
        """
        Normaliza datos de diferentes APIs RENIEC a formato estándar
        
        Args:
            data: Datos crudos de la API
            
        Returns:
            DniData: Datos normalizados
        """
        apellido_paterno = data.get("apellidoPaterno") or data.get("apellidoPaterno") or ""
        apellido_materno = data.get("apellidoMaterno") or data.get("apellidoMaterno") or ""
        
        return DniData(
            dni=data.get("numeroDocumento") or data.get("dni") or "",
            nombres=data.get("nombres") or data.get("prenomes") or "",
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            apellidos=f"{apellido_paterno} {apellido_materno}".strip(),
            fecha_nacimiento=data.get("fechaNacimiento") or None,
            estado_civil=data.get("estadoCivil") or "SOLTERO",
            ubigeo=data.get("ubigeo") or None,
            direccion=data.get("direccion") or None,
            restricciones=data.get("restricciones") or None
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio RENIEC"""
        try:
            return {
                "provider": self.provider.value,
                "disponible": len(self.api_endpoints) > 0,
                "apis_principales": len(self.api_endpoints),
                "apis_backup": len(self.backup_endpoints),
                "ultimo_check": datetime.utcnow().isoformat(),
                "timeout": self.timeout,
                "cache_ttl": self.cache_ttl
            }
        except Exception as e:
            return {
                "provider": self.provider.value,
                "disponible": False,
                "error": str(e),
                "ultimo_check": datetime.utcnow().isoformat()
            }
