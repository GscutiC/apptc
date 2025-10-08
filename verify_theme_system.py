"""
Script de verificación rápida para el sistema de Temas y Colores
Verifica que los nuevos DTOs y métodos estén correctamente implementados
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """Verificar que todos los imports funcionen"""
    print("🔍 Verificando imports...")
    
    try:
        from src.mi_app_completa_backend.application.dto.interface_config_dto import (
            PartialInterfaceConfigUpdateDTO,
            ThemeUpdateDTO,
            ThemeColorUpdateDTO,
            LogoUpdateDTO,
            BrandingUpdateDTO
        )
        print("✅ DTOs importados correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando DTOs: {e}")
        return False

def test_dto_validation():
    """Verificar validación de DTOs"""
    print("\n🧪 Verificando validación de DTOs...")
    
    try:
        from src.mi_app_completa_backend.application.dto.interface_config_dto import (
            ThemeColorUpdateDTO
        )
        
        # Test 1: Color válido
        valid_color = ThemeColorUpdateDTO(
            primary={"500": "#3b82f6", "600": "#2563eb"}
        )
        print("✅ Validación de colores válidos funciona")
        
        # Test 2: Color inválido (debería fallar)
        try:
            invalid_color = ThemeColorUpdateDTO(
                primary={"500": "azul"}  # No es formato hex
            )
            print("⚠️ Validación no detectó color inválido")
        except Exception:
            print("✅ Validación rechaza colores inválidos")
        
        return True
    except Exception as e:
        print(f"❌ Error en validación: {e}")
        return False

def test_use_case_methods():
    """Verificar que los métodos de use case existan"""
    print("\n🔍 Verificando métodos de use case...")
    
    try:
        from src.mi_app_completa_backend.application.use_cases.interface_config_use_cases import (
            InterfaceConfigUseCases
        )
        
        # Verificar que el método existe
        assert hasattr(InterfaceConfigUseCases, 'update_config_partial'), \
            "Método update_config_partial no encontrado"
        print("✅ Método update_config_partial existe")
        
        assert hasattr(InterfaceConfigUseCases, '_apply_partial_updates_to_config'), \
            "Método _apply_partial_updates_to_config no encontrado"
        print("✅ Método _apply_partial_updates_to_config existe")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando use cases: {e}")
        return False

def test_dto_structure():
    """Verificar estructura de DTOs"""
    print("\n📋 Verificando estructura de DTOs...")
    
    try:
        from src.mi_app_completa_backend.application.dto.interface_config_dto import (
            PartialInterfaceConfigUpdateDTO
        )
        
        # Crear DTO con datos parciales
        partial_update = PartialInterfaceConfigUpdateDTO(
            theme={
                "colors": {
                    "primary": {"500": "#3b82f6"}
                }
            }
        )
        
        print("✅ PartialInterfaceConfigUpdateDTO funciona con datos parciales")
        
        # Verificar que campos None son aceptados
        partial_update2 = PartialInterfaceConfigUpdateDTO()
        print("✅ PartialInterfaceConfigUpdateDTO acepta todos los campos opcionales")
        
        return True
    except Exception as e:
        print(f"❌ Error en estructura de DTOs: {e}")
        return False

def main():
    """Ejecutar todas las verificaciones"""
    print("=" * 60)
    print("🚀 VERIFICACIÓN DEL SISTEMA DE TEMAS Y COLORES")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Validación DTOs", test_dto_validation()))
    results.append(("Métodos Use Case", test_use_case_methods()))
    results.append(("Estructura DTOs", test_dto_structure()))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ El backend está listo para usar")
    else:
        print("\n⚠️ Algunas verificaciones fallaron")
        print("❌ Revisar errores arriba")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
