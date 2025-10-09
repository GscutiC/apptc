#!/usr/bin/env python3
"""
Script para actualizar automáticamente los permisos del Super Administrador
agregando el permiso 'modules.techo_propio'
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.mi_app_completa_backend.infrastructure.config.database import get_database
from src.mi_app_completa_backend.domain.value_objects.permissions import DefaultRoles

def update_super_admin_permissions():
    """Actualizar permisos del rol Super Administrador"""
    try:
        # Obtener conexión a la base de datos
        db = get_database()
        roles_collection = db.roles
        
        # Buscar el rol Super Administrador
        super_admin_role = roles_collection.find_one({"name": "super_admin"})
        
        if not super_admin_role:
            print("❌ No se encontró el rol Super Administrador")
            return False
        
        # Obtener permisos actuales del rol
        current_permissions = set(super_admin_role.get("permissions", []))
        
        # Obtener permisos esperados para Super Admin
        expected_permissions = set([str(p) for p in DefaultRoles.SUPER_ADMIN_PERMISSIONS])
        
        # Verificar si ya tiene el permiso
        if "modules.techo_propio" in current_permissions:
            print("✅ El Super Administrador ya tiene el permiso 'modules.techo_propio'")
            return True
        
        # Actualizar permisos del rol
        result = roles_collection.update_one(
            {"name": "super_admin"},
            {
                "$set": {
                    "permissions": list(expected_permissions),
                    "updated_at": "2025-10-09T00:00:00Z"
                }
            }
        )
        
        if result.modified_count > 0:
            print("✅ Permisos del Super Administrador actualizados exitosamente")
            print(f"📊 Total permisos: {len(expected_permissions)}")
            print("🏠 Permiso 'modules.techo_propio' agregado")
            return True
        else:
            print("❌ No se pudo actualizar el rol")
            return False
            
    except Exception as e:
        print(f"❌ Error al actualizar permisos: {e}")
        return False

def verify_permissions():
    """Verificar que los permisos se aplicaron correctamente"""
    try:
        db = get_database()
        roles_collection = db.roles
        
        super_admin_role = roles_collection.find_one({"name": "super_admin"})
        
        if super_admin_role and "modules.techo_propio" in super_admin_role.get("permissions", []):
            print("✅ Verificación exitosa: Super Admin tiene acceso a Techo Propio")
            return True
        else:
            print("❌ Verificación fallida: Permiso no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Actualizando permisos del Super Administrador...")
    print("=" * 50)
    
    success = update_super_admin_permissions()
    
    if success:
        print("\n🔍 Verificando cambios...")
        verify_permissions()
        print("\n🎉 ¡Actualización completada!")
        print("\n📝 Próximos pasos:")
        print("1. Reinicia el backend si está corriendo")
        print("2. Reinicia el frontend si está corriendo") 
        print("3. Ve a http://localhost:3000/techo-propio")
        print("4. ¡Deberías tener acceso completo!")
    else:
        print("\n❌ La actualización falló")
        print("Intenta ejecutar manualmente desde la interfaz web:")
        print("1. Ve a /roles")
        print("2. Edita 'Super Administrador'")
        print("3. Marca 'Acceso al módulo Techo Propio'")
        print("4. Guarda los cambios")