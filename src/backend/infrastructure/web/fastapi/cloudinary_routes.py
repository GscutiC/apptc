"""
Rutas FastAPI para el servicio de Cloudinary
Reemplaza file_routes.py para usar Cloudinary en lugar de almacenamiento local
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from typing import Optional

from ...services.cloudinary_service import cloudinary_service
from .auth_dependencies import get_current_user
from ....domain.entities.auth_models import User


# Router
router = APIRouter(prefix="/api/cloudinary", tags=["Cloudinary"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    folder: str = Query(default="apptc", description="Folder in Cloudinary"),
    current_user: User = Depends(get_current_user)
):
    """
    Sube una imagen a Cloudinary
    🔐 REQUIERE AUTENTICACIÓN

    Args:
        file: Archivo de imagen a subir
        folder: Carpeta en Cloudinary (default: apptc)

    Returns:
        {
            "public_id": str,
            "url": str,
            "secure_url": str,
            "format": str,
            "width": int,
            "height": int,
            "bytes": int
        }
    """
    try:
        result = await cloudinary_service.upload_image(file=file, folder=folder)
        return {
            "success": True,
            "message": "Image uploaded successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading to Cloudinary: {str(e)}"
        )


@router.post("/upload-logo")
async def upload_logo(
    file: UploadFile = File(...),
    logo_type: str = Query(
        default="primary",
        description="Logo type: primary, secondary, favicon"
    ),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un logo a Cloudinary con configuración específica
    🔐 REQUIERE AUTENTICACIÓN

    Args:
        file: Archivo de logo
        logo_type: Tipo de logo (primary, secondary, favicon)

    Returns:
        {
            "public_id": str,
            "url": str,
            "secure_url": str,
            ...
        }
    """
    try:
        result = await cloudinary_service.upload_logo(file=file, logo_type=logo_type)
        return {
            "success": True,
            "message": f"{logo_type.capitalize()} logo uploaded successfully",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading logo to Cloudinary: {str(e)}"
        )


@router.delete("/delete/{public_id:path}")
async def delete_image(
    public_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Elimina una imagen de Cloudinary
    🔐 REQUIERE AUTENTICACIÓN

    Args:
        public_id: ID público de la imagen en Cloudinary (puede incluir carpetas, ej: apptc/logos/primary_logo)

    Returns:
        {"success": bool, "message": str}
    """
    try:
        success = await cloudinary_service.delete_image(public_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Image not found or could not be deleted"
            )

        return {
            "success": True,
            "message": "Image deleted successfully",
            "public_id": public_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting from Cloudinary: {str(e)}"
        )


@router.get("/url/{public_id:path}")
async def get_image_url(
    public_id: str,
    width: Optional[int] = Query(default=None, description="Image width"),
    height: Optional[int] = Query(default=None, description="Image height"),
    crop: Optional[str] = Query(default=None, description="Crop mode: fill, fit, scale, etc.")
):
    """
    Obtiene URL de una imagen con transformaciones opcionales
    ⚠️ Endpoint público (no requiere autenticación)

    Args:
        public_id: ID público de la imagen
        width: Ancho deseado (opcional)
        height: Alto deseado (opcional)
        crop: Modo de recorte (opcional)

    Returns:
        {"url": str, "public_id": str}
    """
    try:
        transformation = None
        if width or height or crop:
            transformation = {}
            if width:
                transformation["width"] = width
            if height:
                transformation["height"] = height
            if crop:
                transformation["crop"] = crop

        url = cloudinary_service.get_image_url(public_id, transformation)

        if not url:
            raise HTTPException(status_code=404, detail="Image not found")

        return {
            "url": url,
            "public_id": public_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating Cloudinary URL: {str(e)}"
        )


@router.get("/health")
async def cloudinary_health_check():
    """Health check para el servicio de Cloudinary"""
    try:
        # Verificar que las credenciales están configuradas
        cloud_name = cloudinary_service.cloud_name

        return {
            "status": "healthy",
            "service": "cloudinary_service",
            "cloud_name": cloud_name,
            "configured": bool(cloud_name)
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Cloudinary service unhealthy: {str(e)}"
        )
