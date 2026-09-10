"""Calendario de feriados nacionales de Chile."""

import unicodedata

import holidays


def normalize_holiday_name(name):
    """Devuelve una clave estable para comparar un feriado entre años."""
    normalized = unicodedata.normalize("NFKD", str(name))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(normalized.lower().split())


def national_holidays(year):
    """Devuelve feriados nacionales de Chile agrupados por clave de nombre."""
    calendar = holidays.country_holidays("CL", years=year, subdiv=None, language="es")
    result = {}
    for holiday_date, name in calendar.items():
        key = normalize_holiday_name(name)
        result.setdefault(key, []).append({"fecha": holiday_date, "nombre": name})
    return result


def december_holidays(year):
    """Devuelve los feriados nacionales que caen en diciembre del año indicado."""
    return [
        holiday
        for items in national_holidays(year).values()
        for holiday in items
        if holiday["fecha"].month == 12
    ]
