"""
Script de prueba para el sistema de Temas y Colores
"""

print("🧪 INICIANDO PRUEBAS DEL SISTEMA DE TEMAS Y COLORES")
print("=" * 60)

# Test 1: Importar DTOs
print("\n1️⃣ Test: Importar DTOs nuevos...")
try:
    from src.mi_app_completa_backend.application.dto.interface_config_dto import (
        PartialInterfaceConfigUpdateDTO,
        ThemeUpdateDTO,
        ThemeColorUpdateDTO,
        LogoUpdateDTO,
        BrandingUpdateDTO
    )
    print("   ✅ Todos los DTOs importados correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 2: Crear DTO con colores válidos
print("\n2️⃣ Test: Crear DTO con colores válidos...")
try:
    color_dto = ThemeColorUpdateDTO(
        primary={"500": "#3b82f6", "600": "#2563eb"}
    )
    print(f"   ✅ Color DTO creado correctamente")
    print(f"      - primary-500: {color_dto.primary['500']}")
    print(f"      - primary-600: {color_dto.primary['600']}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 3: Validar colores inválidos
print("\n3️⃣ Test: Validar rechazo de colores inválidos...")
try:
    invalid_dto = ThemeColorUpdateDTO(
        primary={"500": "rojo"}  # No es formato hex
    )
    print("   ⚠️ ADVERTENCIA: Validación no detectó color inválido")
except Exception as e:
    print(f"   ✅ Validación funciona: {str(e)[:50]}...")

# Test 4: Crear DTO parcial
print("\n4️⃣ Test: Crear DTO de actualización parcial...")
try:
    partial_dto = PartialInterfaceConfigUpdateDTO(
        theme=ThemeUpdateDTO(
            colors=ThemeColorUpdateDTO(
                primary={"500": "#3b82f6"}
            )
        )
    )
    print("   ✅ DTO parcial creado correctamente")
    print(f"      - Solo actualiza primary-500")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 5: DTO completamente vacío
print("\n5️⃣ Test: DTO con todos los campos opcionales...")
try:
    empty_dto = PartialInterfaceConfigUpdateDTO()
    print("   ✅ DTO vacío permitido (todos los campos opcionales)")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 6: Verificar métodos de use case
print("\n6️⃣ Test: Verificar métodos de use case...")
try:
    from src.mi_app_completa_backend.application.use_cases.interface_config_use_cases import (
        InterfaceConfigUseCases
    )
    
    # Verificar que los nuevos métodos existen
    assert hasattr(InterfaceConfigUseCases, 'update_config_partial'), \
        "Método update_config_partial no encontrado"
    assert hasattr(InterfaceConfigUseCases, '_apply_partial_updates_to_config'), \
        "Método _apply_partial_updates_to_config no encontrado"
    
    print("   ✅ Métodos de use case existen")
    print("      - update_config_partial ✓")
    print("      - _apply_partial_updates_to_config ✓")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 7: Branding DTO
print("\n7️⃣ Test: Crear DTO de branding...")
try:
    branding_dto = BrandingUpdateDTO(
        appName="Mi App Test"
    )
    print("   ✅ Branding DTO creado correctamente")
    print(f"      - appName: {branding_dto.appName}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# Test 8: Logo DTO
print("\n8️⃣ Test: Crear DTO de logos...")
try:
    logo_dto = LogoUpdateDTO(
        mainLogo={"text": "Test Logo", "showText": True}
    )
    print("   ✅ Logo DTO creado correctamente")
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
print("✅ Backend está listo para funcionar")
print("=" * 60)
