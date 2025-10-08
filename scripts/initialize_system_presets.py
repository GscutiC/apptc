"""
Script para inicializar los presets del sistema en MongoDB

Este script crea los 3 presets base del sistema:
1. Elegante Azul (Por defecto) - Tema profesional azul-morado
2. Oscuro Elegante - Versión oscura del tema elegante
3. Verde Corporativo (Actual) - Tema verde profesional

Uso:
    python scripts/initialize_system_presets.py
    
Características:
- Solo crea presets si no existen (evita duplicados)
- Marca "Elegante Azul" como preset por defecto
- Todos los presets tienen isSystem=true (no se pueden eliminar)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / 'src'))

from motor.motor_asyncio import AsyncIOMotorClient


# ============================================================================
# CONFIGURACIÓN DE CONEXIÓN
# ============================================================================

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "mi_app_completa_db"
PRESETS_COLLECTION = "preset_configurations"


# ============================================================================
# DEFINICIÓN DE PRESETS DEL SISTEMA
# ============================================================================

SYSTEM_PRESETS = [
    {
        "id": "default-elegant-blue",
        "name": "Elegante Azul (Por defecto)",
        "description": "Tema elegante con gradientes azul-morado, perfecto para aplicaciones profesionales",
        "isDefault": True,
        "isSystem": True,
        "theme": {
            "mode": "light",
            "name": "Tema Corporativo",
            "colors": {
                "primary": {
                    "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe", "300": "#93c5fd",
                    "400": "#60a5fa", "500": "#3b82f6", "600": "#2563eb", "700": "#1d4ed8",
                    "800": "#1e40af", "900": "#1e3a8a"
                },
                "secondary": {
                    "50": "#faf5ff", "100": "#f3e8ff", "200": "#e9d5ff", "300": "#d8b4fe",
                    "400": "#c084fc", "500": "#a855f7", "600": "#9333ea", "700": "#7c3aed",
                    "800": "#6b21a8", "900": "#581c87"
                },
                "accent": {
                    "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0", "300": "#6ee7b7",
                    "400": "#34d399", "500": "#10b981", "600": "#059669", "700": "#047857",
                    "800": "#065f46", "900": "#064e3b"
                },
                "neutral": {
                    "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb", "300": "#d1d5db",
                    "400": "#9ca3af", "500": "#6b7280", "600": "#4b5563", "700": "#374151",
                    "800": "#1f2937", "900": "#111827"
                }
            },
            "typography": {
                "fontFamily": {
                    "primary": "-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif",
                    "secondary": "Georgia, serif",
                    "mono": "monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                    "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
                    "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem"
                },
                "fontWeight": {
                    "light": 300, "normal": 400, "medium": 500,
                    "semibold": 600, "bold": 700
                }
            },
            "layout": {
                "borderRadius": {
                    "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                    "lg": "0.5rem", "xl": "0.75rem", "2xl": "1rem", "full": "9999px"
                },
                "spacing": {
                    "xs": "0.5rem", "sm": "0.75rem", "base": "1rem",
                    "md": "1.5rem", "lg": "2rem", "xl": "3rem", "2xl": "4rem"
                },
                "shadows": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "base": "0 1px 3px 0 rgb(0 0 0 / 0.1)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)",
                    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
                }
            }
        },
        "logos": {
            "mainLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False
            },
            "favicon": {},
            "sidebarLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False,
                "collapsedText": "MA"
            }
        },
        "branding": {
            "appName": "Mi Aplicación",
            "appDescription": "Sistema de gestión profesional",
            "tagline": "Gestión eficiente y moderna",
            "companyName": "Tu Empresa",
            "welcomeMessage": "Bienvenido a Mi Aplicación",
            "loginPageTitle": "Bienvenido",
            "loginPageDescription": "Inicia sesión para acceder al sistema"
        },
        "customCSS": "",
        "isActive": False
    },
    {
        "id": "dark-elegant",
        "name": "Oscuro Elegante",
        "description": "Versión oscura del tema elegante, ideal para uso prolongado",
        "isDefault": False,
        "isSystem": True,
        "theme": {
            "mode": "dark",
            "name": "Tema Oscuro Elegante",
            "colors": {
                "primary": {
                    "50": "#1e3a8a", "100": "#1e40af", "200": "#1d4ed8", "300": "#2563eb",
                    "400": "#3b82f6", "500": "#60a5fa", "600": "#93c5fd", "700": "#bfdbfe",
                    "800": "#dbeafe", "900": "#eff6ff"
                },
                "secondary": {
                    "50": "#581c87", "100": "#6b21a8", "200": "#7c3aed", "300": "#9333ea",
                    "400": "#a855f7", "500": "#c084fc", "600": "#d8b4fe", "700": "#e9d5ff",
                    "800": "#f3e8ff", "900": "#faf5ff"
                },
                "accent": {
                    "50": "#064e3b", "100": "#065f46", "200": "#047857", "300": "#059669",
                    "400": "#10b981", "500": "#34d399", "600": "#6ee7b7", "700": "#a7f3d0",
                    "800": "#d1fae5", "900": "#ecfdf5"
                },
                "neutral": {
                    "50": "#111827", "100": "#1f2937", "200": "#374151", "300": "#4b5563",
                    "400": "#6b7280", "500": "#9ca3af", "600": "#d1d5db", "700": "#e5e7eb",
                    "800": "#f3f4f6", "900": "#f9fafb"
                }
            },
            "typography": {
                "fontFamily": {
                    "primary": "-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif",
                    "secondary": "Georgia, serif",
                    "mono": "monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                    "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
                    "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem"
                },
                "fontWeight": {
                    "light": 300, "normal": 400, "medium": 500,
                    "semibold": 600, "bold": 700
                }
            },
            "layout": {
                "borderRadius": {
                    "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                    "lg": "0.5rem", "xl": "0.75rem", "2xl": "1rem", "full": "9999px"
                },
                "spacing": {
                    "xs": "0.5rem", "sm": "0.75rem", "base": "1rem",
                    "md": "1.5rem", "lg": "2rem", "xl": "3rem", "2xl": "4rem"
                },
                "shadows": {
                    "sm": "0 2px 4px 0 rgb(0 0 0 / 0.2)",
                    "base": "0 4px 6px 0 rgb(0 0 0 / 0.3)",
                    "md": "0 8px 12px -2px rgb(0 0 0 / 0.3)",
                    "lg": "0 16px 24px -4px rgb(0 0 0 / 0.3)",
                    "xl": "0 24px 32px -6px rgb(0 0 0 / 0.3)",
                    "2xl": "0 32px 48px -12px rgb(0 0 0 / 0.4)"
                }
            }
        },
        "logos": {
            "mainLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False
            },
            "favicon": {},
            "sidebarLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False,
                "collapsedText": "MA"
            }
        },
        "branding": {
            "appName": "Mi Aplicación",
            "appDescription": "Sistema de gestión profesional",
            "tagline": "Modo oscuro para mayor comodidad",
            "companyName": "Tu Empresa",
            "welcomeMessage": "Bienvenido a Mi Aplicación",
            "loginPageTitle": "Bienvenido",
            "loginPageDescription": "Inicia sesión para acceder al sistema"
        },
        "customCSS": "",
        "isActive": False
    },
    {
        "id": "green-corporate",
        "name": "Verde Corporativo (Actual)",
        "description": "Tema verde profesional del archivo de configuración actual",
        "isDefault": False,
        "isSystem": True,
        "theme": {
            "mode": "light",
            "name": "Tema Verde Corporativo",
            "colors": {
                "primary": {
                    "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0", "300": "#6ee7b7",
                    "400": "#34d399", "500": "#10b981", "600": "#059669", "700": "#047857",
                    "800": "#065f46", "900": "#064e3b"
                },
                "secondary": {
                    "50": "#f0fdf4", "100": "#dcfce7", "200": "#bbf7d0", "300": "#86efac",
                    "400": "#4ade80", "500": "#22c55e", "600": "#16a34a", "700": "#15803d",
                    "800": "#166534", "900": "#14532d"
                },
                "accent": {
                    "50": "#fef3c7", "100": "#fde68a", "200": "#fcd34d", "300": "#fbbf24",
                    "400": "#f59e0b", "500": "#d97706", "600": "#b45309", "700": "#92400e",
                    "800": "#78350f", "900": "#451a03"
                },
                "neutral": {
                    "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb", "300": "#d1d5db",
                    "400": "#9ca3af", "500": "#6b7280", "600": "#4b5563", "700": "#374151",
                    "800": "#1f2937", "900": "#111827"
                }
            },
            "typography": {
                "fontFamily": {
                    "primary": "-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif",
                    "secondary": "Georgia, serif",
                    "mono": "monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                    "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem",
                    "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem"
                },
                "fontWeight": {
                    "light": 300, "normal": 400, "medium": 500,
                    "semibold": 600, "bold": 700
                }
            },
            "layout": {
                "borderRadius": {
                    "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                    "lg": "0.5rem", "xl": "0.75rem", "2xl": "1rem", "full": "9999px"
                },
                "spacing": {
                    "xs": "0.5rem", "sm": "0.75rem", "base": "1rem",
                    "md": "1.5rem", "lg": "2rem", "xl": "3rem", "2xl": "4rem"
                },
                "shadows": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "base": "0 1px 3px 0 rgb(0 0 0 / 0.1)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
                    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1)",
                    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
                }
            }
        },
        "logos": {
            "mainLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False
            },
            "favicon": {},
            "sidebarLogo": {
                "text": "MiApp",
                "showText": True,
                "showImage": False,
                "collapsedText": "MA"
            }
        },
        "branding": {
            "appName": "Mi Aplicación",
            "appDescription": "Sistema de gestión profesional",
            "tagline": "Profesional y moderno",
            "companyName": "Tu Empresa",
            "welcomeMessage": "Bienvenido a Mi Aplicación",
            "loginPageTitle": "Bienvenido",
            "loginPageDescription": "Inicia sesión para acceder al sistema"
        },
        "customCSS": "",
        "isActive": False
    }
]


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def print_header(text: str):
    """Imprimir header decorado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_step(step: int, text: str):
    """Imprimir paso numerado"""
    print(f"\n[{step}] {text}")


