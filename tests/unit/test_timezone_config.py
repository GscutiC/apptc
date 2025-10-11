"""
Tests Unitarios para el Módulo de Configuración de Zona Horaria

Este archivo contiene tests exhaustivos para todas las funciones
del módulo timezone_config.py, asegurando el correcto manejo de
fechas y horas con conciencia de zona horaria.

Autor: Sistema Backend AppTc
Fecha: 2025-10-11
"""
import pytest
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from src.mi_app_completa_backend.infrastructure.config.timezone_config import (
    LIMA_TZ,
    UTC_TZ,
    get_lima_timezone,
    lima_now,
    utc_now,
    to_lima_time,
    to_utc_time,
    format_lima_datetime,
    parse_lima_datetime,
    get_lima_date_range,
    is_timezone_aware,
    ensure_timezone_aware,
    get_current_time,
    now,
    FORMAT_ISO,
    FORMAT_DATE,
    FORMAT_TIME,
    FORMAT_DATETIME,
    FORMAT_DATE_ES,
    FORMAT_DATETIME_ES,
    FORMAT_FILENAME,
)


class TestTimezoneConstants:
    """Tests para constantes de zona horaria"""
    
    def test_lima_tz_is_correct(self):
        """Verificar que LIMA_TZ apunte a America/Lima"""
        assert str(LIMA_TZ) == "America/Lima"
        assert isinstance(LIMA_TZ, ZoneInfo)
    
    def test_utc_tz_is_correct(self):
        """Verificar que UTC_TZ sea timezone UTC"""
        assert UTC_TZ == timezone.utc


class TestGetLimaTimezone:
    """Tests para función get_lima_timezone()"""
    
    def test_returns_zoneinfo_object(self):
        """Debe retornar un objeto ZoneInfo"""
        tz = get_lima_timezone()
        assert isinstance(tz, ZoneInfo)
    
    def test_returns_lima_timezone(self):
        """Debe retornar la zona horaria de Lima"""
        tz = get_lima_timezone()
        assert str(tz) == "America/Lima"
    
    def test_returns_same_object_as_constant(self):
        """Debe retornar el mismo objeto que la constante"""
        tz = get_lima_timezone()
        assert tz is LIMA_TZ


class TestLimaNow:
    """Tests para función lima_now()"""
    
    def test_returns_datetime_object(self):
        """Debe retornar un objeto datetime"""
        now = lima_now()
        assert isinstance(now, datetime)
    
    def test_has_lima_timezone(self):
        """Debe tener timezone de Lima"""
        now = lima_now()
        assert now.tzinfo is not None
        assert str(now.tzinfo) == "America/Lima"
    
    def test_is_timezone_aware(self):
        """Debe ser timezone-aware"""
        now = lima_now()
        assert now.tzinfo is not None
        assert now.tzinfo.utcoffset(now) is not None
    
    def test_returns_current_time(self):
        """Debe retornar tiempo cercano al actual"""
        before = datetime.now(LIMA_TZ)
        result = lima_now()
        after = datetime.now(LIMA_TZ)
        
        # Debe estar entre before y after (con margen de 1 segundo)
        assert before <= result <= after + timedelta(seconds=1)


class TestUtcNow:
    """Tests para función utc_now()"""
    
    def test_returns_datetime_object(self):
        """Debe retornar un objeto datetime"""
        now = utc_now()
        assert isinstance(now, datetime)
    
    def test_has_utc_timezone(self):
        """Debe tener timezone UTC"""
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == timezone.utc
    
    def test_is_timezone_aware(self):
        """Debe ser timezone-aware"""
        now = utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo.utcoffset(now) == timedelta(0)
    
    def test_returns_current_time(self):
        """Debe retornar tiempo cercano al actual"""
        before = datetime.now(timezone.utc)
        result = utc_now()
        after = datetime.now(timezone.utc)
        
        assert before <= result <= after + timedelta(seconds=1)


