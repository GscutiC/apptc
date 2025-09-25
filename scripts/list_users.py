#!/usr/bin/env python3
"""
Script para listar todos los usuarios en la base de datos
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def list_all_users():
    """Listar todos los usuarios en la base de datos"""
    
    # Conectar directamente a MongoDB
    MONGODB_URL = "mongodb://localhost:27017"
    DB_NAME = "mi_app_completa_db"
    
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DB_NAME]
    
    try:
        print("📋 Listando todos los usuarios en la base de datos...")
        
        users_cursor = database.users.find({})
        user_count = 0
        
        async for user in users_cursor:
            user_count += 1
            print(f"\n👤 Usuario #{user_count}:")
            print(f"  - MongoDB ID: {user.get('_id')}")
            print(f"  - ID: {user.get('id')}")
            print(f"  - Clerk ID: {user.get('clerk_id')}")
            print(f"  - Email: {user.get('email')}")
            print(f"  - Nombre: {user.get('first_name')} {user.get('last_name')}")
            print(f"  - Nombre completo: {user.get('full_name')}")
            print(f"  - Role ID: {user.get('role_id')}")
            print(f"  - Activo: {user.get('is_active')}")
            print(f"  - Creado: {user.get('created_at')}")
        
        if user_count == 0:
            print("❌ No se encontraron usuarios en la base de datos")
        else:
            print(f"\n✅ Total de usuarios encontrados: {user_count}")
            
        # También listar roles disponibles
        print("\n📋 Listando todos los roles disponibles...")
        
        roles_cursor = database.roles.find({})
        role_count = 0
        
        async for role in roles_cursor:
            role_count += 1
            print(f"\n🔐 Rol #{role_count}:")
            print(f"  - MongoDB ID: {role.get('_id')}")
            print(f"  - Nombre: {role.get('name')}")
            print(f"  - Nombre para mostrar: {role.get('display_name')}")
            print(f"  - Descripción: {role.get('description')}")
            print(f"  - Permisos: {len(role.get('permissions', []))}")
            
        if role_count == 0:
            print("❌ No se encontraron roles en la base de datos")
        else:
            print(f"\n✅ Total de roles encontrados: {role_count}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(list_all_users())