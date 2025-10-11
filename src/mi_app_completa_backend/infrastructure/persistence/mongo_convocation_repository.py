"""
Implementación COMPLETA del repositorio de convocatorias usando MongoDB
Compatible con ConvocationRepository interface
"""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, date
import logging

from ...domain.entities.techo_propio.convocation_entity import Convocation
from ...domain.repositories.techo_propio.convocation_repository import ConvocationRepository
from ..config.database import get_database
from ..config.timezone_config import utc_now

logger = logging.getLogger(__name__)
logger.info("🔥 CARGANDO mongo_convocation_repository.py - VERSIÓN CORREGIDA CON CURSORES")


class MongoConvocationRepository(ConvocationRepository):
    """Implementación COMPLETA de ConvocationRepository usando MongoDB"""

    def __init__(self):
        self.db = get_database()
        self.collection = self.db.convocations

        # Crear índices únicos si no existen
        try:
            self.collection.create_index("code", unique=True)
        except Exception:
            pass  # Índice ya existe

    def _entity_to_dict(self, convocation: Convocation) -> Dict[str, Any]:
        """Convierte una entidad Convocation a dict para MongoDB"""
        # Convertir date a datetime para MongoDB (Motor no puede serializar date directamente)
        start_date = convocation.start_date
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())

        end_date = convocation.end_date
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())

        doc = {
            "code": convocation.code,
            "title": convocation.title,
            "description": convocation.description,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": convocation.is_active,
            "is_published": convocation.is_published,
            "max_applications": convocation.max_applications,
            "year": convocation.year,
            "sequential_number": convocation.sequential_number,
            "created_by": convocation.created_by,
            "created_at": convocation.created_at or utc_now(),
            "updated_at": convocation.updated_at or utc_now()
        }

        if convocation.id:
            doc["_id"] = ObjectId(convocation.id)

        return doc

    def _dict_to_entity(self, doc: Dict[str, Any]) -> Convocation:
        """Convierte un documento de MongoDB a entidad Convocation"""
        # Convertir datetime a date si es necesario (MongoDB almacena como datetime)
        start_date = doc["start_date"]
        if isinstance(start_date, datetime):
            start_date = start_date.date()

        end_date = doc["end_date"]
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        conv = Convocation(
            code=doc["code"],
            title=doc["title"],
            description=doc.get("description"),
            start_date=start_date,
            end_date=end_date,
            is_active=doc.get("is_active", True),
            is_published=doc.get("is_published", False),
            max_applications=doc.get("max_applications"),
            year=doc.get("year"),
            sequential_number=doc.get("sequential_number")
        )
        conv.id = str(doc["_id"])
        conv.created_by = doc.get("created_by")
        conv.created_at = doc.get("created_at", utc_now())
        conv.updated_at = doc.get("updated_at", utc_now())
        return conv

    # ==================== CRUD BÁSICO ====================

    async def create_convocation(self, convocation: Convocation) -> Convocation:
        """Crear nueva convocatoria"""
        try:
            # Preparar documento
            doc = self._entity_to_dict(convocation)
            doc.pop("_id", None)  # MongoDB generará el ID
            doc["created_at"] = utc_now()
            doc["updated_at"] = utc_now()

            # Insertar
            result = await self.collection.insert_one(doc)

            # Devolver entidad con ID generado
            convocation.id = str(result.inserted_id)
            convocation.created_at = doc["created_at"]
            convocation.updated_at = doc["updated_at"]

            return convocation

        except Exception as e:
            if "duplicate key error" in str(e).lower():
                raise ValueError(f"Ya existe una convocatoria con el código '{convocation.code}'")
            raise

    async def get_convocation_by_id(self, convocation_id: str) -> Optional[Convocation]:
        """Obtener convocatoria por ID"""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(convocation_id)})
            return self._dict_to_entity(doc) if doc else None
        except Exception:
            return None

    async def get_convocation_by_code(self, code: str) -> Optional[Convocation]:
        """Obtener convocatoria por código"""
        doc = await self.collection.find_one({"code": code})
        return self._dict_to_entity(doc) if doc else None

    async def update_convocation(self, convocation: Convocation) -> Convocation:
        """Actualizar convocatoria existente"""
        try:
            doc = self._entity_to_dict(convocation)
            doc["updated_at"] = utc_now()

            # No actualizar el código ni el ID
            doc.pop("code", None)
            doc.pop("_id", None)
            doc.pop("created_at", None)  # Preservar fecha de creación

            result = await self.collection.update_one(
                {"_id": ObjectId(convocation.id)},
                {"$set": doc}
            )

            if result.matched_count > 0:
                convocation.updated_at = doc["updated_at"]
                return convocation
            raise ValueError("Convocatoria no encontrada")

        except Exception as e:
            raise ValueError(f"Error al actualizar convocatoria: {str(e)}")

    async def delete_convocation(self, convocation_id: str) -> bool:
        """Eliminar convocatoria"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(convocation_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    # ==================== CONSULTAS ESPECIALIZADAS ====================

    async def get_all_convocations(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Convocation]:
        """Obtener todas las convocatorias con paginación"""
        logger.info(f"✅ get_all_convocations LLAMADO - skip={skip}, limit={limit}")
        query = {} if include_inactive else {"is_active": True}
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        logger.info(f"✅ Cursor creado: {type(cursor)}")
        docs = await cursor.to_list(length=limit)  # Convertir cursor async a lista
        logger.info(f"✅ Documentos obtenidos: {len(docs)}")
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_active_convocations(self) -> List[Convocation]:
        """Obtener solo convocatorias activas"""
        cursor = self.collection.find({"is_active": True}).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_current_convocations(self) -> List[Convocation]:
        """Obtener convocatorias vigentes (en período actual)"""
        today = datetime.combine(date.today(), datetime.min.time())
        cursor = self.collection.find({
            "is_active": True,
            "start_date": {"$lte": today},
            "end_date": {"$gte": today}
        }).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_published_convocations(self) -> List[Convocation]:
        """Obtener convocatorias publicadas"""
        cursor = self.collection.find({
            "is_active": True,
            "is_published": True
        }).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_convocations_by_year(self, year: int) -> List[Convocation]:
        """Obtener convocatorias de un año específico"""
        cursor = self.collection.find({"year": year}).sort("sequential_number", 1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_upcoming_convocations(self) -> List[Convocation]:
        """Obtener convocatorias futuras"""
        today = datetime.combine(date.today(), datetime.min.time())
        cursor = self.collection.find({
            "is_active": True,
            "start_date": {"$gt": today}
        }).sort("start_date", 1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    async def get_expired_convocations(self) -> List[Convocation]:
        """Obtener convocatorias expiradas"""
        today = datetime.combine(date.today(), datetime.min.time())
        cursor = self.collection.find({
            "end_date": {"$lt": today}
        }).sort("end_date", -1)
        docs = await cursor.to_list(length=None)
        return [self._dict_to_entity(doc) for doc in docs]

    # ==================== VALIDACIONES Y UTILIDADES ====================

    async def code_exists(self, code: str, exclude_id: Optional[str] = None) -> bool:
        """Verificar si un código de convocatoria ya existe"""
        query = {"code": code}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        count = await self.collection.count_documents(query)
        return count > 0

    async def get_next_sequential_number(self, year: int) -> int:
        """Obtener el siguiente número secuencial para un año"""
        # Buscar la convocatoria con el número secuencial más alto del año
        result = await self.collection.find_one(
            {"year": year},
            sort=[("sequential_number", -1)]
        )

        if result and result.get("sequential_number"):
            return result["sequential_number"] + 1
        return 1

    async def count_applications_by_convocation(self, convocation_code: str) -> int:
        """Contar solicitudes asociadas a una convocatoria"""
        # Aquí deberías contar en la colección de applications
        # Por ahora retorna 0 (implementar cuando tengamos la colección de solicitudes)
        return 0

    # ==================== OPERACIONES MASIVAS ====================

    async def activate_convocation(self, convocation_id: str) -> bool:
        """Activar una convocatoria"""
        result = await self.collection.update_one(
            {"_id": ObjectId(convocation_id)},
            {"$set": {"is_active": True, "updated_at": utc_now()}}
        )
        return result.matched_count > 0

    async def deactivate_convocation(self, convocation_id: str) -> bool:
        """Desactivar una convocatoria"""
        result = await self.collection.update_one(
            {"_id": ObjectId(convocation_id)},
            {"$set": {"is_active": False, "updated_at": utc_now()}}
        )
        return result.matched_count > 0

    async def publish_convocation(self, convocation_id: str) -> bool:
        """Publicar una convocatoria"""
        result = await self.collection.update_one(
            {"_id": ObjectId(convocation_id)},
            {"$set": {"is_published": True, "updated_at": utc_now()}}
        )
        return result.matched_count > 0

    async def unpublish_convocation(self, convocation_id: str) -> bool:
        """Despublicar una convocatoria"""
        result = await self.collection.update_one(
            {"_id": ObjectId(convocation_id)},
            {"$set": {"is_published": False, "updated_at": utc_now()}}
        )
        return result.matched_count > 0

    async def extend_convocation_deadline(
        self,
        convocation_id: str,
        new_end_date: date
    ) -> bool:
        """Extender fecha límite de una convocatoria"""
        # Convertir date a datetime para MongoDB
        end_date_datetime = new_end_date
        if isinstance(new_end_date, date) and not isinstance(new_end_date, datetime):
            end_date_datetime = datetime.combine(new_end_date, datetime.min.time())

        result = await self.collection.update_one(
            {"_id": ObjectId(convocation_id)},
            {"$set": {"end_date": end_date_datetime, "updated_at": utc_now()}}
        )
        return result.matched_count > 0

    # ==================== ESTADÍSTICAS ====================

    async def get_convocation_statistics(self, convocation_code: str) -> dict:
        """Obtener estadísticas de una convocatoria específica"""
        return {
            "convocation_code": convocation_code,
            "total_applications": 0,
            "applications_by_status": {},
            "average_priority_score": 0.0,
            "completion_rate": 0.0,
            "applications_per_day": {}
        }

    async def get_general_statistics(self) -> dict:
        """Obtener estadísticas generales"""
        total = await self.collection.count_documents({})
        active = await self.collection.count_documents({"is_active": True})
        published = await self.collection.count_documents({"is_published": True})

        return {
            "total_convocations": total,
            "active_convocations": active,
            "published_convocations": published,
            "total_applications_all_convocations": 0
        }
