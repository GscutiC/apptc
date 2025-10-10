"""
Implementación MongoDB del repositorio Techo Propio
Maneja persistencia, queries complejas, y mapeo entidad-documento
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError, PyMongoError

# Importar entidades de dominio
from ....domain.entities.techo_propio import (
    TechoPropioApplication, Applicant, PropertyInfo,
    HouseholdMember, EconomicInfo
)
from ....domain.value_objects.techo_propio import ApplicationStatus
from ....domain.repositories.techo_propio import TechoPropioRepository

# Importar configuración existente
from ...config.database import get_database


logger = logging.getLogger(__name__)


class MongoTechoPropioRepository(TechoPropioRepository):
    """
    Implementación MongoDB del repositorio Techo Propio
    Maneja toda la persistencia y queries complejas para el módulo
    """
    
    def __init__(self, db_client: MongoClient = None):
        """
        Inicializar repositorio MongoDB
        
        Args:
            db_client: Cliente MongoDB (opcional, se obtiene de configuración si no se proporciona)
        """
        self.db = get_database() if db_client is None else db_client.get_database()
        self.collection: Collection = self.db.techo_propio_applications
        
        # Crear índices necesarios
        self._create_indexes()
    
    def _create_indexes(self) -> None:
        """Crear índices para optimizar consultas"""
        try:
            # Solo crear índices si estamos en el contexto principal, no en worker threads
            import threading
            if threading.current_thread() is not threading.main_thread():
                logger.info("Saltando creación de índices en worker thread")
                return
                
            # Índice único para DNI del solicitante principal
            self.collection.create_index(
                "main_applicant.document_number",
                unique=True,
                name="unique_main_applicant_dni"
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
    
    async def save_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Guardar nueva solicitud"""
        try:
            document = self._entity_to_document(application)
            result = self.collection.insert_one(document)
            
            # Actualizar ID de la entidad
            application.id = str(result.inserted_id)
            
            logger.info(f"Solicitud guardada: {application.id}")
            return application
            
        except DuplicateKeyError:
            raise ValueError(f"Ya existe una solicitud con el DNI {application.main_applicant.document_number}")
        except PyMongoError as e:
            logger.error(f"Error guardando solicitud: {e}")
            raise
    
    async def update_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Actualizar solicitud existente"""
        try:
            document = self._entity_to_document(application)
            
            # Remover _id del documento para actualización
            if '_id' in document:
                del document['_id']
            
            result = self.collection.update_one(
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
    
    async def get_application_by_id(self, application_id: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por ID"""
        try:
            document = self.collection.find_one({"_id": ObjectId(application_id)})
            
            if not document:
                return None
            
            return self._document_to_entity(document)
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitud {application_id}: {e}")
            return None
    
    async def get_application_by_dni(self, document_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por DNI del solicitante principal"""
        try:
            document = self.collection.find_one({
                "main_applicant.document_number": document_number
            })
            
            if not document:
                return None
            
            return self._document_to_entity(document)
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitud por DNI {document_number}: {e}")
            return None
    
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
                applications.append(self._document_to_entity(document))
            
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
                applications.append(self._document_to_entity(document))
            
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
                applications.append(self._document_to_entity(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por ubicación: {e}")
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
                applications.append(self._document_to_entity(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {e}")
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
                applications.append(self._document_to_entity(document))
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por prioridad: {e}")
            return []
    
    async def check_dni_exists_in_applications(
        self,
        document_number: str,
        exclude_application_id: Optional[str] = None
    ) -> bool:
        """Verificar si DNI existe en solicitudes activas"""
        try:
            query = {
                "$or": [
                    {"main_applicant.document_number": document_number},
                    {"spouse.document_number": document_number},
                    {"household_members.document_number": document_number}
                ]
            }
            
            if exclude_application_id:
                query["_id"] = {"$ne": ObjectId(exclude_application_id)}
            
            count = self.collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando DNI {document_number}: {e}")
            return False
    
    async def delete_application(self, application_id: str) -> bool:
        """Eliminar solicitud"""
        try:
            result = self.collection.delete_one({"_id": ObjectId(application_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error eliminando solicitud {application_id}: {e}")
            return False
    
    # Métodos de conteo
    async def count_all_applications(self) -> int:
        """Contar todas las solicitudes"""
        return self.collection.count_documents({})
    
    async def count_applications_by_user(
        self,
        user_id: str,
        status_filter: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de un usuario"""
        query = {"created_by": user_id}
        if status_filter:
            query["status"] = status_filter.value
        return self.collection.count_documents(query)
    
    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado"""
        return self.collection.count_documents({"status": status.value})
    
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
        
        return self.collection.count_documents(query)
    
    async def count_search_results(self, search_query: Dict[str, Any]) -> int:
        """Contar resultados de búsqueda"""
        mongo_query = self._build_mongo_query(search_query)
        return self.collection.count_documents(mongo_query)
    
    async def count_priority_applications(self, min_priority_score: Optional[float] = None) -> int:
        """Contar solicitudes prioritarias"""
        query = {}
        if min_priority_score is not None:
            query["priority_score"] = {"$gte": min_priority_score}
        return self.collection.count_documents(query)
    
    # Métodos de estadísticas
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
            
            result = list(self.collection.aggregate(pipeline))
            
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
    
    def _entity_to_document(self, application: TechoPropioApplication) -> Dict[str, Any]:
        """Convertir entidad a documento MongoDB"""
        document = {
            "status": application.status.value,
            "priority_score": float(application.priority_score),
            "created_by": application.created_by,
            "created_at": application.created_at,
            "updated_at": application.updated_at,
            "updated_by": application.updated_by,
            "version": application.version,
            
            # Solicitante principal
            "main_applicant": self._applicant_to_dict(application.main_applicant),
            
            # Información del predio
            "property_info": self._property_info_to_dict(application.property_info),
            
            # Información económica principal
            "main_applicant_economic": self._economic_info_to_dict(application.main_applicant_economic),
        }
        
        # Cónyuge (opcional)
        if application.spouse:
            document["spouse"] = self._applicant_to_dict(application.spouse)
        
        # Información económica del cónyuge (opcional)
        if application.spouse_economic:
            document["spouse_economic"] = self._economic_info_to_dict(application.spouse_economic)
        
        # Miembros de carga familiar
        if application.household_members:
            document["household_members"] = [
                self._household_member_to_dict(member) 
                for member in application.household_members
            ]
        
        # Datos de auditoría adicionales
        if hasattr(application, 'submitted_at') and application.submitted_at:
            document["submitted_at"] = application.submitted_at
        
        if hasattr(application, 'reviewed_at') and application.reviewed_at:
            document["reviewed_at"] = application.reviewed_at
        
        if hasattr(application, 'reviewer_id') and application.reviewer_id:
            document["reviewer_id"] = application.reviewer_id
        
        return document
    
    def _document_to_entity(self, document: Dict[str, Any]) -> TechoPropioApplication:
        """Convertir documento MongoDB a entidad"""
        
        # Crear solicitante principal
        main_applicant = self._dict_to_applicant(document["main_applicant"])
        
        # Crear información del predio
        property_info = self._dict_to_property_info(document["property_info"])
        
        # Crear información económica principal
        main_applicant_economic = self._dict_to_economic_info(document["main_applicant_economic"])
        
        # Crear solicitud
        application = TechoPropioApplication(
            main_applicant=main_applicant,
            property_info=property_info,
            main_applicant_economic=main_applicant_economic,
            created_by=document["created_by"]
        )
        
        # Asignar ID
        application.id = str(document["_id"])
        
        # Restaurar metadatos
        application.status = ApplicationStatus(document["status"])
        application.priority_score = document.get("priority_score", 0.0)
        application.created_at = document["created_at"]
        application.updated_at = document.get("updated_at")
        application.updated_by = document.get("updated_by")
        application.version = document.get("version", 1)
        
        # Restaurar cónyuge si existe
        if "spouse" in document:
            spouse = self._dict_to_applicant(document["spouse"])
            application.set_spouse(spouse)
        
        # Restaurar información económica del cónyuge
        if "spouse_economic" in document:
            application.spouse_economic = self._dict_to_economic_info(document["spouse_economic"])
        
        # Restaurar miembros de carga familiar
        if "household_members" in document:
            application.household_members = [
                self._dict_to_household_member(member_dict)
                for member_dict in document["household_members"]
            ]
        
        # Restaurar datos de auditoría adicionales
        if "submitted_at" in document:
            application.submitted_at = document["submitted_at"]
        
        if "reviewed_at" in document:
            application.reviewed_at = document["reviewed_at"]
        
        if "reviewer_id" in document:
            application.reviewer_id = document["reviewer_id"]
        
        return application
    
    def _applicant_to_dict(self, applicant: Applicant) -> Dict[str, Any]:
        """Convertir Applicant a diccionario"""
        return {
            "id": applicant.id,
            "document_type": applicant.document_type.value,
            "document_number": applicant.document_number,
            "first_name": applicant.first_name,
            "paternal_surname": applicant.paternal_surname,
            "maternal_surname": applicant.maternal_surname,
            "birth_date": applicant.birth_date.isoformat(),
            "civil_status": applicant.civil_status.value,
            "education_level": applicant.education_level.value,
            "occupation": applicant.occupation.value if applicant.occupation else None,
            "disability_type": applicant.disability_type.value if applicant.disability_type else None,
            "is_main_applicant": applicant.is_main_applicant,
            "phone_number": applicant.phone_number,
            "email": applicant.email,
            "created_at": applicant.created_at,
            "updated_at": applicant.updated_at
        }
    
    def _dict_to_applicant(self, data: Dict[str, Any]) -> Applicant:
        """Convertir diccionario a Applicant"""
        from ....domain.value_objects.techo_propio import (
            DocumentType, CivilStatus, EducationLevel, 
            Occupation, DisabilityType
        )
        
        applicant = Applicant(
            document_type=DocumentType(data["document_type"]),
            document_number=data["document_number"],
            first_name=data["first_name"],
            paternal_surname=data["paternal_surname"],
            maternal_surname=data["maternal_surname"],
            birth_date=datetime.fromisoformat(data["birth_date"]).date(),
            civil_status=CivilStatus(data["civil_status"]),
            education_level=EducationLevel(data["education_level"]),
            occupation=Occupation(data["occupation"]) if data.get("occupation") else None,
            disability_type=DisabilityType(data["disability_type"]) if data.get("disability_type") else None,
            is_main_applicant=data["is_main_applicant"],
            phone_number=data.get("phone_number"),
            email=data.get("email")
        )
        
        applicant.id = data["id"]
        applicant.created_at = data["created_at"]
        applicant.updated_at = data.get("updated_at")
        
        return applicant
    
    def _property_info_to_dict(self, property_info: PropertyInfo) -> Dict[str, Any]:
        """Convertir PropertyInfo a diccionario"""
        return {
            "id": property_info.id,
            "department": property_info.department,
            "province": property_info.province,
            "district": property_info.district,
            "lote": property_info.lote,
            "ubigeo_code": property_info.ubigeo_code,
            "populated_center": property_info.populated_center,
            "manzana": property_info.manzana,
            "sub_lote": property_info.sub_lote,
            "reference": property_info.reference,
            "latitude": float(property_info.latitude) if property_info.latitude else None,
            "longitude": float(property_info.longitude) if property_info.longitude else None,
            "created_at": property_info.created_at,
            "updated_at": property_info.updated_at
        }
    
    def _dict_to_property_info(self, data: Dict[str, Any]) -> PropertyInfo:
        """Convertir diccionario a PropertyInfo"""
        property_info = PropertyInfo(
            department=data["department"],
            province=data["province"],
            district=data["district"],
            lote=data["lote"],
            ubigeo_code=data.get("ubigeo_code"),
            populated_center=data.get("populated_center"),
            manzana=data.get("manzana"),
            sub_lote=data.get("sub_lote"),
            reference=data.get("reference"),
            latitude=Decimal(str(data["latitude"])) if data.get("latitude") else None,
            longitude=Decimal(str(data["longitude"])) if data.get("longitude") else None
        )
        
        property_info.id = data["id"]
        property_info.created_at = data["created_at"]
        property_info.updated_at = data.get("updated_at")
        
        return property_info
    
    def _economic_info_to_dict(self, economic_info: EconomicInfo) -> Dict[str, Any]:
        """Convertir EconomicInfo a diccionario"""
        return {
            "id": economic_info.id,
            "employment_situation": economic_info.employment_situation.value,
            "monthly_income": float(economic_info.monthly_income),
            "applicant_id": economic_info.applicant_id,
            "work_condition": economic_info.work_condition.value if economic_info.work_condition else None,
            "occupation_detail": economic_info.occupation_detail,
            "employer_name": economic_info.employer_name,
            "has_additional_income": economic_info.has_additional_income,
            "additional_income_amount": float(economic_info.additional_income_amount) if economic_info.additional_income_amount else None,
            "additional_income_source": economic_info.additional_income_source,
            "is_main_applicant": economic_info.is_main_applicant,
            "created_at": economic_info.created_at,
            "updated_at": economic_info.updated_at
        }
    
    def _dict_to_economic_info(self, data: Dict[str, Any]) -> EconomicInfo:
        """Convertir diccionario a EconomicInfo"""
        from ....domain.value_objects.techo_propio import (
            EmploymentSituation, WorkCondition
        )
        
        economic_info = EconomicInfo(
            employment_situation=EmploymentSituation(data["employment_situation"]),
            monthly_income=Decimal(str(data["monthly_income"])),
            applicant_id=data["applicant_id"],
            work_condition=WorkCondition(data["work_condition"]) if data.get("work_condition") else None,
            occupation_detail=data.get("occupation_detail"),
            employer_name=data.get("employer_name"),
            has_additional_income=data.get("has_additional_income", False),
            additional_income_amount=Decimal(str(data["additional_income_amount"])) if data.get("additional_income_amount") else None,
            additional_income_source=data.get("additional_income_source"),
            is_main_applicant=data.get("is_main_applicant", False)
        )
        
        economic_info.id = data["id"]
        economic_info.created_at = data["created_at"]
        economic_info.updated_at = data.get("updated_at")
        
        return economic_info
    
    def _household_member_to_dict(self, member: HouseholdMember) -> Dict[str, Any]:
        """Convertir HouseholdMember a diccionario"""
        return {
            "id": member.id,
            "first_name": member.first_name,
            "paternal_surname": member.paternal_surname,
            "maternal_surname": member.maternal_surname,
            "document_type": member.document_type.value,
            "document_number": member.document_number,
            "birth_date": member.birth_date.isoformat(),
            "relationship": member.relationship.value,
            "education_level": member.education_level.value if member.education_level else None,
            "disability_type": member.disability_type.value if member.disability_type else None,
            "is_dependent": member.is_dependent,
            "created_at": member.created_at,
            "updated_at": member.updated_at
        }
    
    def _dict_to_household_member(self, data: Dict[str, Any]) -> HouseholdMember:
        """Convertir diccionario a HouseholdMember"""
        from ....domain.value_objects.techo_propio import (
            DocumentType, FamilyRelationship, EducationLevel, DisabilityType
        )
        
        member = HouseholdMember(
            first_name=data["first_name"],
            paternal_surname=data["paternal_surname"],
            maternal_surname=data["maternal_surname"],
            document_type=DocumentType(data["document_type"]),
            document_number=data["document_number"],
            birth_date=datetime.fromisoformat(data["birth_date"]).date(),
            relationship=FamilyRelationship(data["relationship"]),
            education_level=EducationLevel(data["education_level"]) if data.get("education_level") else None,
            disability_type=DisabilityType(data["disability_type"]) if data.get("disability_type") else None,
            is_dependent=data.get("is_dependent", True)
        )
        
        member.id = data["id"]
        member.created_at = data["created_at"]
        member.updated_at = data.get("updated_at")
        
        return member
    
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
        
        # Filtros familiares
        if search_query.get("has_spouse") is not None:
            if search_query["has_spouse"]:
                mongo_query["spouse"] = {"$exists": True}
            else:
                mongo_query["spouse"] = {"$exists": False}
        
        if search_query.get("min_household_members") or search_query.get("max_household_members"):
            household_filter = {}
            if search_query.get("min_household_members"):
                household_filter["$gte"] = search_query["min_household_members"]
            if search_query.get("max_household_members"):
                household_filter["$lte"] = search_query["max_household_members"]
            mongo_query["household_members"] = {"$size": household_filter}
        
        # Filtros de prioridad
        if search_query.get("min_priority_score") or search_query.get("max_priority_score"):
            priority_filter = {}
            if search_query.get("min_priority_score"):
                priority_filter["$gte"] = search_query["min_priority_score"]
            if search_query.get("max_priority_score"):
                priority_filter["$lte"] = search_query["max_priority_score"]
            mongo_query["priority_score"] = priority_filter
        
        return mongo_query

    # ===== MÉTODOS FALTANTES PARA COMPLETAR LA IMPLEMENTACIÓN =====
    
    async def create_application(self, application: TechoPropioApplication) -> TechoPropioApplication:
        """Crear nueva solicitud (alias para save_application)"""
        return await self.save_application(application)
    
    async def get_application_by_number(self, application_number: str) -> Optional[TechoPropioApplication]:
        """Obtener solicitud por número de solicitud"""
        try:
            document = self.collection.find_one({
                "application_number": application_number
            })
            
            if not document:
                return None
            
            return self._document_to_entity(document)
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitud por número {application_number}: {e}")
            return None
    
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
            
            documents = list(self.collection.find(query))
            applications = []
            
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento a entidad: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por DNI {dni}: {e}")
            return []
    
    async def check_application_number_exists(self, application_number: str) -> bool:
        """Verificar si un número de solicitud ya existe"""
        try:
            count = self.collection.count_documents({
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
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por rango de fechas: {e}")
            return []
    
    async def get_applications_by_department(
        self,
        department: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por departamento"""
        try:
            query = {"property_info.department": department}
            
            if status:
                query["status"] = status.value
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
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
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por distrito específico"""
        try:
            query = {
                "property_info.department": department,
                "property_info.province": province,
                "property_info.district": district
            }
            
            if status:
                query["status"] = status.value
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por distrito: {e}")
            return []
    
    async def get_applications_by_household_size(
        self,
        min_size: int,
        max_size: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por tamaño de familia"""
        try:
            query = {
                "household_size": {
                    "$gte": min_size,
                    "$lte": max_size
                }
            }
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por tamaño de hogar: {e}")
            return []
    
    async def get_applications_by_income_range(
        self,
        min_income: float,
        max_income: float,
        limit: int = 100,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por rango de ingresos familiares"""
        try:
            query = {
                "economic_info.total_household_income": {
                    "$gte": min_income,
                    "$lte": max_income
                }
            }
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes por rango de ingresos: {e}")
            return []
    
    async def get_applications_submitted_today(self) -> List[TechoPropioApplication]:
        """Obtener solicitudes enviadas hoy"""
        try:
            # Fecha de inicio y fin del día actual
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            return await self.get_applications_by_date_range(
                start_date=start_of_day,
                end_date=end_of_day,
                limit=1000  # Sin límite práctico para hoy
            )
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes de hoy: {e}")
            return []
    
    async def get_expired_draft_applications(
        self,
        days_threshold: int = 30
    ) -> List[TechoPropioApplication]:
        """Obtener borradores expirados para limpieza"""
        try:
            # Calcular fecha límite
            threshold_date = datetime.now() - timedelta(days=days_threshold)
            
            query = {
                "status": ApplicationStatus.DRAFT.value,
                "created_at": {"$lt": threshold_date}
            }
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", ASCENDING)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo borradores expirados: {e}")
            return []
    
    async def get_pending_review_applications(
        self,
        reviewer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes pendientes de revisión"""
        try:
            query = {"status": ApplicationStatus.PENDING_REVIEW.value}
            
            if reviewer_id:
                query["assigned_reviewer"] = reviewer_id
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", ASCENDING)  # FIFO para revisiones
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes pendientes: {e}")
            return []
    
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
    
    async def bulk_update_status(
        self,
        application_ids: List[str],
        new_status: ApplicationStatus,
        updated_by: str,
        reason: Optional[str] = None
    ) -> int:
        """Actualizar estado de múltiples solicitudes"""
        try:
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
            
            result = self.collection.update_many(
                {"_id": {"$in": object_ids}},
                update_doc
            )
            
            logger.info(f"Bulk update: {result.modified_count} applications updated to {new_status.value}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error en actualización masiva: {e}")
            return 0

    # ===== MÉTODOS RESTANTES PARA COMPLETAR LA INTERFAZ =====
    
    async def delete_application(self, application_id: str) -> bool:
        """Eliminar solicitud (soft delete recomendado)"""
        try:
            # Soft delete - marcar como eliminado
            result = self.collection.update_one(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "status": ApplicationStatus.CANCELLED.value,
                        "deleted_at": datetime.now(),
                        "is_deleted": True
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error eliminando solicitud {application_id}: {e}")
            return False
    
    async def get_applications_by_user(
        self, 
        user_id: str,
        status: Optional[ApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes de un usuario específico"""
        try:
            query = {"created_by": user_id}
            
            if status:
                query["status"] = status.value
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes del usuario {user_id}: {e}")
            return []
    
    async def count_applications_by_user(
        self, 
        user_id: str,
        status: Optional[ApplicationStatus] = None
    ) -> int:
        """Contar solicitudes de un usuario"""
        try:
            query = {"created_by": user_id}
            
            if status:
                query["status"] = status.value
            
            return self.collection.count_documents(query)
            
        except Exception as e:
            logger.error(f"Error contando solicitudes del usuario {user_id}: {e}")
            return 0
    
    async def get_applications_by_status(
        self,
        status: ApplicationStatus,
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Obtener solicitudes por estado"""
        try:
            query = {"status": status.value}
            
            documents = list(
                self.collection.find(query)
                .sort("created_at", DESCENDING)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error obteniendo solicitudes con estado {status.value}: {e}")
            return []
    
    async def count_applications_by_status(self, status: ApplicationStatus) -> int:
        """Contar solicitudes por estado"""
        try:
            return self.collection.count_documents({"status": status.value})
            
        except Exception as e:
            logger.error(f"Error contando solicitudes con estado {status.value}: {e}")
            return 0
    
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
            
            count = self.collection.count_documents(query)
            return count > 0
            
        except Exception as e:
            logger.error(f"Error verificando DNI {dni}: {e}")
            return False
    

    
    async def search_applications(
        self,
        filters: Dict[str, Any],
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> List[TechoPropioApplication]:
        """Búsqueda avanzada con múltiples filtros"""
        try:
            # Construir query MongoDB usando el método existente
            mongo_query = self._build_mongo_query(filters)
            
            # Determinar orden de sorting
            sort_direction = DESCENDING if sort_order.lower() == "desc" else ASCENDING
            
            documents = list(
                self.collection.find(mongo_query)
                .sort(sort_by, sort_direction)
                .skip(offset)
                .limit(limit)
            )
            
            applications = []
            for doc in documents:
                try:
                    app = self._document_to_entity(doc)
                    applications.append(app)
                except Exception as e:
                    logger.error(f"Error convirtiendo documento: {e}")
                    continue
            
            return applications
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {e}")
            return []
    
    async def count_search_results(self, filters: Dict[str, Any]) -> int:
        """Contar resultados de búsqueda avanzada"""
        try:
            mongo_query = self._build_mongo_query(filters)
            return self.collection.count_documents(mongo_query)
            
        except Exception as e:
            logger.error(f"Error contando resultados de búsqueda: {e}")
            return 0