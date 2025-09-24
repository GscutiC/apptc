from typing import Dict, Any
from ..dto.message_dto import CreateMessageDTO, MessageResponseDTO
from ...domain.entities.message import Message
from ...domain.repositories.message_repository import MessageRepository
from ...domain.services.ai_service import AIService

class ProcessAIMessageUseCase:
    """Caso de uso para procesar mensajes con IA"""

    def __init__(self, message_repository: MessageRepository, ai_service: AIService):
        self.message_repository = message_repository
        self.ai_service = ai_service

    async def execute(self, message_data: CreateMessageDTO) -> MessageResponseDTO:
        """Ejecutar procesamiento de mensaje con IA"""

        # Crear mensaje del usuario
        user_message = Message(
            content=message_data.content,
            message_type="user",
            user_id=message_data.user_id
        )

        # Guardar mensaje del usuario
        await self.message_repository.save(user_message)

        # Procesar con IA
        ai_response = await self.ai_service.process_message(
            message_data.content,
            context={"user_id": message_data.user_id}
        )

        # Crear mensaje de respuesta de IA
        ai_message = Message(
            content=ai_response,
            message_type="ai",
            processed_by=self.ai_service.get_service_name(),
            user_id=message_data.user_id
        )

        # Guardar respuesta de IA
        saved_ai_message = await self.message_repository.save(ai_message)

        # Retornar DTO de respuesta
        return MessageResponseDTO(
            id=saved_ai_message.id,
            response=saved_ai_message.content,
            processed_by=saved_ai_message.processed_by,
            timestamp=saved_ai_message.created_at
        )

class GetWelcomeMessageUseCase:
    """Caso de uso para obtener mensaje de bienvenida"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def execute(self) -> Dict[str, Any]:
        """Ejecutar generación de mensaje de bienvenida"""
        welcome_message = await self.ai_service.generate_welcome_message()

        return {
            "message": welcome_message,
            "processed_by": self.ai_service.get_service_name(),
            "type": "welcome"
        }