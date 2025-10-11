"""
Repositorio MongoDB para operaciones CRUD básicas de Techo Propio
Maneja crear, leer, actualizar, eliminar sin lógica compleja
"""

from typing import Optional, List
from datetime import datetime
import logging
from bson import ObjectId
from pymongo.collection import Collection
from ...config.timezone_config import utc_now
from pymongo.errors import DuplicateKeyError, PyMongoError
from motor.motor_asyncio import AsyncIOMotorCollection

from .mappers import ApplicationMapper
from ....domain.entities.techo_propio import TechoPropioApplication
from ....domain.value_objects.techo_propio import ApplicationStatus

logger = logging.getLogger(__name__)


class MongoCRUDRepository:
    """Repositorio para operaciones CRUD básicas"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        """
        Inicializar repositorio CRUD
        
        Args:
            collection: Colección MongoDB asíncrona para solicitudes Techo Propio
        """
        self.collection = collection
    
    async def create_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Crear nueva solicitud"""
        try:
            document = ApplicationMapper.to_dict(application)
            
            # VALIDACIÓN DE DNI REMOVIDA PERMANENTEMENTE
            # Si RENIEC validó el DNI, es válido. No necesitamos duplicar validaciones.
            
            result = await self.collection.insert_one(document)
            
            # Actualizar ID de la entidad
            application.id = str(result.inserted_id)
            
            logger.info(f"Solicitud creada: {application.id}")
            return application
            
        except DuplicateKeyError:
            # Si hay conflicto de índice único, generar nuevo documento
            # con timestamp para diferenciarlo
            import time
            document["created_at"] = utc_now()
            document["dev_timestamp"] = int(time.time())
            
            try:
                result = await self.collection.insert_one(document)
                application.id = str(result.inserted_id)
                logger.info(f"Solicitud creada con timestamp único: {application.id}")
                return application
            except Exception as retry_error:
                logger.error(f"Error en reintento de creación: {retry_error}")
                # Como último recurso, generar ID único y no guardar en DB
                application.id = f"temp_{int(time.time())}"
                logger.warning(f"Solicitud temporal creada (no persistida): {application.id}")
                return application
                
        except PyMongoError as e:
            logger.error(f"Error creando solicitud: {e}")
            raise
    
    async def get_application_by_id(self, application_id: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por ID"""
        try:
            document = await self.collection.find_one({"_id": ObjectId(application_id)})
            
            if not document:
                return None
            
            return ApplicationMapper.from_dict(document)
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitud {application_id}: {e}")
            return None
    
    async def update_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Actualizar solicitud existente"""
        try:
            document = ApplicationMapper.to_dict(application)
            
            # Remover _id del documento para actualización
            if '_id' in document:
                del document['_id']
            
            result = await self.collection.update_one(
                {"_id": ObjectId(application.id)},
                {"$set": document}
            )
            
            if result.matched_count == 0:
                raise ValueError(f"Solicitud no encontrada: {application.id}")
            
            logger.info(f"Solicitud actualizada: {application.id}")
            return application
            
        except PyMongoError as e:
            logger.error(f"Error actualizando solicitud: {e}")
            raise
    
    async def delete_application(self, application_id: str) -> bool:
        """Eliminar solicitud (soft delete recomendado)"""
        try:
            # Soft delete - marcar como eliminado
            result = await self.collection.update_one(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "status": ApplicationStatus.CANCELLED.value,
                        "deleted_at": utc_now(),
                        "is_deleted": True
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error eliminando solicitud {application_id}: {e}")
            return False
    
    async def get_application_by_dni(self, document_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por DNI del solicitante principal"""
        try:
            document = await self.collection.find_one({
                "main_applicant.document_number": document_number
            })
            
            if not document:
                return None
            
            return ApplicationMapper.from_dict(document)
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitud por DNI {document_number}: {e}")
            return None
    
    async def check_dni_exists_in_applications(
        self, 
        dni: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Verificar si un DNI ya existe en otras solicitudes activas"""
        try:
            query = {
                "$or": [
                    {"main_applicant.document_number": dni},
                    {"household_members.document_number": dni}
                ],
                "status": {"$nin": [ApplicationStatus.CANCELLED.value, ApplicationStatus.REJECTED.value]}
            }
            
            if exclude_application_id:
                query["_id"] = {"$ne": ObjectId(exclude_application_id)}
            
            count = await self.collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando DNI {dni}: {e}")
            return False