import json
import os
from datetime import date

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(ROOT, "Sistema_de_Gestion_de_Turnos.docx")


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_text(cell, text, bold=False, color="1F2937", size=9):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
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
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=9)
        set_cell_shading(table.rows[0].cells[index], "0F766E")
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value, size=8.5)
            if len(table.rows) % 2 == 0:
                set_cell_shading(cells[index], "F0FDFA")
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    document.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    paragraph.paragraph_format.space_after = Pt(5)
    return paragraph


def add_body(document, text, bold_lead=None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.08
    if bold_lead and text.startswith(bold_lead):
        paragraph.add_run(bold_lead).bold = True
        paragraph.add_run(text[len(bold_lead):])
    else:
        paragraph.add_run(text)
    return paragraph


def add_bullets(document, items):
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.add_run(item)


def add_flow_row(document, labels, arrow="  →  "):
    table = document.add_table(rows=1, cols=len(labels) * 2 - 1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, label in enumerate(labels):
        cell = table.rows[0].cells[index * 2]
        set_cell_text(cell, label, bold=True, color="FFFFFF", size=9)
        set_cell_shading(cell, "115E59")
        if index < len(labels) - 1:
            set_cell_text(table.rows[0].cells[index * 2 + 1], arrow, bold=True, color="0F766E", size=12)
    set_table_borders(table, color="FFFFFF", size="0")
    document.add_paragraph().paragraph_format.space_after = Pt(0)


def configure_styles(document):
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(31, 41, 55)
    for name, size, color in (("Title", 28, "115E59"), ("Heading 1", 17, "0F766E"), ("Heading 2", 12, "115E59")):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
    if "Caption" not in styles:
        styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    styles["Caption"].font.name = "Aptos"
    styles["Caption"].font.size = Pt(8)
    styles["Caption"].font.italic = True
    styles["Caption"].font.color.rgb = RGBColor(75, 85, 99)


def add_header_footer(section):
    header = section.header.paragraphs[0]
    header.text = "Sistema de Gestión de Turnos  |  Documento ejecutivo"
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
    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as config_file:
        config = json.load(config_file)

    document = Document()
    configure_styles(document)
    section = document.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    add_header_footer(section)
    document.core_properties.title = "Sistema de Gestión de Turnos"
    document.core_properties.subject = "Resumen ejecutivo, alcance y arquitectura del sistema"
    document.core_properties.author = ""
    document.core_properties.comments = "Generado desde el estado actual del proyecto."

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(100)
    title.paragraph_format.space_after = Pt(12)
    run = title.add_run("Sistema de Gestión\nde Turnos")
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = Pt( thirty := 30)
    run.font.color.rgb = RGBColor(15, 118, 110)
    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Resumen ejecutivo, alcance y arquitectura").font.size = Pt(15)
    document.add_paragraph().paragraph_format.space_after = Pt(70)
    metadata = document.add_table(rows=4, cols=2)
    metadata.alignment = WD_TABLE_ALIGNMENT.CENTER
    metadata.style = "Table Grid"
    set_table_borders(metadata, color="D1D5DB")
    values = [
        ("Versión", "1.0"),
        ("Fecha", date.today().strftime("%d de septiembre de %Y")),
        ("Audiencia", "Persona ejecutiva o responsable de coordinación"),
        ("Fuente", "Implementación y configuración actuales del proyecto"),
    ]
    for row, (key, value) in zip(metadata.rows, values):
        set_cell_text(row.cells[0], key, bold=True, color="FFFFFF")
        set_cell_shading(row.cells[0], "0F766E")
        set_cell_text(row.cells[1], value)
    document.add_page_break()

    add_heading(document, "1. Resumen ejecutivo")
    add_body(document, "El Sistema de Gestión de Turnos es una aplicación de escritorio para planificar y controlar la asignación rotativa semanal de turnos de guardia. Centraliza la planificación mensual, considera excepciones de disponibilidad, conserva el historial y permite entregar un reporte Excel listo para consulta o distribución.")
    add_body(document, "La solución está orientada a un responsable de coordinación que necesita reducir el trabajo manual y mantener continuidad entre meses. La aplicación funciona localmente, conserva su estado en un archivo de configuración y ofrece una interfaz gráfica con vistas de planificación, calendario y ajustes.")
    add_body(document, "El alcance actual cubre la generación de turnos, la gestión de excepciones, el cierre de meses, la consulta del calendario y la exportación a Excel. No incluye autenticación, trabajo multiusuario en red ni un repositorio centralizado de datos.")
    add_heading(document, "2. Problema y oportunidad", level=1)
    add_body(document, "La asignación manual de turnos puede producir omisiones, duplicidades, poca visibilidad del estado de la rotación y dificultad para recuperar turnos cuando una persona no está disponible. También resulta necesario conservar decisiones ya cerradas sin perder la posibilidad de recalcular un periodo cuando cambian sus excepciones.")
    add_body(document, "El sistema aborda esta situación mediante una rotación controlada, reglas explícitas y una separación entre previsualizar, cerrar el mes y exportar el reporte. Así, la persona responsable puede revisar el resultado antes de persistirlo y disponer de un calendario uniforme para su distribución.")
    add_heading(document, "3. Objetivos", level=1)
    add_heading(document, "3.1 Objetivo general", level=2)
    add_body(document, "Gestionar de forma ordenada, trazable y consistente la planificación mensual de turnos semanales de guardia, respetando la rotación del personal, las excepciones y el historial de periodos cerrados.")
    add_heading(document, "3.2 Objetivos específicos", level=2)
    add_bullets(document, [
        "Generar una previsualización mensual antes de confirmar cambios.",
        "Asignar turnos mediante una lista circular y atender primero a las personas pendientes de recuperar un turno.",
        "Respetar semanas fijas, historial y una separación mínima para evitar turnos demasiado próximos.",
        "Registrar excepciones por persona, fecha y tipo, incluyendo DA, FL, LIC y OTR.",
        "Cerrar meses conservando historial, excepciones, puntero de rotación y estado del mes siguiente.",
        "Exportar el calendario a un archivo Excel con una plantilla incorporada.",
    ])

    add_heading(document, "4. Solución y alcance", level=1)
    add_body(document, "La solución se ejecuta como aplicación de escritorio para Windows. La persona usuaria selecciona un periodo, revisa la planificación, registra excepciones cuando corresponde y decide entre exportar el resultado o cerrar el mes para actualizar el estado de la rotación.")
    add_table(document, ["Incluido", "Descripción"], [
        ("Planificación", "Selección de mes y año, previsualización y revisión de semanas asignadas."),
        ("Rotación", "Lista circular, personas pendientes, semanas fijas, historial y snapshots mensuales."),
        ("Excepciones", "Registro por persona, fecha y tipo; las excepciones afectan la asignación de la semana."),
        ("Consulta", "Calendario mensual con navegación entre periodos."),
        ("Exportación", "Reporte Excel con turnos, fines de semana y excepciones diferenciadas por color."),
        ("Persistencia", "Archivo local `config.json` con escritura temporal y reemplazo atómico."),
    ], widths=[1.35, 5.7])
    add_body(document, "Fuera del alcance actual: autenticación y perfiles de usuario, edición concurrente desde varios equipos, almacenamiento en base de datos, auditoría por usuario y sincronización en red.")

    document.add_page_break()
    add_heading(document, "5. Requerimientos principales")
    add_heading(document, "5.1 Requerimientos funcionales", level=2)
    add_table(document, ["ID", "Requerimiento", "Resultado esperado"], [
        ("RF-01", "Seleccionar periodo", "La persona usuaria elige el mes y año que desea consultar o planificar."),
        ("RF-02", "Previsualizar turnos", "El sistema calcula la asignación sin modificar el estado persistido."),
        ("RF-03", "Aplicar rotación", "Se asigna según puntero, pendientes, excepciones e historial."),
        ("RF-04", "Gestionar excepciones", "Se registra persona, fecha y tipo de excepción para el periodo."),
        ("RF-05", "Cerrar mes", "Se guarda historial, excepciones, snapshots y estado de continuidad."),
        ("RF-06", "Consultar calendario", "Se visualiza la distribución mensual en una vista de calendario."),
        ("RF-07", "Exportar Excel", "Se genera `turnos_<Mes>_<Año>.xlsx` con la plantilla incorporada."),
        ("RF-08", "Administrar configuración", "Se puede cambiar el inicio de la rotación y reiniciar el historial mediante la interfaz."),
    ], widths=[0.55, 1.65, 4.85])
    add_heading(document, "5.2 Requerimientos no funcionales", level=2)
    add_table(document, ["Aspecto", "Condición actual"], [
        ("Plataforma", "Aplicación de escritorio orientada a Windows y distribuible con PyInstaller."),
        ("Operación", "Funcionamiento local, sin dependencia de un servidor remoto."),
        ("Persistencia", "Datos almacenados en JSON y protegidos durante el guardado mediante archivo temporal."),
        ("Usabilidad", "Interfaz gráfica con confirmaciones y mensajes de estado para operaciones relevantes."),
        ("Interoperabilidad", "Salida en formato Excel mediante openpyxl y una plantilla incorporada."),
        ("Mantenibilidad", "Separación de vista, coordinación, lógica de negocio y exportación."),
    ], widths=[1.55, 5.5])

    add_heading(document, "6. Arquitectura del sistema")
    add_body(document, "La aplicación utiliza una arquitectura MVC simple. La vista presenta la información y recibe acciones; el controlador coordina las operaciones; el modelo concentra la lógica de rotación y persistencia; y el componente de Excel transforma la planificación en un reporte distribuible.")
    add_flow_row(document, ["main.py", "MainController", "TurnosApp", "ShiftManager", "ExcelHandler"])
    caption = document.add_paragraph("Diagrama 1. Componentes principales y relación de coordinación.", style="Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_table(document, ["Componente", "Responsabilidad"], [
        ("main.py", "Determina la ruta raíz y pone en marcha la aplicación."),
        ("MainController", "Expone operaciones a la interfaz, coordina previsión, exportación y cierre."),
        ("TurnosApp", "Gestiona las pestañas de planificación, calendario y ajustes."),
        ("ShiftManager", "Calcula turnos, gestiona excepciones, historial, pendientes, snapshots y JSON."),
        ("ExcelHandler", "Construye la plantilla Excel en memoria, pinta la grilla y guarda el archivo de salida."),
    ], widths=[1.5, 5.55])
    add_heading(document, "6.1 Persistencia y datos", level=2)
    add_body(document, "El archivo `config.json` funciona como almacén local del estado. Contiene el personal, las semanas iniciales, el historial, el siguiente identificador de rotación, las personas pendientes, los snapshots por mes y las excepciones. El sistema normaliza las claves mensuales de snapshots y usa una escritura temporal antes de reemplazar el archivo principal.")
    add_body(document, "La estructura base del reporte Excel está incorporada en `ExcelHandler`; el exportador crea la grilla en memoria, identifica las filas del personal y colorea los días de turno, fines de semana y excepciones. Por ello, el ejecutable no depende de un archivo `ejemplo.xlsx` externo.")

    document.add_page_break()
    add_heading(document, "7. Flujo operativo mensual")
    add_flow_row(document, ["Seleccionar\nperiodo", "Registrar\nexcepciones", "Previsualizar", "Decidir"])
    add_flow_row(document, ["Cerrar mes\ny persistir", "Actualizar\nrotación", "Consultar\ncalendario", "Exportar\nExcel"])
    caption = document.add_paragraph("Diagrama 2. Flujo general desde la planificación hasta la consulta y distribución.", style="Caption")
    caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_heading(document, "7.1 Generación de una planificación", level=2)
    add_bullets(document, [
        "La persona selecciona el mes y año, y el sistema obtiene el estado correspondiente o encadena una previsión para meses futuros.",
        "Se incorporan las excepciones temporales y se calcula la asignación sin guardar automáticamente cambios.",
        "El algoritmo respeta semanas iniciales inmutables e historial, intenta atender pendientes y luego continúa la lista circular.",
        "Una persona con excepción se omite para esa semana y queda pendiente para recuperar su turno cuando exista disponibilidad.",
        "La separación mínima de semanas reduce la posibilidad de asignaciones demasiado cercanas.",
    ])
    add_heading(document, "7.2 Cierre y exportación", level=2)
    add_body(document, "Cerrar el mes y exportar el Excel son acciones independientes. El cierre actualiza el estado operativo: historial, excepciones, siguiente persona, pendientes y snapshot del mes posterior. La exportación genera un archivo Excel y no avanza la cola de rotación.")
    add_heading(document, "8. Entradas y salidas", level=1)
    add_table(document, ["Tipo", "Elementos"], [
        ("Entradas de usuario", "Mes, año, persona, fechas y tipos de excepción, persona inicial de la rotación."),
        ("Entradas del sistema", "config.json y estado previamente guardado; la estructura Excel está incorporada en el sistema."),
        ("Salidas de interfaz", "Tabla de planificación, calendario mensual, mensajes de estado y confirmaciones."),
        ("Salidas persistentes", "config.json actualizado al cerrar el mes."),
        ("Salidas de distribución", "Archivos Excel con el formato `turnos_<Mes>_<Año>.xlsx`."),
    ], widths=[1.65, 5.4])

    add_heading(document, "9. Beneficios esperados")
    add_bullets(document, [
        "Menor esfuerzo manual para construir la planificación mensual.",
        "Mayor continuidad entre meses gracias al historial y los snapshots.",
        "Tratamiento explícito de indisponibilidades y recuperación de turnos omitidos.",
        "Mayor claridad para revisar una planificación antes de confirmarla.",
        "Reporte Excel uniforme para consulta y distribución.",
    ])
    add_heading(document, "10. Consideraciones de operación")
    add_body(document, "El sistema depende de la integridad de `config.json`; la estructura del reporte Excel está incorporada en el código y no requiere archivos auxiliares junto al ejecutable. La solución actual está diseñada para un uso local con un responsable que controla el estado de la planificación.")
    add_heading(document, "11. Conclusión")
    add_body(document, "El Sistema de Gestión de Turnos entrega una solución concreta para organizar la rotación semanal y convertirla en un calendario mensual consultable y exportable. Su diseño separa la interfaz, la lógica de negocio, la coordinación y la generación de reportes, lo que permite entender el funcionamiento general y mantener una continuidad controlada entre periodos.")
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build_document()