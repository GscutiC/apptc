"""
Implementación del repositorio de archivos usando MongoDB y sistema de archivos
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ...domain.entities.file_entity import File
from ...domain.repositories.file_repository import FileRepository


class FileSystemFileRepository(FileRepository):
    """Implementación del repositorio de archivos usando archivos JSON como almacén de metadatos"""
    
    def __init__(self, metadata_file: str = "file_metadata.json"):
        self.metadata_file = Path(metadata_file)
        self._ensure_metadata_file()
    
    def _ensure_metadata_file(self):
        """Asegurar que existe el archivo de metadatos"""
        if not self.metadata_file.exists():
            self._save_metadata({})
    
    def _load_metadata(self) -> dict:
        """Cargar metadatos desde archivo"""
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_metadata(self, metadata: dict):
        """Guardar metadatos a archivo"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str, ensure_ascii=False)
    
    def _dict_to_file(self, data: dict) -> File:
        """Convertir diccionario a entidad File"""
        return File(
            id=data['id'],
            original_filename=data['original_filename'],
            stored_filename=data['stored_filename'],
            file_path=data['file_path'],
            file_size=data['file_size'],
            mime_type=data['mime_type'],
            file_category=data['file_category'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            created_by=data.get('created_by'),
            metadata=data.get('metadata'),
            is_active=data.get('is_active', True)
        )
    
    def _file_to_dict(self, file: File) -> dict:
        """Convertir entidad File a diccionario"""
        return {
            'id': file.id,
            'original_filename': file.original_filename,
            'stored_filename': file.stored_filename,
            'file_path': file.file_path,
            'file_size': file.file_size,
            'mime_type': file.mime_type,
            'file_category': file.file_category,
            'created_at': file.created_at.isoformat(),
            'updated_at': file.updated_at.isoformat() if file.updated_at else None,
            'created_by': file.created_by,
            'metadata': file.metadata,
            'is_active': file.is_active
        }
    
    async def save_file(self, file: File) -> File:
        """Guardar archivo en el repositorio"""
        metadata = self._load_metadata()
        metadata[file.id] = self._file_to_dict(file)
        self._save_metadata(metadata)
        return file
    
    async def get_file_by_id(self, file_id: str) -> Optional[File]:
        """Obtener archivo por ID"""
        metadata = self._load_metadata()
        file_data = metadata.get(file_id)
        
        if not file_data:
            return None
        
        return self._dict_to_file(file_data)
    
    async def get_files_by_category(self, category: str) -> List[File]:
        """Obtener archivos por categoría"""
        metadata = self._load_metadata()
        files = []
        
        for file_data in metadata.values():
            if file_data.get('file_category') == category and file_data.get('is_active', True):
                files.append(self._dict_to_file(file_data))
        
        return files
    
    async def get_files_by_user(self, user_id: str) -> List[File]:
        """Obtener archivos de un usuario"""
        metadata = self._load_metadata()
        files = []
        
        for file_data in metadata.values():
            if file_data.get('created_by') == user_id and file_data.get('is_active', True):
                files.append(self._dict_to_file(file_data))
        
        return files
    
    async def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo del repositorio"""
        metadata = self._load_metadata()
        
        if file_id in metadata:
            del metadata[file_id]
            self._save_metadata(metadata)
            return True
        
        return False
    
    async def update_file(self, file: File) -> File:
        """Actualizar información del archivo"""
        metadata = self._load_metadata()
        
        if file.id not in metadata:
            raise ValueError(f"File with id {file.id} not found")
        
        metadata[file.id] = self._file_to_dict(file)
        self._save_metadata(metadata)
        return file
    
    async def file_exists(self, file_id: str) -> bool:
        """Verificar si un archivo existe"""
        metadata = self._load_metadata()
        return file_id in metadata and metadata[file_id].get('is_active', True)
    
    async def get_all_files(self, limit: int = 100, offset: int = 0) -> List[File]:
        """Obtener todos los archivos con paginación"""
        metadata = self._load_metadata()
        files = []
        
        active_files = [
            file_data for file_data in metadata.values() 
            if file_data.get('is_active', True)
        ]
        
        # Ordenar por fecha de creación (más recientes primero)
        active_files.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Aplicar paginación
        paginated_files = active_files[offset:offset + limit]
        
        for file_data in paginated_files:
            files.append(self._dict_to_file(file_data))
        
        return files
    
    async def cleanup_inactive_files(self) -> int:
        """Limpiar archivos inactivos y retornar cantidad eliminada"""
        metadata = self._load_metadata()
        initial_count = len(metadata)
        
        # Filtrar solo archivos activos
        active_metadata = {
            file_id: file_data for file_id, file_data in metadata.items()
            if file_data.get('is_active', True)
        }
        
        self._save_metadata(active_metadata)
        return initial_count - len(active_metadata)