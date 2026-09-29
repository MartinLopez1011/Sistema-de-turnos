"""
Pruebas de invariantes y casos extremos adicionales para ShiftManager.

Complementa test_shift_manager_extreme_cases.py con:
1. Fuzz determinista (semillas fijas) que valida invariantes tras cerrar meses en cadena.
2. Equipos muy pequeños (2 y 3 personas) donde la ventana de descanso es inalcanzable.
3. Semanas puente (lunes-domingo que cruzan de mes) con excepciones ingresadas DESPUÉS del cierre.
4. Operaciones sobre personal (remove_person / set_notification_settings) y sus rollbacks.
5. Idempotencia del cierre, ausencia de mutación en vistas previas y rendimiento de previews lejanos.

Los defectos confirmados en la revisión están marcados con @unittest.expectedFailure y describen
el comportamiento CORRECTO esperado; al corregir el código, quitar el decorador.
"""

import json
import random
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from models.shift_manager import ShiftManager


def _build_manager(root, size):
    personal = [{"id": i, "nombre": f"P{i:02d} TEST", "email": ""} for i in range(1, size + 1)]
    path = Path(root) / "config.json"
    path.write_text(json.dumps({
        "personal": personal, "inicio": {}, "historial": {}, "siguiente_id": 1,
        "pendientes": [], "snapshots": {}, "excepciones": {},
        "asignaciones_manuales": {}, "asignaciones_manuales_motivos": {},
    }), encoding="utf-8")
    return ShiftManager(str(path))


def _next_month(year, month):
    return (year + 1, 1) if month == 12 else (year, month + 1)


class _TempManagerCase(unittest.TestCase):
    team_size = 8

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.manager = _build_manager(self.tmp.name, self.team_size)


class RandomizedInvariantTests(unittest.TestCase):
    """Cierra 5 meses consecutivos con licencias aleatorias y valida invariantes globales."""

    SEEDS = (0, 1, 2, 3, 4, 5)
    MONTHS = 5

    def _run_seed(self, seed):
        rnd = random.Random(seed)
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp, 16)
            ids = {p["id"] for p in manager.personal}
            year, month = 2030, 1
            for _ in range(self.MONTHS):
                exceptions = []
                for _ in range(rnd.randint(0, 3)):
                    who = rnd.choice(manager.personal)["nombre"]
                    start = date(year, month, rnd.randint(1, 28))
                    exceptions += [
                        {"persona": who, "fecha": start + timedelta(days=k), "tipo": "LIC"}
                        for k in range(rnd.randint(1, 20))
                    ]
                before = json.dumps(manager.historial, sort_keys=True)
                state = manager.get_initial_state_for_period(year, month)
                shifts, next_id, pending = manager.generate_shifts(year, month, exceptions, state=state)

                # La vista previa no puede mutar el estado persistente.
                self.assertEqual(before, json.dumps(manager.historial, sort_keys=True))
                # Puntero y pendientes válidos y sin duplicados.
                self.assertIn(next_id, ids)
                self.assertTrue(set(pending) <= ids)
                self.assertEqual(len(pending), len(set(pending)))
                for shift in shifts:
                    start_w, end_w = shift["semana"]
                    self.assertIsNotNone(shift["persona"], f"semana sin asignar {start_w} (seed {seed})")
                    for exc in exceptions:
                        if exc["persona"] == shift["persona"]:
                            self.assertFalse(start_w <= exc["fecha"] <= end_w,
                                             f"{shift['persona']} asignado en su licencia (seed {seed})")
                ok, msg = manager.advance_month(year, month, exceptions)
                self.assertTrue(ok, msg)
                year, month = _next_month(year, month)

            # Con 16 personas nadie repite en menos de 3 semanas de descanso.
            last = {}
            for key in sorted(manager.historial):
                start_w = date.fromisoformat(key.split("_")[0])
                person = manager.historial[key]
                if person in last:
                    self.assertGreaterEqual((start_w - last[person]).days, 21,
                                            f"{person} repite muy pronto (seed {seed})")
                last[person] = start_w

    def test_invariants_hold_across_seeds(self):
        for seed in self.SEEDS:
            with self.subTest(seed=seed):
                self._run_seed(seed)


