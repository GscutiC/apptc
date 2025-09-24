"""
Script de limpieza y migración para roles existentes
"""
import asyncio
import os
import sys
from datetime import datetime

# Agregar el directorio src al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database

async def clean_and_migrate_roles():
    """Limpiar roles existentes y crear roles por defecto"""
    print("🧹 LIMPIEZA Y MIGRACIÓN DE ROLES")
    print("=" * 60)
    
    try:
        # Conectar a la base de datos directamente
        db = get_database()
        roles_collection = db.roles
        users_collection = db.users
        
        print("🔍 Verificando roles existentes en la base de datos...")
        
        # Obtener roles existentes directamente de MongoDB
        existing_roles_cursor = roles_collection.find({})
        existing_roles = await existing_roles_cursor.to_list(length=None)
        
        print(f"   Roles encontrados: {len(existing_roles)}")
        
        if existing_roles:
            print("   Roles actuales:")
            for role in existing_roles:
                permissions = role.get('permissions', [])
                print(f"   - {role.get('name', 'Sin nombre')}: {permissions}")
        
        # Preguntar si queremos limpiar los roles existentes
        print(f"\n⚠️  Se encontraron {len(existing_roles)} roles con permisos del sistema anterior.")
        print("   Estos roles tienen permisos incompatibles con el nuevo sistema granular.")
        print("   Opciones:")
        print("   1. Limpiar todos los roles existentes y crear los nuevos (RECOMENDADO)")
        print("   2. Cancelar migración")
        
        # Para automatizar, vamos con la opción 1
        print("   🤖 Ejecutando limpieza automática...")
        
        # 1. Limpiar roles existentes
        print("\n🗑️  Eliminando roles existentes...")
        delete_result = await roles_collection.delete_many({})
        print(f"   ✅ Eliminados {delete_result.deleted_count} roles")
        
        # 2. Actualizar usuarios para remover referencias a roles eliminados
        print("\n👥 Actualizando usuarios...")
        update_result = await users_collection.update_many(
            {"role_id": {"$exists": True}},
            {"$unset": {"role_id": ""}, "$set": {"role_name": "user"}}
        )
        print(f"   ✅ Actualizados {update_result.modified_count} usuarios")
        
        # 3. Crear roles por defecto del nuevo sistema
        print("\n🏗️  Creando roles por defecto del nuevo sistema...")
        
        from mi_app_completa_backend.domain.value_objects.permissions import DefaultRoles
        
        created_count = 0
        for role_name, role_config in DefaultRoles.ROLES_CONFIG.items():
            role_data = {
                "name": role_name,
                "display_name": role_config["display_name"],
                "description": role_config["description"],
                "permissions": role_config["permissions"],
                "is_active": True,
                "is_system_role": True,  # Roles del sistema
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await roles_collection.insert_one(role_data)
            created_count += 1
            print(f"   ✅ Creado rol: {role_name} ({len(role_config['permissions'])} permisos)")
        
        print(f"\n🎉 Migración completada exitosamente!")
        print(f"   • Roles eliminados: {delete_result.deleted_count}")
        print(f"   • Usuarios actualizados: {update_result.modified_count}")
        print(f"   • Roles nuevos creados: {created_count}")
        
        # 4. Verificar que todo esté correcto
        print("\n🔍 Verificando migración...")
        new_roles_cursor = roles_collection.find({})
        new_roles = await new_roles_cursor.to_list(length=None)
        
        print(f"   Roles después de migración: {len(new_roles)}")
        for role in new_roles:
            permissions_count = len(role.get('permissions', []))
            print(f"   ✅ {role['name']}: {role['display_name']} ({permissions_count} permisos)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def verify_system_permissions():
    """Verificar que el sistema de permisos funciona correctamente"""
    print("\n🧪 VERIFICANDO SISTEMA DE PERMISOS")
    print("=" * 60)
    
    try:
        from mi_app_completa_backend.domain.value_objects.permissions import SystemPermissions, DefaultRoles
        
        # Verificar permisos del sistema
        all_permissions = SystemPermissions.get_all_permissions()
        print(f"✅ Sistema de permisos cargado: {len(all_permissions)} permisos disponibles")
        
        # Verificar roles por defecto
        roles_config = DefaultRoles.ROLES_CONFIG
        print(f"✅ Configuración de roles cargada: {len(roles_config)} roles por defecto")
        
        # Verificar validación de permisos
        for role_name, config in roles_config.items():
            try:
                SystemPermissions.validate_permissions(config["permissions"])
                print(f"✅ Rol '{role_name}': permisos válidos ({len(config['permissions'])})")
            except ValueError as e:
                print(f"❌ Rol '{role_name}': {e}")
                return False
        
        print("🎉 Sistema de permisos funcionando correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando sistema: {e}")
        return False

async def main():
    """Función principal"""
    print("🔄 SCRIPT DE LIMPIEZA Y MIGRACIÓN DE ROLES")
    print("=" * 60)
    print("Este script va a:")
    print("1. Limpiar roles existentes con permisos incompatibles")
    print("2. Crear roles por defecto del nuevo sistema")
    print("3. Actualizar usuarios para usar rol 'user' por defecto")
    print("4. Verificar que todo funcione correctamente")
    print()
    
    # Verificar sistema de permisos
    if not await verify_system_permissions():
        print("❌ El sistema de permisos tiene problemas. Abortando.")
        return 1
    
    # Ejecutar limpieza y migración
    if await clean_and_migrate_roles():
        print("\n✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("🎯 Próximos pasos:")
        print("1. Ejecutar el script de migración normal: python scripts/migrate_roles.py")
        print("2. Asignar roles específicos a usuarios via API")
        print("3. Aplicar decoradores de autorización a endpoints")
        return 0
    else:
        print("\n❌ LA MIGRACIÓN FALLÓ")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())