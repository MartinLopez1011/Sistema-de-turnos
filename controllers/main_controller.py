import os
from datetime import date
from models.shift_manager import ShiftManager
from utils.excel_handler import ExcelHandler
from utils.logger import get_logger

logger = get_logger("controller")

class MainController:
    def __init__(self, root_path):
        self.root_path = root_path
        self.config_path = os.path.join(root_path, 'config.json')
        self.output_path = os.path.join(root_path, 'turnos_generados.xlsx')
        
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

    def set_starting_person(self, person_name):
        return self.shift_manager.set_starting_person(person_name)

    def add_person(self, name):
        new_id = self.shift_manager.add_person(name)
        return new_id is not None, f"Persona añadida con ID {new_id}" if new_id else "Error al añadir persona"

    def edit_person(self, person_id, new_name):
        success = self.shift_manager.edit_person(person_id, new_name)
        return success, "Persona editada" if success else "Persona no encontrada"

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

    def preview_shifts(self, year, month, exceptions):
        target_key = f"{year}-{month:02d}"
        today = date.today()
        target_is_future = (year, month) > (today.year, today.month)

        def exception_signature(items):
            return sorted(
                (item['persona'], item['fecha'].isoformat(), item['tipo'])
                for item in items)

        saved_exceptions = self.shift_manager.get_exceptions(target_key)
        exceptions_changed = (
            exception_signature(exceptions) != exception_signature(saved_exceptions))

        # Un mes cerrado puede editarse: si cambiaron sus excepciones,
        # recalcular desde el estado guardado al inicio del periodo.
        if target_key in self.shift_manager.snapshots and exceptions_changed:
            state = self.shift_manager.snapshots[target_key]
            shifts, _, _ = self.shift_manager.generate_shifts(
                year, month, exceptions, state=state,
                recalculate_history=True)
            return shifts

        # A future month without snapshot must continue after the current month,
        # otherwise each preview starts again from the global pointer.
        if not target_is_future or target_key in self.shift_manager.snapshots:
            shifts, _, _ = self.shift_manager.generate_shifts(year, month, exceptions)
            return shifts

        state = {
            "siguiente_id": self.shift_manager.siguiente_id,
            "pendientes": self.shift_manager.pendientes.copy()
        }
        preview_year, preview_month = today.year, today.month

        while (preview_year, preview_month) <= (year, month):
            preview_key = f"{preview_year}-{preview_month:02d}"
            period_exceptions = (
                exceptions if preview_key == target_key
                else self.shift_manager.get_exceptions(preview_key)
            )
            shifts, final_id, final_pending = self.shift_manager.generate_shifts(
                preview_year, preview_month, period_exceptions, state=state)
            if preview_key == target_key:
                return shifts

            state = {
                "siguiente_id": final_id,
                "pendientes": final_pending
            }
            if preview_month == 12:
                preview_year += 1
                preview_month = 1
            else:
                preview_month += 1

        return []

    def process_generation(self, year, month, exceptions, target_path=None):
        try:
            # 1. Generar los turnos basados en el mes y excepciones (forma pura)
            shifts, _, _ = self.shift_manager.generate_shifts(year, month, exceptions)
            warnings = self.shift_manager.last_warnings
            
            # 2. Inicializar manejador de Excel
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            nombre_mes = meses[month - 1]
            dynamic_output = target_path or os.path.join(self.root_path, f"turnos_{nombre_mes}_{year}.xlsx")
            
            excel_handler = ExcelHandler(dynamic_output, self.shift_manager.personal)
            excel_handler.load_template()
            
            # 3. Escribir los datos
            excel_handler.write_shifts(shifts, exceptions, year, month)
            
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

    def advance_queue(self, year, month, exceptions):
        try:
            self.shift_manager.advance_month(year, month, exceptions)
            warnings = self.shift_manager.last_warnings
            if warnings:
                return True, (
                    "Mes guardado con advertencias: "
                    f"{len(warnings)} feriado repetido por falta de alternativa"
                )
            return True, "Cola avanzada exitosamente. Empezamos nuevo mes."
        except Exception as e:
            return False, f"Error: {str(e)}"
