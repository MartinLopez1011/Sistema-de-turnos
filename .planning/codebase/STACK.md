---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# Technology Stack

**Analysis Date:** 2026-10-06

## Languages

**Primary:**
- Python 3.14 (3.14.7 active in `.venv`) - Core application logic, GUI, controllers, models, utilities, and test suites

**Secondary:**
- JavaScript (ES6+) - Google Apps Script webhook integration (`scripts/google_apps_script.js`)

## Runtime

**Environment:**
- CPython 3.14.7 (Windows x86-64)
- Standalone portable desktop executable compiled via PyInstaller (`dist/Sistema de Turnos.exe`)

**Package Manager:**
- pip (Standard Python package installer)
- Lockfile: missing (relies on unpinned/minimum versions in `requirements.txt` and `requirements-dev.txt`)

## Frameworks

**Core:**
- CustomTkinter 5.x (`customtkinter`) - Modern dark-mode GUI desktop framework built on Tkinter
- openpyxl 3.x (`openpyxl`) - Excel workbook generation, cell styling, and print formatting
- Pillow 10.x/11.x (`Pillow`) - UI icon loading, image scaling, and avatar graphics

**Testing:**
- pytest 9.1.1 (`pytest`) - Test runner and assertion framework
- pytest-mock 3.x (`pytest-mock`) - Fixture-based test mocking integration

**Build/Dev:**
- PyInstaller 6.x (`pyinstaller`) - Standalone single-executable bundler (`Sistema de Turnos.spec`)

## Key Dependencies

**Critical:**
- `customtkinter` (>=5.2.0) - Core desktop UI widgets and windowing (`views/gui.py`, `views/tabs/tab_plan.py`)
- `openpyxl` (>=3.1.0) - Monthly shift spreadsheet generation and color styling (`utils/excel_handler.py`)
- `holidays` (>=0.104,<1) - Chilean national holiday calculation (`utils/chilean_holidays.py`)
- `Pillow` (>=10.0.0) - Graphical image handling for avatars and status icons (`views/components/widgets.py`)
- `python-docx` (>=1.1.0) - Word document interaction and specifications documentation

**Infrastructure:**
- `smtplib` / `email` (Python standard library) - Direct SMTP email transmission with file attachments (`utils/email_notifier.py`)
- `urllib.request` / `socket` (Python standard library) - Network connectivity checks and webhook HTTP requests (`utils/email_notifier.py`)

## Configuration

**Environment:**
- Loaded via `utils/env_helper.py` (`load_env_file`) from `.env` in application data directory
- Variables: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_NAME`, `VPN_PROVEEDOR`, `VPN_FORMULARIO_URL`, `VPN_CORREO_SOPORTE`

**Build:**
- `Sistema de Turnos.spec` - PyInstaller build specification (single-file mode, windowed/noconsole, bundles `assets/` and `holidays.countries.chile`)

## Platform Requirements

**Development:**
- Windows 10/11 with Python 3.14 (virtual environment `.venv`)
- Command: `pip install -r requirements-dev.txt`

**Production:**
- Windows 10/11 64-bit desktop environment
- Standalone `.exe` (`dist/Sistema de Turnos.exe`), zero Python installation required, runs in user space without administrator privileges

---

*Stack analysis: 2026-10-06*
