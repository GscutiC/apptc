"""
Dependencias de autenticación para endpoints de FastAPI
Este módulo evita importaciones circulares separando las dependencias
"""
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import requests
from typing import Optional

from ....domain.entities.auth_models import User
from ....domain.repositories.auth_repository import UserRepository
from ...persistence.mongodb.auth_repository_impl import MongoUserRepository
from ...config.database import get_database

security = HTTPBearer()

# Configuración JWT (debe coincidir con Clerk)
CLERK_ISSUER = "https://primary-bat-80.clerk.accounts.dev"
CLERK_AUDIENCE = "primary-bat-80"  # App ID de Clerk


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


async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verificar token JWT de Clerk usando PyJWKClient"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    CLERK_JWT_ISSUER = "https://primary-bat-80.clerk.accounts.dev"
    CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    
    if not CLERK_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clerk configuration missing"
        )
    
    try:
        if debug_mode:
            print(f"🔍 Debug: Verificando token con issuer: {CLERK_JWT_ISSUER}")
        
        # Usar PyJWKClient para obtener las claves automáticamente
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        if debug_mode:
            print(f"🔍 Debug: JWKS URL: {jwks_url}")
        
        jwks_client = PyJWKClient(jwks_url)
        
        # Obtener la clave de firma del token
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        if debug_mode:
            print(f"🔍 Debug: Signing key obtenida exitosamente")
        
        # Configuración JWT adaptativa según entorno
        jwt_options = {
            "verify_signature": True,  # Siempre verificar firma
            "verify_exp": True,        # Siempre verificar expiración
            "verify_iss": True,        # Siempre verificar emisor
            "verify_iat": not debug_mode,  # Más tolerante en desarrollo
            "verify_nbf": not debug_mode,  # Más tolerante en desarrollo
        }
        
        # Decodificar y verificar el token
        payload = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER,
            options=jwt_options
        )
        
        if debug_mode:
            print(f"🔍 Debug: Token decoded successfully. User: {payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError as e:
        if debug_mode:
            print(f"🚨 Debug: Token expired: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        if debug_mode:
            print(f"🚨 Debug: Invalid token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        if debug_mode:
            print(f"🚨 Debug: Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

async def get_current_user(
    token_data: dict = Depends(verify_clerk_token),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Obtener usuario actual autenticado
    """
    from ....domain.entities.auth_models import UserCreate, UserWithRole
    
    clerk_id = token_data.get("sub")

    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )

    user = await user_repo.get_user_with_role(clerk_id)
    if not user:
        # Si el usuario no existe en nuestra DB, lo creamos desde los datos del token
        try:
            user_data = UserCreate(
                clerk_id=clerk_id,
                email=token_data.get("email", ""),
                first_name=token_data.get("given_name"),
                last_name=token_data.get("family_name"),
                full_name=token_data.get("name"),
                image_url=token_data.get("image_url"),
                phone_number=token_data.get("phone_number")
            )
            created_user = await user_repo.create_user(user_data)
            user = await user_repo.get_user_with_role(clerk_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user"
            )
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active"
        )
    
    # Actualizar último login
    # await user_repo.update_last_login(clerk_id)  # Comentado por ahora si no existe el método
    # Login actualizado silenciosamente
    
    # Convertir UserWithRole a User para compatibilidad
    user_dict = {
        "id": user.id,
        "clerk_id": user.clerk_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "image_url": user.image_url,
        "phone_number": user.phone_number,
        "role_id": None,  # No necesario para User
        "role_name": user.role.get("name") if user.role else "user",
        "is_active": user.is_active,
        "last_login": user.last_login,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }
    
    user_obj = User(**user_dict)
    user_obj.role = user.role  # Añadir la información completa del rol
    
    return user_obj
