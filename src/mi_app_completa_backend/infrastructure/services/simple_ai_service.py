import random
from typing import Dict, Any
from datetime import datetime
from ...domain.services.ai_service import AIService

class SimpleAIService(AIService):
    """Implementación simple del servicio de IA (mock para demostración)"""

    def __init__(self):
        self.responses = [
            "¡Hola! ¿En qué puedo ayudarte hoy?",
            "Esa es una pregunta interesante. Déjame pensarlo...",
            "Entiendo lo que dices. ¿Podrías darme más detalles?",
            "¡Excelente pregunta! Mi respuesta es...",
            "Basándome en tu mensaje, creo que...",
            "¡Qué interesante! Nunca había pensado en eso.",
            "Tienes razón. Eso es algo importante a considerar.",
            "Me parece una buena idea. ¿Has pensado también en...?",
        ]

        self.welcome_messages = [
            "¡Bienvenido! Soy tu asistente de IA. ¿En qué puedo ayudarte?",
            "¡Hola! Estoy aquí para ayudarte con lo que necesites.",
            "¡Saludos! Soy tu compañero digital. ¿Qué tal si conversamos?",
            "¡Hola Mundo! 🌍 Desde el backend con mucho cariño y algo de IA 🤖",
            "¡Bienvenido a mi_app_completa_backend! La comunicación backend-frontend-IA funciona perfectamente ✨",
        ]

    async def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        """Procesar mensaje con IA simple (mock)"""
        # Simular procesamiento
        await self._simulate_thinking()

        # Respuestas contextuales simples
        message_lower = message.lower()

        if "hola" in message_lower or "hello" in message_lower:
            return f"¡Hola! Vi que dijiste: '{message}'. ¡Qué bueno saludarte!"

        if "como estas" in message_lower or "how are you" in message_lower:
            return "¡Estoy funcionando perfectamente! Gracias por preguntar. ¿Y tú cómo estás?"

        if "mi_app_completa_backend" in message_lower:
            return f"¡Excelente! Estás probando mi_app_completa_backend. Todo funciona correctamente: Backend ✅ Frontend ✅ IA ✅"

        if "prueba" in message_lower or "test" in message_lower:
            return f"¡Prueba exitosa! Tu mensaje '{message}' fue procesado correctamente y guardado en MongoDB."

        if "base de datos" in message_lower or "database" in message_lower:
            return "¡La conexión con MongoDB está funcionando! Tu mensaje se guardó correctamente en la base de datos."

        # Respuesta aleatoria por defecto
        response = random.choice(self.responses)
        return f"{response} (Procesé tu mensaje: '{message[:50]}{'...' if len(message) > 50 else ''}')"

    async def generate_welcome_message(self) -> str:
        """Generar mensaje de bienvenida"""
        await self._simulate_thinking()
        return random.choice(self.welcome_messages)

    def get_service_name(self) -> str:
        """Obtener nombre del servicio de IA"""
        return "SimpleAI"

    async def _simulate_thinking(self):
        """Simular tiempo de procesamiento de IA"""
        import asyncio
        await asyncio.sleep(0.5)  # Simular 500ms de procesamiento