import os
from datetime import date
from models.shift_manager import ShiftManager
from utils.excel_handler import ExcelHandler
from utils.logger import get_logger
from utils.email_notifier import is_valid_email
from views.theme import MESES

logger = get_logger("controller")

class MainController:
    def __init__(self, root_path):
        self.root_path = root_path
        self.config_path = os.path.join(root_path, 'config.json')
        self.shift_manager = ShiftManager(self.config_path)

    def get_personal_list(self):
        return [p['nombre'] for p in self.shift_manager.personal]

    def get_all_persons(self):
        return self.shift_manager.personal


    def get_starting_person(self):
        return self.shift_manager.get_person_by_id(self.shift_manager.siguiente_id)

    def get_saved_exceptions(self):
        return {
            period_key: self.shift_manager.get_exceptions(period_key)
            for period_key in self.shift_manager.excepciones
        }

    def get_saved_manual_assignments(self):
        return {
            period_key: self.shift_manager.get_manual_assignments(period_key)
            for period_key in self.shift_manager.asignaciones_manuales
        }

    def set_starting_person(self, person_name):
        return self.shift_manager.set_starting_person(person_name)

    def add_person(self, name, email=""):
        if not isinstance(name, str) or not " ".join(name.split()):
            return False, "El nombre no puede estar vacío"
        clean_name = " ".join(name.split())
        for p in self.shift_manager.personal:
            if " ".join(p['nombre'].split()).casefold() == clean_name.casefold():
                return False, f"Ya existe un funcionario con el nombre '{clean_name}'"
        
        clean_email = email.strip() if isinstance(email, str) else ""
        if clean_email and not is_valid_email(clean_email):
            return False, "El formato del correo electrónico no es válido (ej: usuario@dominio.cl)"

        new_id = self.shift_manager.add_person(clean_name, email=clean_email)
        return new_id is not None, f"Persona añadida con ID {new_id}" if new_id else "Error al añadir persona"

    def edit_person(self, person_id, new_name, new_email=None):
        if not isinstance(new_name, str) or not " ".join(new_name.split()):
            return False, "El nombre no puede estar vacío"
        clean_name = " ".join(new_name.split())
        for p in self.shift_manager.personal:
            if p['id'] != person_id and " ".join(p['nombre'].split()).casefold() == clean_name.casefold():
                return False, f"Ya existe un funcionario con el nombre '{clean_name}'"

        clean_email = None
        if new_email is not None:
            clean_email = new_email.strip() if isinstance(new_email, str) else ""
            if clean_email and not is_valid_email(clean_email):
                return False, "El formato del correo electrónico no es válido (ej: usuario@dominio.cl)"

        success = self.shift_manager.edit_person(person_id, clean_name, new_email=clean_email)
        return success, f"Funcionario editado: {clean_name}" if success else "Funcionario no encontrado"

    def validate_all_emails_registered(self):
        return self.shift_manager.validate_all_emails_registered()

    def get_notification_settings(self):
        return self.shift_manager.get_notification_settings()

    def set_notification_settings(self, webhook_url, activo=True):
        success = self.shift_manager.set_notification_settings(webhook_url, activo)
        if not success:
            return False, "No se pudo guardar la configuración de notificaciones"
        return True, "Configuración de notificaciones guardada"

    def get_manual_motive(self, period_key, week_key):
        return self.shift_manager.get_manual_motive(period_key, week_key)

    def get_all_manual_motives(self, period_key):
        return dict(self.shift_manager.asignaciones_manuales_motivos.get(period_key, {}))

    def remove_person(self, person_id):
        success = self.shift_manager.remove_person(person_id)
        return success, "Persona eliminada" if success else "Persona no encontrada"

    def move_person_up(self, person_id):
        success = self.shift_manager.move_person_up(person_id)
        return success, "Orden actualizado" if success else "Error al actualizar"

    def move_person_down(self, person_id):
        success = self.shift_manager.move_person_down(person_id)
        return success, "Orden actualizado" if success else "Error al actualizar"

    def reset_historial(self, preserve_inicio=True):
        success = self.shift_manager.reset_historial(preserve_inicio=preserve_inicio)
        return success, "Historial y configuraciones eliminadas correctamente" if success else "Error al limpiar historial"

    def list_backups(self):
        return self.shift_manager.list_backups()

    def create_backup(self, tag=None):
        return self.shift_manager.create_backup(tag)

    def restore_backup(self, backup_path):
        return self.shift_manager.restore_backup(backup_path)

    def get_audit_entries(self, limit=20):
        return list(reversed(self.shift_manager.auditoria[-limit:]))

    def preview_shifts(self, year, month, exceptions, manual_assignments=None):
        target_key = f"{year}-{month:02d}"

        def exception_signature(items):
            return sorted(
                (item['persona'], item['fecha'].isoformat(), item['tipo'])
                for item in items)

        saved_exceptions = self.shift_manager.get_exceptions(target_key)
        saved_manual = self.shift_manager.get_manual_assignments(target_key)
        active_manual = manual_assignments if manual_assignments is not None else saved_manual
        exceptions_changed = (
            exception_signature(exceptions) != exception_signature(saved_exceptions) or
            active_manual != saved_manual)

        initial_state = self.shift_manager.get_initial_state_for_period(year, month)

        # Un mes cerrado puede editarse: si cambiaron sus excepciones o asignaciones manuales,
        # recalcular desde el estado guardado al inicio del periodo.
        if target_key in self.shift_manager.snapshots and exceptions_changed:
            shifts, _, _ = self.shift_manager.generate_shifts(
                year, month, exceptions, state=initial_state,
                recalculate_history=True, manual_assignments=active_manual)
            return shifts

        shifts, _, _ = self.shift_manager.generate_shifts(
            year, month, exceptions, state=initial_state,
            manual_assignments=active_manual)
        return shifts

    def validate_month(self, year, month, exceptions, manual_assignments=None):
        return self.shift_manager.validate_month(
            year, month, exceptions, manual_assignments=manual_assignments
        )

    def process_generation(self, year, month, exceptions, manual_assignments=None, target_path=None, manual_motives=None):
        try:
            period_key = f"{year}-{month:02d}"
            active_manual = manual_assignments if manual_assignments is not None else self.shift_manager.asignaciones_manuales.get(period_key, {})
            active_motives = manual_motives if manual_motives is not None else self.shift_manager.asignaciones_manuales_motivos.get(period_key, {})

            # 1. Generar los turnos usando preview_shifts para garantizar paridad exacta con la UI
            shifts = self.preview_shifts(year, month, exceptions, manual_assignments=active_manual)
            warnings = self.shift_manager.last_warnings

            # 1.1 Detectar cambios manuales y determinar a quién reemplazan
            has_manual = any(sh.get('es_manual') or sh.get('es_forzado') for sh in shifts) or bool(active_manual)
            manual_changes = []
            if has_manual:
                shifts_auto = self.preview_shifts(year, month, exceptions, manual_assignments={})
                orig_by_week = {
                    f"{s['semana'][0].isoformat()}_{s['semana'][1].isoformat()}": s.get('persona', 'Sin asignar')
                    for s in shifts_auto
                }
                for sh in shifts:
                    s_d, e_d = sh['semana']
                    wk = f"{s_d.isoformat()}_{e_d.isoformat()}"
                    if sh.get('es_manual') or sh.get('es_forzado') or (active_manual and wk in active_manual):
                        orig_p = orig_by_week.get(wk, "Rotación automática")
                        mot = (active_motives.get(wk) if active_motives else None) or sh.get('motivo') or "No especificado"
                        manual_changes.append({
                            "semana": (s_d, e_d),
                            "nuevo": sh.get('persona', 'Sin asignar'),
                            "anterior": orig_p,
                            "motivo": mot
                        })
            
            # 2. Inicializar manejador de Excel garantizando paridad con personal histórico
            nombre_mes = MESES[month - 1]
            dynamic_output = target_path or os.path.join(self.root_path, f"turnos_{nombre_mes}_{year}.xlsx")
            
            # Combinar personal activo con personas presentes en turnos o excepciones históricas
            export_personal = [dict(p) for p in self.shift_manager.personal]
            existing_names = {p['nombre'] for p in export_personal}
            for sh in shifts:
                p_name = sh.get('persona')
                if p_name and p_name != "NADIE DISPONIBLE" and p_name not in existing_names:
                    export_personal.append({"id": None, "nombre": p_name})
                    existing_names.add(p_name)
            for exc in exceptions:
                p_name = exc.get('persona')
                if p_name and p_name not in existing_names:
                    export_personal.append({"id": None, "nombre": p_name})
                    existing_names.add(p_name)

            with ExcelHandler(dynamic_output, export_personal) as excel_handler:
                excel_handler.load_template()
                
                # 3. Escribir los datos
                excel_handler.write_shifts(shifts, exceptions, year, month, manual_changes=manual_changes)
                
                # 4. Guardar archivo
                excel_handler.save_report()
            logger.info("Excel exportado exitosamente a %s", dynamic_output)
            
            if warnings:
                return True, (
                    "Turnos exportados con advertencias: "
                    f"{len(warnings)} feriado repetido por falta de alternativa"
                )
            return True, f"Turnos exportados a Excel exitosamente ({os.path.basename(dynamic_output)})"
            
        except PermissionError:
            file_name = os.path.basename(dynamic_output) if 'dynamic_output' in locals() else "el archivo"
            logger.error("Error de permisos al escribir Excel %s", file_name)
            return False, (
                f"No se pudo guardar '{file_name}'. El archivo está abierto en Microsoft Excel u otra aplicación. "
                "Por favor ciérralo e intenta nuevamente."
            )
        except Exception as e:
            logger.error("Error en process_generation: %s", e, exc_info=True)
            return False, f"Error: {str(e)}"

    def advance_queue(self, year, month, exceptions, manual_assignments=None, manual_motives=None):
        try:
            self.shift_manager.advance_month(
                year, month, exceptions,
                manual_assignments=manual_assignments,
                manual_motives=manual_motives
            )
            warnings = self.shift_manager.last_warnings
            if warnings:
                return True, (
                    "Mes guardado con advertencias: "
                    f"{len(warnings)} feriado repetido por falta de alternativa"
                )
            return True, "Cola avanzada exitosamente. Empezamos nuevo mes."
        except Exception as e:
            return False, f"Error: {str(e)}"
