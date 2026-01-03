"""
Sistema de logging centralizado
Configura logging basado en variable de entorno DEBUG
"""
import logging
import os
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger configurado según modo DEBUG

    Args:
        name: Nombre del logger (usualmente __name__)

    Returns:
        Logger configurado con nivel apropiado
    """
    logger = logging.getLogger(name)

    # Configurar solo si no está configurado previamente
    if not logger.handlers:
        handler = logging.StreamHandler()

        # Determinar nivel según variable de entorno
        debug_mode = os.getenv("DEBUG", "False").lower() == "true"
        level = logging.DEBUG if debug_mode else logging.WARNING

        # Formato simple pero informativo
        formatter = logging.Formatter(
            '%(levelname)s: %(name)s - %(message)s'
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger
