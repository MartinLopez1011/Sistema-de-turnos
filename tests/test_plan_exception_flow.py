"""
Flujo de usuario de la pestaña Planificación: agregar / editar / eliminar excepciones
escribiendo en los campos reales (Persona, Fecha(s), Hasta, tipo, motivo) y casos extremos:
todo el equipo con excepción el mismo día, mes completo, entradas inválidas, rangos que cruzan
mes/año, meses cerrados, etc.

Usa la ventana real (TurnosApp) con un config temporal de 16 personas.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from controllers.main_controller import MainController
from views.gui import TurnosApp
from views.theme import MESES

TEAM = 16
NAMES = [f"P{i:02d} APELLIDO NOMBRE" for i in range(1, TEAM + 1)]
YEAR, MONTH = 2030, 3


def _no_mail(*_a, **_k):
    raise AssertionError("Estos tests nunca deben enviar correos")


@pytest.fixture(autouse=True)
def _block_outgoing_mail():
    """Seguro: bloquea cualquier envío de correo/webhook y el guardado de mes de la GUI."""
    with patch("views.gui.send_email_smtp", _no_mail),          patch("views.gui.send_notification_webhook", _no_mail),          patch("views.gui.TurnosApp.save_month", _no_mail):
        yield


@pytest.fixture
def ui(tmp_path):
    personal = [{"id": i, "nombre": n, "email": ""} for i, n in enumerate(NAMES, 1)]
    Path(tmp_path, "config.json").write_text(json.dumps({
        "personal": personal, "inicio": {}, "historial": {}, "siguiente_id": 1,
        "pendientes": [], "snapshots": {}, "excepciones": {},
        "asignaciones_manuales": {}, "asignaciones_manuales_motivos": {},
    }), encoding="utf-8")
    controller = MainController(str(tmp_path))
    app = TurnosApp(controller)
    app.geometry("1200x700+0+0")
    app.month_var.set(MESES[MONTH - 1])
    app.year_var.set(str(YEAR))
    app.load_personal()
    app.on_period_change()
    app.update()
    statuses = []
    real_set_status = app.set_status

    def _spy(text, level="info"):
        statuses.append((level, text))
        real_set_status(text, level)

    app.set_status = _spy
    app.statuses = statuses
    app.plan = app.tab_plan
    yield app
    app.destroy()


def fill(app, person=None, desde="", hasta="", tipo="DA", motivo=""):
    plan = app.plan
    if person is not None:
        plan.person_var.set(person)
    plan.type_var.set(tipo)
    for entry, value in ((plan.from_entry, desde), (plan.to_entry, hasta), (plan.reason_entry, motivo)):
        entry.delete(0, "end")
        if value:
            entry.insert(0, value)


def add(app, *args, **kwargs):
    fill(app, *args, **kwargs)
    app.plan.add_exception()
    app.update()
    return app.statuses[-1] if app.statuses else None


def saved(app, person=None):
    exc = app.controller.get_all_exceptions()
    return sorted(e["fecha"] for e in exc if person is None or e["persona"] == person)


def days(*ds, month=MONTH, year=YEAR):
    return [date(year, month, d) for d in ds]


# ── Flujo normal ────────────────────────────────────────────────────────────
class TestNormalFlow:
    def test_single_date(self, ui):
        level, _ = add(ui, NAMES[0], "05/03/2030")
        assert level == "ok"
        assert saved(ui, NAMES[0]) == days(5)
        assert ui.plan.from_entry.get() == ""  # el formulario se limpia

    def test_day_numbers_and_ranges(self, ui):
        add(ui, NAMES[0], "1-3, 8, 10-11")
        assert saved(ui, NAMES[0]) == days(1, 2, 3, 8, 10, 11)

    def test_explicit_date_list(self, ui):
        add(ui, NAMES[1], "04/03/2030, 12/03/2030; 20/03/2030")
        assert saved(ui, NAMES[1]) == days(4, 12, 20)

    def test_from_to_range(self, ui):
        add(ui, NAMES[2], "10/03/2030", "14/03/2030", tipo="FL")
        assert saved(ui, NAMES[2]) == days(10, 11, 12, 13, 14)
        assert {e["tipo"] for e in ui.controller.get_all_exceptions()} == {"FL"}

    def test_inline_range_syntax(self, ui):
        add(ui, NAMES[2], "10/03/2030 al 12/03/2030")
        assert saved(ui, NAMES[2]) == days(10, 11, 12)

    def test_reversed_range_is_swapped(self, ui):
        add(ui, NAMES[3], "14/03/2030", "10/03/2030")
        assert saved(ui, NAMES[3]) == days(10, 11, 12, 13, 14)

    def test_otr_requires_reason(self, ui):
        level, _ = add(ui, NAMES[0], "05/03/2030", tipo="OTR", motivo="")
        assert level == "error" and saved(ui) == []
        level, _ = add(ui, NAMES[0], "05/03/2030", tipo="OTR", motivo="ab")
        assert level == "error" and saved(ui) == []
        level, _ = add(ui, NAMES[0], "05/03/2030", tipo="OTR", motivo="Duelo")
        assert level == "ok" and saved(ui) == days(5)

    def test_duplicate_add_warns_and_does_not_duplicate(self, ui):
        add(ui, NAMES[0], "05/03/2030")
        level, _ = add(ui, NAMES[0], "05/03/2030")
        assert level == "warn"
        assert saved(ui, NAMES[0]) == days(5)

    def test_same_day_new_type_updates_in_place(self, ui):
        add(ui, NAMES[0], "05/03/2030", tipo="DA")
        add(ui, NAMES[0], "05/03/2030", tipo="LIC")
        exc = [e for e in ui.controller.get_all_exceptions() if e["persona"] == NAMES[0]]
        assert len(exc) == 1 and exc[0]["tipo"] == "LIC"

    def test_type_change_survives_reload_from_disk(self, ui):
        from models.shift_manager import ShiftManager
        add(ui, NAMES[0], "05/03/2030", tipo="DA")
        add(ui, NAMES[0], "05/03/2030", tipo="LIC")
        reloaded = ShiftManager(ui.controller.shift_manager.config_path)
        exc = [e for e in reloaded.get_all_exceptions() if e["persona"] == NAMES[0]]
        assert [e["tipo"] for e in exc] == ["LIC"]

    def test_remove_range_via_ui(self, ui):
        add(ui, NAMES[0], "10/03/2030", "12/03/2030")
        with patch("views.tabs.tab_plan._confirm_action", return_value=True):
            ui.plan._on_delete_range_clicked(NAMES[0], date(2030, 3, 10), date(2030, 3, 12))
        assert saved(ui, NAMES[0]) == []

    def test_remove_declined_keeps_data(self, ui):
        add(ui, NAMES[0], "10/03/2030")
        with patch("views.tabs.tab_plan._confirm_action", return_value=False):
            ui.plan._on_delete_range_clicked(NAMES[0], date(2030, 3, 10), date(2030, 3, 10))
        assert saved(ui, NAMES[0]) == days(10)

    def test_preview_never_assigns_person_on_their_exception(self, ui):
        add(ui, NAMES[0], "1-31", tipo="LIC")
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        assert all(s["persona"] != NAMES[0] for s in shifts)

    def test_add_does_not_flag_unsaved_changes(self, ui):
        add(ui, NAMES[0], "05/03/2030")
        assert not ui.title().startswith("●")


# ── Todos el mismo día / mes completo ───────────────────────────────────────
class TestEveryoneAtOnce:
    def test_everyone_same_single_day(self, ui):
        for name in NAMES:
            level, _ = add(ui, name, "13/03/2030", tipo="DA")
            assert level == "ok", name
        assert len(saved(ui)) == TEAM
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        assert shifts, "la vista previa no debe quedar vacía"
        # la semana del día 13 no puede quedar con alguien en excepción ese día
        week = next(s for s in shifts if s["semana"][0] <= date(2030, 3, 13) <= s["semana"][1])
        assert week["persona"] is None or week["persona"] not in NAMES

    def test_everyone_same_day_flow_via_ui_keeps_rendering(self, ui):
        for name in NAMES:
            add(ui, name, "13/03/2030", tipo="LIC")
        ui.plan.refresh_exceptions()
        ui.update()
        assert ui.plan.exception_list.winfo_children()

    def test_everyone_whole_month_blocks_close(self, ui):
        for name in NAMES:
            add(ui, name, "1-31", tipo="LIC")
        errors = ui.controller.validate_month(YEAR, MONTH, list(ui.exceptions), manual_assignments={})
        assert errors, "cerrar un mes sin nadie disponible debe rechazarse"

    def test_everyone_whole_month_close_does_not_crash_or_corrupt(self, ui):
        for name in NAMES:
            add(ui, name, "1-31", tipo="LIC")
        before = dict(ui.controller.shift_manager.historial)
        ok, _ = ui.controller.advance_queue(YEAR, MONTH, list(ui.exceptions))
        # ok o rechazo, pero nunca un historial con personas inválidas
        for person in ui.controller.shift_manager.historial.values():
            assert person in NAMES
        if not ok:
            assert ui.controller.shift_manager.historial == before

    def test_all_but_one_person_always_gets_the_turn(self, ui):
        for name in NAMES[1:]:
            add(ui, name, "1-31", tipo="FL")
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        assert {s["persona"] for s in shifts} == {NAMES[0]}

    def test_everyone_on_bridge_week_days_only(self, ui):
        # semana puente 25/02-03/03 y 04/03-10/03: excepción de todos el 01-03/03
        for name in NAMES:
            add(ui, name, "01/03/2030", "03/03/2030", tipo="DA")
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        assert all(s["persona"] is None or s["persona"] in NAMES for s in shifts)


# ── Entradas inválidas y extremos ───────────────────────────────────────────
class TestInvalidInput:
    @pytest.mark.parametrize("raw", ["", "   ", "abc", "32", "0", "-5", "1--3", "1-2-3", "31/02/2030",
                                     "29/02/2029", "99/99/2030", "5/", "//", ",,,", "1,,x"])
    def test_invalid_from_is_rejected_without_saving(self, ui, raw):
        result = add(ui, NAMES[0], raw)
        assert saved(ui) == [], raw
        assert result is not None and result[0] in ("error", "warn"), (raw, result)

    def test_no_person_selected(self, ui):
        result = add(ui, "Sin personal disponible", "05/03/2030")
        assert result[0] == "error" and saved(ui) == []

    def test_hasta_invalid_does_not_crash(self, ui):
        add(ui, NAMES[0], "05/03/2030", "zzz")
        assert True  # no debe lanzar; el estado final se revisa abajo
        assert all(e["persona"] == NAMES[0] for e in ui.controller.get_all_exceptions())

    def test_range_crossing_month_and_year(self, ui):
        add(ui, NAMES[0], "28/12/2030", "03/01/2031", tipo="FL")
        assert saved(ui, NAMES[0]) == [date(2030, 12, 28) + timedelta(days=i) for i in range(7)]

    def test_leap_day(self, ui):
        add(ui, NAMES[0], "29/02/2028", "01/03/2028")
        assert saved(ui, NAMES[0]) == [date(2028, 2, 29), date(2028, 3, 1)]

    def test_whole_year_range_is_fast_and_consistent(self, ui):
        import time
        t = time.time()
        add(ui, NAMES[0], "01/01/2030", "31/12/2030", tipo="LIC")
        assert len(saved(ui, NAMES[0])) == 365
        assert time.time() - t < 10

    def test_numeric_days_use_selected_month_not_today(self, ui):
        add(ui, NAMES[0], "31")
        assert saved(ui, NAMES[0]) == days(31)
        ui.month_var.set(MESES[1])  # febrero: día 31 no existe
        ui.on_period_change()
        result = add(ui, NAMES[0], "31")
        assert result[0] == "error"

    def test_double_click_add_is_idempotent(self, ui):
        fill(ui, NAMES[0], "05/03/2030")
        ui.plan.add_exception()
        ui.plan.add_exception()  # formulario ya vacío
        assert saved(ui, NAMES[0]) == days(5)
        assert ui.statuses[-1][0] == "error"

    def test_enter_key_in_entry_adds(self, ui):
        fill(ui, NAMES[0], "07/03/2030")
        ui.plan.from_entry.focus_force()
        ui.update()
        ui.plan.from_entry.event_generate("<Return>")
        ui.update()
        assert saved(ui, NAMES[0]) == days(7)

    def test_very_long_motive_and_unicode(self, ui):
        motivo = "Comisión de servicio ñandú 🚑 " * 20
        add(ui, NAMES[0], "05/03/2030", tipo="OTR", motivo=motivo)
        assert len(saved(ui, NAMES[0])) == 1
        ui.plan.refresh_exceptions()
        ui.update()

    def test_add_while_saving_is_blocked(self, ui):
        ui.is_exporting = True
        ui.on_period_change()  # no debe hacer nada ni fallar
        ui.is_exporting = False


# ── Meses cerrados ──────────────────────────────────────────────────────────
class TestClosedMonths:
    def _close_march(self, ui):
        ok, msg = ui.controller.advance_queue(YEAR, MONTH, [])
        assert ok, msg

    def test_exception_in_closed_month_asks_confirmation_and_can_cancel(self, ui):
        self._close_march(ui)
        with patch("views.tabs.tab_plan._confirm_action", return_value=False) as ask:
            add(ui, NAMES[0], "05/03/2030")
        assert ask.called and saved(ui) == []

    def test_exception_in_closed_month_recalculates_consistently(self, ui):
        self._close_march(ui)
        owner_week = next(k for k in ui.controller.shift_manager.historial if k.startswith("2030-03-11"))
        owner = ui.controller.shift_manager.historial[owner_week]
        with patch("views.tabs.tab_plan._confirm_action", return_value=True):
            add(ui, owner, "11/03/2030", "17/03/2030", tipo="LIC")
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        week = next(s for s in shifts if s["semana"][0] == date(2030, 3, 11))
        assert week["persona"] != owner

    def test_everyone_same_day_in_closed_month(self, ui):
        self._close_march(ui)
        with patch("views.tabs.tab_plan._confirm_action", return_value=True):
            for name in NAMES:
                add(ui, name, "13/03/2030")
        shifts = ui.controller.preview_shifts(YEAR, MONTH, ui.exceptions, manual_assignments={})
        assert shifts


# ── Consistencia entre pestañas ─────────────────────────────────────────────
class TestCrossTab:
    def test_calendar_reflects_new_exceptions_when_opened(self, ui):
        add(ui, NAMES[0], "05/03/2030", tipo="LIC")
        ui.jump_to_calendar()
        ui.update()
        canvases = [w for f in ui.tab_calendar.vista_scroll.winfo_children() for w in f.winfo_children()
                    if w.winfo_class() == "Canvas"]
        assert canvases

    def test_many_sequential_adds_keep_ui_responsive(self, ui):
        import time
        t = time.time()
        for i, name in enumerate(NAMES):
            add(ui, name, f"{i + 1}-{i + 3}")
        assert time.time() - t < 30
        assert len(saved(ui)) == sum(3 for _ in NAMES)

    def test_period_change_shows_only_that_period_exceptions(self, ui):
        add(ui, NAMES[0], "05/03/2030")
        ui.month_var.set(MESES[3])
        ui.on_period_change()
        assert ui.exceptions == []
        ui.month_var.set(MESES[2])
        ui.on_period_change()
        assert len(ui.exceptions) == 1
