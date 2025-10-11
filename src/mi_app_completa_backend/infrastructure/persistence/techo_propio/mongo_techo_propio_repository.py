"""
Repositorio MongoDB Refactorizado para Techo Propio
Orchestrador que coordina CRUD, Query y Statistics repositories
REEMPLAZA el archivo mongo_techo_propio_repository.py original de 1474 líneas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from motor.motor_asyncio import AsyncIOMotorCollection

# Importar entidades de dominio
from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import ApplicationStatus
from ....domain.repositories.techo_propio import TechoPropioRepository

# Importar configuración existente
from ...config.database import get_database

# Importar repositorios especializados
from .mongo_crud_repository import MongoCRUDRepository
from .mongo_query_repository import MongoQueryRepository
from .mongo_statistics_repository import MongoStatisticsRepository

logger = logging.getLogger(__name__)


class MongoTechoPropioRepository(TechoPropioRepository):
    """
    Repositorio MongoDB Refactorizado para Techo Propio
    
    Orchestrador que coordina:
    - CRUD básico (crear, leer, actualizar, eliminar)
    - Consultas complejas (búsquedas, filtros)
    - Estadísticas y reportes (conteos, agregaciones)
    
    BENEFICIOS DE LA REFACTORIZACIÓN:
    - Reducido de 1474 a ~300 líneas
    - Separación clara de responsabilidades
    - Facilita testing y mantenimiento
    - Reutilización de componentes
    """
    
    def __init__(self, db_client: MongoClient = None):
        """
        Inicializar repositorio orchestrador
        
        Args:
            db_client: Cliente MongoDB (opcional, se obtiene de configuración si no se proporciona)
        """
        self.db = get_database() if db_client is None else db_client.get_database()
        self.collection: AsyncIOMotorCollection = self.db.techo_propio_applications
        
        # Inicializar repositorios especializados
        self.crud_repo = MongoCRUDRepository(self.collection)
        self.query_repo = MongoQueryRepository(self.collection)
        self.stats_repo = MongoStatisticsRepository(self.collection)
        
        # NOTA: Los índices deben crearse una sola vez manualmente o mediante migración
        # No se pueden crear síncronamente en el constructor con AsyncIOMotorCollection
        # self._create_indexes()
        logger.info("Repositorio MongoDB inicializado (índices deben crearse por separado)")
    
    def _create_indexes(self) -> None:
        """Crear índices para optimizar consultas"""
        try:
            # Solo crear índices si estamos en el contexto principal
            import threading
            if threading.current_thread() is not threading.main_thread():
                logger.info("Saltando creación de índices en worker thread")
                return
                
            # Índice NO ÚNICO para DNI del solicitante principal (para performance)
            # VALIDACIÓN DE DNI REMOVIDA: RENIEC ya valida, no necesitamos duplicar
            self.collection.create_index(
                "main_applicant.document_number",
                unique=False,  # No único, permite múltiples solicitudes del mismo DNI
                name="main_applicant_dni_index"
            )
            
            # Índices para búsquedas frecuentes
            self.collection.create_index("status", name="status_index")
            self.collection.create_index("created_by", name="created_by_index")
            self.collection.create_index("created_at", name="created_at_index")
            
            # Índices compuestos
            self.collection.create_index([
                ("status", ASCENDING),
                ("created_at", DESCENDING)
            ], name="status_created_at_index")
            
            self.collection.create_index([
                ("property_info.department", ASCENDING),
                ("property_info.province", ASCENDING),
                ("property_info.district", ASCENDING)
            ], name="location_index")
            
            # Índice de texto para búsquedas
            self.collection.create_index([
                ("main_applicant.first_name", "text"),
                ("main_applicant.paternal_surname", "text"),
                ("main_applicant.maternal_surname", "text"),
                ("main_applicant.document_number", "text")
            ], name="text_search_index")
            
            logger.info("Índices MongoDB creados exitosamente")
            
        except Exception as e:
            logger.error(f"Error creando índices: {e}")
    
    # ==================== DELEGACIÓN A REPOSITORIOS ESPECIALIZADOS ====================
    
    # === OPERACIONES CRUD (Delegación a CRUDRepository) ===
    
    async def save_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Guardar nueva solicitud (delegado a CRUD repo)"""
        return await self.crud_repo.create_application(application)
    
    async def create_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Crear nueva solicitud (alias para save_application)"""
        return await self.save_application(application)
    
    async def update_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Actualizar solicitud existente (delegado a CRUD repo)"""
        return await self.crud_repo.update_application(application)
    
    async def get_application_by_id(self, application_id: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por ID (delegado a CRUD repo)"""
        return await self.crud_repo.get_application_by_id(application_id)
    
    async def get_application_by_dni(self, document_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por DNI (delegado a CRUD repo)"""
        return await self.crud_repo.get_application_by_dni(document_number)
    
    async def delete_application(self, application_id: str) -> bool:
        """Eliminar solicitud (delegado a CRUD repo)"""
        return await self.crud_repo.delete_application(application_id)
    
    async def check_dni_exists_in_applications(
        self, 
        document_number: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Verificar si DNI existe (delegado a CRUD repo)"""
        return await self.crud_repo.check_dni_exists_in_applications(
            document_number, exclude_application_id
        )
    
    # === OPERACIONES DE CONSULTA (Delegación a QueryRepository) ===
    
    async def get_applications_by_user(
        self,
        user_id: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes de usuario (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_user(
            user_id, status, limit, offset
        )
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por estado (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_status(
            status, limit, offset
        )
    
    async def get_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por ubicación (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_location(
            department, province, district, page, page_size
        )
    
    async def get_applications_by_priority(
        self,
        page: int = 1,
        page_size: int = 20,
        min_priority_score: Optional[float] = None
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por prioridad (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_priority(
            page, page_size, min_priority_score
        )
    
    async def search_applications(
        self,
        search_query: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> List[TechoPropioApplication]:
        """Búsqueda avanzada (delegado a Query repo)"""
        return await self.query_repo.search_applications(search_query, page, page_size)
    
    async def get_applications_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por rango de fechas (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_date_range(
            start_date, end_date, status, limit, offset
        )
    
    async def get_applications_by_dni(self, dni: str) -> List[TechoPropioApplication]:
        """Obtener todas las solicitudes con DNI específico (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_dni(dni)
    
    # === OPERACIONES DE ESTADÍSTICAS (Delegación a StatisticsRepository) ===
    
    async def count_all_applications(self) -> int:
        """Contar todas las solicitudes (delegado a Stats repo)"""
        return await self.stats_repo.count_all_applications()
    
    async def count_applications_by_user(
        self,
        user_id: str,
        status: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de usuario (delegado a Query repo)"""
        return await self.query_repo.count_applications_by_user(user_id, status)
    
    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado (delegado a Query repo)"""
        return await self.query_repo.count_applications_by_status(status)
    
    async def count_applications_by_location(
        self,
        department: Optional[str] = None,
        province: Optional[str] = None,
        district: Optional[str] = None
    ) -> int:
        """Contar solicitudes por ubicación (delegado a Stats repo)"""
        return await self.stats_repo.count_applications_by_location(department, province, district)
    
    async def count_search_results(self, search_query: Dict[str, Any]) -> int:
        """Contar resultados de búsqueda (delegado a Stats repo)"""
        return await self.stats_repo.count_search_results(search_query)
    
    async def count_priority_applications(self, min_priority_score: Optional[float] = None) -> int:
        """Contar solicitudes prioritarias (delegado a Stats repo)"""
        return await self.stats_repo.count_priority_applications(min_priority_score)
    
    async def get_application_statistics(
        self,
        department: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Obtener estadísticas detalladas (delegado a Stats repo)"""
        return await self.stats_repo.get_application_statistics(department, date_from, date_to)
    
    # ==================== MÉTODOS DE COMPATIBILIDAD ====================
    # Métodos adicionales para mantener compatibilidad con código existente
    
    async def get_application_by_number(self, application_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por número de solicitud"""
        # Implementación usando query repo
        query = {"application_number": application_number}
        results = await self.query_repo.search_applications(query, page=1, page_size=1)
        return results[0] if results else None
    
    async def bulk_update_status(
        self,
        application_ids: List[str],
        new_status: ApplicationStatus,
        updated_by: str,
        reason: Optional[str] = None
    ) -> int:
        """Actualizar estado de múltiples solicitudes"""
        try:
            from bson import ObjectId
            
            object_ids = [ObjectId(app_id) for app_id in application_ids]
            
            update_doc = {
                "$set": {
                    "status": new_status.value,
                    "updated_at": datetime.now(),
                    "updated_by": updated_by
                }
            }
            
            if reason:
                update_doc["$set"]["status_change_reason"] = reason
            
            result = await self.collection.update_many(
                {"_id": {"$in": object_ids}},
                update_doc
            )
            
            logger.info(f"Bulk update: {result.modified_count} applications updated to {new_status.value}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error en actualización masiva: {e}")
            return 0
    
    # ==================== MÉTODOS DE UTILIDAD ====================
    
    # ==================== MÉTODOS FALTANTES PARA COMPLETAR INTERFAZ ABSTRACTA ====================
    
    async def check_application_number_exists(self, application_number: str) -> bool:
        """Verificar si un número de solicitud ya existe"""
        try:
            count = await self.collection.count_documents({
                "application_number": application_number
            })
            return count > 0
        except Exception as e:
            logger.error(f"Error verificando número de solicitud {application_number}: {e}")
            return False
    
    async def get_application_history(self, application_id: str) -> List[Dict[str, Any]]:
        """Obtener historial de cambios de una solicitud"""
        try:
            # Por simplicidad, retornamos historial vacío
            # En producción, esto debería consultar una colección de auditoría
            return []
        except Exception as e:
            logger.error(f"Error obteniendo historial de solicitud {application_id}: {e}")
            return []
    
    async def get_applications_by_department(
        self,
        department: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por departamento (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_department(
            department, status, limit, offset
        )
    
    async def get_applications_by_district(
        self,
        department: str,
        province: str,
        district: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por distrito específico (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_district(
            department, province, district, status, limit, offset
        )
    
    async def get_applications_by_household_size(
        self,
        min_size: int,
        max_size: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por tamaño de familia (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_household_size(
            min_size, max_size, limit, offset
        )
    
    async def get_applications_by_income_range(
        self,
        min_income: float,
        max_income: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por rango de ingresos (delegado a Query repo)"""
        return await self.query_repo.get_applications_by_income_range(
            min_income, max_income, limit, offset
        )
    
    async def get_applications_submitted_today(self) -> List[TechoPropioApplication]:
        """Obtener solicitudes enviadas hoy (delegado a Query repo)"""
        return await self.query_repo.get_applications_submitted_today()
    
    async def get_expired_draft_applications(
        self,
        days_old: int = 30
    ) -> List[TechoPropioApplication]:
        """Obtener borradores expirados para limpieza (delegado a Query repo)"""
        return await self.query_repo.get_expired_draft_applications(days_old)
    
    async def get_pending_review_applications(
        self,
        reviewer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes pendientes de revisión (delegado a Query repo)"""
        return await self.query_repo.get_pending_review_applications(
            reviewer_id, limit, offset
        )
    
    async def log_application_change(
        self,
        application_id: str,
        user_id: str,
        action: str,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Registrar cambio en solicitud para auditoría"""
        try:
            # Por simplicidad, solo loggeamos. En producción se guardaría en colección de auditoría
            logger.info(f"Application {application_id} - Action: {action} by User: {user_id}")
            if old_values:
                logger.info(f"Old values: {old_values}")
            if new_values:
                logger.info(f"New values: {new_values}")
            
            return True
        except Exception as e:
            logger.error(f"Error registrando cambio de solicitud: {e}")
            return False
    
    # ==================== MÉTODO DE SALUD MANTENIDO ====================
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud del repositorio"""
        try:
            # Verificar conexión a MongoDB
            self.db.command('ping')
            
            return {
                "status": "healthy",
                "database": self.db.name,
                "collection": self.collection.name,
                "components": {
                    "crud_repo": "initialized",
                    "query_repo": "initialized", 
                    "stats_repo": "initialized"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }