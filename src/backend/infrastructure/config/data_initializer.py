"""
Inicializador de datos del sistema
Crea roles predeterminados y configura el super administrador inicial
"""

import os
from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId

from .database import get_database
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Roles predeterminados del sistema
DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "display_name": "Super Administrador",
        "description": "Acceso total al sistema, puede gestionar todos los aspectos",
        "permissions": ["all"],
        "is_system": True,
        "is_active": True,
        "priority": 100
    },
    {
        "name": "admin",
        "display_name": "Administrador",
        "description": "Administrador del sistema con acceso a gestión de usuarios y configuración",
        "permissions": [
            "users.read", "users.create", "users.update", "users.delete",
            "roles.read", "roles.create", "roles.update",
            "config.read", "config.update",
            "reports.read", "reports.create",
            "techo_propio.read", "techo_propio.create", "techo_propio.update", "techo_propio.delete",
            "ai.process_message"
        ],
        "is_system": True,
        "is_active": True,
        "priority": 80
    },
    {
        "name": "user",
        "display_name": "Usuario",
        "description": "Usuario estándar con acceso básico al sistema",
        "permissions": [
            "users.read_own", "users.update_own",
            "techo_propio.read", "techo_propio.create_own",
            "ai.process_message"
        ],
        "is_system": True,
        "is_active": True,
        "priority": 10
    }
]

# Email del super administrador inicial (configurable por variable de entorno)
SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "gscutic@gmail.com")


async def initialize_roles() -> dict:
    """
    Inicializa los roles predeterminados en la base de datos.
    Solo crea roles que no existen.
    """
    db = get_database()
    roles_collection = db.roles
    
    created = []
    existing = []
    
    for role_data in DEFAULT_ROLES:
        # Verificar si el rol ya existe
        existing_role = await roles_collection.find_one({"name": role_data["name"]})
        
        if existing_role:
            existing.append(role_data["name"])
            logger.info(f"ℹ️ Rol '{role_data['name']}' ya existe")
        else:
            # Crear el rol
            role_doc = {
                **role_data,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await roles_collection.insert_one(role_doc)
            created.append(role_data["name"])
            logger.info(f"✅ Rol '{role_data['name']}' creado exitosamente")
    
    return {
        "created": created,
        "existing": existing,
        "total_roles": len(DEFAULT_ROLES)
    }


async def get_role_by_name(role_name: str) -> Optional[dict]:
    """Obtener un rol por su nombre"""
    db = get_database()
    return await db.roles.find_one({"name": role_name})


async def assign_super_admin(clerk_id: str = None, email: str = None) -> dict:
    """
    Asigna el rol de super_admin a un usuario específico.
    Se puede identificar por clerk_id o email.
    """
    db = get_database()
    users_collection = db.users
    roles_collection = db.roles
    
    # Obtener el rol super_admin
    super_admin_role = await roles_collection.find_one({"name": "super_admin"})
    if not super_admin_role:
        # Crear roles si no existen
        await initialize_roles()
        super_admin_role = await roles_collection.find_one({"name": "super_admin"})
    
    if not super_admin_role:
        return {
            "success": False,
            "message": "No se pudo encontrar o crear el rol super_admin"
        }
    
    # Buscar el usuario
    query = {}
    if clerk_id:
        query["clerk_id"] = clerk_id
    elif email:
        query["email"] = email
    else:
        return {
            "success": False,
            "message": "Debe proporcionar clerk_id o email"
        }
    
    user = await users_collection.find_one(query)
    
    if not user:
        return {
            "success": False,
            "message": f"Usuario no encontrado con {query}"
        }
    
    # Actualizar el usuario con el rol super_admin
    result = await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "role_id": super_admin_role["_id"],
                "role_name": "super_admin",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count > 0:
        logger.info(f"✅ Usuario {user.get('email', user.get('clerk_id'))} asignado como super_admin")
        return {
            "success": True,
            "message": f"Usuario asignado como super_admin exitosamente",
            "user": {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "clerk_id": user.get("clerk_id"),
                "role_name": "super_admin"
            }
        }
    else:
        return {
            "success": False,
            "message": "No se pudo actualizar el usuario"
        }


async def fix_users_without_role_id() -> dict:
    """
    Corrige usuarios que tienen role_name pero no role_id.
    Esto puede pasar cuando los usuarios fueron creados antes de que existieran los roles.
    """
    db = get_database()
    users_collection = db.users
    roles_collection = db.roles
    
    # Asegurar que los roles existen
    await initialize_roles()
    
    # Obtener todos los roles
    roles = {}
    async for role in roles_collection.find({}):
        roles[role["name"]] = role["_id"]
    
    # Buscar usuarios sin role_id pero con role_name
    users_to_fix = users_collection.find({
        "$or": [
            {"role_id": None},
            {"role_id": {"$exists": False}}
        ],
        "role_name": {"$exists": True}
    })
    
    fixed_count = 0
    errors = []
    
    async for user in users_to_fix:
        role_name = user.get("role_name", "user")
        role_id = roles.get(role_name)
        
        if role_id:
            await users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role_id": role_id,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            fixed_count += 1
            logger.info(f"✅ Usuario {user.get('email', user.get('clerk_id'))} corregido con role_id")
        else:
            errors.append(f"Rol '{role_name}' no encontrado para usuario {user.get('clerk_id')}")
    
    return {
        "success": True,
        "fixed_count": fixed_count,
        "errors": errors
    }


async def initialize_super_admin_by_email() -> dict:
    """
    Inicializa el super administrador usando el email configurado en SUPER_ADMIN_EMAIL.
    Este método se llama automáticamente al iniciar la aplicación.
    """
    db = get_database()
    users_collection = db.users
    
    # Verificar si ya existe un super_admin
    existing_super_admin = await users_collection.find_one({"role_name": "super_admin"})
    if existing_super_admin:
        logger.info(f"ℹ️ Ya existe un super_admin: {existing_super_admin.get('email')}")
        return {
            "success": True,
            "message": "Super admin ya existe",
            "email": existing_super_admin.get("email")
        }
    
    # Buscar el usuario por email configurado
    user = await users_collection.find_one({"email": SUPER_ADMIN_EMAIL})
    if user:
        result = await assign_super_admin(email=SUPER_ADMIN_EMAIL)
        return result
    else:
        logger.info(f"ℹ️ Usuario con email {SUPER_ADMIN_EMAIL} aún no existe. Se asignará super_admin cuando se registre.")
        return {
            "success": True,
            "message": f"Esperando registro del usuario {SUPER_ADMIN_EMAIL}",
            "pending_email": SUPER_ADMIN_EMAIL
        }


async def initialize_all_data() -> dict:
    """
    Inicializa todos los datos necesarios del sistema.
    Se debe llamar al iniciar la aplicación.
    """
    logger.info("🚀 Iniciando inicialización de datos del sistema...")
    
    results = {
        "roles": None,
        "super_admin": None,
        "users_fixed": None
    }
    
    try:
        # 1. Inicializar roles
        results["roles"] = await initialize_roles()
        logger.info(f"✅ Roles: {results['roles']['created']} creados, {results['roles']['existing']} existentes")
        
        # 2. Corregir usuarios sin role_id
        results["users_fixed"] = await fix_users_without_role_id()
        logger.info(f"✅ Usuarios corregidos: {results['users_fixed']['fixed_count']}")
        
        # 3. Inicializar super_admin
        results["super_admin"] = await initialize_super_admin_by_email()
        logger.info(f"✅ Super admin: {results['super_admin']['message']}")
        
        logger.info("🎉 Inicialización de datos completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en inicialización de datos: {str(e)}")
        results["error"] = str(e)
    
    return results
