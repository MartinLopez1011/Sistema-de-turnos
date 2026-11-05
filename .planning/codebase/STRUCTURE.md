---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# Codebase Structure

**Analysis Date:** 2026-10-06

## Directory Layout

```
Sistema de turnos/
├── assets/                    # Static image assets and status icons
├── backups/                   # Automatic timestamped backups of config.json
├── controllers/               # Application controller layer (MVC)
│   └── main_controller.py    # Main mediator between GUI views and domain models
├── dist/                      # PyInstaller build artifacts and standalone .exe
├── models/                    # Domain logic, rotation rules, and data repository
│   ├── config_repository.py  # Atomic JSON persistence and validation
│   ├── domain_types.py       # Domain data classes (ExceptionRecord, ShiftAssignment)
│   ├── rotation_engine.py    # Shift rotation engine boundary
│   └── shift_manager.py      # Core rotation engine and state manager
├── scripts/                   # Integration scripts (Google Apps Script)
│   └── google_apps_script.js # Serverless Google Workspace email webhook
├── tests/                     # Automated pytest and unittest test suites
├── utils/                     # Utility helpers (Excel, email, logger, paths, holidays)
│   ├── app_paths.py          # Application data and portable paths resolver
│   ├── chilean_holidays.py   # Chilean national holiday engine
│   ├── config_validator.py   # State dictionary validation
│   ├── email_notifier.py     # SMTP and webhook email dispatch
│   ├── env_helper.py         # .env loader and writer
│   ├── excel_handler.py      # Excel report generator and cell styler
│   ├── logger.py             # Rotating file and console logger
│   └── notification_queue.py # Offline notification outbox
├── views/                     # CustomTkinter graphical user interface
│   ├── components/            # Reusable widgets and modal dialogs
│   │   ├── dialogs.py         # Custom dialogs (date picker, confirmation, person form)
│   │   └── widgets.py         # UI avatars, headers, and row hover helpers
│   ├── tabs/                  # Main tab views
│   │   ├── tab_calendar.py    # Monthly calendar interactive view
│   │   ├── tab_plan.py        # Planning table and exceptions view
│   │   └── tab_settings.py    # Configuration, staff management, and audit view
│   ├── gui.py                 # Main TurnosApp window coordinator
│   └── theme.py               # Dark mode color palette and UI tokens
├── .env.example               # Template for environment configuration
├── app_version.py             # Version metadata and schema version
├── CLAUDE.md                  # Project instructions for AI assistants
├── config.example.json        # Template configuration database
├── conftest.py                # Pytest configuration and root sys.path setup
├── main.py                    # Application launch entry point
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development and test dependencies
├── reset_historial.py         # Utility script to reset shift history
└── Sistema de Turnos.spec     # PyInstaller single-executable build specification
```

## Directory Purposes

**`controllers/`:**
- Purpose: Connects user actions from views with domain operations in models
- Contains: Controller classes with input validation and response tuples
- Key files: `controllers/main_controller.py`

**`models/`:**
- Purpose: Core business domain, rotation algorithm, persistence repository
- Contains: State managers, data types, rotation calculations, config repository
- Key files: `models/shift_manager.py`, `models/config_repository.py`, `models/rotation_engine.py`, `models/domain_types.py`

**`views/`:**
- Purpose: CustomTkinter presentation layer and UI layout
- Contains: App window coordinator, color tokens, widgets, tabs, modal dialogs
- Key files: `views/gui.py`, `views/theme.py`, `views/tabs/tab_plan.py`, `views/tabs/tab_calendar.py`, `views/tabs/tab_settings.py`, `views/components/dialogs.py`, `views/components/widgets.py`

**`utils/`:**
- Purpose: Cross-cutting helper modules
- Contains: Excel workbook generation, email sending, logging, environment variables, Chilean holidays
- Key files: `utils/excel_handler.py`, `utils/email_notifier.py`, `utils/logger.py`, `utils/app_paths.py`, `utils/chilean_holidays.py`, `utils/config_validator.py`, `utils/env_helper.py`, `utils/notification_queue.py`

**`tests/`:**
- Purpose: Automated test verification suite
- Contains: Unit, integration, and UI component tests
- Key files: `tests/test_shift_manager_rotation.py`, `tests/test_excel_handler.py`, `tests/test_manual_assignments.py`, `tests/test_future_preview.py`

**`scripts/`:**
- Purpose: External platform scripts and automation
- Contains: Google Apps Script code for webhook integration
- Key files: `scripts/google_apps_script.js`

**`assets/`:**
- Purpose: Binary assets and icon graphics
- Contains: PNG files for dialog buttons, statuses, and window icons

**`backups/`:**
- Purpose: Automated timestamped snapshots of `config.json` before closures and resets
- Contains: JSON backup files created on month closures

## Key File Locations

**Entry Points:**
- `main.py`: Main desktop app launcher

**Configuration:**
- `config.json`: Primary application state and database (gitignored)
- `config.example.json`: Example base database schema
- `.env`: Environment variables for SMTP and paths (gitignored)
- `.env.example`: Template for environment variables

**Core Logic:**
- `models/shift_manager.py`: Shift allocation, skip queues, exceptions, snapshots
- `models/config_repository.py`: File I/O, validation, and safe atomic updates

**Testing:**
- `conftest.py`: Root path configuration for pytest
- `tests/`: Directory containing ~36 test suite files

## Naming Conventions

**Files:**
- Snake_case for Python source files: `shift_manager.py`, `main_controller.py`
- Test files prefixed with `test_`: `test_shift_manager.py`

**Directories:**
- Lowercase snake_case: `controllers/`, `models/`, `views/`, `utils/`

## Where to Add New Code

**New Feature (e.g. New Tab or Setting):**
- Primary code: Add tab class in `views/tabs/` and register in `views/gui.py`
- Controller methods: Add mediator methods in `controllers/main_controller.py`
- Tests: Add corresponding test file in `tests/test_<feature>.py`

**New Domain Model / Algorithm Rule:**
- Implementation: Add to `models/shift_manager.py` (or delegate into `models/rotation_engine.py`)
- Tests: Add unit tests in `tests/test_shift_manager_rotation.py`

**Utilities:**
- Shared helpers: `utils/`

## Special Directories

**`backups/`:**
- Purpose: Holds automatic recovery copies of `config.json`
- Generated: Yes
- Committed: No (in `.gitignore`)

**`dist/` and `build/`:**
- Purpose: PyInstaller compilation output
- Generated: Yes
- Committed: No (in `.gitignore`)

---

*Structure analysis: 2026-10-06*
