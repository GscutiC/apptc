from datetime import datetime
from pydantic import BaseModel, field_validator
import re

class CreateUserDTO(BaseModel):
    """DTO para crear usuario"""
    name: str
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Email format is invalid')
        return v

class UpdateUserDTO(BaseModel):
    """DTO para actualizar usuario"""
    name: str = None
    email: str = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None:
            return v
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Email format is invalid')
        return v

class UserResponseDTO(BaseModel):
    """DTO de respuesta de usuario"""
    id: str
    name: str
    email: str
    created_at: str

    class Config:
        from_attributes = True