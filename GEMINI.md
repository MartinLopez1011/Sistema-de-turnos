<!-- GSD:project-start source:PROJECT.md -->

## Project

**Sistema de Turnos**

Aplicación de escritorio en Python (CustomTkinter) para la gestión, planificación semanal rotativa, administración de excepciones y emisión de reportes oficiales de turnos para equipos operativos y funcionarios. Genera reportes mensuales en Excel y notificaciones automáticas vía SMTP y webhook.

**Core Value:** Planificación confiable y automatizada de turnos semanales con asignación rotativa justa, gestión precisa de excepciones y generación de reportes sin errores de estado.

### Constraints

- **Compatibilidad**: No romper las pruebas automatizadas existentes ni la integridad de los datos en `config.json`.
- **Experiencia de usuario**: Mantener la estética visual y diseño en modo oscuro sin desalinear elementos de la interfaz.
- **Concordancia de idioma**: Cuidar género y número gramatical al reemplazar términos en español.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.14 (3.14.7 active in `.venv`) - Core application logic, GUI, controllers, models, utilities, and test suites
- JavaScript (ES6+) - Google Apps Script webhook integration (`scripts/google_apps_script.js`)

## Runtime

- CPython 3.14.7 (Windows x86-64)
- Standalone portable desktop executable compiled via PyInstaller (`dist/Sistema de Turnos.exe`)
- pip (Standard Python package installer)
- Lockfile: missing (relies on unpinned/minimum versions in `requirements.txt` and `requirements-dev.txt`)

## Frameworks

- CustomTkinter 5.x (`customtkinter`) - Modern dark-mode GUI desktop framework built on Tkinter
- openpyxl 3.x (`openpyxl`) - Excel workbook generation, cell styling, and print formatting
- Pillow 10.x/11.x (`Pillow`) - UI icon loading, image scaling, and avatar graphics
- pytest 9.1.1 (`pytest`) - Test runner and assertion framework
- pytest-mock 3.x (`pytest-mock`) - Fixture-based test mocking integration
- PyInstaller 6.x (`pyinstaller`) - Standalone single-executable bundler (`Sistema de Turnos.spec`)

## Key Dependencies

- `customtkinter` (>=5.2.0) - Core desktop UI widgets and windowing (`views/gui.py`, `views/tabs/tab_plan.py`)
- `openpyxl` (>=3.1.0) - Monthly shift spreadsheet generation and color styling (`utils/excel_handler.py`)
- `holidays` (>=0.104,<1) - Chilean national holiday calculation (`utils/chilean_holidays.py`)
- `Pillow` (>=10.0.0) - Graphical image handling for avatars and status icons (`views/components/widgets.py`)
- `python-docx` (>=1.1.0) - Word document interaction and specifications documentation
- `smtplib` / `email` (Python standard library) - Direct SMTP email transmission with file attachments (`utils/email_notifier.py`)
- `urllib.request` / `socket` (Python standard library) - Network connectivity checks and webhook HTTP requests (`utils/email_notifier.py`)

## Configuration

