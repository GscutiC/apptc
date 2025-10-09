"""
Servicio de validación UBIGEO para ubicaciones geográficas
Proporciona validación de códigos UBIGEO y datos geográficos
"""

from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UbigeoValidationResult:
    """Resultado de validación UBIGEO"""
    is_valid: bool
    ubigeo_code: Optional[str] = None
    department: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    validation_errors: Optional[List[str]] = None
    geographic_data: Optional[Dict[str, Any]] = None


@dataclass
class GeographicLocation:
    """Datos de ubicación geográfica"""
    ubigeo_code: str
    department: str
    province: str
    district: str
    department_code: str
    province_code: str
    district_code: str
    altitude: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    surface_km2: Optional[float] = None
    population: Optional[int] = None


class UbigeoValidationService:
    """
    Servicio para validación de códigos UBIGEO y ubicaciones geográficas
    Proporciona validación y normalización de datos geográficos del Perú
    """
    
    def __init__(self):
        # En una implementación real, estos datos podrían venir de una base de datos
        # o servicio externo. Por ahora, incluimos algunos ejemplos básicos.
        self._initialize_ubigeo_data()
    
    def _initialize_ubigeo_data(self):
        """Inicializar datos UBIGEO básicos"""
        # Datos de ejemplo - en producción deberían venir de una fuente oficial
        self.ubigeo_data = {
            # Lima
            "150101": GeographicLocation("150101", "LIMA", "LIMA", "LIMA", "15", "01", "01", 154.0, -12.0464, -77.0428),
            "150102": GeographicLocation("150102", "LIMA", "LIMA", "ANCON", "15", "01", "02", 69.0, -11.7703, -77.1469),
            "150103": GeographicLocation("150103", "LIMA", "LIMA", "ATE", "15", "01", "03", 350.0, -12.0317, -76.9181),
            "150104": GeographicLocation("150104", "LIMA", "LIMA", "BARRANCO", "15", "01", "04", 85.0, -12.1439, -77.0181),
            "150105": GeographicLocation("150105", "LIMA", "LIMA", "BREÑA", "15", "01", "05", 154.0, -12.0581, -77.0453),
            
            # Callao
            "070101": GeographicLocation("070101", "CALLAO", "PROV. CONST. DEL CALLAO", "CALLAO", "07", "01", "01", 34.0, -12.0500, -77.1200),
            "070102": GeographicLocation("070102", "CALLAO", "PROV. CONST. DEL CALLAO", "BELLAVISTA", "07", "01", "02", 67.0, -12.0617, -77.1078),
            
            # Cusco
            "080101": GeographicLocation("080101", "CUSCO", "CUSCO", "CUSCO", "08", "01", "01", 3399.0, -13.5226, -71.9686),
            "080102": GeographicLocation("080102", "CUSCO", "CUSCO", "CCORCA", "08", "01", "02", 3800.0, -13.6000, -72.0500),
            
            # Arequipa
            "040101": GeographicLocation("040101", "AREQUIPA", "AREQUIPA", "AREQUIPA", "04", "01", "01", 2335.0, -16.4090, -71.5375),
            "040102": GeographicLocation("040102", "AREQUIPA", "AREQUIPA", "ALTO SELVA ALEGRE", "04", "01", "02", 2552.0, -16.3739, -71.5281),
        }
        
        # Índices para búsqueda rápida
        self.departments = {}
        self.provinces = {}
        self.districts = {}
        
        for ubigeo_code, location in self.ubigeo_data.items():
            # Índice por departamento
            if location.department not in self.departments:
                self.departments[location.department] = {}
            if location.province not in self.departments[location.department]:
                self.departments[location.department][location.province] = []
            self.departments[location.department][location.province].append(location)
            
            # Índice por provincia
            province_key = f"{location.department}|{location.province}"
            if province_key not in self.provinces:
                self.provinces[province_key] = []
            self.provinces[province_key].append(location)
            
            # Índice por distrito
            self.districts[location.district] = location
    
    async def validate_ubigeo_code(self, ubigeo_code: str) -> UbigeoValidationResult:
        """
        Validar código UBIGEO
        
        Args:
            ubigeo_code: Código UBIGEO de 6 dígitos
            
        Returns:
            UbigeoValidationResult: Resultado de la validación
        """
        
        # Validar formato
        format_validation = self._validate_ubigeo_format(ubigeo_code)
        if not format_validation.is_valid:
            return format_validation
        
        # Buscar en datos
        location = self.ubigeo_data.get(ubigeo_code)
        if not location:
            return UbigeoValidationResult(
                is_valid=False,
                ubigeo_code=ubigeo_code,
                validation_errors=[f"Código UBIGEO no encontrado: {ubigeo_code}"]
            )
        
        return UbigeoValidationResult(
            is_valid=True,
            ubigeo_code=ubigeo_code,
            department=location.department,
            province=location.province,
            district=location.district,
            geographic_data={
                "department_code": location.department_code,
                "province_code": location.province_code,
                "district_code": location.district_code,
                "altitude": location.altitude,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "surface_km2": location.surface_km2,
                "population": location.population
            }
        )
    
    async def validate_location_names(
        self,
        department: str,
        province: str,
        district: str
    ) -> UbigeoValidationResult:
        """
        Validar nombres de ubicación y obtener código UBIGEO
        
        Args:
            department: Nombre del departamento
            province: Nombre de la provincia
            district: Nombre del distrito
            
        Returns:
            UbigeoValidationResult: Resultado de la validación
        """
        
        errors = []
        
        # Normalizar nombres
        dept_normalized = department.upper().strip()
        prov_normalized = province.upper().strip()
        dist_normalized = district.upper().strip()
        
        # Buscar departamento
        if dept_normalized not in self.departments:
            errors.append(f"Departamento no encontrado: {department}")
            return UbigeoValidationResult(
                is_valid=False,
                validation_errors=errors
            )
        
        # Buscar provincia
        if prov_normalized not in self.departments[dept_normalized]:
            errors.append(f"Provincia no encontrada en {department}: {province}")
            return UbigeoValidationResult(
                is_valid=False,
                validation_errors=errors
            )
        
        # Buscar distrito
        districts_in_province = self.departments[dept_normalized][prov_normalized]
        district_found = None
        
        for location in districts_in_province:
            if location.district.upper() == dist_normalized:
                district_found = location
                break
        
        if not district_found:
            errors.append(f"Distrito no encontrado en {province}, {department}: {district}")
            return UbigeoValidationResult(
                is_valid=False,
                validation_errors=errors
            )
        
        return UbigeoValidationResult(
            is_valid=True,
            ubigeo_code=district_found.ubigeo_code,
            department=district_found.department,
            province=district_found.province,
            district=district_found.district,
            geographic_data={
                "department_code": district_found.department_code,
                "province_code": district_found.province_code,
                "district_code": district_found.district_code,
                "altitude": district_found.altitude,
                "latitude": district_found.latitude,
                "longitude": district_found.longitude,
                "surface_km2": district_found.surface_km2,
                "population": district_found.population
            }
        )
    
    async def get_ubigeo_by_coordinates(
        self,
        latitude: float,
        longitude: float,
        max_distance_km: float = 5.0
    ) -> Optional[UbigeoValidationResult]:
        """
        Obtener UBIGEO más cercano por coordenadas
        
        Args:
            latitude: Latitud
            longitude: Longitud
            max_distance_km: Distancia máxima en kilómetros
            
        Returns:
            UbigeoValidationResult: Ubicación más cercana encontrada
        """
        
        closest_location = None
        min_distance = float('inf')
        
        for location in self.ubigeo_data.values():
            if location.latitude is None or location.longitude is None:
                continue
            
            # Calcular distancia aproximada (fórmula haversine simplificada)
            distance = self._calculate_distance(
                latitude, longitude,
                location.latitude, location.longitude
            )
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                closest_location = location
        
        if not closest_location:
            return None
        
        return UbigeoValidationResult(
            is_valid=True,
            ubigeo_code=closest_location.ubigeo_code,
            department=closest_location.department,
            province=closest_location.province,
            district=closest_location.district,
            geographic_data={
                **closest_location.__dict__,
                "distance_km": round(min_distance, 2)
            }
        )
    
    async def search_locations(
        self,
        search_term: str,
        limit: int = 10
    ) -> List[UbigeoValidationResult]:
        """
        Buscar ubicaciones por término de búsqueda
        
        Args:
            search_term: Término de búsqueda
            limit: Límite de resultados
            
        Returns:
            List[UbigeoValidationResult]: Lista de ubicaciones encontradas
        """
        
        results = []
        search_normalized = search_term.upper().strip()
        
        for location in self.ubigeo_data.values():
            # Buscar en departamento, provincia y distrito
            if (search_normalized in location.department.upper() or
                search_normalized in location.province.upper() or
                search_normalized in location.district.upper()):
                
                results.append(UbigeoValidationResult(
                    is_valid=True,
                    ubigeo_code=location.ubigeo_code,
                    department=location.department,
                    province=location.province,
                    district=location.district,
                    geographic_data=location.__dict__
                ))
                
                if len(results) >= limit:
                    break
        
        return results
    
    async def get_departments(self) -> List[str]:
        """Obtener lista de departamentos"""
        return sorted(list(self.departments.keys()))
    
    async def get_provinces(self, department: str) -> List[str]:
        """Obtener provincias de un departamento"""
        dept_normalized = department.upper().strip()
        if dept_normalized not in self.departments:
            return []
        return sorted(list(self.departments[dept_normalized].keys()))
    
    async def get_districts(self, department: str, province: str) -> List[str]:
        """Obtener distritos de una provincia"""
        dept_normalized = department.upper().strip()
        prov_normalized = province.upper().strip()
        
        if (dept_normalized not in self.departments or
            prov_normalized not in self.departments[dept_normalized]):
            return []
        
        districts = []
        for location in self.departments[dept_normalized][prov_normalized]:
            districts.append(location.district)
        
        return sorted(districts)
    
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
            
            # Provincia no puede ser 00
            if prov_code == "00":
                errors.append("Código de provincia no puede ser 00")
            
            # Distrito no puede ser 00
            if dist_code == "00":
                errors.append("Código de distrito no puede ser 00")
        
        return UbigeoValidationResult(
            is_valid=len(errors) == 0,
            ubigeo_code=ubigeo_code if len(errors) == 0 else None,
            validation_errors=errors if errors else None
        )
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distancia entre dos puntos (fórmula haversine simplificada)"""
        import math
        
        # Radio de la Tierra en kilómetros
        R = 6371.0
        
        # Convertir grados a radianes
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Diferencias
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Fórmula haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        return distance