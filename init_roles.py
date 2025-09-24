#!/usr/bin/env python3
"""
Script para inicializar los roles por defecto en MongoDB
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configuración de MongoDB
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "mi_app_completa"

# Roles por defecto
DEFAULT_ROLES = [
    {
        "name": "super_admin",
        "display_name": "Super Administrador",
        "description": "Acceso completo al sistema con todos los permisos administrativos",
        "permissions": [
            "users.create",
            "users.read",
            "users.update",
            "users.delete",
            "users.manage_roles",
            "roles.create",
            "roles.read",
            "roles.update",
            "roles.delete",
            "system.admin",
            "system.settings",
            "reports.view",
            "reports.export",
            "audit.view"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "cliente",
        "display_name": "Cliente",
        "description": "Usuario cliente con acceso a servicios premium",
        "permissions": [
            "profile.read",
            "profile.update",
            "chat.premium",
            "chat.history",
            "services.premium",
            "support.priority",
            "reports.personal"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    {
        "name": "user",
        "display_name": "Usuario",
        "description": "Usuario básico con acceso limitado al sistema",
        "permissions": [
            "profile.read",
            "profile.update",
            "chat.basic",
            "services.basic"
        ],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
]

async def init_roles():
    """Inicializar roles por defecto en MongoDB"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    roles_collection = db.roles
    
    print("🚀 Inicializando roles por defecto...")
    
    for role_data in DEFAULT_ROLES:
        # Verificar si el rol ya existe
        existing_role = await roles_collection.find_one({"name": role_data["name"]})
        
        if existing_role:
            print(f"✅ Rol '{role_data['name']}' ya existe, actualizando permisos...")
            # Actualizar permisos manteniendo otros datos
            await roles_collection.update_one(
                {"name": role_data["name"]},
                {
                    "$set": {
                        "permissions": role_data["permissions"],
                        "description": role_data["description"],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        else:
            print(f"➕ Creando rol '{role_data['name']}'...")
            await roles_collection.insert_one(role_data)
    
    # Crear índices para optimizar consultas
    print("📊 Creando índices...")
    await roles_collection.create_index("name", unique=True)
    await roles_collection.create_index("is_active")
    
    # Hacer lo mismo para usuarios
    users_collection = db.users
    await users_collection.create_index("clerk_id", unique=True)
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("role_name")
    await users_collection.create_index("is_active")
    
    print("✨ Inicialización completada!")
    print("\n📋 Roles creados:")
    
    # Mostrar resumen de roles
    async for role in roles_collection.find({"is_active": True}):
        print(f"  • {role['display_name']} ({role['name']})")
        print(f"    Permisos: {len(role['permissions'])}")
        print(f"    Descripción: {role['description']}")
        print()
    
    client.close()

async def create_test_super_admin():
    """Crear un super admin de prueba (opcional)"""
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    users_collection = db.users
    roles_collection = db.roles
    
    # Obtener el rol de super admin
    super_admin_role = await roles_collection.find_one({"name": "super_admin"})
    
    if not super_admin_role:
        print("❌ Error: Rol super_admin no encontrado")
        return
    
    # Crear usuario de prueba (esto se haría normalmente via webhook de Clerk)
    test_user = {
        "clerk_id": "test_super_admin_123",  # Este sería el ID real de Clerk
        "email": "admin@ejemplo.com",
        "first_name": "Super",
        "last_name": "Admin",
        "full_name": "Super Admin",
        "role_id": super_admin_role["_id"],
        "role_name": "super_admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    existing_user = await users_collection.find_one({"clerk_id": test_user["clerk_id"]})
    if not existing_user:
        await users_collection.insert_one(test_user)
        print("👤 Usuario super admin de prueba creado")
        print("   Clerk ID: test_super_admin_123")
        print("   Email: admin@ejemplo.com")
    else:
        print("👤 Usuario super admin de prueba ya existe")
    
    client.close()

if __name__ == "__main__":
    print("🔧 Configuración de Base de Datos - Mi App Completa")
    print("=" * 50)
    
    # Ejecutar inicialización
    asyncio.run(init_roles())
    
    # Preguntar si crear usuario de prueba
    create_test = input("\n¿Crear usuario super admin de prueba? (y/N): ").lower().strip()
    if create_test in ['y', 'yes', 's', 'si']:
        asyncio.run(create_test_super_admin())
    
    print("\n🎉 Configuración completada!")
    print("Puedes ahora ejecutar tu aplicación FastAPI.")