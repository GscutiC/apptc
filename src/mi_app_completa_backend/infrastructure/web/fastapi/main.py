from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List
from ....application.use_cases.create_user import CreateUserUseCase
from ....application.use_cases.process_ai_message import ProcessAIMessageUseCase, GetWelcomeMessageUseCase
from ....application.dto.user_dto import CreateUserDTO, UserResponseDTO
from ....application.dto.message_dto import CreateMessageDTO, MessageResponseDTO
from ....infrastructure.persistence.mongodb.user_repository_impl import MongoUserRepository
from ....infrastructure.persistence.mongodb.message_repository_impl import MongoMessageRepository
from ....infrastructure.services.simple_ai_service import SimpleAIService
from ....infrastructure.config.database import DatabaseConfig
from .auth_routes import router as auth_router

app = FastAPI(
    title="mi_app_completa_backend API",
    description="API con arquitectura hexagonal usando python y mongodb",
    version="1.0.0"
)

# Configurar CORS de manera más segura
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Incluir rutas de autenticación
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# Configuración de dependencias
db_config = DatabaseConfig()

def get_user_repository():
    """Dependency injection para UserRepository"""
    database = db_config.get_database()
    return MongoUserRepository(database)

def get_message_repository():
    """Dependency injection para MessageRepository"""
    database = db_config.get_database()
    return MongoMessageRepository(database)

def get_ai_service():
    """Dependency injection para AIService"""
    return SimpleAIService()

def get_create_user_use_case(user_repo: MongoUserRepository = Depends(get_user_repository)):
    """Dependency injection para CreateUserUseCase"""
    return CreateUserUseCase(user_repo)

def get_process_ai_message_use_case(
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
    return {"status": "healthy", "service": "mi_app_completa_backend"}

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
    use_case: GetWelcomeMessageUseCase = Depends(get_welcome_message_use_case)
):
    """Obtener mensaje de bienvenida de la IA"""
    try:
        result = await use_case.execute()
        return {
            "message": result["message"],
            "timestamp": "2023-01-01T00:00:00",  # Simplificado para demo
            "service": result["processed_by"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generando mensaje de bienvenida")

@app.post("/ai/message", response_model=MessageResponseDTO)
async def process_message(
    message_data: CreateMessageDTO,
    use_case: ProcessAIMessageUseCase = Depends(get_process_ai_message_use_case)
):
    """Procesar mensaje con IA"""
    try:
        return await use_case.execute(message_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error procesando mensaje")

# Endpoints adicionales de usuarios para completar CRUD
@app.get("/users", response_model=List[UserResponseDTO])
async def get_users(
    user_repo: MongoUserRepository = Depends(get_user_repository)
):
    """Obtener todos los usuarios"""
    try:
        # Para simplificar, vamos a implementar esto directamente
        from ....domain.entities.user import User
        users = await user_repo.find_all()
        return [UserResponseDTO(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat() if user.created_at else ""
        ) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error obteniendo usuarios")

@app.get("/users/{user_id}", response_model=UserResponseDTO)
async def get_user(
    user_id: str,
    user_repo: MongoUserRepository = Depends(get_user_repository)
):
    """Obtener usuario por ID"""
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
    user_repo: MongoUserRepository = Depends(get_user_repository)
):
    """Eliminar usuario por ID"""
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

@app.on_event("shutdown")
async def shutdown_event():
    """Cerrar conexiones al apagar la aplicación"""
    db_config.close_connection()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)