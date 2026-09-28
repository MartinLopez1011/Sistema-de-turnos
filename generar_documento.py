"""
Generador del Documento Ejecutivo del Sistema de Gestión de Turnos (.docx).
Genera un informe ejecutivo integral, formal y actualizado con alcance, requerimientos,
arquitectura, flujo operativo y beneficios del sistema.
"""

import json
import os
import sys
from datetime import date

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# Asegurar salida de consola UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(ROOT, "Sistema_de_Gestion_de_Turnos.docx")

MESES_ESPANOL = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}


def fecha_en_espanol(d=None):
    if d is None:
        d = date.today()
    return f"{d.day} de {MESES_ESPANOL.get(d.month, 'septiembre')} de {d.year}"


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_text(cell, text, bold=False, color="1F2937", size=9, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.08
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_table_borders(table, color="D1D5DB", size="6"):
    properties = table._tbl.tblPr
    borders = properties.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def add_table(document, headers, rows, widths=None):
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    set_table_borders(table)
    for index, header in enumerate(headers):
        align = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=9, align=align)
        set_cell_shading(table.rows[0].cells[index], "0F766E")
    for r_idx, row in enumerate(rows):
        cells = table.add_row().cells
        bg_color = "F0FDFA" if r_idx % 2 == 1 else "FFFFFF"
        for index, value in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.CENTER if index == 0 and len(str(value)) <= 8 else WD_ALIGN_PARAGRAPH.LEFT
            bold = True if index == 0 and len(str(value)) <= 8 else False
            set_cell_text(cells[index], value, bold=bold, size=8.8, align=align)
            set_cell_shading(cells[index], bg_color)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(2)
    return table


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(13 if level == 1 else 9)
    paragraph.paragraph_format.space_after = Pt(4)
    return paragraph


def add_body(document, text, bold_lead=None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.12
    if bold_lead and text.startswith(bold_lead):
        r1 = paragraph.add_run(bold_lead)
        r1.bold = True
        r1.font.name = "Aptos"
        r1.font.size = Pt(9.8)
        r2 = paragraph.add_run(text[len(bold_lead):])
        r2.font.name = "Aptos"
        r2.font.size = Pt(9.8)
    else:
        r = paragraph.add_run(text)
        r.font.name = "Aptos"
        r.font.size = Pt(9.8)
    return paragraph


def add_bullets(document, items):
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2.5)
        paragraph.paragraph_format.line_spacing = 1.1
        if ":" in item:
            parts = item.split(":", 1)
            r1 = paragraph.add_run(parts[0] + ":")
            r1.bold = True
            r1.font.name = "Aptos"
            r1.font.size = Pt(9.5)
            r2 = paragraph.add_run(parts[1])
            r2.font.name = "Aptos"
            r2.font.size = Pt(9.5)
        else:
            r = paragraph.add_run(item)
            r.font.name = "Aptos"
            r.font.size = Pt(9.5)


def add_flow_row(document, labels, arrow="  →  "):
    table = document.add_table(rows=1, cols=len(labels) * 2 - 1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, label in enumerate(labels):
        cell = table.rows[0].cells[index * 2]
        set_cell_text(cell, label, bold=True, color="FFFFFF", size=8.8, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cell, "115E59")
        if index < len(labels) - 1:
            set_cell_text(table.rows[0].cells[index * 2 + 1], arrow, bold=True, color="0F766E", size=11, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_table_borders(table, color="FFFFFF", size="0")
    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(2)


def configure_styles(document):
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9.8)
    normal.font.color.rgb = RGBColor(31, 41, 55)
    for name, size, color in (("Title", 26, "115E59"), ("Heading 1", 15, "0F766E"), ("Heading 2", 11.5, "115E59")):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
    if "Caption" not in styles:
        styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    styles["Caption"].font.name = "Aptos"
    styles["Caption"].font.size = Pt(8.2)
    styles["Caption"].font.italic = True
    styles["Caption"].font.color.rgb = RGBColor(75, 85, 99)


def add_header_footer(section):
    header = section.header.paragraphs[0]
    header.text = "Sistema de Gestión de Turnos  |  Documento Ejecutivo y Resumen del Proyecto"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        run.font.name = "Aptos"
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(107, 114, 128)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)


