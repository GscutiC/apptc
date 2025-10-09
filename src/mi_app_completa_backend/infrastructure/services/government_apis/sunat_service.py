"""
Servicio SUNAT para consultas RUC - Arquitectura Modular
Implementa BaseGovernmentAPI para consultas a SUNAT
"""

import requests
import logging
from datetime import datetime
from typing import Dict, Any

from .base_government_api import (
    BaseGovernmentAPI,
    APIProvider,
    DocumentValidationException,
    APIUnavailableException
)
from ....domain.entities.government_apis import RucData, RucConsultaResponse

logger = logging.getLogger(__name__)


class SunatService(BaseGovernmentAPI):
    """Servicio para consultas reales a SUNAT"""
    
    def __init__(self):
        super().__init__()
        self.provider = APIProvider.SUNAT
        self.api_endpoints = [
            "https://api.apis.net.pe/v1/ruc",
        ]
        self.backup_endpoints = [
            "https://dniruc.apisperu.com/api/v1/ruc/",
            "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/"
        ]
        self.timeout = 10
        self.max_retries = 3
        self.cache_ttl = 7200  # 2 horas (datos empresariales cambian menos)
    
    def validate_document(self, document: str) -> bool:
        """
        Validar que el RUC tenga el formato correcto
        
        Args:
            document: RUC de 11 dígitos
            
        Returns:
            bool: True si es válido
        """
        if not document or len(document) != 11:
            return False
        
        if not document.isdigit():
            return False
        
        # Los primeros dos dígitos deben ser válidos para tipo de contribuyente
        tipo_contrib = document[:2]
        tipos_validos = ["10", "15", "17", "20"]
        
        return tipo_contrib in tipos_validos
    
    async def query_document(self, document: str) -> RucConsultaResponse:
        """
        Consulta información de empresa por RUC en SUNAT
        
        Args:
            document: RUC de 11 dígitos
            
        Returns:
            RucConsultaResponse: Datos de la empresa
        """
        try:
            logger.info(f"🔍 [SUNAT] Consultando RUC: {document}")
            
            # Validar RUC
            if not self.validate_document(document):
                logger.error(f"❌ [SUNAT] RUC inválido: {document}")
                raise DocumentValidationException(
                    "RUC inválido. Debe tener 11 dígitos numéricos y formato válido."
                )
            
            # Intentar consulta con API principal
            for endpoint in self.api_endpoints:
                try:
                    logger.info(f"🔄 [SUNAT] Probando API principal: {endpoint}")
                    resultado = await self._consultar_api_principal(document, endpoint)
                    if resultado.success:
                        logger.info(f"✅ [SUNAT] API principal exitosa: {endpoint}")
                        return resultado
                except Exception as e:
                    logger.warning(f"⚠️ [SUNAT] API principal falló {endpoint}: {e}")
                    continue
            
            # Si falla, intentar APIs de respaldo
            for backup_url in self.backup_endpoints:
                try:
                    logger.info(f"🔄 [SUNAT] Probando API backup: {backup_url}")
                    resultado = await self._consultar_api_backup(document, backup_url)
                    if resultado.success:
                        logger.info(f"✅ [SUNAT] API backup exitosa: {backup_url}")
                        return resultado
                except Exception as e:
                    logger.warning(f"⚠️ [SUNAT] API backup falló {backup_url}: {e}")
                    continue
            
            # Si todas las APIs fallan
            logger.error(f"❌ [SUNAT] Todas las APIs fallaron para RUC: {document}")
            raise APIUnavailableException(
                "No se pudo obtener información del RUC. Todos los servicios no están disponibles."
            )
            
        except DocumentValidationException:
            raise
        except APIUnavailableException:
            raise
        except Exception as e:
            logger.error(f"❌ [SUNAT] Error general para RUC {document}: {e}")
            raise Exception(f"Error en consulta SUNAT: {str(e)}")
    
    async def _consultar_api_principal(self, ruc: str, endpoint: str) -> RucConsultaResponse:
        """Consulta usando API principal"""
        try:
            url = f"{endpoint}?numero={ruc}"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                ruc_data = self.normalize_response(data)
                
                return RucConsultaResponse(
                    success=True,
                    message="Consulta exitosa",
                    data=ruc_data,
                    fuente=f"API Principal - {endpoint}",
                    timestamp=datetime.utcnow(),
                    cache_hit=False
                )
            else:
                return RucConsultaResponse(
                    success=False,
                    message=f"Error HTTP {response.status_code} en API principal",
                    data=None,
                    fuente=endpoint,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            return RucConsultaResponse(
                success=False,
                message=f"Error API principal: {str(e)}",
                data=None,
                fuente=endpoint,
                timestamp=datetime.utcnow()
            )
    
    async def _consultar_api_backup(self, ruc: str, backup_url: str) -> RucConsultaResponse:
        """Consulta usando APIs de respaldo"""
        try:
            url = f"{backup_url}{ruc}"
            response = requests.get(url, headers=self.headers, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                ruc_data = self.normalize_response(data)
                
                return RucConsultaResponse(
                    success=True,
                    message="Consulta exitosa",
                    data=ruc_data,
                    fuente=f"API Backup - {backup_url}",
                    timestamp=datetime.utcnow(),
                    cache_hit=False
                )
            else:
                return RucConsultaResponse(
                    success=False,
                    message=f"Error HTTP {response.status_code} en API backup",
                    data=None,
                    fuente=backup_url,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            return RucConsultaResponse(
                success=False,
                message=f"Error API backup: {str(e)}",
                data=None,
                fuente=backup_url,
                timestamp=datetime.utcnow()
            )
    
    def normalize_response(self, data: Dict[str, Any]) -> RucData:
        """
        Normalizar los datos de diferentes APIs a un formato estándar
        
        Args:
            data: Datos crudos de la API
            
        Returns:
            RucData: Datos normalizados
        """
        return RucData(
            ruc=data.get("numeroDocumento") or data.get("ruc") or "",
            razon_social=data.get("razonSocial") or data.get("nombre") or "",
            nombre_comercial=data.get("nombreComercial") or data.get("nombreComercial") or None,
            estado=data.get("estado") or data.get("condicion") or "ACTIVO",
            condicion=data.get("condicion") or None,
            tipo_empresa=data.get("tipoDocumento") or data.get("tipo") or None,
            tipo_contribuyente=data.get("tipoContribuyente") or None,
            direccion=data.get("direccion") or data.get("domicilioFiscal") or None,
            ubigeo=data.get("ubigeo") or None,
            departamento=data.get("departamento") or None,
            provincia=data.get("provincia") or None,
            distrito=data.get("distrito") or None,
            fecha_inscripcion=data.get("fechaInscripcion") or None,
            fecha_inicio_actividades=data.get("fechaInicioActividades") or None,
            actividad_economica=data.get("actividadEconomica") or None,
            sistema_contabilidad=data.get("sistemaContabilidad") or None,
            tipo_facturacion=data.get("tipoFacturacion") or None,
            comercio_exterior=data.get("comercioExterior") or None,
            telefono=data.get("telefono") or None,
            email=data.get("email") or None,
            representante_legal=data.get("representanteLegal") or None,
            trabajadores=data.get("trabajadores") or 0
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado del servicio SUNAT"""
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
