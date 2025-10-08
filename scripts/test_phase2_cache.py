#!/usr/bin/env python3
"""
Script para probar FASE 2: Caché y sincronización
"""

import asyncio
import os
import sys
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database
from mi_app_completa_backend.infrastructure.persistence.mongodb.interface_config_repository_impl import (
    MongoInterfaceConfigRepository,
    MongoPresetConfigRepository
)
from mi_app_completa_backend.infrastructure.services.cache_service import (
    interface_config_cache,
    preset_cache
)


def print_separator():
    print("=" * 70)


async def test_cache():
    """Probar sistema de caché"""

    print_separator()
    print("  PRUEBA DE CACHE - FASE 2.2")
    print_separator()

    # Inicializar repositorios
    db = get_database()
    config_repo = MongoInterfaceConfigRepository(db)
    preset_repo = MongoPresetConfigRepository(db)

    # Test 1: Primera lectura (sin caché)
    print("\n[TEST 1] Primera lectura de configuracion (sin cache)...")
    start_time = time.time()
    config1 = await config_repo.get_current_config()
    time1 = (time.time() - start_time) * 1000
    if config1:
        print(f"   [OK] Configuracion obtenida: {config1.branding.app_name}")
        print(f"   [TIME] Tiempo sin cache: {time1:.2f}ms")

    # Test 2: Segunda lectura (desde caché)
    print("\n[TEST 2] Segunda lectura de configuracion (desde cache)...")
    start_time = time.time()
    config2 = await config_repo.get_current_config()
    time2 = (time.time() - start_time) * 1000
    if config2:
        print(f"   [OK] Configuracion obtenida: {config2.branding.app_name}")
        print(f"   [TIME] Tiempo con cache: {time2:.2f}ms")
        print(f"   [SPEEDUP] Mejora: {time1/time2:.1f}x mas rapido")

    # Test 3: Estadísticas del caché
    print("\n[TEST 3] Estadisticas del cache...")
    config_stats = interface_config_cache.get_stats()
    print(f"   [INFO] Configuraciones en cache: {config_stats['active_entries']}")
    print(f"   [INFO] TTL configurado: {config_stats['ttl_seconds']}s")

    # Test 4: Presets con caché
    print("\n[TEST 4] Obtener presets (sin cache)...")
    start_time = time.time()
    presets1 = await preset_repo.get_all_presets()
    time3 = (time.time() - start_time) * 1000
    print(f"   [OK] {len(presets1)} presets obtenidos")
    print(f"   [TIME] Tiempo sin cache: {time3:.2f}ms")

    print("\n[TEST 5] Obtener presets (desde cache)...")
    start_time = time.time()
    presets2 = await preset_repo.get_all_presets()
    time4 = (time.time() - start_time) * 1000
    print(f"   [OK] {len(presets2)} presets obtenidos")
    print(f"   [TIME] Tiempo con cache: {time4:.2f}ms")
    print(f"   [SPEEDUP] Mejora: {time3/time4:.1f}x mas rapido")

    preset_stats = preset_cache.get_stats()
    print(f"   [INFO] Presets en cache: {preset_stats['active_entries']}")
    print(f"   [INFO] TTL configurado: {preset_stats['ttl_seconds']}s")

    # Test 6: Invalidación de caché
    print("\n[TEST 6] Probar invalidacion de cache...")
    interface_config_cache.delete("interface_config:current")
    print("   [OK] Cache de configuracion invalidado")

    config3 = await config_repo.get_current_config()
    if config3:
        print("   [OK] Configuracion recargada desde MongoDB")

    config_stats_after = interface_config_cache.get_stats()
    print(f"   [INFO] Entradas activas despues: {config_stats_after['active_entries']}")

    print_separator()
    print("  PRUEBAS DE CACHE COMPLETADAS")
    print_separator()


if __name__ == "__main__":
    asyncio.run(test_cache())