class TestToLimaTime:
    """Tests para función to_lima_time()"""
    
    def test_converts_utc_to_lima(self):
        """Debe convertir correctamente de UTC a Lima"""
        # UTC: 2025-10-11 20:30:00 -> Lima: 2025-10-11 15:30:00 (UTC-5)
        utc_dt = datetime(2025, 10, 11, 20, 30, 0, tzinfo=timezone.utc)
        lima_dt = to_lima_time(utc_dt)
        
        assert lima_dt.hour == 15
        assert lima_dt.minute == 30
        assert str(lima_dt.tzinfo) == "America/Lima"
    
    def test_handles_naive_datetime(self):
        """Debe manejar datetime naive (asume UTC)"""
        naive_dt = datetime(2025, 10, 11, 20, 30, 0)
        lima_dt = to_lima_time(naive_dt)
        
        assert lima_dt.hour == 15
        assert str(lima_dt.tzinfo) == "America/Lima"
    
    def test_preserves_date(self):
        """Debe preservar la fecha correctamente"""
        utc_dt = datetime(2025, 10, 11, 3, 30, 0, tzinfo=timezone.utc)
        lima_dt = to_lima_time(utc_dt)
        
        # 03:30 UTC = 22:30 Lima del día anterior
        assert lima_dt.year == 2025
        assert lima_dt.month == 10
        assert lima_dt.day == 10
        assert lima_dt.hour == 22
    
    def test_already_lima_datetime(self):
        """Debe manejar datetime que ya está en Lima"""
        original = datetime(2025, 10, 11, 15, 30, 0, tzinfo=LIMA_TZ)
        result = to_lima_time(original)
        
        assert result.hour == 15
        assert result.minute == 30
        assert str(result.tzinfo) == "America/Lima"


class TestToUtcTime:
    """Tests para función to_utc_time()"""
    
    def test_converts_lima_to_utc(self):
        """Debe convertir correctamente de Lima a UTC"""
        # Lima: 2025-10-11 15:30:00 -> UTC: 2025-10-11 20:30:00 (UTC+5)
        lima_dt = datetime(2025, 10, 11, 15, 30, 0, tzinfo=LIMA_TZ)
        utc_dt = to_utc_time(lima_dt)
        
        assert utc_dt.hour == 20
        assert utc_dt.minute == 30
        assert utc_dt.tzinfo == timezone.utc
    
    def test_handles_naive_datetime(self):
        """Debe manejar datetime naive (asume Lima)"""
        naive_dt = datetime(2025, 10, 11, 15, 30, 0)
        utc_dt = to_utc_time(naive_dt)
        
        assert utc_dt.hour == 20
        assert utc_dt.tzinfo == timezone.utc
    
    def test_preserves_date(self):
        """Debe preservar la fecha correctamente"""
        lima_dt = datetime(2025, 10, 11, 22, 30, 0, tzinfo=LIMA_TZ)
        utc_dt = to_utc_time(lima_dt)
        
        # 22:30 Lima = 03:30 UTC del día siguiente
        assert utc_dt.year == 2025
        assert utc_dt.month == 10
        assert utc_dt.day == 12
        assert utc_dt.hour == 3
    
    def test_already_utc_datetime(self):
        """Debe manejar datetime que ya está en UTC"""
        original = datetime(2025, 10, 11, 20, 30, 0, tzinfo=timezone.utc)
        result = to_utc_time(original)
        
        assert result.hour == 20
        assert result.minute == 30
        assert result.tzinfo == timezone.utc


