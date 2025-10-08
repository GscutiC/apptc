#!/usr/bin/env python3
"""
Script para probar los endpoints refactorizados de interface config
"""

import asyncio
import os
import sys
from datetime import datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database
from mi_app_completa_backend.infrastructure.persistence.mongodb.interface_config_repository_impl import (
    MongoInterfaceConfigRepository,
    MongoPresetConfigRepository,
    MongoConfigHistoryRepository
)
from mi_app_completa_backend.application.use_cases.interface_config_use_cases import InterfaceConfigUseCases


def print_separator():
    print("=" * 70)


async def test_api():
    """Probar funcionalidad del API refactorizado"""

    print_separator()
    print("  PRUEBA DE API REFACTORIZADO")
    print_separator()

    # Inicializar repositorios y use cases
    db = get_database()
    config_repo = MongoInterfaceConfigRepository(db)
    preset_repo = MongoPresetConfigRepository(db)
    history_repo = MongoConfigHistoryRepository(db)
    use_cases = InterfaceConfigUseCases(config_repo, preset_repo, history_repo)

    # Test 1: Obtener configuración actual
    print("\n[TEST 1] Obtener configuracion actual...")
    current_config = await use_cases.get_current_config()
    if current_config:
        print(f"   [OK] Config activa: {current_config.branding.appName}")
        print(f"   [OK] Tema: {current_config.theme.name}")
        print(f"   [OK] ID: {current_config.id}")
    else:
        print("   [WARNING] No hay configuracion activa")

    # Test 2: Obtener todos los presets
    print("\n[TEST 2] Obtener todos los presets...")
    presets = await use_cases.get_all_presets()
    print(f"   [OK] Total de presets: {len(presets)}")
    for preset in presets:
        default_mark = "[DEFAULT]" if preset.isDefault else ""
        system_mark = "[SYSTEM]" if preset.isSystem else ""
        print(f"   - {preset.name} {default_mark} {system_mark}")

    # Test 3: Obtener historial
    print("\n[TEST 3] Obtener historial de cambios...")
    history = await use_cases.get_config_history(limit=5)
    print(f"   [OK] Total de entradas en historial: {len(history)}")
    for entry in history:
        print(f"   - Version {entry.version}: {entry.changeDescription} (por {entry.changedBy})")

    # Test 4: Aplicar un preset diferente
    if len(presets) >= 2:
        print("\n[TEST 4] Aplicar preset diferente...")
        # Buscar un preset que no sea el actual
        preset_to_apply = None
        for preset in presets:
            if current_config and preset.config.theme.name != current_config.theme.name:
                preset_to_apply = preset
                break

        if preset_to_apply:
            print(f"   [INFO] Aplicando preset: {preset_to_apply.name}")
            applied_config = await use_cases.apply_preset(
                preset_id=preset_to_apply.id,
                applied_by="test_script"
            )
            if applied_config:
                print(f"   [OK] Preset aplicado correctamente")
                print(f"   [OK] Nuevo tema activo: {applied_config.theme.name}")

                # Verificar que se guardó en historial
                new_history = await use_cases.get_config_history(limit=1)
                if new_history:
                    print(f"   [OK] Entrada de historial creada: {new_history[0].changeDescription}")
            else:
                print("   [ERROR] No se pudo aplicar el preset")
        else:
            print("   [SKIP] No hay preset diferente para aplicar")
    else:
        print("\n[TEST 4] SKIP - No hay suficientes presets")

    # Test 5: Verificar que solo hay una configuración activa
    print("\n[TEST 5] Verificar unicidad de configuracion activa...")
    all_configs = await config_repo.get_all_configs()
    active_configs = [c for c in all_configs if c.is_active]
    if len(active_configs) == 1:
        print(f"   [OK] Solo hay 1 configuracion activa")
    else:
        print(f"   [ERROR] Hay {len(active_configs)} configuraciones activas (deberia ser 1)")

    print_separator()
    print("  PRUEBAS COMPLETADAS")
    print_separator()


if __name__ == "__main__":
    asyncio.run(test_api())
