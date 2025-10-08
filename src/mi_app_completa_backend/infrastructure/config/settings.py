"""
Configuración centralizada de la aplicación usando Pydantic Settings
"""
import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""
    
    # Base de datos
    mongodb_url: str = Field(default="mongodb://localhost:27017", description="URL de conexión a MongoDB")
    database_name: str = Field(default="apptc", description="Nombre de la base de datos")
    
    # API
    api_host: str = Field(default="0.0.0.0", description="Host de la API")
    api_port: int = Field(default=8000, description="Puerto de la API")
    debug: bool = Field(default=True, description="Modo de desarrollo")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Orígenes permitidos para CORS (separados por coma)"
    )
    
    # Clerk Authentication
    clerk_secret_key: str = Field(..., description="Clave secreta de Clerk")
    clerk_publishable_key: Optional[str] = Field(default=None, description="Clave pública de Clerk")
    clerk_webhook_secret: Optional[str] = Field(default=None, description="Secret del webhook de Clerk")
    
    # Configuración adicional
    log_level: str = Field(default="INFO", description="Nivel de logging")
    max_upload_size: int = Field(default=10485760, description="Tamaño máximo de archivo (10MB)")
    rate_limit_per_minute: int = Field(default=100, description="Límite de requests por minuto")
    
    def get_cors_origins_list(self) -> List[str]:
        """Obtener CORS origins como lista"""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, v):
        """Convertir string a boolean para DEBUG"""
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_ignore_empty=True,
        extra='ignore'
    )


class ProductionSettings(Settings):
    """Configuración para producción con valores por defecto optimizados"""
    
    debug: bool = Field(default=False, description="Modo de desarrollo (desactivado en prod)")
    log_level: str = Field(default="WARNING", description="Nivel de logging para producción")
    cors_origins: str = Field(
        default="https://tu-dominio.com",
        description="Orígenes permitidos para CORS en producción (separados por coma)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding='utf-8',
        case_sensitive=False
    )


def get_settings(environment: str = "development") -> Settings:
    """
    Factory function para obtener la configuración según el entorno
    
    Args:
        environment: "development" o "production"
        
    Returns:
        Instancia de Settings configurada para el entorno
    """
    if environment.lower() == "production":
        return ProductionSettings()
    
    # Para desarrollo, intentar cargar desde .env
    env_file = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_file):
        return Settings(_env_file=env_file)
    return Settings()


def load_settings_from_env_file(env_file: str = None) -> Settings:
    """
    Cargar configuración desde un archivo .env específico
    
    Args:
        env_file: Ruta al archivo .env (por defecto usa .env)
        
    Returns:
        Instancia de Settings
    """
    if env_file and os.path.exists(env_file):
        return Settings(_env_file=env_file)
    return Settings()


# Instancia global de configuración (se inicializa con development por defecto)
settings = get_settings(os.getenv("ENVIRONMENT", "development"))


def get_database_url() -> str:
    """Obtener URL de la base de datos"""
    return settings.mongodb_url


def get_database_name() -> str:
    """Obtener nombre de la base de datos"""
    return settings.database_name


def is_debug_mode() -> bool:
    """Verificar si está en modo debug"""
    return settings.debug


def get_cors_origins() -> List[str]:
    """Obtener orígenes CORS permitidos"""
    return settings.get_cors_origins_list()