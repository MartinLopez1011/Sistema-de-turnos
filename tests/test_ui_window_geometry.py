import os
import json
import pytest
from unittest.mock import MagicMock, patch
from views.gui import TurnosApp
from main import setup_windows_dpi
from views.theme import FONT_FAMILY


def test_font_family_configured():
    assert FONT_FAMILY == "Segoe UI"


def test_setup_windows_dpi_executes_safely():
    # Debería ejecutarse sin lanzar excepciones en cualquier plataforma
    setup_windows_dpi()


def test_ui_state_persistence(tmp_path):
    mock_controller = MagicMock()
    mock_controller.root_path = str(tmp_path)
    mock_controller.get_saved_exceptions.return_value = {}
    mock_controller.get_saved_manual_assignments.return_value = {}
    mock_controller.get_exceptions_for_period.return_value = []
    mock_controller.get_all_manual_motives.return_value = {}
    mock_controller.get_personal_list.return_value = ["PEREZ JUAN"]
    mock_controller.preview_shifts.return_value = []
    mock_controller.get_starting_person.return_value = "PEREZ JUAN"
    mock_controller.get_all_persons.return_value = []
    mock_controller.shift_manager.historial = {}
    mock_controller.shift_manager.last_warnings = []
    mock_controller.shift_manager.group_exceptions_into_ranges.return_value = []
    mock_controller.get_exceptions_grouped.return_value = []

    with patch("customtkinter.CTk.mainloop"):
        app = TurnosApp(mock_controller)
        try:
            # Simular guardado de estado
            app.tabview.set("  📅  Ver Turnos del Mes  ")
            app._save_ui_state()

            ui_state_file = os.path.join(str(tmp_path), "ui_state.json")
            assert os.path.exists(ui_state_file)

            with open(ui_state_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "is_maximized" in data
            assert data.get("last_tab") == "  📅  Ver Turnos del Mes  "

            # Carga del estado
            loaded = app._load_ui_state()
            assert loaded.get("last_tab") == "  📅  Ver Turnos del Mes  "
        finally:
            app.destroy()


def test_window_geometry_bounds_protection(tmp_path):
    mock_controller = MagicMock()
    mock_controller.root_path = str(tmp_path)
    mock_controller.get_saved_exceptions.return_value = {}
    mock_controller.get_saved_manual_assignments.return_value = {}
    mock_controller.get_exceptions_for_period.return_value = []
    mock_controller.get_all_manual_motives.return_value = []
    mock_controller.get_personal_list.return_value = []
    mock_controller.preview_shifts.return_value = []
    mock_controller.get_starting_person.return_value = ""
    mock_controller.get_all_persons.return_value = []
    mock_controller.shift_manager.historial = {}
    mock_controller.shift_manager.last_warnings = []
    mock_controller.shift_manager.group_exceptions_into_ranges.return_value = []
    mock_controller.get_exceptions_grouped.return_value = []

    # Guardar un estado con coordenadas fuera de pantalla (ej: monitor desconectado x=4000)
    ui_state_file = os.path.join(str(tmp_path), "ui_state.json")
    with open(ui_state_file, "w", encoding="utf-8") as f:
        json.dump({
            "is_maximized": False,
            "width": 1400,
            "height": 800,
            "x": 4000,
            "y": 3000
        }, f)

    with patch("customtkinter.CTk.mainloop"):
        app = TurnosApp(mock_controller)
        try:
            # Al detectar x=4000 fuera de los límites de un monitor normal, debe usar el default centrado
            # winfo_x() no debe ser 4000
            assert app.winfo_x() < 3500
        finally:
            app.destroy()


def test_desktop_keyboard_shortcuts_and_tab_switching(tmp_path):
    mock_controller = MagicMock()
    mock_controller.root_path = str(tmp_path)
    mock_controller.get_saved_exceptions.return_value = {}
    mock_controller.get_saved_manual_assignments.return_value = {}
    mock_controller.get_exceptions_for_period.return_value = []
    mock_controller.get_all_manual_motives.return_value = {}
    mock_controller.get_personal_list.return_value = []
    mock_controller.preview_shifts.return_value = []
    mock_controller.get_starting_person.return_value = ""
    mock_controller.get_all_persons.return_value = []
    mock_controller.shift_manager.historial = {}
    mock_controller.shift_manager.last_warnings = []
    mock_controller.shift_manager.group_exceptions_into_ranges.return_value = []
    mock_controller.get_exceptions_grouped.return_value = []

    with patch("customtkinter.CTk.mainloop"):
        app = TurnosApp(mock_controller)
        try:
            # Probar cambio rápido con Ctrl+1, 2, 3
            app._switch_tab_index(1)
            assert app.tabview.get() == "  📅  Ver Turnos del Mes  "

            app._switch_tab_index(2)
            assert app.tabview.get() == "  ⚙  Ajustes  "

            app._switch_tab_index(0)
            assert app.tabview.get() == "  📋  Planificación  "

            # Probar ciclo de pestañas adelante y atrás (_cycle_tab)
            app._cycle_tab(1)
            assert app.tabview.get() == "  📅  Ver Turnos del Mes  "
            app._cycle_tab(1)
            assert app.tabview.get() == "  ⚙  Ajustes  "
            app._cycle_tab(1)
            assert app.tabview.get() == "  📋  Planificación  "
            app._cycle_tab(-1)
            assert app.tabview.get() == "  ⚙  Ajustes  "

            # Probar navegación horizontal de mes (_nav_month)
            app.tabview.set("  📋  Planificación  ")
            m_before = app.month_var.get()
            app._nav_month(1)
            assert app.month_var.get() != m_before
            app._nav_month(-1)
            assert app.month_var.get() == m_before

            # Probar refresco contextual con F5 sin errores
            app._refresh_current_view()
            app._switch_tab_index(1)
            app._refresh_current_view()
            app._switch_tab_index(2)
            app._refresh_current_view()
        finally:
            app.destroy()


def test_calendar_tab_rendering_and_status_caching(tmp_path):
    mock_controller = MagicMock()
    mock_controller.root_path = str(tmp_path)
    mock_controller.get_saved_exceptions.return_value = {}
    mock_controller.get_saved_manual_assignments.return_value = {}
    mock_controller.get_exceptions_for_period.return_value = []
    mock_controller.get_all_manual_motives.return_value = {}
    mock_controller.get_personal_list.return_value = ["PEREZ JUAN"]
    mock_controller.preview_shifts.return_value = []
    mock_controller.get_starting_person.return_value = "PEREZ JUAN"
    mock_controller.get_all_persons.return_value = [{"id": 1, "nombre": "PEREZ JUAN"}]
    mock_controller.shift_manager.historial = {}
    mock_controller.shift_manager.last_warnings = []
    mock_controller.shift_manager.group_exceptions_into_ranges.return_value = []
    mock_controller.get_exceptions_grouped.return_value = []

    with patch("customtkinter.CTk.mainloop"):
        app = TurnosApp(mock_controller)
        try:
            # Probar render de turnos
            app.tab_calendar.render_turnos_view()

            # Probar caché de set_status
            app.set_status("Prueba 1", "info")
            assert app._last_status_text == "Prueba 1"

            # Llamar con el mismo texto no debe provocar reconfiguración de labels
            with patch.object(app.tab_calendar.cal_status_lbl, "configure") as mock_cfg:
                app.set_status("Prueba 1", "info")
                mock_cfg.assert_not_called()

            # Probar debounce de leave/enter
            app.tab_calendar._on_cell_enter("Turno test")
            assert app._last_status_text == "Turno test"
            app.tab_calendar._on_cell_leave()
            assert app.tab_calendar._status_leave_job is not None
        finally:
            app.destroy()


