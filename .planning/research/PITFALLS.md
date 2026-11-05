# Pitfalls Research

**Domain:** Terminology Refactoring & String Replacements  
**Researched:** 2026-10-06  
**Confidence:** HIGH  

## Critical Pitfalls to Avoid

### 1. Spanish Gender and Article Mismatch

- **The Pitfall:** Replacing "guardia" mechanically without updating articles and prepositions results in grammatically broken Spanish phrases:
  - `"la guardia"` → broken: `"la turno"` | correct: `"el turno"`
  - `"las guardias"` → broken: `"las turnos"` | correct: `"los turnos"`
  - `"a la guardia"` → broken: `"a la turno"` | correct: `"al turno"`
  - `"de guardia"` → broken: `"de la turno"` | correct: `"de turno"`
- **Prevention:** Review each replacement in context and adjust surrounding articles, pronouns, and adjectives.

### 2. Breaking Automated Test String Assertions

- **The Pitfall:** Several existing tests in `tests/` inspect exact string contents of generated Excel headers, email subjects, or dialog titles:
  - E.g., tests asserting `"CAMBIO MANUAL DE GUARDIA"` or email subjects containing `"[Sistema de Turnos] Modificación de Guardia"`.
- **Prevention:** Run test suite with `pytest` after string replacements and update corresponding test assertions that verify these specific user-facing strings.

### 3. Modifying Internal Data Identifiers or Schema Keys

- **The Pitfall:** Accidental replacement in JSON keys or internal database structures:
  - If a key like `"historial"` or snapshot structures were mutated, existing `config.json` files would fail to load or validate.
- **Prevention:** Keep all changes strictly isolated to presentation layers, user-facing output messages, report generation strings, and documentation.

### 4. Layout Clipping or Text Overflow in GUI Buttons

- **The Pitfall:** In CustomTkinter, button width and label wraps depend on string lengths.
  - E.g., `"Asignar Guardia"` (15 chars) vs `"Asignar Turno"` (13 chars). Since "turno" is generally shorter or equal in length to "guardia", truncation risk is low, but badge alignments (e.g. `"GUARDIA EN CURSO"` → `"TURNO EN CURSO"`) must be verified.
- **Prevention:** Verify visual rendering of badges and buttons in `views/gui.py` and `views/tabs/tab_plan.py`.

---
*Research completed: 2026-10-06*
