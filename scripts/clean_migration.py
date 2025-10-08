#!/usr/bin/env python3
"""Script para limpiar datos de migración en MongoDB"""

import asyncio
import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database


async def clean():
    db = get_database()

    result1 = await db.interface_configurations.delete_many({})
    result2 = await db.preset_configurations.delete_many({})
    result3 = await db.configuration_history.delete_many({})

    print(f"Configuraciones eliminadas: {result1.deleted_count}")
    print(f"Presets eliminados: {result2.deleted_count}")
    print(f"Historial eliminado: {result3.deleted_count}")
    print("Base de datos limpiada")


if __name__ == "__main__":
    asyncio.run(clean())
