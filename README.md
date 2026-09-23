# 🗓️ Sistema de Gestión de Turnos de Guardia

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)
![UI Framework](https://img.shields.io/badge/GUI-CustomTkinter%20(Dark%20Mode)-16877D)
![Reports](https://img.shields.io/badge/reports-OpenPyXL%20(Excel)-217346?logo=microsoftexcel&logoColor=white)
![Notifications](https://img.shields.io/badge/notifications-Google%20Apps%20Script%20(Serverless)-EA4335?logo=google&logoColor=white)
![Tests](https://img.shields.io/badge/tests-78%20passing-brightgreen?logo=pytest&logoColor=white)
![Distribution](https://img.shields.io/badge/dist-PyInstaller%20Standalone%20.exe-orange)

**Aplicación de escritorio moderna, robusta y automatizada para la planificación, asignación rotativa semanal, gestión de excepciones y notificación institucional de turnos de guardia.**

[Características](#-características-principales) •
[Arquitectura](#-arquitectura-del-sistema) •
[Instalación y Uso](#-instalación-y-uso-rápido) •
[Notificaciones Serverless](#-notificaciones-por-correo-google-apps-script) •
[Flujo Operativo](#-flujo-de-trabajo-operativo-recomendado) •
[Documentación](#-documentación-oficial-del-proyecto)

</div>

---

## 📌 Descripción General

El **Sistema de Gestión de Turnos** es una solución informática de escritorio diseñada específicamente para resolver la complejidad operativa en la distribución de turnos de guardia semanales en equipos de funcionarios o personal técnico/operativo (diseñado para dotaciones de 16 personas o escalable a cualquier número).

Tradicionalmente, la confección manual de calendarios en planillas de cálculo dispersas genera errores humanos frecuentes: funcionarios que repiten guardias consecutivas tras recuperar permisos, asignación injusta en feriados patrios o festivos de fin de año, pérdida del historial de rotación al cerrar meses fuera de orden, y falta de comunicación oportuna cuando se aprueban cambios o permutas de última hora.

Este sistema soluciona dichos problemas combinando un **motor algorítmico determinista con reglas de equidad**, una **interfaz gráfica moderna en modo oscuro**, **exportación de informes oficiales en Excel** y un **mecanismo serverless de notificación por correo electrónico** sin costo operativo.

---

## ✨ Características Principales

### 🔄 1. Motor de Rotación Algorítmica Inteligente
- **Cola Circular Continua:** Asigna las semanas de guardia siguiendo estrictamente el orden del personal (`siguiente_id`), garantizando que todos cumplan su cuota proporcional de servicio.
- **Cola de Recuperación de Pendientes (`pendientes`):** Si un funcionario no puede cumplir su turno programado por encontrarse con permiso o licencia médica, se salta automáticamente y se registra en la lista de pendientes para recuperar su turno apenas se encuentre disponible.
- **Regla de Enfriamiento y Espaciado (`min_gap_weeks = 4`):** El algoritmo impide que un funcionario reciba dos turnos en un intervalo menor a 4 semanas (incluso al recuperar turnos pendientes o tras asignaciones forzadas), evitando sobrecargas laborales y fatiga.
- **Regla Anual de Feriados Chilenos (`holidays.countries.chile`):** Consulta el historial del año anterior para evitar que una persona repita la guardia en el mismo feriado nacional (Fiestas Patrias, Navidad, Año Nuevo, etc.) en años consecutivos. Compara los feriados por nombre normalizado, adaptándose a feriados móviles.
- **Asignaciones Manuales con Motivo Obligatorio:** Permite forzar o permutar la guardia de cualquier semana directamente desde la interfaz, exigiendo un motivo justificativo registrado para auditoría y aviso al equipo.

### 🖥️ 2. Interfaz Gráfica Ergonómica (CustomTkinter Dark Mode)
- **Diseño Ergonómico Moderno:** Paleta de colores de alto contraste inspirada en suites profesionales (`#111418`, `#1C2228`, `#57C7B5`).
- **Pestaña 📋 Planificación:**
  - Selector ágil de mes y año con previsualización en tiempo real.
  - Indicador dinámico que calcula y muestra la fecha del próximo turno proyectado para el funcionario seleccionado.
  - Ingreso flexible de excepciones por rangos o listas (ej: `1-5, 12, 20-25`).
  - Tarjetas semanales interactivas con detalle de fechas, funcionario asignado, estado (automático, forzado o manual) y diálogo modal para reasignaciones.
  - Detección de cambios sin guardar mediante indicador visual en el título (`● Sistema de Turnos`) y confirmación de seguridad al salir.
- **Pestaña 📅 Ver Turnos del Mes:**
  - Vista de calendario mensual en cuadrícula con celdas coloreadas según el estado de cada día (Turno, DA, FL, LIC, OTR, Fin de semana y Día actual).
  - Navegación temporal instantánea (mes anterior, mes siguiente, botón "Hoy").
  - Botón directo para exportar el reporte oficial en Excel (`📊 Exportar Excel`).
- **Pestaña ⚙️ Ajustes:**
  - Configuración y ajuste manual del funcionario de inicio de la rotación.
  - **Gestión completa de personal (CRUD):** Agregar funcionario con correo, editar datos, eliminar preservando el historial y reordenar la rotación mediante botones `⬆` y `⬇`.
  - Panel de control del Webhook de correo con botón interactivo de prueba de envío.
  - Herramientas de mantenimiento y reinicio controlado de historial.

### 📊 3. Generación Oficial de Reportes Excel (.xlsx)
- Construido mediante `openpyxl` directamente en memoria, sin requerir plantillas externas.
- **Matriz Mensual de 31 Días:** Cuadrícula completa con nombres de funcionarios, días numéricos y letras de días de la semana (`L, M, X, J, V, S, D`).
- **Identificación Visual:** Días de guardia en rojo institucional (`#FF3B30`), fines de semana en gris tenue (`#D9D9D9`) y días inválidos bloqueados (ej: 29-31 en febrero o 31 en meses de 30 días).
- **Columnas de Totales Acumulados:** Métricas por funcionario al costado derecho: cantidad total de `TURNOS`, `DA`, `FL`, `LIC` y `OTR`.
- **Bloque de Convenciones y Leyenda:** Muestras de color y descripciones formales al pie de la tabla.
- **Configuración de Impresión:** Orientación horizontal (Landscape Carta) autoajustada exactamente a 1 página de ancho (`fitToWidth = 1`).
- **Respeto Histórico:** Incluye en el reporte a funcionarios que hayan tenido turnos o excepciones en ese periodo, aunque hayan sido dados de baja del personal activo posteriormente.

### 📧 4. Notificaciones Serverless por Correo Electrónico
- **Cero Costo y Máxima Privacidad:** Implementado mediante Google Apps Script (`scripts/google_apps_script.js`), utilizando la infraestructura de Gmail sin almacenar credenciales en la máquina local.
- **Envío Automatizado:** Al guardar un mes que contenga asignaciones manuales o permutas, el sistema despacha una notificación por correo a todo el equipo.
- **Pre-validaciones de Seguridad:**
  1. Comprueba conexión activa a Internet antes de proceder.
  2. Verifica que el 100% de los funcionarios activos tengan un correo válido registrado.
  3. Ejecuta el envío en un hilo en segundo plano (`threading.Thread`) para evitar bloqueos en la interfaz.
- **Formato Claro y Estructurado:** Detalla la semana modificada, el funcionario que estaba originalmente programado, el nuevo funcionario asignado, el motivo del cambio y la marca temporal de registro.

### 🛡️ 5. Resiliencia de Datos y Tolerancia a Fallos
- **Escritura Atómica de Configuración:** Las modificaciones a `config.json` se escriben primero en un archivo temporal (`config.json.tmp`), se sincronizan a disco con `os.fsync()` y se reemplazan atómicamente con `os.replace()`, evitando la corrupción de datos ante cortes eléctricos o cierres forzados.
- **Respaldos Automáticos Fechados:** Antes de cada avance de mes o cambio crítico, se genera una copia de seguridad en la carpeta `backups/` (`config_YYYYMMDD_HHMMSS_pre_advance.json`). Mantiene automáticamente los últimos 20 respaldos.
- **Recuperación ante Archivos Corruptos:** Si `config.json` se daña por causas externas, el sistema lo aísla en `backups/*.corrupted_<timestamp>` e inicializa un estado seguro sin interrumpir la ejecución.
- **Registro Centralizado de Eventos (`turnos.log`):** Logger con rotación de archivos para diagnóstico y trazabilidad de operaciones.

---

## 🏛️ Arquitectura del Sistema

El proyecto sigue una arquitectura **MVC (Modelo - Vista - Controlador)** desacoplada y modular:

```mermaid
flowchart TD
    subgraph Entrada
        MAIN[main.py\nEntrypoint & Exception Hook]
    end

    subgraph Controlador
        CTRL[controllers/main_controller.py\nOrquestador de Negocio y Flujos]
    end

    subgraph Modelo
        MODEL[models/shift_manager.py\nLógica de Rotación, Snapshots y Backups]
        CONF[(config.json\nEstado Persistente)]
        BACKUPS[(backups/\nCopias Fechadas)]
    end

    subgraph Vista
        GUI[views/gui.py\nVentana Principal TurnosApp]
        PLAN[views/tabs/tab_plan.py\nPlanificación y Semanas]
        CAL[views/tabs/tab_calendar.py\nCalendario Mensual]
        SETT[views/tabs/tab_settings.py\nAjustes y Personal]
        THEME[views/theme.py\nTokens de Diseño]
    end

    subgraph Utilidades
        EXCEL[utils/excel_handler.py\nMotor de Reportes OpenPyXL]
        NOTIF[utils/email_notifier.py\nWebhook & Redirecciones 302]
        HOLIDAYS[utils/chilean_holidays.py\nFeriados de Chile]
        LOG[utils/logger.py\nLogging Rotativo]
        ENV[utils/env_helper.py\nGestión de .env]
    end

    subgraph Nube Serverless
        GAS[Google Apps Script\nWebhook Gmail]
    end

    MAIN --> CTRL
    MAIN --> GUI
    CTRL --> MODEL
    CTRL --> EXCEL
    MODEL --> CONF
    MODEL --> BACKUPS
    MODEL --> HOLIDAYS
    GUI --> PLAN
    GUI --> CAL
    GUI --> SETT
    PLAN --> CTRL
    CAL --> CTRL
    SETT --> CTRL
    GUI -.->|Envío en segundo plano| NOTIF
    NOTIF --> GAS
```

### Componentes y Responsabilidades

| Módulo / Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. Detecta si corre como binario `.exe` o script `.py`, carga variables `.env`, configura el capturador global de errores (`sys.excepthook`) y lanza la GUI. |
| `controllers/main_controller.py` | Media entre la vista y el modelo. Resuelve cadenas temporales de meses futuros, prepara listas de personal activo e histórico para exportación y valida reglas de negocio. |
| `models/shift_manager.py` | Núcleo del sistema: algoritmo de rotación circular, cola de pendientes, reglas de feriados chilenos, cálculo de gap mínimo (4 semanas), snapshots mensuales y guardado atómico. |
| `views/gui.py` | Coordinador principal de la ventana CustomTkinter. Gestiona hilos en segundo plano, control de cambios sucios (indicador ●) y orquesta el cierre de mes con notificaciones. |
| `views/tabs/tab_plan.py` | Vista de planificación: selector de periodo, formulario de excepciones, tarjetas interactivas semanales y botón "Guardar mes". |
| `views/tabs/tab_calendar.py` | Vista visual de calendario en cuadrícula con chips de color y botón para exportar a Excel. |
| `views/tabs/tab_settings.py` | Panel de ajustes: punto de inicio, CRUD de personal con reordenamiento, configuración del Webhook de correos y prueba interactiva. |
| `utils/excel_handler.py` | Generador de plantillas y planillas Excel (.xlsx) con estilos, fórmulas de resumen, leyendas y formato de impresión. |
| `utils/email_notifier.py` | Validador de conexión a Internet, formateador de mensajes y cliente HTTP POST compatible con redirecciones 302 de Google Apps Script. |
| `utils/chilean_holidays.py` | Interfaz con la librería `holidays` para Chile y normalización de nombres de días festivos. |
| `utils/logger.py` | Sistema de logging rotativo que escribe en consola y en `turnos.log`. |
| `scripts/google_apps_script.js` | Código fuente listo para desplegar en Google Apps Script para actuar como webhook receptor y emisor de correos vía Gmail. |

---

## 🏷️ Convenciones de Excepciones y Personal

### Tipos de Excepción Admitidos

| Sigla | Nombre | Color Visual | Descripción |
|:---:|---|:---:|---|
| **`DA`** | Día Administrativo | Naranja (`#B45309`) | Permiso administrativo legalmente concedido. |
| **`FL`** | Feriado Legal | Violeta (`#5B21B6`) | Periodo de vacaciones o descanso reglamentario. |
| **`LIC`** | Licencia Médica | Turquesa (`#0E7490`) | Reposo por prescripción de salud. |
| **`OTR`** | Otro Permiso | Gris Azulado (`#374151`) | Comisión de servicio, duelo, capacitación, etc. |
| **`FOR`** | Asignación Forzada | Verde Esmeralda (`#059669`) | Reemplazo o asignación manual directa en la semana. |

### Convenciones de Nombres del Personal
Los nombres de los funcionarios se registran bajo el formato estandarizado:
```
[RANGO] [(SUFIJO)] [APELLIDO1] [APELLIDO2] [NOMBRES]
```
Prefijos reconocidos y omitidos automáticamente en tarjetas reducidas y avatares:
- `COM`: Comisario
- `SBC`: Subcomisario
- `PRO`: Profesional
- `(A)`: Administrativo
- `(F)`: Femenino

---

## 🚀 Instalación y Uso Rápido

### Modo 1: Usuario Final (Ejecutable `.exe` Standalone)

No requiere tener Python instalado. Compatible con **Windows 10** y **Windows 11**.

1. Descarga la versión compilada `Sistema de Turnos.exe`.
2. Asegúrate de tener en la misma carpeta:
   - `Sistema de Turnos.exe`
   - `config.json` (base de datos con la lista inicial de personal)
   - `.env` (opcional, para la URL del webhook de correos)
3. Haz doble clic en `Sistema de Turnos.exe`.
4. Los archivos Excel generados (`turnos_<Mes>_<Año>.xlsx`) y los respaldos (`backups/`) se guardarán automáticamente en esa misma carpeta.

---

### Modo 2: Desarrollador (Ejecución desde Código Fuente)

#### Requisitos Previos:
- Python 3.10 o superior instalado en el sistema.
- PowerShell o terminal de comandos en Windows.

#### Paso a paso:

1. **Clonar el repositorio:**
   ```powershell
   git clone https://github.com/MartinLopez1011/Sistema-de-turnos.git
   cd "Sistema de turnos"
   ```

2. **Crear y activar el entorno virtual:**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Instalar dependencias del proyecto:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno (opcional):**
   ```powershell
   Copy-Item .env.example .env
   ```

5. **Iniciar la aplicación:**
   ```powershell
   python main.py
   ```

---

## 📧 Notificaciones por Correo (Google Apps Script)

El sistema incluye una integración lista para usar con **Google Apps Script**, permitiendo enviar correos institucionales de notificación de forma 100% gratuita y sin servidores adicionales.

### Despliegue en 3 minutos:

1. Ingresa a [Google Apps Script](https://script.google.com/) con la cuenta de Gmail o Google Workspace que enviará los correos.
2. Haz clic en **"Nuevo proyecto"** y nómbralo `Webhook Sistema Turnos`.
3. Abre el archivo [`scripts/google_apps_script.js`](./scripts/google_apps_script.js) de este repositorio, copia todo su contenido y pégalo en el editor de Apps Script (reemplazando cualquier código existente).
4. Haz clic en el botón azul superior **"Implementar" > "Nueva implementación"**:
   - Tipo: **Aplicación web**.
   - Descripción: `Notificaciones Sistema de Turnos`.
   - Ejecutar como: **Yo (tu cuenta de correo)**.
   - Quién tiene acceso: **Cualquier persona** *(imprescindible para que la app de escritorio pueda comunicarse vía HTTP POST)*.
5. Haz clic en **Implementar**, concede los permisos solicitados y copia la **URL de la aplicación web** (terminada en `/exec`).
6. En la aplicación de escritorio, ve a la pestaña **Ajustes > Notificaciones por Correo**, pega la URL y realiza una prueba con el botón **"✉ Probar Envío"**.

> [!NOTE]
> La URL del webhook se guarda automáticamente en `config.json` y se sincroniza con el archivo `.env` local (`WEBHOOK_URL`).

---

## 📋 Flujo de Trabajo Operativo Recomendado

Para garantizar la integridad del historial y la equidad en los turnos, sigue este ciclo mensual de trabajo:

```mermaid
sequenceDiagram
    autonumber
    actor Sup as Encargado / Supervisor
    participant UI as Sistema de Turnos (GUI)
    participant XL as ExcelHandler
    participant GAS as Webhook Google
    participant DB as config.json

    Sup->>UI: Selecciona Mes y Año en "Planificación"
    Sup->>UI: Registra Excepciones (DA, FL, LIC, OTR)
    UI-->>UI: Recalcula previsualización instantánea
    opt Asignación Manual / Permuta
        Sup->>UI: Clic en "Cambiar Guardia" e ingresa funcionario y motivo
        UI-->>UI: Marca semana con asignación forzada
    end
    Sup->>UI: Abre pestaña "Ver Turnos del Mes" y revisa calendario
    Sup->>XL: Clic en "📊 Exportar Excel"
    XL-->>Sup: Genera y guarda turnos_Mes_Año.xlsx
    Note over Sup,UI: El mes está validado y aprobado
    Sup->>UI: Vuelve a "Planificación" y presiona "💾 Guardar mes"
    alt Hubo asignaciones manuales
        UI->>UI: Valida conexión a Internet y correos del 100%
        UI->>GAS: Despacha notificación por correo al equipo
        GAS-->>UI: Confirmación de envío OK
    end
    UI->>DB: Guarda en historial, genera snapshot del mes siguiente y avanza cola
    UI-->>Sup: Notifica éxito y pasa al siguiente mes
```

> [!IMPORTANT]
> **Diferencia Crítica:**
> - **📊 Exportar Excel:** Es una operación de solo lectura. Permite generar la planilla oficial tantas veces como sea necesario para revisión sin alterar la cola ni guardar cambios permanentes.
> - **💾 Guardar mes:** Es la operación de cierre definitivo. Registra las semanas en el historial oficial, crea el snapshot del mes siguiente, dispara los avisos por correo si hubo cambios manuales y avanza la rotación.

---

## 🛠️ Compilación a Ejecutable Standalone (.exe)

Para compilar la aplicación en un único archivo ejecutable `.exe` independiente que incluya todos los recursos (íconos, estilos y feriados):

```powershell
.\.venv\Scripts\python.exe -m PyInstaller "Sistema de Turnos.spec"
```

El ejecutable resultante se creará en el directorio `dist/Sistema de Turnos.exe`.

### Especificaciones de Compilación (`Sistema de Turnos.spec`):
- **Modo:** One-file (`pyz` empaquetado en un único ejecutable).
- **Consola:** Desactivada (`console=False`), ejecución silenciosa nativa de Windows.
- **Recursos incluidos:** Carpeta `assets/` (íconos PNG).
- **Módulos ocultos:** `holidays.countries.chile` para garantizar el cálculo de feriados nacionales en entornos congelados.

---

## 🧪 Pruebas Automatizadas (Testing)

El proyecto cuenta con una batería de **78 pruebas unitarias y de integración** automatizadas desarrolladas con `pytest` y `pytest-mock`, cubriendo:
- Rotación pura y ciclo circular.
- Asignación de pendientes y reglas de espaciado (gap de 4 semanas).
- Restricciones anuales de feriados patrios y festivos de diciembre.
- Asignaciones manuales, reversiones y motivos obligatorios.
- Resiliencia y atomicidad en `config.json`, creación y rotación de backups.
- Validación y paridad de exportación a Excel (.xlsx).
- Webhook de notificación por correo, reintentos y redirecciones 302.
- CRUD de funcionarios y preservación de registros históricos.

Para ejecutar todas las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Resultado esperado:
```text
============================= 78 passed in ~1.6s =============================
```

---

## 📁 Estructura del Repositorio

```text
Sistema de turnos/
├── assets/                          # Recursos gráficos (íconos PNG de estado)
│   ├── error.png
│   ├── save.png
│   └── success.png
├── backups/                         # Copias de seguridad automáticas fechadas de config.json
├── controllers/                     # Capa de control (MVC)
│   └── main_controller.py          # Coordinador entre GUI, ShiftManager y ExcelHandler
├── models/                          # Capa de datos y lógica de negocio (MVC)
│   └── shift_manager.py             # Motor algorítmico, rotación, backups y atomicidad
├── views/                           # Capa de presentación gráfica (MVC)
│   ├── components/                  # Componentes reutilizables y modales
│   │   ├── dialogs.py               # Diálogos modales personalizados (Formularios, Cambios)
│   │   └── widgets.py               # Avatares, encabezados y efectos hover
│   ├── tabs/                        # Módulos de pestañas de la interfaz
│   │   ├── tab_calendar.py          # Pestaña "Ver Turnos del Mes" (Calendario visual)
│   │   ├── tab_plan.py              # Pestaña "Planificación" (Semanas, excepciones)
│   │   └── tab_settings.py          # Pestaña "Ajustes" (Personal, Webhook, inicio)
│   ├── gui.py                       # Ventana principal TurnosApp y orquestador UI
│   └── theme.py                     # Tokens de diseño, paleta Dark Mode y constantes
├── utils/                           # Utilidades y servicios auxiliares
│   ├── chilean_holidays.py          # Integración con feriados nacionales de Chile
│   ├── email_notifier.py            # Despachador de notificaciones y cliente Webhook
│   ├── env_helper.py                # Carga y sincronización de variables .env
│   ├── excel_handler.py             # Generador de reportes Excel openpyxl
│   └── logger.py                    # Logger rotativo en consola y archivo turnos.log
├── scripts/                         # Scripts de backend y soporte
│   └── google_apps_script.js        # Webhook serverless para Google Apps Script
├── tests/                           # Suite de 78 pruebas automatizadas con pytest
├── .env.example                     # Plantilla de variables de entorno
├── config.json                      # Estado actual de personal, historial y rotación
├── main.py                          # Punto de entrada de la aplicación
├── requirements.txt                 # Dependencias Python requeridas
├── Sistema de Turnos.spec           # Archivo de especificación para PyInstaller
└── README.md                        # Documentación principal del repositorio
```

---

## 📚 Documentación Oficial del Proyecto

Encuentra los manuales y documentos técnicos generados en la raíz del proyecto:

- 📄 **[Manual de Usuario Oficial (PDF)](./Manual_de_Usuario_Sistema_de_Turnos.pdf):** Manual interactivo a todo color con capturas, instrucciones detalladas de uso, paso a paso para funcionarios y supervisores.
- 📝 **[Requerimientos y Alcance del Sistema (Word)](./Requerimientos_del_Sistema_Turnos.docx):** Especificación funcional formal con requerimientos funcionales (RF), no funcionales (RNF) y matriz de alcance.
- 📊 **[Documento Ejecutivo del Proyecto (Word)](./Sistema_de_Gestion_de_Turnos.docx):** Informe ejecutivo con diagramas editables, análisis de retorno operativo y propuesta de valor institucional.

---

## 📄 Licencia y Créditos

Desarrollado para optimizar la gestión operativa de turnos de guardia.  
Código abierto bajo los términos establecidos en la organización institucional.
