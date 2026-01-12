"""
Script para gestionar índices de MongoDB
Ejecutar cuando se necesite actualizar los índices de convocatorias
"""

import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio src al path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from backend.infrastructure.config.database import get_database


async def fix_convocation_indexes():
    """Eliminar índice antiguo y crear el nuevo índice compuesto"""
    
    print("🔧 Iniciando gestión de índices de MongoDB...")
    
    try:
        # Obtener base de datos
        db = get_database()
        collection = db.convocations
        
        print("\n📋 Índices actuales:")
        indexes = await collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")
        
        # Intentar eliminar índice antiguo
        print("\n🗑️ Intentando eliminar índice antiguo 'code_1'...")
        try:
            await collection.drop_index("code_1")
            print("  ✅ Índice 'code_1' eliminado exitosamente")
        except Exception as e:
            if "IndexNotFound" in str(e) or "index not found" in str(e).lower():
                print("  ℹ️ Índice 'code_1' no existe (ya fue eliminado o nunca existió)")
            else:
                print(f"  ⚠️ Error al eliminar índice: {e}")
        
        # Crear nuevo índice compuesto
        print("\n✨ Creando índice compuesto 'code_created_by_unique'...")
        try:
            await collection.create_index(
                [("code", 1), ("created_by", 1)],
                unique=True,
                name="code_created_by_unique",
                background=True
            )
            print("  ✅ Índice compuesto creado exitosamente")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ℹ️ Índice compuesto ya existe")
            else:
                print(f"  ❌ Error al crear índice: {e}")
                raise
        
        # Mostrar índices finales
        print("\n📋 Índices finales:")
        indexes = await collection.list_indexes().to_list(length=None)
        for idx in indexes:
            print(f"  - {idx['name']}: {idx.get('key', {})}")
        
        print("\n✅ Gestión de índices completada exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante la gestión de índices: {e}")
        raise


if __name__ == "__main__":
    print("=" * 70)
    print("📊 Script de Gestión de Índices de MongoDB - Convocatorias")
    print("=" * 70)
    
    asyncio.run(fix_convocation_indexes())
    
    print("\n" + "=" * 70)
    print("🎉 Proceso completado. Reinicia el backend para aplicar cambios.")
    print("=" * 70)
