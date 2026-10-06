# Features Research

**Domain:** Shift Scheduling Desktop Terminology Migration ("Guardia" → "Turno")  
**Researched:** 2026-10-06  
**Confidence:** HIGH  

## Feature Breakdown

### Table Stakes (Must Have)

| Feature | Complexity | Dependencies | User Impact |
|---------|------------|--------------|-------------|
| GUI Label and Button Standardization | Low | `views/gui.py`, `views/tabs/`, `views/components/` | All user-visible dialogs, buttons, tooltips, and badges display "Turno/Turnos" |
| Dialog and Modal Text Updates | Low | `views/components/dialogs.py` | Modals (e.g., "Asignar Turno", "Cambiar Turno") reflect proper naming |
| Excel Report Header & Legend Harmonization | Low | `utils/excel_handler.py` | Excel titles ("REGISTRO DE CAMBIOS MANUALES DE TURNO"), legends ("Turno", "Cambio de Turno") match official naming |
| Email and Webhook Notification Text Updates | Low | `utils/email_notifier.py` | Subjects and bodies use "AVISO DE CAMBIO DE TURNO", "RECORDATORIO DE TURNOS" |
| Grammatical Gender and Agreement Alignment | Medium | Across all UI/Export strings | Ensuring feminine agreements ("la guardia", "las guardias") become masculine ("el turno", "los turnos") |

### Differentiators (Value Adds)

| Feature | Complexity | Dependencies | User Impact |
|---------|------------|--------------|-------------|
| Documentation Consistency | Low | `README.md`, `CLAUDE.md`, `POLITICAS_Y_SEGURIDAD.md` | Developers and system administrators have accurate, consistent documentation |
| Test Assertions Parity | Low | `tests/` | Existing tests asserting string formats are updated cleanly to pass without regressions |

### Anti-Features (Deliberately NOT Built)

| Anti-Feature | Why Excluded |
|--------------|--------------|
| Renaming Internal Python Functions/Variables | High risk of breaking reflection, tests, or legacy integrations for zero user benefit |
| Renaming Existing Snapshot/Config JSON Keys | Would require database migration and could break backwards compatibility with archived backups |
| Unsupervised Global Search-and-Replace | Blind string replacement causes Spanish grammatical errors like "la turno" or "de la turno" |

---
*Research completed: 2026-10-06*
