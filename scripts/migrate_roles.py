"""
Script de migración para inicializar el sistema de roles mejorado
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
from mi_app_completa_backend.infrastructure.persistence.mongodb.auth_repository_impl import MongoRoleRepository
from mi_app_completa_backend.application.use_cases.role_management import InitializeDefaultRolesUseCase
from mi_app_completa_backend.domain.value_objects.permissions import DefaultRoles, SystemPermissions

async def migrate_roles():
    """Migración principal para roles"""
    print("🚀 Iniciando migración del sistema de roles...")
    
    try:
        # Conectar a la base de datos
        db = get_database()
        role_repository = MongoRoleRepository(db)
        
        # Inicializar casos de uso
        initialize_roles_use_case = InitializeDefaultRolesUseCase(role_repository)
        
        print("📋 Verificando roles existentes...")
        existing_roles = await role_repository.list_roles()
        print(f"   Roles actuales: {len(existing_roles)}")
        
        if existing_roles:
            print("   Roles encontrados:")
            for role in existing_roles:
                print(f"   - {role.name}: {role.display_name} ({len(role.permissions)} permisos)")
        
        print("\n🔧 Inicializando roles por defecto...")
        created_roles = await initialize_roles_use_case.execute()
        
        if created_roles:
            print(f"✅ Se crearon {len(created_roles)} nuevos roles:")
            for role in created_roles:
                print(f"   - {role.name}: {role.display_name}")
                print(f"     Permisos: {len(role.permissions)}")
                if role.permissions and len(role.permissions) <= 5:
                    for perm in role.permissions:
                        print(f"       * {perm}")
                elif role.permissions:
                    print(f"       * {role.permissions[0]}")
                    print(f"       * ... y {len(role.permissions) - 1} más")
                print()
        else:
            print("ℹ️  No se crearon nuevos roles (ya existen)")
        
        print("📊 Verificando permisos del sistema...")
        all_permissions = SystemPermissions.get_all_permissions()
        print(f"   Total de permisos disponibles: {len(all_permissions)}")
        
        # Organizar por categorías
        by_category = {}
        for perm in all_permissions:
            category = perm.category.value
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(perm)
        
        for category, perms in by_category.items():
            print(f"   - {category}: {len(perms)} permisos")
        
        print("\n🔍 Verificando configuración de roles por defecto...")
        for role_name, config in DefaultRoles.ROLES_CONFIG.items():
            print(f"   - {role_name}:")
            print(f"     Display: {config['display_name']}")
            print(f"     Permisos: {len(config['permissions'])}")
            
            # Verificar que todos los permisos sean válidos
            try:
                SystemPermissions.validate_permissions(config['permissions'])
                print(f"     ✅ Todos los permisos son válidos")
            except ValueError as e:
                print(f"     ❌ Error en permisos: {e}")
        
        print("\n✅ Migración completada exitosamente!")
        print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def verify_migration():
    """Verificar que la migración fue exitosa"""
    print("\n🔍 Verificando migración...")
    
    try:
        db = get_database()
        role_repository = MongoRoleRepository(db)
        
        # Verificar que existen los roles básicos
        required_roles = ["user", "admin", "super_admin"]
        missing_roles = []
        
        for role_name in required_roles:
            role = await role_repository.get_role_by_name(role_name)
            if not role:
                missing_roles.append(role_name)
            else:
                print(f"   ✅ Rol '{role_name}' existe con {len(role.permissions)} permisos")
        
        if missing_roles:
            print(f"   ❌ Roles faltantes: {missing_roles}")
            return False
        
        # Verificar que el super_admin tiene permisos suficientes
        super_admin = await role_repository.get_role_by_name("super_admin")
        if super_admin and len(super_admin.permissions) > 10:
            print(f"   ✅ Super admin tiene {len(super_admin.permissions)} permisos")
        else:
            print(f"   ⚠️  Super admin tiene pocos permisos: {len(super_admin.permissions) if super_admin else 0}")
        
        print("   ✅ Verificación completada")
        return True
        
    except Exception as e:
        print(f"   ❌ Error en verificación: {e}")
        return False

async def show_migration_summary():
    """Mostrar resumen de la migración"""
    print("\n📋 RESUMEN DE LA MIGRACIÓN")
    print("=" * 50)
    
    try:
        db = get_database()
        role_repository = MongoRoleRepository(db)
        
        roles = await role_repository.list_roles()
        
        print(f"Total de roles: {len(roles)}")
        print(f"Permisos del sistema: {len(SystemPermissions.get_all_permissions())}")
        print(f"Categorías de permisos: {len(set(p.category.value for p in SystemPermissions.get_all_permissions()))}")
        
        print("\nRoles creados/verificados:")
        for role in roles:
            status = "🟢 Sistema" if role.is_system_role else "🔵 Personalizado"
            active = "✅ Activo" if role.is_active else "❌ Inactivo"
            print(f"  {status} {role.name}: {role.display_name} ({len(role.permissions)} permisos) {active}")
        
        print(f"\n⏰ Migración completada: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 Sistema de roles mejorado listo para usar!")
        
    except Exception as e:
        print(f"❌ Error mostrando resumen: {e}")

async def main():
    """Función principal de migración"""
    print("🎯 MIGRACIÓN DEL SISTEMA DE ROLES Y PERMISOS")
    print("=" * 60)
    
    # Ejecutar migración
    success = await migrate_roles()
    
    if success:
        # Verificar migración
        verification_success = await verify_migration()
        
        if verification_success:
            # Mostrar resumen
            await show_migration_summary()
        else:
            print("⚠️  La migración se completó pero hubo problemas en la verificación")
            return 1
    else:
        print("❌ La migración falló")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())