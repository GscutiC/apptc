"""
Rutas FastAPI para el servicio de archivos
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import Response
from typing import Optional, List
import mimetypes

from ....application.use_cases.file_use_cases import FileUseCases
from ....application.dto.file_dto import (
    FileResponseDTO, FileUploadResponseDTO, FileListResponseDTO,
    FileUpdateDTO, ErrorResponseDTO, FileUploadRequest
)
from ...persistence.file_repository import FileSystemFileRepository


# Crear instancias
file_repository = FileSystemFileRepository("file_metadata.json")
file_use_cases = FileUseCases(file_repository, "uploads")

# Router
router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=FileUploadResponseDTO)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Query(default="image", description="File category: logo, favicon, image, document"),
    description: Optional[str] = Query(default=None, description="File description")
):
    """
    Subir un archivo al servidor
    
    - **file**: Archivo a subir
    - **category**: Categoría del archivo (logo, favicon, image, document)
    - **description**: Descripción opcional del archivo
    """
    try:
        # Leer contenido del archivo
        content = await file.read()
        
        # Determinar MIME type
        mime_type = file.content_type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                mime_type = 'application/octet-stream'
        
        # Subir archivo usando casos de uso
        result = await file_use_cases.upload_file(
            file_content=content,
            original_filename=file.filename or "unnamed_file",
            mime_type=mime_type,
            category=category,
            created_by=None  # TODO: Obtener del contexto de autenticación
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.get("/{file_id}")
async def get_file(file_id: str):
    """
    Servir archivo por ID
    
    - **file_id**: ID único del archivo
    """
    try:
        file_data = await file_use_cases.get_file_content(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")
        
        content, mime_type, filename = file_data
        
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Cache-Control": "public, max-age=86400"  # Cache por 1 día
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


@router.get("/{file_id}/info", response_model=FileResponseDTO)
async def get_file_info(file_id: str):
    """
    Obtener información de un archivo sin descargarlo
    
    - **file_id**: ID único del archivo
    """
    try:
        file_info = await file_use_cases.get_file(file_id)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    Eliminar un archivo
    
    - **file_id**: ID único del archivo
    """
    try:
        success = await file_use_cases.delete_file(file_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="File not found or could not be deleted")
        
        return {"message": "File deleted successfully", "file_id": file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.patch("/{file_id}", response_model=FileResponseDTO)
async def update_file_metadata(file_id: str, update_data: FileUpdateDTO):
    """
    Actualizar metadatos de un archivo
    
    - **file_id**: ID único del archivo
    - **update_data**: Datos a actualizar
    """
    try:
        updated_file = await file_use_cases.update_file(file_id, update_data)
        
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")
        
        return updated_file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating file: {str(e)}")


@router.get("/", response_model=FileListResponseDTO)
async def list_files(
    category: Optional[str] = Query(default=None, description="Filter by category"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    """
    Listar archivos con filtros y paginación
    
    - **category**: Filtrar por categoría (opcional)
    - **page**: Número de página
    - **page_size**: Elementos por página (máximo 100)
    """
    try:
        files_list = await file_use_cases.list_files(
            category=category,
            page=page,
            page_size=page_size
        )
        
        return files_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@router.post("/cleanup")
async def cleanup_files():
    """
    Limpiar archivos inactivos del sistema
    (Solo para administradores)
    """
    try:
        # TODO: Agregar verificación de permisos de administrador
        
        deleted_count = await file_use_cases.file_repository.cleanup_inactive_files()
        
        return {
            "message": "Cleanup completed successfully",
            "deleted_files": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")


# Endpoint de health check específico para files
@router.get("/health/check")
async def files_health_check():
    """Health check para el servicio de archivos"""
    try:
        # Verificar que el directorio de uploads existe
        uploads_dir = file_use_cases.upload_dir
        
        return {
            "status": "healthy",
            "service": "file_service",
            "uploads_directory": str(uploads_dir),
            "uploads_directory_exists": uploads_dir.exists(),
            "timestamp": str(file_use_cases.file_repository._load_metadata())
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"File service unhealthy: {str(e)}")