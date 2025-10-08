#!/usr/bin/env python3
"""
Script de inicio para el backend FastAPI con soporte para múltiples entornos
"""
import sys
import os
import argparse
from pathlib import Path

# Agregar el directorio src al path de Python
backend_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(backend_dir, 'src')
sys.path.insert(0, src_dir)


def parse_arguments():
    """Parsear argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description="Iniciar el servidor FastAPI")
    parser.add_argument(
        '--env', 
        choices=['development', 'production'],
        default='development',
        help='Entorno de ejecución (default: development)'
    )
    parser.add_argument(
        '--env-file',
        type=str,
        help='Ruta a archivo .env específico'
    )
    parser.add_argument(
        '--host',
        type=str,
        help='Host del servidor (sobrescribe configuración)'
    )
    parser.add_argument(
        '--port',
        type=int,
        help='Puerto del servidor (sobrescribe configuración)'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Activar modo reload (solo para desarrollo)'
    )
    return parser.parse_args()


def setup_environment(args):
    """Configurar el entorno basado en argumentos"""
    # Establecer variable de entorno ENVIRONMENT
    os.environ['ENVIRONMENT'] = args.env
    
    # Si se especifica un archivo .env personalizado, configurarlo
    if args.env_file:
        env_file_path = Path(args.env_file)
        if not env_file_path.exists():
            print(f"Error: El archivo .env especificado no existe: {args.env_file}")
            sys.exit(1)
        os.environ['CUSTOM_ENV_FILE'] = str(env_file_path)


if __name__ == "__main__":
    args = parse_arguments()
    
    # Configurar entorno
    setup_environment(args)
    
    # Importar configuración después de establecer el entorno
    from mi_app_completa_backend.infrastructure.config.settings import settings
    import uvicorn
    
    # Usar argumentos de CLI si se proporcionan, sino usar configuración
    host = args.host if args.host else settings.api_host
    port = args.port if args.port else settings.api_port
    
    # El modo reload solo está disponible en desarrollo
    reload_mode = False
    if args.env == 'development':
        reload_mode = args.reload or settings.debug
    
    # Configurar directorios de reload solo en desarrollo
    reload_dirs = [src_dir] if reload_mode else None
    
    print(f"[SERVER] Iniciando servidor en modo {args.env}")
    print(f"[URL] http://{host}:{port}")
    print(f"[RELOAD] {'Activado' if reload_mode else 'Desactivado'}")
    print(f"[DEBUG] {'Activado' if settings.debug else 'Desactivado'}")
    
    uvicorn.run(
        "mi_app_completa_backend.infrastructure.web.fastapi.main:app",
        host=host,
        port=port,
        reload=reload_mode,
        reload_dirs=reload_dirs
    )