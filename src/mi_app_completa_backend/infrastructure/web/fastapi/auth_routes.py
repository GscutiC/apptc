from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests
from datetime import datetime

from ....domain.entities.auth_models import User, Role, UserCreate, UserUpdate, UserWithRole
from ....domain.repositories.auth_repository import UserRepository, RoleRepository
from ...persistence.mongodb.auth_repository_impl import MongoUserRepository, MongoRoleRepository
from ...config.database import get_database

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# Clerk configuration
CLERK_PUBLISHABLE_KEY = "pk_test_cHJpbWFyeS1iYXQtODAuY2xlcmsuYWNjb3VudHMuZGV2JA"
CLERK_JWT_ISSUER = "https://primary-bat-80.clerk.accounts.dev"

async def get_user_repository() -> UserRepository:
    """Dependency para obtener el repositorio de usuarios"""
    db = await get_database()
    return MongoUserRepository(db)

async def get_role_repository() -> RoleRepository:
    """Dependency para obtener el repositorio de roles"""
    db = await get_database()
    return MongoRoleRepository(db)

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verificar token JWT de Clerk"""
    try:
        # Obtener las claves públicas de Clerk
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        jwks_response = requests.get(jwks_url)
        jwks = jwks_response.json()
        
        # Decodificar el token
        header = jwt.get_unverified_header(credentials.credentials)
        key = None
        
        for jwk in jwks["keys"]:
            if jwk["kid"] == header["kid"]:
                key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token key not found"
            )
        
        payload = jwt.decode(
            credentials.credentials,
            key,
            algorithms=["RS256"],
            issuer=CLERK_JWT_ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

async def get_current_user(
    token_data: dict = Depends(verify_clerk_token),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserWithRole:
    """Obtener usuario actual desde token"""
    clerk_id = token_data.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject"
        )
    
    user = await user_repo.get_user_with_role(clerk_id)
    if not user:
        # Si el usuario no existe en nuestra DB, lo creamos desde los datos del token
        user_data = UserCreate(
            clerk_id=clerk_id,
            email=token_data.get("email", ""),
            first_name=token_data.get("given_name"),
            last_name=token_data.get("family_name"),
            full_name=token_data.get("name")
        )
        await user_repo.create_user(user_data)
        user = await user_repo.get_user_with_role(clerk_id)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active"
        )
    
    # Actualizar último login
    await user_repo.update_last_login(clerk_id)
    
    return user

# Endpoints de usuarios
@router.get("/me", response_model=UserWithRole)
async def get_current_user_info(
    current_user: UserWithRole = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.put("/me", response_model=UserWithRole)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Actualizar información del usuario actual"""
    updated_user = await user_repo.update_user(current_user.clerk_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return await user_repo.get_user_with_role(current_user.clerk_id)

@router.get("/users", response_model=List[UserWithRole])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Listar usuarios (solo super_admin)"""
    if not current_user.role or current_user.role.get("name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can list users"
        )
    
    return await user_repo.list_users(skip=skip, limit=limit)

@router.put("/users/{clerk_id}/role", response_model=UserWithRole)
async def update_user_role(
    clerk_id: str,
    role_name: str,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Actualizar rol de usuario (solo super_admin)"""
    if not current_user.role or current_user.role.get("name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can update user roles"
        )
    
    # Verificar que el rol existe
    role = await role_repo.get_role_by_name(role_name)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found"
        )
    
    # Actualizar usuario
    user_update = UserUpdate(role_name=role_name)
    updated_user = await user_repo.update_user(clerk_id, user_update)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return await user_repo.get_user_with_role(clerk_id)

# Endpoints de roles
@router.get("/roles", response_model=List[Role])
async def list_roles(
    current_user: UserWithRole = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Listar todos los roles"""
    return await role_repo.list_roles()

@router.post("/roles", response_model=Role)
async def create_role(
    role: Role,
    current_user: UserWithRole = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Crear nuevo rol (solo super_admin)"""
    if not current_user.role or current_user.role.get("name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create roles"
        )
    
    try:
        return await role_repo.create_role(role)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    role_id: str,
    role_data: dict,
    current_user: UserWithRole = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Actualizar rol (solo super_admin)"""
    if not current_user.role or current_user.role.get("name") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can update roles"
        )
    
    updated_role = await role_repo.update_role(role_id, role_data)
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    return updated_role

# Webhook para sincronización con Clerk
@router.post("/webhook/clerk")
async def clerk_webhook(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Endpoint para webhooks de Clerk"""
    try:
        payload = await request.json()
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        if event_type == "user.created":
            # Crear usuario en nuestra DB
            user_data = UserCreate(
                clerk_id=data["id"],
                email=data.get("email_addresses", [{}])[0].get("email_address", ""),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                image_url=data.get("image_url"),
                phone_number=data.get("phone_numbers", [{}])[0].get("phone_number")
            )
            await user_repo.create_user(user_data)
            
        elif event_type == "user.updated":
            # Actualizar usuario en nuestra DB
            user_update = UserUpdate(
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                image_url=data.get("image_url"),
                phone_number=data.get("phone_numbers", [{}])[0].get("phone_number")
            )
            await user_repo.update_user(data["id"], user_update)
            
        elif event_type == "user.deleted":
            # Eliminar usuario de nuestra DB
            await user_repo.delete_user(data["id"])
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )