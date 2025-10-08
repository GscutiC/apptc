#!/usr/bin/env python3
"""Script para diagnosticar problemas de migración"""

import asyncio
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database


async def diagnose():
    db = get_database()

    print("="*70)
    print("  DIAGNOSTICO DE MIGRACION")
    print("="*70)

    # Verificar conexión
    print("\n1. Verificando conexion a MongoDB...")
    try:
        await db.list_collection_names()
        print("   [OK] Conectado correctamente")
    except Exception as e:
        print(f"   [ERROR] {e}")
        return

    # Listar colecciones
    print("\n2. Colecciones disponibles:")
    collections = await db.list_collection_names()
    for coll in collections:
        count = await db[coll].count_documents({})
        print(f"   - {coll}: {count} documentos")

    # Ver documentos raw en cada colección
    print("\n3. Documentos en interface_configurations:")
    count = 0
    async for doc in db.interface_configurations.find():
        count += 1
        print(f"   Doc #{count}:")
        print(f"      _id: {doc.get('_id')}")
        print(f"      isActive: {doc.get('isActive')}")
        print(f"      theme.name: {doc.get('theme', {}).get('name')}")
        print(f"      branding.appName: {doc.get('branding', {}).get('appName')}")

    if count == 0:
        print("   [WARNING] No se encontraron documentos")

    print("\n4. Documentos en preset_configurations:")
    count = 0
    async for doc in db.preset_configurations.find():
        count += 1
        print(f"   Doc #{count}:")
        print(f"      _id: {doc.get('_id')}")
        print(f"      name: {doc.get('name')}")
        print(f"      isDefault: {doc.get('isDefault')}")
        print(f"      isSystem: {doc.get('isSystem')}")

    if count == 0:
        print("   [WARNING] No se encontraron documentos")

    print("\n5. Documentos en configuration_history:")
    count = 0
    async for doc in db.configuration_history.find():
        count += 1
        print(f"   Doc #{count}:")
        print(f"      _id: {doc.get('_id')}")
        print(f"      version: {doc.get('version')}")
        print(f"      changedBy: {doc.get('changedBy')}")

    if count == 0:
        print("   [WARNING] No se encontraron documentos")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(diagnose())