class TestFormatLimaDatetime:
    """Tests para función format_lima_datetime()"""
    
    def test_formats_with_default_format(self):
        """Debe formatear con formato por defecto"""
        dt = datetime(2025, 10, 11, 15, 30, 45, tzinfo=LIMA_TZ)
        formatted = format_lima_datetime(dt)
        
        assert formatted == "2025-10-11 15:30:45"
    
    def test_formats_utc_to_lima(self):
        """Debe convertir UTC a Lima antes de formatear"""
        utc_dt = datetime(2025, 10, 11, 20, 30, 0, tzinfo=timezone.utc)
        formatted = format_lima_datetime(utc_dt)
        
        # 20:30 UTC = 15:30 Lima
        assert "15:30" in formatted
    
    def test_custom_format_date_only(self):
        """Debe soportar formato personalizado (solo fecha)"""
        dt = datetime(2025, 10, 11, 15, 30, tzinfo=LIMA_TZ)
        formatted = format_lima_datetime(dt, FORMAT_DATE)
        
        assert formatted == "2025-10-11"
    
    def test_custom_format_time_only(self):
        """Debe soportar formato personalizado (solo hora)"""
        dt = datetime(2025, 10, 11, 15, 30, 45, tzinfo=LIMA_TZ)
        formatted = format_lima_datetime(dt, FORMAT_TIME)
        
        assert formatted == "15:30:45"
    
    def test_custom_format_spanish(self):
        """Debe soportar formato español"""
        dt = datetime(2025, 10, 11, 15, 30, tzinfo=LIMA_TZ)
        formatted = format_lima_datetime(dt, FORMAT_DATETIME_ES)
        
        assert formatted == "11/10/2025 15:30"
    
    def test_custom_format_filename(self):
        """Debe soportar formato para nombres de archivo"""
        dt = datetime(2025, 10, 11, 15, 30, 45, tzinfo=LIMA_TZ)
        formatted = format_lima_datetime(dt, FORMAT_FILENAME)
        
        assert formatted == "20251011_153045"


class TestParseLimaDatetime:
    """Tests para función parse_lima_datetime()"""
    
    def test_parses_with_default_format(self):
        """Debe parsear con formato por defecto"""
        date_str = "2025-10-11 15:30:45"
        dt = parse_lima_datetime(date_str)
        
        assert dt.year == 2025
        assert dt.month == 10
        assert dt.day == 11
        assert dt.hour == 15
        assert dt.minute == 30
        assert dt.second == 45
        assert str(dt.tzinfo) == "America/Lima"
    
    def test_parses_date_only(self):
        """Debe parsear solo fecha"""
        date_str = "2025-10-11"
        dt = parse_lima_datetime(date_str, FORMAT_DATE)
        
        assert dt.year == 2025
        assert dt.month == 10
        assert dt.day == 11
        assert dt.hour == 0
        assert dt.minute == 0
        assert str(dt.tzinfo) == "America/Lima"
    
    def test_parses_spanish_format(self):
        """Debe parsear formato español"""
        date_str = "11/10/2025 15:30"
        dt = parse_lima_datetime(date_str, FORMAT_DATETIME_ES)
        
        assert dt.day == 11
        assert dt.month == 10
        assert dt.year == 2025
        assert dt.hour == 15
        assert dt.minute == 30
    
    def test_result_is_timezone_aware(self):
        """Resultado debe ser timezone-aware"""
        date_str = "2025-10-11 15:30:00"
        dt = parse_lima_datetime(date_str)
        
        assert dt.tzinfo is not None
        assert str(dt.tzinfo) == "America/Lima"


