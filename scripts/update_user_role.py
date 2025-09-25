#!/usr/bin/env python3
"""
Script para actualizar el rol de un usuario específico a super_admin
"""

import asyncio
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from mi_app_completa_backend.infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository, MongoRoleRepository
from mi_app_completa_backend.infrastructure.config.database import get_database
from mi_app_completa_backend.domain.value_objects.permissions import DefaultRoles

async def update_user_role():
    """Actualizar el rol del usuario Jonathan Elías Delgado a super_admin"""
    
    # Configurar base de datos
    database = await get_database()
    user_repo = MongoUserRepository(database)
    role_repo = MongoRoleRepository(database)
    
    try:
        # Buscar el usuario por email o clerk_id
        user_email = "vedjonathanelias@gmail.com"
        clerk_id = "user_339MX93RuwY00NUReUR2HCxBrDu"
        
        print(f"🔍 Buscando usuario con email: {user_email}")
        print(f"🔍 O con clerk_id: {clerk_id}")
        
        # Intentar buscar por ambos métodos
        user = None
        users = await user_repo.find_all()
        
        for u in users:
            if u.email == user_email or u.clerk_id == clerk_id:
                user = u
                break
        
        if not user:
            print(f"❌ Usuario no encontrado con email {user_email} o clerk_id {clerk_id}")
            
            # Mostrar todos los usuarios disponibles
            print("\n📋 Usuarios disponibles:")
            for u in users:
                print(f"  - ID: {u.id}")
                print(f"    Email: {u.email}")
                print(f"    Clerk ID: {u.clerk_id}")
                print(f"    Nombre: {u.full_name}")
                print(f"    Rol actual: {u.role_id if hasattr(u, 'role_id') else 'N/A'}")
                print("")
            return
        
        print(f"✅ Usuario encontrado: {user.full_name} ({user.email})")
        
        # Obtener el rol de super_admin
        print("🔍 Buscando rol super_admin...")
        
        # Verificar si el rol existe
        roles = await role_repo.get_all_roles()
        super_admin_role = None
        
        for role in roles:
            if role.name == "super_admin":
                super_admin_role = role
                break
        
        if not super_admin_role:
            print("❌ Rol super_admin no encontrado")
            print("📋 Roles disponibles:")
            for role in roles:
                print(f"  - {role.name}: {role.display_name}")
            return
        
        print(f"✅ Rol super_admin encontrado: {super_admin_role.display_name}")
        
        # Actualizar el rol del usuario
        print(f"🔄 Actualizando rol del usuario {user.full_name}...")
        
        success = await role_repo.assign_role_to_user_by_clerk_id(user.clerk_id, "super_admin")
        
        if success:
            print(f"✅ ¡Rol actualizado exitosamente!")
            print(f"   Usuario: {user.full_name}")
            print(f"   Email: {user.email}")
            print(f"   Nuevo rol: super_admin")
            
            # Verificar que el cambio se aplicó
            updated_user = await user_repo.get_user_by_clerk_id(user.clerk_id)
            if updated_user:
                print(f"🔍 Verificación - Rol actual: {updated_user.role_id}")
        else:
            print("❌ Error al actualizar el rol")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(update_user_role())