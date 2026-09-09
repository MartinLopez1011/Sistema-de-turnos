# Regla: Archivo de Contexto CLAUDE.md para Proyectos

## Cuándo aplicar

- Cuando el usuario pida un archivo de resumen del proyecto para IA (`CLAUDE.md`, `AGENTS.md`, `AI_CONTEXT.md`, etc.)
- Cuando empieces a trabajar en un proyecto sin archivo de contexto existente, sugerí crearlo
- Cuando hagas cambios significativos al proyecto (nueva arquitectura, módulos nuevos, cambios en datos), sugerí actualizar la sección relevante del `CLAUDE.md`

---

## Estructura canónica del archivo (orden obligatorio)

Creá el archivo en la **raíz del proyecto** (mismo nivel que `main.py`, `package.json`, etc.) siguiendo esta estructura de 14 secciones:

1. **Descripción** — Qué hace el sistema en 2-3 líneas (stack, distribución, persistencia, output)
2. **Arquitectura** — Árbol de archivos con comentario inline explicando el rol de cada uno
3. **Flujo de la aplicación** — Diagrama ASCII de cómo se conectan los componentes + sub-flujo del caso de uso principal
4. **Esquema de datos** — Estructura del almacén principal (JSON/DB/etc.) con comentarios explicando cada campo y sus valores posibles
5. **Lógica de negocio clave** — El algoritmo central en pasos numerados con lenguaje natural (no código)
6. **Componente principal de UI/API** — Clase raíz, design system (paleta de colores, tokens), listado de vistas/endpoints y sus funciones
7. **Módulos auxiliares** — Utilidades, handlers, helpers y qué hace cada uno
8. **Convenciones** — Nomenclatura, formatos, prefijos/sufijos usados en el proyecto
9. **Patrones de persistencia** — Cómo se guarda el estado (atómico, transaccional, caché, etc.)
10. **Build y distribución** — Comandos de build/run, dependencias principales, modo de despliegue
11. **Archivos críticos** — Tabla de qué no tocar sin cuidado y por qué
12. **Bugs conocidos y fixes** — Historial de iteraciones y correcciones aplicadas (con etiquetas ITER N / BUG FIX)
13. **Mejores prácticas** — Por área (lógica de negocio, UI/API, datos, debug). Incluir anti-patrones
14. **Estado actual** — Snapshot del estado real del proyecto al momento de escribir (datos concretos, no genéricos)

---

## Principios de eficiencia de tokens

- **Tablas** en lugar de párrafos para información estructurada y comparativa
- **Diagramas ASCII** para arquitectura y flujos (nunca descripciones textuales largas)
- **Sin redundancia** — cada línea aporta información nueva que no está en otra sección
- **Valores concretos con backticks** — usar `` `#FF3B30` ``, `` `config.json` ``, `` `siguiente_id` `` en lugar de descripciones vagas
- **Alertas de riesgo** (⚠️) para información crítica que no se debe omitir
- **El objetivo:** la IA debe saber exactamente qué archivo abrir y qué función modificar sin explorar el proyecto

---

## Qué NO incluir

- Código fuente completo (solo patrones y snippets de 3-5 líneas máximo)
- Historial de commits o changelog detallado
- Documentación de uso para usuarios finales
- Información que cambia constantemente (versiones exactas de dependencias de terceros)

---

## Mantenimiento del archivo

- **Actualizar sección 14 (Estado actual)** siempre que cambie el estado del sistema
- **Actualizar sección 12 (Bugs/fixes)** cuando se apliquen correcciones significativas
- **Actualizar secciones 2-3 (Arquitectura/Flujo)** cuando se agreguen módulos nuevos
- Sugerir al usuario actualizar el `CLAUDE.md` al final de sesiones donde se hicieron cambios estructurales
