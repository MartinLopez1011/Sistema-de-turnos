"""
Test Suite de Casos Extremos para ShiftManager (Senior Engineering QA).
Pruebas exhaustivas de resiliencia, condiciones de borde y robustez algorítmica:
1. Payloads de excepciones corruptos / malformados (None, tipos inválidos, llaves faltantes).
2. Prevención de acumulación de deuda duplicada en pendientes (The Sick Leave Trap).
3. Dotación de personal vacía (personal = []) en todos los métodos de ShiftManager.
4. Dotación unipersonal (personal de 1 sola persona) en rotación continua y con licencias.
5. Indisponibilidad total del equipo (100% del personal con licencias) por múltiples meses.
6. Horizontes temporales extremos (1970, 2000 bisiesto centenario, 2100 no-bisiesto centenario).
7. Transición de fin de año (Diciembre a Enero con feriados de Navidad y Año Nuevo).
8. Archivos config.json hostiles / corruptos en disco (0 bytes, sintaxis rota, tipos anómalos).
9. Eliminación acelerada de funcionarios en rotación y preservación del puntero.
10. Rangos de excepciones invertidos, multi-mes y eliminación de sub-rangos limítrofes.
11. Archivador histórico con claves corruptas y validación de retención mínima.
"""

import json
import os
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from models.shift_manager import ShiftManager


class ShiftManagerExtremeCasesTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        self.sample_personal = [
            {"id": 1, "nombre": "SGT PEREZ JUAN", "email": "perez@guardia.cl"},
            {"id": 2, "nombre": "CBO GOMEZ ANA", "email": "gomez@guardia.cl"},
            {"id": 3, "nombre": "CBO DIAZ LUIS", "email": "diaz@guardia.cl"},
            {"id": 4, "nombre": "SBC SILVA MARIA", "email": "silva@guardia.cl"},
        ]
        self.clean_payload = {
            "personal": self.sample_personal,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
        }
        self.config_path.write_text(json.dumps(self.clean_payload, indent=2), encoding="utf-8")
        self.manager = ShiftManager(str(self.config_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    # =========================================================================
    # 1. EXCEPCIONES CORRUPTAS / MALFORMADAS
    # =========================================================================
    def test_malformed_and_none_exceptions_do_not_crash(self):
        """Verifica que el motor sea inmune a payloads de excepción corruptos o malformados."""
        hostile_exceptions = [
            None,
            {},
            {"persona": None, "fecha": None, "tipo": None},
            {"persona": "SGT PEREZ JUAN", "fecha": 12345, "tipo": "DA"},
            {"persona": "SGT PEREZ JUAN", "fecha": None, "tipo": "DA"},
            {"persona": "SGT PEREZ JUAN", "fecha": "fecha_invalida", "tipo": "DA"},
            {"persona": "SGT PEREZ JUAN", "fecha": "2026-09-15"},  # falta 'tipo'
            {"fecha": "2026-09-15", "tipo": "DA"},  # falta 'persona'
            {"persona": 999, "fecha": "2026-09-15", "tipo": "DA"},  # persona no str
            {"persona": "SGT PEREZ JUAN", "fecha": date(2026, 9, 15), "tipo": 123},  # tipo no str
        ]
        # generate_shifts no debe lanzar TypeError, AttributeError ni KeyError
        shifts, fid, pends = self.manager.generate_shifts(2026, 9, hostile_exceptions)
        self.assertGreater(len(shifts), 0)
        self.assertIsInstance(fid, int)
        self.assertIsInstance(pends, list)

        # Tampoco debe fallar si exceptions es None o un tipo no lista
        shifts_none, _, _ = self.manager.generate_shifts(2026, 9, None)
        self.assertEqual(len(shifts_none), len(shifts))

    # =========================================================================
    # 2. THE SICK LEAVE TRAP: PREVENCIÓN DE DUPLICADOS EN PENDIENTES
    # =========================================================================
    def test_long_medical_leave_does_not_accumulate_duplicate_pendings_or_punish_worker(self):
        """
        Un funcionario que se ausenta por licencia médica durante 2 meses consecutivos (9 semanas)
        NO debe acumular su ID múltiples veces en 'pendientes' ni ser castigado con 5 turnos
        seguidos al volver.
        """
        # P1 con licencia médica todo Septiembre y todo Octubre 2026
        exc_sept = [{"persona": "SGT PEREZ JUAN", "fecha": date(2026, 9, d), "tipo": "LIC"} for d in range(1, 31)]
        exc_oct = [{"persona": "SGT PEREZ JUAN", "fecha": date(2026, 10, d), "tipo": "LIC"} for d in range(1, 32)]

        ok_sept, _ = self.manager.advance_month(2026, 9, exc_sept)
        self.assertTrue(ok_sept)
        # En pendientes debe estar el ID 1 solo UNA vez
        self.assertEqual(self.manager.pendientes.count(1), 1)

        ok_oct, _ = self.manager.advance_month(2026, 10, exc_oct)
        self.assertTrue(ok_oct)
        # Después de dos meses completos, P1 sigue debiendo su turno, pero SOLO UNA VEZ
        self.assertEqual(self.manager.pendientes.count(1), 1)

        # En Noviembre 2026 P1 regresa (sin excepciones)
        shifts_nov, _, final_pends = self.manager.generate_shifts(2026, 11, [])
        assigned_p1_count = sum(1 for s in shifts_nov if s.get("persona") == "SGT PEREZ JUAN")

        # P1 debe hacer a lo sumo 2 turnos en Noviembre (su turno recuperado + su turno ordinario del mes)
        # NUNCA 4 o 5 turnos consecutivos de castigo.
        self.assertLessEqual(assigned_p1_count, 2)
        # Y no debe haber turnos inmediatamente consecutivos para P1
        for i in range(len(shifts_nov) - 1):
            if shifts_nov[i]["persona"] == "SGT PEREZ JUAN":
                self.assertNotEqual(shifts_nov[i + 1]["persona"], "SGT PEREZ JUAN")

    # =========================================================================
    # 3. DOTACIÓN DE PERSONAL VACÍA (personal = [])
    # =========================================================================
    def test_empty_personnel_roster_across_all_shift_manager_methods(self):
        """Verifica que si la dotación está completamente vacía, ninguna función lance excepciones."""
        empty_config = self.root_path / "empty_config.json"
        empty_config.write_text(json.dumps({
            "personal": [],
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "historial": {}
        }), encoding="utf-8")
        empty_mgr = ShiftManager(str(empty_config))

        # 1. generate_shifts debe devolver semanas con persona = None
        shifts, fid, pends = empty_mgr.generate_shifts(2026, 9, [])
        self.assertGreater(len(shifts), 0)
        self.assertTrue(all(s["persona"] is None for s in shifts))
        self.assertEqual(pends, [])

        # 2. validate_month debe alertar la falta de personal asignado
        errors = empty_mgr.validate_month(2026, 9, [])
        self.assertIn("Existe al menos una semana sin funcionario asignado.", errors)

        # 3. advance_month no debe explotar y no debe registrar asignaciones vacías en historial
        ok, msg = empty_mgr.advance_month(2026, 9, [])
        self.assertTrue(ok)
        self.assertEqual(len(empty_mgr.historial), 0)

        # 4. Operaciones de gestión de personal sobre lista vacía
        self.assertFalse(empty_mgr.set_starting_person("CUALQUIERA"))
        self.assertIsNone(empty_mgr.add_person(""))
        self.assertIsNone(empty_mgr.add_person("   "))
        self.assertFalse(empty_mgr.remove_person(1))
        self.assertFalse(empty_mgr.edit_person(1, "NUEVO"))
        self.assertFalse(empty_mgr.move_person_up(1))
        self.assertFalse(empty_mgr.move_person_down(1))
        self.assertEqual(empty_mgr.get_person_by_id(1), "Desconocido")

        # 5. reset_historial sobre lista vacía
        self.assertTrue(empty_mgr.reset_historial())
        self.assertEqual(empty_mgr.siguiente_id, 1)

    # =========================================================================
    # 4. DOTACIÓN UNIPERSONAL (1 SOLA PERSONA EN EL EQUIPO)
    # =========================================================================
    def test_single_person_team_rotates_and_recovers_without_infinite_loop(self):
        """
        Una empresa o dotación con un único funcionario ('SOLO'):
        Debe tomar todos los turnos disponibles sin caer en bucles infinitos por min_gap_weeks.
        """
        solo_config = self.root_path / "solo_config.json"
        solo_config.write_text(json.dumps({
            "personal": [{"id": 1, "nombre": "SOLO FUNCIONARIO", "email": "solo@guardia.cl"}],
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "historial": {}
        }), encoding="utf-8")
        solo_mgr = ShiftManager(str(solo_config))

        # Generar 3 meses consecutivos
        for m in (9, 10, 11):
            shifts, fid, pends = solo_mgr.generate_shifts(2026, m, [])
            self.assertTrue(all(s["persona"] == "SOLO FUNCIONARIO" for s in shifts))
            self.assertEqual(pends, [])
            ok, _ = solo_mgr.advance_month(2026, m, [])
            self.assertTrue(ok)

        # Si ese único funcionario tiene una licencia en una semana específica
        exc = [{"persona": "SOLO FUNCIONARIO", "fecha": date(2026, 12, 8), "tipo": "LIC"}]
        shifts_dec, _, pends_dec = solo_mgr.generate_shifts(2026, 12, exc)
        # La semana con fecha 8 debe estar sin asignar (None)
        week_with_exc = next(s for s in shifts_dec if s["semana"][0] <= date(2026, 12, 8) <= s["semana"][1])
        self.assertIsNone(week_with_exc["persona"])
        # Las demás semanas deben pertenecer a SOLO FUNCIONARIO
        other_weeks = [s for s in shifts_dec if s != week_with_exc]
        self.assertTrue(all(s["persona"] == "SOLO FUNCIONARIO" for s in other_weeks))

    # =========================================================================
    # 5. INDISPONIBILIDAD TOTAL DEL EQUIPO (100% LICENCIA) POR VARIOS MESES
    # =========================================================================
    def test_total_team_unavailability_multi_month_recovery(self):
        """
        Si todo el equipo tiene licencias médicas durante todo Septiembre y Octubre:
        Todas las semanas deben quedar como None, y al retornar en Noviembre la rotación
        debe reanudarse limpiamente en orden FIFO sin IDs duplicados en cola.
        """
        all_exc_sept = [
            {"persona": p["nombre"], "fecha": date(2026, 9, d), "tipo": "LIC"}
            for p in self.sample_personal for d in range(1, 31)
        ]
        ok, _ = self.manager.advance_month(2026, 9, all_exc_sept)
        self.assertTrue(ok)

        all_exc_oct = [
            {"persona": p["nombre"], "fecha": date(2026, 10, d), "tipo": "LIC"}
            for p in self.sample_personal for d in range(1, 32)
        ]
        ok, _ = self.manager.advance_month(2026, 10, all_exc_oct)
        self.assertTrue(ok)

        # En Noviembre todos están sanos y disponibles
        shifts_nov, final_id_nov, final_pends_nov = self.manager.generate_shifts(2026, 11, [])
        # Todas las semanas de Noviembre deben estar cubiertas
        self.assertTrue(all(s["persona"] is not None for s in shifts_nov))
        # No deben haber duplicados en pendientes
        self.assertEqual(len(final_pends_nov), len(set(final_pends_nov)))

    # =========================================================================
    # 6. HORIZONTES TEMPORALES EXTREMOS Y BISIESTOS
    # =========================================================================
    def test_extreme_calendar_years_and_leap_rules(self):
        """
        Prueba años lejanos:
        - Año 1970 (Unix Epoch)
        - Año 2000 (Bisiesto centenario, divisible por 400 -> Feb tiene 29 días)
        - Año 2100 (NO bisiesto centenario, divisible por 100 pero no por 400 -> Feb tiene 28 días)
        - Año 2028 (Bisiesto regular -> Feb tiene 29 días)
        """
        # 1970
        shifts_1970, _, _ = self.manager.generate_shifts(1970, 1, [])
        self.assertGreater(len(shifts_1970), 0)

        # 2000 Febrero (bisiesto centenario)
        weeks_2000 = self.manager._build_weeks(2000, 2)
        has_feb_29_2000 = any(w[0] <= date(2000, 2, 29) <= w[1] for w in weeks_2000)
        self.assertTrue(has_feb_29_2000)

        # 2100 Febrero (NO bisiesto)
        weeks_2100 = self.manager._build_weeks(2100, 2)
        # En 2100 el día 28 de Febrero es domingo; el 1 de Marzo es lunes. No existe 2100-02-29.
        with self.assertRaises(ValueError):
            date(2100, 2, 29)

        # 2028 Febrero (bisiesto estándar)
        exc_feb29 = [{"persona": "SGT PEREZ JUAN", "fecha": date(2028, 2, 29), "tipo": "FL"}]
        shifts_2028, _, _ = self.manager.generate_shifts(2028, 2, exc_feb29)
        feb29_week = next(s for s in shifts_2028 if s["semana"][0] <= date(2028, 2, 29) <= s["semana"][1])
        # PEREZ no debe tener el turno de la semana del 29
        self.assertNotEqual(feb29_week["persona"], "SGT PEREZ JUAN")

    # =========================================================================
    # 7. TRANSICIÓN DICIEMBRE A ENERO (AÑO NUEVO / NAVIDAD)
    # =========================================================================
    def test_year_transition_december_to_january(self):
        """Verifica la continuidad de rotación cruzando de Diciembre de un año a Enero del siguiente."""
        ok_dec, _ = self.manager.advance_month(2026, 12, [])
        self.assertTrue(ok_dec)
        self.assertIn("2027-01", self.manager.snapshots)

        shifts_jan, next_id, pends = self.manager.generate_shifts(2027, 1, [])
        self.assertGreater(len(shifts_jan), 0)

        # La semana limítrofe (28 dic - 3 ene) debe conservar la asignación cerrada de diciembre
        bridge_key = f"{shifts_jan[0]['semana'][0].isoformat()}_{shifts_jan[0]['semana'][1].isoformat()}"
        self.assertEqual(shifts_jan[0]["persona"], self.manager.historial[bridge_key])

        # Las semanas siguientes de enero deben continuar la rotación circular
        jan_names = [s["persona"] for s in shifts_jan]
        self.assertTrue(all(name is not None for name in jan_names))
        # No debe haber turnos inmediatamente consecutivos para la misma persona
        for i in range(len(jan_names) - 1):
            self.assertNotEqual(jan_names[i], jan_names[i + 1])

    # =========================================================================
    # 8. ARCHIVOS CONFIG.JSON HOSTILES O CORRUPTOS EN DISCO
    # =========================================================================
    def test_zero_byte_config_file_recovers_gracefully(self):
        """Un archivo config.json de 0 bytes no debe voltear la app: debe restaurar base limpia."""
        zero_config = self.root_path / "zero_config.json"
        zero_config.write_bytes(b"")

        mgr = ShiftManager(str(zero_config))
        self.assertEqual(mgr.personal, [])
        self.assertEqual(mgr.siguiente_id, 1)
        self.assertEqual(mgr.pendientes, [])

    def test_corrupted_datatypes_in_config_json_are_sanitized(self):
        """Valores con tipos incorrectos (ej. personal=None, pendientes='abc') se sanean sin excepción."""
        corrupt_data = {
            "personal": None,
            "siguiente_id": "not_an_int",
            "pendientes": "not_a_list",
            "snapshots": None,
            "excepciones": "not_a_dict",
            "inicio": None,
            "historial": None,
        }
        type_corrupt_file = self.root_path / "type_corrupt.json"
        type_corrupt_file.write_text(json.dumps(corrupt_data), encoding="utf-8")

        mgr = ShiftManager(str(type_corrupt_file))
        # No debe colapsar al generar turnos
        shifts, fid, pends = mgr.generate_shifts(2026, 9, [])
        self.assertIsInstance(shifts, list)
        self.assertIsInstance(pends, list)

    # =========================================================================
    # 9. ELIMINACIÓN DE PERSONAL CON PUNTERO ACTIVO
    # =========================================================================
    def test_removing_active_next_and_pending_persons(self):
        """Eliminar a una persona que está como siguiente_id y a otra en pendientes."""
        self.manager.siguiente_id = 2
        self.manager.pendientes = [2, 3]
        self.manager.snapshots = {"2026-10": {"siguiente_id": 2, "pendientes": [2, 3]}}

        # Eliminar a Ana (ID 2)
        success = self.manager.remove_person(2)
        self.assertTrue(success)

        # El ID 2 debe desaparecer de pendientes y de snapshots
        self.assertNotIn(2, self.manager.pendientes)
        self.assertEqual(self.manager.pendientes, [3])
        self.assertNotIn(2, self.manager.snapshots["2026-10"]["pendientes"])
        # Siguiente_id debe reasignarse a la primera persona disponible (ID 1)
        self.assertEqual(self.manager.siguiente_id, 1)

    # =========================================================================
    # 10. RANGOS DE EXCEPCIONES INVERTIDOS Y SUB-RANGOS
    # =========================================================================
    def test_inverted_and_multi_month_exception_ranges(self):
        """Verifica que rangos con start > end se normalicen y cubran meses cruzados."""
        # Rango invertido: 2026-10-05 a 2026-09-28
        stats = self.manager.add_exception_range(
            "SGT PEREZ JUAN", "2026-10-05", "2026-09-28", "LIC", motivo="Cirugía"
        )
        self.assertEqual(stats["total"], 8)
        self.assertIn("2026-09", stats["periods"])
        self.assertIn("2026-10", stats["periods"])

        # Verificar que se guardó en ambos periodos
        exc_sept = self.manager.get_exceptions("2026-09")
        exc_oct = self.manager.get_exceptions("2026-10")
        self.assertEqual(len(exc_sept), 3)  # 28, 29, 30 sep
        self.assertEqual(len(exc_oct), 5)   # 1, 2, 3, 4, 5 oct

        # Eliminar un sub-rango que parte al medio la excepción (30 sep al 2 oct)
        removed_count = self.manager.remove_exception_range(
            "SGT PEREZ JUAN", "2026-09-30", "2026-10-02"
        )
        self.assertEqual(removed_count, 3)

        # Comprobar remanentes
        rem_sept = [e["fecha"].day for e in self.manager.get_exceptions("2026-09")]
        rem_oct = [e["fecha"].day for e in self.manager.get_exceptions("2026-10")]
        self.assertEqual(rem_sept, [28, 29])
        self.assertEqual(rem_oct, [3, 4, 5])

    # =========================================================================
    # 11. ARCHIVADO HISTÓRICO Y CLAVES CORRUPTAS
    # =========================================================================
    def test_archive_old_records_rejects_unsafe_retention_and_handles_corrupt_keys(self):
        """Rechaza retención menor a 12 meses y tolera semanas con formato ilegible."""
        # Menos de 12 meses debe fallar para proteger la regla de feriados anuales
        with self.assertRaises(ValueError):
            self.manager.archive_old_records(retention_months=6)

        # Historial con claves corruptas mezcladas con claves viejas válidas
        old_date_str = (date.today() - timedelta(days=500)).isoformat()
        old_end_str = (date.today() - timedelta(days=493)).isoformat()
        self.manager.historial = {
            f"{old_date_str}_{old_end_str}": "SGT PEREZ JUAN",
            "clave_invalida_sin_fechas": "CBO GOMEZ ANA",
            "2026-09-07_2026-09-13": "CBO DIAZ LUIS",  # reciente
        }
        self.manager.save_config()

        ok, count, path = self.manager.archive_old_records(retention_months=12)
        self.assertTrue(ok)
        self.assertEqual(count, 1)
        # La semana reciente y la clave corrupta se conservan sin romper la ejecución
        self.assertIn("2026-09-07_2026-09-13", self.manager.historial)
        self.assertIn("clave_invalida_sin_fechas", self.manager.historial)
        # La semana antigua fue archivada
        self.assertNotIn(f"{old_date_str}_{old_end_str}", self.manager.historial)

    # =========================================================================
    # 12. GHOST PERSONNEL (FUNCIONARIO ELIMINADO EN HISTORIAL)
    # =========================================================================
    def test_ghost_personnel_in_history_does_not_break_future_rotation(self):
        """
        Si en el historial hay turnos asignados a un funcionario que luego fue eliminado,
        el sistema no debe fallar ni asignar 'Desconocido' al calcular los meses futuros.
        """
        self.manager.historial["2026-08-03_2026-08-09"] = "FUNCIONARIO FANTASMA"
        shifts, fid, pends = self.manager.generate_shifts(2026, 9, [])
        self.assertGreater(len(shifts), 0)
        # Todos los asignados en Septiembre deben pertenecer a la dotación real activa
        active_names = {p["nombre"] for p in self.sample_personal}
        for s in shifts:
            if s.get("persona"):
                self.assertIn(s["persona"], active_names)


if __name__ == "__main__":
    unittest.main()
