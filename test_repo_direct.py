"""
Script de prueba directo para diagnosticar el problema del repositorio
"""
import asyncio
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mi_app_completa_backend.infrastructure.config.database import get_database
from mi_app_completa_backend.infrastructure.persistence.techo_propio.mongo_techo_propio_repository import MongoTechoPropioRepository


async def test_repository():
    """Probar el repositorio directamente"""
    print("🔍 Iniciando prueba del repositorio...")
    
    try:
        # Crear instancia del repositorio
        print("📦 Creando instancia del repositorio...")
        repo = MongoTechoPropioRepository()
        
        print(f"✅ Repositorio creado. Tipo de colección: {type(repo.collection)}")
        
        # Probar get_applications_by_user
        print("\n🔎 Probando get_applications_by_user...")
        user_id = "real_user_123"
        
        applications = await repo.get_applications_by_user(
            user_id=user_id,
            limit=10,
            offset=0
        )
        
        print(f"✅ Resultado: {len(applications)} aplicaciones encontradas")
        
        # Probar count_applications_by_user
        print("\n🔢 Probando count_applications_by_user...")
        total_count = await repo.count_applications_by_user(
            user_id=user_id,
            status=None
        )
        
        print(f"✅ Total count: {total_count} (tipo: {type(total_count)})")
        
        # Probar cálculo de paginación
        print("\n📊 Probando cálculo de paginación...")
        limit = 10
        offset = 0
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        
        print(f"✅ Página: {page}, Total páginas: {total_pages}")
        print(f"📋 Aplicaciones: {applications}")
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DIRECTO DEL REPOSITORIO TECHO PROPIO")
    print("=" * 60)
    
    asyncio.run(test_repository())
    
    print("\n" + "=" * 60)
    print("FIN DE LA PRUEBA")
    print("=" * 60)
