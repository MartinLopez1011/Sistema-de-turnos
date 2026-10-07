# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Sistema de Turnos — Resumen de Proyecto para IA

> **Propósito de este archivo:** Proveer contexto suficiente al asistente de IA para trabajar sin necesidad de leer cada archivo en detalle. Leé esto antes de cualquier otra cosa.

---

## 0. Comandos

```bash
pip install -r requirements-dev.txt          # dentro de .venv
.venv\Scripts\python.exe main.py             # ejecutar la app
.venv\Scripts\python.exe -m pytest -q        # toda la suite (~165 tests, ~100 s)
.venv\Scripts\python.exe -m pytest tests/test_shift_manager_rotation.py -x   # un archivo
.venv\Scripts\python.exe -m pytest tests/test_shift_manager.py::NombreTest::test_x   # un test
pyinstaller "Sistema de Turnos.spec"         # build del .exe
python reset_historial.py                    # limpiar historial
```

`conftest.py` solo agrega la raíz del proyecto al `sys.path`. No hay linter configurado.

## 1. ¿Qué es este proyecto?

Aplicación de escritorio en **Python** que gestiona la asignación rotativa semanal de turnos para un equipo de 16 personas. Genera reportes Excel y tiene una GUI moderna.

- **Tecnología principal:** Python + CustomTkinter (GUI dark mode)
- **Distribución:** Compilado con PyInstaller → `Sistema de Turnos.exe` (standalone, sin instalar Python)
- **Persistencia:** Un único archivo `config.json` en el directorio del ejecutable
- **Output:** Archivos `turnos_<Mes>_<Año>.xlsx` generados con `openpyxl`

---

## 2. Arquitectura (MVC simple)

```
main.py                    ← Entrypoint. Detecta si es .exe o script y resuelve root_path
controllers/
  main_controller.py       ← Orquesta modelo y vista. Sin lógica de negocio.
models/
  shift_manager.py         ← TODA la lógica de negocio (rotación, snapshots, excepciones, backups)
views/
  gui.py                   ← Ventana principal TurnosApp (coordinador liviano)
  theme.py                 ← Paleta de diseño P, avatares, constantes MESES/DIAS
  components/              ← Widgets auxiliares y diálogos CTk modales
  tabs/                    ← Pestañas modulares: tab_plan, tab_calendar, tab_settings
utils/
  logger.py                ← Logging rotativo en archivo (turnos.log) y consola
  excel_handler.py         ← Construye la plantilla Excel en memoria, escribe turnos y guarda reporte
  chilean_holidays.py      ← Obtiene feriados nacionales de Chile y normaliza sus nombres
  email_notifier.py        ← Validación de internet, formateo de texto plano y webhook Apps Script
scripts/
  google_apps_script.js    ← Código fuente gratuito listo para desplegar en Google Apps Script
assets/                    ← Íconos PNG (success, error, save)
backups/                   ← Respaldos automáticos fechados de config.json
config.json                ← Base de datos en JSON (ver sección 4)
Sistema_de_Gestion_de_Turnos.docx ← Documento ejecutivo (estático, ya no se genera por script)
Manual_de_Usuario_Sistema_de_Turnos.pdf ← Manual de usuario oficial en PDF (actualizado)
Requerimientos_del_Sistema_Turnos.docx ← Documento Word de requerimientos y alcance definido
dist/Sistema de Turnos.exe   ← Ejecutable standalone autónomo (sin instalador, no requiere admin)
```

### Notas de arquitectura adicionales (verificadas en el código)

