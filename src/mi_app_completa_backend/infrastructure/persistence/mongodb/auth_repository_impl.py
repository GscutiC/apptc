from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from ....domain.repositories.auth_repository import UserRepository, RoleRepository
from ....domain.entities.auth_models import User, Role, UserCreate, UserUpdate, UserWithRole

class MongoUserRepository(UserRepository):
    """Implementación MongoDB para usuarios"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.users_collection = database.users
        self.roles_collection = database.roles
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Crear un nuevo usuario"""
        print(f"📝 create_user: Creando usuario con datos: {user_data.dict()}")
        
        # Verificar si ya existe
        existing = await self.get_user_by_clerk_id(user_data.clerk_id)
        if existing:
            print(f"⚠️ Usuario ya existe: {existing.clerk_id}")
            raise ValueError(f"Usuario con clerk_id {user_data.clerk_id} ya existe")
        
        # Obtener rol por defecto
        default_role = await self.roles_collection.find_one({"name": "user"})
        print(f"🔍 Rol por defecto encontrado: {default_role}")
        
        user_dict = user_data.dict()
        user_dict.update({
            "role_id": default_role["_id"] if default_role else None,
            "role_name": "user",  # Siempre en minúsculas
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        print(f"📋 Datos finales a insertar: {user_dict}")
        result = await self.users_collection.insert_one(user_dict)
        user_dict["_id"] = result.inserted_id
        print(f"✅ Usuario insertado con ID: {result.inserted_id}")
        
        return User(**user_dict)
    
    async def get_user_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        """Obtener usuario por ID de Clerk"""
        user_doc = await self.users_collection.find_one({"clerk_id": clerk_id})
        if user_doc:
            return User(**user_doc)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        user_doc = await self.users_collection.find_one({"email": email})
        if user_doc:
            return User(**user_doc)
        return None
    
    async def get_user_with_role(self, clerk_id: str) -> Optional[UserWithRole]:
        """Obtener usuario con información completa del rol"""
        print(f"🔍 get_user_with_role: Buscando usuario con clerk_id: {clerk_id}")
        
        pipeline = [
            {"$match": {"clerk_id": clerk_id}},
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "role_id",
                    "foreignField": "_id",
                    "as": "role_info"
                }
            },
            {
                "$addFields": {
                    "role": {"$arrayElemAt": ["$role_info", 0]},
                    "last_login": {"$ifNull": ["$last_login", None]}
                }
            },
            {"$unset": ["role_info", "role_id"]}
        ]
        
        print(f"📝 Pipeline: {pipeline}")
        result = await self.users_collection.aggregate(pipeline).to_list(1)
        print(f"📊 Resultado agregación: {result}")
        
        if result:
            user_data = result[0]
            # print(f"📋 Datos usuario antes de procesar: {user_data}")
            user_data["id"] = str(user_data.pop("_id"))
            if user_data.get("role") and user_data["role"].get("_id"):
                user_data["role"]["id"] = str(user_data["role"].pop("_id"))
            # print(f"📋 Datos usuario después de procesar: {user_data}")
            try:
                user_with_role = UserWithRole(**user_data)
                print(f"✅ UserWithRole creado exitosamente: {user_with_role.email}")
                return user_with_role
            except Exception as e:
                print(f"❌ Error creando UserWithRole: {e}")
                print(f"📋 Datos que causaron el error: {user_data}")
                return None
        else:
            print(f"❌ No se encontró usuario con clerk_id: {clerk_id}")
            return None
    
    async def update_user(self, clerk_id: str, user_data: UserUpdate) -> Optional[User]:
        """Actualizar usuario"""
        update_dict = {k: v for k, v in user_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Si se actualiza el rol, obtener la referencia (case-insensitive)
        if "role_name" in update_dict:
            # Normalizar a minúsculas para búsqueda case-insensitive
            role_name_normalized = update_dict["role_name"].lower().strip()
            role = await self.roles_collection.find_one({"name": role_name_normalized})
            if role:
                update_dict["role_id"] = role["_id"]
                update_dict["role_name"] = role_name_normalized  # Guardar normalizado
            else:
                raise ValueError(f"Rol {update_dict['role_name']} no encontrado")
        
        result = await self.users_collection.update_one(
            {"clerk_id": clerk_id},
            {"$set": update_dict}
        )
        
        if result.matched_count:
            return await self.get_user_by_clerk_id(clerk_id)
        return None
    
    async def delete_user(self, clerk_id: str) -> bool:
        """Eliminar usuario"""
        result = await self.users_collection.delete_one({"clerk_id": clerk_id})
        return result.deleted_count > 0
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[UserWithRole]:
        """Listar usuarios con paginación"""
        pipeline = [
            {"$skip": skip},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "roles",
                    "localField": "role_id",
                    "foreignField": "_id",
                    "as": "role_info"
                }
            },
            {
                "$addFields": {
                    "role": {"$arrayElemAt": ["$role_info", 0]},
                    "last_login": {"$ifNull": ["$last_login", None]}
                }
            },
            {"$unset": ["role_info", "role_id"]},
            {"$sort": {"created_at": -1}}
        ]
        
        cursor = self.users_collection.aggregate(pipeline)
        users = []
        async for user_data in cursor:
            user_data["id"] = str(user_data.pop("_id"))
            if user_data.get("role") and user_data["role"].get("_id"):
                user_data["role"]["id"] = str(user_data["role"].pop("_id"))
            users.append(UserWithRole(**user_data))
        
        return users
    
    async def update_last_login(self, clerk_id: str) -> bool:
        """Actualizar última fecha de login"""
        result = await self.users_collection.update_one(
            {"clerk_id": clerk_id},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        return result.matched_count > 0

class MongoRoleRepository(RoleRepository):
    """Implementación MongoDB para roles"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.db = database
        self.collection = database.roles
    
    async def create_role(self, role: Role) -> Role:
        """Crear un nuevo rol"""
        # Verificar si ya existe
        existing = await self.get_role_by_name(role.name)
        if existing:
            raise ValueError(f"Rol con nombre {role.name} ya existe")
        
        role_dict = role.dict(by_alias=True)
        result = await self.collection.insert_one(role_dict)
        role_dict["_id"] = result.inserted_id
        
        return Role(**role_dict)
    
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Obtener rol por nombre"""
        role_doc = await self.collection.find_one({"name": name, "is_active": True})
        if role_doc:
            return Role(**role_doc)
        return None
    
    async def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """Obtener rol por ID"""
        try:
            role_doc = await self.collection.find_one({"_id": ObjectId(role_id), "is_active": True})
            if role_doc:
                return Role(**role_doc)
        except Exception:
            pass
        return None
    
    async def list_roles(self) -> List[Role]:
        """Listar todos los roles activos"""
        cursor = self.collection.find({"is_active": True}).sort("display_name", 1)
        roles = []
        async for role_doc in cursor:
            roles.append(Role(**role_doc))
        return roles
    
    async def update_role(self, role_id: str, role_data: dict) -> Optional[Role]:
        """Actualizar rol"""
        try:
            role_data["updated_at"] = datetime.now(timezone.utc)
            result = await self.collection.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": role_data}
            )
            
            if result.matched_count:
                return await self.get_role_by_id(role_id)
        except Exception:
            pass
        return None
    
    async def delete_role(self, role_id: str) -> bool:
        """Eliminar rol (soft delete)"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}}
            )
            return result.matched_count > 0
        except Exception:
            return False