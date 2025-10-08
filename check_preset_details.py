"""Script para ver detalles completos de presets en MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_preset_details():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['mi_app_completa_db']
    
    print("🔍 DETALLES DE PRESETS EN MONGODB:\n")
    
    async for preset in db.preset_configurations.find({'isSystem': True}).sort("name", 1):
        name = preset.get('name', 'N/A')
        preset_id = preset.get('id', 'N/A')
        is_default = preset.get('isDefault', False)
        
        # Obtener colores
        theme = preset.get('theme', {})
        colors = theme.get('colors', {})
        primary = colors.get('primary', {})
        
        print(f"📋 Preset: {name}")
        print(f"   ID: {preset_id}")
        print(f"   Default: {is_default}")
        print(f"   Color Primario 500: {primary.get('500', 'N/A')}")
        print(f"   Modo: {theme.get('mode', 'N/A')}")
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_preset_details())
