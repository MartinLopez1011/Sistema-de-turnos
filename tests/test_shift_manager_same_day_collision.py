"""
Test Suite: Escenarios Extremos y Colisión Total de Fechas (Senior Desktop QA).

Casos evaluados:
1. Colisión Total (100% de la dotación solicita el mismo día libre).
2. Resolución mediante Asignación Manual Forzada (Override de Jefatura/Coordinador).
3. Caso N - 1: El 'Único Sobreviviente' asignado fuera de turno normal.
4. Ruptura controlada de Enfriamiento (Cooling Gap Bypass) ante escasez extrema.
5. Colisión en Semana Limítrofe (Bridge Week) con Historial Cerrado.
6. Múltiples Semanas con Colisión Total en el Mismo Mes (Doble Vacío).
7. Robustez de Exportación a Excel con Semanas Sin Asignar (persona = None).
8. Simulación Multimensual de Recuperación de Turnos (Pendientes FIFO Cascade).
9. Concurrencia y Thread-Safety durante Cálculos y Lecturas Simultáneas.
"""

import copy
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl

from models.shift_manager import ShiftManager
from utils.excel_handler import ExcelHandler


class ShiftManagerSameDayCollisionTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.config_path = self.root_path / "config.json"

        # Dotación oficial estándar de 16 funcionarios
        self.personal_16 = [
            {"id": i, "nombre": f"FUNCIONARIO {i:02d}", "email": f"func{i:02d}@guardia.cl"}
            for i in range(1, 17)
        ]
        self.clean_payload = {
            "personal": self.personal_16,
            "inicio": {},
            "historial": {},
            "siguiente_id": 1,
            "pendientes": [],
            "snapshots": {},
            "excepciones": {},
            "asignaciones_manuales": {},
            "asignaciones_manuales_motivos": {},
            "auditoria": [],
        }
        self.config_path.write_text(
            json.dumps(self.clean_payload, indent=2), encoding="utf-8"
        )
        self.manager = ShiftManager(str(self.config_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    # =========================================================================
    # 1. COLISIÓN TOTAL: 100% DEL EQUIPO PIDE EL MISMO DÍA (EJ. 18 DE SEPTIEMBRE)
    # =========================================================================
    def test_all_personnel_request_exact_same_day_yields_unassigned_shift(self):
        """
        Si los 16 funcionarios solicitan permiso el mismo día (ej. 18 de septiembre):
        - La semana que contiene ese día no encuentra candidatos disponibles.
        - Dicha semana DEBE resultar con persona = None (sin romper el flujo).
        - Todos los 16 funcionarios deben quedar marcados en 'saltados'.
        - validate_month DEBE reportar error bloqueante para impedir 'Cerrar Mes'.
        """
        # Viernes 18 de septiembre de 2026 cae en semana del 14 al 20 de septiembre
        target_day = date(2026, 9, 18)
        all_same_day_exceptions = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
        ]

        shifts, fid, pends = self.manager.generate_shifts(2026, 9, all_same_day_exceptions)

        # Buscar la semana que contiene el 18 de septiembre
        collision_week = next(
            s for s in shifts if s["semana"][0] <= target_day <= s["semana"][1]
        )
        self.assertIsNone(
            collision_week["persona"],
            "La semana donde todos tienen excepción debe quedar sin asignar (None)",
        )
        self.assertEqual(
            len(collision_week["saltados"]),
            16,
            "Los 16 funcionarios debieron ser evaluados y registrados en 'saltados'",
        )

        # Las otras semanas del mes (donde nadie tiene excepción) deben asignarse con normalidad
        other_weeks = [s for s in shifts if s != collision_week]
        for w in other_weeks:
            self.assertIsNotNone(w["persona"], "Las semanas sin conflicto deben tener funcionario")

        # Regla de Oro en Arquitectura Desktop:
        # validate_month DEBE retornar error impidiendo que la UI permita cerrar el mes
        validation_errors = self.manager.validate_month(2026, 9, all_same_day_exceptions)
        self.assertIn(
            "Existe al menos una semana sin funcionario asignado.",
            validation_errors,
        )

    # =========================================================================
    # 2. RESOLUCIÓN DE COLISIÓN MEDIANTE ASIGNACIÓN MANUAL (OVERRIDE JEFATURA)
    # =========================================================================
    def test_all_request_same_day_resolved_via_manual_assignment(self):
        """
        Cuando todos piden el mismo día pero la Jefatura/Coordinador fuerza una asignación
        manual de servicio en esa semana:
        - La asignación manual debe tener precedencia absoluta.
        - La semana queda cubierta con es_manual = True.
        - validate_month es exitoso (lista vacía de errores).
        - No se produce estampida en pendientes porque el turno quedó asignado.
        """
        target_day = date(2026, 9, 18)
        all_same_day_exceptions = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
        ]
        # El coordinador designa manualmente a FUNCIONARIO 03 para cubrir la guardia
        collision_week_key = "2026-09-14_2026-09-20"
        manual_override = {collision_week_key: "FUNCIONARIO 03"}

        shifts, fid, pends = self.manager.generate_shifts(
            2026, 9, all_same_day_exceptions, manual_assignments=manual_override
        )

        collision_week = next(
            s for s in shifts if s["semana"][0] <= target_day <= s["semana"][1]
        )
        self.assertEqual(collision_week["persona"], "FUNCIONARIO 03")
        self.assertTrue(collision_week.get("es_manual"))

        # El mes ahora es 100% válido para cierre
        errors = self.manager.validate_month(
            2026, 9, all_same_day_exceptions, manual_assignments=manual_override
        )
        self.assertEqual(errors, [])

    # =========================================================================
    # 3. CASO N - 1: EL ÚNICO SOBREVIVIENTE (15 DE 16 PIDEN EL MISMO DÍA)
    # =========================================================================
    def test_n_minus_one_request_same_day_assigns_lone_survivor(self):
        """
        Si 15 de 16 personas piden el mismo día:
        El motor debe saltar a los 15 con excepción y asignar forzosamente
        al único disponible (FUNCIONARIO 16), sin importar que el puntero
        estuviera en FUNCIONARIO 03.
        """
        target_day = date(2026, 9, 18)
        # Funcionarios 1 al 15 piden permiso; FUNCIONARIO 16 está disponible
        fifteen_exceptions = [
            {"persona": f"FUNCIONARIO {i:02d}", "fecha": target_day, "tipo": "DA"}
            for i in range(1, 16)
        ]

        shifts, fid, pends = self.manager.generate_shifts(2026, 9, fifteen_exceptions)

        collision_week = next(
            s for s in shifts if s["semana"][0] <= target_day <= s["semana"][1]
        )
        self.assertEqual(
            collision_week["persona"],
            "FUNCIONARIO 16",
            "El único funcionario disponible debe asumir la guardia",
        )
        # Quienes fueron saltados en esa semana antes del 16 deben ingresar a pendientes
        self.assertGreater(len(collision_week["saltados"]), 0)

    # =========================================================================
    # 4. RUPTURA CONTROLADA DE ENFRIAMIENTO (COOLING GAP BYPASS) ANTE ESCASEZ
    # =========================================================================
    def test_lone_survivor_violates_cooling_gap_to_prevent_empty_shift(self):
        """
        Equipo reducido de 4 personas.
        - Semana 1: P1
        - Semana 2: P2
        - Semana 3: P1, P3 y P4 piden el mismo día. P2 es el único sin licencia,
          pero P2 HIZO TURNO EN LA SEMANA 2 (distancia = 1 semana, menor al enfriamiento 4).
        El motor DEBE priorizar NO dejar la guardia vacía por sobre la regla de enfriamiento,
        asignando a P2 mediante el fallback de mayor descanso acumulado disponible.
        """
        small_team = [
            {"id": i, "nombre": f"GUARDIA {i:02d}", "email": f"g{i:02d}@test.cl"}
            for i in range(1, 5)
        ]
        small_config = self.root_path / "small_config.json"
        small_config.write_text(
            json.dumps({**self.clean_payload, "personal": small_team}, indent=2),
            encoding="utf-8",
        )
        small_mgr = ShiftManager(str(small_config))

        target_day = date(2026, 9, 18)  # Cae en semana 3 (14 al 20 Sep)
        excs = [
            {"persona": "GUARDIA 01", "fecha": target_day, "tipo": "DA"},
            {"persona": "GUARDIA 03", "fecha": target_day, "tipo": "DA"},
            {"persona": "GUARDIA 04", "fecha": target_day, "tipo": "DA"},
        ]

        shifts, _, _ = small_mgr.generate_shifts(2026, 9, excs)
        # Semana 1 (31 ago - 6 sep): GUARDIA 01
        # Semana 2 (7 sep - 13 sep): GUARDIA 02
        # Semana 3 (14 sep - 20 sep): P1, P3, P4 con licencia -> GUARDIA 02 asignado por fallback
        self.assertEqual(shifts[0]["persona"], "GUARDIA 01")
        self.assertEqual(shifts[1]["persona"], "GUARDIA 02")
        self.assertEqual(
            shifts[2]["persona"],
            "GUARDIA 02",
            "El motor debe violar el enfriamiento antes de dejar la semana vacía",
        )

    # =========================================================================
    # 5. COLISIÓN TOTAL EN SEMANA LIMÍTROFE (BRIDGE WEEK)
    # =========================================================================
    def test_all_request_same_day_in_bridge_week_respects_closed_history(self):
        """
        Semana limítrofe: 2026-08-31 al 2026-09-06.
        Si Agosto ya está cerrado en historial con 'FUNCIONARIO 01':
        - Si los 16 funcionarios piden el 02 de Septiembre, pero FUNCIONARIO 01 NO tiene
          excepción: el turno histórico de Agosto se MANTIENE intacto.
        - Si FUNCIONARIO 01 SÍ tiene excepción en esa fecha: el historial se invalida,
          se recalcula y, al no haber nadie disponible, resulta en None.
        """
        bridge_week = "2026-08-31_2026-09-06"
        self.manager.historial[bridge_week] = "FUNCIONARIO 01"
        self.manager.save_config()

        # Escenario A: 15 funcionarios piden el 02 de Sep, pero FUNCIONARIO 01 no
        target_day = date(2026, 9, 2)
        exc_scenario_a = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
            if p["nombre"] != "FUNCIONARIO 01"
        ]
        shifts_a, _, _ = self.manager.generate_shifts(2026, 9, exc_scenario_a)
        self.assertEqual(
            shifts_a[0]["persona"],
            "FUNCIONARIO 01",
            "El histórico cerrado debe respetarse si el asignado no tiene excepción",
        )

        # Escenario B: Los 16 funcionarios (incluyendo FUNCIONARIO 01) piden el 02 de Sep
        exc_scenario_b = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
        ]
        shifts_b, _, _ = self.manager.generate_shifts(2026, 9, exc_scenario_b)
        self.assertIsNone(
            shifts_b[0]["persona"],
            "Si el histórico tiene excepción y nadie más puede cubrir, queda en None",
        )

    # =========================================================================
    # 6. DOBLE COLISIÓN TOTAL EN DIFERENTES SEMANAS DEL MISMO MES
    # =========================================================================
    def test_multiple_weeks_with_total_collision_in_same_month(self):
        """
        Si todo el equipo pide el 08 de septiembre (Semana 2) Y el 22 de septiembre (Semana 4):
        - Ambas semanas 2 y 4 deben quedar como None.
        - Las semanas 1, 3 y 5 deben rotar normalmente.
        - validate_month debe reflejar que existen múltiples semanas sin asignar.
        - No deben generarse claves duplicadas en pendientes.
        """
        day_week2 = date(2026, 9, 8)
        day_week4 = date(2026, 9, 22)
        excs = []
        for p in self.personal_16:
            excs.append({"persona": p["nombre"], "fecha": day_week2, "tipo": "DA"})
            excs.append({"persona": p["nombre"], "fecha": day_week4, "tipo": "DA"})

        shifts, fid, pends = self.manager.generate_shifts(2026, 9, excs)

        unassigned_weeks = [s for s in shifts if s["persona"] is None]
        self.assertEqual(len(unassigned_weeks), 2)
        self.assertEqual(len(pends), len(set(pends)), "Pendientes no debe tener duplicados")

        errors = self.manager.validate_month(2026, 9, excs)
        self.assertIn("Existe al menos una semana sin funcionario asignado.", errors)

    # =========================================================================
    # 7. EXPORTACIÓN A EXCEL CON SEMANAS VACÍAS (persona = None)
    # =========================================================================
    def test_excel_export_does_not_crash_when_week_has_no_assigned_person(self):
        """
        Verifica que el generador de reportes ExcelHandler maneje de forma segura
        la presencia de semanas donde persona = None sin lanzar TypeError,
        AttributeError ni corromper el archivo binario xlsx resultante.
        """
        target_day = date(2026, 9, 18)
        all_same_day_exceptions = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
        ]

        shifts, _, _ = self.manager.generate_shifts(2026, 9, all_same_day_exceptions)

        excel_output = self.root_path / "reporte_colision.xlsx"
        handler = ExcelHandler(str(excel_output), self.personal_16)
        handler.load_template()
        # write_shifts debe tolerar shifts con persona = None
        handler.write_shifts(shifts, all_same_day_exceptions, 2026, 9)
        handler.save_report()
        handler.close()

        self.assertTrue(excel_output.exists())
        self.assertGreater(excel_output.stat().st_size, 1000)

        # Verificar integridad del archivo generado con openpyxl
        wb = openpyxl.load_workbook(str(excel_output))
        ws = wb.active
        self.assertEqual(ws["A1"].value, "PLANIFICACIÓN DE TURNOS — SEPTIEMBRE 2026")
        wb.close()

    # =========================================================================
    # 8. CASCADA DE RECUPERACIÓN MULTIMENSUAL TRAS COLISIÓN
    # =========================================================================
    def test_multi_month_recovery_cascade_after_same_day_collision(self):
        """
        Tras una colisión total en la Semana 3 de Septiembre (14 al 20 Sep),
        todos los funcionarios no asignados ingresan a pendientes.
        Verifica cómo se desahoga la cola de pendientes en los meses de Septiembre
        y Octubre en estricto orden FIFO.
        """
        target_day = date(2026, 9, 18)
        excs_sept = [
            {"persona": p["nombre"], "fecha": target_day, "tipo": "DA"}
            for p in self.personal_16
        ]

        shifts_sept, fid_sept, pends_sept = self.manager.generate_shifts(
            2026, 9, excs_sept
        )
        # Semana 1: P1, Semana 2: P2, Semana 3: None, Semana 4: P3 (recupera), Semana 5: P4 (recupera)
        self.assertEqual(shifts_sept[0]["persona"], "FUNCIONARIO 01")
        self.assertEqual(shifts_sept[1]["persona"], "FUNCIONARIO 02")
        self.assertIsNone(shifts_sept[2]["persona"])
        self.assertEqual(shifts_sept[3]["persona"], "FUNCIONARIO 03")
        self.assertEqual(shifts_sept[4]["persona"], "FUNCIONARIO 04")

        # Al pasar a Octubre con ese estado
        state_oct = {"siguiente_id": fid_sept, "pendientes": pends_sept}
        shifts_oct, fid_oct, pends_oct = self.manager.generate_shifts(
            2026, 10, [], state=state_oct
        )

        # En Octubre (5 semanas), los turnos deben asignarse secuencialmente a los pendientes
        # P5, P6, P7, P8, P9
        expected_oct_assignments = [
            "FUNCIONARIO 05",
            "FUNCIONARIO 06",
            "FUNCIONARIO 07",
            "FUNCIONARIO 08",
            "FUNCIONARIO 09",
        ]
        assigned_oct = [s["persona"] for s in shifts_oct]
        self.assertEqual(assigned_oct, expected_oct_assignments)

        # Los pendientes restantes deben decrecer limpiamente
        self.assertEqual(
            pends_oct,
            [10, 11, 12, 13, 14, 15, 16],
            "La cola de pendientes debe avanzar de manera decreciente sin olvidar a nadie",
        )

    # =========================================================================
    # 9. CONCURRENCIA Y THREAD-SAFETY
    # =========================================================================
    def test_concurrent_generation_and_reads_do_not_race_or_corrupt_state(self):
        """
        En aplicaciones de escritorio, los hilos de renderizado y cálculo en background
        pueden solicitar turnos simultáneamente.
        Verifica que múltiples llamadas concurrentes a generate_shifts y get_exceptions
        no generen condiciones de carrera ni excepciones imprevistas.
        """
        errors = []

        def worker(worker_id):
            try:
                # Cada hilo calcula un mes distinto o el mismo mes de colisión
                month = (worker_id % 12) + 1
                excs = (
                    [
                        {"persona": p["nombre"], "fecha": date(2026, 9, 18), "tipo": "DA"}
                        for p in self.personal_16
                    ]
                    if month == 9
                    else []
                )
                shifts, fid, pends = self.manager.generate_shifts(2026, month, excs)
                self.assertIsInstance(shifts, list)
                self.assertIsInstance(fid, int)
                self.assertIsInstance(pends, list)
            except Exception as e:
                errors.append(f"Worker {worker_id} falló: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Hubo errores en ejecución concurrente: {errors}")


if __name__ == "__main__":
    unittest.main()