- `main.py` resuelve el directorio de datos con `utils/app_paths.get_application_data_dir()`, carga `.env` con `utils/env_helper.load_env_file` e instala un `sys.excepthook` global que loguea y muestra un messagebox.
- `utils/` también contiene `config_validator.py`, `notification_queue.py` (cola `pending_notifications.json` para reintentos) y `env_helper.py`. `email_notifier.py` soporta SMTP directo con adjunto (variables `SMTP_*` en `.env`, ver `.env.example`) y webhook Apps Script (`WEBHOOK_URL`, `NOTIFICACIONES_ACTIVAS`) como respaldo.
- `ShiftManager` (~1960 líneas): `generate_shifts` delega en `RotationEngine.generate` (`models/rotation_engine.py`), que a su vez llama a `_generate_shifts_legacy`: ahí vive toda la lógica real. Aplica una ventana de enfriamiento `min_gap_weeks=4` entre turnos de una misma persona. También maneja auditoría (`_record_audit`), backups/restauración y `archive_old_records`.
- Las excepciones `OTR` exigen motivo (≥3 caracteres); las asignaciones manuales exigen motivo. Cada persona puede tener `email`.
- `config.json`, `.env`, `config.privado.json`, `backups/`, `*.spec`, `dist/` y `build/` están en `.gitignore`: no commitear datos operativos. Documentación de usuario en `README.md`; políticas en `SECURITY.md` y `POLITICAS_Y_SEGURIDAD.md`.

---

## 3. Flujo de la aplicación

```
main.py
  └─► MainController(root_path)
        └─► ShiftManager(config.json)   ← carga estado al iniciar
  └─► TurnosApp(controller)
        ├─► Tab "Planificación"         ← seleccionar mes/año + ver tabla de turnos + excepciones
        ├─► Tab "Ver Turnos del Mes"    ← vista calendario mensual con colores
        └─► Tab "Ajustes"               ← gestión de personal, historial, reinicio
```

### Flujo de generación de un mes:

1. Usuario selecciona **mes/año** y opcionalmente agrega **excepciones** (DA, FL, LIC u OTR con fecha)
2. `preview_shifts(year, month, exceptions)` → genera vista previa sin guardar
3. Usuario presiona **"Exportar Excel"** → `process_generation()` → crea `turnos_Mes_Año.xlsx`
4. Usuario presiona **"Cerrar Mes"** → `advance_queue()` → guarda en `historial`, crea snapshot del mes siguiente, actualiza puntero global

> ⚠️ **Exportar** y **Cerrar Mes** son operaciones SEPARADAS. Exportar NO modifica el estado.

---

## 4. `config.json` — Estructura y significado

```json
{
  "personal": [{"id": 1, "nombre": "APELLIDO NOMBRE"}],       // Lista ordenada de personas
  "inicio": {                                                   // Semanas con asignación fija/inmutable
    "2026-08-03_2026-08-09": "NOMBRE COMPLETO"
  },
  "historial": {                                                // Semanas ya cerradas (no se recalculan)
    "YYYY-MM-DD_YYYY-MM-DD": "NOMBRE COMPLETO"
  },
  "siguiente_id": 13,                                           // ID de la persona que toca ahora
  "pendientes": [],                                             // IDs que "deben turno" por haber sido saltados
  "snapshots": {                                                // Estado al inicio de cada mes futuro
    "2026-09": {"siguiente_id": 5, "pendientes": [3]}
  },
  "excepciones": {                                              // Excepciones guardadas por período
    "2026-09": [{"persona": "NOMBRE", "fecha": "2026-09-15", "tipo": "DA"}]
  },
  "asignaciones_manuales": {                                    // Asignaciones forzadas/manuales por semana
    "2026-09": {"2026-09-07_2026-09-13": "JUAN PEREZ"}
  },
  "asignaciones_manuales_motivos": {                            // Motivos obligatorios de asignación manual
    "2026-09": {"2026-09-07_2026-09-13": "Permuta acordada"}
  },
  "notificaciones": {                                           // Configuración del webhook serverless
    "webhook_url": "https://script.google.com/macros/s/.../exec",
    "activo": true
  }
}
```

