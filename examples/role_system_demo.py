"""
Ejemplo de uso del nuevo sistema de roles y permisos
"""
import asyncio
import os
import sys
from typing import List

# Agregar el directorio src al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.domain.value_objects.permissions import (
    SystemPermissions, DefaultRoles, has_permission
)
from mi_app_completa_backend.domain.entities.auth_models import Role, UserWithRole
from mi_app_completa_backend.application.dto.role_dto import RoleCreateDTO

def demonstrate_permissions():
    """Demostrar el sistema de permisos"""
    print("🔐 SISTEMA DE PERMISOS GRANULARES")
    print("=" * 50)
    
    # Mostrar todos los permisos disponibles
    all_permissions = SystemPermissions.get_all_permissions()
    print(f"📋 Total de permisos en el sistema: {len(all_permissions)}")
    
    # Organizar por categorías
    by_category = {}
    for perm in all_permissions:
        category = perm.category.value
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(perm)
    
    print("\n📂 Permisos por categoría:")
    for category, perms in by_category.items():
        print(f"  {category.upper()}:")
        for perm in perms:
            print(f"    • {perm} - {perm.description}")
        print()

def demonstrate_roles():
    """Demostrar los roles por defecto"""
    print("👥 ROLES POR DEFECTO DEL SISTEMA")
    print("=" * 50)
    
    for role_name, config in DefaultRoles.ROLES_CONFIG.items():
        print(f"🎭 {role_name.upper()}")
        print(f"   Nombre: {config['display_name']}")
        print(f"   Descripción: {config['description']}")
        print(f"   Permisos ({len(config['permissions'])}):")
        
        if len(config['permissions']) <= 8:
            for perm in config['permissions']:
                print(f"     • {perm}")
        else:
            for perm in config['permissions'][:5]:
                print(f"     • {perm}")
            print(f"     • ... y {len(config['permissions']) - 5} permisos más")
        print()

def demonstrate_permission_checking():
    """Demostrar verificación de permisos"""
    print("🔍 VERIFICACIÓN DE PERMISOS")
    print("=" * 50)
    
    # Simular diferentes usuarios
    users = [
        {
            "name": "Usuario Básico",
            "permissions": DefaultRoles.ROLES_CONFIG["user"]["permissions"]
        },
        {
            "name": "Administrador",
            "permissions": DefaultRoles.ROLES_CONFIG["admin"]["permissions"]
        },
        {
            "name": "Super Admin",
            "permissions": DefaultRoles.ROLES_CONFIG["super_admin"]["permissions"]
        }
    ]
    
    # Permisos a verificar
    test_permissions = [
        "users.create",
        "users.read",
        "roles.create",
        "roles.update",
        "messages.create",
        "ai.process",
        "admin.manage_settings"
    ]
    
    print("Verificando permisos por usuario:\n")
    
    for user in users:
        print(f"👤 {user['name']}:")
        user_perms = user['permissions']
        
        for test_perm in test_permissions:
            has_perm = has_permission(user_perms, test_perm)
            status = "✅" if has_perm else "❌"
            print(f"   {status} {test_perm}")
        
        print(f"   📊 Total permisos: {len(user_perms)}")
        print()

def demonstrate_role_creation():
    """Demostrar creación de roles personalizados"""
    print("🛠️  CREACIÓN DE ROLES PERSONALIZADOS")
    print("=" * 50)
    
    # Ejemplo de rol personalizado
    custom_role_dto = RoleCreateDTO(
        name="content_moderator",
        display_name="Moderador de Contenido",
        description="Usuario que puede moderar mensajes y ver usuarios básicos",
        permissions=[
            "messages.create",
            "messages.read", 
            "messages.update",
            "messages.delete",
            "users.read",
            "ai.process"
        ],
        is_active=True
    )
    
    print("📝 Ejemplo de rol personalizado:")
    print(f"   Nombre: {custom_role_dto.name}")
    print(f"   Display: {custom_role_dto.display_name}")
    print(f"   Descripción: {custom_role_dto.description}")
    print(f"   Permisos ({len(custom_role_dto.permissions)}):")
    for perm in custom_role_dto.permissions:
        print(f"     • {perm}")
    print()
    
    # Verificar que los permisos son válidos
    try:
        SystemPermissions.validate_permissions(custom_role_dto.permissions)
        print("✅ Todos los permisos son válidos")
    except ValueError as e:
        print(f"❌ Error en permisos: {e}")

