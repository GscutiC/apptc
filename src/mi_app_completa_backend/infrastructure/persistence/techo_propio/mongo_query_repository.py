"""
Repositorio MongoDB para consultas complejas de Techo Propio
Maneja búsquedas, filtros y consultas especializadas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import logging
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from ...config.timezone_config import lima_now
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorCollection

from .mappers import ApplicationMapper
from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import ApplicationStatus

logger = logging.getLogger(__name__)


class MongoQueryRepository:
    """Repositorio para consultas complejas y búsquedas"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Inicializar repositorio de consultas
        
        Args:
            collection: Colección MongoDB asíncrona para solicitudes Techo Propio
        """
        self.collection = collection
    
    async def get_applications_by_user(
        self,
        user_id: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes de un usuario"""
        try:
            # ✅ CORRECCIÓN: Buscar por user_id (no created_by)
            query = {"user_id": user_id}
            
            # 🐛 DEBUG: Log de consulta
            logger.info(f"📋 Consultando aplicaciones con query: {query}")
            logger.info(f"📊 Parámetros: user_id={user_id}, status={status}, limit={limit}, offset={offset}")
            
            if status:
                query["status"] = status.value
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes del usuario {user_id}: {e}")
            return []
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por estado"""
        try:
            query = {"status": status.value}
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", DESCENDING)
            
            applications = []
            async for document in cursor:
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
            async for document in cursor:
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
            async for document in cursor:
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
            async for document in cursor:
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
            mongo_query["user_id"] = search_query["user_id"]  # ✅ CORRECCIÓN: user_id en lugar de created_by
        
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
    
    async def get_pending_review_applications(
        self,
        reviewer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes pendientes de revisión"""
        try:
            query = {"status": ApplicationStatus.SUBMITTED.value}
            
            if reviewer_id:
                query["assigned_reviewer"] = reviewer_id
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("submitted_at", ASCENDING)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes pendientes de revisión: {e}")
            return []

    async def count_applications_by_user(
        self, 
        user_id: str,
        status: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de un usuario"""
        try:
            # ✅ CORRECCIÓN: Buscar por user_id (no created_by)
            query = {"user_id": user_id}
            
            if status:
                query["status"] = status.value
            
            count = await self.collection.count_documents(query)
            logger.info(f"📊 Documentos encontrados para user_id={user_id}: {count}")
            
            return count
            
        except Exception as e:
            logger.error(f"Error contando solicitudes del usuario {user_id}: {e}")
            return 0

    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado"""
        try:
            query = {"status": status.value}
            return await self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error contando solicitudes por estado {status}: {e}")
            return 0

    async def get_applications_by_department(
        self,
        department: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por departamento"""
        try:
            query = {"contact_information.department": department}
            
            if status:
                query["status"] = status.value
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por departamento {department}: {e}")
            return []

    async def get_applications_by_district(
        self,
        department: str,
        province: str,
        district: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por distrito específico"""
        try:
            query = {
                "contact_information.department": department,
                "contact_information.province": province,
                "contact_information.district": district
            }
            
            if status:
                query["status"] = status.value
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por distrito {district}: {e}")
            return []

    async def get_applications_by_household_size(
        self,
        min_size: int,
        max_size: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por tamaño de familia"""
        try:
            query = {"household_information.household_size": {"$gte": min_size}}
            
            if max_size:
                query["household_information.household_size"]["$lte"] = max_size
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por tamaño de familia: {e}")
            return []

    async def get_applications_by_income_range(
        self,
        min_income: float,
        max_income: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por rango de ingresos"""
        try:
            query = {"economic_information.monthly_income": {"$gte": min_income}}
            
            if max_income:
                query["economic_information.monthly_income"]["$lte"] = max_income
            
            cursor = self.collection.find(query).skip(offset).limit(limit).sort("created_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por rango de ingresos: {e}")
            return []

    async def get_applications_submitted_today(self) -> List[TechoPropioApplication]:
        """Obtener solicitudes enviadas hoy"""
        try:
            today = lima_now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            query = {
                "submitted_at": {
                    "$gte": today,
                    "$lte": tomorrow
                }
            }
            
            cursor = self.collection.find(query).sort("submitted_at", -1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes de hoy: {e}")
            return []

    async def get_expired_draft_applications(
        self,
        days_old: int = 30
    ) -> List[TechoPropioApplication]:
        """Obtener borradores expirados"""
        try:
            cutoff_date = lima_now() - timedelta(days=days_old)
            
            query = {
                "status": ApplicationStatus.DRAFT.value,
                "created_at": {"$lt": cutoff_date}
            }
            
            cursor = self.collection.find(query).sort("created_at", 1)
            
            applications = []
            async for document in cursor:
                applications.append(ApplicationMapper.from_dict(document))
            
            return applications
        except Exception as e:
            logger.error(f"Error obteniendo borradores expirados: {e}")
            return []