**Tipos de excepción soportados:**
- `DA` = Día Administrativo (color naranja `#B45309`)
- `FL` = Feriado Legal (color violeta `#5B21B6`)
- `LIC` = Licencia (color turquesa `#0E7490`)
- `OTR` = Otro (color gris `#374151`)
*(Nota: El tipo legacy `FOR` se mantiene como fallback de compatibilidad histórica, pero fue reemplazado en la interfaz por asignación manual directa en la tarjeta semanal).*

---

## 5. Lógica de rotación (`ShiftManager.generate_shifts`)

El algoritmo recorre cada semana del mes calendario y:

1. Si la semana tiene asignación manual directa (`manual_assignments` o `asignaciones_manuales`) → asigna a esa persona, marca `es_manual: True` y avanza el puntero/pendientes.
2. Si la semana está en `self.inicio` → asigna fijo, continúa (no modifica puntero)
3. Si la semana está en `self.historial` → respeta lo guardado, SALVO que el asignado tenga excepción en esa semana (en ese caso recalcula)
4. Si hay **pendientes** → intenta asignar al primero de la lista que NO tenga excepción
5. Si no hay pendientes libres → sigue la **lista circular** desde `siguiente_id`
6. Si alguien es saltado (tiene excepción) → se agrega a `pendientes` para recuperar turno después
7. En diciembre, evita que una persona repita el mismo feriado nacional chileno del diciembre anterior cuando existe otra alternativa
8. Si no existe alternativa por las restricciones de rotación, asigna igualmente y registra una advertencia visible

La previsualización de un mes futuro sin snapshot encadena temporalmente los meses desde el estado actual para no reiniciar la rotación. Un mes cerrado puede recalcularse si cambian sus excepciones.

La regla anual de feriados usa solo asignaciones confiables de `historial` o `inicio`. Si no existe el antecedente del diciembre anterior, no aplica el bloqueo. Los feriados móviles se comparan por nombre normalizado y no por fecha fija.

**Snapshot:** Al cerrar un mes se guarda el estado `{siguiente_id, pendientes}` del mes SIGUIENTE para que la previsión futura sea correcta aunque se cierren meses fuera de orden.

---

## 6. GUI — `views/gui.py`

**Clase principal:** `TurnosApp(ctk.CTk)` — hereda de CustomTkinter.

**Design System:** Diccionario `P` con todos los colores del tema dark. NO usar colores hardcodeados, siempre referenciar `P["nombre_color"]`.

**Paleta clave:**
| Variable | Color | Uso |
|----------|-------|-----|
| `P["accent"]` | `#57C7B5` | Botones principales |
| `P["bg_app"]` | `#111418` | Fondo general |
| `P["bg_card"]`| `#1C2228` | Cards/paneles |
| `P["turno"]` | `#991B1B` | Celdas de turno asignado |
| `P["da"]` | `#B45309` | Excepción DA |
| `P["fl"]` | `#5B21B6` | Excepción FL |

**3 pestañas:**
- `tab_plan` → `_build_tab_plan()`: sidebar + tabla de semanas + gestión de excepciones
- `tab_vista` → `_build_tab_vista()`: vista calendario mensual
- `tab_ajustes` → `_build_tab_ajustes()`: gestión de personal y configuración

**Helper functions en gui.py:**
- `_section_header(parent, text, row)` → encabezado de sección con línea decorativa
- `_avatar_ctk(parent, initials, color, size)` → avatar circular con iniciales
- `_short_name(full, words)` → nombre corto descriptivo para tarjetas y reportes
- `_initials(full)` → 2 letras de iniciales para avatares visuales
- `_make_row_hover(ref_widget, row_widgets)` → hover con debounce para evitar parpadeo

---

## 7. `ExcelHandler` — Lógica del reporte

