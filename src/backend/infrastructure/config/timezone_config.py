"""
Configuración centralizada de zona horaria para el sistema AppTc
Zona horaria oficial: America/Lima (Perú) - UTC-5

Este módulo proporciona funciones helper para manejar fechas y horas
con conciencia de zona horaria (timezone-aware) en todo el sistema.

REGLAS DE ORO:
1. Siempre usar funciones de este módulo (nunca datetime.now() directo)
2. Almacenar en UTC, mostrar en Lima
3. Todas las fechas deben ser timezone-aware

Autor: Sistema Backend AppTc
Fecha: 2025-10-11
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

# ============================================================================
# CONSTANTES - Zonas Horarias
# ============================================================================

# Zona horaria de Perú (UTC-5)
LIMA_TZ = ZoneInfo("America/Lima")

# Zona horaria UTC estándar
UTC_TZ = timezone.utc


# ============================================================================
# FUNCIONES PRINCIPALES - Obtener Datetime Actual
# ============================================================================

def get_lima_timezone() -> ZoneInfo:
    """
    Obtener el objeto ZoneInfo para Lima, Perú
    
    Returns:
        ZoneInfo: Zona horaria de Lima (UTC-5)
        
    Example:
        >>> tz = get_lima_timezone()
        >>> print(tz)  # zoneinfo.ZoneInfo(key='America/Lima')
    """
    return LIMA_TZ


def lima_now() -> datetime:
    """
    Obtener la fecha y hora actual en zona horaria de Lima (Perú)
    
    Esta es la función principal para obtener el tiempo actual en la
    zona horaria local del sistema. Usar para lógica de negocio que
    requiere hora local peruana.
    
    Returns:
        datetime: Datetime actual con timezone de Lima (UTC-5)
        
    Example:
        >>> now = lima_now()
        >>> print(now)  # 2025-10-11 15:30:00-05:00
        >>> print(now.tzinfo)  # America/Lima
        
    Use Cases:
        - Fechas límite de convocatorias
        - Validaciones de DNI con fecha actual
        - Logs que necesitan hora local
        - Timestamps visibles para usuarios peruanos
    """
    return datetime.now(LIMA_TZ)


def utc_now() -> datetime:
    """
    Obtener la fecha y hora actual en UTC (timezone-aware)
    
    Esta función debe usarse para almacenamiento en base de datos.
    UTC es el estándar internacional y facilita:
    - Migraciones futuras
    - Sistemas multi-timezone
    - Sincronización entre servicios
    
    Returns:
        datetime: Datetime actual en UTC con timezone
        
    Example:
        >>> now = utc_now()
        >>> print(now)  # 2025-10-11 20:30:00+00:00
        >>> print(now.tzinfo)  # UTC
        
    Use Cases:
        - Almacenar created_at en MongoDB
        - Almacenar updated_at en base de datos
        - Timestamps para auditoría
        - Sincronización con APIs externas
    """
    return datetime.now(UTC_TZ)


# ============================================================================
# FUNCIONES DE CONVERSIÓN - Entre Zonas Horarias
# ============================================================================

def to_lima_time(dt: datetime) -> datetime:
    """
    Convertir un datetime a zona horaria de Lima
    
    Maneja automáticamente:
    - Datetime timezone-aware (convierte directamente)
    - Datetime naive (asume UTC y luego convierte)
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
        
    Returns:
        datetime: Datetime en zona horaria de Lima
        
    Examples:
        >>> # Desde UTC aware
        >>> utc_dt = datetime(2025, 10, 11, 20, 30, tzinfo=timezone.utc)
        >>> lima_dt = to_lima_time(utc_dt)
        >>> print(lima_dt)  # 2025-10-11 15:30:00-05:00
        
        >>> # Desde naive (asume UTC)
        >>> naive_dt = datetime(2025, 10, 11, 20, 30)
        >>> lima_dt = to_lima_time(naive_dt)
        >>> print(lima_dt)  # 2025-10-11 15:30:00-05:00
        
    Use Cases:
        - Convertir timestamps de MongoDB a hora local
        - Preparar fechas para mostrar en frontend
        - Formatear respuestas de API en hora peruana
    """
    if dt.tzinfo is None:
        # Si es naive, asumimos que está en UTC
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(LIMA_TZ)


def to_utc_time(dt: datetime) -> datetime:
    """
    Convertir un datetime a UTC
    
    Maneja automáticamente:
    - Datetime timezone-aware (convierte directamente)
    - Datetime naive (asume Lima y luego convierte)
    
    Args:
        dt: Datetime a convertir (puede ser naive o aware)
        
    Returns:
        datetime: Datetime en UTC
        
    Examples:
        >>> # Desde Lima aware
        >>> lima_dt = datetime(2025, 10, 11, 15, 30, tzinfo=ZoneInfo("America/Lima"))
        >>> utc_dt = to_utc_time(lima_dt)
        >>> print(utc_dt)  # 2025-10-11 20:30:00+00:00
        
        >>> # Desde naive (asume Lima)
        >>> naive_dt = datetime(2025, 10, 11, 15, 30)
        >>> utc_dt = to_utc_time(naive_dt)
        >>> print(utc_dt)  # 2025-10-11 20:30:00+00:00
        
    Use Cases:
        - Preparar fechas para almacenar en MongoDB
        - Convertir input de usuario (en Lima) a UTC
        - Sincronizar con servicios externos en UTC
    """
    if dt.tzinfo is None:
        # Si es naive, asumimos que está en hora de Lima
        dt = dt.replace(tzinfo=LIMA_TZ)
    return dt.astimezone(UTC_TZ)


# ============================================================================
# FUNCIONES DE FORMATO - String <-> Datetime
# ============================================================================

def format_lima_datetime(
    dt: datetime, 
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Formatear un datetime en zona horaria de Lima como string
    
    El datetime se convierte automáticamente a Lima antes de formatear.
    
    Args:
        dt: Datetime a formatear (puede estar en cualquier timezone)
        format_str: Formato de salida (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        str: Datetime formateado en zona horaria de Lima
        
    Examples:
        >>> # Formatear UTC a Lima
        >>> utc_dt = datetime(2025, 10, 11, 20, 30, tzinfo=timezone.utc)
        >>> formatted = format_lima_datetime(utc_dt)
        >>> print(formatted)  # "2025-10-11 15:30:00"
        
        >>> # Formato personalizado
        >>> formatted = format_lima_datetime(utc_dt, "%d/%m/%Y %H:%M")
        >>> print(formatted)  # "11/10/2025 15:30"
        
        >>> # Formato ISO
        >>> formatted = format_lima_datetime(utc_dt, "%Y-%m-%dT%H:%M:%S")
        >>> print(formatted)  # "2025-10-11T15:30:00"
        
    Use Cases:
        - Generar strings de fecha para mostrar en UI
        - Crear nombres de archivo con timestamp
        - Logs legibles para humanos
        - Exportar datos con fechas en hora local
        
    Common Formats:
        - "%Y-%m-%d %H:%M:%S" -> "2025-10-11 15:30:00"
        - "%d/%m/%Y %H:%M" -> "11/10/2025 15:30"
        - "%Y-%m-%d" -> "2025-10-11"
        - "%H:%M:%S" -> "15:30:00"
    """
    lima_dt = to_lima_time(dt)
    return lima_dt.strftime(format_str)


