from datetime import datetime


VALID_EXCEPTION_TYPES = {"DA", "FL", "LIC", "OTR", "FOR"}


def validate_config(data):
    """Return actionable validation errors without mutating the loaded payload."""
    errors = []
    if not isinstance(data, dict):
        return ["La configuración debe ser un objeto JSON."]

    people = data.get("personal", [])
    if not isinstance(people, list):
        errors.append("personal debe ser una lista.")
        people = []

    ids = []
    names = set()
    for index, person in enumerate(people):
        if not isinstance(person, dict):
            errors.append(f"personal[{index}] debe ser un objeto.")
            continue
        person_id = person.get("id")
        name = person.get("nombre")
        if not isinstance(person_id, int) or isinstance(person_id, bool) or person_id < 1:
            errors.append(f"personal[{index}].id debe ser un entero positivo.")
        elif person_id in ids:
            errors.append(f"ID de funcionario duplicado: {person_id}.")
        else:
            ids.append(person_id)
        if not isinstance(name, str) or not name.strip():
            errors.append(f"personal[{index}].nombre no puede estar vacío.")
        elif name.casefold() in names:
            errors.append(f"Nombre de funcionario duplicado: {name}.")
        else:
            names.add(name.casefold())

    next_id = data.get("siguiente_id", 1)
    if not isinstance(next_id, int) or next_id not in ids and ids:
        errors.append("siguiente_id no apunta a un funcionario válido.")

    pending = data.get("pendientes", [])
    if not isinstance(pending, list) or any(item not in ids for item in pending):
        errors.append("pendientes contiene IDs inválidos.")

    exceptions = data.get("excepciones", {})
    if not isinstance(exceptions, dict):
        errors.append("excepciones debe ser un objeto.")
    else:
        for period, items in exceptions.items():
            if not isinstance(items, list):
                errors.append(f"excepciones[{period}] debe ser una lista.")
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"excepciones[{period}][{index}] debe ser un objeto.")
                    continue
                if item.get("tipo") not in VALID_EXCEPTION_TYPES:
                    errors.append(f"Tipo de excepción inválido en {period}: {item.get('tipo')}.")
                if "motivo" in item and not isinstance(item["motivo"], str):
                    errors.append(f"Motivo de excepción inválido en {period}[{index}].")
                try:
                    datetime.strptime(item.get("fecha", ""), "%Y-%m-%d")
                except (TypeError, ValueError):
                    errors.append(f"Fecha de excepción inválida en {period}.")

    for field in ("inicio", "historial", "snapshots", "asignaciones_manuales",
                  "asignaciones_manuales_motivos", "notificaciones"):
        if field in data and not isinstance(data[field], dict):
            errors.append(f"{field} debe ser un objeto.")
    if "auditoria" in data and not isinstance(data["auditoria"], list):
        errors.append("auditoria debe ser una lista.")
    return errors
