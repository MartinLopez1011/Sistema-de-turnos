# Documento de Requerimientos de Software (ERS Simple)
## Sistema de Gestión de Turnos de Guardia

---

### 1. Información General del Proyecto
- **Nombre del Sistema:** Sistema de Gestión de Turnos (TurnosApp)
- **Tipo de Aplicación:** Aplicación de Escritorio (Desktop) para Windows
- **Objetivo Principal:** Automatizar y ordenar la asignación semanal y rotativa de turnos de guardia para el equipo de trabajo, respetando la equidad, gestionando ausencias/excepciones, evitando la duplicación de guardias en feriados críticos y permitiendo la exportación a Excel.
- **Usuario Principal:** Coordinador / Responsable de la planificación de turnos.

---

### 2. Alcance del Sistema

#### Dentro del Alcance (Incluido):
- Planificación mensual con asignación rotativa semanal.
- Gestión de ausencias y excepciones por funcionario (Días Administrativos, Feriados Legales, Licencias Médicas, Otros).
- Ajustes y asignaciones manuales forzadas por semana.
- Previsualización no destructiva del calendario antes de confirmar.
- Cierre y consolidación mensual en un historial persistente.
- Vista de calendario interactiva mensual.
- Exportación del calendario formateado a archivo Excel (`.xlsx`).
- Administración de la nómina de personal y orden de la lista.
- Respaldos automáticos de datos.

#### Fuera del Alcance (No Incluido):
- Autenticación con contraseña o perfiles multiusuario.
- Concurrencia o edición simultánea en red multi-equipo.
- Base de datos cliente-servidor externa (SQL/Cloud).
- Sincronización web o envío automático de correos electrónicos.

---

### 3. Requerimientos Funcionales (RF)

| ID | Requerimiento | Descripción |
| :--- | :--- | :--- |
| **RF-01** | **Selección de Período** | El usuario puede seleccionar el mes y el año calendario a planificar o visualizar. |
| **RF-02** | **Rotación Automática Equitativa** | El sistema asigna turnos semanales de forma rotativa y circular respetando el orden de la lista del personal. |
| **RF-03** | **Gestión de Pendientes (Compensaciones)** | Si un funcionario es saltado por no disponibilidad (excepción), se le registra en una lista de pendientes para otorgarle turno en la siguiente semana libre. |
| **RF-04** | **Registro de Excepciones y Ausencias** | Permite registrar excepciones para una persona indicando día o rango de días y el tipo: <br>• `DA`: Día Administrativo<br>• `FL`: Feriado Legal<br>• `LIC`: Licencia Médica<br>• `OTR`: Otro motivo |
| **RF-05** | **Asignación Manual por Semana** | Permite al coordinador forzar la asignación de un funcionario específico en una semana particular, identificándose con la etiqueta `MANUAL` y con opción de volver a cálculo `Auto`. |
| **RF-06** | **Regla Anual de Feriados (Diciembre)** | En el mes de diciembre, el sistema evita asignar a una persona al mismo feriado nacional chileno (ej. Navidad o Año Nuevo) si ya lo cubrió en el diciembre anterior registrado. Si no hay otra opción disponible, asigna y emite una advertencia. |
| **RF-07** | **Previsualización de Turnos** | Permite simular y revisar las asignaciones del mes en curso o meses futuros sin alterar el puntero de rotación ni modificar el historial. |
| **RF-08** | **Cierre y Guardado de Mes** | Al confirmar el mes: <br>1. Las asignaciones se consolidan en el historial.<br>2. Se actualiza el puntero de rotación para el siguiente mes.<br>3. Se guardan *snapshots* de continuidad. |
| **RF-09** | **Vista de Calendario Mensual** | Visualización gráfica del mes con diferenciación por color: días con turno asignado, excepciones por funcionario y fines de semana. Incluye navegación rápida (Mes Anterior, Mes Siguiente, Hoy). |
| **RF-10** | **Exportación a Excel** | Genera un archivo `.xlsx` formal con formato visual profesional, cabecera institucional, cuadrícula de días y tabla de leyenda de colores. |
| **RF-11** | **Gestión de Personal** | Permite agregar nuevos funcionarios, modificar nombres, eliminar registros y ajustar el orden de rotación en la lista mediante flechas. |
| **RF-12** | **Ajustes de Inicio y Reinicio** | Permite definir qué persona encabeza la rotación y reiniciar el historial con confirmación y respaldo de seguridad. |

---

### 4. Requerimientos No Funcionales (RNF)

| ID | Categoría | Requerimiento / Condición |
| :--- | :--- | :--- |
| **RNF-01** | **Rendimiento** | El cálculo y previsualización de turnos debe ser instantáneo (< 1 segundo). La generación del reporte Excel debe tomar menos de 2 segundos. |
| **RNF-02** | **Usabilidad e Interfaz** | Interfaz gráfica moderna en Modo Oscuro (Dark Theme), avatares visuales, diálogos de confirmación para acciones críticas y avisos de éxito/error. |
| **RNF-03** | **Portabilidad y Distribución** | Empaquetado como ejecutable único para Windows (`Sistema de Turnos.exe`), ejecutable directamente sin necesidad de instalar Python ni librerías externas. |
| **RNF-04** | **Operación Offline** | La aplicación debe funcionar 100% de manera local, sin requerir conexión a internet ni servidores externos. |
| **RNF-05** | **Integridad de Datos** | La persistencia de datos en `config.json` debe ser atómica (escritura en archivo temporal previo al reemplazo) y generar respaldos automáticos fechados en `/backups` para prevenir corrupción de datos. |
| **RNF-06** | **Arquitectura y Mantenibilidad** | Separación clara de responsabilidades bajo el patrón MVC (Model-View-Controller) y módulos especializados para Excel, feriados y registro de eventos (`turnos.log`). |

---

### 5. Reglas de Negocio Principales (RN)

1. **RN-01 (Jerarquía de Asignación Semanal):**
   Para cada semana, el sistema evalúa la asignación en el siguiente orden estricto de prioridad:
   1. *Asignación Manual Directa:* Si el coordinador fijó a alguien para esa semana.
   2. *Semanas de Inicio Fijas:* Semanas inmutables definidas en configuración.
   3. *Historial de Meses Cerrados:* Respeta turnos ya consolidados (salvo que aparezca una excepción sobrevenida).
   4. *Lista de Pendientes:* Asigna primero al funcionario más antiguo que deba turno por una excepción anterior.
   5. *Rotación Circular Regular:* Asigna al siguiente funcionario según el puntero de la lista.

2. **RN-02 (Desacoplamiento entre Exportar y Cerrar Mes):**
   - **Exportar Excel:** Genera el archivo para revisión o difusión. **No** altera el historial ni mueve el turno de rotación.
   - **Guardar Mes:** Operación de cierre definitivo que registra el período en el historial y avanza formalmente la cola.

3. **RN-03 (Incompatibilidad Turno-Excepción):**
   Un funcionario con una excepción activa (DA, FL, LIC, OTR) durante una semana no puede recibir asignación de guardia para ese mismo período.
