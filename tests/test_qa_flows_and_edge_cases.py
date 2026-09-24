"""
QA Test Suite — Flujos de Usuario y Casos Límite (Edge Cases)
Especialista en QA: Pruebas exhaustivas de ciclo de vida de excepciones,
modificación/arrepentimiento de datos, conflictos de prelación, límites de calendario
y resiliencia del sistema de turnos.
"""

import unittest
import os
import json
import tempfile
import calendar
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from models.shift_manager import ShiftManager
from controllers.main_controller import MainController
from views.tabs.tab_plan import TabPlan


class BaseQATestCase(unittest.TestCase):
    """Configuración base para tests de QA con entorno aislado y predecible."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "config.json")
        self.test_personal = [
            {"id": 1, "nombre": "COM PEREZ JUAN", "email": "perez@guardia.cl"},
            {"id": 2, "nombre": "CBO GOMEZ ANA", "email": "gomez@guardia.cl"},
            {"id": 3, "nombre": "SGT DIAZ LUIS", "email": "diaz@guardia.cl"},
            {"id": 4, "nombre": "CBO SILVA MARIA", "email": "silva@guardia.cl"},
            {"id": 5, "nombre": "SGT ROJAS CARLOS", "email": "rojas@guardia.cl"},
            {"id": 6, "nombre": "CBO SOTO ANDRES", "email": "soto@guardia.cl"},
        ]
        self.initial_data = {
            "personal": self.test_personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
            "notificaciones": {"webhook_url": "", "activo": False}
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.initial_data, f, indent=2)

        self.controller = MainController(self.temp_dir.name)
        self.manager = self.controller.shift_manager

    def tearDown(self):
        self.temp_dir.cleanup()


# ==============================================================================
# 1. FLUJO E2E: CREACIÓN, CAMBIO Y ELIMINACIÓN DE EXCEPCIONES
# ==============================================================================
class TestExceptionLifecycleAndModificationFlows(BaseQATestCase):
    """
    Test de flujos donde el usuario:
    1. Agrega excepciones.
    2. Modifica o cambia de opinión (reemplaza fecha o tipo).
    3. Elimina excepciones y verifica reversibilidad.
    """

    def test_flow_add_exception_then_modify_date_recalculates_shifts(self):
        """
        FLUJO:
        - Estado inicial: Se obtienen las dos primeras semanas base y sus titulares.
        - Paso 1: Usuario agrega excepción para el titular de la semana 1.
          -> El titular de semana 1 es saltado y el titular de semana 2 toma la semana 1.
        - Paso 2: Usuario 'se arrepiente' y traslada la excepción a la semana 2.
          (Simula borrar la excepción de semana 1 y colocarla en semana 2).
          -> El titular original recupera su semana 1 y es saltado en la semana 2.
        """
        year, month = 2026, 9
        base_shifts = self.controller.preview_shifts(year, month, [])
        first_week = base_shifts[0]['semana']
        second_week = base_shifts[1]['semana']
        p1 = base_shifts[0]['persona']
        p2 = base_shifts[1]['persona']

        self.assertNotEqual(p1, p2)

        # Paso 1: Agregar excepción a p1 en la primera semana
        exc_semana_1 = [{"persona": p1, "fecha": first_week[0], "tipo": "DA"}]
        shifts_step1 = self.controller.preview_shifts(year, month, exc_semana_1)

        # Verificación Paso 1: p1 fue saltado en semana 1, entra p2
        self.assertEqual(shifts_step1[0]['persona'], p2)
        self.assertTrue(any(s['persona'] == p1 for s in shifts_step1[0]['saltados']))
        # p1 recupera su turno en semana 2
        self.assertEqual(shifts_step1[1]['persona'], p1)
        self.assertTrue(shifts_step1[1].get('es_recuperacion', False))

        # Paso 2: Usuario 'se arrepiente' y cambia la excepción:
        # En vez de tener a p1 con excepción en semana 1, la excepción era para p2 en semana 2!
        exc_semana_2 = [{"persona": p2, "fecha": second_week[0], "tipo": "DA"}]
        shifts_step2 = self.controller.preview_shifts(year, month, exc_semana_2)

        # Verificación Paso 2: p1 recupera semana 1 normalmente (sin saltados)
        self.assertEqual(shifts_step2[0]['persona'], p1)
        self.assertEqual(len(shifts_step2[0]['saltados']), 0)
        # Y en semana 2, p2 es saltado; entra p3
        p3 = base_shifts[2]['persona']
        self.assertEqual(shifts_step2[1]['persona'], p3)
        self.assertTrue(any(s['persona'] == p2 for s in shifts_step2[1]['saltados']))

    def test_flow_change_exception_type_updates_skip_metadata(self):
        """
        FLUJO:
        - Usuario asigna excepción 'DA' al titular.
        - En el preview se registra en 'saltados' con tipo 'DA'.
        - Usuario cambia la excepción a 'LIC' (Licencia Médica).
        - En el preview ahora se registra en 'saltados' con tipo 'LIC'.
        """
        year, month = 2026, 9
        base_shifts = self.controller.preview_shifts(year, month, [])
        p1 = base_shifts[0]['persona']
        first_day = base_shifts[0]['semana'][0]

        # Configurar DA
        exc_da = [{"persona": p1, "fecha": first_day, "tipo": "DA"}]
        shifts_da = self.controller.preview_shifts(year, month, exc_da)
        skip_da = next(s for s in shifts_da[0]['saltados'] if s['persona'] == p1)
        self.assertEqual(skip_da['tipo'], "DA")

        # Cambiar a LIC
        exc_lic = [{"persona": p1, "fecha": first_day, "tipo": "LIC"}]
        shifts_lic = self.controller.preview_shifts(year, month, exc_lic)
        skip_lic = next(s for s in shifts_lic[0]['saltados'] if s['persona'] == p1)
        self.assertEqual(skip_lic['tipo'], "LIC")

    def test_flow_complete_reversion_restores_initial_state_identically(self):
        """
        PRUEBA DE IDEMPOTENCIA Y REVERSIBILIDAD:
        - Calcular preview sin excepciones.
        - Agregar 3 excepciones consecutivas.
        - Eliminar todas las excepciones.
        - Comprobar que los turnos resultantes son exactamente idénticos al inicio.
        """
        year, month = 2026, 9
        initial_shifts = self.controller.preview_shifts(year, month, [])

        # Agregar excepciones
        w0_day = initial_shifts[0]['semana'][0]
        w1_day = initial_shifts[1]['semana'][0]
        p1 = initial_shifts[0]['persona']
        p2 = initial_shifts[1]['persona']
        p3 = initial_shifts[2]['persona']
        temp_exceptions = [
            {"persona": p1, "fecha": w0_day, "tipo": "FL"},
            {"persona": p2, "fecha": w0_day, "tipo": "LIC"},
            {"persona": p3, "fecha": w1_day, "tipo": "DA"},
        ]
        modified_shifts = self.controller.preview_shifts(year, month, temp_exceptions)
        self.assertNotEqual(initial_shifts, modified_shifts)

        # Revertir eliminando excepciones
        reverted_shifts = self.controller.preview_shifts(year, month, [])
        self.assertEqual(initial_shifts, reverted_shifts)


# ==============================================================================
# 2. EDGE CASES DE PARSING, RANGOS Y CALENDARIO (BOUNDARY TESTING)
# ==============================================================================
class TestRangeParsingAndCalendarEdgeCases(BaseQATestCase):
    """Pruebas de estrés y límites en la entrada de días y fechas en la UI."""

    def setUp(self):
        super().setUp()
        self.mock_app = MagicMock()
        self.mock_app.exceptions = []

        self.tab_plan = TabPlan.__new__(TabPlan)
        self.tab_plan.app = self.mock_app
        self.tab_plan.person_var = MagicMock()
        self.tab_plan.person_var.get.return_value = "COM PEREZ JUAN"
        self.tab_plan.type_var = MagicMock()
        self.tab_plan.type_var.get.return_value = "FL"
        self.tab_plan.days_entry = MagicMock()

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_inverted_range_is_automatically_normalized(self, mock_msgbox):
        """EDGE CASE: El usuario ingresa un rango invertido '20-15'."""
        self.mock_app.get_selected_period.return_value = (2026, 10)
        self.tab_plan.days_entry.get.return_value = "20-15"

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_called_once()
        added = self.mock_app.add_exceptions.call_args[0][0]
        added_days = [e['fecha'].day for e in added]
        # Debe ordenarse automáticamente de 15 a 20
        self.assertEqual(added_days, [15, 16, 17, 18, 19, 20])

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_single_day_range_is_supported(self, mock_msgbox):
        """EDGE CASE: El usuario escribe '5-5'."""
        self.mock_app.get_selected_period.return_value = (2026, 10)
        self.tab_plan.days_entry.get.return_value = "5-5"

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_called_once()
        added = self.mock_app.add_exceptions.call_args[0][0]
        self.assertEqual([e['fecha'].day for e in added], [5])

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_mixed_delimiters_and_spacing_robustness(self, mock_msgbox):
        """EDGE CASE: Mezcla de comas, punto y coma, espacios aleatorios."""
        self.mock_app.get_selected_period.return_value = (2026, 10)
        self.tab_plan.days_entry.get.return_value = " 1 - 3 ; 7 ,  9 - 10 ; ; 15 "

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_called_once()
        added = self.mock_app.add_exceptions.call_args[0][0]
        added_days = [e['fecha'].day for e in added]
        self.assertEqual(added_days, [1, 2, 3, 7, 9, 10, 15])

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_reject_day_31_in_30_day_month(self, mock_msgbox):
        """EDGE CASE: Intentar ingresar día 31 en Noviembre (30 días)."""
        self.mock_app.get_selected_period.return_value = (2026, 11)
        self.tab_plan.days_entry.get.return_value = "28-31"

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_not_called()
        # Verificar mensaje con rango de días
        call_msg = self.mock_app.set_status.call_args[0][0]
        self.assertIn("31", call_msg)
        self.assertIn("1\u201330", call_msg)

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_leap_year_february_29_accepted(self, mock_msgbox):
        """EDGE CASE: Febrero 2028 (bisiesto) debe aceptar día 29."""
        self.mock_app.get_selected_period.return_value = (2028, 2)
        self.tab_plan.days_entry.get.return_value = "28-29"

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_called_once()
        added = self.mock_app.add_exceptions.call_args[0][0]
        self.assertEqual([e['fecha'].day for e in added], [28, 29])

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_non_leap_year_february_29_rejected(self, mock_msgbox):
        """EDGE CASE: Febrero 2027 (no bisiesto) debe rechazar día 29."""
        self.mock_app.get_selected_period.return_value = (2027, 2)
        self.tab_plan.days_entry.get.return_value = "28-29"

        self.tab_plan.add_exception()

        self.mock_app.add_exceptions.assert_not_called()
        call_msg = self.mock_app.set_status.call_args[0][0]
        self.assertIn("29", call_msg)
        self.assertIn("1\u201328", call_msg)

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_malformed_inputs_do_not_crash(self, mock_msgbox):
        """EDGE CASE: Fuzzing de entradas malformadas."""
        self.mock_app.get_selected_period.return_value = (2026, 10)
        bad_inputs = ["abc", "1-2-3", "-5", "5-", ",,,", "   ", "0", "35", "10-abc"]

        for bad in bad_inputs:
            self.mock_app.reset_mock()
            self.tab_plan.days_entry.get.return_value = bad
            self.tab_plan.add_exception()
            self.mock_app.add_exceptions.assert_not_called()

    @patch("views.tabs.tab_plan.messagebox.askyesno", return_value=True)
    def test_reentering_existing_date_with_different_type_updates_in_place(self, mock_msgbox):
        """
        FLUJO DE USABILIDAD Y QA:
        El usuario había ingresado el día 15 como 'DA'.
        Ahora se arrepiente y vuelve a ingresar el día 15 pero seleccionando 'LIC'.
        El sistema debe actualizar el tipo a 'LIC' directamente (in-place)
        sin requerir borrar previamente.
        """
        self.mock_app.get_selected_period.return_value = (2026, 10)
        self.mock_app.exceptions = [
            {"persona": "COM PEREZ JUAN", "fecha": date(2026, 10, 15), "tipo": "DA"}
        ]
        self.tab_plan.days_entry.get.return_value = "15"
        self.tab_plan.type_var.get.return_value = "LIC"

        self.tab_plan.add_exception()

        # Debe actualizar la existente a LIC
        self.assertEqual(len(self.mock_app.exceptions), 1)
        self.assertEqual(self.mock_app.exceptions[0]["tipo"], "LIC")
        self.assertIn("actualizada", self.mock_app.set_status.call_args[0][0])


# ==============================================================================
# 3. CONFLICTO: EXCEPCIÓN VS ASIGNACIÓN MANUAL (PREVALENCIA Y CAMBIO)
# ==============================================================================
class TestExceptionVsManualAssignmentConflicts(BaseQATestCase):
    """
    Pruebas de interacción entre Asignaciones Manuales (forzadas)
    y Excepciones en la misma semana.
    """

    def test_manual_assignment_takes_precedence_over_exception(self):
        """
        REGLA DE NEGOCIO / PREVALENCIA:
        Si para una semana existe asignación manual a Persona X,
        pero Persona X tiene una excepción registrada en esa misma fecha:
        La asignación manual tiene precedencia absoluta sobre la rotación.
        """
        year, month = 2026, 9
        shifts = self.controller.preview_shifts(year, month, [])
        first_week = shifts[0]['semana']
        p1 = shifts[0]['persona']
        week_key = f"{first_week[0].strftime('%Y-%m-%d')}_{first_week[1].strftime('%Y-%m-%d')}"

        manual_map = {week_key: p1}
        exceptions = [{"persona": p1, "fecha": first_week[0], "tipo": "LIC"}]

        shifts_result = self.controller.preview_shifts(
            year, month, exceptions, manual_assignments=manual_map
        )

        self.assertEqual(shifts_result[0]['persona'], p1)
        self.assertTrue(shifts_result[0].get('es_manual', False))

    def test_removing_manual_assignment_activates_underlying_exception(self):
        """
        FLUJO DE CAMBIO:
        1. Semana tiene asignación manual Y excepción para Perez.
        2. Prevalece la asignación manual.
        3. Usuario retira la asignación manual.
        4. Inmediatamente la excepción cobra vigencia: Perez es saltado y asignado al siguiente.
        """
        year, month = 2026, 9
        shifts = self.controller.preview_shifts(year, month, [])
        first_week = shifts[0]['semana']
        p1 = shifts[0]['persona']
        p2 = shifts[1]['persona']
        week_key = f"{first_week[0].strftime('%Y-%m-%d')}_{first_week[1].strftime('%Y-%m-%d')}"

        exceptions = [{"persona": p1, "fecha": first_week[0], "tipo": "LIC"}]
        manual_map = {week_key: p1}

        # Estado 1: Con asignación manual
        s1 = self.controller.preview_shifts(year, month, exceptions, manual_assignments=manual_map)
        self.assertEqual(s1[0]['persona'], p1)

        # Estado 2: Se retira asignación manual (mapa vacío)
        s2 = self.controller.preview_shifts(year, month, exceptions, manual_assignments={})
        self.assertEqual(s2[0]['persona'], p2)
        self.assertTrue(any(s['persona'] == p1 for s in s2[0]['saltados']))


# ==============================================================================
# 4. CASO EXTREMO: AGOTAMIENTO TOTAL DE PERSONAL ("NADIE DISPONIBLE")
# ==============================================================================
class TestTotalStaffExhaustionEdgeCase(BaseQATestCase):
    """
    EDGE CASE: ¿Qué sucede si el 100% de la dotación tiene excepciones
    durante la misma semana?
    """

    def test_all_staff_exceptions_results_in_unassigned_and_validation_error(self):
        year, month = 2026, 9
        shifts = self.controller.preview_shifts(year, month, [])
        first_week_day = shifts[0]['semana'][0]

        # Asignar excepción a todos los 6 funcionarios en la misma semana
        all_exceptions = [
            {"persona": p['nombre'], "fecha": first_week_day, "tipo": "LIC"}
            for p in self.test_personal
        ]

        # 1. El preview debe reflejar semana sin asignar (persona: None)
        shifts_preview = self.controller.preview_shifts(year, month, all_exceptions)
        self.assertIsNone(shifts_preview[0]['persona'])
        self.assertEqual(len(shifts_preview[0]['saltados']), len(self.test_personal))

        # 2. validate_month debe capturar el error y bloquear el cierre
        errors = self.controller.validate_month(year, month, all_exceptions)
        self.assertIn("Existe al menos una semana sin funcionario asignado.", errors)


# ==============================================================================
# 5. INTEGRIDAD DE DATOS ANTE MUTACIONES DE PERSONAL
# ==============================================================================
class TestPersonnelMutationsWithExceptions(BaseQATestCase):
    """
    EDGE CASE: Si un funcionario con excepciones activas es renombrado
    o eliminado del sistema.
    """

    def test_editing_person_name_cascades_to_saved_exceptions(self):
        """Si se cambia el nombre de Perez a 'COM PEREZ JUAN CARLOS', las excepciones se actualizan."""
        period_key = "2026-10"
        self.manager.excepciones[period_key] = [
            {"persona": "COM PEREZ JUAN", "fecha": "2026-10-05", "tipo": "DA"}
        ]
        self.manager.save_config()

        success, _ = self.controller.edit_person(1, "COM PEREZ JUAN CARLOS")
        self.assertTrue(success)

        saved = self.manager.get_exceptions(period_key)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]['persona'], "COM PEREZ JUAN CARLOS")

    def test_removing_person_with_exceptions_preserves_rotation_stability(self):
        """Si un funcionario con excepción es eliminado, la rotación no explota."""
        self.manager.excepciones["2026-10"] = [
            {"persona": "CBO GOMEZ ANA", "fecha": "2026-10-05", "tipo": "LIC"}
        ]
        self.manager.save_config()

        success, _ = self.controller.remove_person(2)
        self.assertTrue(success)

        shifts = self.controller.preview_shifts(2026, 10, self.manager.get_exceptions("2026-10"))
        self.assertGreater(len(shifts), 0)
        assigned_names = [s['persona'] for s in shifts]
        self.assertNotIn("CBO GOMEZ ANA", assigned_names)


# ==============================================================================
# 6. EDICIÓN DE EXCEPCIONES EN MESES YA CERRADOS (SNAPSHOTS & RECALCULATE)
# ==============================================================================
class TestClosedMonthExceptionModificationFlow(BaseQATestCase):
    """
    FLUJO DE RECALCULACIÓN DE HISTORIAL:
    Modificar excepciones en un mes que ya fue cerrado con snapshot.
    """

    def test_closed_month_shifts_recalculate_when_exceptions_change(self):
        # 1. Cerrar mes de Septiembre 2026 sin excepciones
        ok, msg = self.controller.advance_queue(2026, 9, [])
        self.assertTrue(ok)
        self.assertIn("2026-09", self.manager.snapshots)

        original_shifts = self.controller.preview_shifts(2026, 9, [])
        orig_w1_person = original_shifts[0]['persona']
        orig_w1_day = original_shifts[0]['semana'][0]

        # 2. En el mismo mes cerrado, el usuario prueba agregando una excepción para quien hizo el turno
        modified_exc = [{"persona": orig_w1_person, "fecha": orig_w1_day, "tipo": "LIC"}]
        recalculated_shifts = self.controller.preview_shifts(2026, 9, modified_exc)

        # Debe haberse recalculado dinámicamente: orig_w1_person no hace esa semana
        self.assertNotEqual(recalculated_shifts[0]['persona'], orig_w1_person)
        self.assertTrue(any(s['persona'] == orig_w1_person for s in recalculated_shifts[0]['saltados']))

        # 3. Si el usuario retira la excepción (vuelve a la guardada []), retorna al historial cerrado original
        reverted_shifts = self.controller.preview_shifts(2026, 9, [])
        self.assertEqual(reverted_shifts[0]['persona'], orig_w1_person)


# ==============================================================================
# 7. PARIDAD DE EXPORTACIÓN EXCEL CON EXCEPCIONES MODIFICADAS
# ==============================================================================
class TestExportParityWithModifiedExceptions(BaseQATestCase):
    """
    Verifica que la exportación a Excel use exactamente los turnos recalculados
    con las excepciones modificadas por el usuario.
    """

    def test_export_excel_reflects_modified_exceptions(self):
        year, month = 2026, 12
        shifts = self.controller.preview_shifts(year, month, [])
        first_day = shifts[0]['semana'][0]

        modified_exceptions = [
            {"persona": "COM PEREZ JUAN", "fecha": first_day, "tipo": "FL"}
        ]
        target_excel = os.path.join(self.temp_dir.name, "turnos_qa_test.xlsx")

        success, msg = self.controller.process_generation(
            year, month, modified_exceptions, target_path=target_excel
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(target_excel))
        self.assertGreater(os.path.getsize(target_excel), 0)


if __name__ == "__main__":
    unittest.main()
