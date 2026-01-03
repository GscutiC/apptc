"""
Entidad para manejo de archivos
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class File:
    """Entidad que representa un archivo en el sistema"""
    
    id: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int  # en bytes
    mime_type: str
    file_category: str  # 'logo', 'favicon', 'image', etc.
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    metadata: Optional[dict] = None  # Para datos adicionales como dimensiones
    is_active: bool = True
    
    def __post_init__(self):
        """Validaciones post-inicialización"""
        if not self.id:
            raise ValueError("File ID is required")
        if not self.original_filename:
            raise ValueError("Original filename is required")
        if not self.stored_filename:
            raise ValueError("Stored filename is required")
        if not self.file_path:
            raise ValueError("File path is required")
        if self.file_size <= 0:
            raise ValueError("File size must be positive")
        if not self.mime_type:
            raise ValueError("MIME type is required")
    
    def get_public_url(self, base_url: str) -> str:
        """Generar URL pública para el archivo"""
        return f"{base_url}/api/files/{self.id}"
    
    def is_image(self) -> bool:
        """Verificar si el archivo es una imagen"""
        return self.mime_type.startswith('image/')
    
    def get_file_extension(self) -> str:
        """Obtener extensión del archivo"""
        return self.original_filename.split('.')[-1].lower() if '.' in self.original_filename else ''
    
    def update_metadata(self, **kwargs):
        """Actualizar metadatos del archivo"""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update(kwargs)
        self.updated_at = datetime.utcnow()