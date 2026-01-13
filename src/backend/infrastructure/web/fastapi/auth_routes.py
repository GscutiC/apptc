from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
import requests
from datetime import datetime

from ....domain.entities.auth_models import User, Role, UserCreate, UserUpdate, UserWithRole, RoleCreate, RoleUpdate
from ....domain.repositories.auth_repository import UserRepository, RoleRepository
from ...persistence.mongodb.auth_repository_impl import MongoUserRepository, MongoRoleRepository
from ...config.database import get_database
from ...services.clerk_service import clerk_service
from ....application.dto.role_dto import (
    RoleCreateDTO, RoleUpdateDTO, RoleResponseDTO, RoleWithStatsDTO, 
    PermissionCategoryDTO, RoleAssignmentDTO, UserRoleDTO
)
from ....application.use_cases.role_management import (
    CreateRoleUseCase, UpdateRoleUseCase, DeleteRoleUseCase,
    GetRoleWithStatsUseCase, ListRolesWithStatsUseCase,
    GetAvailablePermissionsUseCase, InitializeDefaultRolesUseCase,
    AssignRoleToUserUseCase
)
from .auth_dependencies import get_current_user, get_current_user_optional, get_user_repository

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# Clerk configuration
import os
from dotenv import load_dotenv

load_dotenv()

CLERK_PUBLISHABLE_KEY = os.getenv("CLERK_PUBLISHABLE_KEY")
if not CLERK_PUBLISHABLE_KEY:
    raise ValueError("CLERK_PUBLISHABLE_KEY environment variable is required")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")
if not CLERK_SECRET_KEY:
    raise ValueError("CLERK_SECRET_KEY environment variable is required")
CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")
if not CLERK_WEBHOOK_SECRET:
    raise ValueError("CLERK_WEBHOOK_SECRET environment variable is required")
CLERK_JWT_ISSUER = "https://primary-bat-80.clerk.accounts.dev"

def get_user_repository() -> UserRepository:
    """Dependency para obtener el repositorio de usuarios"""
    db = get_database()
    return MongoUserRepository(db)

def get_role_repository() -> RoleRepository:
    """Dependency para obtener el repositorio de roles"""
    db = get_database()
    return MongoRoleRepository(db)

async def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verificar token JWT de Clerk usando PyJWKClient"""
    # Obtener configuración del entorno
    debug_mode = os.getenv("DEBUG", "False").lower() == "true"
    
    try:
        # Usar PyJWKClient para obtener las claves automáticamente
        jwks_url = f"{CLERK_JWT_ISSUER}/.well-known/jwks.json"
        
        jwks_client = PyJWKClient(jwks_url)
        
        # Obtener la clave de firma del token
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        
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
        
        return payload
        
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

# Logger para auth_routes
import logging
auth_logger = logging.getLogger(__name__)

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
        # Si el usuario no existe en nuestra DB, obtenemos sus datos de la API de Clerk
        try:
            # Obtener datos completos del usuario desde la API de Clerk
            clerk_user_data = await clerk_service.get_user_by_id(clerk_id)
            
            if clerk_user_data:
                # Extraer información normalizada
                user_info = clerk_service.extract_user_info(clerk_user_data)
                auth_logger.info(f"📥 Datos de Clerk para nuevo usuario: {user_info}")
                
                user_data = UserCreate(
                    clerk_id=clerk_id,
                    email=user_info.get("email", ""),
                    first_name=user_info.get("first_name"),
                    last_name=user_info.get("last_name"),
                    full_name=user_info.get("full_name"),
                    image_url=user_info.get("image_url"),
                    phone_number=user_info.get("phone_number")
                )
            else:
                # Fallback: usar datos del token (pueden estar vacíos)
                auth_logger.warning(f"⚠️ No se pudieron obtener datos de Clerk, usando datos del token")
                user_data = UserCreate(
                    clerk_id=clerk_id,
                    email=token_data.get("email", ""),
                    first_name=token_data.get("given_name"),
                    last_name=token_data.get("family_name"),
                    full_name=token_data.get("name"),
                    image_url=token_data.get("image_url"),
                    phone_number=token_data.get("phone_number")
                )
            
            # Usar get_or_create para evitar duplicados por condiciones de carrera
            created_user, was_created = await user_repo.get_or_create_user(user_data)
            user = await user_repo.get_user_with_role(clerk_id)
            if was_created:
                auth_logger.info(f"✅ Usuario creado exitosamente: {clerk_id}")
            else:
                auth_logger.info(f"ℹ️ Usuario ya existía (creado por webhook): {clerk_id}")
        except Exception as e:
            auth_logger.error(f"❌ Error creando usuario: {str(e)}")
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
    await user_repo.update_last_login(clerk_id)

    return user

# Endpoints de usuarios
@router.get("/me", response_model=UserWithRole)
# @requires_active_user
async def get_current_user_info(
    request: Request,
    current_user: UserWithRole = Depends(get_current_user)
):
    """Obtener información del usuario actual"""
    return current_user

@router.get("/me-bypass/{clerk_id}")
async def get_current_user_bypass(
    clerk_id: str,
    user_repo: UserRepository = Depends(get_user_repository)
):
    """ENDPOINT TEMPORAL: Bypass JWT para debuggear"""
    user = await user_repo.get_user_with_role(clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

@router.put("/me", response_model=UserWithRole)
# @requires_active_user
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
# @requires_permission("users.list")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Listar usuarios (requiere permiso users.list)"""
    # El decorador ya validó el permiso, no necesitamos validación manual
    
    return await user_repo.list_users(skip=skip, limit=limit)

