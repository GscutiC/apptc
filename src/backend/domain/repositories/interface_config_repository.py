"""
Repositorio para configuración de interfaz
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.interface_config import InterfaceConfig, PresetConfig, ConfigHistory


class InterfaceConfigRepository(ABC):
    """Repositorio abstracto para configuración de interfaz"""

    @abstractmethod
    async def get_current_config(self) -> Optional[InterfaceConfig]:
        """Obtener la configuración actual activa"""
        pass

    @abstractmethod
    async def save_config(self, config: InterfaceConfig) -> InterfaceConfig:
        """Guardar configuración"""
        pass

    @abstractmethod
    async def get_config_by_id(self, config_id: str) -> Optional[InterfaceConfig]:
        """Obtener configuración por ID"""
        pass

    @abstractmethod
    async def get_all_configs(self) -> List[InterfaceConfig]:
        """Obtener todas las configuraciones"""
        pass

    @abstractmethod
    async def delete_config(self, config_id: str) -> bool:
        """Eliminar configuración"""
        pass

    @abstractmethod
    async def set_active_config(self, config_id: str) -> bool:
        """Establecer configuración como activa"""
        pass


class PresetConfigRepository(ABC):
    """Repositorio abstracto para presets de configuración"""

    @abstractmethod
    async def get_all_presets(self) -> List[PresetConfig]:
        """Obtener todos los presets"""
        pass

    @abstractmethod
    async def get_preset_by_id(self, preset_id: str) -> Optional[PresetConfig]:
        """Obtener preset por ID"""
        pass

    @abstractmethod
    async def get_system_presets(self) -> List[PresetConfig]:
        """Obtener presets del sistema"""
        pass

    @abstractmethod
    async def get_custom_presets(self) -> List[PresetConfig]:
        """Obtener presets personalizados"""
        pass

    @abstractmethod
    async def get_default_preset(self) -> Optional[PresetConfig]:
        """Obtener preset por defecto"""
        pass

    @abstractmethod
    async def save_preset(self, preset: PresetConfig) -> PresetConfig:
        """Guardar preset"""
        pass

    @abstractmethod
    async def delete_preset(self, preset_id: str) -> bool:
        """Eliminar preset (solo si no es del sistema)"""
        pass

    @abstractmethod
    async def set_default_preset(self, preset_id: str) -> bool:
        """Establecer preset como por defecto"""
        pass


class ConfigHistoryRepository(ABC):
    """Repositorio abstracto para historial de configuraciones"""

    @abstractmethod
    async def save_history_entry(self, history: ConfigHistory) -> ConfigHistory:
        """Guardar entrada en el historial"""
        pass

    @abstractmethod
    async def get_history(self, limit: int = 10) -> List[ConfigHistory]:
        """Obtener historial de configuraciones"""
        pass

    @abstractmethod
    async def get_history_by_config_id(self, config_id: str, limit: int = 10) -> List[ConfigHistory]:
        """Obtener historial de una configuración específica"""
        pass

    @abstractmethod
    async def clear_old_history(self, days: int = 30) -> int:
        """Limpiar historial antiguo y retornar número de entradas eliminadas"""
        pass