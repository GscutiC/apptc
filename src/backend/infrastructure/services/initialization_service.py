"""
Servicio de inicialización de datos del sistema.
Este servicio se ejecuta al iniciar la aplicación para asegurar que existan
los datos necesarios en la base de datos (roles, configuración, etc.).
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class DataInitializationService:
    """
    Servicio centralizado para inicializar datos del sistema.
    Asegura que los datos esenciales existan en la base de datos.
    """
    
    def __init__(self, database):
        self.database = database
        self._initialized = False
    
    async def initialize_all(self) -> Dict[str, Any]:
        """
        Ejecuta todas las inicializaciones necesarias.
        Retorna un resumen de lo inicializado.
        """
        if self._initialized:
            logger.info("⏭️ Sistema ya inicializado, omitiendo...")
            return {"status": "already_initialized", "created": {}}
        
        logger.info("🚀 Iniciando inicialización de datos del sistema...")
        
        results = {
            "roles": await self._initialize_roles(),
            "interface_config": await self._initialize_interface_config(),
        }
        
        self._initialized = True
        
        total_created = sum(
            len(v.get("created", [])) if isinstance(v, dict) else 0 
            for v in results.values()
        )
        
        logger.info(f"✅ Inicialización completada. {total_created} elementos creados.")
        
        return {
            "status": "success",
            "created": results
        }
    
    async def _initialize_roles(self) -> Dict[str, Any]:
        """Inicializa los roles por defecto del sistema."""
        from ...domain.value_objects.permissions import DefaultRoles
        from ...infrastructure.persistence.mongodb.auth_repository_impl import MongoRoleRepository
        from ...application.use_cases.role_management import InitializeDefaultRolesUseCase
        
        try:
            logger.info("📋 Verificando roles del sistema...")
            
            role_repo = MongoRoleRepository(self.database)
            use_case = InitializeDefaultRolesUseCase(role_repo)
            
            created_roles = await use_case.execute()
            
            if created_roles:
                role_names = [role.name for role in created_roles]
                logger.info(f"✅ Roles creados: {role_names}")
                return {
                    "status": "created",
                    "created": role_names,
                    "count": len(created_roles)
                }
            else:
                logger.info("✅ Roles ya existentes, no se requiere inicialización")
                return {
                    "status": "already_exists",
                    "created": [],
                    "count": 0
                }
        except Exception as e:
            logger.error(f"❌ Error inicializando roles: {e}")
            return {
                "status": "error",
                "error": str(e),
                "created": []
            }
    
    async def _initialize_interface_config(self) -> Dict[str, Any]:
        """Inicializa la configuración de interfaz por defecto."""
        try:
            logger.info("🎨 Verificando configuración de interfaz...")
            
            collection = self.database["interface_configurations"]
            
            # Verificar si ya existe alguna configuración global (sin clerk_id específico)
            existing = await collection.find_one({"clerk_id": "__global__"})
            
            if not existing:
                # Crear configuración global por defecto
                default_config = self._get_default_interface_config()
                default_config["clerk_id"] = "__global__"
                
                await collection.insert_one(default_config)
                logger.info("✅ Configuración de interfaz global creada")
                return {
                    "status": "created",
                    "created": ["__global__"],
                    "count": 1
                }
            else:
                logger.info("✅ Configuración de interfaz ya existe")
                return {
                    "status": "already_exists",
                    "created": [],
                    "count": 0
                }
        except Exception as e:
            logger.error(f"❌ Error inicializando configuración de interfaz: {e}")
            return {
                "status": "error",
                "error": str(e),
                "created": []
            }
    
    def _get_default_interface_config(self) -> Dict[str, Any]:
        """Retorna la configuración de interfaz por defecto."""
        return {
            "theme": {
                "primaryColor": {
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
                "secondaryColor": {
                    "50": "#f8fafc",
                    "100": "#f1f5f9",
                    "200": "#e2e8f0",
                    "300": "#cbd5e1",
                    "400": "#94a3b8",
                    "500": "#64748b",
                    "600": "#475569",
                    "700": "#334155",
                    "800": "#1e293b",
                    "900": "#0f172a"
                },
                "accentColor": {
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
                "backgroundColor": "#ffffff",
                "textColor": "#1f2937",
                "borderRadius": "0.5rem",
                "fontFamily": "Inter, system-ui, sans-serif"
            },
            "branding": {
                "companyName": "Mi Aplicación",
                "companySlogan": "Sistema de Gestión",
                "showLogo": True,
                "logoPosition": "left"
            },
            "layout": {
                "sidebarPosition": "left",
                "sidebarCollapsed": False,
                "headerFixed": True,
                "footerVisible": True
            },
            "features": {
                "darkMode": False,
                "notifications": True,
                "animations": True,
                "compactMode": False
            }
        }


# Instancia singleton del servicio
_initialization_service: Optional[DataInitializationService] = None


async def initialize_system_data(database) -> Dict[str, Any]:
    """
    Función helper para inicializar datos del sistema.
    Usa un singleton para evitar múltiples inicializaciones.
    """
    global _initialization_service
    
    if _initialization_service is None:
        _initialization_service = DataInitializationService(database)
    
    return await _initialization_service.initialize_all()


async def ensure_roles_initialized(database) -> bool:
    """
    Verifica que los roles estén inicializados.
    Puede ser llamado desde cualquier parte de la aplicación.
    """
    from ...domain.value_objects.permissions import DefaultRoles
    
    try:
        roles_collection = database["roles"]
        
        # Verificar que existan los roles básicos
        for role_name in DefaultRoles.ROLES_CONFIG.keys():
            exists = await roles_collection.find_one({"name": role_name})
            if not exists:
                # Si falta algún rol, ejecutar inicialización completa
                service = DataInitializationService(database)
                await service._initialize_roles()
                return True
        
        return True
    except Exception as e:
        logger.error(f"Error verificando roles: {e}")
        return False
