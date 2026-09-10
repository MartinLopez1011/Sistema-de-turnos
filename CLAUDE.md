# Sistema de Turnos — Resumen de Proyecto para IA

> **Propósito de este archivo:** Proveer contexto suficiente al asistente de IA para trabajar sin necesidad de leer cada archivo en detalle. Leé esto antes de cualquier otra cosa.

---

## 1. ¿Qué es este proyecto?

Aplicación de escritorio en **Python** que gestiona la asignación rotativa semanal de turnos de guardia para un equipo de 16 personas. Genera reportes Excel y tiene una GUI moderna.

- **Tecnología principal:** Python + CustomTkinter (GUI dark mode)
- **Distribución:** Compilado con PyInstaller → `Sistema de Turnos.exe` (standalone, sin instalar Python)
- **Persistencia:** Un único archivo `config.json` en el directorio del ejecutable
- **Output:** Archivos `turnos_<Mes>_<Año>.xlsx` generados con `openpyxl` y el documento ejecutivo `Sistema_de_Gestion_de_Turnos.docx`

---

## 2. Arquitectura (MVC simple)

```
main.py                    ← Entrypoint. Detecta si es .exe o script y resuelve root_path
controllers/
  main_controller.py       ← Orquesta modelo y vista. Sin lógica de negocio.
models/
  shift_manager.py         ← TODA la lógica de negocio (rotación, snapshots, excepciones)
views/
  gui.py                   ← GUI con CustomTkinter (~1400 líneas). TurnosApp(ctk.CTk)
utils/
  excel_handler.py         ← Construye la plantilla Excel en memoria, escribe turnos y guarda reporte
assets/                    ← Íconos PNG (success, error, save)
config.json                ← Base de datos en JSON (ver sección 4)
generar_documento.py      ← Genera el documento ejecutivo editable en Word
Sistema_de_Gestion_de_Turnos.docx ← Documento ejecutivo generado del proyecto
```

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
  "personal": [{"id": 1, "nombre": "COM APELLIDO NOMBRE"}],   // Lista ordenada de 16 personas
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
  }
}
```

**Tipos de excepción soportados:**
- `DA` = Día Administrativo (color naranja `#B45309`)
- `FL` = Feriado Legal (color violeta `#5B21B6`)
- `LIC` = Licencia (color turquesa `#0E7490`)
- `OTR` = Otro (color gris `#374151`)

---

## 5. Lógica de rotación (`ShiftManager.generate_shifts`)

El algoritmo recorre cada semana del mes calendario y:

1. Si la semana está en `self.inicio` → asigna fijo, continúa (no modifica puntero)
2. Si la semana está en `self.historial` → respeta lo guardado, SALVO que el asignado tenga excepción en esa semana (en ese caso recalcula)
3. Si hay **pendientes** → intenta asignar al primero de la lista que NO tenga excepción
4. Si no hay pendientes libres → sigue la **lista circular** desde `siguiente_id`
5. Si alguien es saltado (tiene excepción) → se agrega a `pendientes` para recuperar turno después

La previsualización de un mes futuro sin snapshot encadena temporalmente los meses desde el estado actual para no reiniciar la rotación. Un mes cerrado puede recalcularse si cambian sus excepciones.

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
- `_short_name(full, words)` → nombre corto omitiendo prefijos (COM, PRO, SBC, (A), (F))
- `_initials(full)` → 2 letras de iniciales omitiendo prefijos
- `_make_row_hover(ref_widget, row_widgets)` → hover con debounce para evitar parpadeo

---

## 7. `ExcelHandler` — Lógica del reporte

1. Construye en memoria la plantilla base con la grilla de 31 días y las personas configuradas
2. **Auto-detecta** la fila de días buscando la fila con valores 1, 2, 3...
3. Limpia toda la grilla, pinta fines de semana en gris `#D9D9D9`
4. Por cada turno: pinta en **rojo** (`#FF3B30`) todos los días de esa semana que pertenezcan al mes
5. Por cada excepción: sobreescribe la celda con el tipo (`DA`, `FL`, `LIC` u `OTR`) y el color correspondiente

---

## 8. Convenciones de nombres del personal

Los nombres siguen el formato: `RANGO (SUFIJO) APELLIDO1 APELLIDO2 NOMBRE`

Prefijos/rangos conocidos que se omiten al mostrar nombres cortos:
- `COM` = Comisario
- `PRO` = Profesional
- `SBC` = Sub-comisario
- `(A)` = Administrativo
- `(F)` = Femenino

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

El `.spec` incluye la carpeta `assets/` y produce un ejecutable único.

**Dependencias principales:**
- `customtkinter` — GUI moderna dark mode
- `openpyxl` — creación/escritura de Excel
- `Pillow` — carga de íconos PNG
- `python-docx` — generación del documento ejecutivo editable
- `pyinstaller` — compilación (solo dev)

El generador del Word se ejecuta desde el entorno virtual del proyecto:
```bash
.venv\Scripts\python.exe generar_documento.py
```

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
- El hover de filas usa `_make_row_hover()` — aplicar en cualquier lista nueva

### Al tocar `config.json`:
- Nunca leer/escribir directamente fuera de `ShiftManager`
- Si se agrega un campo nuevo, agregarlo también en `save_config()` Y en `load_config()`

### Para agregar una nueva persona al personal:
- Agregar en `config.json["personal"]` con `id` único incremental
- El `id` debe ser único y nunca reutilizarse (los `pendientes` usan IDs)

### Para debug:
- Usar `reset_historial.py` para limpiar historial y volver a estado inicial
- El `.exe` busca `config.json` relativo al directorio del ejecutable

---

## 14. Estado actual (Septiembre 2026)

- Personal: 16 personas activas (IDs 1–16)
- Siguiente en turnar: ID 1 (COM MARFULL VILLANUEVA SCARLETT)
- Historial: semanas desde el 7 de septiembre hasta el 4 de octubre de 2026
- Snapshots: datos de inicio disponibles para septiembre y octubre de 2026
- Excepciones guardadas: periodo septiembre de 2026 sin excepciones registradas

> Este estado refleja `config.json` al 10 de septiembre de 2026. Si el archivo cambia, debe considerarse la fuente de verdad para el estado operativo.

---

## 15. Documento ejecutivo del proyecto

El archivo `Sistema_de_Gestion_de_Turnos.docx` resume el problema, los objetivos, el alcance, los requerimientos, la arquitectura MVC, el flujo mensual, las entradas y salidas y los beneficios esperados. Está dirigido a una persona ejecutiva y contiene tablas y diagramas editables de Word.

Para regenerarlo después de modificar la implementación o `config.json`:
```bash
.venv\Scripts\python.exe generar_documento.py
```

El documento toma el código y la configuración actuales como fuente de verdad. No debe confundirse con una especificación de funcionalidades futuras: exportar Excel y cerrar el mes siguen siendo operaciones separadas, y la exportación no modifica la cola de rotación.
