#!/usr/bin/env python3
"""
Script simple para actualizar el rol de un usuario específico a super_admin
"""

import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

async def update_user_role_direct():
    """Actualizar el rol del usuario Jonathan Elías Delgado a super_admin directamente en MongoDB"""
    
    # Conectar directamente a MongoDB
    MONGODB_URL = "mongodb://localhost:27017"
    DB_NAME = "mi_app_completa_db"
    
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DB_NAME]
    
    try:
        # Buscar el usuario por email o clerk_id
        user_email = "vedjonathanelias@gmail.com"
        clerk_id = "user_339MX93RuwY00NUReUR2HCxBrDu"
        
        print(f"🔍 Buscando usuario con email: {user_email}")
        print(f"🔍 O con clerk_id: {clerk_id}")
        
        # Buscar usuario
        user = await database.users.find_one({
            "$or": [
                {"email": user_email},
                {"clerk_id": clerk_id}
            ]
        })
        
        if not user:
            print(f"❌ Usuario no encontrado")
            
            # Mostrar todos los usuarios disponibles
            print("\n📋 Usuarios disponibles:")
            users_cursor = database.users.find({})
            async for u in users_cursor:
                print(f"  - ID: {u.get('_id')}")
                print(f"    Email: {u.get('email')}")
                print(f"    Clerk ID: {u.get('clerk_id')}")
                print(f"    Nombre: {u.get('full_name')}")
                print(f"    Rol actual: {u.get('role_id', 'N/A')}")
                print("")
            return
        
        print(f"✅ Usuario encontrado: {user.get('full_name')} ({user.get('email')})")
        
        # Buscar el rol de super_admin
        print("🔍 Buscando rol super_admin...")
        
        super_admin_role = await database.roles.find_one({"name": "super_admin"})
        
        if not super_admin_role:
            print("❌ Rol super_admin no encontrado")
            print("📋 Roles disponibles:")
            roles_cursor = database.roles.find({})
            async for role in roles_cursor:
                print(f"  - {role.get('name')}: {role.get('display_name')}")
            return
        
        print(f"✅ Rol super_admin encontrado: {super_admin_role.get('display_name')}")
        
        # Actualizar el rol del usuario
        print(f"🔄 Actualizando rol del usuario {user.get('full_name')}...")
        
        result = await database.users.update_one(
            {"clerk_id": user.get('clerk_id')},
            {"$set": {"role_id": super_admin_role.get('_id')}}
        )
        
        if result.modified_count > 0:
            print(f"✅ ¡Rol actualizado exitosamente!")
            print(f"   Usuario: {user.get('full_name')}")
            print(f"   Email: {user.get('email')}")
            print(f"   Nuevo rol: super_admin")
            
            # Verificar que el cambio se aplicó
            updated_user = await database.users.find_one({"clerk_id": user.get('clerk_id')})
            if updated_user:
                print(f"🔍 Verificación - Role ID: {updated_user.get('role_id')}")
                print(f"🔍 Verificación - Rol correcto: {updated_user.get('role_id') == super_admin_role.get('_id')}")
        else:
            print("❌ Error al actualizar el rol o no hubo cambios")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(update_user_role_direct())