#!/usr/bin/env python3
"""
Script de migración para transferir configuraciones de interfaz desde JSON a MongoDB
Incluye backup automático, validación, dry-run y rollback
"""

import asyncio
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

# Agregar el directorio src al path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

from mi_app_completa_backend.infrastructure.config.database import get_database
from mi_app_completa_backend.infrastructure.persistence.mongodb.interface_config_repository_impl import (
    MongoInterfaceConfigRepository,
    MongoPresetConfigRepository,
    MongoConfigHistoryRepository
)
from mi_app_completa_backend.domain.entities.interface_config import (
    InterfaceConfig,
    PresetConfig,
    ConfigHistory,
    ThemeConfig,
    ColorConfig,
    TypographyConfig,
    LayoutConfig,
    LogoConfig,
    BrandingConfig
)


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Rutas de archivos
CONFIG_FILE = Path(backend_dir) / "interface_config.json"
BACKUPS_DIR = Path(backend_dir) / "backups"
MIGRATED_SUFFIX = ".migrated"

# Presets del sistema predefinidos (del código de routes)
SYSTEM_PRESETS_DATA = [
    {
        "id": "default-elegant-blue",
        "name": "Elegante Azul (Por defecto)",
        "description": "Tema elegante con gradientes azul-morado, perfecto para aplicaciones profesionales",
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
                    "primary": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                    "secondary": "Georgia, Cambria, serif",
                    "mono": "'SF Mono', Monaco, 'Cascadia Code', monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
                    "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem"
                },
                "fontWeight": {
                    "light": 300, "normal": 400, "medium": 500, "semibold": 600, "bold": 700
                }
            },
            "layout": {
                "borderRadius": {
                    "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                    "lg": "0.5rem", "xl": "0.75rem", "2xl": "1rem"
                },
                "spacing": {
                    "xs": "0.5rem", "sm": "0.75rem", "base": "1rem",
                    "md": "1.5rem", "lg": "2rem", "xl": "3rem", "2xl": "4rem"
                },
                "shadows": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "base": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
                    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
                    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
                }
            }
        },
        "logos": {
            "mainLogo": {"text": "WorkTecApp", "showText": True, "showImage": False},
            "favicon": {},
            "sidebarLogo": {"text": "WorkTecApp", "showText": True, "showImage": False, "collapsedText": "WT"}
        },
        "branding": {
            "appName": "WorkTecApp",
            "appDescription": "Soluciones empresariales sostenibles",
            "tagline": "Soluciones empresariales sostenibles",
            "companyName": "WorkTec Solutions",
            "supportEmail": "support@worktec.com",
            "websiteUrl": "https://worktec.com",
            "welcomeMessage": "¡Bienvenido a WorkTecApp!",
            "loginPageTitle": "Iniciar Sesión",
            "loginPageDescription": "Accede a tu cuenta"
        },
        "isDefault": True,
        "isSystem": True
    },
    {
        "id": "dark-elegant",
        "name": "Oscuro Elegante",
        "description": "Versión oscura del tema elegante, ideal para uso prolongado",
        "theme": {
            "mode": "dark",
            "name": "Tema Oscuro Elegante",
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
                    "50": "#111827", "100": "#1f2937", "200": "#374151", "300": "#4b5563",
                    "400": "#6b7280", "500": "#9ca3af", "600": "#d1d5db", "700": "#e5e7eb",
                    "800": "#f3f4f6", "900": "#f9fafb"
                }
            },
            "typography": {
                "fontFamily": {
                    "primary": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                    "secondary": "Georgia, Cambria, serif",
                    "mono": "'SF Mono', Monaco, 'Cascadia Code', monospace"
                },
                "fontSize": {
                    "xs": "0.75rem", "sm": "0.875rem", "base": "1rem", "lg": "1.125rem",
                    "xl": "1.25rem", "2xl": "1.5rem", "3xl": "1.875rem", "4xl": "2.25rem", "5xl": "3rem"
                },
                "fontWeight": {
                    "light": 300, "normal": 400, "medium": 500, "semibold": 600, "bold": 700
                }
            },
            "layout": {
                "borderRadius": {
                    "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                    "lg": "0.5rem", "xl": "0.75rem", "2xl": "1rem"
                },
                "spacing": {
                    "xs": "0.5rem", "sm": "0.75rem", "base": "1rem",
                    "md": "1.5rem", "lg": "2rem", "xl": "3rem", "2xl": "4rem"
                },
                "shadows": {
                    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
                    "base": "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
                    "md": "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
                    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
                    "xl": "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
                    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)"
                }
            }
        },
        "logos": {
            "mainLogo": {"text": "WorkTecApp", "showText": True, "showImage": False},
            "favicon": {},
            "sidebarLogo": {"text": "WorkTecApp", "showText": True, "showImage": False, "collapsedText": "WT"}
        },
        "branding": {
            "appName": "WorkTecApp",
            "appDescription": "Soluciones empresariales sostenibles",
            "tagline": "Soluciones empresariales sostenibles",
            "companyName": "WorkTec Solutions",
            "supportEmail": "support@worktec.com",
            "websiteUrl": "https://worktec.com",
            "welcomeMessage": "¡Bienvenido a WorkTecApp!",
            "loginPageTitle": "Iniciar Sesión",
            "loginPageDescription": "Accede a tu cuenta"
        },
        "isDefault": False,
        "isSystem": True
    }
]


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def print_header(text: str):
    """Imprimir encabezado con formato"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_step(number: int, text: str):
    """Imprimir paso con número"""
    print(f"\n[Paso {number}] {text}")


def print_success(text: str, indent: int = 3):
    """Imprimir mensaje de éxito"""
    print(f"{' '*indent}[OK] {text}")


def print_error(text: str, indent: int = 3):
    """Imprimir mensaje de error"""
    print(f"{' '*indent}[ERROR] {text}")


def print_info(text: str, indent: int = 3):
    """Imprimir mensaje informativo"""
    print(f"{' '*indent}[INFO] {text}")


def create_backup(config_data: Dict[str, Any]) -> Path:
    """Crear backup del archivo de configuración"""
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    backup_file = BACKUPS_DIR / f"interface_config.backup.{timestamp}.json"

    # Crear directorio si no existe
    BACKUPS_DIR.mkdir(exist_ok=True)

    # Agregar metadata al backup
    backup_data = {
        "metadata": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "original_file": str(CONFIG_FILE),
            "migration_version": "1.0.0"
        },
        "data": config_data
    }

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)

    return backup_file


def validate_config_structure(config: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validar que la estructura del JSON sea correcta"""
    errors = []

    # Campos requeridos de primer nivel
    required_fields = ['theme', 'logos', 'branding']
    for field in required_fields:
        if field not in config:
            errors.append(f"Campo requerido faltante: {field}")

    # Validar estructura de theme
    if 'theme' in config:
        theme = config['theme']
        theme_required = ['mode', 'name', 'colors', 'typography', 'layout']
        for field in theme_required:
            if field not in theme:
                errors.append(f"Campo requerido faltante en theme: {field}")

        # Validar colores
        if 'colors' in theme:
            colors = theme['colors']
            color_palettes = ['primary', 'secondary', 'accent', 'neutral']
            for palette in color_palettes:
                if palette not in colors:
                    errors.append(f"Paleta de colores faltante: {palette}")

    # Validar logos
    if 'logos' in config:
        logos = config['logos']
        logo_fields = ['mainLogo', 'sidebarLogo']
        for field in logo_fields:
            if field not in logos:
                errors.append(f"Campo requerido faltante en logos: {field}")

    # Validar branding
    if 'branding' in config:
        branding = config['branding']
        branding_fields = ['appName', 'appDescription', 'welcomeMessage',
                          'loginPageTitle', 'loginPageDescription']
        for field in branding_fields:
            if field not in branding:
                errors.append(f"Campo requerido faltante en branding: {field}")

    return len(errors) == 0, errors


