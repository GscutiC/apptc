#!/usr/bin/env python3
"""
Script para verificar el estado de la migración en MongoDB
"""

import asyncio
import os
import sys

# Agregar el directorio src al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database


async def verify_migration():
    """Verificar estado de la migración"""
    print("="*70)
    print("  VERIFICACION DE MIGRACION")
    print("="*70)

    db = get_database()

    # Contar documentos
    configs_count = await db.interface_configurations.count_documents({})
    presets_count = await db.preset_configurations.count_documents({})
    history_count = await db.configuration_history.count_documents({})

    print(f"\nColecciones:")
    print(f"   Configuraciones: {configs_count}")
    print(f"   Presets: {presets_count}")
    print(f"   Historial: {history_count}")

    # Verificar configuración activa
    print(f"\nConfiguracion activa:")
    active_config = await db.interface_configurations.find_one({"isActive": True})
    if active_config:
        theme_name = active_config.get("theme", {}).get("name", "N/A")
        app_name = active_config.get("branding", {}).get("appName", "N/A")
        print(f"   Tema: {theme_name}")
        print(f"   App: {app_name}")
        print(f"   ID: {active_config.get('_id')}")
    else:
        print("   [ERROR] No se encontro configuracion activa")

    # Listar presets
    print(f"\nPresets disponibles:")
    async for preset in db.preset_configurations.find():
        name = preset.get("name", "N/A")
        is_default = preset.get("isDefault", False)
        is_system = preset.get("isSystem", False)
        default_mark = " [DEFAULT]" if is_default else ""
        system_mark = " [SYSTEM]" if is_system else ""
        print(f"   - {name}{default_mark}{system_mark}")

    # Historial
    print(f"\nHistorial:")
    async for entry in db.configuration_history.find().limit(5):
        version = entry.get("version", "N/A")
        changed_by = entry.get("changedBy", "N/A")
        description = entry.get("changeDescription", "N/A")
        print(f"   Version {version}: {description} (por {changed_by})")

    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(verify_migration())
