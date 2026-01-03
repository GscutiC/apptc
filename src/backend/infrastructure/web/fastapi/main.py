from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import os
from typing import List
import logging
from ....application.use_cases.create_user import CreateUserUseCase
from ....application.use_cases.process_ai_message import ProcessAIMessageUseCase, GetWelcomeMessageUseCase
from ....application.dto.user_dto import CreateUserDTO, UserResponseDTO
from ....application.dto.message_dto import CreateMessageDTO, MessageResponseDTO
from ....infrastructure.persistence.mongodb.user_repository_impl import MongoUserRepository
from ....infrastructure.persistence.mongodb.message_repository_impl import MongoMessageRepository
from ....infrastructure.services.simple_ai_service import SimpleAIService
from ....infrastructure.config.database import DatabaseConfig
from ....infrastructure.config.settings import get_settings
from .auth_routes import router as auth_router
from .interface_config_routes import router as interface_config_router
# DESHABILITADO: Sistema contextual causa conflictos
# from .contextual_config_routes import router as contextual_config_router
from .file_routes import router as file_router
from .government_routes import router as government_router
from ....domain.entities.auth_models import User
from ....domain.value_objects.auth_decorators import (
    requires_permission, requires_role, requires_active_user,
    verify_active_user, verify_permission, verify_role
)

# Configurar logger
logger = logging.getLogger(__name__)

# Obtener configuración centralizada
settings = get_settings()

app = FastAPI(
    title="mi_app_completa_backend API",
    description="API con arquitectura hexagonal usando python y mongodb",
    version="1.0.0"
)

# 🐛 Manejador global de errores de validación (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Captura errores de validación de Pydantic (422) y los registra en detalle
    """
    errors = exc.errors()
    logger.error(f"❌ Error de validación 422 en {request.method} {request.url.path}")
    logger.error(f"📋 Detalles de errores de validación:")
    
    for error in errors:
        logger.error(f"  - Campo: {' -> '.join(str(loc) for loc in error['loc'])}")
        logger.error(f"    Tipo: {error['type']}")
        logger.error(f"    Mensaje: {error['msg']}")
        if 'ctx' in error:
            logger.error(f"    Contexto: {error['ctx']}")
    
    # Intentar leer el body de la request
    try:
        body = await request.body()
        logger.error(f"📦 Body recibido (raw): {body.decode('utf-8')[:1000]}")  # Primeros 1000 chars
    except Exception as e:
        logger.error(f"No se pudo leer el body: {e}")
    
    # ✅ FIX: Limpiar errors para asegurar que sean JSON serializables
    def clean_error(error: dict) -> dict:
        """Convierte objetos no serializables a strings"""
        cleaned = error.copy()
        if 'ctx' in cleaned and cleaned['ctx']:
            # Convertir valores no serializables a strings
            cleaned['ctx'] = {
                k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                for k, v in cleaned['ctx'].items()
            }
        return cleaned
    
    cleaned_errors = [clean_error(e) for e in errors]
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": cleaned_errors,
            "message": "Error de validación en los datos enviados"
        }
    )

# Configurar CORS usando configuración centralizada
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "Accept", 
        "X-Requested-With",
        "Access-Control-Allow-Headers",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods"
    ] if not settings.debug else ["*"],  # Más restrictivo en producción
)

# Incluir rutas de autenticación
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Incluir rutas de configuración de interfaz
app.include_router(interface_config_router)

# DESHABILITADO: Sistema contextual causa conflictos con interface_configurations
# app.include_router(contextual_config_router)

# Incluir rutas de archivos
app.include_router(file_router)

# Incluir rutas de APIs gubernamentales (RENIEC, SUNAT, etc.)
app.include_router(government_router)

# Incluir rutas de Techo Propio
from .routes.techo_propio_routes import router as techo_propio_router
app.include_router(techo_propio_router)

# Incluir rutas de configuración de Techo Propio
from .techo_propio_config_routes import router as techo_propio_config_router
app.include_router(techo_propio_config_router)

# Configuración de dependencias
from ....infrastructure.config.database import get_database

async def get_user_repository():
    """Dependency injection para UserRepository"""
    database = get_database()
    return MongoUserRepository(database)

async def get_message_repository():
    """Dependency injection para MessageRepository"""
    database = get_database()
    return MongoMessageRepository(database)

def get_ai_service():
    """Dependency injection para AIService"""
    return SimpleAIService()

async def get_create_user_use_case(user_repo: MongoUserRepository = Depends(get_user_repository)):
    """Dependency injection para CreateUserUseCase"""
    return CreateUserUseCase(user_repo)

async def get_process_ai_message_use_case(
    message_repo: MongoMessageRepository = Depends(get_message_repository),
    ai_service: SimpleAIService = Depends(get_ai_service)
):
    """Dependency injection para ProcessAIMessageUseCase"""
    return ProcessAIMessageUseCase(message_repo, ai_service)

def get_welcome_message_use_case(ai_service: SimpleAIService = Depends(get_ai_service)):
    """Dependency injection para GetWelcomeMessageUseCase"""
    return GetWelcomeMessageUseCase(ai_service)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "mi_app_completa_backend API running"}

@app.get("/hello")
async def hello():
    """Endpoint simple de Hello World"""
    return {
        "message": "¡Hola Mundo desde el Backend!",
        "status": "success",
        "timestamp": "2024-01-01T00:00:00",
        "backend": "FastAPI",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mi_app_completa_backend", "version": "1.0.1", "debug_endpoints": "active"}

@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to test CORS"""
    return {
        "message": "CORS test successful",
        "timestamp": "2024-01-01T00:00:00",
        "frontend_can_access": True
    }

