"""
Ejemplos de uso del módulo de APIs Gubernamentales
Casos de uso reales desde diferentes partes del sistema
"""

import asyncio
from typing import Optional

# ============== Ejemplo 1: Uso Básico con Helper ==============

async def ejemplo_uso_basico():
    """Ejemplo más simple: usar el helper service"""
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Consultar DNI
    persona = await helper.get_persona_by_dni("12345678")
    if persona:
        print(f"Nombre: {persona.nombre_completo}")
        print(f"DNI: {persona.dni}")
    else:
        print("No se encontró información")
    
    # Consultar RUC
    empresa = await helper.get_empresa_by_ruc("20123456789")
    if empresa:
        print(f"Empresa: {empresa.razon_social}")
        print(f"Estado: {empresa.estado}")


# ============== Ejemplo 2: Validación de Usuarios ==============

async def validar_usuario_por_dni(dni: str, user_id: str) -> bool:
    """
    Validar que un DNI existe en RENIEC antes de crear usuario
    
    Caso de uso: Registro de usuarios
    """
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Primero validar formato
    if not helper.validate_dni(dni):
        print(f"❌ DNI {dni} tiene formato inválido")
        return False
    
    # Consultar en RENIEC
    persona = await helper.get_persona_by_dni(dni, user_id)
    
    if persona:
        print(f"✅ DNI válido: {persona.nombre_completo}")
        return True
    else:
        print(f"❌ DNI no encontrado en RENIEC")
        return False


# ============== Ejemplo 3: Validación de Empresas ==============

async def validar_empresa_activa(ruc: str) -> tuple[bool, Optional[str]]:
    """
    Validar que una empresa está activa en SUNAT
    
    Caso de uso: Registro de proveedores
    Returns:
        (es_valida, razon_social)
    """
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Validar formato
    if not helper.validate_ruc(ruc):
        return (False, None)
    
    # Consultar en SUNAT
    empresa = await helper.get_empresa_by_ruc(ruc)
    
    if not empresa:
        return (False, None)
    
    # Verificar que está activa
    if empresa.estado == "ACTIVO":
        return (True, empresa.razon_social)
    else:
        return (False, empresa.razon_social)


# ============== Ejemplo 4: Desde un Caso de Uso ==============

async def ejemplo_desde_caso_uso():
    """
    Integración en un caso de uso existente
    Ejemplo: CreateClienteUseCase
    """
    from application.use_cases.government_queries import create_government_queries_use_case
    
    # Crear caso de uso con dependencias
    government_use_case = create_government_queries_use_case(
        cache_service=None,  # Inyectar tu servicio de caché
        audit_service=None   # Inyectar tu servicio de auditoría
    )
    
    # Consultar con respuesta completa
    dni_result = await government_use_case.query_dni(
        dni="12345678",
        user_id="user_123",
        use_cache=True
    )
    
    if dni_result.success:
        print(f"✅ Consulta exitosa")
        print(f"Fuente: {dni_result.fuente}")
        print(f"Caché: {dni_result.cache_hit}")
        print(f"Nombre: {dni_result.data.nombre_completo}")
    else:
        print(f"❌ Error: {dni_result.message}")


# ============== Ejemplo 5: Factory Pattern Directo ==============

async def ejemplo_factory_pattern():
    """Uso directo del Factory Pattern"""
    from infrastructure.services.government_apis import (
        GovernmentAPIFactory,
        APIProvider
    )
    
    # Crear servicio dinámicamente
    factory = GovernmentAPIFactory()
    
    # Obtener servicio de RENIEC
    reniec_service = factory.create_service(APIProvider.RENIEC)
    result = await reniec_service.query_document("12345678")
    
    if result.success:
        print(f"Persona: {result.data.nombre_completo}")
    
    # Obtener servicio de SUNAT
    sunat_service = factory.create_service(APIProvider.SUNAT)
    result = await sunat_service.query_document("20123456789")
    
    if result.success:
        print(f"Empresa: {result.data.razon_social}")


# ============== Ejemplo 6: Consultas en Batch ==============

async def ejemplo_consultas_batch():
    """Consultar múltiples documentos"""
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Consultar múltiples DNIs
    dnis = ["12345678", "87654321", "11111111"]
    resultados_dni = await helper.query_multiple_dni(dnis, user_id="admin")
    
    for dni, persona in resultados_dni.items():
        if persona:
            print(f"✅ {dni}: {persona.nombre_completo}")
        else:
            print(f"❌ {dni}: No encontrado")
    
    # Consultar múltiples RUCs
    rucs = ["20123456789", "20987654321"]
    resultados_ruc = await helper.query_multiple_ruc(rucs)
    
    for ruc, empresa in resultados_ruc.items():
        if empresa:
            print(f"✅ {ruc}: {empresa.razon_social}")
        else:
            print(f"❌ {ruc}: No encontrado")


# ============== Ejemplo 7: En un Endpoint Personalizado ==============

