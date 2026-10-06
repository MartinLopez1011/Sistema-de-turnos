# Phase 01: Interfaz de Usuario y Diálogos Modales - Research

**Researched:** 2026-10-06  
**Domain:** CustomTkinter UI Text & Modal Dialogs Terminology Refactoring  
**Confidence:** HIGH  

<user_constraints>
## User Constraints

### Locked Decisions
- Cambiar la palabra "guardia" por "turnos" / "turno" en todos los textos visibles de la aplicación.
- Cuidar estrictamente la concordancia gramatical de género y número en español ("el turno", "al turno", "los turnos").
- NO modificar nombres de variables internas, métodos de clases ni claves en `config.json` para evitar regresiones o inconsistencias de esquema.

### the agent's Discretion
- Formulación concisa de los textos en badges y tooltips para evitar desalineación en el diseño gráfico de CustomTkinter.
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

Single-tier desktop application — todas las capacidades de esta fase residen en la capa de interfaz gráfica (`views/`).

| Capability | Primary Tier | Rationale |
|------------|-------------|-----------|
| Diálogos modales (`views/components/dialogs.py`) | Desktop GUI View | Controles `CTkButton` y `CTkLabel` mostrados al usuario |
| Pestaña de planificación (`views/tabs/tab_plan.py`) | Desktop GUI View | Botones de acción y badge de estado de turno semanal |
| Pestaña de calendario (`views/tabs/tab_calendar.py`) | Desktop GUI View | Texto de tooltip / hover sobre celdas del mes |
| Coordinador de ventana (`views/gui.py`) | Desktop GUI Coordinator | Notificaciones en barra de estado y asunto modal de modificación |
</architectural_responsibility_map>

<research_summary>
## Summary

Se realizó un escaneo exhaustivo en el directorio `views/` para identificar todas las apariciones de "guardia". Se encontraron exactamente 8 apariciones repartidas en 4 archivos.

Todas las apariciones corresponden a etiquetas visuales, títulos de ventanas modales, badges y mensajes de barra de estado. Ninguna de estas cadenas afecta el motor de cálculo o el almacenamiento JSON.

**Recomendación principal:** Reemplazar quirúrgicamente las 8 ocurrencias identificadas aplicando contracciones y concordancias gramaticales precisas ("al turno", "de turno", "Turno en curso").
</research_summary>

<codebase_findings>
## Codebase Findings & Target Changes

### 1. `views/components/dialogs.py` (GUI-01)
- **Línea 451 (`CustomConfirmDialog` / `ManualShiftAssignmentDialog`):**
  - Actual: `btn_frame, text="Asignar Guardia",`
  - Reemplazo: `btn_frame, text="Asignar Turno",`
- **Línea 605 (`ChangeShiftDialog`):**
  - Actual: `dialog, text=f"Semana de guardia: {dates_prompt}",`
  - Reemplazo: `dialog, text=f"Semana de turno: {dates_prompt}",`
- **Línea 612 (`ChangeShiftDialog`):**
  - Actual: `dialog, text="Nuevo funcionario asignado a la guardia:",`
  - Reemplazo: `dialog, text="Nuevo funcionario asignado al turno:",` (contracción a + la guardia -> al turno)

### 2. `views/tabs/tab_plan.py` (GUI-02)
- **Línea 1074 (`_on_change` modal opener):**
  - Actual: `title="Cambiar Guardia de Turno",`
  - Reemplazo: `title="Cambiar Turno",`
- **Línea 1156 (Badge de turno actual / próximo):**
  - Actual: `badge_text = "● GUARDIA EN CURSO" if is_current else "⏳ PRÓXIMO TURNO"`
  - Reemplazo: `badge_text = "● TURNO EN CURSO" if is_current else "⏳ PRÓXIMO TURNO"`

### 3. `views/tabs/tab_calendar.py` (GUI-03)
- **Línea 499 (Hover en celda de cambio manual):**
  - Actual: `m_text = f"📌 Guardia manual de turno: {p_short} (Día {d}) — Motivo: {mot}"`
  - Reemplazo: `m_text = f"📌 Turno manual: {p_short} (Día {d}) — Motivo: {mot}"`
- **Línea 501 (Hover en celda de turno regular):**
  - Actual: `m_text = f"🗓 Guardia de turno regular: {p_short} (Día {d})"`
  - Reemplazo: `m_text = f"🗓 Turno regular: {p_short} (Día {d})"`

### 4. `views/gui.py` (GUI-04)
- **Línea 531 (`set_manual_assignment` status bar):**
  - Actual: `self.set_status(f"Guardia asignada manualmente: {person_name}", "ok")`
  - Reemplazo: `self.set_status(f"Turno asignado manualmente: {person_name}", "ok")`
- **Línea 816 (`_save_month_flow` subject):**
  - Actual: `subject = f"[Sistema de Turnos] Modificación de Guardia - {MESES[month - 1]} {year}"`
  - Reemplazo: `subject = f"[Sistema de Turnos] Modificación de Turno - {MESES[month - 1]} {year}"`
</codebase_findings>

<validation_architecture>
## Validation Architecture

1. **Pruebas existentes:**
   - `tests/test_custom_dialogs.py` y `tests/test_tab_plan_ranges.py` deben ejecutarse y pasar al 100%.
2. **Verificación estática:**
   - Un script / comando de verificación que confirme cero apariciones de "guardia" en `views/`.
3. **Prueba unitaria automatizada:**
   - Agregar aserciones en las pruebas o un nuevo test suite verificando que `views/` solo utiliza terminología de "turno" y "turnos".
</validation_architecture>
