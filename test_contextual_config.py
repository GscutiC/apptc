"""
Script de testing para configuraciones contextuales
FASE 3: Validación completa del sistema de configuración contextual
"""

import asyncio
import sys
import os

# Añadir el directorio raíz al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import json

from src.mi_app_completa_backend.infrastructure.persistence.mongodb.contextual_config_repository_impl import MongoContextualConfigRepository
from src.mi_app_completa_backend.infrastructure.persistence.mongodb.interface_config_repository_impl import MongoInterfaceConfigRepository
from src.mi_app_completa_backend.application.use_cases.contextual_config_use_cases import ContextualConfigUseCases
from src.mi_app_completa_backend.application.dto.contextual_config_dto import (
    ContextualConfigCreateDTO,
    ConfigContextDTO,
    EffectiveConfigRequestDTO,
    UserPreferencesDTO
)
from src.mi_app_completa_backend.application.dto.interface_config_dto import (
    InterfaceConfigCreateDTO,
    ThemeConfigDTO,
    ColorConfigDTO,
    TypographyConfigDTO,
    LayoutConfigDTO,
    LogoConfigDTO,
    BrandingConfigDTO
)

# Configuración de MongoDB
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "mi_app_completa_db_test")

class ContextualConfigTester:
    """Tester para el sistema de configuraciones contextuales"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.contextual_repo = None
        self.interface_repo = None
        self.use_cases = None
        
    async def setup(self):
        """Configurar conexión y repositorios"""
        print("🔧 Configurando conexión a MongoDB...")
        
        self.client = AsyncIOMotorClient(MONGODB_URL)
        self.db = self.client[DATABASE_NAME]
        
        # Crear repositorios
        self.contextual_repo = MongoContextualConfigRepository(self.db)
        self.interface_repo = MongoInterfaceConfigRepository(self.db)
        
        # Crear casos de uso
        self.use_cases = ContextualConfigUseCases(
            self.contextual_repo,
            self.interface_repo
        )
        
        print("✅ Conexión configurada correctamente")
        
    async def cleanup(self):
        """Limpiar datos de prueba"""
        print("🧹 Limpiando datos de prueba...")
        
        try:
            # Limpiar colecciones de prueba
            await self.db.contextual_configurations.delete_many({"test_data": True})
            await self.db.interface_configurations.delete_many({"test_data": True})
            print("✅ Datos de prueba eliminados")
        except Exception as e:
            print(f"⚠️ Error limpiando datos: {e}")
        
        if self.client:
            self.client.close()
            
    def create_sample_interface_config(self, name: str = "Test Theme") -> InterfaceConfigCreateDTO:
        """Crear configuración de interfaz de ejemplo"""
        return InterfaceConfigCreateDTO(
            theme=ThemeConfigDTO(
                mode="light",
                name=name,
                colors=ColorConfigDTO(
                    primary={
                        "50": "#eff6ff", "100": "#dbeafe", "200": "#bfdbfe",
                        "300": "#93c5fd", "400": "#60a5fa", "500": "#3b82f6",
                        "600": "#2563eb", "700": "#1d4ed8", "800": "#1e40af",
                        "900": "#1e3a8a"
                    },
                    secondary={
                        "50": "#faf5ff", "100": "#f3e8ff", "200": "#e9d5ff",
                        "300": "#d8b4fe", "400": "#c084fc", "500": "#a855f7",
                        "600": "#9333ea", "700": "#7c3aed", "800": "#6b21a8",
                        "900": "#581c87"
                    },
                    accent={
                        "50": "#ecfdf5", "100": "#d1fae5", "200": "#a7f3d0",
                        "300": "#6ee7b7", "400": "#34d399", "500": "#10b981",
                        "600": "#059669", "700": "#047857", "800": "#065f46",
                        "900": "#064e3b"
                    },
                    neutral={
                        "50": "#f9fafb", "100": "#f3f4f6", "200": "#e5e7eb",
                        "300": "#d1d5db", "400": "#9ca3af", "500": "#6b7280",
                        "600": "#4b5563", "700": "#374151", "800": "#1f2937",
                        "900": "#111827"
                    }
                ),
                typography=TypographyConfigDTO(
                    fontFamily={
                        "primary": "Inter, sans-serif",
                        "secondary": "Georgia, serif",
                        "mono": "Monaco, monospace"
                    },
                    fontSize={
                        "xs": "0.75rem", "sm": "0.875rem", "base": "1rem",
                        "lg": "1.125rem", "xl": "1.25rem", "2xl": "1.5rem"
                    },
                    fontWeight={
                        "light": 300, "normal": 400, "medium": 500,
                        "semibold": 600, "bold": 700
                    }
                ),
                layout=LayoutConfigDTO(
                    borderRadius={
                        "sm": "0.125rem", "base": "0.25rem", "md": "0.375rem",
                        "lg": "0.5rem", "xl": "0.75rem"
                    },
                    spacing={
                        "1": "0.25rem", "2": "0.5rem", "3": "0.75rem",
                        "4": "1rem", "5": "1.25rem", "6": "1.5rem"
                    },
                    shadows={
                        "sm": "0 1px 2px rgba(0,0,0,0.05)",
                        "base": "0 4px 6px rgba(0,0,0,0.1)",
                        "lg": "0 10px 15px rgba(0,0,0,0.1)"
                    }
                )
            ),
            logos=LogoConfigDTO(
                mainLogo={"text": "Test App", "showText": True},
                favicon={},
                sidebarLogo={"text": "TA", "showText": True}
            ),
            branding=BrandingConfigDTO(
                appName="Test Application",
                appDescription="Aplicación de prueba para configuraciones contextuales",
                welcomeMessage="¡Bienvenido al sistema de pruebas!",
                footerText="© 2025 Test App",
                supportEmail="test@example.com",
                companyName="Test Company"
            ),
            customCSS="/* CSS personalizado de prueba */",
            isActive=True
        )
    
    async def test_create_global_config(self):
        """Test: Crear configuración global"""
        print("\n🧪 Test 1: Crear configuración global")
        
        try:
            # Crear configuración global
            config_dto = ContextualConfigCreateDTO(
                config=self.create_sample_interface_config("Tema Global de Prueba"),
                context=ConfigContextDTO(context_type="global"),
                is_active=True
            )
            
            result = await self.use_cases.create_contextual_config(
                config_dto,
                created_by="test_system"
            )
            
            print(f"✅ Configuración global creada: {result.id}")
            print(f"   - Nombre: {result.config.theme.name}")
            print(f"   - Contexto: {result.context.context_type}")
            print(f"   - Activa: {result.is_active}")
            
            return result.id
            
        except Exception as e:
            print(f"❌ Error creando configuración global: {e}")
            return None
    
    async def test_create_role_config(self):
        """Test: Crear configuración por rol"""
        print("\n🧪 Test 2: Crear configuración por rol")
        
        try:
            # Crear configuración para rol admin
            config_dto = ContextualConfigCreateDTO(
                config=self.create_sample_interface_config("Tema Admin"),
                context=ConfigContextDTO(
                    context_type="role",
                    context_id="admin"
                ),
                is_active=True
            )
            
            result = await self.use_cases.create_contextual_config(
                config_dto,
                created_by="test_admin"
            )
            
            print(f"✅ Configuración de rol creada: {result.id}")
            print(f"   - Rol: {result.context.context_id}")
            print(f"   - Tema: {result.config.theme.name}")
            
            return result.id
            
        except Exception as e:
            print(f"❌ Error creando configuración de rol: {e}")
            return None
    
    async def test_create_user_config(self):
        """Test: Crear configuración por usuario"""
        print("\n🧪 Test 3: Crear configuración por usuario")
        
        try:
            # Crear configuración para usuario específico
            config_dto = ContextualConfigCreateDTO(
                config=self.create_sample_interface_config("Mi Tema Personal"),
                context=ConfigContextDTO(
                    context_type="user",
                    context_id="user_test_123"
                ),
                is_active=True
            )
            
            result = await self.use_cases.create_contextual_config(
                config_dto,
                created_by="user_test_123"
            )
            
            print(f"✅ Configuración de usuario creada: {result.id}")
            print(f"   - Usuario: {result.context.context_id}")
            print(f"   - Tema: {result.config.theme.name}")
            
            return result.id
            
        except Exception as e:
            print(f"❌ Error creando configuración de usuario: {e}")
            return None
    
    async def test_effective_config_resolution(self):
        """Test: Resolución de configuración efectiva"""
        print("\n🧪 Test 4: Resolución de configuración efectiva")
        
        try:
            # Test 1: Usuario sin configuración propia (debe usar rol o global)
            request1 = EffectiveConfigRequestDTO(
                user_id="user_without_config",
                user_role="admin"
            )
            
            result1 = await self.use_cases.get_effective_config(request1)
            
            if result1:
                print(f"✅ Configuración efectiva resuelta para usuario sin config:")
                print(f"   - Resuelta desde: {result1.resolved_from.context_type}")
                print(f"   - Tema: {result1.config.theme.name}")
            else:
                print("⚠️ No se pudo resolver configuración efectiva")
            
            # Test 2: Usuario con configuración propia
            request2 = EffectiveConfigRequestDTO(
                user_id="user_test_123",
                user_role="admin"
            )
            
            result2 = await self.use_cases.get_effective_config(request2)
            
            if result2:
                print(f"✅ Configuración efectiva resuelta para usuario con config:")
                print(f"   - Resuelta desde: {result2.resolved_from.context_type}")
                print(f"   - ID contexto: {result2.resolved_from.context_id}")
                print(f"   - Tema: {result2.config.theme.name}")
                print(f"   - Cadena de resolución: {[ctx.context_type for ctx in result2.resolution_chain]}")
            
        except Exception as e:
            print(f"❌ Error en resolución de configuración efectiva: {e}")
    
    async def test_user_preferences(self):
        """Test: Guardar preferencias simplificadas de usuario"""
        print("\n🧪 Test 5: Preferencias simplificadas de usuario")
        
        try:
            # Crear preferencias de usuario
            preferences = UserPreferencesDTO(
                user_id="user_preferences_test",
                theme_mode="dark",
                primary_color="#ff6b6b",
                font_size="lg",
                compact_mode=True
            )
            
            result = await self.use_cases.save_user_preferences(preferences)
            
            print(f"✅ Preferencias de usuario guardadas: {result.id}")
            print(f"   - Usuario: {preferences.user_id}")
            print(f"   - Modo tema: {preferences.theme_mode}")
            print(f"   - Color primario: {preferences.primary_color}")
            print(f"   - Tamaño fuente: {preferences.font_size}")
            print(f"   - Modo compacto: {preferences.compact_mode}")
            
        except Exception as e:
            print(f"❌ Error guardando preferencias de usuario: {e}")
    
    async def test_search_and_list(self):
        """Test: Búsqueda y listado de configuraciones"""
        print("\n🧪 Test 6: Búsqueda y listado")
        
        try:
            # Obtener todas las configuraciones contextuales
            all_configs = await self.contextual_repo.list_all(active_only=False)
            
            print(f"✅ Configuraciones contextuales encontradas: {len(all_configs)}")
            
            for config in all_configs[:3]:  # Mostrar solo las primeras 3
                print(f"   - {config.context.context_type}:{config.context.context_id or 'global'}")
                print(f"     Tema: {config.config.theme.name}")
                print(f"     Activa: {config.is_active}")
                print(f"     Creada por: {config.created_by}")
            
        except Exception as e:
            print(f"❌ Error en búsqueda y listado: {e}")
    
    async def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 Iniciando tests de configuraciones contextuales")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Ejecutar tests en orden
            global_id = await self.test_create_global_config()
            role_id = await self.test_create_role_config()
            user_id = await self.test_create_user_config()
            
            await self.test_effective_config_resolution()
            await self.test_user_preferences()
            await self.test_search_and_list()
            
            print("\n" + "=" * 60)
            print("🎉 Tests completados exitosamente")
            
            # Mostrar resumen
            print(f"\n📊 Resumen:")
            print(f"   - Configuración global: {global_id or 'Error'}")
            print(f"   - Configuración rol: {role_id or 'Error'}")
            print(f"   - Configuración usuario: {user_id or 'Error'}")
            
        except Exception as e:
            print(f"💥 Error general en los tests: {e}")
            
        finally:
            await self.cleanup()


async def main():
    """Función principal"""
    tester = ContextualConfigTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Ejecutar tests
    asyncio.run(main())