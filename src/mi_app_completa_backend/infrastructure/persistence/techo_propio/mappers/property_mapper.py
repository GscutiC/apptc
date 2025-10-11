"""
Mapper para entidad PropertyInfo
Maneja conversión entre PropertyInfo entity y documento MongoDB
"""

from typing import Dict, Any
from decimal import Decimal
import logging

from .base_mapper import BaseMapper
from .....domain.entities.techo_propio import PropertyInfo

logger = logging.getLogger(__name__)


class PropertyMapper(BaseMapper):
    """Mapper especializado para entidades PropertyInfo"""
    
    @classmethod
    def to_dict(cls, property_info: PropertyInfo) -> Dict[str, Any]:
        """Convertir PropertyInfo a diccionario para MongoDB"""
        try:
            return {
                "id": property_info.id,
                "department": property_info.department,
                "province": property_info.province,
                "district": property_info.district,
                "lote": property_info.lote,
                "address": property_info.address,
                "ubigeo_code": property_info.ubigeo_code,
                "populated_center": property_info.populated_center,
                "manzana": property_info.manzana,
                "sub_lote": property_info.sub_lote,
                "reference": property_info.reference,
                "latitude": cls.safe_decimal_to_float(property_info.latitude),
                "longitude": cls.safe_decimal_to_float(property_info.longitude),
                "created_at": property_info.created_at,
                "updated_at": property_info.updated_at
            }
        except Exception as e:
            cls.handle_mapping_error("PropertyInfo", "to_dict", e)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PropertyInfo:
        """Convertir diccionario MongoDB a entidad PropertyInfo"""
        try:
            # Crear entidad PropertyInfo
            property_info = PropertyInfo(
                department=data["department"],
                province=data["province"],
                district=data["district"],
                lote=data["lote"],
                address=data["address"],
                ubigeo_code=data.get("ubigeo_code"),
                populated_center=data.get("populated_center"),
                manzana=data.get("manzana"),
                sub_lote=data.get("sub_lote"),
                reference=data.get("reference"),
                latitude=cls.safe_float_to_decimal(data.get("latitude")),
                longitude=cls.safe_float_to_decimal(data.get("longitude"))
            )
            
            # Restaurar metadatos
            property_info.id = data["id"]
            property_info.created_at = data["created_at"]
            property_info.updated_at = data.get("updated_at")
            
            return property_info
            
        except Exception as e:
            cls.handle_mapping_error("PropertyInfo", "from_dict", e)