"""
Script temporal para verificar convocatorias en MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def check_convocations():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['apptc']
    
    # Obtener todas las convocatorias
    convocations = await db.convocations.find().to_list(length=100)
    
    print(f"\n{'='*60}")
    print(f"Total convocatorias encontradas: {len(convocations)}")
    print(f"{'='*60}\n")
    
    if len(convocations) == 0:
        print("⚠️  NO HAY CONVOCATORIAS EN LA BASE DE DATOS")
        print("   Necesitas crear al menos una convocatoria activa y publicada\n")
    else:
        for conv in convocations:
            print(f"📋 Código: {conv.get('code')}")
            print(f"   Título: {conv.get('title')}")
            print(f"   is_active: {conv.get('is_active')}")
            print(f"   is_published: {conv.get('is_published')}")
            print(f"   is_current: {conv.get('is_current', False)}")
            print(f"   Fecha inicio: {conv.get('start_date')}")
            print(f"   Fecha fin: {conv.get('end_date')}")
            print()
    
    # Verificar convocatorias activas y publicadas
    active_published = await db.convocations.find({
        'is_active': True,
        'is_published': True
    }).to_list(length=100)
    
    print(f"{'='*60}")
    print(f"Convocatorias ACTIVAS y PUBLICADAS: {len(active_published)}")
    print(f"{'='*60}\n")
    
    if len(active_published) == 0:
        print("⚠️  NO HAY CONVOCATORIAS ACTIVAS Y PUBLICADAS")
        print("   El endpoint /active NO retornará ninguna convocatoria")
        print("   Debes publicar una convocatoria para que aparezca\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_convocations())
