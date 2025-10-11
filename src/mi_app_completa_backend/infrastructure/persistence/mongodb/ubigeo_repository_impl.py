"""
Repositorio MongoDB para datos UBIGEO
Maneja consultas optimizadas de departamentos, provincias y distritos
"""

from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
import logging

logger = logging.getLogger(__name__)

class MongoUbigeoRepository:
    """Repositorio para consultas UBIGEO en MongoDB"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.ubigeo_locations
    
    async def get_departments(self) -> List[Dict[str, str]]:
        """Obtener todos los departamentos únicos con sus códigos"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$department",
                        "code": {"$first": {"$substr": ["$ubigeo_code", 0, 2]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$code",
                        "name": "$_id"
                    }
                },
                {
                    "$sort": {"name": ASCENDING}
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            departments = await cursor.to_list(length=None)
            
            logger.info(f"Obtenidos {len(departments)} departamentos")
            return departments
            
        except Exception as e:
            logger.error(f"Error obteniendo departamentos: {e}")
            raise
    
    async def get_provinces(self, department_code_or_name: str) -> List[Dict[str, str]]:
        """Obtener provincias de un departamento específico (por código o nombre)"""
        try:
            # Determinar si es código (2 dígitos) o nombre
            department_filter = {}
            if department_code_or_name.isdigit() and len(department_code_or_name) == 2:
                # Es un código de departamento (ej: "10")
                department_filter = {"$expr": {"$eq": [{"$substr": ["$ubigeo_code", 0, 2]}, department_code_or_name.zfill(2)]}}
            else:
                # Es un nombre de departamento (ej: "HUANUCO")
                department_filter = {"department": department_code_or_name.upper().strip()}
            
            pipeline = [
                {
                    "$match": department_filter
                },
                {
                    "$group": {
                        "_id": "$province",
                        "code": {"$first": {"$substr": ["$ubigeo_code", 0, 4]}},
                        "department_code": {"$first": {"$substr": ["$ubigeo_code", 0, 2]}}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$code",
                        "name": "$_id",
                        "department_code": "$department_code"
                    }
                },
                {
                    "$sort": {"name": ASCENDING}
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            provinces = await cursor.to_list(length=None)
            
            logger.info(f"Obtenidas {len(provinces)} provincias para {department_code_or_name}")
            return provinces
            
        except Exception as e:
            logger.error(f"Error obteniendo provincias para {department_code_or_name}: {e}")
            raise
    
    async def get_districts(self, department_code_or_name: str, province_code_or_name: str) -> List[Dict[str, str]]:
        """Obtener distritos de una provincia específica (por código o nombre)"""
        try:
            # Crear filtros según si son códigos o nombres
            match_filter = {}
            
            # Determinar filtro de departamento
            if department_code_or_name.isdigit() and len(department_code_or_name) == 2:
                # Es código de departamento
                match_filter["$expr"] = {"$eq": [{"$substr": ["$ubigeo_code", 0, 2]}, department_code_or_name.zfill(2)]}
            else:
                # Es nombre de departamento
                match_filter["department"] = department_code_or_name.upper().strip()
            
            # Determinar filtro de provincia  
            if province_code_or_name.isdigit() and len(province_code_or_name) == 4:
                # Es código de provincia (ej: "1001")
                if not match_filter.get("$expr"):
                    match_filter["$expr"] = {"$eq": [{"$substr": ["$ubigeo_code", 0, 4]}, province_code_or_name.zfill(4)]}
                else:
                    # Ya hay filtro de departamento por código, agregar filtro de provincia
                    match_filter["$expr"] = {"$and": [
                        match_filter["$expr"],
                        {"$eq": [{"$substr": ["$ubigeo_code", 0, 4]}, province_code_or_name.zfill(4)]}
                    ]}
            else:
                # Es nombre de provincia
                match_filter["province"] = province_code_or_name.upper().strip()
            
            pipeline = [
                {
                    "$match": match_filter
                },
                {
                    "$project": {
                        "_id": 0,
                        "code": "$ubigeo_code", 
                        "name": "$district",
                        "province_code": {"$substr": ["$ubigeo_code", 0, 4]}
                    }
                },
                {
                    "$sort": {"name": ASCENDING}
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            districts = await cursor.to_list(length=None)
            
            logger.info(f"Obtenidos {len(districts)} distritos para {department_code_or_name}/{province_code_or_name}")
            return districts
            
        except Exception as e:
            logger.error(f"Error obteniendo distritos para {department_code_or_name}/{province_code_or_name}: {e}")
            raise
    
    async def search_locations(self, search_term: str, limit: int = 10) -> List[Dict[str, str]]:
        """Buscar ubicaciones por término de búsqueda"""
        try:
            search_regex = {"$regex": search_term.upper(), "$options": "i"}
            
            pipeline = [
                {
                    "$match": {
                        "$or": [
                            {"department": search_regex},
                            {"province": search_regex},
                            {"district": search_regex}
                        ]
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "ubigeo_code": 1,
                        "department": 1,
                        "province": 1,
                        "district": 1,
                        "full_location": {
                            "$concat": ["$department", " > ", "$province", " > ", "$district"]
                        }
                    }
                },
                {
                    "$sort": {"department": ASCENDING, "province": ASCENDING, "district": ASCENDING}
                },
                {
                    "$limit": limit
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            locations = await cursor.to_list(length=None)
            
            logger.info(f"Encontradas {len(locations)} ubicaciones para '{search_term}'")
            return locations
            
        except Exception as e:
            logger.error(f"Error buscando ubicaciones: {e}")
            raise
    
    async def get_location_by_ubigeo(self, ubigeo_code: str) -> Optional[Dict[str, str]]:
        """Obtener ubicación por código UBIGEO"""
        try:
            location = await self.collection.find_one(
                {"ubigeo_code": ubigeo_code},
                {"_id": 0}
            )
            
            if location:
                logger.info(f"Ubicación encontrada para UBIGEO {ubigeo_code}")
            else:
                logger.warning(f"No se encontró ubicación para UBIGEO {ubigeo_code}")
            
            return location
            
        except Exception as e:
            logger.error(f"Error obteniendo ubicación por UBIGEO {ubigeo_code}: {e}")
            raise
    
    async def validate_ubigeo_hierarchy(self, department: str, province: str, district: str) -> bool:
        """Validar que existe la jerarquía departamento > provincia > distrito"""
        try:
            count = await self.collection.count_documents({
                "department": department.upper().strip(),
                "province": province.upper().strip(), 
                "district": district.upper().strip()
            })
            
            is_valid = count > 0
            logger.info(f"Jerarquía {department}/{province}/{district} {'válida' if is_valid else 'inválida'}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validando jerarquía: {e}")
            raise
    
    async def get_statistics(self) -> Dict[str, int]:
        """Obtener estadísticas de la base de datos UBIGEO"""
        try:
            stats = {}
            
            # Total de distritos
            stats['total_districts'] = await self.collection.count_documents({})
            
            # Total de provincias únicas
            stats['total_provinces'] = len(await self.collection.distinct("province"))
            
            # Total de departamentos únicos
            stats['total_departments'] = len(await self.collection.distinct("department"))
            
            logger.info(f"📊 Estadísticas UBIGEO: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise