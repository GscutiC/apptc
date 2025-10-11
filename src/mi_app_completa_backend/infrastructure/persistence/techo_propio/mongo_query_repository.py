"""
Repositorio MongoDB para consultas complejas de Techo Propio
Maneja búsquedas, filtros y consultas especializadas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.collection import Collection

from .mappers import ApplicationMapper
from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import ApplicationStatus

logger = logging.getLogger(__name__)


class MongoQueryRepository:
    """Repositorio para consultas complejas y búsquedas"""
    
    def __init__(self, collection: Collection):
        """
        Inicializar repositorio de consultas
        
        Args:
            collection: Colección MongoDB para solicitudes Techo Propio
        """
        self.collection = collection
    
    async def get_applications_by_user(
        self,
        user_id: str,
        status_filter: Optional[ApplicationStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes de un usuario"""
        try:
            query = {"created_by": user_id}
            
            if status_filter:
                query["status"] = status_filter.value
            
            skip = (page - 1) * page_size
            
            cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
            
            applications = []
            for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes del usuario {user_id}: {e}")
            return []
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por estado"""
        try:
            query = {"status": status.value}
            
            skip = (page - 1) * page_size
            sort_direction = DESCENDING if sort_order == "desc" else ASCENDING
            
            cursor = self.collection.find(query).skip(skip).limit(page_size).sort(sort_by, sort_direction)
            
            applications = []
            for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por estado {status}: {e}")
            return []
    
    async def get_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por ubicación"""
        try:
            query = {}
            
            if department:
                query["property_info.department"] = {"$regex": department, "$options": "i"}
            if province:
                query["property_info.province"] = {"$regex": province, "$options": "i"}
            if district:
                query["property_info.district"] = {"$regex": district, "$options": "i"}
            
            skip = (page - 1) * page_size
            
            cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
            
            applications = []
            for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por ubicación: {e}")
            return []
    
    async def get_applications_by_priority(
        self,
        page: int = 1,
        page_size: int = 20,
        min_priority_score: Optional[float] = None
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes ordenadas por prioridad"""
        try:
            query = {}
            
            if min_priority_score is not None:
                query["priority_score"] = {"$gte": min_priority_score}
            
            skip = (page - 1) * page_size
            
            cursor = self.collection.find(query).skip(skip).limit(page_size).sort("priority_score", -1)
            
            applications = []
            for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por prioridad: {e}")
            return []
    
    async def search_applications(
        self,
        search_query: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> List[TechoPropioApplication]:
        """Búsqueda avanzada de solicitudes"""
        try:
            mongo_query = self._build_mongo_query(search_query)
            
            skip = (page - 1) * page_size
            sort_by = search_query.get("sort_by", "created_at")
            sort_order = DESCENDING if search_query.get("sort_order", "desc") == "desc" else ASCENDING
            
            cursor = self.collection.find(mongo_query).skip(skip).limit(page_size).sort(sort_by, sort_order)
            
            applications = []
            for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {e}")
            return []
    
    async def get_applications_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes en rango de fechas"""
        try:
            query = {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            if status:
                query["status"] = status.value
            
            cursor = self.collection.find(query).sort("created_at", DESCENDING).skip(offset).limit(limit)
            
            applications = []
            for doc in cursor:
                try:
                    app = ApplicationMapper.from_dict(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por rango de fechas: {e}")
            return []
    
    async def get_applications_by_dni(self, dni: str) -> List[TechoPropioApplication]:
        """Obtener todas las solicitudes que incluyen un DNI específico"""
        try:
            # Buscar en solicitante principal y miembros del hogar
            query = {
                "$or": [
                    {"main_applicant.document_number": dni},
                    {"household_members.document_number": dni}
                ]
            }
            
            cursor = self.collection.find(query)
            applications = []
            
            for doc in cursor:
                try:
                    app = ApplicationMapper.from_dict(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento a entidad: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por DNI {dni}: {e}")
            return []
    
    def _build_mongo_query(self, search_query: Dict[str, Any]) -> Dict[str, Any]:
        """Construir query MongoDB desde parámetros de búsqueda"""
        mongo_query = {}
        
        # Búsqueda por texto
        if search_query.get("search_term"):
            mongo_query["$text"] = {"$search": search_query["search_term"]}
        
        # Filtros exactos
        if search_query.get("status"):
            mongo_query["status"] = search_query["status"].value if hasattr(search_query["status"], 'value') else search_query["status"]
        
        if search_query.get("user_id"):
            mongo_query["created_by"] = search_query["user_id"]
        
        # Filtros de ubicación
        if search_query.get("department"):
            mongo_query["property_info.department"] = {"$regex": search_query["department"], "$options": "i"}
        
        if search_query.get("province"):
            mongo_query["property_info.province"] = {"$regex": search_query["province"], "$options": "i"}
        
        if search_query.get("district"):
            mongo_query["property_info.district"] = {"$regex": search_query["district"], "$options": "i"}
        
        # Filtros de fecha
        if search_query.get("date_from") or search_query.get("date_to"):
            date_filter = {}
            if search_query.get("date_from"):
                date_filter["$gte"] = datetime.combine(search_query["date_from"], datetime.min.time())
            if search_query.get("date_to"):
                date_filter["$lte"] = datetime.combine(search_query["date_to"], datetime.max.time())
            mongo_query["created_at"] = date_filter
        
        # Filtros económicos
        if search_query.get("min_monthly_income") or search_query.get("max_monthly_income"):
            income_filter = {}
            if search_query.get("min_monthly_income"):
                income_filter["$gte"] = search_query["min_monthly_income"]
            if search_query.get("max_monthly_income"):
                income_filter["$lte"] = search_query["max_monthly_income"]
            mongo_query["main_applicant_economic.monthly_income"] = income_filter
        
        # Filtros de prioridad
        if search_query.get("min_priority_score") or search_query.get("max_priority_score"):
            priority_filter = {}
            if search_query.get("min_priority_score"):
                priority_filter["$gte"] = search_query["min_priority_score"]
            if search_query.get("max_priority_score"):
                priority_filter["$lte"] = search_query["max_priority_score"]
            mongo_query["priority_score"] = priority_filter
        
        return mongo_query