class TestGetLimaDateRange:
    """Tests para función get_lima_date_range()"""
    
    def test_converts_both_dates(self):
        """Debe convertir ambas fechas a Lima"""
        start_utc = datetime(2025, 10, 1, 0, 0, tzinfo=timezone.utc)
        end_utc = datetime(2025, 10, 31, 23, 59, tzinfo=timezone.utc)
        
        start_lima, end_lima = get_lima_date_range(start_utc, end_utc)
        
        assert str(start_lima.tzinfo) == "America/Lima"
        assert str(end_lima.tzinfo) == "America/Lima"
    
    def test_preserves_order(self):
        """Debe preservar el orden de las fechas"""
        start = datetime(2025, 10, 1, 0, 0, tzinfo=LIMA_TZ)
        end = datetime(2025, 10, 31, 23, 59, tzinfo=LIMA_TZ)
        
        start_result, end_result = get_lima_date_range(start, end)
        
        assert start_result < end_result
    
    def test_returns_tuple(self):
        """Debe retornar una tupla"""
        start = datetime(2025, 10, 1, tzinfo=LIMA_TZ)
        end = datetime(2025, 10, 31, tzinfo=LIMA_TZ)
        
        result = get_lima_date_range(start, end)
        
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestIsTimezoneAware:
    """Tests para función is_timezone_aware()"""
    
    def test_returns_true_for_utc_aware(self):
        """Debe retornar True para datetime UTC aware"""
        dt = datetime.now(timezone.utc)
        assert is_timezone_aware(dt) is True
    
    def test_returns_true_for_lima_aware(self):
        """Debe retornar True para datetime Lima aware"""
        dt = lima_now()
        assert is_timezone_aware(dt) is True
    
    def test_returns_false_for_naive(self):
        """Debe retornar False para datetime naive"""
        dt = datetime.now()
        assert is_timezone_aware(dt) is False
    
    def test_returns_false_for_none_tzinfo(self):
        """Debe retornar False para tzinfo=None"""
        dt = datetime(2025, 10, 11, 15, 30)
        assert is_timezone_aware(dt) is False


class TestEnsureTimezoneAware:
    """Tests para función ensure_timezone_aware()"""
    
    def test_returns_aware_datetime_unchanged(self):
        """No debe modificar datetime ya aware"""
        original = lima_now()
        result = ensure_timezone_aware(original)
        
        assert result == original
        assert str(result.tzinfo) == "America/Lima"
    
    def test_adds_utc_to_naive_by_default(self):
        """Debe agregar UTC a naive por defecto"""
        naive = datetime(2025, 10, 11, 15, 30)
        result = ensure_timezone_aware(naive)
        
        assert result.tzinfo == timezone.utc
    
    def test_adds_lima_when_specified(self):
        """Debe agregar Lima cuando se especifica"""
        naive = datetime(2025, 10, 11, 15, 30)
        result = ensure_timezone_aware(naive, "Lima")
        
        assert str(result.tzinfo) == "America/Lima"
    
    def test_raises_error_for_invalid_timezone(self):
        """Debe lanzar error para timezone inválido"""
        naive = datetime(2025, 10, 11, 15, 30)
        
        with pytest.raises(ValueError, match="Timezone no soportado"):
            ensure_timezone_aware(naive, "Invalid")


class TestAliases:
    """Tests para funciones alias"""
    
    def test_get_current_time_equals_lima_now(self):
        """get_current_time() debe comportarse igual que lima_now()"""
        result = get_current_time()
        
        assert isinstance(result, datetime)
        assert str(result.tzinfo) == "America/Lima"
    
    def test_now_equals_lima_now(self):
        """now() debe comportarse igual que lima_now()"""
        result = now()
        
        assert isinstance(result, datetime)
        assert str(result.tzinfo) == "America/Lima"


class TestFormatConstants:
    """Tests para constantes de formato"""
    
    def test_format_constants_exist(self):
        """Deben existir todas las constantes de formato"""
        assert FORMAT_ISO is not None
        assert FORMAT_DATE is not None
        assert FORMAT_TIME is not None
        assert FORMAT_DATETIME is not None
        assert FORMAT_DATE_ES is not None
        assert FORMAT_DATETIME_ES is not None
        assert FORMAT_FILENAME is not None
    
    def test_format_constants_are_strings(self):
        """Todas las constantes deben ser strings"""
        assert isinstance(FORMAT_ISO, str)
        assert isinstance(FORMAT_DATE, str)
        assert isinstance(FORMAT_TIME, str)
        assert isinstance(FORMAT_DATETIME, str)
        assert isinstance(FORMAT_DATE_ES, str)
        assert isinstance(FORMAT_DATETIME_ES, str)
        assert isinstance(FORMAT_FILENAME, str)


