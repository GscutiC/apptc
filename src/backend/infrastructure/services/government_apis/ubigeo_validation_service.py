"""
Servicio de validación UBIGEO para el Perú
Utiliza datos de MongoDB para validar códigos y ubicaciones
"""

from typing import List, Dict, Optional, Any, Tuple
import logging
from dataclasses import dataclass

# Importar repositorio
from ...persistence.mongodb.ubigeo_repository_impl import MongoUbigeoRepository

# Configurar logger
logger = logging.getLogger(__name__)


@dataclass
class UbigeoValidationResult:
    """Resultado de validación UBIGEO"""
    is_valid: bool
    ubigeo_code: Optional[str] = None
    department: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    validation_errors: List[str] = None
    geographic_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
        if self.geographic_data is None:
            self.geographic_data = {}


class UbigeoValidationService:
    """
    Servicio para validación de códigos UBIGEO y ubicaciones geográficas
    Utiliza MongoDB para obtener datos completos del Perú
    """
    
    def __init__(self, ubigeo_repository: MongoUbigeoRepository):
        self.ubigeo_repository = ubigeo_repository

    # ==================== MÉTODOS PRINCIPALES ====================
    
    async def get_departments_with_codes(self) -> List[Dict[str, str]]:
        """Obtener lista de departamentos con códigos desde MongoDB"""
        return await self.ubigeo_repository.get_departments()
    
    async def get_provinces_with_codes(self, department: str) -> List[Dict[str, str]]:
        """Obtener provincias de un departamento con códigos desde MongoDB"""
        return await self.ubigeo_repository.get_provinces(department)
    
    async def get_districts_with_codes(self, department: str, province: str) -> List[Dict[str, str]]:
        """Obtener distritos de una provincia con códigos desde MongoDB"""
        return await self.ubigeo_repository.get_districts(department, province)
    
    async def search_locations(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Buscar ubicaciones por término de búsqueda"""
        return await self.ubigeo_repository.search_locations(search_term, limit)
    
    async def validate_ubigeo_hierarchy(self, department: str, province: str, district: str) -> bool:
        """Validar que existe la jerarquía departamento > provincia > distrito"""
        return await self.ubigeo_repository.validate_ubigeo_hierarchy(department, province, district)
    
    async def get_location_by_ubigeo(self, ubigeo_code: str) -> Optional[Dict[str, str]]:
        """Obtener ubicación por código UBIGEO"""
        return await self.ubigeo_repository.get_location_by_ubigeo(ubigeo_code)

    # ==================== MÉTODOS DE VALIDACIÓN ====================
    
    async def validate_location_names(
        self,
        department: str,
        province: str,
        district: str
    ) -> UbigeoValidationResult:
        """Validar nombres de ubicación"""
        errors = []
        suggestions = []
        
        # Validar que la jerarquía existe
        is_valid = await self.validate_ubigeo_hierarchy(department, province, district)
        
        if not is_valid:
            errors.append(f"La jerarquía {department}/{province}/{district} no es válida")
            
            # Buscar sugerencias
            search_results = await self.search_locations(district, limit=5)
            if search_results:
                suggestions = [loc['full_location'] for loc in search_results]
        
        return UbigeoValidationResult(
            is_valid=is_valid,
            errors=errors,
            suggestions=suggestions,
            normalized_location={
                'department': department.upper().strip(),
                'province': province.upper().strip(),
                'district': district.upper().strip()
            } if is_valid else None
        )
    
    def _validate_ubigeo_format(self, ubigeo_code: str) -> UbigeoValidationResult:
        """Validar formato de código UBIGEO"""
        errors = []
        
        # Validar longitud
        if len(ubigeo_code) != 6:
            errors.append("El código UBIGEO debe tener exactamente 6 dígitos")
        
        # Validar que solo contenga números
        if not ubigeo_code.isdigit():
            errors.append("El código UBIGEO debe contener solo números")
        
        # Validar rangos básicos
        if len(ubigeo_code) == 6:
            dept_code = ubigeo_code[:2]
            prov_code = ubigeo_code[2:4]
            dist_code = ubigeo_code[4:6]
            
            # Departamento debe estar entre 01 y 25
            if not (1 <= int(dept_code) <= 25):
                errors.append(f"Código de departamento inválido: {dept_code}")
            
            # Provincia y distrito no pueden ser 00
            if prov_code == "00":
                errors.append("Código de provincia no puede ser 00")
            if dist_code == "00":
                errors.append("Código de distrito no puede ser 00")
        
        return UbigeoValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            suggestions=[],
            ubigeo_code=ubigeo_code if len(errors) == 0 else None
        )
    
    async def validate_ubigeo_code(self, ubigeo_code: str) -> UbigeoValidationResult:
        """Validar código UBIGEO completo"""
        # Primero validar formato
        format_result = self._validate_ubigeo_format(ubigeo_code)
        if not format_result.is_valid:
            return format_result
        
        # Luego validar que existe en la base de datos
        location = await self.get_location_by_ubigeo(ubigeo_code)
        
        if location:
            return UbigeoValidationResult(
                is_valid=True,
                errors=[],
                suggestions=[],
                ubigeo_code=ubigeo_code,
                normalized_location=location,
                geographic_data=location
            )
        else:
            return UbigeoValidationResult(
                is_valid=False,
                errors=[f"Código UBIGEO {ubigeo_code} no encontrado en la base de datos"],
                suggestions=[],
                ubigeo_code=ubigeo_code
            )

    # ==================== MÉTODOS DE UTILIDAD ====================
    
    async def get_statistics(self) -> Dict[str, int]:
        """Obtener estadísticas de la base de datos UBIGEO"""
        return await self.ubigeo_repository.get_statistics()
    
    async def normalize_location_name(self, name: str) -> str:
        """Normalizar nombre de ubicación"""
        return name.upper().strip()
    
    def extract_ubigeo_components(self, ubigeo_code: str) -> Tuple[str, str, str]:
        """Extraer componentes del código UBIGEO"""
        if len(ubigeo_code) != 6:
            raise ValueError("Código UBIGEO debe tener 6 dígitos")
        
        return (
            ubigeo_code[:2],  # Departamento
            ubigeo_code[2:4], # Provincia
            ubigeo_code[4:6]  # Distrito
        )