# Requirements: Sistema de Turnos

**Defined:** 2026-10-06  
**Core Value:** Planificación confiable y automatizada de turnos semanales con asignación rotativa justa, gestión precisa de excepciones y generación de reportes sin errores de estado.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Interfaz Gráfica (GUI)

- [x] **GUI-01**: Modales y diálogos de asignación en `views/components/dialogs.py` muestran "Asignar Turno", "Cambiar Turno" y textos contextuales asociados.
- [x] **GUI-02**: Pestaña de planificación `views/tabs/tab_plan.py` muestra badges actualizados ("TURNO EN CURSO", "PRÓXIMO TURNO") y opciones contextuales sin referencia a "guardia".
- [x] **GUI-03**: Pestaña de calendario `views/tabs/tab_calendar.py` muestra mensajes de hover y ayuda actualizados ("Turno manual", "Turno regular").
- [x] **GUI-04**: Ventana principal `views/gui.py` muestra mensajes de barra de estado consistentes ("Turno asignado manualmente").

### Reportes Excel

- [x] **EXCEL-01**: Encabezado de la tabla de auditoría de cambios manuales en `utils/excel_handler.py` titula "REGISTRO DE CAMBIOS MANUALES DE TURNO (PERMUTAS / REEMPLAZOS)".
- [x] **EXCEL-02**: Comentarios de celda y columnas de auditoría utilizan "TURNO ORIGINAL" y "Turno original".
- [x] **EXCEL-03**: Leyenda de convenciones al pie del reporte mensual clasifica las muestras como "Turno" y "Cambio de Turno (Manual)".

### Notificaciones y Correo

- [x] **NOTIF-01**: Asuntos y encabezados de correo en `utils/email_notifier.py` usan "[Sistema de Turnos] Modificación de Turno" y "AVISO DE CAMBIO DE TURNO".
- [x] **NOTIF-02**: Líneas descriptivas del cuerpo del correo detallan "Turno programado original" y "Nuevo turno asignado".
- [x] **NOTIF-03**: Nota informativa de VPN parametriza "RECORDATORIO DE TURNOS" con concordancia gramatical correcta.

### Documentación y Pruebas

- [x] **DOC-01**: Documentación del proyecto (`README.md`, `CLAUDE.md`, `POLITICAS_Y_SEGURIDAD.md`) refleja la terminología unificada de "turnos".
- [x] **TEST-01**: Pruebas unitarias y de integración en `tests/` que validan cadenas generadas se actualizan y pasan sin regresiones.

## v2 Requirements

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Internacionalización

- **I18N-01**: Sistema formal de internacionalización gettext para soporte multilingüe.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Renombrar variables o métodos internos del motor de rotación | Alto riesgo de introducir regresiones en la lógica matemática de asignación para cero beneficio de usuario |
| Alterar claves del esquema JSON en `config.json` | Rompería compatibilidad con archivos y respaldos históricos de datos |
| Reemplazo ciego sin concordancia de género ("la turno") | Generaría errores ortográficos y gramaticales en la aplicación |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUI-01 | Phase 1 | Complete |
| GUI-02 | Phase 1 | Complete |
| GUI-03 | Phase 1 | Complete |
| GUI-04 | Phase 1 | Complete |
| EXCEL-01 | Phase 2 | Complete |
| EXCEL-02 | Phase 2 | Complete |
| EXCEL-03 | Phase 2 | Complete |
| NOTIF-01 | Phase 2 | Complete |
| NOTIF-02 | Phase 2 | Complete |
| NOTIF-03 | Phase 2 | Complete |
| DOC-01 | Phase 3 | Complete |
| TEST-01 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-10-06*
