# Stack Research

**Domain:** Desktop UI Terminology Refactoring & Report Standardization (Python / CustomTkinter / openpyxl)  
**Researched:** 2026-10-06  
**Confidence:** HIGH  

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.14.7 | Application runtime | Existing project environment; maintains native desktop performance |
| CustomTkinter | 5.2.2 | GUI Framework | Controls all labels, titles, dialogs, buttons, and status messages |
| openpyxl | 3.1.5 | Excel Spreadsheet Generation | Generates monthly shift calendars and changes audit sheets |
| pytest | 9.1.1 | Regression Testing Suite | Validates that string replacements don't break regexes, contracts, or exports |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | Built-in | Regex validation | Checking email patterns and text parsing in notifier and views |
| email.mime (stdlib) | Built-in | Email composition | Formatting notification subjects and plaintext body messages |
| unittest.mock | Built-in | Test assertions | Asserting that GUI dialogs and export helpers format strings correctly |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Test suite runner | Run `.venv\Scripts\python.exe -m pytest -q` to verify full suite |
| git | Version control | Commit atomic changes per component |

## Installation

```bash
# Existing virtual environment already contains all dependencies:
.venv\Scripts\pip install -r requirements-dev.txt
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| In-place string update in views & utils | Full i18n gettext localization | Only if multi-language support (e.g. English + Spanish) is required in the future |
| Focused user-facing replacement | Full variable and schema rename | Only if breaking database changes and comprehensive migrations are desired |

## What NOT to Use

- Do NOT alter JSON keys in `config.json` (such as historical entries or internal keys) to avoid corrupting previous backups and states.
- Do NOT use blanket find-and-replace scripts without checking grammatical gender in Spanish (e.g., replacing "la guardia" with "la turno" would produce grammatical errors).

---
*Research completed: 2026-10-06*
