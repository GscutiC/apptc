#!/usr/bin/env python3
"""
Script de inicio simple para el backend FastAPI
"""
import sys
import os

# Agregar el directorio src al path de Python
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    import uvicorn
    from mi_app_completa_backend.infrastructure.web.fastapi.main import app
    
    # Configurar para desarrollo sin base de datos por ahora
    os.environ.setdefault('MONGODB_URL', 'mongodb://localhost:27017')
    os.environ.setdefault('DATABASE_NAME', 'test_db')
    # Configurar Clerk (deberás reemplazar con tus claves reales)
    os.environ.setdefault('CLERK_SECRET_KEY', 'tu_clerk_secret_key_aqui')
    os.environ.setdefault('CLERK_WEBHOOK_SECRET', 'tu_webhook_secret_aqui')
    
    uvicorn.run(
        "mi_app_completa_backend.infrastructure.web.fastapi.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[src_dir]
    )