---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# Testing Patterns

**Analysis Date:** 2026-10-06

## Test Framework

**Runner:**
- pytest 9.1.1 (executed via `.venv/Scripts/python.exe -m pytest`)
- Config: `conftest.py` adds project root to `sys.path`

**Assertion Library:**
- pytest standard `assert` statements alongside `unittest.TestCase` assertions

**Run Commands:**

```bash
.venv\Scripts\python.exe -m pytest -q                                           # Run full suite (~250 tests)
.venv\Scripts\python.exe -m pytest tests/test_shift_manager_rotation.py -x     # Stop on first failure
.venv\Scripts\python.exe -m pytest tests/test_shift_manager.py -k "test_name"  # Filter by test name
```

## Test File Organization

**Location:**
- Centralized in `tests/` directory at repository root

**Naming:**
- Prefixed with `test_`: `test_shift_manager.py`, `test_excel_handler.py`, `test_manual_assignments.py`

**Structure:**

```
tests/
├── test_app_paths.py
├── test_controller_export_parity.py
├── test_cross_month_continuity.py
├── test_cross_month_exceptions.py
├── test_custom_dialogs.py
├── test_email_notification_feature.py
├── test_email_notifier.py
├── test_env_helper.py
├── test_excel_handler.py
├── test_excel_historical_and_styling.py
├── test_future_preview.py
├── test_improvements.py
├── test_loading_modal.py
├── test_logger.py
├── test_manual_assignments.py
├── test_manual_assignments_edge_cases.py
├── test_manual_assignments_excel.py
├── test_monday_to_monday_shifts.py
├── test_otr_motive.py
├── test_phase2_boundaries.py
├── test_plan_exception_flow.py
├── test_qa_flows_and_edge_cases.py
├── test_reliability_features.py
├── test_reset_historial.py
├── test_settings_smtp_lock.py
├── test_shift_manager.py
├── test_shift_manager_backup_and_reset.py
├── test_shift_manager_crud.py
├── test_shift_manager_extreme_cases.py
├── test_shift_manager_hardening.py
├── test_shift_manager_invariants.py
├── test_shift_manager_resilience.py
├── test_shift_manager_rotation.py
├── test_shift_manager_same_day_collision.py
├── test_tab_plan_ranges.py
└── test_ui_window_geometry.py
```

## Test Structure

**Suite Organization:**

```python
import pytest
from datetime import date
from models.shift_manager import ShiftManager

@pytest.fixture
def manager(tmp_path):
    config_file = tmp_path / "config.json"
    # setup minimal config json
    return ShiftManager(str(config_file))

def test_excepcion_y_recuperacion(manager):
    excepciones = [{"persona": "SGT (F) PEREZ JUAN", "fecha": date(2024, 1, 3), "tipo": "FL"}]
    shifts, final_id, pendientes = manager.generate_shifts(2024, 1, excepciones)
    assert shifts[0]['persona'] == "CBO (M) GOMEZ ANA"
    assert any(s['persona'] == "SGT (F) PEREZ JUAN" for s in shifts[0]['saltados'])
```

**Patterns:**
- Setup: Pytest `tmp_path` fixture or `tempfile.TemporaryDirectory` creating isolated temporary `config.json`
- Teardown: Cleaned up automatically by fixtures/context managers
- Assertion: State invariant checks (`len(shifts) == 5`, `final_id == expected`)

## Mocking

**Framework:**
- `unittest.mock` (Python standard library) and `pytest-mock`

**Patterns:**

```python
from unittest.mock import patch, MagicMock

@patch("utils.email_notifier.smtplib.SMTP")
def test_send_email_smtp(mock_smtp):
    mock_instance = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_instance
    # execute test
```

**What to Mock:**
- Network socket calls (`socket.create_connection`, `smtplib.SMTP`, `urllib.request`)
- Tkinter GUI dialogs during headless tests (`messagebox.askyesno`, `messagebox.showerror`)

**What NOT to Mock:**
- Shift calculation logic and rotation engine
- JSON serializing / parsing logic (tested against real temporary files)

## Fixtures and Factories

**Test Data:**

```python
initial_data = {
    "inicio": {},
    "historial": {},
    "personal": [
        {"id": 1, "nombre": "SGT (F) PEREZ JUAN"},
        {"id": 2, "nombre": "CBO (M) GOMEZ ANA"}
    ],
    "siguiente_id": 1,
    "pendientes": [],
    "snapshots": {},
    "excepciones": {}
}
```

**Location:**
- Defined locally in test files as pytest fixtures (`base_config`, `manager`)

## Coverage

**Requirements:** None enforced by CI gate

**View Coverage:**

```bash
.venv\Scripts\python.exe -m pytest --cov=.
```

## Test Types

**Unit Tests:**
- Core rotation engine, exception skips, queue recovery, date parsing (`tests/test_shift_manager_rotation.py`)

**Integration Tests:**
- End-to-end month closing, Excel report building, and controller coordination (`tests/test_controller_export_parity.py`, `tests/test_excel_handler.py`)

**E2E Tests:**
- Headless GUI simulation tests verifying window geometry and dialog interactions (`tests/test_ui_window_geometry.py`, `tests/test_plan_exception_flow.py`)

## Common Patterns

**Async Testing:**
- UI timer jobs and background threads tested via `app.update()` or mock calls

**Error Testing:**

```python
with pytest.raises(ValueError):
    manager.add_person("")
```

---

*Testing analysis: 2026-10-06*
