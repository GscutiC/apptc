"""
Implementación MongoDB para el repositorio de auditoría
"""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from ....domain.repositories.audit_repository import AuditLogRepository
from ....domain.entities.audit_log import AuditLog, AuditLogCreate, AuditLogFilter

class MongoAuditLogRepository(AuditLogRepository):
    """Implementación MongoDB para logs de auditoría"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.audit_logs
        # Crear índices para mejorar performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Crear índices para la colección de auditoría"""
        # Índice compuesto para búsquedas comunes
        self.collection.create_index([
            ("clerk_id", 1),
            ("timestamp", -1)
        ])
        
        # Índice para acciones
        self.collection.create_index([
            ("action", 1),
            ("timestamp", -1)
        ])
        
        # Índice para tipo de recurso
        self.collection.create_index([
            ("resource_type", 1),
            ("timestamp", -1)
        ])
        
        # Índice para timestamp (para limpieza automática)
        self.collection.create_index([
            ("timestamp", -1)
        ])
        
        # Índice TTL para auto-eliminación de logs antiguos (opcional, 1 año)
        self.collection.create_index(
            [("timestamp", 1)],
            expireAfterSeconds=365*24*60*60  # 1 año en segundos
        )
    
    async def create_log(self, log_data: AuditLogCreate) -> AuditLog:
        """Crear un nuevo log de auditoría"""
        log_dict = log_data.dict()
        log_dict["timestamp"] = datetime.now(timezone.utc)
        
        result = await self.collection.insert_one(log_dict)
        log_dict["_id"] = result.inserted_id
        
        return AuditLog(**log_dict)
    
    async def get_log_by_id(self, log_id: str) -> Optional[AuditLog]:
        """Obtener log por ID"""
        try:
            log_doc = await self.collection.find_one({"_id": ObjectId(log_id)})
            if log_doc:
                return AuditLog(**log_doc)
            return None
        except Exception:
            return None
    
    async def list_logs(self, filters: AuditLogFilter) -> List[AuditLog]:
        """Listar logs de auditoría con filtros"""
        query = {}
        
        # Aplicar filtros
        if filters.user_id:
            query["user_id"] = filters.user_id
        if filters.clerk_id:
            query["clerk_id"] = filters.clerk_id
        if filters.action:
            query["action"] = filters.action
        if filters.resource_type:
            query["resource_type"] = filters.resource_type
        if filters.resource_id:
            query["resource_id"] = filters.resource_id
        if filters.success is not None:
            query["success"] = filters.success
        
        # Filtros de fecha
        date_filter = {}
        if filters.start_date:
            date_filter["$gte"] = filters.start_date
        if filters.end_date:
            date_filter["$lte"] = filters.end_date
        if date_filter:
            query["timestamp"] = date_filter
        
        # Ejecutar consulta con paginación
        cursor = self.collection.find(query).sort("timestamp", -1)
        
        if filters.skip > 0:
            cursor = cursor.skip(filters.skip)
        
        cursor = cursor.limit(filters.limit)
        
        logs = []
        async for log_doc in cursor:
            logs.append(AuditLog(**log_doc))
        
        return logs
    
    async def count_logs(self, filters: AuditLogFilter) -> int:
        """Contar logs que coinciden con los filtros"""
        query = {}
        
        # Aplicar filtros (misma lógica que list_logs)
        if filters.user_id:
            query["user_id"] = filters.user_id
        if filters.clerk_id:
            query["clerk_id"] = filters.clerk_id
        if filters.action:
            query["action"] = filters.action
        if filters.resource_type:
            query["resource_type"] = filters.resource_type
        if filters.resource_id:
            query["resource_id"] = filters.resource_id
        if filters.success is not None:
            query["success"] = filters.success
        
        date_filter = {}
        if filters.start_date:
            date_filter["$gte"] = filters.start_date
        if filters.end_date:
            date_filter["$lte"] = filters.end_date
        if date_filter:
            query["timestamp"] = date_filter
        
        return await self.collection.count_documents(query)
    
    async def delete_old_logs(self, days_to_keep: int = 90) -> int:
        """Eliminar logs antiguos"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        result = await self.collection.delete_many({
            "timestamp": {"$lt": cutoff_date}
        })
        
        return result.deleted_count
    
    async def get_user_activity_summary(self, clerk_id: str, days: int = 30) -> dict:
        """Obtener resumen de actividad de un usuario"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        pipeline = [
            {
                "$match": {
                    "clerk_id": clerk_id,
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$action",
                    "count": {"$sum": 1},
                    "last_occurrence": {"$max": "$timestamp"},
                    "success_count": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "error_count": {"$sum": {"$cond": ["$success", 0, 1]}}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        result = []
        async for doc in self.collection.aggregate(pipeline):
            result.append({
                "action": doc["_id"],
                "count": doc["count"],
                "last_occurrence": doc["last_occurrence"],
                "success_count": doc["success_count"],
                "error_count": doc["error_count"],
                "success_rate": doc["success_count"] / doc["count"] if doc["count"] > 0 else 0
            })
        
        total_actions = await self.collection.count_documents({
            "clerk_id": clerk_id,
            "timestamp": {"$gte": start_date}
        })
        
        return {
            "clerk_id": clerk_id,
            "period_days": days,
            "total_actions": total_actions,
            "actions_breakdown": result,
            "period_start": start_date,
            "period_end": datetime.now(timezone.utc)
        }
    
    async def get_action_statistics(self, days: int = 30) -> dict:
        """Obtener estadísticas de acciones en el período especificado"""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Pipeline para estadísticas generales
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "action": "$action",
                        "resource_type": "$resource_type"
                    },
                    "count": {"$sum": 1},
                    "success_count": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "error_count": {"$sum": {"$cond": ["$success", 0, 1]}},
                    "unique_users": {"$addToSet": "$clerk_id"}
                }
            },
            {
                "$addFields": {
                    "unique_user_count": {"$size": "$unique_users"}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        action_stats = []
        async for doc in self.collection.aggregate(pipeline):
            action_stats.append({
                "action": doc["_id"]["action"],
                "resource_type": doc["_id"]["resource_type"],
                "count": doc["count"],
                "success_count": doc["success_count"],
                "error_count": doc["error_count"],
                "unique_users": doc["unique_user_count"],
                "success_rate": doc["success_count"] / doc["count"] if doc["count"] > 0 else 0
            })
        
        # Estadísticas de usuarios más activos
        user_pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date},
                    "clerk_id": {"$ne": None}
                }
            },
            {
                "$group": {
                    "_id": "$clerk_id",
                    "action_count": {"$sum": 1},
                    "user_email": {"$first": "$user_email"},
                    "last_activity": {"$max": "$timestamp"}
                }
            },
            {
                "$sort": {"action_count": -1}
            },
            {
                "$limit": 10
            }
        ]
        
        top_users = []
        async for doc in self.collection.aggregate(user_pipeline):
            top_users.append({
                "clerk_id": doc["_id"],
                "user_email": doc["user_email"],
                "action_count": doc["action_count"],
                "last_activity": doc["last_activity"]
            })
        
        total_logs = await self.collection.count_documents({
            "timestamp": {"$gte": start_date}
        })
        
        return {
            "period_days": days,
            "period_start": start_date,
            "period_end": datetime.now(timezone.utc),
            "total_logs": total_logs,
            "action_statistics": action_stats,
            "top_active_users": top_users
        }