async def ejemplo_endpoint_custom():
    """
    Ejemplo de cómo usar en un endpoint personalizado
    """
    from fastapi import APIRouter, Depends
    from infrastructure.services.government_helper import get_government_helper
    from domain.entities.auth_models import User
    from infrastructure.web.fastapi.auth_dependencies import get_current_user
    
    router = APIRouter()
    
    @router.post("/clientes/validar-dni")
    async def validar_dni_cliente(
        dni: str,
        current_user: User = Depends(get_current_user)
    ):
        """Validar DNI de un cliente antes de registrarlo"""
        helper = get_government_helper()
        
        # Consultar
        persona = await helper.get_persona_by_dni(dni, current_user.clerk_id)
        
        if not persona:
            return {
                "valid": False,
                "message": "DNI no encontrado en RENIEC"
            }
        
        return {
            "valid": True,
            "message": "DNI válido",
            "data": {
                "nombre_completo": persona.nombre_completo,
                "dni": persona.dni
            }
        }


# ============== Ejemplo 8: Validación en Model/Entity ==============

from pydantic import BaseModel, field_validator

class ClienteCreate(BaseModel):
    """Modelo para crear cliente con validación de DNI"""
    nombre: str
    dni: str
    email: str
    
    @field_validator('dni')
    @classmethod
    def validate_dni_format(cls, v):
        """Validar formato de DNI"""
        from infrastructure.services.government_helper import GovernmentAPIHelper
        
        if not GovernmentAPIHelper.validate_dni(v):
            raise ValueError('DNI debe tener 8 dígitos numéricos')
        
        return v


async def crear_cliente_con_validacion(cliente_data: ClienteCreate, user_id: str):
    """Crear cliente validando DNI en RENIEC"""
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Consultar RENIEC
    persona = await helper.get_persona_by_dni(cliente_data.dni, user_id)
    
    if not persona:
        raise ValueError(f"DNI {cliente_data.dni} no encontrado en RENIEC")
    
    # Verificar que el nombre coincida
    if persona.nombre_completo.lower() != cliente_data.nombre.lower():
        print("⚠️ Advertencia: El nombre no coincide con RENIEC")
    
    # Crear cliente...
    print(f"✅ Cliente creado: {persona.nombre_completo}")


# ============== Ejemplo 9: Health Check ==============

async def ejemplo_health_check():
    """Verificar estado de los servicios"""
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Health check completo
    health = await helper.health_check()
    
    print("Estado de servicios:")
    print(f"Total: {health['total_services']}")
    
    for provider, status in health['services'].items():
        if status['disponible']:
            print(f"✅ {provider}: OK")
        else:
            print(f"❌ {provider}: {status.get('error', 'No disponible')}")


# ============== Ejemplo 10: Función de Utilidad ==============

async def obtener_nombre_razon_social(documento: str, user_id: str) -> Optional[str]:
    """
    Función de utilidad: obtener nombre o razón social según tipo de documento
    
    Args:
        documento: DNI (8 dígitos) o RUC (11 dígitos)
        user_id: ID del usuario
        
    Returns:
        Nombre completo o razón social
    """
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    # Determinar tipo de documento
    if len(documento) == 8:
        return await helper.get_nombre_completo(documento, user_id)
    elif len(documento) == 11:
        return await helper.get_razon_social(documento, user_id)
    else:
        return None


# ============== Ejemplo 11: Quick Functions ==============

async def ejemplo_quick_functions():
    """Usar funciones de atajo"""
    from infrastructure.services.government_helper import (
        quick_query_dni,
        quick_query_ruc
    )
    
    # Forma más rápida de consultar
    persona = await quick_query_dni("12345678")
    empresa = await quick_query_ruc("20123456789")
    
    if persona:
        print(f"Persona: {persona.nombre_completo}")
    
    if empresa:
        print(f"Empresa: {empresa.razon_social}")


# ============== Ejemplo 12: Manejo de Errores ==============

async def ejemplo_manejo_errores():
    """Manejo robusto de errores"""
    from infrastructure.services.government_apis import (
        DocumentValidationException,
        APIUnavailableException
    )
    from infrastructure.services.government_helper import get_government_helper
    
    helper = get_government_helper()
    
    try:
        persona = await helper.get_persona_by_dni("12345678")
        
        if persona:
            print(f"✅ Encontrado: {persona.nombre_completo}")
        else:
            print("❌ No encontrado")
            
    except DocumentValidationException as e:
        print(f"❌ Validación: {str(e)}")
    except APIUnavailableException as e:
        print(f"❌ Servicio no disponible: {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


# ============== Main para pruebas ==============

async def main():
    """Ejecutar ejemplos"""
    print("=" * 60)
    print("EJEMPLOS DE USO - APIs Gubernamentales")
    print("=" * 60)
    
    # Ejecutar ejemplos
    await ejemplo_uso_basico()
    # await ejemplo_factory_pattern()
    # await ejemplo_health_check()
    
    print("\n✅ Ejemplos completados")


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(main())
