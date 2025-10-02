"""
Rutas para configuración de interfaz
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/interface-config", tags=["Interface Config"])

# Archivo para guardar la configuración global
CONFIG_FILE = Path("interface_config.json")

# Configuración por defecto
DEFAULT_CONFIG = {
    "id": "global-config",
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
        "websiteUrl": "https://worktec.com"
    },
    "isActive": True,
    "createdAt": "2025-09-25T20:30:00.000Z",
    "updatedAt": "2025-09-25T20:30:00.000Z"
}

def load_config() -> Dict[str, Any]:
    """Cargar configuración desde archivo"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando configuración: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Guardar configuración a archivo con merge inteligente"""
    try:
        # Cargar configuración existente
        existing_config = load_config() if CONFIG_FILE.exists() else DEFAULT_CONFIG.copy()
        
        # Hacer merge inteligente preservando ciertos campos
        # Los logos y branding se mantienen si ya existen, a menos que se envíen explícitamente
        if 'logos' in existing_config and 'logos' not in config:
            config['logos'] = existing_config['logos']
        if 'branding' in existing_config and 'branding' not in config:
            config['branding'] = existing_config['branding']
            
        # Guardar configuración actualizada
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return config
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        raise HTTPException(status_code=500, detail="Error guardando configuración")

@router.get("/current")
async def get_current_config():
    """Obtener la configuración actual de interfaz"""
    return load_config()

@router.post("/")
async def save_interface_config(config: Dict[str, Any]):
    """Guardar nueva configuración de interfaz"""
    try:
        # Agregar timestamp de actualización
        config["updatedAt"] = "2025-09-25T20:30:00.000Z"  # En producción usar datetime.now()
        
        saved_config = save_config(config)
        return saved_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/partial")
async def update_partial_config(updates: Dict[str, Any]):
    """Actualizar solo partes específicas de la configuración"""
    try:
        # Cargar configuración actual
        current_config = load_config()
        
        # Hacer merge profundo de los cambios
        def deep_merge(base: Dict, updates: Dict) -> Dict:
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        # Aplicar actualizaciones
        updated_config = deep_merge(current_config, updates)
        updated_config["updatedAt"] = "2025-09-25T20:30:00.000Z"  # En producción usar datetime.now()
        
        return save_config(updated_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reset")
async def reset_to_default():
    """Resetear configuración a valores por defecto"""
    return save_config(DEFAULT_CONFIG.copy())


# === ENDPOINTS PARA PRESETS ===

# Presets predefinidos del sistema
SYSTEM_PRESETS = [
    {
        "id": "default-elegant-blue",
        "name": "Elegante Azul (Por defecto)",
        "description": "Tema elegante con gradientes azul-morado, perfecto para aplicaciones profesionales",
        "config": DEFAULT_CONFIG.copy(),
        "isDefault": True,
        "isSystem": True,
        "createdAt": "2025-09-25T20:30:00.000Z",
        "updatedAt": "2025-09-25T20:30:00.000Z"
    },
    {
        "id": "dark-elegant", 
        "name": "Oscuro Elegante",
        "description": "Versión oscura del tema elegante, ideal para uso prolongado",
        "config": {
            **DEFAULT_CONFIG,
            "theme": {
                **DEFAULT_CONFIG["theme"],
                "mode": "dark",
                "name": "Tema Oscuro Elegante",
                "colors": {
                    **DEFAULT_CONFIG["theme"]["colors"],
                    "neutral": {
                        "50": "#111827", "100": "#1f2937", "200": "#374151", "300": "#4b5563",
                        "400": "#6b7280", "500": "#9ca3af", "600": "#d1d5db", "700": "#e5e7eb", 
                        "800": "#f3f4f6", "900": "#f9fafb"
                    }
                }
            }
        },
        "isDefault": False,
        "isSystem": True,
        "createdAt": "2025-09-25T20:30:00.000Z",
        "updatedAt": "2025-09-25T20:30:00.000Z"
    },
    {
        "id": "green-corporate",
        "name": "Verde Corporativo", 
        "description": "Tema verde profesional para empresas enfocadas en sostenibilidad",
        "config": {
            **DEFAULT_CONFIG,
            "theme": {
                **DEFAULT_CONFIG["theme"],
                "name": "Tema Verde Corporativo",
                "colors": {
                    **DEFAULT_CONFIG["theme"]["colors"],
                    "primary": {
                        "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0", "300": "#6ee7b7",
                        "400": "#34d399", "500": "#10b981", "600": "#059669", "700": "#047857",
                        "800": "#065f46", "900": "#064e3b"
                    }
                }
            },
            "branding": {
                **DEFAULT_CONFIG["branding"],
                "tagline": "Soluciones empresariales sostenibles"
            }
        },
        "isDefault": False,
        "isSystem": True,
        "createdAt": "2025-09-25T20:30:00.000Z", 
        "updatedAt": "2025-09-25T20:30:00.000Z"
    }
]

@router.get("/presets")
async def get_presets():
    """Obtener todos los presets disponibles"""
    try:
        # Por ahora solo devolvemos presets del sistema
        # En el futuro se pueden cargar presets personalizados desde base de datos
        return SYSTEM_PRESETS
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/presets/{preset_id}")
async def get_preset_by_id(preset_id: str):
    """Obtener preset específico por ID"""
    try:
        preset = next((p for p in SYSTEM_PRESETS if p["id"] == preset_id), None)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset no encontrado")
        return preset
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/presets/{preset_id}/apply")
async def apply_preset(preset_id: str):
    """Aplicar un preset específico"""
    try:
        # Buscar el preset
        preset = next((p for p in SYSTEM_PRESETS if p["id"] == preset_id), None)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset no encontrado")
        
        # Aplicar la configuración del preset
        config_to_apply = preset["config"].copy()
        config_to_apply["updatedAt"] = "2025-09-25T20:30:00.000Z"  # En producción usar datetime.now()
        
        saved_config = save_config(config_to_apply)
        return {
            "message": f"Preset '{preset['name']}' aplicado correctamente",
            "preset_id": preset_id,
            "config": saved_config
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aplicando preset: {str(e)}")

@router.post("/presets")
async def create_custom_preset(preset_data: Dict[str, Any]):
    """Crear preset personalizado"""
    # Por ahora solo mensaje de que no está implementado
    # En el futuro se implementará guardado en base de datos
    raise HTTPException(
        status_code=501, 
        detail="Creación de presets personalizados no implementada aún"
    )

@router.delete("/presets/{preset_id}")  
async def delete_preset(preset_id: str):
    """Eliminar preset personalizado"""
    # Verificar que no sea preset del sistema
    preset = next((p for p in SYSTEM_PRESETS if p["id"] == preset_id), None)
    if preset and preset["isSystem"]:
        raise HTTPException(
            status_code=400, 
            detail="No se pueden eliminar presets del sistema"
        )
    
    # Por ahora solo mensaje de que no está implementado
    raise HTTPException(
        status_code=501,
        detail="Eliminación de presets personalizados no implementada aún"  
    )