import json
import os
import collections
import calendar
from datetime import datetime, timedelta

class ShiftManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.inicio = data.get('inicio', {})
            self.historial = data.get('historial', {})
            self.personal = data.get('personal', [])
            self.siguiente_id = data.get('siguiente_id', 1)
            self.pendientes = data.get('pendientes', [])
            self.snapshots = data.get('snapshots', {})
            saved_exceptions = data.get('excepciones', {})
            self.excepciones = saved_exceptions if isinstance(saved_exceptions, dict) else {}

            # ITER 2 bug fix: normalizar keys de snapshots al formato YYYY-MM (con cero)
            raw_snapshots = self.snapshots
            normalized = {}
            for k, v in raw_snapshots.items():
                parts = k.split('-')
                if len(parts) == 2:
                    try:
                        norm_k = f"{int(parts[0])}-{int(parts[1]):02d}"
                        normalized[norm_k] = v
                    except ValueError:
                        normalized[k] = v
                else:
                    normalized[k] = v
            self.snapshots = normalized

    def save_config(self):
        directory = os.path.dirname(os.path.abspath(self.config_path))
        temporary_path = self.config_path + '.tmp'
        payload = {
            "personal": self.personal,
            "inicio": self.inicio,
            "historial": self.historial,
            "siguiente_id": self.siguiente_id,
            "pendientes": self.pendientes,
            "snapshots": self.snapshots,
            "excepciones": self.excepciones
        }
        try:
            with open(temporary_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary_path, self.config_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def get_exceptions(self, period_key):
        exceptions = []
        seen = set()
        for item in self.excepciones.get(period_key, []):
            try:
                exception = {
                    'persona': item['persona'],
                    'fecha': datetime.strptime(item['fecha'], '%Y-%m-%d').date(),
                    'tipo': item['tipo']
                }
                key = (exception['persona'], exception['fecha'])
                if key not in seen:
                    exceptions.append(exception)
                    seen.add(key)
            except (KeyError, TypeError, ValueError):
                continue
        return exceptions

    def get_person_by_id(self, p_id):
        for p in self.personal:
            if p['id'] == p_id:
                return p['nombre']
        return "Desconocido"

    def set_starting_person(self, person_name):
        for person in self.personal:
            if person['nombre'] == person_name:
                self.siguiente_id = person['id']
                self.save_config()
                return True
        return False

    def generate_shifts(self, year, month, exceptions, state=None):
        cal = calendar.Calendar().monthdatescalendar(year, month)
        weeks = []
        for week in cal:
            start_date = week[0]
            end_date = week[-1]
            weeks.append((start_date, end_date))

        shifts = []
        
        # 1. Cargar snapshot o estado temporal para calcular una previsión encadenada
        snapshot_key = f"{year}-{month:02d}"
        if state is not None:
            current_siguiente_id = state["siguiente_id"]
            current_pendientes = state["pendientes"].copy()
        elif snapshot_key in self.snapshots:
            current_siguiente_id = self.snapshots[snapshot_key]["siguiente_id"]
            current_pendientes = self.snapshots[snapshot_key]["pendientes"].copy()
        else:
            current_siguiente_id = self.siguiente_id
            current_pendientes = self.pendientes.copy()
            
        personal_ids = [p['id'] for p in self.personal]
        personal_id_set = set(personal_ids)
        if personal_ids:
            try:
                current_person_index = personal_ids.index(current_siguiente_id)
            except ValueError:
                current_person_index = 0
            current_siguiente_id = personal_ids[current_person_index]
        else:
            current_person_index = 0

        recalculate_history = False
        for start_date, end_date in weeks:
            week_key = f"{start_date.isoformat()}_{end_date.isoformat()}"
            historical_skipped = []
            
            # 2. Respetar inicio inmutable
            if hasattr(self, 'inicio') and week_key in self.inicio:
                shifts.append({
                    'semana': (start_date, end_date),
                    'persona': self.inicio[week_key],
                    'saltados': []
                })
                continue
                
            # 3. Un mes cerrado debe conservar exactamente su asignación.
            if week_key in self.historial:
                historical_person = self.historial[week_key]
                historical_exception = any(
                    exc['persona'] == historical_person and
                    start_date <= exc['fecha'] <= end_date
                    for exc in exceptions
                )
                if not historical_exception and not recalculate_history:
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': historical_person,
                        'saltados': []
                    })
                    continue

                if historical_exception:
                    historical_type = next(
                        exc['tipo'] for exc in exceptions
                        if exc['persona'] == historical_person and
                        start_date <= exc['fecha'] <= end_date
                    )
                    historical_skipped.append({
                        'persona': historical_person,
                        'tipo': historical_type
                    })

                if personal_ids and historical_exception:
                        historical_index = next(
                            (index for index, person in enumerate(self.personal)
                             if person['nombre'] == historical_person),
                            current_person_index
                        )
                        historical_id = personal_ids[historical_index]
                        # BUG FIX: agregar la persona histórica a pendientes para que
                        # recupere su turno en la próxima semana disponible.
                        if historical_id not in current_pendientes:
                            current_pendientes.append(historical_id)
                        current_person_index = (historical_index + 1) % len(personal_ids)
                        recalculate_history = True
                
            assigned = False
            skipped_this_week = historical_skipped.copy()
            
            # 3. Intentar asignar a pendientes (Opción B)
            new_pendientes = []
            for p_id in current_pendientes:
                if p_id not in personal_id_set:
                    continue
                if assigned:
                    new_pendientes.append(p_id)
                    continue
                    
                nombre = self.get_person_by_id(p_id)
                has_exception = False
                exc_tipo = ""
                for exc in exceptions:
                    if exc['persona'] == nombre and start_date <= exc['fecha'] <= end_date:
                        has_exception = True
                        exc_tipo = exc['tipo']
                        break
                        
                if has_exception:
                    new_pendientes.append(p_id)
                    skipped_this_week.append({'persona': nombre, 'tipo': exc_tipo})
                else:
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': nombre,
                        'saltados': skipped_this_week.copy()
                    })
                    assigned = True
                    current_person_index = (personal_ids.index(p_id) + 1) % len(personal_ids)
                    current_siguiente_id = personal_ids[current_person_index]
                    
            current_pendientes = new_pendientes

            # 4. Si no hay pendientes libres, seguimos la lista normal
            iterations = 0
            while not assigned and personal_ids and iterations < len(personal_ids):
                p_id = personal_ids[current_person_index]
                nombre = self.get_person_by_id(p_id)
                
                # Avanzar puntero circularmente
                current_person_index = (current_person_index + 1) % len(personal_ids)
                current_siguiente_id = personal_ids[current_person_index]
                    
                has_exception = False
                exc_tipo = ""
                for exc in exceptions:
                    if exc['persona'] == nombre and start_date <= exc['fecha'] <= end_date:
                        has_exception = True
                        exc_tipo = exc['tipo']
                        break
                        
                if has_exception:
                    current_pendientes.append(p_id)
                    skipped_this_week.append({'persona': nombre, 'tipo': exc_tipo})
                else:
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': nombre,
                        'saltados': skipped_this_week.copy()
                    })
                    assigned = True
                
                iterations += 1
                
            if not assigned:
                shifts.append({
                    'semana': (start_date, end_date),
                    'persona': None,
                    'saltados': skipped_this_week.copy()
                })

        return shifts, current_siguiente_id, current_pendientes

    def advance_month(self, year, month, exceptions):
        shifts, final_id, final_pendientes = self.generate_shifts(year, month, exceptions)
        
        for shift in shifts:
            start_date = shift['semana'][0]
            end_date = shift['semana'][1]
            person = shift['persona']
            
            # Solo guardamos en historial las semanas que recalculamos (o que ya estaban)
            if person:
                week_key = f"{start_date.isoformat()}_{end_date.isoformat()}"
                # No sobrescribir el inicio
                if not (hasattr(self, 'inicio') and week_key in self.inicio):
                    self.historial[week_key] = person
                
        # Crear snapshot para el MES SIGUIENTE
        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
            
        next_snapshot_key = f"{next_year}-{next_month:02d}"
        self.snapshots[next_snapshot_key] = {
            "siguiente_id": final_id,
            "pendientes": final_pendientes.copy()
        }
        
        # Actualizar estado global
        self.siguiente_id = final_id
        self.pendientes = final_pendientes

        period_key = f"{year}-{month:02d}"
        self.excepciones[period_key] = [
            {
                'persona': exc['persona'],
                'fecha': exc['fecha'].isoformat(),
                'tipo': exc['tipo']
            }
            for exc in exceptions
        ]
        
        self.save_config()
        return True, "Turnos guardados y cola avanzada."
