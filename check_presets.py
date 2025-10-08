"""Script para verificar presets en MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_presets():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['mi_app_completa_db']
    
    # Contar presets
    total = await db.preset_configurations.count_documents({})
    system = await db.preset_configurations.count_documents({'isSystem': True})
    custom = await db.preset_configurations.count_documents({'isSystem': False})
    
    print(f"📊 PRESETS EN MONGODB:")
    print(f"   Total: {total}")
    print(f"   Sistema: {system}")
    print(f"   Personalizados: {custom}")
    print()
    
    # Listar presets del sistema
    if system > 0:
        print("🎨 Presets del Sistema:")
        async for preset in db.preset_configurations.find({'isSystem': True}):
            name = preset.get('name', 'N/A')
            is_default = preset.get('isDefault', False)
            default_mark = " [DEFAULT]" if is_default else ""
            print(f"   ✓ {name}{default_mark}")
    else:
        print("⚠️  NO HAY PRESETS DEL SISTEMA EN MONGODB")
        print("   Los presets del sistema deberían haber sido creados durante la migración")
    
    print()
    
    # Listar presets personalizados
    if custom > 0:
        print("👤 Presets Personalizados:")
        async for preset in db.preset_configurations.find({'isSystem': False}):
            name = preset.get('name', 'N/A')
            print(f"   • {name}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_presets())
