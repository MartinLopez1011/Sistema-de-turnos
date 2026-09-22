import json
import os
import collections
import calendar
from datetime import datetime, timedelta, date

from utils.chilean_holidays import national_holidays, normalize_holiday_name
from utils.logger import get_logger

logger = get_logger("shift_manager")

class ShiftManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.last_warnings = []
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            logger.warning("Archivo de configuración %s no encontrado. Creando configuración base limpia.", self.config_path)
            self._init_defaults()
            self.save_config()
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error("Archivo config.json corrupto o ilegible: %s. Creando respaldo y restaurando base limpia.", e)
            try:
                config_dir = os.path.dirname(os.path.abspath(self.config_path))
                backups_dir = os.path.join(config_dir, "backups")
                os.makedirs(backups_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = os.path.basename(self.config_path)
                corrupt_path = os.path.join(backups_dir, f"{base_name}.corrupted_{timestamp}")
                with open(self.config_path, 'rb') as src, open(corrupt_path, 'wb') as dst:
                    dst.write(src.read())
                logger.info("Respaldo de archivo corrupto guardado en %s", corrupt_path)
            except Exception as be:
                logger.warning("No se pudo respaldar el archivo corrupto: %s", be)

            self._init_defaults()
            self.save_config()
            return

        self._parse_config_data(data)

    def _init_defaults(self):
        self.inicio = {}
        self.historial = {}
        self.personal = []
        self.siguiente_id = 1
        self.pendientes = []
        self.snapshots = {}
        self.excepciones = {}
        self.asignaciones_manuales = {}

    def _parse_config_data(self, data):
        self.inicio = data.get('inicio', {})
        self.historial = data.get('historial', {})
        self.personal = data.get('personal', [])
        self.siguiente_id = data.get('siguiente_id', 1)
        self.pendientes = data.get('pendientes', [])
        self.snapshots = data.get('snapshots', {})
        saved_exceptions = data.get('excepciones', {})
        self.excepciones = saved_exceptions if isinstance(saved_exceptions, dict) else {}
        saved_manual = data.get('asignaciones_manuales', {})
        self.asignaciones_manuales = saved_manual if isinstance(saved_manual, dict) else {}

        # Normalizar keys de snapshots al formato YYYY-MM (con cero)
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
        os.makedirs(directory, exist_ok=True)
        temporary_path = self.config_path + '.tmp'
        payload = {
            "personal": self.personal,
            "inicio": self.inicio,
            "historial": self.historial,
            "siguiente_id": self.siguiente_id,
            "pendientes": self.pendientes,
            "snapshots": self.snapshots,
            "excepciones": self.excepciones,
            "asignaciones_manuales": self.asignaciones_manuales
        }
        try:
            with open(temporary_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary_path, self.config_path)
            logger.debug("Configuración guardada en %s", self.config_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

    def create_backup(self, tag=None):
        """Crea una copia de seguridad fechada de config.json en la carpeta backups/."""
        try:
            config_dir = os.path.dirname(os.path.abspath(self.config_path))
            backups_dir = os.path.join(config_dir, "backups")
            os.makedirs(backups_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tag_str = f"_{tag}" if tag else ""
            backup_filename = f"config_{timestamp}{tag_str}.json"
            backup_path = os.path.join(backups_dir, backup_filename)

            payload = {
                "personal": self.personal,
                "inicio": self.inicio,
                "historial": self.historial,
                "siguiente_id": self.siguiente_id,
                "pendientes": self.pendientes,
                "snapshots": self.snapshots,
                "excepciones": self.excepciones,
                "asignaciones_manuales": self.asignaciones_manuales
            }
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)

            logger.info("Backup creado: %s", backup_path)

            # Rotar manteniendo un máximo de 20 backups
            existing_backups = sorted(
                [f for f in os.listdir(backups_dir) if f.startswith("config_") and f.endswith(".json")]
            )
            if len(existing_backups) > 20:
                for old_f in existing_backups[:-20]:
                    try:
                        os.remove(os.path.join(backups_dir, old_f))
                    except OSError:
                        pass

            return backup_path
        except Exception as e:
            logger.warning("Error creando backup de config: %s", e)
            return None

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

    def get_manual_assignments(self, period_key):
        return dict(self.asignaciones_manuales.get(period_key, {}))

    def set_manual_assignment(self, period_key, week_key, person_name):
        if period_key not in self.asignaciones_manuales:
            self.asignaciones_manuales[period_key] = {}
        self.asignaciones_manuales[period_key][week_key] = person_name
        self.save_config()

    def remove_manual_assignment(self, period_key, week_key):
        if period_key in self.asignaciones_manuales and week_key in self.asignaciones_manuales[period_key]:
            del self.asignaciones_manuales[period_key][week_key]
            if not self.asignaciones_manuales[period_key]:
                del self.asignaciones_manuales[period_key]
            self.save_config()

    def get_person_by_id(self, p_id):
        for p in self.personal:
            if p['id'] == p_id:
                return p['nombre']
        return "Desconocido"

    def _did_recently(self, nombre, before_date, shifts_so_far,
                      min_gap_weeks=4, ignored_period=None):
        """
        Devuelve True si 'nombre' ya hizo turno en las últimas min_gap_weeks semanas
        antes de before_date, considerando el historial guardado y los turnos
        calculados en la sesión actual (shifts_so_far).
        Esto evita que alguien reciba dos turnos muy seguidos al recuperar un
        pendiente o al arrancar el siguiente mes.
        """
        cutoff = before_date - timedelta(weeks=min_gap_weeks)
        last_date = self._last_shift_date(
            nombre, before_date, shifts_so_far, ignored_period=ignored_period
        )
        return last_date >= cutoff

    def _last_shift_date(self, nombre, before_date, shifts_so_far, ignored_period=None):
        """
        Devuelve la fecha de fin del turno más reciente de 'nombre' antes de before_date,
        o date.min si no tiene turnos previos registrados.
        """
        latest = date.min

        # Revisar historial guardado
        for week_key, person in self.historial.items():
            if person != nombre:
                continue
            try:
                parts = week_key.split('_')
                week_start = datetime.strptime(parts[0], '%Y-%m-%d').date()
                week_end = datetime.strptime(parts[1], '%Y-%m-%d').date()
                if ignored_period and week_start <= ignored_period[1] and week_end >= ignored_period[0]:
                    continue
                if week_end < before_date and week_end > latest:
                    latest = week_end
            except (ValueError, IndexError):
                continue

        # Revisar inicio inmutable
        for week_key, person in self.inicio.items():
            if person != nombre:
                continue
            try:
                parts = week_key.split('_')
                week_start = datetime.strptime(parts[0], '%Y-%m-%d').date()
                week_end = datetime.strptime(parts[1], '%Y-%m-%d').date()
                if ignored_period and week_start <= ignored_period[1] and week_end >= ignored_period[0]:
                    continue
                if week_end < before_date and week_end > latest:
                    latest = week_end
            except (ValueError, IndexError):
                continue

        # Revisar turnos ya calculados en esta sesión
        for sh in shifts_so_far:
            if sh.get('persona') == nombre:
                sh_start, sh_end = sh['semana']
                if ignored_period and sh_start <= ignored_period[1] and sh_end >= ignored_period[0]:
                    continue
                if sh_end < before_date and sh_end > latest:
                    latest = sh_end

        return latest

    def _was_forced_recently(self, nombre, before_date, current_exceptions, min_gap_weeks=4):
        cutoff = before_date - timedelta(weeks=min_gap_weeks)
        
        for exc in current_exceptions:
            if exc.get('persona') == nombre and exc.get('tipo') == "FOR":
                fecha = exc.get('fecha')
                if isinstance(fecha, str):
                    fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
                if fecha and cutoff <= fecha < before_date:
                    return True
                    
        for period_key, exc_list in self.excepciones.items():
            for exc in exc_list:
                if exc.get('persona') == nombre and exc.get('tipo') == "FOR":
                    fecha_str = exc.get('fecha')
                    if isinstance(fecha_str, str):
                        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    else:
                        fecha = fecha_str
                        
                    if fecha and cutoff <= fecha < before_date:
                        return True

        # Revisar asignaciones manuales guardadas (sucesor de FOR)
        for period_key, week_dict in self.asignaciones_manuales.items():
            for week_key, person in week_dict.items():
                if person == nombre:
                    try:
                        parts = week_key.split('_')
                        w_start = datetime.strptime(parts[0], '%Y-%m-%d').date()
                        if cutoff <= w_start < before_date:
                            return True
                    except (ValueError, IndexError):
                        continue
                        
        return False

    def _week_for_date(self, year, month, target_date):
        for week in calendar.Calendar().monthdatescalendar(year, month):
            if week[0] <= target_date <= week[-1]:
                return week[0], week[-1]
        return None

    def _historical_assignment_for_date(self, target_date):
        week = self._week_for_date(target_date.year, target_date.month, target_date)
        if not week:
            return None
        week_key = f"{week[0].isoformat()}_{week[1].isoformat()}"
        return self.historial.get(week_key) or self.inicio.get(week_key)

    def _get_holiday_restrictions(self, year, month, weeks):
        """
        Obtiene las restricciones de asignación basadas en feriados pasados.
        Evita que una persona repita el mismo feriado (buscado por nombre) 
        que ya trabajó el año anterior.
        """
        restrictions = {}
        if year <= 1:
            return restrictions
            
        previous_holidays = national_holidays(year - 1)
        current_year_holidays = national_holidays(year)
        
        all_current_holidays = [
            holiday for items in current_year_holidays.values() for holiday in items
        ]
        
        for holiday in all_current_holidays:
            current_week = next(
                (week for week in weeks if week[0] <= holiday["fecha"] <= week[1]),
                None)
                
            if not current_week:
                continue
                
            holiday_key = normalize_holiday_name(holiday["nombre"])
            previous_items = previous_holidays.get(holiday_key, [])
            
            # Buscar el feriado del año pasado sin importar en qué mes cayó
            previous_holiday = next((item for item in previous_items), None)
            if not previous_holiday:
                continue

            previous_person = self._historical_assignment_for_date(previous_holiday["fecha"])
            if not previous_person:
                continue

            restrictions.setdefault(current_week, []).append({
                "feriado": holiday["nombre"],
                "fecha": holiday["fecha"],
                "persona": previous_person,
            })
            
        return restrictions

    def set_starting_person(self, person_name):
        for person in self.personal:
            if person['nombre'] == person_name:
                self.siguiente_id = person['id']
                self.save_config()
                return True
        return False

    def generate_shifts(self, year, month, exceptions, state=None,
                        recalculate_history=False, manual_assignments=None):
        self.last_warnings = []

        # Normalizar excepciones asegurando que fecha sea date
        normalized_exceptions = []
        for exc in exceptions:
            f = exc.get('fecha')
            if isinstance(f, str):
                try:
                    f = datetime.strptime(f, '%Y-%m-%d').date()
                except ValueError:
                    continue
            normalized_exceptions.append({
                'persona': exc['persona'],
                'fecha': f,
                'tipo': exc['tipo']
            })
        exceptions = normalized_exceptions

        cal = calendar.Calendar().monthdatescalendar(year, month)
        weeks = []
        for week in cal:
            start_date = week[0]
            end_date = week[-1]
            weeks.append((start_date, end_date))

        holiday_restrictions = self._get_holiday_restrictions(year, month, weeks)

        shifts = []
        
        # 1. Cargar snapshot o estado temporal para calcular una previsión encadenada
        snapshot_key = f"{year}-{month:02d}"
        if manual_assignments is None:
            manual_assignments = self.asignaciones_manuales.get(snapshot_key, {})
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
        effective_gap = 4
        if personal_ids:
            try:
                current_person_index = personal_ids.index(current_siguiente_id)
            except ValueError:
                current_person_index = 0
            current_siguiente_id = personal_ids[current_person_index]
        else:
            current_person_index = 0

        history_recalculated = recalculate_history
        recalculated_period = (weeks[0][0], weeks[-1][1]) if recalculate_history else None
        for start_date, end_date in weeks:
            week_key = f"{start_date.isoformat()}_{end_date.isoformat()}"
            historical_skipped = []
            week_restrictions = holiday_restrictions.get((start_date, end_date), [])
            restricted_people = {
                item["persona"] for item in week_restrictions
            }
            blocked_fallback = None
            blocked_fallback_reason = None
            
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
                    start_date <= exc['fecha'] <= end_date and
                    exc['tipo'] != 'FOR'
                    for exc in exceptions
                )
                has_manual_override = bool(
                    manual_assignments and
                    week_key in manual_assignments and
                    manual_assignments[week_key] != historical_person
                )
                if not historical_exception and not history_recalculated and not has_manual_override:
                    # Avanzar el puntero para que la rotación refleje quién ya hizo turno
                    hist_idx = next(
                        (i for i, p in enumerate(self.personal)
                         if p['nombre'] == historical_person),
                        None
                    )
                    if hist_idx is not None:
                        historical_id = personal_ids[hist_idx]
                        # Si ya cumplió turno, no debe arrastrarse como pendiente
                        # desde un cálculo anterior hacia el mes siguiente.
                        current_pendientes = [
                            p_id for p_id in current_pendientes
                            if p_id != historical_id
                        ]
                        next_idx = (hist_idx + 1) % len(personal_ids)
                        # Solo avanzar si el puntero actual está "detrás" de esta persona
                        # (evita retroceder si ya pasamos a alguien más adelante)
                        if personal_ids[current_person_index] == personal_ids[hist_idx]:
                            current_person_index = next_idx
                            current_siguiente_id = personal_ids[current_person_index]

                    is_hist_manual = bool(
                        (self.asignaciones_manuales.get(snapshot_key, {}).get(week_key) == historical_person) or
                        (manual_assignments and manual_assignments.get(week_key) == historical_person)
                    )
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': historical_person,
                        'saltados': [],
                        'es_manual': is_hist_manual
                    })
                    continue

                if has_manual_override:
                    history_recalculated = True

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
                    history_recalculated = True
                
            assigned = False
            skipped_this_week = historical_skipped.copy()
            
            # 3.0 Asignación manual directa (Alternativa 1)
            if manual_assignments and week_key in manual_assignments:
                nombre_manual = manual_assignments[week_key]
                manual_id = next((p['id'] for p in self.personal if p['nombre'] == nombre_manual), None)
                if manual_id:
                    current_pendientes = [p for p in current_pendientes if p != manual_id]
                    if personal_ids and personal_ids[current_person_index] == manual_id:
                        current_person_index = (current_person_index + 1) % len(personal_ids)
                        current_siguiente_id = personal_ids[current_person_index]
                shifts.append({
                    'semana': (start_date, end_date),
                    'persona': nombre_manual,
                    'saltados': skipped_this_week.copy(),
                    'es_manual': True
                })
                assigned = True

            # 3.0b Intentar asignación forzada legacy (FOR en excepciones)
            if not assigned:
                for exc in exceptions:
                    if start_date <= exc['fecha'] <= end_date and exc['tipo'] == "FOR":
                        nombre_forzado = exc['persona']
                        current_pendientes = [p for p in current_pendientes if self.get_person_by_id(p) != nombre_forzado]
                        shifts.append({
                            'semana': (start_date, end_date),
                            'persona': nombre_forzado,
                            'saltados': skipped_this_week.copy(),
                            'es_forzado': True
                        })
                        assigned = True
                        break
            
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

                if not has_exception and nombre in restricted_people:
                    if blocked_fallback is None:
                        blocked_fallback = (p_id, nombre)
                        blocked_fallback_reason = week_restrictions
                    new_pendientes.append(p_id)
                    continue

                # Un pendiente recupera el turno perdido en la primera semana
                # disponible; no debe esperar el intervalo de la rotación normal.
                if has_exception:
                    new_pendientes.append(p_id)
                    if not any(
                            skipped['persona'] == nombre
                            for skipped in skipped_this_week):
                        skipped_this_week.append({
                            'persona': nombre,
                            'tipo': exc_tipo
                        })
                else:
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': nombre,
                        'saltados': skipped_this_week.copy(),
                        'es_recuperacion': True
                    })
                    assigned = True
                    
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

                if not has_exception and nombre in restricted_people:
                    if blocked_fallback is None:
                        blocked_fallback = (p_id, nombre)
                        blocked_fallback_reason = week_restrictions
                    current_pendientes.append(p_id)
                    iterations += 1
                    continue

                # Protección turno doble: si ya hizo turno muy reciente, vuelve al final
                did_recently = (
                    not has_exception and
                    self._did_recently(
                        nombre, start_date, shifts,
                        min_gap_weeks=effective_gap,
                        ignored_period=recalculated_period)
                )
                        
                if has_exception:
                    current_pendientes.append(p_id)
                    skipped_this_week.append({'persona': nombre, 'tipo': exc_tipo})
                elif did_recently:
                    # Mandarlo al fondo de pendientes para que recupere su lugar
                    # más adelante sin duplicar turno, a menos que haya sido forzado
                    if not self._was_forced_recently(nombre, start_date, exceptions, min_gap_weeks=effective_gap):
                        current_pendientes.append(p_id)
                else:
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': nombre,
                        'saltados': skipped_this_week.copy()
                    })
                    assigned = True
                
                iterations += 1

            if not assigned and blocked_fallback:
                fallback_id, fallback_name = blocked_fallback
                warning = {
                    "semana": (start_date, end_date),
                    "persona": fallback_name,
                    "feriados": [item["feriado"] for item in blocked_fallback_reason],
                    "fechas": [item["fecha"] for item in blocked_fallback_reason],
                    "mensaje": (
                        f"{fallback_name} repite un feriado "
                        "porque no había otra persona disponible"
                    ),
                }
                self.last_warnings.append(warning)
                shifts.append({
                    'semana': (start_date, end_date),
                    'persona': fallback_name,
                    'saltados': skipped_this_week.copy(),
                    'advertencias': [warning],
                })
                current_pendientes = [
                    p_id for p_id in current_pendientes if p_id != fallback_id
                ]
                assigned = True

            if not assigned and self.personal:
                # Fallback: asignar a quien lleve más tiempo de descanso acumulado y no tenga excepción
                available_candidates = []
                for p in self.personal:
                    p_nombre = p['nombre']
                    has_exc = any(
                        exc['persona'] == p_nombre and start_date <= exc['fecha'] <= end_date
                        for exc in exceptions
                    )
                    if not has_exc and p_nombre not in restricted_people:
                        available_candidates.append(p)

                if available_candidates:
                    best_person = min(
                        available_candidates,
                        key=lambda p: self._last_shift_date(p['nombre'], start_date, shifts)
                    )
                    best_id = best_person['id']
                    best_name = best_person['nombre']
                    shifts.append({
                        'semana': (start_date, end_date),
                        'persona': best_name,
                        'saltados': skipped_this_week.copy(),
                    })
                    current_pendientes = [
                        p_id for p_id in current_pendientes if p_id != best_id
                    ]
                    if personal_ids:
                        try:
                            best_idx = personal_ids.index(best_id)
                            current_person_index = (best_idx + 1) % len(personal_ids)
                            current_siguiente_id = personal_ids[current_person_index]
                        except ValueError:
                            pass
                    assigned = True
                
            if not assigned:
                shifts.append({
                    'semana': (start_date, end_date),
                    'persona': None,
                    'saltados': skipped_this_week.copy()
                })

        # Una persona que ya recibió turno en este periodo no puede quedar
        # pendiente para reaparecer al inicio del siguiente mes.
        assigned_names = {
            shift['persona'] for shift in shifts if shift.get('persona')
        }
        assigned_ids = {
            person['id'] for person in self.personal
            if person['nombre'] in assigned_names
        }
        current_pendientes = [
            p_id for p_id in current_pendientes
            if p_id not in assigned_ids
        ]

        return shifts, current_siguiente_id, current_pendientes

    def advance_month(self, year, month, exceptions, manual_assignments=None):
        self.create_backup(f"pre_advance_{year}_{month:02d}")
        period_key = f"{year}-{month:02d}"
        if manual_assignments is None:
            manual_assignments = self.asignaciones_manuales.get(period_key, {})

        # Determinar si este periodo es anterior al frente de rotación ya registrado en historial o snapshots
        latest_recorded_period = None
        for wk in self.historial.keys():
            try:
                w_start = datetime.strptime(wk.split('_')[0], '%Y-%m-%d').date()
                p_tuple = (w_start.year, w_start.month)
                if latest_recorded_period is None or p_tuple > latest_recorded_period:
                    latest_recorded_period = p_tuple
            except Exception:
                pass

        for snap_k in self.snapshots.keys():
            try:
                parts = snap_k.split('-')
                p_tuple = (int(parts[0]), int(parts[1]))
                prev_month = p_tuple[1] - 1
                prev_year = p_tuple[0]
                if prev_month == 0:
                    prev_month = 12
                    prev_year -= 1
                closed_p = (prev_year, prev_month)
                if latest_recorded_period is None or closed_p > latest_recorded_period:
                    latest_recorded_period = closed_p
            except Exception:
                pass

        is_past_period = False
        if latest_recorded_period is not None and (year, month) < latest_recorded_period:
            is_past_period = True

        previous_exceptions = self.get_exceptions(period_key)
        previous_manual = self.get_manual_assignments(period_key)
        exception_signature = lambda items: sorted(
            (item['persona'], item['fecha'].isoformat(), item['tipo'])
            for item in items)
        manual_assignments_dict = dict(manual_assignments) if manual_assignments is not None else {}
        exceptions_changed = (
            exception_signature(exceptions) != exception_signature(previous_exceptions) or
            manual_assignments_dict != previous_manual
        )

        if period_key not in self.snapshots:
            self.snapshots[period_key] = {
                "siguiente_id": self.siguiente_id,
                "pendientes": self.pendientes.copy()
            }

        recalculation_state = self.snapshots.get(period_key) if exceptions_changed else None
        shifts, final_id, final_pendientes = self.generate_shifts(
            year, month, exceptions,
            state=recalculation_state,
            recalculate_history=exceptions_changed,
            manual_assignments=manual_assignments)
        
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
        
        # Solo actualizar el puntero global (siguiente_id y pendientes) si NO es un mes pasado
        if not is_past_period:
            self.siguiente_id = final_id
            self.pendientes = final_pendientes
        else:
            logger.info(
                "Mes pasado (%s) guardado como historial sin alterar la cola de turnos del presente (siguiente_id=%s).",
                period_key, self.siguiente_id
            )

        self.excepciones[period_key] = [
            {
                'persona': exc['persona'],
                'fecha': exc['fecha'].isoformat(),
                'tipo': exc['tipo']
            }
            for exc in exceptions
        ]
        if manual_assignments is not None:
            if manual_assignments:
                self.asignaciones_manuales[period_key] = dict(manual_assignments)
            elif period_key in self.asignaciones_manuales:
                del self.asignaciones_manuales[period_key]
        
        self.save_config()
        return True, "Turnos guardados y cola avanzada."

    # ── Person Management ──────────────────────────────────────
    def add_person(self, name):
        """Add a new person with the next sequential ID and persist to config."""
        if not isinstance(name, str):
            return None

        normalized_name = " ".join(name.split())
        if not normalized_name:
            return None

        normalized_names = {
            " ".join(person["nombre"].split()).casefold()
            for person in self.personal
        }
        if normalized_name.casefold() in normalized_names:
            return None

        max_id = max((p['id'] for p in self.personal), default=0)
        new_id = max_id + 1
        self.personal.append({"id": new_id, "nombre": normalized_name})
        self.save_config()
        return new_id

    def edit_person(self, person_id, new_name):
        """Edit the name of an existing person and update all historical records."""
        if not isinstance(new_name, str):
            return False

        normalized_name = " ".join(new_name.split())
        if not normalized_name:
            return False

        # Rechazar si el nombre normalizado ya pertenece a otra persona distinta
        for p in self.personal:
            if p['id'] != person_id and " ".join(p['nombre'].split()).casefold() == normalized_name.casefold():
                return False

        old_name = None
        for p in self.personal:
            if p['id'] == person_id:
                old_name = p['nombre']
                p['nombre'] = normalized_name
                break

        if old_name:
            if old_name != normalized_name:
                # Update inicio
                for k, v in self.inicio.items():
                    if v == old_name:
                        self.inicio[k] = normalized_name
                        
                # Update historial
                for k, v in self.historial.items():
                    if v == old_name:
                        self.historial[k] = normalized_name
                        
                # Update excepciones
                for period, exc_list in self.excepciones.items():
                    for exc in exc_list:
                        if exc.get('persona') == old_name:
                            exc['persona'] = normalized_name
                            
            self.save_config()
            return True
        return False

    def remove_person(self, person_id):
        """Remove a person from future rotation while preserving past records."""
        for i, p in enumerate(self.personal):
            if p['id'] == person_id:
                del self.personal[i]

                replacement_id = self.personal[0]["id"] if self.personal else 1

                if self.siguiente_id == person_id:
                    self.siguiente_id = replacement_id

                self.pendientes = [
                    pending_id for pending_id in self.pendientes
                    if pending_id != person_id
                ]
                for snapshot in self.snapshots.values():
                    if not isinstance(snapshot, dict):
                        continue
                    snapshot["pendientes"] = [
                        pending_id
                        for pending_id in snapshot.get("pendientes", [])
                        if pending_id != person_id
                    ]
                    if snapshot.get("siguiente_id") == person_id:
                        snapshot["siguiente_id"] = replacement_id

                self.save_config()
                return True
        return False

    def move_person_up(self, person_id):
        """Mueve a una persona una posición arriba en la lista de personal."""
        for i, p in enumerate(self.personal):
            if p['id'] == person_id:
                if i > 0:
                    self.personal[i], self.personal[i-1] = self.personal[i-1], self.personal[i]
                    self.save_config()
                    return True
                break
        return False

    def move_person_down(self, person_id):
        """Mueve a una persona una posición abajo en la lista de personal."""
        for i, p in enumerate(self.personal):
            if p['id'] == person_id:
                if i < len(self.personal) - 1:
                    self.personal[i], self.personal[i+1] = self.personal[i+1], self.personal[i]
                    self.save_config()
                    return True
                break
        return False

    def reset_historial(self, preserve_inicio=True):
        """Limpia historial, snapshots y excepciones, preservando personal e inicio por defecto."""
        self.create_backup("pre_reset")
        if not preserve_inicio:
            self.inicio = {}
        self.historial = {}
        self.snapshots = {}
        self.pendientes = []
        self.excepciones = {}
        self.asignaciones_manuales = {}

        # Recalcular siguiente_id a partir de la última asignación de inicio
        personal_ids = [p['id'] for p in self.personal]
        if self.inicio and personal_ids:
            ultima_semana = sorted(self.inicio.keys())[-1]
            ultimo_nombre = self.inicio[ultima_semana]
            ultimo_idx = next((i for i, p in enumerate(self.personal) if p['nombre'] == ultimo_nombre), None)
            if ultimo_idx is not None:
                siguiente_idx = (ultimo_idx + 1) % len(personal_ids)
                self.siguiente_id = personal_ids[siguiente_idx]
            else:
                self.siguiente_id = personal_ids[0]
        else:
            self.siguiente_id = personal_ids[0] if personal_ids else 1

        self.save_config()
        logger.info("Historial reseteado (preserve_inicio=%s). Siguiente ID: %s", preserve_inicio, self.siguiente_id)
        return True
