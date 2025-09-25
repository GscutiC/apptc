#!/usr/bin/env python3
"""
Script para conectar directamente a MongoDB y verificar/actualizar usuarios
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'apptc')

async def verify_and_update_user():
    """Verificar usuarios en la base de datos correcta y actualizar si es necesario"""
    
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]
    
    try:
        print(f"🔗 Conectando a MongoDB: {MONGODB_URL}")
        print(f"📁 Base de datos: {DATABASE_NAME}")
        
        # Verificar colecciones existentes
        collections = await db.list_collection_names()
        print(f"📚 Colecciones disponibles: {collections}")
        
        # Buscar en la colección de usuarios
        users_collection = db.users
        users = await users_collection.find({}).to_list(None)
        
        print(f"\n👥 Usuarios encontrados: {len(users)}")
        
        jonathan_user = None
        for user in users:
            print(f"\n📋 Usuario:")
            print(f"  - ID: {user.get('_id')}")
            print(f"  - Email: {user.get('email')}")
            print(f"  - Nombre: {user.get('full_name')}")
            print(f"  - Clerk ID: {user.get('clerk_id')}")
            print(f"  - Role ID: {user.get('role_id')}")
            print(f"  - Activo: {user.get('is_active')}")
            
            if user.get('email') == 'vedjonathan5@gmail.com' or 'jonathan' in user.get('full_name', '').lower():
                jonathan_user = user
        
        if not jonathan_user:
            print("❌ Usuario Jonathan no encontrado")
            return
        
        print(f"\n✅ Usuario Jonathan encontrado:")
        print(f"   Email: {jonathan_user.get('email')}")
        print(f"   Nombre: {jonathan_user.get('full_name')}")
        print(f"   Role ID actual: {jonathan_user.get('role_id')}")
        
        # Verificar roles disponibles
        roles_collection = db.roles
        roles = await roles_collection.find({}).to_list(None)
        
        print(f"\n🎭 Roles disponibles: {len(roles)}")
        super_admin_role = None
        
        for role in roles:
            print(f"  - {role.get('name')}: {role.get('display_name')} (ID: {role.get('_id')})")
            if role.get('name') == 'super_admin':
                super_admin_role = role
        
        if not super_admin_role:
            print("❌ Rol super_admin no encontrado")
            return
        
        # Verificar si el usuario ya tiene el rol correcto
        current_role_id = jonathan_user.get('role_id')
        super_admin_role_id = super_admin_role.get('_id')
        
        print(f"\n🔍 Comparando roles:")
        print(f"   Role ID actual: {current_role_id}")
        print(f"   Super admin ID: {super_admin_role_id}")
        
        if str(current_role_id) == str(super_admin_role_id):
            print("✅ El usuario ya tiene el rol super_admin asignado correctamente")
        else:
            print("🔄 Actualizando rol del usuario...")
            
            # Actualizar el rol del usuario
            result = await users_collection.update_one(
                {'_id': jonathan_user['_id']},
                {
                    '$set': {
                        'role_id': super_admin_role_id,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print("✅ ¡Rol actualizado exitosamente!")
                
                # Verificar la actualización
                updated_user = await users_collection.find_one({'_id': jonathan_user['_id']})
                print(f"🔍 Verificación - Nuevo role_id: {updated_user.get('role_id')}")
            else:
                print("❌ No se pudo actualizar el rol")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_and_update_user())