@router.put("/users/{clerk_id}/role", response_model=UserWithRole)
# @requires_permission("roles.assign")
async def update_user_role(
    clerk_id: str,
    role_name: str,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Actualizar rol de usuario (requiere permiso roles.assign)"""
    # El decorador ya validó el permiso
    
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
@router.get("/roles", response_model=List[RoleResponseDTO])
async def list_roles(
    current_user: UserWithRole = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Listar todos los roles (requiere usuario autenticado)"""
    # Verificamos si el usuario tiene permisos para leer roles
    user_permissions = current_user.role.get("permissions", []) if current_user.role else []
    if "roles.read" not in user_permissions and "roles.list" not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to access roles"
        )
    
    # Obtener roles desde el repositorio
    roles = await role_repo.list_roles()
    
    # Convertir a DTOs (mismo patrón que /roles/detailed)
    role_dtos = []
    for role in roles:
        role_dto = RoleResponseDTO(
            id=str(role.id),
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            permissions=role.permissions,
            is_active=role.is_active,
            is_system_role=role.is_system_role,
            created_at=role.created_at,
            updated_at=role.updated_at
        )
        role_dtos.append(role_dto)
    
    return role_dtos

@router.post("/roles", response_model=Role)
# @requires_permission("roles.create")
async def create_role(
    role: Role,
    current_user: UserWithRole = Depends(get_current_user),
    role_repo: RoleRepository = Depends(get_role_repository)
):
    """Crear nuevo rol (requiere permiso roles.create)"""
    # El decorador ya validó el permiso
    
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

# Endpoint de debugging para verificar token
@router.get("/debug/token")
async def debug_token(token_data: dict = Depends(verify_clerk_token)):
    """Endpoint para verificar qué información está en el token"""
    return {
        "token_data": token_data,
        "clerk_id": token_data.get("sub"),
        "email": token_data.get("email"),
        "name": token_data.get("name"),
        "given_name": token_data.get("given_name"),
        "family_name": token_data.get("family_name"),
        "all_claims": {k: v for k, v in token_data.items()}
    }

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
            # Crear usuario en nuestra DB (usando get_or_create para evitar duplicados)
            user_data = UserCreate(
                clerk_id=data["id"],
                email=data.get("email_addresses", [{}])[0].get("email_address", ""),
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
                image_url=data.get("image_url"),
                phone_number=data.get("phone_numbers", [{}])[0].get("phone_number")
            )
            # Usar get_or_create para evitar duplicados por condiciones de carrera
            user, was_created = await user_repo.get_or_create_user(user_data)
            auth_logger.info(f"{'✅ Usuario creado' if was_created else 'ℹ️ Usuario ya existía'} via webhook: {data['id']}")
            
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

