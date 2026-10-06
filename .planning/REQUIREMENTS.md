# Requirements: Sistema de Turnos

**Defined:** 2026-10-06  
**Core Value:** Planificación confiable y automatizada de turnos semanales con asignación rotativa justa, gestión precisa de excepciones y generación de reportes sin errores de estado.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Interfaz Gráfica (GUI)

- [ ] **GUI-01**: Modales y diálogos de asignación en `views/components/dialogs.py` muestran "Asignar Turno", "Cambiar Turno" y textos contextuales asociados.
- [ ] **GUI-02**: Pestaña de planificación `views/tabs/tab_plan.py` muestra badges actualizados ("TURNO EN CURSO", "PRÓXIMO TURNO") y opciones contextuales sin referencia a "guardia".
- [ ] **GUI-03**: Pestaña de calendario `views/tabs/tab_calendar.py` muestra mensajes de hover y ayuda actualizados ("Turno manual", "Turno regular").
- [ ] **GUI-04**: Ventana principal `views/gui.py` muestra mensajes de barra de estado consistentes ("Turno asignado manualmente").

### Reportes Excel

- [ ] **EXCEL-01**: Encabezado de la tabla de auditoría de cambios manuales en `utils/excel_handler.py` titula "REGISTRO DE CAMBIOS MANUALES DE TURNO (PERMUTAS / REEMPLAZOS)".
- [ ] **EXCEL-02**: Comentarios de celda y columnas de auditoría utilizan "TURNO ORIGINAL" y "Turno original".
- [ ] **EXCEL-03**: Leyenda de convenciones al pie del reporte mensual clasifica las muestras como "Turno" y "Cambio de Turno (Manual)".

### Notificaciones y Correo

- [ ] **NOTIF-01**: Asuntos y encabezados de correo en `utils/email_notifier.py` usan "[Sistema de Turnos] Modificación de Turno" y "AVISO DE CAMBIO DE TURNO".
- [ ] **NOTIF-02**: Líneas descriptivas del cuerpo del correo detallan "Turno programado original" y "Nuevo turno asignado".
- [ ] **NOTIF-03**: Nota informativa de VPN parametriza "RECORDATORIO DE TURNOS" con concordancia gramatical correcta.

### Documentación y Pruebas

- [ ] **DOC-01**: Documentación del proyecto (`README.md`, `CLAUDE.md`, `POLITICAS_Y_SEGURIDAD.md`) refleja la terminología unificada de "turnos".
- [ ] **TEST-01**: Pruebas unitarias y de integración en `tests/` que validan cadenas generadas se actualizan y pasan sin regresiones.

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
| GUI-01 | Phase 1 | Pending |
| GUI-02 | Phase 1 | Pending |
| GUI-03 | Phase 1 | Pending |
| GUI-04 | Phase 1 | Pending |
| EXCEL-01 | Phase 2 | Pending |
| EXCEL-02 | Phase 2 | Pending |
| EXCEL-03 | Phase 2 | Pending |
| NOTIF-01 | Phase 2 | Pending |
| NOTIF-02 | Phase 2 | Pending |
| NOTIF-03 | Phase 2 | Pending |
| DOC-01 | Phase 3 | Pending |
| TEST-01 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-10-06*
