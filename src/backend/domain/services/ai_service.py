from abc import ABC, abstractmethod
from typing import Dict, Any

class AIService(ABC):
    """Interface del servicio de IA"""

    @abstractmethod
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Procesar mensaje con IA"""
        pass

    @abstractmethod
    async def generate_welcome_message(self) -> str:
        """Generar mensaje de bienvenida"""
        pass

    @abstractmethod
    def get_service_name(self) -> str:
        """Obtener nombre del servicio de IA"""
        pass