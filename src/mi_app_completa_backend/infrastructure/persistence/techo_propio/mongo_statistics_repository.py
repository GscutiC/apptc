"""
Repositorio MongoDB para estadísticas y reportes de Techo Propio
Maneja agregaciones, conteos y análisis de datos
"""

from typing import Dict, Any, Optional
from datetime import datetime, date
import logging
from pymongo.collection import Collection
from motor.motor_asyncio import AsyncIOMotorCollection

from ....domain.value_objects.techo_propio import ApplicationStatus

logger = logging.getLogger(__name__)


class MongoStatisticsRepository:
    """Repositorio para estadísticas y reportes"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Inicializar repositorio de estadísticas
        
        Args:
            collection: Colección MongoDB asíncrona para solicitudes Techo Propio
        """
        self.collection = collection
    
    # ===== MÉTODOS DE CONTEO =====
    
    async def count_all_applications(self) -> int:
        """Contar todas las solicitudes"""
        return await self.collection.count_documents({})
    
    async def count_applications_by_user(
        self,
        user_id: str,
        status_filter: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de un usuario"""
        query = {"user_id": user_id}  # ✅ CORRECCIÓN: user_id en lugar de created_by
        if status_filter:
            query["status"] = status_filter.value
        return await self.collection.count_documents(query)
    
    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado"""
        return await self.collection.count_documents({"status": status.value})
    
    async def count_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None
    ) -> int:
        """Contar solicitudes por ubicación"""
        query = {}
        if department:
            query["property_info.department"] = {"$regex": department, "$options": "i"}
        if province:
            query["property_info.province"] = {"$regex": province, "$options": "i"}
        if district:
            query["property_info.district"] = {"$regex": district, "$options": "i"}
        
        return await self.collection.count_documents(query)
    
    async def count_search_results(self, search_query: Dict[str, Any]) -> int:
        """Contar resultados de búsqueda"""
        mongo_query = self._build_mongo_query(search_query)
        return await self.collection.count_documents(mongo_query)
    
    async def count_priority_applications(self, min_priority_score: Optional[float] = None) -> int:
        """Contar solicitudes prioritarias"""
        query = {}
        if min_priority_score is not None:
            query["priority_score"] = {"$gte": min_priority_score}
        return await self.collection.count_documents(query)
    
    # ===== ESTADÍSTICAS AVANZADAS =====
    
    async def get_application_statistics(
        self,
        department: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas detalladas"""
        try:
            match_stage = {}
            
            if department:
                match_stage["property_info.department"] = {"$regex": department, "$options": "i"}
            
            if date_from or date_to:
                date_filter = {}
                if date_from:
                    date_filter["$gte"] = datetime.combine(date_from, datetime.min.time())
                if date_to:
                    date_filter["$lte"] = datetime.combine(date_to, datetime.max.time())
                match_stage["created_at"] = date_filter
            
            pipeline = []
            
            if match_stage:
                pipeline.append({"$match": match_stage})
            
            pipeline.extend([
                {
                    "$group": {
                        "_id": None,
                        "total_applications": {"$sum": 1},
                        "status_breakdown": {
                            "$push": "$status"
                        },
                        "avg_priority_score": {"$avg": "$priority_score"},
                        "total_income": {"$sum": "$main_applicant_economic.monthly_income"},
                        "departments": {"$addToSet": "$property_info.department"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total_applications": 1,
                        "avg_priority_score": {"$round": ["$avg_priority_score", 2]},
                        "total_income": 1,
                        "unique_departments": {"$size": "$departments"},
                        "status_breakdown": 1
                    }
                }
            ])
            
            # Usar await con to_list() para cursores asíncronos
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            
            if not result:
                return {
                    "total_applications": 0,
                    "status_breakdown": {},
                    "avg_priority_score": 0.0,
                    "total_income": 0.0,
                    "unique_departments": 0
                }
            
            stats = result[0]
            
            # Procesar breakdown de estados
            status_breakdown = stats.get("status_breakdown", [])
            status_counts = {}
            
            # Convertir a lista si es un cursor
            if hasattr(status_breakdown, '__iter__') and not isinstance(status_breakdown, (list, dict)):
                status_breakdown = list(status_breakdown)
            
            if isinstance(status_breakdown, list):
                for status in status_breakdown:
                    status_counts[status] = status_counts.get(status, 0) + 1
            else:
                status_counts = status_breakdown
            
            stats["status_breakdown"] = status_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    async def get_monthly_statistics(
        self,
        year: int,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas mensuales"""
        try:
            # Construir filtro de fecha
            if month:
                # Estadísticas de un mes específico
                from calendar import monthrange
                start_date = datetime(year, month, 1)
                _, last_day = monthrange(year, month)
                end_date = datetime(year, month, last_day, 23, 59, 59)
            else:
                # Estadísticas de todo el año
                start_date = datetime(year, 1, 1)
                end_date = datetime(year, 12, 31, 23, 59, 59)
            
            match_stage = {
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            pipeline = [
                {"$match": match_stage},
                {
                    "$group": {
                        "_id": {
                            "year": {"$year": "$created_at"},
                            "month": {"$month": "$created_at"} if not month else month,
                            "status": "$status"
                        },
                        "count": {"$sum": 1},
                        "avg_priority": {"$avg": "$priority_score"}
                    }
                },
                {
                    "$group": {
                        "_id": {"year": "$_id.year", "month": "$_id.month"},
                        "status_counts": {
                            "$push": {
                                "status": "$_id.status",
                                "count": "$count"
                            }
                        },
                        "total_applications": {"$sum": "$count"},
                        "avg_priority_score": {"$avg": "$avg_priority"}
                    }
                },
                {"$sort": {"_id.year": 1, "_id.month": 1}}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            
            # Procesar resultados
            statistics = []
            for item in result:
                period_stats = {
                    "year": item["_id"]["year"],
                    "month": item["_id"]["month"],
                    "total_applications": item["total_applications"],
                    "avg_priority_score": round(item.get("avg_priority_score", 0), 2),
                    "status_breakdown": {}
                }
                
                # Procesar breakdown de estados
                for status_info in item["status_counts"]:
                    period_stats["status_breakdown"][status_info["status"]] = status_info["count"]
                
                statistics.append(period_stats)
            
            return {
                "period": f"{year}" + (f"-{month:02d}" if month else ""),
                "statistics": statistics,
                "total_periods": len(statistics)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas mensuales: {e}")
            return {}
    
    async def get_department_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas por departamento"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$property_info.department",
                        "total_applications": {"$sum": 1},
                        "avg_priority_score": {"$avg": "$priority_score"},
                        "status_breakdown": {"$push": "$status"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "department": "$_id",
                        "total_applications": 1,
                        "avg_priority_score": {"$round": ["$avg_priority_score", 2]},
                        "status_breakdown": 1
                    }
                },
                {"$sort": {"total_applications": -1}}
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=None)
            
            # Procesar breakdown de estados por departamento
            for dept_stats in result:
                status_counts = {}
                for status in dept_stats["status_breakdown"]:
                    status_counts[status] = status_counts.get(status, 0) + 1
                dept_stats["status_breakdown"] = status_counts
            
            return {
                "departments": result,
                "total_departments": len(result)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas por departamento: {e}")
            return {}
    
    def _build_mongo_query(self, search_query: Dict[str, Any]) -> Dict[str, Any]:
        """Construir query MongoDB desde parámetros de búsqueda (para conteos)"""
        mongo_query = {}
        
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
        
        return mongo_query