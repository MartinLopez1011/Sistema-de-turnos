---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
<!-- refreshed: 2026-10-06 -->

# Architecture

**Analysis Date:** 2026-10-06

## System Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                     │
├──────────────────┬──────────────────┬───────────────────────┤
│   Tab Plan       │   Tab Calendar   │    Tab Settings       │
│  `views/tabs/`   │  `views/tabs/`   │   `views/tabs/`       │
└────────┬─────────┴────────┬─────────┴──────────┬────────────┘
         │                  │                     │
         ▼                  ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 Controller / Coordination                   │
│         `controllers/main_controller.py`                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
┌────────────────────────────────┐ ┌──────────────────────────┐
│          Domain Model          │ │     Report & Notifier    │
│  `models/shift_manager.py`     │ │ `utils/excel_handler.py` │
│  `models/rotation_engine.py`   │ │ `utils/email_notifier.py`│
│  `models/config_repository.py` │ └──────────────────────────┘
└────────────────┬───────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│  State Store & Backups                                      │
│  `config.json` / `backups/`                                 │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `main.py` | Application entry point, Windows DPI awareness setup, global crash handlers | `main.py` |
| `TurnosApp` | Main CustomTkinter window, tab coordinator, theme management, modal binding | `views/gui.py` |
| `TabPlan` | Shift preview table, exceptions manager, manual overrides, export & closure actions | `views/tabs/tab_plan.py` |
| `TabCalendar` | Interactive monthly calendar view with color coding and hover info | `views/tabs/tab_calendar.py` |
| `TabSettings` | Personnel CRUD, initial assignment, email list, SMTP config, audit log viewer | `views/tabs/tab_settings.py` |
| `MainController` | Orchestration between GUI views and domain model; inputs validation; pure mediator | `controllers/main_controller.py` |
| `ShiftManager` | Core business logic, rotation queue, exception skips/recovery, snapshots, audit | `models/shift_manager.py` |
| `RotationEngine` | Domain abstraction interface for shift generation algorithm | `models/rotation_engine.py` |
| `ConfigRepository` | Atomic JSON file persistence with fsync, validation, and corrupt file recovery | `models/config_repository.py` |
| `ExcelHandler` | Memory construction and cell styling for monthly Excel report spreadsheets | `utils/excel_handler.py` |
| `EmailNotifier` | SMTP transmission and Google Apps Script webhook integration | `utils/email_notifier.py` |
| `ChileanHolidays` | Calculation and normalization of Chilean national public holidays | `utils/chilean_holidays.py` |
| `AppPaths` | Portable vs APPDATA directory resolution for desktop runtime | `utils/app_paths.py` |
| `Logger` | Centralized rotating logging configuration (`turnos.log`) | `utils/logger.py` |

## Pattern Overview

**Overall:** Model-View-Controller (MVC) with Desktop Document Storage.

**Key Characteristics:**
- **Separation of Concerns:** `views/` contains only Tkinter/CustomTkinter widgets; `controllers/` mediates user events and validates input; `models/` contains zero GUI code and is fully testable headlessly.
- **Pure Shift Calculation:** Shift generation receives snapshot state and returns updated state + assignments without mutating persistent storage until explicitly committed.
- **Fail-Safe File Persistence:** JSON updates write to temporary files first, sync to disk via `os.fsync`, and atomically swap with `os.replace` to prevent corrupted states on sudden shutdown.

## Layers

**Presentation Layer (`views/`):**
- Purpose: Render dark-mode graphical user interface and receive user interactions
- Location: `views/gui.py`, `views/theme.py`, `views/tabs/`, `views/components/`
- Contains: CustomTkinter frames, buttons, tables, dialogs, calendar widgets
- Depends on: `controllers/main_controller.py`, `views/theme.py`, `views/components/`
- Used by: `main.py`

**Controller Layer (`controllers/`):**
- Purpose: Mediate between GUI tabs and backend models, coordinating multi-step flows
- Location: `controllers/main_controller.py`
- Contains: `MainController` class, parameter sanitization, delegation
- Depends on: `models/shift_manager.py`, `utils/excel_handler.py`, `utils/email_notifier.py`
- Used by: `views/gui.py`, `views/tabs/tab_*.py`

**Domain & Model Layer (`models/`):**
- Purpose: Core rotation algorithm, state invariants, snapshots, exceptions, backups
- Location: `models/shift_manager.py`, `models/rotation_engine.py`, `models/domain_types.py`, `models/config_repository.py`
- Contains: Shift rotation rules, skip queues, recovery tracking, persistence repository
- Depends on: `utils/chilean_holidays.py`, `utils/config_validator.py`, `utils/logger.py`
- Used by: `controllers/main_controller.py`