- Loaded via `utils/env_helper.py` (`load_env_file`) from `.env` in application data directory
- Variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_NAME`, `VPN_PROVEEDOR`, `VPN_FORMULARIO_URL`, `VPN_CORREO_SOPORTE`
- `Sistema de Turnos.spec` - PyInstaller build specification (single-file mode, windowed/noconsole, bundles `assets/` and `holidays.countries.chile`)

## Platform Requirements

- Windows 10/11 with Python 3.14 (virtual environment `.venv`)
- Command: `pip install -r requirements-dev.txt`
- Windows 10/11 64-bit desktop environment
- Standalone `.exe` (`dist/Sistema de Turnos.exe`), zero Python installation required, runs in user space without administrator privileges

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Snake_case for modules and test scripts (`main_controller.py`, `test_shift_manager_rotation.py`)
- Snake_case with descriptive action verbs: `generate_shifts()`, `preview_shifts()`, `load_config()`, `_parse_week_range()`
- Private/internal helpers prefixed with single underscore: `_build_ui()`, `_default_payload()`, `_init_defaults()`, `_confirm_action()`
- Snake_case for local variables and attributes: `start_date`, `shift_manager`, `person_dropdown`
- UPPER_SNAKE_CASE for global constants: `FONT_FAMILY`, `MESES`, `EXC_COLORS`, `APP_NAME`, `CONFIG_SCHEMA_VERSION`
- PascalCase for classes and custom dialogs: `ShiftManager`, `MainController`, `TurnosApp`, `ExcelHandler`, `CustomConfirmDialog`

## Code Style

- Standard PEP 8 4-space indentation
- Maximum line length ~100-120 characters
- No automated external linter enforced in CI (Flake8/Black/Ruff not present in dev requirements)
- Runtime schema and invariant validation enforced via `utils/config_validator.py`

## Import Organization

- None configured; `conftest.py` ensures project root is on `sys.path` for uniform root-relative imports

## Error Handling

- Controllers return `(success: bool, message: str)` tuples for user-facing actions
- Domain models raise descriptive exceptions or log warnings and fall back to safe defaults
- File I/O operations wrap writes in atomic `.tmp` files with `os.fsync()` and `os.replace()`
- Top-level Tkinter and system crashes intercepted with `messagebox.showerror` and logged to `turnos.log`

## Logging

- Always obtain module-scoped logger via `logger = get_logger("module_name")`
- Use formatted arguments instead of f-strings: `logger.info("Backup creado: %s", path)`
- Pass `exc_info=True` on unexpected exceptions

## Comments

- Docstrings on public methods explaining arguments, return structures, and constraints
- Inline comments explaining complex domain rules (e.g., cooling period between shifts, December holiday restrictions, Monday-to-Monday week shifts)
- Not applicable (Python project uses standard Python docstrings)

## Function Design

- Modular UI builders (`_build_ui()`, `_build_tab_plan()`) partitioned into focused helper methods
- Pure functions preferred for date calculations and schedule previews
- Explicit typing hints used in newer modules (`models/domain_types.py`, `models/config_repository.py`)
- Default parameter values for optional flags (`recalculate_history=False`, `motivo=""`)
- Controllers return `(bool, Any)` tuples
- Generators and parsers return explicit lists or dictionaries

## Module Design

- Explicit imports used across modules; `__all__` not commonly specified
- Package directories include `__init__.py` where applicable
- `views/components/__init__.py` and `views/tabs/__init__.py` expose component classes

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

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

- **Separation of Concerns:** `views/` contains only Tkinter/CustomTkinter widgets; `controllers/` mediates user events and validates input; `models/` contains zero GUI code and is fully testable headlessly.
- **Pure Shift Calculation:** Shift generation receives snapshot state and returns updated state + assignments without mutating persistent storage until explicitly committed.
- **Fail-Safe File Persistence:** JSON updates write to temporary files first, sync to disk via `os.fsync`, and atomically swap with `os.replace` to prevent corrupted states on sudden shutdown.

## Layers

- Purpose: Render dark-mode graphical user interface and receive user interactions
- Location: `views/gui.py`, `views/theme.py`, `views/tabs/`, `views/components/`
- Contains: CustomTkinter frames, buttons, tables, dialogs, calendar widgets
- Depends on: `controllers/main_controller.py`, `views/theme.py`, `views/components/`
- Used by: `main.py`
- Purpose: Mediate between GUI tabs and backend models, coordinating multi-step flows
- Location: `controllers/main_controller.py`
- Contains: `MainController` class, parameter sanitization, delegation
- Depends on: `models/shift_manager.py`, `utils/excel_handler.py`, `utils/email_notifier.py`
- Used by: `views/gui.py`, `views/tabs/tab_*.py`
- Purpose: Core rotation algorithm, state invariants, snapshots, exceptions, backups
- Location: `models/shift_manager.py`, `models/rotation_engine.py`, `models/domain_types.py`, `models/config_repository.py`
- Contains: Shift rotation rules, skip queues, recovery tracking, persistence repository
- Depends on: `utils/chilean_holidays.py`, `utils/config_validator.py`, `utils/logger.py`
- Used by: `controllers/main_controller.py`
- Purpose: Excel document generation, email/webhook communication, system paths, logging
- Location: `utils/excel_handler.py`, `utils/email_notifier.py`, `utils/app_paths.py`, `utils/logger.py`, `utils/env_helper.py`
- Contains: `openpyxl` styling logic, SMTP/TLS sockets, network check helpers
- Depends on: Python standard library, `openpyxl`, `holidays`
- Used by: `controllers/main_controller.py`, `models/shift_manager.py`, `views/tabs/tab_*.py`

## Data Flow

### Primary Request Path (Monthly Generation & Closure)

### Secondary Flow Name (Manual Assignment & Override)

- Single source of truth in `config.json`.
- State loaded into memory at startup as dictionary attributes on `ShiftManager`.
- Re-entrant thread lock (`threading.RLock`) in `ShiftManager` protects concurrent operations.

## Key Abstractions

- Purpose: Manages state transitions, circular staff queue, exceptions, and audit logs
- Examples: `models/shift_manager.py`
- Pattern: Domain Manager / Facade
- Purpose: Atomic filesystem persistence and backup handler
- Examples: `models/config_repository.py`
- Pattern: Repository Pattern
- Purpose: Fluent Excel spreadsheet generation with conditional color fills and headers
- Examples: `utils/excel_handler.py`
- Pattern: Builder / Report Generator

## Entry Points

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

### Hardcoded Hex Colors in UI Widgets

## Error Handling

- Global `sys.excepthook` and `report_callback_exception` in `main.py` capture unexpected UI errors.
- Method operations return `(success: bool, message: str)` tuples in `controllers/main_controller.py`.
- Atomic `.tmp` file writing with automatic recovery and corruption backups in `models/config_repository.py`.

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.agents/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
