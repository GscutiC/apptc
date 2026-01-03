"""
Servicio para interactuar con la API de Clerk
Permite obtener información de usuarios que no está disponible en el token JWT
"""
import os
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from ..utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
CLERK_API_URL = "https://api.clerk.com/v1"


class ClerkService:
    """Servicio para interactuar con la API de Clerk"""
    
    def __init__(self):
        if not CLERK_SECRET_KEY:
            logger.warning("CLERK_SECRET_KEY no está configurado")
        self.secret_key = CLERK_SECRET_KEY
        self.api_url = CLERK_API_URL
        
    def _get_headers(self) -> Dict[str, str]:
        """Obtener headers para la API de Clerk"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def get_user_by_id(self, clerk_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información completa de un usuario desde la API de Clerk
        
        Args:
            clerk_id: ID del usuario en Clerk (ej: user_2xyz...)
            
        Returns:
            Diccionario con los datos del usuario o None si no se encuentra
        """
        if not self.secret_key:
            logger.error("CLERK_SECRET_KEY no está configurado, no se puede obtener datos del usuario")
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/users/{clerk_id}",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"✅ Datos de usuario obtenidos de Clerk para {clerk_id}")
                    return user_data
                elif response.status_code == 404:
                    logger.warning(f"Usuario {clerk_id} no encontrado en Clerk")
                    return None
                else:
                    logger.error(f"Error obteniendo usuario de Clerk: {response.status_code} - {response.text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout al obtener usuario {clerk_id} de Clerk")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener usuario de Clerk: {str(e)}")
            return None
    
    def extract_user_info(self, clerk_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extraer información relevante del usuario desde la respuesta de Clerk
        
        Args:
            clerk_user_data: Datos crudos de la API de Clerk
            
        Returns:
            Diccionario con los campos normalizados para nuestra aplicación
        """
        if not clerk_user_data:
            return {}
            
        # Extraer email principal
        email_addresses = clerk_user_data.get("email_addresses", [])
        primary_email = ""
        if email_addresses:
            # Buscar el email primario o tomar el primero
            for email_obj in email_addresses:
                if email_obj.get("id") == clerk_user_data.get("primary_email_address_id"):
                    primary_email = email_obj.get("email_address", "")
                    break
            if not primary_email and email_addresses:
                primary_email = email_addresses[0].get("email_address", "")
        
        # Extraer teléfono principal
        phone_numbers = clerk_user_data.get("phone_numbers", [])
        primary_phone = None
        if phone_numbers:
            for phone_obj in phone_numbers:
                if phone_obj.get("id") == clerk_user_data.get("primary_phone_number_id"):
                    primary_phone = phone_obj.get("phone_number")
                    break
            if not primary_phone and phone_numbers:
                primary_phone = phone_numbers[0].get("phone_number")
        
        # Construir nombre completo
        first_name = clerk_user_data.get("first_name") or ""
        last_name = clerk_user_data.get("last_name") or ""
        full_name = f"{first_name} {last_name}".strip() or None
        
        return {
            "clerk_id": clerk_user_data.get("id"),
            "email": primary_email,
            "first_name": first_name or None,
            "last_name": last_name or None,
            "full_name": full_name,
            "image_url": clerk_user_data.get("image_url"),
            "phone_number": primary_phone,
            "username": clerk_user_data.get("username"),
            "created_at_clerk": clerk_user_data.get("created_at"),
            "updated_at_clerk": clerk_user_data.get("updated_at"),
        }


# Instancia singleton del servicio
clerk_service = ClerkService()