def build_document():
    # Cargar datos actuales de configuración
    config_path = os.path.join(ROOT, "config.json")
    total_personal = 16
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
                total_personal = len(cfg.get("personal", []))
        except Exception:
            pass

    document = Document()
    configure_styles(document)
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    add_header_footer(section)

    document.core_properties.title = "Sistema de Gestión de Turnos - Documento Ejecutivo"
    document.core_properties.subject = "Resumen ejecutivo, alcance, requerimientos y arquitectura del sistema"
    document.core_properties.author = "Sistema de Gestión de Turnos"
    document.core_properties.comments = "Generado a partir del estado actual del proyecto con 132 pruebas automatizadas."

    # ── PORTADA / ENCABEZADO ──────────────────────────────────────────────────
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(80)
    title.paragraph_format.space_after = Pt(8)
    run = title.add_run("Sistema de Gestión\nde Turnos")
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = Pt(30)
    run.font.color.rgb = RGBColor(15, 118, 110)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(30)
    r_sub = subtitle.add_run("Resumen Ejecutivo, Alcance, Requerimientos y Arquitectura del Sistema")
    r_sub.font.name = "Aptos"
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = RGBColor(75, 85, 99)

    metadata = document.add_table(rows=6, cols=2)
    metadata.alignment = WD_TABLE_ALIGNMENT.CENTER
    metadata.style = "Table Grid"
    set_table_borders(metadata, color="D1D5DB")
    values = [
        ("Versión del Sistema", "1.0.0 (Producción)"),
        ("Fecha de Emisión", fecha_en_espanol()),
        ("Audiencia Objetivo", "Jefaturas de Servicio, Coordinadores de Turnos y Responsables Operativos"),
        ("Plataforma y Despliegue", "Windows 10 / 11 — Ejecutable Standalone (.exe) sin instalación ni privilegios de administrador"),
        ("Aseguramiento de Calidad", "132 pruebas automatizadas unitarias y de integración (100% aprobadas)"),
        ("Estado Operativo", f"Dotación activa: {total_personal} funcionarios | Rotación continua | Persistencia atómica"),
    ]
    for idx, (key, value) in enumerate(values):
        row = metadata.rows[idx]
        set_cell_text(row.cells[0], key, bold=True, color="FFFFFF", size=9)
        set_cell_shading(row.cells[0], "0F766E")
        set_cell_text(row.cells[1], value, size=9)
        set_cell_shading(row.cells[1], "F8FAFC")
        row.cells[0].width = Inches(2.2)
        row.cells[1].width = Inches(4.8)

    document.add_page_break()

    # ── 1. RESUMEN EJECUTIVO ──────────────────────────────────────────────────
    add_heading(document, "1. Resumen Ejecutivo")
    add_body(
        document,
        "El Sistema de Gestión de Turnos es una solución de software de escritorio de alto rendimiento, "
        "desarrollada en Python con interfaz CustomTkinter en modo oscuro, diseñada para automatizar, controlar y transparentar "
        "la distribución rotativa semanal de turnos de guardia en equipos operativos e institucionales."
    )
    add_body(
        document,
        "La herramienta resuelve de forma definitiva las inconsistencias inherentes a la confección manual de turnos: "
        "garantiza una rotación matemática circular estricta, mantiene una cola de recuperación para funcionarios que estuvieron "
        "de permiso justificado (días administrativos, vacaciones, licencias médicas u otros), aplica una ventana mínima de descanso "
        "de 4 semanas para prevenir sobrecargas de servicio y consulta el historial nacional chileno de feriados para impedir que un "
        "funcionario repita festividades críticas (como Navidad, Año Nuevo o Fiestas Patrias) en años consecutivos."
    )
    add_body(
        document,
        "El sistema combina autonomía operativa absoluta (100% funcional fuera de línea en el computador) con integración en la nube "
        "cero-costo mediante Google Apps Script para el despacho automático de correos institucionales al equipo cuando se autorizan cambios manuales. "
        "La exportación genera planillas de Excel (.xlsx) de nivel corporativo con matriz de 31 días, colores oficiales, notas de auditoría en celdas, "
        "tablas de permutas y de permisos especiales, listas para ser impresas y visadas por la jefatura."
    )

    # ── 2. PROBLEMA Y OPORTUNIDAD ─────────────────────────────────────────────
    add_heading(document, "2. Problema y Oportunidad", level=1)
    add_body(
        document,
        "En organizaciones de servicio continuo, la distribución manual de guardias semanales mediante hojas de cálculo aisladas "
        "o borradores en papel acarrea fricciones constantes y riesgos operativos significativos:",
        bold_lead="Diagnóstico de la situación previa:"
    )
    add_bullets(document, [
        "Injusticias y falta de equidad: Funcionarios que acumulan más turnos que otros o que son programados mientras disfrutan de feriado legal o reposo médico.",
        "Repetición injusta de festivos: Dificultad para recordar qué funcionario cubrió Navidad, Año Nuevo o Fiestas Patrias el año anterior, generando que las mismas personas asuman fechas complejas dos años seguidos.",
        "Pérdida de continuidad: Saltos de turno 'perdonados' sin compensación posterior o desincronización de la cola rotativa al revisar o corregir meses pasados.",
        "Falta de comunicación oportuna: Permutas de palabra entre funcionarios que no son informadas a tiempo a la jefatura ni al resto del equipo.",
        "Vulnerabilidad de datos: Archivos de Excel sobreescritos accidentalmente, pérdida de fórmulas y ausencia de respaldos automáticos.",
    ])
    add_body(
        document,
        "Oportunidad de modernización: La implementación de un sistema local determinista erradica el error humano, ahorra "
        "horas de trabajo administrativo a los coordinadores, aporta trazabilidad irrevocable y dota al servicio de un marco de "
        "transparencia y justicia laboral verificable por cualquier funcionario."
    )

    # ── 3. OBJETIVOS DEL SISTEMA ──────────────────────────────────────────────
    add_heading(document, "3. Objetivos del Sistema", level=1)
    add_heading(document, "3.1 Objetivo General", level=2)
    add_body(
        document,
        "Automatizar, garantizar la equidad y transparentar la planificación mensual de turnos semanales de guardia, "
        "asegurando continuidad rotativa ininterrumpida, respeto estricto de ausencias justificadas, trazabilidad de permutas "
        "y generación de reportes oficiales listos para firma institucional."
    )
    add_heading(document, "3.2 Objetivos Específicos", level=2)
    add_bullets(document, [
        "Previsualizar meses futuros de forma inmediata y no destructiva, calculando la fecha estimada del próximo turno por persona.",
        "Gestionar una cola circular continua con lista prioritaria de pendientes (FIFO) para recuperación de turnos omitidos.",
        "Prevenir la fatiga del personal mediante una restricción de enfriamiento de al menos 4 semanas entre turnos regulares.",
        "Alternar automáticamente las festividades de fin de año y feriados chilenos apoyándose en el registro histórico y la librería holidays.",
        "Registrar y auditar reasignaciones manuales (permutas), exigiendo un motivo obligatorio y ofreciendo reversión a cálculo automático (↺ Auto).",
        "Notificar oportunamente al equipo vía correo institucional mediante webhook serverless de Google Apps Script ante cambios manuales.",
        "Exportar planillas Excel (.xlsx) con matriz de 31 días, leyendas cromáticas, comentarios de auditoría y totales acumulados.",
        "Ofrecer administración completa de la dotación (CRUD de personal con reordenamiento ágil mediante botones ⬆/⬇).",
        "Proteger la información mediante escritura atómica (.tmp -> fsync -> replace), copias de seguridad automáticas fechadas y recuperación segura.",
    ])

    # ── 4. SOLUCIÓN Y ALCANCE ─────────────────────────────────────────────────
    add_heading(document, "4. Solución y Alcance del Proyecto", level=1)
    add_body(
        document,
        "La solución se despliega como un ejecutable autónomo para Windows (Sistema de Turnos.exe). "
        "No requiere instalación, configuraciones de servidor ni permisos de administrador institucional."
    )

    add_table(document, ["Componente", "Alcance Incluido en la Solución"], [
        ("Planificación", "Selección de mes/año, tarjetas semanales interactivas, estimación de próximo turno y previsualización no destructiva."),
        ("Rotación Inteligente", "Cola circular continua, atención prioritaria de pendientes, ventana de enfriamiento (4 semanas) y snapshots mensuales."),
        ("Gestión de Ausencias", "Registro flexible por rangos/listas (ej. 1-5, 12) de DA, FL, LIC y OTR (este último con justificación obligatoria)."),
        ("Protección Feriados", "Verificación del calendario chileno (holidays) para evitar repetición de feriados de diciembre respecto al año anterior."),
        ("Permutas y Cambios", "Asignación manual por semana con motivo obligatorio justificado, etiqueta visual MANUAL y botón de reversión rápida (↺ Auto)."),
        ("Notificaciones Nube", "Despacho automatizado de correos vía Google Apps Script al cerrar meses con cambios manuales; cola de reintentos offline si falla la red."),
        ("Consulta de Calendario", "Cuadrícula mensual cromática (rojo=guardia, naranja=DA, violeta=FL, turquesa=LIC, gris=OTR, gris claro=fin de semana)."),
        ("Reportes Excel (.xlsx)", "Generación en memoria sin plantillas externas: matriz 31 días, colores, totales por persona, tabla de permutas y tabla OTR."),
        ("Gestión de Personal", "Alta con correo, edición, reordenamiento con botones ⬆/⬇ y retiro preservando historial y coherencia de rotación."),
        ("Resiliencia de Datos", "Escritura atómica de config.json, respaldos fechados automáticos en /backups y restauración con protección pre_restore."),
    ], widths=[1.8, 5.2])

    add_body(
        document,
        "Límites del alcance (Fuera de alcance): El sistema no realiza marcación horaria biométrica (reloj control), "
        "no aprueba permisos administrativos (estos deben ser autorizados previamente por la jefatura), no requiere bases de datos en la nube "
        "ni conectividad permanente para calcular o exportar, no es multiusuario concurrente en red simultánea y no despacha mensajes por WhatsApp ni SMS.",
        bold_lead="Límites del alcance:"
    )

    document.add_page_break()

    # ── 5. REQUERIMIENTOS DEL SISTEMA ─────────────────────────────────────────
    add_heading(document, "5. Requerimientos del Sistema")
    add_heading(document, "5.1 Requerimientos Funcionales (RF)", level=2)

    rf_rows = [
        ("RF-01", "Seleccionar Período", "Permite elegir libremente mes y año, cargando las semanas y excepciones correspondientes."),
        ("RF-02", "Previsualizar Turnos", "Calcula y presenta la distribución semanal sin alterar el estado persistido ni la cola de rotación."),
        ("RF-03", "Rotación Circular Continua", "Asigna secuencialmente las semanas entre la dotación garantizando igual carga de servicio."),
        ("RF-04", "Compensación de Pendientes", "Si un funcionario es saltado por permiso, ingresa a la lista prioritaria para recuperar su turno."),
        ("RF-05", "Asignación Manual con Motivo", "Permite cambiar al asignado de una semana exigiendo obligatoriamente un motivo para auditoría."),
        ("RF-06", "Reversión Automática (↺ Auto)", "Permite cancelar una asignación manual y restituir al funcionario que le correspondía por cálculo."),
        ("RF-07", "Protección Feriados Chilenos", "Evita que un funcionario repita la guardia en el mismo feriado nacional de diciembre del año anterior."),
        ("RF-08", "Estimación de Próximo Turno", "Calcula y muestra la fecha proyectada en que el funcionario seleccionado volverá a tener guardia."),
        ("RF-09", "Calendario Visual Mensual", "Ofrece cuadrícula mensual navegable con celdas coloreadas por estado de guardia, permiso y feriado."),
        ("RF-10", "Exportar Reporte Excel (.xlsx)", "Genera informe institucional en memoria con matriz de 31 días, tablas de permutas, OTR y leyendas."),
        ("RF-11", "Cierre y Guardado de Mes", "Registra semanas en historial permanente, actualiza punteros, genera snapshots y crea respaldo fechado."),
        ("RF-12", "Notificación Serverless por Correo", "Despacha correo institucional al equipo vía webhook Google Apps Script cuando hay cambios manuales."),
        ("RF-13", "Cola de Reintentos Offline", "Si la red falla durante el cierre, almacena la notificación en cola para reintento con un clic."),
        ("RF-14", "Administración de Dotación", "Permite agregar, editar, reordenar (⬆/⬇) y retirar funcionarios manteniendo coherencia histórica."),
        ("RF-15", "Copias de Seguridad y Restauración", "Genera copias automáticas fechadas en /backups y permite restaurar creando un respaldo pre_restore."),
    ]
    add_table(document, ["ID", "Requerimiento", "Descripción Operativa"], rf_rows, widths=[0.75, 1.85, 4.4])

    add_heading(document, "5.2 Requerimientos No Funcionales (RNF)", level=2)
    rnf_rows = [
        ("RNF-01", "Plataforma y Portabilidad", "Ejecución en Windows 10/11 como standalone .exe empaquetado con PyInstaller, sin requerir Python."),
        ("RNF-02", "Velocidad de Respuesta", "Cálculo de planificación mensual en <1 segundo y generación de archivo Excel en <2 segundos."),
        ("RNF-03", "Operación Desconectada (Offline)", "El cálculo, visualización y exportación funcionan 100% de forma local sin depender de Internet."),
        ("RNF-04", "Persistencia Atómica", "Escritura segura en config.json (.tmp -> fsync -> os.replace) para evitar corrupción ante cortes eléctricos."),
        ("RNF-05", "Ergonomía Visual", "Interfaz gráfica CustomTkinter en modo oscuro (#111418, #57C7B5), avatares visuales y control de cambios sucios (●)."),
        ("RNF-06", "Privacidad y Seguridad", "Sin almacenamiento local de contraseñas de correo; webhook seguro y sanitización de datos sensibles."),
        ("RNF-07", "Confiabilidad Acreditada", "Suite completa de 132 pruebas automatizadas (pytest) con 100% de aprobación continua."),
    ]
    add_table(document, ["ID", "Atributo de Calidad", "Criterio de Cumplimiento Técnico"], rnf_rows, widths=[0.8, 1.8, 4.4])

    # ── 6. ARQUITECTURA DEL SISTEMA ───────────────────────────────────────────
    add_heading(document, "6. Arquitectura del Sistema", level=1)
    add_body(
        document,
        "La aplicación adopta una arquitectura modular Modelo-Vista-Controlador (MVC) desacoplada, "
        "optimizada para la robustez en entornos de escritorio y facilidad de mantenimiento:"
    )

    add_flow_row(document, ["main.py", "MainController", "TurnosApp", "ShiftManager", "ExcelHandler"])
    caption = document.add_paragraph("Diagrama 1. Flujo de invocación y coordinación MVC del sistema.", style="Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_table(document, ["Módulo / Capa", "Archivo / Componente", "Responsabilidad Principal"], [
        ("Entrada", "main.py", "Punto de acceso. Resuelve rutas (AppData vs Portable), captura errores globales y lanza la GUI."),
        ("Controlador", "controllers/main_controller.py", "Orquestador de negocio. Conecta GUI con el modelo, encadena meses futuros y coordina exportación."),
        ("Vista (UI)", "views/gui.py", "Ventana principal CustomTkinter, control de hilos en segundo plano y detección de cambios sin guardar."),
        ("Pestañas UI", "views/tabs/ (plan, calendar, settings)", "Vistas modulares para planificación semanal, calendario mensual y ajustes del sistema."),
        ("Modelo", "models/shift_manager.py", "Lógica algorítmica: rotación circular, cola FIFO de pendientes, regla de 4 semanas y snapshots."),
        ("Límites Modelo", "models/ (config_repository, rotation_engine)", "Submódulos especializados para persistencia atómica y motor determinista de turnos."),
        ("Reportes", "utils/excel_handler.py", "Construcción en memoria de la matriz mensual openpyxl, tablas de permutas, OTR y leyendas."),
        ("Notificaciones", "utils/email_notifier.py", "Validador de red, cliente HTTP POST con soporte de redirecciones 302 hacia Google Apps Script."),
        ("Servidor Serverless", "scripts/google_apps_script.js", "Endpoint web serverless desplegado en Google Apps Script para emisión segura de correos vía Gmail."),
        ("Feriados y Logs", "utils/chilean_holidays.py, logger.py", "Integración con feriados de Chile (holidays) y registro rotativo de eventos en turnos.log."),
    ], widths=[1.2, 2.2, 3.6])

    add_heading(document, "6.1 Gestión de Datos y Persistencia", level=2)
    add_body(
        document,
        "El estado completo del sistema reside en config.json, ubicado en %APPDATA%\\Sistema de Turnos\\ (en modo empaquetado) "
        "o en la raíz del proyecto (en modo portable). Este archivo almacena la dotación del personal, el historial inmutable de semanas cerradas, "
        "los identificadores de rotación (siguiente_id), la lista de pendientes, las excepciones fechadas, las asignaciones manuales con sus motivos "
        "y la configuración del webhook. Cada operación de escritura se efectúa atómicamente y se resguarda con copias fechadas en /backups."
    )

    document.add_page_break()

    # ── 7. FLUJO OPERATIVO MENSUAL ────────────────────────────────────────────
    add_heading(document, "7. Flujo Operativo Mensual")
    add_body(
        document,
        "Para preservar la equidad de la rotación y la integridad del historial oficial, el coordinador ejecuta un ciclo mensual estandarizado:"
    )

    add_flow_row(document, ["1. Seleccionar\nMes y Año", "2. Registrar\nAusencias", "3. Aplicar\nPermutas", "4. Previsualizar\nTurnos"])
    add_flow_row(document, ["5. Revisar\nCalendario", "6. Exportar\nExcel Oficial", "7. Guardar Mes\nDefinitivo", "8. Aviso por\nCorreo"])
    caption2 = document.add_paragraph("Diagrama 2. Ciclo operativo mensual desde la configuración hasta el cierre definitivo.", style="Caption")
    caption2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_heading(document, "7.1 Etapas del Flujo Mensual", level=2)
    add_bullets(document, [
        "Paso 1 (Selección del Período): El usuario elige el mes y año. El sistema carga las semanas naturales (lunes a domingo) correspondientes.",
        "Paso 2 (Ingreso de Excepciones): Se registran las indisponibilidades conocidas (DA, FL, LIC u OTR con motivo). El sistema actualiza en tiempo real la previsualización.",
        "Paso 3 (Permutas y Cambios Manuales): Si existen acuerdos de cambio de guardia entre funcionarios, se pulsa 'Cambiar' en la semana respectiva, se selecciona al reemplazante y se escribe el motivo obligatorio.",
        "Paso 4 (Revisión y Consulta): Se valida la distribución en la pestaña 'Ver Turnos del Mes' o en las tarjetas semanales. Se comprueba que no existan inconsistencias.",
        "Paso 5 (Exportación a Excel): Se presiona 'Exportar Excel' para generar turnos_<Mes>_<Año>.xlsx. Esta acción es de solo lectura y puede repetirse cuantas veces sea necesario.",
        "Paso 6 (Cierre Definitivo): Al presionar 'Guardar mes' en Planificación, el sistema valida la coherencia, genera un respaldo fechado, almacena las semanas en el historial inmutable, avanza el puntero de rotación y despacha automáticamente el correo de notificación si hubo cambios manuales.",
    ])

    add_body(
        document,
        "Diferencia fundamental de operaciones: 'Exportar Excel' es una operación de consulta y distribución que NO altera "
        "la cola de rotación. 'Guardar mes' es la firma de cierre que consolida el período en el historial y hace girar la lista para el mes siguiente.",
        bold_lead="Principio de inmutabilidad operativa:"
    )

    # ── 8. ENTRADAS Y SALIDAS ─────────────────────────────────────────────────
    add_heading(document, "8. Entradas y Salidas del Sistema", level=1)
    add_table(document, ["Categoría", "Tipo de Elemento", "Detalle Específico"], [
        ("Entradas del Usuario", "Selección de Fechas", "Mes y año de planificación."),
        ("Entradas del Usuario", "Permisos y Ausencias", "Funcionario, rango de fechas y tipo de permiso (DA, FL, LIC, OTR con justificación)."),
        ("Entradas del Usuario", "Asignaciones Manuales", "Semana objetivo, funcionario reemplazante y motivo obligatorio del cambio."),
        ("Entradas del Usuario", "Administración Personal", "Nombres completos, correos electrónicos y orden en la fila de rotación (⬆/⬇)."),
        ("Entradas del Sistema", "Base de Datos Local", "config.json (personal, historial, punteros, pendientes, snapshots y webhook)."),
        ("Entradas del Sistema", "Calendario Feriados", "Feriados nacionales oficiales de Chile vía librería holidays."),
        ("Salidas en Pantalla", "Vistas Interactivas", "Tarjetas de semanas, grilla de calendario a color, fecha estimada de próximo turno y diálogo de avisos."),
        ("Salidas Persistentes", "Archivos Locales", "config.json actualizado, copias fechadas en /backups y bitácora técnica en turnos.log."),
        ("Salidas Documentales", "Planillas Oficiales", "Archivos Excel (.xlsx) con matriz de 31 días, notas de auditoría, tablas de permutas y totales."),
        ("Salidas Telemáticas", "Comunicaciones", "Correos electrónicos despachados a todo el equipo vía webhook Google Apps Script con detalle de cambios."),
    ], widths=[1.5, 1.8, 3.7])

    # ── 9. BENEFICIOS Y RETORNO OPERATIVO ─────────────────────────────────────
    add_heading(document, "9. Beneficios y Retorno Operativo", level=1)
    add_bullets(document, [
        "Ahorro de tiempo superior al 90%: La confección mensual de turnos pasa de requerir varias horas de cálculo manual a completarse en menos de 5 minutos.",
        "Equidad matemática absoluta: Erradica suspicacias o percepciones de arbitrariedad en la asignación de guardias y festivos complejos.",
        "Compensación garantizada: Ningún turno omitido por permiso queda en el olvido gracias a la cola prioritaria de pendientes.",
        "Trazabilidad y transparencia institucional: Cada permuta queda respaldada con nombre, fecha, motivo y aviso formal por correo a todo el equipo.",
        "Cero costo de infraestructura: Funciona íntegramente en computadores estándar con Windows y utiliza la infraestructura gratuita de Google Apps Script.",
        "Resiliencia y seguridad ante desastres: La información nunca se corrompe gracias a la persistencia atómica y a los respaldos fechados automáticos.",
    ])

    # ── 10. CONSIDERACIONES DE OPERACIÓN ──────────────────────────────────────
    add_heading(document, "10. Consideraciones de Operación y Mantenimiento", level=1)
    add_body(
        document,
        "El sistema está concebido para ser operado directamente por la jefatura de unidad o el coordinador de guardia. "
        "No requiere servicios de mantenimiento técnico especializado continuo. Para el traspaso de mando entre coordinadores, "
        "basta con transferir la carpeta o el archivo ejecutable con sus respaldos. En caso de reemplazo de equipo informático, "
        "copiar la carpeta de configuración restaura el 100% de la historia y el estado de la rotación sin ninguna pérdida."
    )

    # ── 11. CONCLUSIÓN ────────────────────────────────────────────────────────
    add_heading(document, "11. Conclusión", level=1)
    add_body(
        document,
        "El Sistema de Gestión de Turnos representa una solución madura, robusta y completamente validada para la administración "
        "institucional de guardias semanales. Al conjugar algoritmos de equidad, diseño ergonómico en modo oscuro, reportes Excel corporativos, "
        "notificaciones serverless automáticas y una sólida arquitectura MVC respaldada por 132 pruebas automatizadas, "
        "la institución cuenta con una plataforma confiable que garantiza la continuidad del servicio y la satisfacción del equipo de trabajo."
    )

    document.save(OUTPUT)
    print(f"[OK] Documento ejecutivo generado exitosamente en: {OUTPUT}")


if __name__ == "__main__":
    build_document()