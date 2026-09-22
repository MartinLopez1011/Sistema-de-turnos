"""Calendario de feriados nacionales de Chile."""

import functools
import unicodedata

import holidays


def normalize_holiday_name(name):
    """Devuelve una clave estable para comparar un feriado entre años."""
    normalized = unicodedata.normalize("NFKD", str(name))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(normalized.lower().split())


@functools.lru_cache(maxsize=16)
def national_holidays(year):
    """Devuelve feriados nacionales de Chile agrupados por clave de nombre."""
    calendar = holidays.country_holidays("CL", years=year, subdiv=None, language="es")
    result = {}
    for holiday_date, name in calendar.items():
        key = normalize_holiday_name(name)
        result.setdefault(key, []).append({"fecha": holiday_date, "nombre": name})
    return result

