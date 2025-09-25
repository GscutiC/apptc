#!/usr/bin/env python3
"""
Script para normalizar roles en la base de datos existente
Convierte todos los role_name a minúsculas para consistencia
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

async def normalize_roles_in_database():
    """Normalizar todos los role_name en la base de datos a minúsculas"""
    
    # Configuración de conexión
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    database_name = os.getenv("DATABASE_NAME", "apptc")
    
    print(f"🔄 Conectando a MongoDB: {mongodb_url}")
    print(f"📁 Base de datos: {database_name}")
    
    client = AsyncIOMotorClient(mongodb_url)
    database = client[database_name]
    users_collection = database.users
    
    try:
        # Obtener todos los usuarios
        print("\n📊 Analizando usuarios existentes...")
        users_cursor = users_collection.find({})
        users_to_update = []
        
        async for user in users_cursor:
            role_name = user.get("role_name")
            if role_name and role_name != role_name.lower():
                users_to_update.append({
                    "_id": user["_id"],
                    "current_role": role_name,
                    "normalized_role": role_name.lower()
                })
        
        print(f"✅ Encontrados {len(users_to_update)} usuarios que necesitan actualización")
        
        if not users_to_update:
            print("🎉 ¡Todos los roles ya están normalizados!")
            return
        
        # Mostrar cambios pendientes
        print("\n📋 Cambios a realizar:")
        for user in users_to_update:
            print(f"  • {user['current_role']} → {user['normalized_role']}")
        
        # Confirmar antes de proceder
        confirm = input(f"\n❓ ¿Proceder con la actualización de {len(users_to_update)} usuarios? (s/N): ")
        if confirm.lower() not in ['s', 'si', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
        
        # Realizar actualizaciones
        print("\n🔄 Actualizando usuarios...")
        updated_count = 0
        
        for user in users_to_update:
            result = await users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role_name": user["normalized_role"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"  ✅ Actualizado: {user['current_role']} → {user['normalized_role']}")
        
        print(f"\n🎉 ¡Migración completada!")
        print(f"📈 Usuarios actualizados: {updated_count}/{len(users_to_update)}")
        
        # Verificar resultados
        print("\n🔍 Verificando resultados...")
        verification_cursor = users_collection.find({})
        roles_found = set()
        
        async for user in verification_cursor:
            role_name = user.get("role_name")
            if role_name:
                roles_found.add(role_name)
        
        print("📋 Roles encontrados después de la migración:")
        for role in sorted(roles_found):
            print(f"  • {role}")
        
        # Verificar que no hay roles en mayúsculas
        uppercase_roles = [role for role in roles_found if role != role.lower()]
        if uppercase_roles:
            print(f"⚠️  Advertencia: Aún existen roles con mayúsculas: {uppercase_roles}")
        else:
            print("✅ Todos los roles están ahora en minúsculas")
            
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        raise
    finally:
        client.close()
        print("\n🔌 Conexión cerrada")

async def main():
    """Función principal"""
    print("🚀 Iniciando migración de normalización de roles")
    print("=" * 50)
    
    await normalize_roles_in_database()
    
    print("\n" + "=" * 50)
    print("✨ Migración finalizada")

if __name__ == "__main__":
    # Cargar variables de entorno si existe archivo .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📄 Variables de entorno cargadas desde .env")
    except ImportError:
        print("📄 python-dotenv no disponible, usando variables de entorno del sistema")
    
    asyncio.run(main())