@app.post("/debug/create-user")
async def debug_create_user(user_data: dict):
    """Endpoint de debug para crear usuarios desde el frontend (SOLO PARA DESARROLLO)"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        from ....domain.entities.auth_models import UserCreate
        from ....infrastructure.services.clerk_service import clerk_service
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        clerk_id = user_data.get("clerk_id")
        
        # Verificar si ya existe
        existing_user = await user_repo.get_user_by_clerk_id(clerk_id)
        if existing_user:
            # Si existe pero tiene datos vacíos, intentar actualizar desde Clerk
            if not existing_user.email or existing_user.email == "":
                clerk_user_data = await clerk_service.get_user_by_id(clerk_id)
                if clerk_user_data:
                    user_info = clerk_service.extract_user_info(clerk_user_data)
                    from ....domain.entities.auth_models import UserUpdate
                    update_data = UserUpdate(
                        email=user_info.get("email") or existing_user.email,
                        first_name=user_info.get("first_name") or existing_user.first_name,
                        last_name=user_info.get("last_name") or existing_user.last_name,
                        full_name=user_info.get("full_name") or existing_user.full_name,
                        image_url=user_info.get("image_url") or existing_user.image_url,
                        phone_number=user_info.get("phone_number") or existing_user.phone_number
                    )
                    updated_user = await user_repo.update_user(clerk_id, update_data)
                    return {
                        "success": True,
                        "message": "Usuario actualizado con datos de Clerk",
                        "user": {
                            "id": str(updated_user.id) if updated_user else str(existing_user.id),
                            "email": updated_user.email if updated_user else existing_user.email,
                            "full_name": updated_user.full_name if updated_user else existing_user.full_name,
                            "role": updated_user.role_name if updated_user else existing_user.role_name
                        }
                    }
            
            return {
                "success": True,
                "message": "Usuario ya existe",
                "user": {
                    "id": str(existing_user.id),
                    "email": existing_user.email,
                    "full_name": existing_user.full_name,
                    "role": existing_user.role_name
                }
            }
        
        # Intentar obtener datos de Clerk primero
        clerk_user_data = await clerk_service.get_user_by_id(clerk_id)
        if clerk_user_data:
            user_info = clerk_service.extract_user_info(clerk_user_data)
            logger.info(f"📥 Creando usuario con datos de Clerk: {user_info}")
            new_user = UserCreate(
                clerk_id=clerk_id,
                email=user_info.get("email", user_data.get("email", "")),
                first_name=user_info.get("first_name") or user_data.get("first_name"),
                last_name=user_info.get("last_name") or user_data.get("last_name"),
                full_name=user_info.get("full_name") or user_data.get("full_name"),
                image_url=user_info.get("image_url") or user_data.get("image_url"),
                phone_number=user_info.get("phone_number") or user_data.get("phone_number")
            )
        else:
            # Fallback: usar datos del frontend
            logger.warning(f"⚠️ No se pudieron obtener datos de Clerk, usando datos del frontend")
            new_user = UserCreate(
                clerk_id=clerk_id,
                email=user_data.get("email", ""),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                full_name=user_data.get("full_name"),
                image_url=user_data.get("image_url"),
                phone_number=user_data.get("phone_number")
            )
        
        # Crear nuevo usuario
        created_user = await user_repo.create_user(new_user)
        
        return {
            "success": True,
            "message": "Usuario creado exitosamente",
            "user": {
                "id": str(created_user.id),
                "email": created_user.email,
                "full_name": created_user.full_name,
                "role": created_user.role_name
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en debug_create_user: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/debug/refresh-user-from-clerk/{clerk_id}")
async def debug_refresh_user_from_clerk(clerk_id: str):
    """Endpoint para actualizar un usuario existente con datos frescos de Clerk"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        from ....domain.entities.auth_models import UserUpdate
        from ....infrastructure.services.clerk_service import clerk_service
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        
        # Verificar que el usuario existe
        existing_user = await user_repo.get_user_by_clerk_id(clerk_id)
        if not existing_user:
            return {
                "success": False,
                "message": "Usuario no encontrado en la base de datos"
            }
        
        # Obtener datos actualizados de Clerk
        clerk_user_data = await clerk_service.get_user_by_id(clerk_id)
        if not clerk_user_data:
            return {
                "success": False,
                "message": "No se pudieron obtener datos de Clerk"
            }
        
        user_info = clerk_service.extract_user_info(clerk_user_data)
        
        # Actualizar usuario
        update_data = UserUpdate(
            email=user_info.get("email") or existing_user.email,
            first_name=user_info.get("first_name"),
            last_name=user_info.get("last_name"),
            full_name=user_info.get("full_name"),
            image_url=user_info.get("image_url"),
            phone_number=user_info.get("phone_number")
        )
        
        updated_user = await user_repo.update_user(clerk_id, update_data)
        
        return {
            "success": True,
            "message": "Usuario actualizado con datos de Clerk",
            "user": {
                "id": str(updated_user.id) if updated_user else None,
                "email": updated_user.email if updated_user else None,
                "first_name": updated_user.first_name if updated_user else None,
                "last_name": updated_user.last_name if updated_user else None,
                "full_name": updated_user.full_name if updated_user else None,
                "image_url": updated_user.image_url if updated_user else None,
                "role": updated_user.role_name if updated_user else None
            },
            "clerk_data": user_info
        }
        
    except Exception as e:
        logger.error(f"❌ Error en refresh_user_from_clerk: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/debug/sync-user-role/{clerk_id}")
