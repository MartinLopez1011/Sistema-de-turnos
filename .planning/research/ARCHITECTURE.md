# Architecture Research

**Domain:** Terminology Migration Across Architectural Layers  
**Researched:** 2026-10-06  
**Confidence:** HIGH  

## Layered Impact Analysis

```text
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                     │
│  - views/gui.py (Status messages, window titles)             │
│  - views/tabs/tab_plan.py (Badges, headers, tooltips)       │
│  - views/tabs/tab_calendar.py (Hover status text)           │
│  - views/components/dialogs.py (Modal titles, prompt labels) │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Controller / Coordination                   │
│  - controllers/main_controller.py (Status return strings)   │
└───────────────────────────┬─────────────────────────────────┘
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
┌────────────────────────────────┐ ┌──────────────────────────┐
│          Domain Model          │ │     Report & Notifier    │
│  (Internal logic preserved;    │ │ - utils/excel_handler.py │
│   no schema mutation needed)   │ │ - utils/email_notifier.py│
└────────────────────────────────┘ └──────────────────────────┘
```

## Component Boundaries & Touchpoints

1. **GUI Presentation (`views/`):**
   - `views/gui.py`: Status bar updates (`"Turno asignado manualmente: {name}"`) and email modal titles.
   - `views/tabs/tab_plan.py`: Badges (`"TURNO EN CURSO"`, `"PRÓXIMO TURNO"`), context menu items (`"Cambiar Turno"`).
   - `views/tabs/tab_calendar.py`: Cell hover text (`"Turno manual: {name}"`, `"Turno regular: {name}"`).
   - `views/components/dialogs.py`: Dialog titles (`"Asignar Turno"`, `"Semana de turno: {dates}"`, `"Nuevo funcionario asignado al turno:"`).

2. **Excel Reporting (`utils/excel_handler.py`):**
   - Header titles in change log: `"REGISTRO DE CAMBIOS MANUALES DE TURNO (PERMUTAS / REEMPLAZOS)"`.
   - Cell comments and change descriptions: `"CAMBIO MANUAL DE TURNO"`, `"Turno original: {orig_p}"`.
   - Table column headers: `"TURNO ORIGINAL"`, `"TURNO NUEVO"`.
   - Legend descriptions: `"Turno"` (red), `"Cambio de Turno (Manual)"` (green).

3. **Notifications (`utils/email_notifier.py`):**
   - Subjects: `"[Sistema de Turnos] Modificación de Turno - {MES} {AÑO}"`.
   - Plaintext headers: `"SISTEMA DE GESTIÓN DE TURNOS - AVISO DE CAMBIO DE TURNO"`.
   - Body descriptions: `"Turno programado original: {anterior}"`, `"Nuevo turno asignado: {nuevo}"`.
   - Informative notes: `"RECORDATORIO DE TURNOS: Se recuerda a todos los funcionarios que deban cumplir turnos..."`.

4. **Documentation (`README.md`, `CLAUDE.md`, `POLITICAS_Y_SEGURIDAD.md`):**
   - Text updates in manuals, security policies, and developer guides to ensure unified vocabulary.

---
*Research completed: 2026-10-06*
