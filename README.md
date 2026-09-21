# Sistema de Turnos

Aplicación de escritorio para planificar y administrar la asignación rotativa semanal de turnos de guardia. Está pensada para equipos que necesitan conservar el historial, gestionar excepciones y generar un calendario mensual en Excel.

## Funcionalidades

- Asignación rotativa semanal de turnos.
- Previsualización de un mes antes de guardarlo.
- Gestión de excepciones por persona, día y tipo:
  - `DA`: Día Administrativo.
  - `FL`: Feriado Legal.
  - `LIC`: Licencia.
  - `OTR`: Otro.
  - `FOR`: Asignación forzada, cuando corresponda.
- Vista calendario mensual con turnos, excepciones y fines de semana.
- Exportación de calendarios a archivos Excel.
- Historial de meses cerrados y continuidad de la cola de rotación.
- Gestión del personal, orden de rotación y persona inicial.

## Uso rápido

### Versión ejecutable

1. Coloca `Sistema de Turnos.exe` junto con `config.json`.
2. Ejecuta el archivo `.exe`.
3. Consulta el [Manual de usuario](./MANUAL_USUARIO.md) para el flujo completo.

La aplicación guarda `config.json` y los archivos `turnos_<Mes>_<Año>.xlsx` en la misma carpeta del ejecutable.

### Ejecución desde el código fuente

Requiere Python instalado. Desde PowerShell, en la carpeta del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Si no existe el entorno virtual `.venv`, créalo antes:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

## Flujo recomendado de trabajo

1. En **Planificación**, selecciona el mes y el año.
2. Agrega las excepciones necesarias.
3. Revisa la vista previa de las semanas.
4. En **Ajustes > Exportar Calendario**, genera el archivo Excel.
5. Cuando el mes esté revisado y terminado, vuelve a **Planificación** y pulsa **Guardar mes**.

> **Importante:** exportar a Excel y guardar/cerrar el mes son operaciones distintas. Exportar no avanza la cola ni modifica el historial. Guardar el mes sí lo registra en el historial y avanza la rotación al siguiente mes.

## Archivos principales

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada de la aplicación. |
| `models/shift_manager.py` | Lógica de rotación, excepciones, historial y snapshots. |
| `views/gui.py` | Interfaz gráfica. |
| `utils/excel_handler.py` | Generación del reporte Excel. |
| `config.json` | Estado persistente de personal, historial y rotación. |
| `MANUAL_USUARIO.md` | Instrucciones para usuarios finales. |
| `Sistema de Turnos.spec` | Configuración de PyInstaller. |

## Desarrollo y compilación

Para generar el ejecutable:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller "Sistema de Turnos.spec"
```

El ejecutable se crea en la carpeta `dist`.

Para ejecutar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Documentación adicional

- [Manual de usuario](./MANUAL_USUARIO.md)
- [Documento ejecutivo](./Sistema_de_Gestion_de_Turnos.docx)
