"""
Dependencias de autenticación para endpoints de FastAPI
Este módulo evita importaciones circulares separando las dependencias
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
from typing import Optional

from ....domain.entities.auth_models import User
from ....domain.repositories.auth_repository import UserRepository
from ...persistence.mongodb.auth_repository_impl import MongoUserRepository
from ...config.database import get_database

security = HTTPBearer()

# Configuración JWT (debe coincidir con Clerk)
CLERK_ISSUER = "https://clerk.com"
CLERK_AUDIENCE = "your-app-id"  # Reemplazar con tu app ID de Clerk


def get_user_repository() -> MongoUserRepository:
    """Dependencia para obtener el repositorio de usuarios"""
    db = get_database()
    return MongoUserRepository(db)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """
    Obtener usuario actual (opcional, no lanza error si no está autenticado)
    """
    if not credentials:
        return None
    
    try:
        # TODO: Implementar validación real con Clerk
        # Por ahora, retornamos None para simular usuario no autenticado
        return None
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Obtener usuario actual autenticado
    """
    try:
        # TODO: Implementar validación real con Clerk JWT
        # Por ahora, simulamos un usuario autenticado para pruebas
        
        # Crear un usuario de prueba con permisos de administrador
        test_user = User(
            id="test_user_id",
            clerk_id="test_clerk_id", 
            email="admin@test.com",
            first_name="Admin",
            last_name="Test",
            image_url="https://example.com/avatar.jpg",
            phone_number="+1234567890",
            role={
                "name": "admin",
                "permissions": [
                    "users.read", "users.write", "users.delete",
                    "roles.read", "roles.write", "roles.delete", 
                    "ai.process_message", "system.read", "admin.full_access"
                ]
            }
        )
        
        return test_user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )