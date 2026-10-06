---
phase: 01-interfaz-de-usuario-y-di-logos-modales
plan: 01
subsystem: ui
tags: [customtkinter, terminology, turnos, spanish-grammar]

requires: []
provides:
  - Reemplazo completo de terminología de guardia a turno en vistas CustomTkinter
  - Suite de pruebas automatizadas tests/test_gui_terminology.py
affects: [02-reportes-excel-y-plantillas-de-notificaciones, 03-documentacion-y-validacion-de-pruebas]

actuals:
  tokens: 1500
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - Verificación estática y dinámica de cadenas de UI mediante pruebas unitarias en tests/test_gui_terminology.py

key-files:
  created:
    - tests/test_gui_terminology.py
  modified:
    - views/components/dialogs.py
    - views/tabs/tab_plan.py
    - views/tabs/tab_calendar.py
    - views/gui.py

key-decisions:
  - "Concordancia gramatical de género en español: 'al turno' para contracción a + el turno, 'Semana de turno', 'Turno manual' y 'Turno regular'"
  - "Mantener intactos los nombres internos de variables y claves de configuración JSON"

patterns-established:
  - "Uso consistente del término 'turno' / 'turnos' en toda la interfaz de usuario"

requirements-completed: [GUI-01, GUI-02, GUI-03, GUI-04]

coverage:
  - id: D1
    description: "Modales y diálogos de asignación en views/components/dialogs.py actualizados a 'Asignar Turno', 'Semana de turno' y 'al turno'"
    requirement: "GUI-01"
    verification:
      - kind: unit
        ref: "tests/test_gui_terminology.py#test_turnos_terminology_present_in_views"
        status: pass
  - id: D2
    description: "Pestaña de planificación views/tabs/tab_plan.py actualizada con 'Cambiar Turno' y '● TURNO EN CURSO'"
    requirement: "GUI-02"
    verification:
      - kind: unit
        ref: "tests/test_gui_terminology.py#test_turnos_terminology_present_in_views"
        status: pass
  - id: D3
    description: "Pestaña de calendario views/tabs/tab_calendar.py actualizada con 'Turno manual' y 'Turno regular'"
    requirement: "GUI-03"
    verification:
      - kind: unit
        ref: "tests/test_gui_terminology.py#test_turnos_terminology_present_in_views"
        status: pass
  - id: D4
    description: "Ventana principal views/gui.py actualizada con 'Turno asignado manualmente' y asunto 'Modificación de Turno'"
    requirement: "GUI-04"
    verification:
      - kind: unit
        ref: "tests/test_gui_terminology.py#test_turnos_terminology_present_in_views"
        status: pass
---

# Phase 01: Plan 01 Summary

## Accomplishments

1. **Diálogos Modales (`views/components/dialogs.py` - GUI-01):**
   - Actualizado el botón de confirmación en `ManualShiftAssignmentDialog` a **"Asignar Turno"**.
   - Actualizada la descripción en `ChangeShiftDialog` a **"Semana de turno: {dates_prompt}"**.
   - Actualizada la etiqueta de selección de personal a **"Nuevo funcionario asignado al turno:"** cuidando la contracción "al".

2. **Pestañas de Planificación y Calendario (`views/tabs/tab_plan.py`, `views/tabs/tab_calendar.py` - GUI-02, GUI-03):**
   - Título modal en `_on_change` actualizado a **"Cambiar Turno"**.
   - Badge visual en `tab_plan.py` actualizado a **"● TURNO EN CURSO"**.
   - Mensajes contextuales y hovers de celda en `tab_calendar.py` actualizados a **"Turno manual: ..."** y **"Turno regular: ..."**.

3. **Ventana Principal y Cobertura de Pruebas (`views/gui.py`, `tests/test_gui_terminology.py` - GUI-04):**
   - Mensaje de barra de estado en `set_manual_assignment` actualizado a **"Turno asignado manualmente: ..."**.
   - Asunto de correo en `_save_month_flow` actualizado a **"[Sistema de Turnos] Modificación de Turno - {MESES[month - 1]} {year}"**.
   - Creado módulo de pruebas unitarias `tests/test_gui_terminology.py` que comprueba que todo el directorio `views/` esté 100% libre de "guardia" y contenga todas las cadenas esperadas.

## Verification

- `Select-String -Path 'views\*.py', 'views\**\*.py' -Pattern 'guardia'` retorna 0 coincidencias.
- `.venv\Scripts\python.exe -m pytest tests/test_gui_terminology.py tests/test_custom_dialogs.py tests/test_tab_plan_ranges.py -q` pasa con 9 pruebas exitosas.

## Commits

- `fdcce0e`: fix(views): reemplazar guardia por turno en dialogs.py
- `ca89f14`: fix(views): reemplazar guardia por turno en tab_plan.py y tab_calendar.py
- `2242c39`: feat(views): actualizar terminologia en gui.py y anadir test_gui_terminology.py

## Self-Check: PASSED
- Archivo `tests/test_gui_terminology.py`: FOUND
- Archivo `views/components/dialogs.py`: FOUND
- Archivo `views/tabs/tab_plan.py`: FOUND
- Archivo `views/tabs/tab_calendar.py`: FOUND
- Archivo `views/gui.py`: FOUND
- Commit fdcce0e: FOUND
- Commit ca89f14: FOUND
- Commit 2242c39: FOUND
