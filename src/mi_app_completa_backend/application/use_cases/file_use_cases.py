"""
Casos de uso para manejo de archivos
"""

import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional, List, BinaryIO
from pathlib import Path

from ..dto.file_dto import (
    FileResponseDTO, FileUploadResponseDTO, FileListResponseDTO, 
    FileUpdateDTO, ErrorResponseDTO
)
from ...domain.entities.file_entity import File
from ...domain.repositories.file_repository import FileRepository
from ...infrastructure.config.settings import Settings


class FileUseCases:
    """Casos de uso para manejo de archivos"""
    
    def __init__(
        self, 
        file_repository: FileRepository, 
        settings: Settings,
        upload_dir: str = "uploads"
    ):
        self.file_repository = file_repository
        self.settings = settings
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # Crear subdirectorios
        (self.upload_dir / "logos").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)
    
    async def upload_file(
        self, 
        file_content: bytes, 
        original_filename: str,
        mime_type: str,
        category: str = 'image',
        created_by: Optional[str] = None
    ) -> FileUploadResponseDTO:
        """Subir y guardar archivo"""
        
        # Validar el archivo
        self._validate_file(file_content, original_filename, mime_type, category)
        
        # Generar ID único y nombre de archivo
        file_id = str(uuid.uuid4())
        file_extension = self._get_file_extension(original_filename)
        stored_filename = f"{file_id}.{file_extension}"
        
        # Determinar directorio según categoría
        category_dir = self.upload_dir / self._get_category_dir(category)
        category_dir.mkdir(exist_ok=True)
        
        file_path = category_dir / stored_filename
        
        try:
            # Guardar archivo físico
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Crear entidad File
            file_entity = File(
                id=file_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=len(file_content),
                mime_type=mime_type,
                file_category=category,
                created_at=datetime.utcnow(),
                created_by=created_by,
                metadata=self._extract_metadata(file_content, mime_type)
            )
            
            # Guardar en repositorio
            saved_file = await self.file_repository.save_file(file_entity)
            
            return FileUploadResponseDTO(
                id=saved_file.id,
                original_filename=saved_file.original_filename,
                file_size=saved_file.file_size,
                mime_type=saved_file.mime_type,
                public_url=self._generate_public_url(saved_file.id)
            )
            
        except Exception as e:
            # Limpiar archivo si falló el guardado
            if file_path.exists():
                file_path.unlink()
            raise Exception(f"Error uploading file: {str(e)}")
    
    async def get_file(self, file_id: str) -> Optional[FileResponseDTO]:
        """Obtener información de archivo por ID"""
        file_entity = await self.file_repository.get_file_by_id(file_id)
        if not file_entity:
            return None
        
        return self._file_to_response_dto(file_entity)
    
    async def get_file_content(self, file_id: str) -> Optional[tuple[bytes, str, str]]:
        """Obtener contenido del archivo para servir"""
        file_entity = await self.file_repository.get_file_by_id(file_id)
        if not file_entity or not file_entity.is_active:
            return None
        
        file_path = Path(file_entity.file_path)
        if not file_path.exists():
            return None
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
            
            return content, file_entity.mime_type, file_entity.original_filename
        except Exception:
            return None
    
    async def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo"""
        file_entity = await self.file_repository.get_file_by_id(file_id)
        if not file_entity:
            return False
        
        try:
            # Eliminar archivo físico
            file_path = Path(file_entity.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # Eliminar del repositorio
            return await self.file_repository.delete_file(file_id)
        except Exception:
            return False
    
    async def update_file(self, file_id: str, update_data: FileUpdateDTO) -> Optional[FileResponseDTO]:
        """Actualizar metadatos del archivo"""
        file_entity = await self.file_repository.get_file_by_id(file_id)
        if not file_entity:
            return None
        
        # Actualizar campos
        if update_data.file_category is not None:
            file_entity.file_category = update_data.file_category
        if update_data.metadata is not None:
            file_entity.metadata = update_data.metadata
        if update_data.is_active is not None:
            file_entity.is_active = update_data.is_active
        
        file_entity.updated_at = datetime.utcnow()
        
        updated_file = await self.file_repository.update_file(file_entity)
        return self._file_to_response_dto(updated_file)
    
    async def list_files(
        self, 
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> FileListResponseDTO:
        """Listar archivos con paginación"""
        offset = (page - 1) * page_size
        
        if category:
            files = await self.file_repository.get_files_by_category(category)
        else:
            files = await self.file_repository.get_all_files(limit=page_size, offset=offset)
        
        total_files = len(files) if category else len(await self.file_repository.get_all_files())
        total_pages = (total_files + page_size - 1) // page_size
        
        file_dtos = [self._file_to_response_dto(f) for f in files[offset:offset + page_size]]
        
        return FileListResponseDTO(
            files=file_dtos,
            total=total_files,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    # Métodos privados de utilidad
    
    def _validate_file(self, content: bytes, filename: str, mime_type: str, category: str):
        """Validar archivo subido"""
        # Validar tamaño
        max_sizes = {
            'logo': 1 * 1024 * 1024,      # 1MB para logos
            'favicon': 512 * 1024,         # 512KB para favicons
            'image': 2 * 1024 * 1024,      # 2MB para otras imágenes
            'document': 5 * 1024 * 1024    # 5MB para documentos
        }
        
        max_size = max_sizes.get(category, 1 * 1024 * 1024)
        if len(content) > max_size:
            raise ValueError(f"File too large. Maximum size for {category}: {max_size // (1024*1024)}MB")
        
        # Validar tipo MIME
        allowed_types = {
            'logo': ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'],
            'favicon': ['image/png', 'image/x-icon', 'image/vnd.microsoft.icon'],
            'image': ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/svg+xml'],
            'document': ['application/pdf', 'text/plain']
        }
        
        category_types = allowed_types.get(category, allowed_types['image'])
        if mime_type not in category_types:
            raise ValueError(f"Invalid file type for {category}. Allowed: {category_types}")
        
        # Validar nombre de archivo
        if not filename or len(filename) > 255:
            raise ValueError("Invalid filename")
    
    def _get_file_extension(self, filename: str) -> str:
        """Obtener extensión del archivo"""
        return filename.split('.')[-1].lower() if '.' in filename else 'bin'
    
    def _get_category_dir(self, category: str) -> str:
        """Obtener directorio según categoría"""
        category_dirs = {
            'logo': 'logos',
            'favicon': 'logos',
            'image': 'logos',
            'document': 'documents'
        }
        return category_dirs.get(category, 'temp')
    
    def _generate_public_url(self, file_id: str) -> str:
        """Generar URL pública para el archivo usando configuración centralizada"""
        base_url = self.settings.base_url.rstrip('/')
        return f"{base_url}/api/files/{file_id}"
    
    def _extract_metadata(self, content: bytes, mime_type: str) -> dict:
        """Extraer metadatos del archivo"""
        metadata = {
            'size_bytes': len(content),
            'uploaded_at': datetime.utcnow().isoformat()
        }
        
        # Para imágenes, podríamos extraer dimensiones aquí
        if mime_type.startswith('image/'):
            metadata['is_image'] = True
            # TODO: Agregar extracción de dimensiones con PIL si es necesario
        
        return metadata
    
    def _file_to_response_dto(self, file_entity: File) -> FileResponseDTO:
        """Convertir entidad File a DTO de respuesta"""
        return FileResponseDTO(
            id=file_entity.id,
            original_filename=file_entity.original_filename,
            stored_filename=file_entity.stored_filename,
            file_size=file_entity.file_size,
            mime_type=file_entity.mime_type,
            file_category=file_entity.file_category,
            public_url=self._generate_public_url(file_entity.id),
            created_at=file_entity.created_at,
            updated_at=file_entity.updated_at,
            created_by=file_entity.created_by,
            metadata=file_entity.metadata,
            is_active=file_entity.is_active
        )