1. Construye en memoria la plantilla base con la grilla de 31 días y el personal (incluyendo funcionarios históricos con turnos o excepciones en el periodo)
2. Combina y centra el título principal en el rango `A1:AF1` (`PLANIFICACIÓN DE TURNOS — [MES] [AÑO]`)
3. **Auto-detecta** la fila de días buscando la fila con valores 1, 2, 3...
4. Limpia toda la grilla, pinta fines de semana en gris `#D9D9D9`
5. Por cada turno: pinta en **rojo** (`#FF3B30`) todos los días de esa semana que pertenezcan al mes
6. Por cada excepción: sobreescribe la celda con el tipo (`DA`, `FL`, `LIC`, `OTR` o `FOR`) y el color correspondiente
7. Al pie de la tabla, genera un bloque de **Leyenda de Convenciones** con muestras de color y nombres descriptivos (Turno, DA, FL, LIC, OTR, FOR, Fin de semana)

---

## 8. Convenciones de nombres del personal

Los nombres siguen el formato estándar: `APELLIDO NOMBRE` o `NOMBRE APELLIDO`.
El sistema extrae las iniciales para los avatares e indicadores visuales a partir de las primeras letras de las palabras del nombre.

---

## 9. Guardado seguro de `config.json`

`save_config()` usa escritura atómica para evitar corrupción:
```python
# Escribe en .tmp → fsync → os.replace() (atómico en Windows)
```
Si el proceso muere a mitad, el `.tmp` queda y el original no se toca.

---

## 10. Build y distribución

```bash
# Compilar a .exe (one-file, sin consola, con assets)
pyinstaller "Sistema de Turnos.spec"
```

El `.spec` incluye la carpeta `assets/` y el módulo `holidays.countries.chile`, y produce un ejecutable único.

**Dependencias principales:**
- `customtkinter` — GUI moderna dark mode
- `openpyxl` — creación/escritura de Excel
- `holidays` — calendario de feriados nacionales de Chile
- `Pillow` — carga de íconos PNG
- `pyinstaller` — compilación (solo dev)


---

## 11. Archivos importantes a no modificar sin cuidado

| Archivo | Riesgo |
|---------|--------|
| `config.json` | Único almacén de estado. Modificar a mano puede romper la rotación. Usar `reset_historial.py` para limpiar. |
| `utils/excel_handler.py` | Contiene la estructura base del reporte Excel. Cambiarla puede afectar la detección de filas y días. |
| `self.inicio` en config | Semanas inmutables ya pasadas. No borrar. |

---

## 12. Bugs conocidos y fixes aplicados

- **ITER 1:** CTkTabview usa `command=` en lugar de sobreescribir `segmented_button`. Auto-fade de mensajes de estado.
- **ITER 2:** Normalización de keys de snapshots a formato `YYYY-MM` con cero (ej: `2026-09` no `2026-9`).
- **ITER 3:** Confirmación al cerrar ventana con `WM_DELETE_WINDOW`.
- **BUG FIX rotación:** Cuando una semana histórica tiene excepción, se agrega al pendiente Y se avanza el puntero histórico para no desincronizar la cola.

---

## 13. Mejores prácticas para trabajar en este proyecto

### Al modificar la lógica de rotación:
- Siempre trabajar en `ShiftManager.generate_shifts` — es el núcleo
- Las funciones son **puras** (reciben `state` como argumento), no modifican `self` excepto `advance_month`
- Después de cualquier cambio, verificar que meses pasados en `historial` no se recalculen

### Al modificar la GUI:
- Usar siempre colores del diccionario `P`, nunca hardcodear hex
- Nuevos widgets deben usar `fg_color=P["bg_card"]` o similar
### Al tocar `config.json`:
- Nunca leer/escribir directamente fuera de `ShiftManager`
- Si se agrega un campo nuevo, agregarlo también en `save_config()` Y en `load_config()`

### Para agregar una nueva persona al personal:
- Agregar en `config.json["personal"]` con `id` único incremental
- El `id` debe ser único y nunca reutilizarse (los `pendientes` usan IDs)

### Para debug:
- Usar `reset_historial.py` para limpiar historial y volver a estado inicial
- El `.exe` busca `config.json` relativo al directorio del ejecutable

