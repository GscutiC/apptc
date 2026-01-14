#!/usr/bin/env python3
"""
Script de prueba para la API RENIEC
Consulta datos de una persona por su DNI
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Agregar el proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from backend.infrastructure.services.government_apis.reniec_service import ReniecService
from backend.domain.entities.government_apis.reniec_entity import DniData, DniConsultaResponse


async def test_reniec_service():
    """Prueba del servicio RENIEC"""
    
    # DNI a consultar
    dni = "47649607"
    
    print("=" * 80)
    print("🔍 PRUEBA DE API RENIEC")
    print("=" * 80)
    print(f"\n📋 DNI a consultar: {dni}")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    print("\n" + "-" * 80)
    
    # Inicializar servicio
    service = ReniecService()
    
    print("\n🔌 Información del servicio:")
    print(f"  • Proveedor: {service.provider.value}")
    print(f"  • Endpoints principales: {len(service.api_endpoints)}")
    for idx, endpoint in enumerate(service.api_endpoints, 1):
        print(f"    {idx}. {endpoint}")
    print(f"  • Endpoints de respaldo: {len(service.backup_endpoints)}")
    for idx, endpoint in enumerate(service.backup_endpoints, 1):
        print(f"    {idx}. {endpoint}")
    print(f"  • Timeout: {service.timeout}s")
    print(f"  • Cache TTL: {service.cache_ttl}s")
    
    print("\n" + "-" * 80)
    print(f"\n📡 Consultando RENIEC con DNI: {dni}\n")
    
    try:
        # Validar DNI
        print(f"1️⃣  Validando formato de DNI...")
        is_valid = service.validate_document(dni)
        if not is_valid:
            print(f"   ❌ DNI inválido: {dni}")
            return
        print(f"   ✅ DNI válido")
        
        # Consultar API
        print(f"\n2️⃣  Consultando API RENIEC...")
        result = await service.query_document(dni)
        
        print(f"\n3️⃣  RESULTADO DE LA CONSULTA:")
        print(f"   • Éxito: {result.success}")
        print(f"   • Mensaje: {result.message}")
        print(f"   • Fuente: {result.fuente}")
        print(f"   • Caché: {'SÍ (hit)' if result.cache_hit else 'No'}")
        print(f"   • Timestamp: {result.timestamp.isoformat()}")
        
        if result.data:
            print(f"\n4️⃣  DATOS OBTENIDOS:")
            print(f"   • DNI: {result.data.dni}")
            print(f"   • Nombres: {result.data.nombres}")
            print(f"   • Apellido Paterno: {result.data.apellido_paterno}")
            print(f"   • Apellido Materno: {result.data.apellido_materno}")
            print(f"   • Apellidos: {result.data.apellidos}")
            print(f"   • Nombre Completo: {result.data.nombre_completo}")
            
            # Esta es la parte que te interesa - Fecha de nacimiento
            if result.data.fecha_nacimiento:
                print(f"\n   🎂 FECHA DE NACIMIENTO: {result.data.fecha_nacimiento}")
            else:
                print(f"\n   ⚠️  Fecha de nacimiento: NO DISPONIBLE")
            
            # Otros campos
            if result.data.estado_civil:
                print(f"   • Estado Civil: {result.data.estado_civil}")
            if result.data.ubigeo:
                print(f"   • UBIGEO: {result.data.ubigeo}")
            if result.data.direccion:
                print(f"   • Dirección: {result.data.direccion}")
            if result.data.restricciones:
                print(f"   • Restricciones: {result.data.restricciones}")
            
            # Mostrar datos en JSON
            print(f"\n5️⃣  DATOS EN JSON:")
            datos_json = {
                "dni": result.data.dni,
                "nombres": result.data.nombres,
                "apellido_paterno": result.data.apellido_paterno,
                "apellido_materno": result.data.apellido_materno,
                "nombre_completo": result.data.nombre_completo,
                "fecha_nacimiento": result.data.fecha_nacimiento,
                "estado_civil": result.data.estado_civil,
                "ubigeo": result.data.ubigeo,
                "direccion": result.data.direccion,
            }
            print(json.dumps(datos_json, indent=2, ensure_ascii=False))
        else:
            print(f"\n   ❌ No se obtuvieron datos")
        
        print("\n" + "=" * 80)
        
        # Health check
        print("\n🏥 HEALTH CHECK DEL SERVICIO:")
        health = await service.health_check()
        print(json.dumps(health, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        import traceback
        print(f"\n   Traceback:")
        traceback.print_exc()


async def test_multiple_endpoints():
    """Prueba cada endpoint de forma individual"""
    
    dni = "47649607"
    service = ReniecService()
    
    print("\n\n" + "=" * 80)
    print("🧪 PRUEBA DE ENDPOINTS INDIVIDUALES")
    print("=" * 80)
    
    all_endpoints = service.api_endpoints + service.backup_endpoints
    
    for idx, endpoint in enumerate(all_endpoints, 1):
        print(f"\n{idx}. Endpoint: {endpoint}")
        print("-" * 60)
        try:
            result = await service._consultar_api_reniec(dni, endpoint)
            print(f"   Resultado: {'✅ Exitoso' if result.success else '❌ Fallido'}")
            print(f"   Mensaje: {result.message}")
            if result.data:
                print(f"   Datos: {result.data.nombre_completo}")
                if result.data.fecha_nacimiento:
                    print(f"   Fecha Nacimiento: {result.data.fecha_nacimiento}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {str(e)}")


async def main():
    """Función principal"""
    await test_reniec_service()
    await test_multiple_endpoints()


if __name__ == "__main__":
    print("\n🚀 Iniciando pruebas de RENIEC...\n")
    asyncio.run(main())
    print("\n✅ Pruebas completadas\n")