async def debug_sync_user_role(clerk_id: str):
    """Endpoint de debug para sincronizar role_id con role_name"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        from ....domain.entities.auth_models import UserUpdate
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        
        # Obtener usuario actual
        user = await user_repo.get_user_by_clerk_id(clerk_id)
        if not user:
            return {
                "success": False,
                "message": "Usuario no encontrado"
            }
        
        # Actualizar usando el método que ya sincroniza role_id y role_name
        user_update = UserUpdate(role_name=user.role_name)
        updated_user = await user_repo.update_user(clerk_id, user_update)
        
        if updated_user:
            return {
                "success": True,
                "message": "Usuario sincronizado exitosamente",
                "user": {
                    "id": str(updated_user.id),
                    "email": updated_user.email,
                    "role_name": updated_user.role_name,
                    "role_id": str(updated_user.role_id) if updated_user.role_id else None
                }
            }
        else:
            return {
                "success": False,
                "message": "Error actualizando usuario"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.get("/debug/user/{clerk_id}")
async def debug_get_user_by_clerk_id(clerk_id: str):
    """Endpoint de debug para obtener usuario por clerk_id"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        
        user = await user_repo.get_user_with_role(clerk_id)
        if not user:
            return {
                "success": False,
                "message": "Usuario no encontrado",
                "user": None
            }
        
        return {
            "success": True,
            "message": "Usuario encontrado",
            "user": {
                "id": user.id,
                "clerk_id": user.clerk_id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role_name
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/debug/verify-token")
async def debug_verify_token(request: Request):
    """Endpoint de debug para verificar tokens JWT de Clerk"""
    try:
        from fastapi.security import HTTPBearer
        from fastapi import HTTPException, status
        import jwt
        
        # Obtener token del header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return {
                "success": False,
                "message": "No authorization header found",
                "token_present": False
            }
        
        token = auth_header.split(" ")[1]
        
        # Obtener header del token sin verificar
        try:
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "success": True,
                "message": "Token info extracted (not verified)",
                "token_present": True,
                "header": header,
                "payload": {
                    "sub": payload.get("sub"),
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
                    "exp": payload.get("exp"),
                    "iat": payload.get("iat"),
                    "email": payload.get("email")
                }
            }
        except Exception as decode_error:
            return {
                "success": False,
                "message": f"Token decode error: {str(decode_error)}",
                "token_present": True,
                "token_preview": token[:50] + "..." if len(token) > 50 else token
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/users", response_model=UserResponseDTO)
async def create_user(
    user_data: CreateUserDTO,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case)
):
    """Crear nuevo usuario"""
    try:
        return await use_case.execute(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# Endpoints de IA
@app.get("/ai/welcome")
async def get_welcome_message(
    current_user: User = Depends(verify_active_user),
    use_case: GetWelcomeMessageUseCase = Depends(get_welcome_message_use_case)
):
    """Obtener mensaje de bienvenida de la IA - Requiere usuario activo"""
    try:
        result = await use_case.execute()
        return {
            "message": result["message"],
            "timestamp": "2023-01-01T00:00:00",  # Simplificado para demo
            "service": result["processed_by"],
            "user": current_user.first_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generando mensaje de bienvenida")

@app.post("/ai/message", response_model=MessageResponseDTO)
async def process_message(
    message_data: CreateMessageDTO,
    current_user: User = Depends(verify_permission("ai.process_message")),
    use_case: ProcessAIMessageUseCase = Depends(get_process_ai_message_use_case)
):
    """Procesar mensaje con IA - Requiere permiso ai.process_message"""
    try:
        return await use_case.execute(message_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error procesando mensaje")

# Endpoints adicionales de usuarios para completar CRUD
@app.get("/users")
async def get_users(
    current_user: User = Depends(verify_permission("users.read"))
):
    """Obtener todos los usuarios - Requiere permiso users.read"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        users = await user_repo.list_users()
        
        return [
            {
                "id": user.id,
                "clerk_id": user.clerk_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "image_url": user.image_url,
                "phone_number": user.phone_number,
                "role_name": user.role.get("name") if user.role else "user",
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo usuarios: {str(e)}")

@app.get("/users/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: str,
    current_user: User = Depends(verify_permission("users.read")),
    user_repo: MongoUserRepository = Depends(get_user_repository)
):
    """Obtener usuario por ID - Requiere permiso users.read"""
    try:
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return UserResponseDTO(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error obteniendo usuario")

@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(verify_permission("users.delete")),
    user_repo: MongoUserRepository = Depends(get_user_repository)
):
    """Eliminar usuario por ID - Requiere permiso users.delete"""
    try:
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        await user_repo.delete(user_id)
        return {"message": "Usuario eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error eliminando usuario")

# Endpoints administrativos
@app.get("/admin/dashboard")
async def admin_dashboard(
    current_user: User = Depends(verify_role("admin"))
):
    """Panel administrativo - Solo administradores"""
    try:
        from ....infrastructure.config.database import get_database
        from ....infrastructure.persistence.mongodb.auth_repository_impl import MongoUserRepository
        
        db = get_database()
        user_repo = MongoUserRepository(db)
        
        # Estadísticas básicas
        all_users = await user_repo.list_users()
        total_users = len(all_users)
        
        roles_count = {}
        for user in all_users:
            role_name = user.role.get("name", "sin_rol") if user.role else "sin_rol"
            roles_count[role_name] = roles_count.get(role_name, 0) + 1
        
        return {
            "message": f"Panel administrativo - Bienvenido {current_user.first_name}",
            "stats": {
                "total_users": total_users,
                "roles_distribution": roles_count,
                "admin_user": {
                    "name": current_user.full_name,
                    "email": current_user.email,
                    "role": current_user.role.get("name") if current_user.role else "sin_rol"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en panel administrativo: {str(e)}")

@app.get("/admin/system-info")
async def system_info(
    current_user: User = Depends(verify_permission("system.read"))
):
    """Información del sistema - Requiere permiso system.read"""
    import platform
    import sys
    
    return {
        "system": {
            "platform": platform.system(),
            "python_version": sys.version,
            "user_requesting": current_user.email,
            "user_role": current_user.role.get("name") if current_user.role else "sin_rol"
        },
        "permissions": {
            "user_permissions": current_user.role.get("permissions", []) if current_user.role else [],
            "has_admin_access": current_user.has_permission("admin.full_access") if hasattr(current_user, 'has_permission') else False
        }
    }

@app.get("/profile/me")
async def get_my_profile(
    current_user: User = Depends(verify_active_user)
):
    """Obtener perfil del usuario actual"""
    return {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
            "image_url": current_user.image_url,
            "phone_number": current_user.phone_number,
            "role": {
                "name": current_user.role.get("name") if current_user.role else "user",
                "permissions": current_user.role.get("permissions", []) if current_user.role else []
            },
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
    }

@app.get("/test/permissions")
async def test_permissions(
    current_user: User = Depends(verify_active_user)
):
    """Endpoint de prueba para verificar permisos del usuario"""
    permissions_to_test = [
        "users.read", "users.write", "users.delete",
        "roles.read", "roles.write", "roles.delete",
        "ai.process_message", "system.read", "admin.full_access"
    ]
    
    result = {
        "user": {
            "email": current_user.email,
            "role": current_user.role.get("name") if current_user.role else "sin_rol"
        },
        "permissions_test": {}
    }
    
    user_permissions = current_user.role.get("permissions", []) if current_user.role else []
    for perm in permissions_to_test:
        result["permissions_test"][perm] = perm in user_permissions
    
    return result

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    try:
        from ....infrastructure.config.database import _db_config
        if _db_config:
            _db_config.close_connection()
    except Exception as e:
        pass  # Log si es necesario en producción

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)