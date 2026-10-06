# Sistema de Turnos

## What This Is

Aplicación de escritorio en Python (CustomTkinter) para la gestión, planificación semanal rotativa, administración de excepciones y emisión de reportes oficiales de turnos para equipos operativos y funcionarios. Genera reportes mensuales en Excel y notificaciones automáticas vía SMTP y webhook.

## Core Value

Planificación confiable y automatizada de turnos semanales con asignación rotativa justa, gestión precisa de excepciones y generación de reportes sin errores de estado.

## Requirements

### Validated

- ✓ Planificación y asignación rotativa de turnos semanales con cola circular — existing
- ✓ Gestión de excepciones (Días Administrativos, Feriados Legales, Licencias, Otros) — existing
- ✓ Generación y exportación de reportes mensuales estilizados en Excel (`openpyxl`) — existing
- ✓ Notificaciones por correo electrónico vía SMTP directo y webhook Google Apps Script — existing
- ✓ Persistencia atómica de configuración e historial en `config.json` con respaldos automáticos — existing
- ✓ Interfaz gráfica moderna en modo oscuro (CustomTkinter) con calendario mensual y pestañas de ajuste — existing

### Active

- [ ] Reemplazar la terminología "guardia/guardias" por "turno/turnos" en toda la interfaz gráfica de usuario (GUI: pestañas de planificación, calendario, ajustes, botones, badges y diálogos modales)
- [ ] Actualizar los textos y encabezados en las plantillas de reportes Excel generados (`utils/excel_handler.py`), incluyendo títulos de tablas de cambios y leyendas
- [ ] Actualizar las plantillas de correos, notificaciones automáticas y notas informativas en `utils/email_notifier.py`
- [ ] Aplicar concordancia gramatical contextual adecuada (ej: "la guardia" → "el turno", "las guardias" → "los turnos", "de guardia" → "de turno")
- [ ] Actualizar la documentación de usuario y especificaciones del proyecto (`README.md`, `CLAUDE.md`, `POLITICAS_Y_SEGURIDAD.md`)

### Out of Scope

- Renombrar variables internas de Python o identificadores de base de datos que no impacten la experiencia de usuario ni la interfaz — evita riesgo de regresiones en la lógica interna del motor
- Modificar el esquema de claves históricas en `config.json` — previene incompatibilidad con historiales existentes

## Context

- Entorno de escritorio Windows (Python 3.14 + CustomTkinter), compilable a ejecutable standalone mediante PyInstaller.
- El sistema cuenta con una suite automatizada de más de 250 pruebas en `pytest`.
- El cambio solicitado unifica la terminología institucional para hablar consistentemente de "turnos" en lugar de "guardias".

## Constraints

- **Compatibilidad**: No romper las pruebas automatizadas existentes ni la integridad de los datos en `config.json`.
- **Experiencia de usuario**: Mantener la estética visual y diseño en modo oscuro sin desalinear elementos de la interfaz.
- **Concordancia de idioma**: Cuidar género y número gramatical al reemplazar términos en español.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Alcance centrado en textos visibles al usuario | Cambiar textos de GUI, Excel, emails y documentación satisface el requerimiento sin alterar la estabilidad interna del motor | — Pending |
| Ajuste con concordancia gramatical | Reemplazar considerando género ("el turno" vs "la guardia") asegura redacción natural y profesional en la aplicación | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-06 after initialization*