def parse_theme_from_json(theme_data: Dict[str, Any]) -> ThemeConfig:
    """Parsear tema desde JSON"""
    colors = ColorConfig(
        primary=theme_data['colors']['primary'],
        secondary=theme_data['colors']['secondary'],
        accent=theme_data['colors']['accent'],
        neutral=theme_data['colors']['neutral']
    )

    typography = TypographyConfig(
        font_family=theme_data['typography']['fontFamily'],
        font_size=theme_data['typography']['fontSize'],
        font_weight=theme_data['typography']['fontWeight']
    )

    layout = LayoutConfig(
        border_radius=theme_data['layout']['borderRadius'],
        spacing=theme_data.get('layout', {}).get('spacing', {}),
        shadows=theme_data.get('layout', {}).get('shadows', {})
    )

    return ThemeConfig(
        mode=theme_data.get('mode', 'light'),
        name=theme_data.get('name', 'Default Theme'),
        colors=colors,
        typography=typography,
        layout=layout
    )


def parse_config_from_json(config_data: Dict[str, Any]) -> InterfaceConfig:
    """Parsear configuración completa desde JSON"""
    theme = parse_theme_from_json(config_data['theme'])

    logos = LogoConfig(
        main_logo=config_data['logos'].get('mainLogo', {}),
        favicon=config_data['logos'].get('favicon', {}),
        sidebar_logo=config_data['logos'].get('sidebarLogo', {})
    )

    branding_data = config_data['branding']
    branding = BrandingConfig(
        app_name=branding_data.get('appName', 'App'),
        app_description=branding_data.get('appDescription', ''),
        welcome_message=branding_data.get('welcomeMessage', ''),
        login_page_title=branding_data.get('loginPageTitle', ''),
        login_page_description=branding_data.get('loginPageDescription', ''),
        tagline=branding_data.get('tagline'),
        company_name=branding_data.get('companyName')
    )

    return InterfaceConfig(
        theme=theme,
        logos=logos,
        branding=branding,
        is_active=config_data.get('isActive', True),
        custom_css=config_data.get('customization', {}).get('customCSS'),
        created_by='migration_script'
    )