def print_success(text: str):
    """Imprimir mensaje de éxito"""
    print(f"  ✓ {text}")


def print_info(text: str):
    """Imprimir información"""
    print(f"  ℹ {text}")


def print_warning(text: str):
    """Imprimir advertencia"""
    print(f"  ⚠ {text}")


def print_error(text: str):
    """Imprimir error"""
    print(f"  ✗ {text}")


# ============================================================================
# LÓGICA PRINCIPAL
# ============================================================================

async def initialize_system_presets(force: bool = False) -> bool:
    """
    Inicializar presets del sistema en MongoDB
    
    Args:
        force: Si True, elimina presets del sistema existentes y los recrea
    
    Returns:
        bool: True si la inicialización fue exitosa
    """
    
    print_header("INICIALIZACIÓN DE PRESETS DEL SISTEMA")
    
    try:
        # Conectar a MongoDB
        print_step(1, "Conectando a MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        collection = db[PRESETS_COLLECTION]
        print_success(f"Conectado a {DATABASE_NAME}")
        
        # Verificar presets existentes
        print_step(2, "Verificando presets existentes...")
        existing_system = await collection.count_documents({"isSystem": True})
        existing_total = await collection.count_documents({})
        
        print_info(f"Presets del sistema existentes: {existing_system}")
        print_info(f"Presets totales: {existing_total}")
        
        # Si hay presets del sistema y no es forzado, preguntar
        if existing_system > 0 and not force:
            print_warning("Ya existen presets del sistema en la base de datos")
            print_info("Usa el parámetro --force para recrearlos")
            return False
        
        # Eliminar presets del sistema si es forzado
        if force and existing_system > 0:
            print_step(3, "Eliminando presets del sistema existentes (--force)...")
            result = await collection.delete_many({"isSystem": True})
            print_success(f"Eliminados {result.deleted_count} presets del sistema")
        
        # Crear presets del sistema
        print_step(4, "Creando presets del sistema...")
        
        now = datetime.utcnow()
        created_count = 0
        
        for preset_data in SYSTEM_PRESETS:
            # Agregar timestamps
            preset_doc = {
                **preset_data,
                "createdAt": now,
                "updatedAt": now,
                "createdBy": "system"
            }
            
            # Insertar preset
            try:
                await collection.insert_one(preset_doc)
                print_success(f"Creado: {preset_data['name']}")
                created_count += 1
            except Exception as e:
                print_error(f"Error creando {preset_data['name']}: {e}")
        
        # Verificar resultado
        print_step(5, "Verificando resultado...")
        final_count = await collection.count_documents({"isSystem": True})
        default_count = await collection.count_documents({"isDefault": True, "isSystem": True})
        
        print_info(f"Presets del sistema creados: {created_count}")
        print_info(f"Presets del sistema en DB: {final_count}")
        print_info(f"Presets por defecto: {default_count}")
        
        # Listar presets creados
        print_step(6, "Presets del sistema disponibles:")
        async for preset in collection.find({"isSystem": True}).sort("name", 1):
            name = preset.get("name", "N/A")
            is_default = preset.get("isDefault", False)
            preset_id = preset.get("id", "N/A")
            default_mark = " [DEFAULT]" if is_default else ""
            print_info(f"{name}{default_mark} (id: {preset_id})")
        
        print_header("INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        print_success(f"Se crearon {created_count} presets del sistema")
        print_success("Los presets están listos para usar en el frontend")
        
        client.close()
        return True
        
    except Exception as e:
        print_error(f"Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_presets():
    """Verificar presets en MongoDB sin crear nuevos"""
    print_header("VERIFICACIÓN DE PRESETS")
    
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        collection = db[PRESETS_COLLECTION]
        
        total = await collection.count_documents({})
        system = await collection.count_documents({"isSystem": True})
        custom = await collection.count_documents({"isSystem": False})
        default = await collection.count_documents({"isDefault": True})
        
        print_info(f"Total presets: {total}")
        print_info(f"Presets del sistema: {system}")
        print_info(f"Presets personalizados: {custom}")
        print_info(f"Presets por defecto: {default}")
        
        if system > 0:
            print("\n📋 Presets del Sistema:")
            async for preset in collection.find({"isSystem": True}).sort("name", 1):
                name = preset.get("name", "N/A")
                is_default = preset.get("isDefault", False)
                default_mark = " [DEFAULT]" if is_default else ""
                print(f"  • {name}{default_mark}")
        else:
            print_warning("No hay presets del sistema. Ejecuta el script sin --verify para crearlos")
        
        if custom > 0:
            print("\n👤 Presets Personalizados:")
            async for preset in collection.find({"isSystem": False}).sort("name", 1):
                name = preset.get("name", "N/A")
                print(f"  • {name}")
        
        client.close()
        
    except Exception as e:
        print_error(f"Error durante la verificación: {e}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Inicializar presets del sistema en MongoDB"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar recreación de presets del sistema existentes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Solo verificar presets existentes sin crear nuevos"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        await verify_presets()
    else:
        success = await initialize_system_presets(force=args.force)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
