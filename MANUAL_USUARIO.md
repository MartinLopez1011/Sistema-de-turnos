# Manual de usuario — Sistema de Turnos

## 1. Abrir la aplicación

1. Abre la carpeta donde está instalado el programa.
2. Haz doble clic en **Sistema de Turnos.exe**.
3. Espera a que aparezca la ventana principal.

No cambies de lugar el archivo `config.json`. La aplicación lo necesita para conservar la información de los turnos.

## 2. Preparar un mes

En la pestaña **Planificación**:

1. Selecciona el **mes** y el **año**.
2. Revisa la tabla de turnos.
3. Si alguien no puede tomar turno, agrega una excepción:
   - Selecciona la persona.
   - Escribe el día o los días. Ejemplo: `5, 12, 19`.
   - Elige el tipo: `DA`, `FL`, `LIC` u `OTR`.
   - Pulsa **Añadir**.
4. Revisa nuevamente la tabla.

## 3. Ver el calendario

Abre la pestaña **Ver Turnos del Mes**.

- Usa **Anterior** y **Siguiente** para cambiar de mes.
- Usa **Hoy** para volver al mes actual.
- Los días marcados con **Turno** muestran los días asignados.
- Los días con `DA`, `FL`, `LIC` u `OTR` muestran excepciones.
- Los días grises son fines de semana.

## 4. Exportar a Excel

1. Abre la pestaña **Ajustes**.
2. Busca la sección **Exportar Calendario**.
3. Pulsa **Exportar a Excel**.
4. Confirma la operación.

El archivo se guardará en la misma carpeta del programa con un nombre parecido a:

```text
turnos_Septiembre_2026.xlsx
```


> Exportar a Excel solo crea el archivo. No cierra el mes ni cambia la rotación.

## 5. Cerrar el mes

Cuando hayas revisado el mes y estés seguro de que está correcto:

1. Regresa a la pestaña **Planificación**.
2. Pulsa **Guardar mes**.
3. Confirma la operación.

Al guardar el mes:

- las asignaciones quedan registradas;
- el mes pasa al historial;
- la rotación avanza al siguiente mes.

> Guarda el mes solo cuando la planificación sea definitiva.

## 6. Cambiar la persona inicial

En la pestaña **Ajustes**:

1. Busca **Persona inicial de la rotación**.
2. Selecciona la persona.
3. Pulsa **Guardar punto de inicio**.

Hazlo solo si el responsable de la planificación indica que debe comenzar otra persona.

## 7. Agregar o modificar personal

En **Ajustes**, en la sección **Gestión de Personal**, puedes:

- pulsar **Añadir Persona** para incorporar a alguien;
- pulsar **Editar** para cambiar un nombre;
- usar las flechas para cambiar el orden;
- pulsar **Eliminar** para quitar una persona.

Estos cambios afectan los próximos turnos. Los meses anteriores no se modifican.

## 8. Importante

- Primero revisa el mes y luego expórtalo a Excel.
- Guarda el mes únicamente cuando esté correcto.
- No borres ni edites `config.json`.
- Conserva los archivos Excel como respaldo.
- Si aparece un error, cierra la aplicación y avisa al responsable.