class SmallTeamTests(unittest.TestCase):
    def test_team_smaller_than_gap_still_assigns_every_week(self):
        for size in (2, 3):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as tmp:
                manager = _build_manager(tmp, size)
                state = manager.get_initial_state_for_period(2030, 3)
                shifts, next_id, pending = manager.generate_shifts(2030, 3, [], state=state)
                self.assertTrue(all(s["persona"] for s in shifts))
                self.assertIn(next_id, {p["id"] for p in manager.personal})
                self.assertEqual(len(pending), len(set(pending)))

    def test_team_of_three_shares_load_evenly_over_a_year(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = _build_manager(tmp, 3)
            year, month = 2030, 1
            for _ in range(12):
                ok, msg = manager.advance_month(year, month, [])
                self.assertTrue(ok, msg)
                year, month = _next_month(year, month)
            counts = {}
            for person in manager.historial.values():
                counts[person] = counts.get(person, 0) + 1
            self.assertLessEqual(max(counts.values()) - min(counts.values()), 2, counts)


class BridgeWeekTests(_TempManagerCase):
    """Semana lunes-domingo que cruza de mes (28-ene a 03-feb de 2030)."""

    BRIDGE = "2030-01-28_2030-02-03"

    def _close_january_then_add_february_license(self):
        self.manager.advance_month(2030, 1, [])
        owner = self.manager.historial[self.BRIDGE]
        exceptions = [{"persona": owner, "fecha": date(2030, 2, 3), "tipo": "LIC"}]
        return owner, exceptions

    @unittest.expectedFailure
    def test_february_view_matches_persisted_bridge_week(self):
        """BUG: la vista de febrero muestra a otra persona en una semana que el historial mantiene."""
        owner, exceptions = self._close_january_then_add_february_license()
        state = self.manager.get_initial_state_for_period(2030, 2)
        shifts, _, _ = self.manager.generate_shifts(2030, 2, exceptions, state=state)
        view = {f"{s['semana'][0]}_{s['semana'][1]}": s["persona"] for s in shifts}
        self.manager.advance_month(2030, 2, exceptions)
        self.assertEqual(view[self.BRIDGE], self.manager.historial[self.BRIDGE])

    @unittest.expectedFailure
    def test_no_back_to_back_double_shift_after_bridge_exception(self):
        """BUG: quien conserva la semana puente además recibe un turno de recuperación la semana siguiente."""
        owner, exceptions = self._close_january_then_add_february_license()
        self.manager.advance_month(2030, 2, exceptions)
        second = self.manager.historial["2030-02-04_2030-02-10"]
        self.assertNotEqual(owner, second)

    @unittest.expectedFailure
    def test_every_member_gets_exactly_one_turn_in_first_cycle(self):
        """BUG: el puntero consume a P04 en el cálculo pero su turno nunca se persiste."""
        owner, exceptions = self._close_january_then_add_february_license()
        self.manager.advance_month(2030, 2, exceptions)
        first_cycle = [self.manager.historial[k] for k in sorted(self.manager.historial)
                       if "2030-01-07" <= k <= "2030-02-25"]
        self.assertEqual(len(set(first_cycle)), len(first_cycle), first_cycle)


class PersonnelOperationTests(_TempManagerCase):
    @unittest.expectedFailure
    def test_removing_next_person_advances_pointer_to_their_successor(self):
        """BUG: al borrar a quien tocaba, el puntero vuelve a la primera persona (repite la cola)."""
        self.manager.siguiente_id = 5
        self.manager.save_config()
        self.assertTrue(self.manager.remove_person(5))
        self.assertEqual(self.manager.siguiente_id, 6)

    @unittest.expectedFailure
    def test_set_notification_settings_rolls_back_on_save_failure(self):
        """BUG: previous se captura después de sobrescribir, así que el rollback no restaura nada."""
        self.manager.notificaciones = {"webhook_url": "OLD", "activo": True}
        self.manager.save_config = lambda: False
        self.assertFalse(self.manager.set_notification_settings("NEW", False))
        self.assertEqual(self.manager.notificaciones, {"webhook_url": "OLD", "activo": True})

    def test_removing_last_person_keeps_manager_usable(self):
        for person in list(self.manager.personal):
            self.assertTrue(self.manager.remove_person(person["id"]))
        shifts, _, pending = self.manager.generate_shifts(2030, 3, [])
        self.assertTrue(all(s["persona"] is None for s in shifts))
        self.assertEqual(pending, [])


class ClosureBehaviourTests(_TempManagerCase):
    def test_closing_same_month_twice_is_idempotent(self):
        self.manager.advance_month(2030, 1, [])
        first = (dict(self.manager.historial), self.manager.siguiente_id, list(self.manager.pendientes))
        self.manager.advance_month(2030, 1, [])
        second = (dict(self.manager.historial), self.manager.siguiente_id, list(self.manager.pendientes))
        self.assertEqual(first, second)

    def test_recalculating_closed_month_does_not_move_global_pointer_backwards(self):
        self.manager.advance_month(2030, 1, [])
        self.manager.advance_month(2030, 2, [])
        pointer = self.manager.siguiente_id
        owner = self.manager.historial["2030-01-14_2030-01-20"]
        license_ = [{"persona": owner, "fecha": date(2030, 1, 16), "tipo": "LIC"}]
        self.manager.advance_month(2030, 1, license_)
        self.assertEqual(self.manager.siguiente_id, pointer)
        self.assertNotEqual(self.manager.historial["2030-01-14_2030-01-20"], owner)

    def test_preview_twice_is_deterministic(self):
        state = self.manager.get_initial_state_for_period(2031, 6)
        first = self.manager.generate_shifts(2031, 6, [], state=dict(state))
        second = self.manager.generate_shifts(2031, 6, [], state=dict(state))
        self.assertEqual(first, second)

    def test_far_future_preview_is_fast(self):
        started = time.time()
        self.manager.get_initial_state_for_period(2060, 1)
        self.assertLess(time.time() - started, 5)


if __name__ == "__main__":
    unittest.main()