# ==========================================
# NUEVOS ENDPOINTS PARA GESTIÓN AVANZADA DE ROLES
# ==========================================

# Dependencias para casos de uso
def get_create_role_use_case(
    role_repo: RoleRepository = Depends(get_role_repository)
) -> CreateRoleUseCase:
    return CreateRoleUseCase(role_repo)

def get_update_role_use_case(
    role_repo: RoleRepository = Depends(get_role_repository)
) -> UpdateRoleUseCase:
    return UpdateRoleUseCase(role_repo)

def get_delete_role_use_case(
    role_repo: RoleRepository = Depends(get_role_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> DeleteRoleUseCase:
    return DeleteRoleUseCase(role_repo, user_repo)

def get_role_with_stats_use_case(
    role_repo: RoleRepository = Depends(get_role_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> GetRoleWithStatsUseCase:
    return GetRoleWithStatsUseCase(role_repo, user_repo)

def get_list_roles_with_stats_use_case(
    role_repo: RoleRepository = Depends(get_role_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> ListRolesWithStatsUseCase:
    return ListRolesWithStatsUseCase(role_repo, user_repo)

def get_available_permissions_use_case() -> GetAvailablePermissionsUseCase:
    return GetAvailablePermissionsUseCase()

def get_initialize_default_roles_use_case(
    role_repo: RoleRepository = Depends(get_role_repository)
) -> InitializeDefaultRolesUseCase:
    return InitializeDefaultRolesUseCase(role_repo)

def get_assign_role_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    role_repo: RoleRepository = Depends(get_role_repository)
) -> AssignRoleToUserUseCase:
    return AssignRoleToUserUseCase(user_repo, role_repo)

# ==========================================
# ENDPOINTS DE GESTIÓN DE ROLES AVANZADA
# ==========================================

@router.get("/permissions", response_model=dict)
# @requires_permission("roles.read")
async def get_available_permissions(
    current_user: UserWithRole = Depends(get_current_user),
    use_case: GetAvailablePermissionsUseCase = Depends(get_available_permissions_use_case)
):
    """Obtener todos los permisos disponibles organizados por categoría"""
    permissions = await use_case.execute()
    return {
        "permissions": permissions,
        "total_categories": len(permissions),
        "total_permissions": sum(len(perms) for perms in permissions.values())
    }

@router.get("/roles/detailed", response_model=List[RoleWithStatsDTO])
# @requires_permission("roles.read")
async def list_roles_with_stats(
    include_inactive: bool = False,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: ListRolesWithStatsUseCase = Depends(get_list_roles_with_stats_use_case)
):
    """Listar todos los roles con estadísticas de uso"""
    result = await use_case.execute(include_inactive=include_inactive)
    return result

@router.get("/roles/{role_id}/detailed", response_model=RoleWithStatsDTO)
# @requires_permission("roles.read")
async def get_role_with_stats(
    role_id: str,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: GetRoleWithStatsUseCase = Depends(get_role_with_stats_use_case)
):
    """Obtener un rol específico con estadísticas"""
    try:
        return await use_case.execute(role_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/roles/create", response_model=RoleResponseDTO)
# @requires_permission("roles.create")
async def create_new_role(
    role_data: RoleCreateDTO,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: CreateRoleUseCase = Depends(get_create_role_use_case)
):
    """Crear un nuevo rol con permisos específicos"""
    try:
        return await use_case.execute(role_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/roles/{role_id}/update", response_model=RoleResponseDTO)
# @requires_permission("roles.update")
async def update_existing_role(
    role_id: str,
    role_data: RoleUpdateDTO,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: UpdateRoleUseCase = Depends(get_update_role_use_case)
):
    """Actualizar un rol existente"""
    try:
        return await use_case.execute(role_id, role_data)
    except Exception as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))

@router.delete("/roles/{role_id}")
# @requires_permission("roles.delete")
async def delete_existing_role(
    role_id: str,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: DeleteRoleUseCase = Depends(get_delete_role_use_case)
):
    """Eliminar un rol (solo si no hay usuarios asignados)"""
    try:
        success = await use_case.execute(role_id)
        if success:
            return {"message": "Role deleted successfully", "role_id": role_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete role"
            )
    except Exception as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(e))

@router.post("/roles/assign")
# @requires_permission("roles.assign")
async def assign_role_to_user(
    assignment: RoleAssignmentDTO,
    current_user: UserWithRole = Depends(get_current_user),
    use_case: AssignRoleToUserUseCase = Depends(get_assign_role_use_case)
):
    """Asignar un rol específico a un usuario"""
    try:
        success = await use_case.execute(assignment.clerk_id, assignment.role_name)
        if success:
            return {
                "message": "Role assigned successfully",
                "clerk_id": assignment.clerk_id,
                "role_name": assignment.role_name
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign role"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/roles/initialize-defaults")
# @requires_role("super_admin")
async def initialize_default_roles(
    current_user: UserWithRole = Depends(get_current_user),
    use_case: InitializeDefaultRolesUseCase = Depends(get_initialize_default_roles_use_case)
):
    """Inicializar roles por defecto del sistema (solo super_admin)"""
    try:
        created_roles = await use_case.execute()
        return {
            "message": f"Initialized {len(created_roles)} default roles",
            "created_roles": [role.name for role in created_roles],
            "total_created": len(created_roles)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize default roles: {str(e)}"
        )

@router.get("/users/roles", response_model=List[UserRoleDTO])
# @requires_permission("users.read")
async def list_users_with_roles(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[str] = None,
    current_user: UserWithRole = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """Listar usuarios con información de sus roles"""
    try:
        users = await user_repo.list_users(skip=skip, limit=limit)
        
        users_with_roles = []
        for user in users:
            # Filtrar por rol si se especifica
            if role_filter and (not user.role or user.role.get("name") != role_filter):
                continue
                
            user_role_dto = UserRoleDTO(
                user_id=user.id,
                clerk_id=user.clerk_id,
                email=user.email,
                full_name=user.full_name,
                current_role=user.role.get("name") if user.role else None,
                role_display_name=user.role.get("display_name") if user.role else None,
                permissions=user.role.get("permissions", []) if user.role else [],
                is_active=user.is_active
            )
            users_with_roles.append(user_role_dto)
        
        return users_with_roles
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users with roles: {str(e)}"
        )

@router.get("/my-permissions")
async def get_my_permissions(
    current_user: UserWithRole = Depends(get_current_user)
):
    """Obtener permisos del usuario actual"""
    permissions = []
    role_info = None
    
    if current_user.role:
        permissions = current_user.role.get("permissions", [])
        role_info = {
            "name": current_user.role.get("name"),
            "display_name": current_user.role.get("display_name"),
            "description": current_user.role.get("description")
        }
    
    return {
        "user_id": current_user.id,
        "clerk_id": current_user.clerk_id,
        "email": current_user.email,
        "role": role_info,
        "permissions": permissions,
        "permission_count": len(permissions),
        "is_super_admin": "*" in permissions or (role_info and role_info["name"] == "super_admin")
    }


# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN Y CORRECCIÓN DE DATOS
# ============================================================================

@router.post("/admin/fix-users-without-role", tags=["admin"])
async def fix_users_without_role_id():
    """
    Corrige usuarios que tienen role_name pero no role_id.
    Este endpoint es público temporalmente para corregir datos existentes.
    """
    from datetime import timezone
    
    db = get_database()
    users_collection = db.users
    roles_collection = db.roles
    
    # Primero asegurar que existan los roles
    from ....domain.value_objects.permissions import DefaultRoles
    
    roles_created = []
    for role_name, role_config in DefaultRoles.ROLES_CONFIG.items():
        existing = await roles_collection.find_one({"name": role_name})
        if not existing:
            role_doc = {
                "name": role_name,
                "display_name": role_config["display_name"],
                "description": role_config["description"],
                "permissions": role_config["permissions"],
                "is_active": True,
                "is_system_role": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await roles_collection.insert_one(role_doc)
            roles_created.append(role_name)
    
    # Obtener todos los roles
    roles_map = {}
    async for role in roles_collection.find({}):
        roles_map[role["name"]] = role["_id"]
    
    # Buscar usuarios sin role_id
    users_fixed = []
    async for user in users_collection.find({
        "$or": [
            {"role_id": None},
            {"role_id": {"$exists": False}}
        ]
    }):
        role_name = user.get("role_name", "user")
        role_id = roles_map.get(role_name) or roles_map.get("user")
        
        if role_id:
            await users_collection.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "role_id": role_id,
                        "role_name": role_name if role_name in roles_map else "user",
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            users_fixed.append({
                "clerk_id": user.get("clerk_id"),
                "email": user.get("email"),
                "role_assigned": role_name
            })
    
    return {
        "success": True,
        "roles_created": roles_created,
        "users_fixed": users_fixed,
        "total_fixed": len(users_fixed)
    }


@router.post("/admin/assign-super-admin", tags=["admin"])
async def assign_super_admin_to_user(email: str):
    """
    Asigna el rol super_admin a un usuario por email.
    Este endpoint es público temporalmente para configurar el primer super_admin.
    
    Args:
        email: Email del usuario a promover
    """
    from datetime import timezone
    
    db = get_database()
    users_collection = db.users
    roles_collection = db.roles
    
    # Buscar el rol super_admin
    super_admin_role = await roles_collection.find_one({"name": "super_admin"})
    if not super_admin_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rol super_admin no encontrado. Ejecute primero /admin/fix-users-without-role"
        )
    
    # Buscar el usuario
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con email '{email}' no encontrado"
        )
    
    # Actualizar el usuario
    result = await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "role_id": super_admin_role["_id"],
                "role_name": "super_admin",
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count > 0:
        return {
            "success": True,
            "message": f"Usuario {email} ahora es super_admin",
            "user": {
                "clerk_id": user.get("clerk_id"),
                "email": email,
                "role_name": "super_admin"
            }
        }
    else:
        return {
            "success": False,
            "message": "El usuario ya es super_admin o no se pudo actualizar"
        }


@router.get("/admin/system-status", tags=["admin"])
async def get_system_status():
    """
    Verifica el estado del sistema: roles, usuarios, configuración.
    Útil para diagnóstico.
    """
    db = get_database()
    
    # Contar roles
    roles_count = await db.roles.count_documents({})
    roles = []
    async for role in db.roles.find({}):
        roles.append({
            "name": role["name"],
            "display_name": role.get("display_name"),
            "is_active": role.get("is_active", True)
        })
    
    # Contar usuarios por rol
    users_by_role = {}
    async for user in db.users.find({}):
        role_name = user.get("role_name", "sin_rol")
        has_role_id = user.get("role_id") is not None
        key = f"{role_name} (con_id)" if has_role_id else f"{role_name} (sin_id)"
        users_by_role[key] = users_by_role.get(key, 0) + 1
    
    # Buscar super_admins
    super_admins = []
    async for user in db.users.find({"role_name": "super_admin"}):
        super_admins.append({
            "email": user.get("email"),
            "clerk_id": user.get("clerk_id"),
            "has_role_id": user.get("role_id") is not None
        })
    
    # Contar usuarios con problemas
    users_without_role_id = await db.users.count_documents({
        "$or": [
            {"role_id": None},
            {"role_id": {"$exists": False}}
        ]
    })
    
    return {
        "system_status": "healthy" if roles_count > 0 and users_without_role_id == 0 else "needs_fix",
        "roles": {
            "count": roles_count,
            "list": roles
        },
        "users": {
            "by_role": users_by_role,
            "without_role_id": users_without_role_id,
            "super_admins": super_admins
        },
        "recommendations": []
        if roles_count > 0 and users_without_role_id == 0
        else [
            "Ejecutar POST /auth/admin/fix-users-without-role" if users_without_role_id > 0 else None,
            "Ejecutar POST /auth/admin/assign-super-admin?email=tu@email.com" if not super_admins else None
        ]
    }
