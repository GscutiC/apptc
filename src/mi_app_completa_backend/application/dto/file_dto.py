"""
DTOs para manejo de archivos
"""

from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
from datetime import datetime


class FileUploadRequest(BaseModel):
    """DTO para solicitud de subida de archivo"""
    category: str = 'image'
    description: Optional[str] = None
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = ['logo', 'favicon', 'image', 'document']
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {allowed_categories}')
        return v


class FileResponseDTO(BaseModel):
    """DTO para respuesta de archivo"""
    id: str
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    file_category: str
    public_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True


class FileListResponseDTO(BaseModel):
    """DTO para respuesta de lista de archivos"""
    files: list[FileResponseDTO]
    total: int
    page: int
    page_size: int
    total_pages: int


class FileUpdateDTO(BaseModel):
    """DTO para actualización de archivo"""
    description: Optional[str] = None
    file_category: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator('file_category')
    def validate_category(cls, v):
        if v is not None:
            allowed_categories = ['logo', 'favicon', 'image', 'document']
            if v not in allowed_categories:
                raise ValueError(f'Category must be one of: {allowed_categories}')
        return v


class FileUploadResponseDTO(BaseModel):
    """DTO específico para respuesta de upload exitoso"""
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    public_url: str
    message: str = "File uploaded successfully"


class ErrorResponseDTO(BaseModel):
    """DTO para respuestas de error"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None