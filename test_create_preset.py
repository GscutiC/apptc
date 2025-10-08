"""
Script de prueba para endpoint POST /api/interface-config/presets
Prueba la creación de presets personalizados
"""

import sys
import os

# Agregar el path del backend al PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import httpx
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000/api/interface-config"
# TODO: Reemplazar con un token JWT real de Clerk
JWT_TOKEN = "REEMPLAZAR_CON_TOKEN_REAL"

async def test_create_preset():
    """Probar creación de preset personalizado"""
    
    preset_data = {
        "name": f"Test Preset {datetime.now().strftime('%H:%M:%S')}",
        "description": "Preset de prueba creado desde script de testing",
        "isDefault": False,
        "isSystem": False,
        "config": {
            "appName": "AppTC Test",
            "theme": {
                "name": "Tema de Prueba",
                "mode": "light",
                "colors": {
                    "primary": {
                        "50": "#eff6ff",
                        "100": "#dbeafe",
                        "200": "#bfdbfe",
                        "300": "#93c5fd",
                        "400": "#60a5fa",
                        "500": "#3b82f6",
                        "600": "#2563eb",
                        "700": "#1d4ed8",
                        "800": "#1e40af",
                        "900": "#1e3a8a"
                    },
                    "secondary": {
                        "50": "#f0fdf4",
                        "100": "#dcfce7",
                        "200": "#bbf7d0",
                        "300": "#86efac",
                        "400": "#4ade80",
                        "500": "#22c55e",
                        "600": "#16a34a",
                        "700": "#15803d",
                        "800": "#166534",
                        "900": "#14532d"
                    },
                    "accent": {
                        "50": "#fefce8",
                        "100": "#fef9c3",
                        "200": "#fef08a",
                        "300": "#fde047",
                        "400": "#facc15",
                        "500": "#eab308",
                        "600": "#ca8a04",
                        "700": "#a16207",
                        "800": "#854d0e",
                        "900": "#713f12"
                    },
                    "neutral": {
                        "50": "#f9fafb",
                        "100": "#f3f4f6",
                        "200": "#e5e7eb",
                        "300": "#d1d5db",
                        "400": "#9ca3af",
                        "500": "#6b7280",
                        "600": "#4b5563",
                        "700": "#374151",
                        "800": "#1f2937",
                        "900": "#111827"
                    }
                },
                "typography": {
                    "fontFamily": "Inter, system-ui, sans-serif",
                    "fontSize": {
                        "xs": "0.75rem",
                        "sm": "0.875rem",
                        "base": "1rem",
                        "lg": "1.125rem",
                        "xl": "1.25rem"
                    }
                },
                "layout": {
                    "containerWidth": "1200px",
                    "borderRadius": "8px",
                    "spacing": "16px"
                }
            },
            "logos": {
                "mainLogo": {
                    "url": "",
                    "text": "AppTC",
                    "position": "left",
                    "size": "medium"
                },
                "mobileLogo": {
                    "url": "",
                    "text": "ATC",
                    "position": "center",
                    "size": "small"
                },
                "favicon": {
                    "url": "",
                    "fallbackColor": "#3b82f6"
                }
            },
            "branding": {
                "appName": "AppTC Test",
                "tagline": "Preset de prueba",
                "companyName": "Test Company",
                "copyrightText": "© 2025 Test Company"
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("🧪 TEST: Crear Preset Personalizado")
    print("=" * 60)
    print(f"📡 URL: {API_BASE_URL}/presets")
    print(f"📝 Nombre: {preset_data['name']}")
    print(f"📄 Descripción: {preset_data['description']}")
    print("")
    
    try:
        async with httpx.AsyncClient() as client:
            print("📤 Enviando petición POST...")
            response = await client.post(
                f"{API_BASE_URL}/presets",
                json=preset_data,
                headers=headers,
                timeout=30.0
            )
            
            print(f"📥 Status Code: {response.status_code}")
            print("")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ SUCCESS: Preset creado exitosamente!")
                print("")
                print("📋 Datos del preset:")
                print(f"  • ID: {result.get('id')}")
                print(f"  • Nombre: {result.get('name')}")
                print(f"  • Descripción: {result.get('description')}")
                print(f"  • Es del sistema: {result.get('isSystem')}")
                print(f"  • Es por defecto: {result.get('isDefault')}")
                print(f"  • Creado por: {result.get('createdBy')}")
                print(f"  • Fecha: {result.get('createdAt')}")
                return True
            elif response.status_code == 403:
                print("❌ ERROR: Permisos insuficientes")
                print("   Se requiere rol de administrador para crear presets")
                print("")
                print("Response:", response.json())
                return False
            elif response.status_code == 400:
                print("❌ ERROR: Datos inválidos")
                print("")
                print("Response:", response.json())
                return False
            else:
                print(f"❌ ERROR: {response.status_code}")
                print("")
                print("Response:", response.text)
                return False
                
    except httpx.ConnectError:
        print("❌ ERROR: No se pudo conectar al servidor")
        print("   Verifica que el backend esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ ERROR inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_list_presets():
    """Probar listado de presets"""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("")
    print("=" * 60)
    print("🧪 TEST: Listar Presets")
    print("=" * 60)
    print(f"📡 URL: {API_BASE_URL}/presets")
    print("")
    
    try:
        async with httpx.AsyncClient() as client:
            print("📤 Enviando petición GET...")
            response = await client.get(
                f"{API_BASE_URL}/presets",
                headers=headers,
                timeout=30.0
            )
            
            print(f"📥 Status Code: {response.status_code}")
            print("")
            
            if response.status_code == 200:
                presets = response.json()
                print(f"✅ SUCCESS: {len(presets)} presets encontrados")
                print("")
                
                for i, preset in enumerate(presets, 1):
                    print(f"{i}. {preset.get('name')}")
                    print(f"   • ID: {preset.get('id')}")
                    print(f"   • Sistema: {'Sí' if preset.get('isSystem') else 'No'}")
                    print(f"   • Descripción: {preset.get('description')}")
                    print("")
                
                return True
            else:
                print(f"❌ ERROR: {response.status_code}")
                print("")
                print("Response:", response.text)
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

async def main():
    """Ejecutar todas las pruebas"""
    
    print("\n" + "=" * 60)
    print("🚀 INICIANDO TESTS DE PRESETS")
    print("=" * 60)
    print("")
    
    # Verificar token
    if JWT_TOKEN == "REEMPLAZAR_CON_TOKEN_REAL":
        print("⚠️ ADVERTENCIA: Debes reemplazar el JWT_TOKEN en el script")
        print("   Para obtener un token:")
        print("   1. Abre la consola del navegador en tu app")
        print("   2. Ejecuta: await window.Clerk.session.getToken()")
        print("   3. Copia el token y reemplázalo en este script")
        print("")
        print("❌ Tests abortados")
        return
    
    # Test 1: Listar presets existentes
    await test_list_presets()
    
    # Test 2: Crear nuevo preset
    success = await test_create_preset()
    
    # Test 3: Listar presets nuevamente para ver el nuevo
    if success:
        print("")
        print("🔄 Listando presets después de crear uno nuevo...")
        await asyncio.sleep(1)  # Esperar un segundo
        await test_list_presets()
    
    print("")
    print("=" * 60)
    print("✅ TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