class TestIntegrationScenarios:
    """Tests de integración para escenarios reales"""
    
    def test_create_and_format_convocation_date(self):
        """Escenario: Crear fecha de convocatoria y formatearla"""
        # Usuario crea convocatoria con fecha límite
        deadline_lima = parse_lima_datetime("2025-12-31 23:59:59")
        
        # Se almacena en UTC en la base de datos
        deadline_utc = to_utc_time(deadline_lima)
        
        # Se recupera y se muestra en Lima
        display_date = format_lima_datetime(deadline_utc, FORMAT_DATETIME_ES)
        
        assert "31/12/2025 23:59" == display_date
    
    def test_compare_dates_from_different_sources(self):
        """Escenario: Comparar fecha actual con fecha límite"""
        # Fecha límite almacenada
        deadline_utc = datetime(2025, 12, 31, 4, 59, 59, tzinfo=timezone.utc)
        
        # Fecha actual en Lima
        current_lima = lima_now()
        
        # Convertir deadline a Lima para comparación
        deadline_lima = to_lima_time(deadline_utc)
        
        # Deben ser comparables sin errores
        is_expired = current_lima > deadline_lima
        assert isinstance(is_expired, bool)
    
    def test_filter_convocations_by_date_range(self):
        """Escenario: Filtrar convocatorias por rango de fechas"""
        # Usuario selecciona rango de octubre 2025
        start_str = "2025-10-01 00:00:00"
        end_str = "2025-10-31 23:59:59"
        
        # Parsear fechas en Lima
        start_lima = parse_lima_datetime(start_str)
        end_lima = parse_lima_datetime(end_str)
        
        # Obtener rango en Lima
        start_filter, end_filter = get_lima_date_range(start_lima, end_lima)
        
        # Verificar que son timezone-aware
        assert is_timezone_aware(start_filter)
        assert is_timezone_aware(end_filter)
        
        # Verificar que están en Lima
        assert str(start_filter.tzinfo) == "America/Lima"
        assert str(end_filter.tzinfo) == "America/Lima"


class TestEdgeCases:
    """Tests para casos límite"""
    
    def test_midnight_conversion(self):
        """Conversión en medianoche"""
        lima_midnight = datetime(2025, 10, 11, 0, 0, 0, tzinfo=LIMA_TZ)
        utc_time = to_utc_time(lima_midnight)
        
        # 00:00 Lima = 05:00 UTC
        assert utc_time.hour == 5
        assert utc_time.day == 11
    
    def test_noon_conversion(self):
        """Conversión al mediodía"""
        lima_noon = datetime(2025, 10, 11, 12, 0, 0, tzinfo=LIMA_TZ)
        utc_time = to_utc_time(lima_noon)
        
        # 12:00 Lima = 17:00 UTC
        assert utc_time.hour == 17
    
    def test_year_boundary(self):
        """Conversión en cambio de año"""
        lima_newyear = datetime(2025, 12, 31, 23, 30, 0, tzinfo=LIMA_TZ)
        utc_time = to_utc_time(lima_newyear)
        
        # 31 Dic 23:30 Lima = 1 Ene 04:30 UTC
        assert utc_time.year == 2026
        assert utc_time.month == 1
        assert utc_time.day == 1
        assert utc_time.hour == 4


# ============================================================================
# FIXTURES PARA TESTS
# ============================================================================

@pytest.fixture
def sample_lima_datetime():
    """Fixture: datetime de ejemplo en Lima"""
    return datetime(2025, 10, 11, 15, 30, 45, tzinfo=LIMA_TZ)


@pytest.fixture
def sample_utc_datetime():
    """Fixture: datetime de ejemplo en UTC"""
    return datetime(2025, 10, 11, 20, 30, 45, tzinfo=timezone.utc)


@pytest.fixture
def sample_naive_datetime():
    """Fixture: datetime naive de ejemplo"""
    return datetime(2025, 10, 11, 15, 30, 45)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