# ============================================================================
# FUNCIÓN PRINCIPAL DE MIGRACIÓN
# ============================================================================

async def migrate_to_mongodb(dry_run: bool = False) -> bool:
    """
    Migrar configuraciones desde JSON a MongoDB

    Args:
        dry_run: Si es True, solo simula sin hacer cambios

    Returns:
        True si la migración fue exitosa, False si hubo errores
    """
    try:
        print_header("MIGRACION DE CONFIGURACIONES A MONGODB")

        if dry_run:
            print_info("MODO DRY-RUN: No se haran cambios reales", indent=0)

        # ====================================================================
        # PASO 1: Verificar archivos
        # ====================================================================
        print_step(1, "Verificando archivos...")

        if not CONFIG_FILE.exists():
            print_error(f"Archivo no encontrado: {CONFIG_FILE}")
            return False

        print_success(f"Encontrado: {CONFIG_FILE}")

        # ====================================================================
        # PASO 2: Leer y validar JSON
        # ====================================================================
        print_step(2, "Leyendo y validando configuración...")

        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        print_success("JSON parseado correctamente")

        # Validar estructura
        is_valid, errors = validate_config_structure(config_data)
        if not is_valid:
            print_error("Estructura de JSON inválida:")
            for error in errors:
                print_error(f"  - {error}")
            return False

        print_success("Estructura válida")
        print_success("Todos los campos requeridos presentes")

        # ====================================================================
        # PASO 3: Crear backup
        # ====================================================================
        print_step(3, "Creando backup...")

        if not dry_run:
            backup_file = create_backup(config_data)
            print_success(f"Backup creado: {backup_file}")
        else:
            print_info(f"[DRY-RUN] Se crearía backup en: {BACKUPS_DIR}")

        # ====================================================================
        # PASO 4: Conectar a MongoDB
        # ====================================================================
        print_step(4, "Conectando a MongoDB...")

        try:
            db = get_database()
            print_success(f"Conectado a MongoDB")
        except Exception as e:
            print_error(f"Error conectando a MongoDB: {e}")
            return False

        # ====================================================================
        # PASO 5: Inicializar repositorios
        # ====================================================================
        print_step(5, "Inicializando repositorios...")

        config_repo = MongoInterfaceConfigRepository(db)
        preset_repo = MongoPresetConfigRepository(db)
        history_repo = MongoConfigHistoryRepository(db)

        print_success("Repositorios inicializados")
        print_info(f"Colección configuraciones: interface_configurations")
        print_info(f"Colección presets: preset_configurations")
        print_info(f"Colección historial: configuration_history")

        # ====================================================================
        # PASO 6: Verificar si ya existe migración
        # ====================================================================
        print_step(6, "Verificando migración existente...")

        existing_config = await config_repo.get_current_config()
        if existing_config and not dry_run:
            print_info("Ya existe una configuración activa en MongoDB")
            print_info(f"Tema actual: {existing_config.theme.name}")
            print_info("Sobrescribiendo configuración existente...")

            # Desactivar configuración existente
            await config_repo.collection.update_many(
                {},
                {"$set": {"isActive": False}}
            )
            print_success("Configuración existente desactivada")
        elif existing_config:
            print_info("[DRY-RUN] Se encontró configuración existente")
        else:
            print_success("No se encontró configuración existente")

        # ====================================================================
        # PASO 7: Migrar configuración principal
        # ====================================================================
        print_step(7, "Migrando configuración principal...")

        # Parsear configuración
        interface_config = parse_config_from_json(config_data)

        if not dry_run:
            # Guardar en MongoDB
            saved_config = await config_repo.save_config(interface_config)
            print_success(f"Configuración guardada (ID: {saved_config.id})")
            print_success(f"Tema: {saved_config.theme.name}")
            print_success(f"App: {saved_config.branding.app_name}")
            print_success("Marcada como activa")
        else:
            print_info("[DRY-RUN] Se guardaría configuración:")
            print_info(f"  - Tema: {interface_config.theme.name}")
            print_info(f"  - App: {interface_config.branding.app_name}")
            print_info(f"  - Activa: {interface_config.is_active}")

        # ====================================================================
        # PASO 8: Crear presets del sistema
        # ====================================================================
        print_step(8, "Creando presets del sistema...")

        # Agregar preset del archivo actual si no está en los predefinidos
        current_theme_preset = {
            "id": "green-corporate",
            "name": "Verde Corporativo (Actual)",
            "description": "Tema verde profesional del archivo de configuración actual",
            "theme": config_data['theme'],
            "logos": config_data['logos'],
            "branding": config_data['branding'],
            "isDefault": False,
            "isSystem": True
        }

        all_presets = SYSTEM_PRESETS_DATA + [current_theme_preset]
        presets_created = 0

        for preset_data in all_presets:
            # Verificar si ya existe
            existing_preset = None
            if not dry_run:
                all_existing = await preset_repo.get_all_presets()
                existing_preset = next((p for p in all_existing if p.name == preset_data['name']), None)

            if existing_preset:
                print_info(f"Preset ya existe: {preset_data['name']}")
                continue

            # Crear configuración para el preset
            preset_theme = parse_theme_from_json(preset_data['theme'])
            preset_logos = LogoConfig(
                main_logo=preset_data['logos'].get('mainLogo', {}),
                favicon=preset_data['logos'].get('favicon', {}),
                sidebar_logo=preset_data['logos'].get('sidebarLogo', {})
            )
            preset_branding_data = preset_data['branding']
            preset_branding = BrandingConfig(
                app_name=preset_branding_data.get('appName', 'App'),
                app_description=preset_branding_data.get('appDescription', ''),
                welcome_message=preset_branding_data.get('welcomeMessage', ''),
                login_page_title=preset_branding_data.get('loginPageTitle', ''),
                login_page_description=preset_branding_data.get('loginPageDescription', ''),
                tagline=preset_branding_data.get('tagline'),
                company_name=preset_branding_data.get('companyName')
            )

            preset_config = InterfaceConfig(
                theme=preset_theme,
                logos=preset_logos,
                branding=preset_branding,
                is_active=False,
                created_by='migration_script'
            )

            preset = PresetConfig(
                name=preset_data['name'],
                description=preset_data['description'],
                config=preset_config,
                is_default=preset_data.get('isDefault', False),
                is_system=preset_data.get('isSystem', True),
                created_by='migration_script'
            )

            if not dry_run:
                await preset_repo.save_preset(preset)
                print_success(f"Preset creado: {preset.name}")
                presets_created += 1
            else:
                print_info(f"[DRY-RUN] Se crearía preset: {preset.name}")

        if not dry_run:
            print_success(f"Total de presets creados: {presets_created}")

        # ====================================================================
        # PASO 9: Crear entrada en historial
        # ====================================================================
        print_step(9, "Creando historial inicial...")

        if not dry_run:
            history_entry = ConfigHistory(
                config=interface_config,
                version=1,
                changed_by='migration_script',
                change_description='Migración inicial desde interface_config.json'
            )

            await history_repo.save_history_entry(history_entry)
            print_success("Entrada de historial creada (Versión 1)")
        else:
            print_info("[DRY-RUN] Se crearía entrada de historial (Versión 1)")

        # ====================================================================
        # PASO 10: Validar migración
        # ====================================================================
        print_step(10, "Validando migración...")

        if not dry_run:
            # Verificar configuración activa
            active_config = await config_repo.get_current_config()
            if active_config:
                print_success(f"Configuración activa: {active_config.theme.name}")
            else:
                print_error("No se encontró configuración activa")

            # Contar presets
            all_presets = await preset_repo.get_all_presets()
            print_success(f"Total de presets: {len(all_presets)}")

            # Contar historial
            history = await history_repo.get_history(limit=100)
            print_success(f"Total de historial: {len(history)}")
        else:
            print_info("[DRY-RUN] Validación omitida en modo dry-run")

        # ====================================================================
        # PASO 11: Archivo original
        # ====================================================================
        if not dry_run:
            print_step(11, "Archivo original...")
            print_info("Archivo original mantenido sin cambios")

        # ====================================================================
        # RESUMEN FINAL
        # ====================================================================
        print_header("MIGRACION COMPLETADA EXITOSAMENTE" if not dry_run else "SIMULACION COMPLETADA")

        print("\nResumen:")
        if not dry_run:
            print_success(f"Configuraciones migradas: 1")
            print_success(f"Presets creados: {presets_created}")
            print_success(f"Entradas de historial: 1")
            print_success(f"Backup guardado en: {backup_file}")
        else:
            print_info("Modo dry-run: No se realizaron cambios")
            print_info(f"Se migraria: 1 configuracion")
            print_info(f"Se crearian: {len(all_presets)} presets")
            print_info(f"Se crearia: 1 entrada de historial")

        if not dry_run:
            print("\nProximos pasos:")
            print_info("1. Verificar configuracion en MongoDB", indent=3)
            print_info("2. Actualizar rutas API para usar repositorios", indent=3)
            print_info("3. Probar en el frontend", indent=3)

        return True

    except Exception as e:
        print_error(f"Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# FUNCIÓN DE ROLLBACK
# ============================================================================

async def rollback_migration(backup_file: Optional[Path] = None) -> bool:
    """
    Revertir migración desde un archivo de backup

    Args:
        backup_file: Ruta al archivo de backup (si es None, usa el más reciente)

    Returns:
        True si el rollback fue exitoso
    """
    try:
        print_header("ROLLBACK DE MIGRACION")

        # ====================================================================
        # Encontrar archivo de backup
        # ====================================================================
        if backup_file is None:
            # Buscar backup más reciente
            backups = sorted(BACKUPS_DIR.glob("interface_config.backup.*.json"), reverse=True)
            if not backups:
                print_error("No se encontraron archivos de backup")
                return False
            backup_file = backups[0]
        else:
            backup_file = Path(backup_file)
            if not backup_file.exists():
                print_error(f"Archivo de backup no encontrado: {backup_file}")
                return False

        print_success(f"Usando backup: {backup_file.name}")

        # ====================================================================
        # Leer backup
        # ====================================================================
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        config_data = backup_data.get('data', backup_data)

        print_success("Backup leído correctamente")
        print_info(f"Creado: {backup_data.get('metadata', {}).get('created_at', 'Desconocido')}")

        # ====================================================================
        # Conectar a MongoDB
        # ====================================================================
        db = get_database()
        print_success("Conectado a MongoDB")

        # ====================================================================
        # Limpiar datos de MongoDB
        # ====================================================================
        print("\n¿Desea eliminar TODOS los datos de configuración en MongoDB? (s/N): ")
        response = input()
        if response.lower() == 's':
            await db.interface_configurations.delete_many({})
            await db.preset_configurations.delete_many({})
            await db.configuration_history.delete_many({})
            print_success("Datos de MongoDB eliminados")

        # ====================================================================
        # Restaurar archivo JSON
        # ====================================================================
        print("\n¿Desea restaurar el archivo interface_config.json? (s/N): ")
        response = input()
        if response.lower() == 's':
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print_success(f"Archivo restaurado: {CONFIG_FILE}")

        print_header("ROLLBACK COMPLETADO")
        return True

    except Exception as e:
        print_error(f"Error durante rollback: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description='Migrar configuraciones de interfaz a MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Simulación sin cambios
  python migrate_interface_config_to_mongodb.py --dry-run

  # Migración real
  python migrate_interface_config_to_mongodb.py

  # Rollback usando último backup
  python migrate_interface_config_to_mongodb.py --rollback

  # Rollback desde backup específico
  python migrate_interface_config_to_mongodb.py --rollback --backup-file=backups/interface_config.backup.2025-10-06-19-30-45.json
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular migración sin hacer cambios reales'
    )

    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Revertir migración usando backup'
    )

    parser.add_argument(
        '--backup-file',
        type=str,
        help='Archivo de backup específico para rollback'
    )

    args = parser.parse_args()

    # Ejecutar rollback o migración
    if args.rollback:
        backup_path = Path(args.backup_file) if args.backup_file else None
        success = asyncio.run(rollback_migration(backup_path))
    else:
        success = asyncio.run(migrate_to_mongodb(dry_run=args.dry_run))

    # Salir con código apropiado
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