def demonstrate_api_usage():
    """Demostrar uso en APIs con decoradores"""
    print("🌐 USO EN ENDPOINTS DE API")
    print("=" * 50)
    
    print("Ejemplos de decoradores para endpoints:")
    print()
    
    examples = [
        {
            "endpoint": "POST /auth/roles/create",
            "decorator": "@requires_permission('roles.create')",
            "description": "Solo usuarios con permiso roles.create"
        },
        {
            "endpoint": "GET /auth/users",
            "decorator": "@requires_permission('users.list')",
            "description": "Solo usuarios con permiso users.list"
        },
        {
            "endpoint": "DELETE /auth/roles/{id}",
            "decorator": "@requires_any_permission(['roles.delete', 'admin.manage_settings'])",
            "description": "Usuarios con cualquiera de estos permisos"
        },
        {
            "endpoint": "POST /admin/settings",
            "decorator": "@super_admin_required()",
            "description": "Solo super administradores"
        },
        {
            "endpoint": "GET /messages",
            "decorator": "@requires_role('user', 'moderator', 'admin')",
            "description": "Usuarios con alguno de estos roles"
        }
    ]
    
    for example in examples:
        print(f"🔗 {example['endpoint']}")
        print(f"   Decorador: {example['decorator']}")
        print(f"   Acceso: {example['description']}")
        print()

def demonstrate_audit_system():
    """Demostrar sistema de auditoría"""
    print("📊 SISTEMA DE AUDITORÍA")
    print("=" * 50)
    
    print("El sistema registra automáticamente:")
    print("• Creación, actualización y eliminación de usuarios")
    print("• Creación, actualización y eliminación de roles") 
    print("• Asignación de roles a usuarios")
    print("• Intentos de acceso no autorizado")
    print("• Cambios en configuración del sistema")
    print("• Login y logout de usuarios")
    print()
    
    print("Información capturada en cada log:")
    print("• Usuario que realizó la acción")
    print("• Timestamp de la acción")
    print("• Tipo de recurso afectado")
    print("• Valores anteriores y nuevos")
    print("• Dirección IP y User-Agent")
    print("• Si la acción fue exitosa o falló")
    print()
    
    print("📈 Estadísticas disponibles:")
    print("• Actividad por usuario")
    print("• Acciones más frecuentes")  
    print("• Usuarios más activos")
    print("• Intentos de acceso no autorizado")
    print("• Resumen de cambios por período")

def main():
    """Función principal del ejemplo"""
    print("🎯 SISTEMA DE ROLES Y PERMISOS AVANZADO")
    print("=" * 60)
    print("Demostrando las capacidades del nuevo sistema\n")
    
    demonstrate_permissions()
    print("\n" + "="*60 + "\n")
    
    demonstrate_roles()
    print("\n" + "="*60 + "\n")
    
    demonstrate_permission_checking()
    print("\n" + "="*60 + "\n")
    
    demonstrate_role_creation()
    print("\n" + "="*60 + "\n")
    
    demonstrate_api_usage()
    print("\n" + "="*60 + "\n")
    
    demonstrate_audit_system()
    print("\n" + "="*60 + "\n")
    
    print("🎉 SISTEMA LISTO PARA PRODUCCIÓN")
    print("=" * 60)
    print("✅ Permisos granulares implementados")
    print("✅ Roles por defecto configurados")
    print("✅ Decoradores de autorización listos")
    print("✅ API endpoints implementados")
    print("✅ Sistema de auditoría activo")
    print("✅ Tests unitarios incluidos")
    print("✅ Script de migración disponible")
    print()
    print("🚀 Para empezar:")
    print("1. Ejecutar: python scripts/migrate_roles.py")
    print("2. Usar decoradores en endpoints existentes")
    print("3. Asignar roles a usuarios via API")
    print("4. Monitorear logs de auditoría")

if __name__ == "__main__":
    main()