def parse_lima_datetime(
    date_str: str, 
    format_str: str = "%Y-%m-%d %H:%M:%S"
) -> datetime:
    """
    Parsear un string de fecha asumiendo zona horaria de Lima
    
    El string se parsea y se le asigna automáticamente timezone de Lima.
    
    Args:
        date_str: String con la fecha a parsear
        format_str: Formato del string de entrada (default: YYYY-MM-DD HH:MM:SS)
        
    Returns:
        datetime: Datetime con timezone de Lima
        
    Examples:
        >>> # Parsear formato estándar
        >>> dt = parse_lima_datetime("2025-10-11 15:30:00")
        >>> print(dt)  # 2025-10-11 15:30:00-05:00
        
        >>> # Parsear formato personalizado
        >>> dt = parse_lima_datetime("11/10/2025 15:30", "%d/%m/%Y %H:%M")
        >>> print(dt)  # 2025-10-11 15:30:00-05:00
        
        >>> # Parsear solo fecha
        >>> dt = parse_lima_datetime("2025-10-11", "%Y-%m-%d")
        >>> print(dt)  # 2025-10-11 00:00:00-05:00
        
    Use Cases:
        - Parsear input de usuario (fechas de formulario)
        - Leer fechas de archivos CSV/JSON
        - Convertir strings de configuración a datetime
        
    Common Formats:
        - "%Y-%m-%d %H:%M:%S" -> "2025-10-11 15:30:00"
        - "%d/%m/%Y %H:%M" -> "11/10/2025 15:30"
        - "%Y-%m-%d" -> "2025-10-11"
        - "%Y-%m-%dT%H:%M:%S" -> "2025-10-11T15:30:00"
    """
    naive_dt = datetime.strptime(date_str, format_str)
    return naive_dt.replace(tzinfo=LIMA_TZ)


