"""
Servicio para manejo de imágenes usando Cloudinary
Reemplaza el almacenamiento local de archivos
"""

import os
from typing import Optional, Dict, Any
import cloudinary
import cloudinary.uploader
import cloudinary.api
from fastapi import UploadFile, HTTPException


class CloudinaryService:
    """
    Servicio para subir y gestionar imágenes en Cloudinary
    """

    def __init__(self):
        """Inicializa la configuración de Cloudinary desde variables de entorno"""
        self.cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        self.api_key = os.getenv('CLOUDINARY_API_KEY')
        self.api_secret = os.getenv('CLOUDINARY_API_SECRET')

        if not all([self.cloud_name, self.api_key, self.api_secret]):
            raise ValueError(
                "Cloudinary credentials not configured. "
                "Please set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET"
            )

        # Configurar Cloudinary
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True
        )

    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "apptc",
        public_id: Optional[str] = None,
        overwrite: bool = True,
        resource_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Sube una imagen a Cloudinary

        Args:
            file: Archivo a subir
            folder: Carpeta en Cloudinary donde se guardará
            public_id: ID público para la imagen (opcional)
            overwrite: Si debe sobrescribir archivo existente
            resource_type: Tipo de recurso (image, video, raw, auto)

        Returns:
            Dict con información de la imagen subida:
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
            # Validar tipo de archivo
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.content_type}. Only images are allowed."
                )

            # Leer contenido del archivo
            contents = await file.read()

            # Opciones de upload
            upload_options = {
                "folder": folder,
                "overwrite": overwrite,
                "resource_type": resource_type,
                "invalidate": True  # Invalidar CDN cache si existe
            }

            if public_id:
                upload_options["public_id"] = public_id

            # Subir a Cloudinary
            result = cloudinary.uploader.upload(contents, **upload_options)

            # Retornar información relevante
            return {
                "public_id": result.get("public_id"),
                "url": result.get("url"),
                "secure_url": result.get("secure_url"),
                "format": result.get("format"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes"),
                "created_at": result.get("created_at")
            }

        except cloudinary.exceptions.Error as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cloudinary upload error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error uploading image: {str(e)}"
            )

    async def delete_image(self, public_id: str) -> bool:
        """
        Elimina una imagen de Cloudinary

        Args:
            public_id: ID público de la imagen a eliminar

        Returns:
            True si se eliminó correctamente
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result.get("result") == "ok"
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {e}")
            return False

    def get_image_url(
        self,
        public_id: str,
        transformation: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera URL de imagen con transformaciones opcionales

        Args:
            public_id: ID público de la imagen
            transformation: Transformaciones a aplicar (ej: {"width": 300, "height": 300, "crop": "fill"})

        Returns:
            URL segura de la imagen
        """
        try:
            if transformation:
                url, _ = cloudinary.utils.cloudinary_url(
                    public_id,
                    transformation=transformation,
                    secure=True
                )
                return url
            else:
                url, _ = cloudinary.utils.cloudinary_url(public_id, secure=True)
                return url
        except Exception as e:
            print(f"Error generating Cloudinary URL: {e}")
            return ""

    async def upload_logo(
        self,
        file: UploadFile,
        logo_type: str = "primary"  # primary, secondary, favicon
    ) -> Dict[str, Any]:
        """
        Sube un logo con configuración específica

        Args:
            file: Archivo del logo
            logo_type: Tipo de logo (primary, secondary, favicon)

        Returns:
            Dict con información del logo subido
        """
        folder = f"apptc/logos/{logo_type}"
        public_id = f"{logo_type}_logo"

        return await self.upload_image(
            file=file,
            folder=folder,
            public_id=public_id,
            overwrite=True
        )


# Instancia singleton del servicio
cloudinary_service = CloudinaryService()
