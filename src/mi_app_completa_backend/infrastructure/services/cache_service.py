"""
Servicio de caché en memoria para configuraciones de interfaz
FASE 2.2: Implementar sistema de caché
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from ...infrastructure.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Servicio de caché simple en memoria
    Para producción, considerar Redis o Memcached
    """

    def __init__(self, ttl_seconds: int = 300):  # 5 minutos por defecto
        """
        Inicializar servicio de caché

        Args:
            ttl_seconds: Tiempo de vida del caché en segundos
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """
        Obtener valor del caché

        Args:
            key: Clave del caché

        Returns:
            Valor cacheado o None si no existe o expiró
        """
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        expires_at = cache_entry.get('expires_at')

        # Verificar si expiró
        if expires_at and datetime.now(timezone.utc) > expires_at:
            del self._cache[key]
            return None

        return cache_entry.get('value')

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Guardar valor en caché

        Args:
            key: Clave del caché
            value: Valor a cachear
            ttl_seconds: TTL personalizado (usa el default si es None)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now(timezone.utc)
        }

    def delete(self, key: str) -> bool:
        """
        Eliminar entrada del caché

        Args:
            key: Clave a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Limpiar todo el caché"""
        self._cache.clear()
        logger.info("Cache cleared")

    def has(self, key: str) -> bool:
        """
        Verificar si existe una clave (sin considerar expiración)

        Args:
            key: Clave a verificar

        Returns:
            True si existe (aunque haya expirado)
        """
        return key in self._cache

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidar todas las claves que coincidan con un patrón

        Args:
            pattern: Patrón a buscar (simple string matching)

        Returns:
            Número de claves invalidadas
        """
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]

        return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del caché

        Returns:
            Diccionario con estadísticas
        """
        now = datetime.now(timezone.utc)
        active_entries = 0
        expired_entries = 0

        for entry in self._cache.values():
            if entry['expires_at'] > now:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'ttl_seconds': self._ttl_seconds
        }


# Instancia singleton del servicio de caché
# Para configuraciones de interfaz (TTL: 5 minutos)
interface_config_cache = CacheService(ttl_seconds=300)

# Para presets (TTL: 10 minutos - cambian menos frecuentemente)
preset_cache = CacheService(ttl_seconds=600)
