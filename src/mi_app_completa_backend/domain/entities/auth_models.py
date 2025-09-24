from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler):
        from pydantic_core import core_schema
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.chain_schema([
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(cls.validate),
                ])
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                str,
                return_schema=core_schema.str_schema(),
                when_used='json',
            ),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class Role(BaseModel):
    """Modelo para roles del sistema"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    """Modelo para usuarios sincronizados desde Clerk"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    clerk_id: str = Field(..., unique=True)  # ID de Clerk
    email: str = Field(...)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    full_name: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    phone_number: Optional[str] = Field(None)
    role_id: Optional[PyObjectId] = Field(None)  # Referencia al rol
    role_name: str = Field(default="user")  # Nombre del rol para fácil acceso
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = Field(None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    """Modelo para crear usuarios desde webhooks de Clerk"""
    clerk_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    image_url: Optional[str] = None
    phone_number: Optional[str] = None

class UserUpdate(BaseModel):
    """Modelo para actualizar usuarios"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    image_url: Optional[str] = None
    phone_number: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserWithRole(BaseModel):
    """Modelo de usuario con información completa del rol"""
    id: str
    clerk_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    image_url: Optional[str]
    phone_number: Optional[str]
    role: Optional[dict] = None  # Información completa del rol
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}