**Utility & Integration Layer (`utils/`):**
- Purpose: Excel document generation, email/webhook communication, system paths, logging
- Location: `utils/excel_handler.py`, `utils/email_notifier.py`, `utils/app_paths.py`, `utils/logger.py`, `utils/env_helper.py`
- Contains: `openpyxl` styling logic, SMTP/TLS sockets, network check helpers
- Depends on: Python standard library, `openpyxl`, `holidays`
- Used by: `controllers/main_controller.py`, `models/shift_manager.py`, `views/tabs/tab_*.py`

## Data Flow

### Primary Request Path (Monthly Generation & Closure)

1. User selects month/year in `TabPlan` (`views/tabs/tab_plan.py:210`)
2. `TabPlan` invokes `MainController.preview_shifts(year, month)` (`controllers/main_controller.py:155`)
3. `MainController` calls `ShiftManager.generate_shifts(year, month, exceptions)` (`models/shift_manager.py:450`)
4. `ShiftManager` runs rotation engine, resolves exceptions/recovering skips, returns schedule preview
5. User clicks "Exportar Excel" → `MainController.generate_excel(year, month)` writes spreadsheet via `ExcelHandler` (`utils/excel_handler.py:80`)
6. User clicks "Cerrar Mes" → `MainController.advance_queue(year, month)` records into `historial`, captures snapshot for subsequent month, creates backup, and saves `config.json` via `ConfigRepository` (`models/config_repository.py:33`)

### Secondary Flow Name (Manual Assignment & Override)

1. User selects a week in `TabPlan` and chooses "Asignación Manual" (`views/tabs/tab_plan.py:530`)
2. Dialog prompts for target person and mandatory justification motive (`views/components/dialogs.py:280`)
3. `MainController.set_manual_assignment(period, week, person, motive)` validates and updates `ShiftManager.asignaciones_manuales`
4. Shift preview table re-renders highlighting manual override with distinct badge (`views/theme.py:46`)

**State Management:**
- Single source of truth in `config.json`.
- State loaded into memory at startup as dictionary attributes on `ShiftManager`.
- Re-entrant thread lock (`threading.RLock`) in `ShiftManager` protects concurrent operations.

## Key Abstractions

**`ShiftManager`:**
- Purpose: Manages state transitions, circular staff queue, exceptions, and audit logs
- Examples: `models/shift_manager.py`
- Pattern: Domain Manager / Facade

**`ConfigRepository`:**
- Purpose: Atomic filesystem persistence and backup handler
- Examples: `models/config_repository.py`
- Pattern: Repository Pattern

**`ExcelHandler`:**
- Purpose: Fluent Excel spreadsheet generation with conditional color fills and headers
- Examples: `utils/excel_handler.py`
- Pattern: Builder / Report Generator

## Entry Points

**Desktop Application:**
- Location: `main.py`
- Triggers: User launches executable or runs `python main.py`
- Responsibilities: High-DPI initialization, uncaught exception traps, controller/window launch

## Architectural Constraints

- **Threading:** Single main UI thread (Tkinter mainloop); network requests (SMTP, webhook) run asynchronously or in background threads where specified to avoid freezing the GUI.
- **Global state:** File-level state loaded via `ConfigRepository`; `_env_loaded` and `_logger_initialized` singletons in utility modules.
- **Circular imports:** Controlled by having `controllers/` import `models/` and `utils/`, but `models/` never importing `controllers/` or `views/`.
- **Platform Execution:** Primary runtime is Windows 64-bit; handles paths and DPI awareness specific to Windows APIs.

## Anti-Patterns

### Modifying State During Preview

**What happens:** Direct mutation of `self.siguiente_id` or `self.pendientes` during temporary preview calculations.
**Why it's wrong:** Causes drift in queue order when users view months without closing them.
**Do this instead:** Pass immutable state copy to `_generate_shifts_legacy(state=...)` and only commit in `advance_month`.

### Hardcoded Hex Colors in UI Widgets

**What happens:** Using raw color codes like `"#111418"` directly in view files.
**Why it's wrong:** Breaks design system consistency and central theme changes.
**Do this instead:** Always reference tokens from `views/theme.py` (`P["bg_app"]`).

## Error Handling

**Strategy:** Layered defensive error trapping with user-facing alerts and detailed logging.

**Patterns:**
- Global `sys.excepthook` and `report_callback_exception` in `main.py` capture unexpected UI errors.
- Method operations return `(success: bool, message: str)` tuples in `controllers/main_controller.py`.
- Atomic `.tmp` file writing with automatic recovery and corruption backups in `models/config_repository.py`.

## Cross-Cutting Concerns

**Logging:** Centralized rotating logger in `utils/logger.py` (`turnos.log`, 2 MB max, 3 backups).
**Validation:** Strict schema and data validation on load/save in `utils/config_validator.py`.
**Authentication:** Environment-variable-based SMTP and webhook credentials via `utils/env_helper.py`.

---

*Architecture analysis: 2026-10-06*