# ============================================================================
# FUNCIONES UTILITARIAS - Operaciones Comunes
# ============================================================================

def get_lima_date_range(
    start_date: datetime, 
    end_date: datetime
) -> tuple[datetime, datetime]:
    """
    Obtener rango de fechas en zona horaria de Lima
    
    Útil para filtros de consultas que necesitan trabajar con rangos
    de fechas en la zona horaria local.
    
    Args:
        start_date: Fecha de inicio (cualquier timezone)
        end_date: Fecha de fin (cualquier timezone)
        
    Returns:
        tuple: (start_date_lima, end_date_lima)
        
    Example:
        >>> start = datetime(2025, 10, 1, 0, 0, tzinfo=timezone.utc)
        >>> end = datetime(2025, 10, 31, 23, 59, tzinfo=timezone.utc)
        >>> lima_start, lima_end = get_lima_date_range(start, end)
        >>> print(lima_start)  # 2025-09-30 19:00:00-05:00
        >>> print(lima_end)    # 2025-10-31 18:59:00-05:00
        
    Use Cases:
        - Filtros de convocatorias por rango de fechas
        - Consultas de auditoría entre fechas
        - Reportes mensuales/anuales
    """
    return to_lima_time(start_date), to_lima_time(end_date)


def is_timezone_aware(dt: datetime) -> bool:
    """
    Verificar si un datetime es timezone-aware
    
    Args:
        dt: Datetime a verificar
        
    Returns:
        bool: True si tiene timezone, False si es naive
        
    Example:
        >>> aware = lima_now()
        >>> naive = datetime.now()
        >>> print(is_timezone_aware(aware))  # True
        >>> print(is_timezone_aware(naive))  # False
        
    Use Cases:
        - Validaciones antes de operaciones
        - Tests unitarios
        - Debugging de problemas de timezone
    """
    return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None


def ensure_timezone_aware(dt: datetime, assume_tz: str = "UTC") -> datetime:
    """
    Asegurar que un datetime sea timezone-aware
    
    Si el datetime ya tiene timezone, lo retorna sin cambios.
    Si es naive, le asigna el timezone especificado.
    
    Args:
        dt: Datetime a verificar/convertir
        assume_tz: Timezone a asumir si es naive ("UTC" o "Lima")
        
    Returns:
        datetime: Datetime timezone-aware
        
    Example:
        >>> naive = datetime(2025, 10, 11, 15, 30)
        >>> aware = ensure_timezone_aware(naive, "Lima")
        >>> print(aware)  # 2025-10-11 15:30:00-05:00
        
    Use Cases:
        - Procesar datos de fuentes externas
        - Migración de código legacy
        - Funciones defensive programming
    """
    if is_timezone_aware(dt):
        return dt
    
    if assume_tz.upper() == "UTC":
        return dt.replace(tzinfo=UTC_TZ)
    elif assume_tz.upper() == "LIMA":
        return dt.replace(tzinfo=LIMA_TZ)
    else:
        raise ValueError(f"Timezone no soportado: {assume_tz}. Use 'UTC' o 'Lima'")


# ============================================================================
# ALIAS - Para Compatibilidad y Conveniencia
# ============================================================================

def get_current_time() -> datetime:
    """
    Alias de lima_now() para compatibilidad con código existente
    
    Returns:
        datetime: Datetime actual en zona horaria de Lima
        
    Note:
        Se recomienda usar lima_now() directamente para mayor claridad
    """
    return lima_now()


def now() -> datetime:
    """
    Alias corto de lima_now() para código más conciso
    
    Returns:
        datetime: Datetime actual en zona horaria de Lima
    """
    return lima_now()


# ============================================================================
# CONSTANTES DE FORMATO - Formatos Comunes
# ============================================================================

# Formatos estándar para fechas
FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"  # 2025-10-11T15:30:00
FORMAT_DATE = "%Y-%m-%d"  # 2025-10-11
FORMAT_TIME = "%H:%M:%S"  # 15:30:00
FORMAT_DATETIME = "%Y-%m-%d %H:%M:%S"  # 2025-10-11 15:30:00
FORMAT_DATE_ES = "%d/%m/%Y"  # 11/10/2025
FORMAT_DATETIME_ES = "%d/%m/%Y %H:%M"  # 11/10/2025 15:30
FORMAT_FILENAME = "%Y%m%d_%H%M%S"  # 20251011_153000
