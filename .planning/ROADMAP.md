# Roadmap: Sistema de Turnos

## Overview

Plan para unificar la terminología de "guardia" a "turnos" en toda la aplicación Sistema de Turnos, abarcando interfaz gráfica (CustomTkinter), reportes oficiales en Excel (openpyxl), notificaciones por correo/webhook (SMTP), documentación y suites de pruebas automatizadas.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Interfaz de Usuario y Diálogos Modales** - Reemplazar "guardia" por "turno/turnos" en botones, badges, modales y mensajes de la GUI con concordancia gramatical
- [ ] **Phase 2: Reportes Excel y Plantillas de Notificaciones** - Actualizar títulos, auditorías, leyendas y plantillas de correo/webhook a la terminología de turnos
- [ ] **Phase 3: Documentación y Validación de Pruebas** - Sincronizar documentación y asegurar que toda la suite de pruebas automatizadas pase exitosamente

## Phase Details

### Phase 1: Interfaz de Usuario y Diálogos Modales
**Goal**: Reemplazar la terminología "guardia" por "turno/turnos" en toda la interfaz gráfica de CustomTkinter, asegurando concordancia de género y redacción natural.
**Mode**: mvp
**Depends on**: Nothing (primera fase)
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04
**Success Criteria** (what must be TRUE):
  1. Los diálogos modales en `views/components/dialogs.py` muestran "Asignar Turno", "Cambiar Turno" y "Semana de turno".
  2. La pestaña de planificación `views/tabs/tab_plan.py` muestra los badges "TURNO EN CURSO" y "PRÓXIMO TURNO".
  3. La pestaña de calendario `views/tabs/tab_calendar.py` muestra mensajes de hover y celda con "Turno manual" y "Turno regular".
  4. La ventana principal `views/gui.py` muestra mensajes de estado como "Turno asignado manualmente".
**Plans**: 1 plan
- [ ] 01-01-PLAN.md — Reemplazar terminología de guardia en diálogos, badges y vistas GUI

### Phase 2: Reportes Excel y Plantillas de Notificaciones
**Goal**: Estandarizar la generación de reportes mensuales en Excel y el envío de notificaciones automáticas con la terminología de turnos.
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: EXCEL-01, EXCEL-02, EXCEL-03, NOTIF-01, NOTIF-02, NOTIF-03
**Success Criteria** (what must be TRUE):
  1. El reporte Excel titula "REGISTRO DE CAMBIOS MANUALES DE TURNO (PERMUTAS / REEMPLAZOS)" y la leyenda muestra "Turno" y "Cambio de Turno (Manual)".
  2. Los comentarios y encabezados de columna en la hoja de cambios indican "TURNO ORIGINAL".
  3. Los correos automáticos en `utils/email_notifier.py` envían asuntos con "[Sistema de Turnos] Modificación de Turno" y avisos con "AVISO DE CAMBIO DE TURNO".
  4. La nota de VPN se actualiza a "RECORDATORIO DE TURNOS" con concordancia adecuada.
**Plans**: 1 plan

### Phase 3: Documentación y Validación de Pruebas
**Goal**: Sincronizar la documentación del repositorio y validar que todas las pruebas unitarias y de integración pasen sin fallas.
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: DOC-01, TEST-01
**Success Criteria** (what must be TRUE):
  1. `README.md`, `CLAUDE.md` y `POLITICAS_Y_SEGURIDAD.md` utilizan consistentemente la terminología de turnos.
  2. La suite de pruebas en `pytest` valida que los textos modificados en Excel, diálogos y notificaciones se generan correctamente sin regresiones.
**Plans**: 1 plan

---
*Roadmap created: 2026-10-06*
