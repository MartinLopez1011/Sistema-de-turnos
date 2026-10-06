---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# Coding Conventions

**Analysis Date:** 2026-10-06

## Naming Patterns

**Files:**
- Snake_case for modules and test scripts (`main_controller.py`, `test_shift_manager_rotation.py`)

**Functions & Methods:**
- Snake_case with descriptive action verbs: `generate_shifts()`, `preview_shifts()`, `load_config()`, `_parse_week_range()`
- Private/internal helpers prefixed with single underscore: `_build_ui()`, `_default_payload()`, `_init_defaults()`, `_confirm_action()`

**Variables:**
- Snake_case for local variables and attributes: `start_date`, `shift_manager`, `person_dropdown`
- UPPER_SNAKE_CASE for global constants: `FONT_FAMILY`, `MESES`, `EXC_COLORS`, `APP_NAME`, `CONFIG_SCHEMA_VERSION`

**Types & Classes:**
- PascalCase for classes and custom dialogs: `ShiftManager`, `MainController`, `TurnosApp`, `ExcelHandler`, `CustomConfirmDialog`

## Code Style

**Formatting:**
- Standard PEP 8 4-space indentation
- Maximum line length ~100-120 characters

**Linting:**
- No automated external linter enforced in CI (Flake8/Black/Ruff not present in dev requirements)
- Runtime schema and invariant validation enforced via `utils/config_validator.py`

## Import Organization

**Order:**
1. Python standard library imports (`os`, `sys`, `json`, `datetime`, `calendar`, `threading`)
2. Third-party dependencies (`customtkinter`, `openpyxl`, `holidays`, `PIL`)
3. Internal application modules (`models.*`, `controllers.*`, `views.*`, `utils.*`)

**Path Aliases:**
- None configured; `conftest.py` ensures project root is on `sys.path` for uniform root-relative imports

## Error Handling

**Patterns:**
- Controllers return `(success: bool, message: str)` tuples for user-facing actions
- Domain models raise descriptive exceptions or log warnings and fall back to safe defaults
- File I/O operations wrap writes in atomic `.tmp` files with `os.fsync()` and `os.replace()`
- Top-level Tkinter and system crashes intercepted with `messagebox.showerror` and logged to `turnos.log`

## Logging

**Framework:** Python standard library `logging` configured via `utils/logger.py` (`turnos.log` rotating handler)

**Patterns:**
- Always obtain module-scoped logger via `logger = get_logger("module_name")`
- Use formatted arguments instead of f-strings: `logger.info("Backup creado: %s", path)`
- Pass `exc_info=True` on unexpected exceptions

## Comments

**When to Comment:**
- Docstrings on public methods explaining arguments, return structures, and constraints
- Inline comments explaining complex domain rules (e.g., cooling period between shifts, December holiday restrictions, Monday-to-Monday week shifts)

**JSDoc/TSDoc:**
- Not applicable (Python project uses standard Python docstrings)

## Function Design

**Size:**
- Modular UI builders (`_build_ui()`, `_build_tab_plan()`) partitioned into focused helper methods
- Pure functions preferred for date calculations and schedule previews

**Parameters:**
- Explicit typing hints used in newer modules (`models/domain_types.py`, `models/config_repository.py`)
- Default parameter values for optional flags (`recalculate_history=False`, `motivo=""`)

**Return Values:**
- Controllers return `(bool, Any)` tuples
- Generators and parsers return explicit lists or dictionaries

## Module Design

**Exports:**
- Explicit imports used across modules; `__all__` not commonly specified
- Package directories include `__init__.py` where applicable

**Barrel Files:**
- `views/components/__init__.py` and `views/tabs/__init__.py` expose component classes

---

*Convention analysis: 2026-10-06*
