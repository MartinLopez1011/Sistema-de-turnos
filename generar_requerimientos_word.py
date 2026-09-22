import os
from datetime import date

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(ROOT, "Documento_de_Requerimientos.docx")


def set_cell_shading(cell, fill):
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def set_cell_text(cell, text, bold=False, color="1F2937", size=9.5, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.space_before = Pt(2)
    paragraph.paragraph_format.line_spacing = 1.05
    run = paragraph.add_run(str(text))
    run.bold = bold
    run.font.name = "Aptos"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_table_borders(table, color="CBD5E1", size="6"):
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
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=9.5, align=align)
        set_cell_shading(table.rows[0].cells[index], "0F766E")

    for r_idx, row in enumerate(rows):
        cells = table.add_row().cells
        bg_color = "F0FDFA" if r_idx % 2 == 1 else "FFFFFF"
        for index, value in enumerate(row):
            align = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
            bold = True if index == 0 else False
            set_cell_text(cells[index], value, bold=bold, size=9, align=align)
            set_cell_shading(cells[index], bg_color)

    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)

    p_after = document.add_paragraph()
    p_after.paragraph_format.space_after = Pt(6)
    return table


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    paragraph.paragraph_format.space_after = Pt(4)
    return paragraph


def add_body(document, text, bold_lead=None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.12
    if bold_lead and text.startswith(bold_lead):
        paragraph.add_run(bold_lead).bold = True
        paragraph.add_run(text[len(bold_lead):])
    else:
        paragraph.add_run(text)
    return paragraph


def add_bullets(document, items):
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(2.5)
        paragraph.paragraph_format.line_spacing = 1.08
        if ":" in item:
            parts = item.split(":", 1)
            r1 = paragraph.add_run(parts[0] + ":")
            r1.bold = True
            paragraph.add_run(parts[1])
        else:
            paragraph.add_run(item)


def configure_styles(document):
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10)
    normal.font.color.rgb = RGBColor(31, 41, 55)

    for name, size, color in (("Title", 26, "0F766E"), ("Heading 1", 15, "0F766E"), ("Heading 2", 12, "115E59")):
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
    styles["Caption"].font.color.rgb = RGBColor(100, 116, 139)


def add_header_footer(section):
    header = section.header.paragraphs[0]
    header.text = "Sistema de Gestión de Turnos  |  Especificación de Requerimientos de Software (ERS)"
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


def build_requirements_document():
    document = Document()
    configure_styles(document)

    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)
    add_header_footer(section)

    document.core_properties.title = "Documento de Requerimientos - Sistema de Gestión de Turnos"
    document.core_properties.subject = "Especificación de Requerimientos de Software (Simple y Ejecutiva)"
    document.core_properties.author = "Sistema de Turnos"

    # Encabezado Principal
    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(30)
    title.paragraph_format.space_after = Pt(4)
    run = title.add_run("Documento de Requerimientos de Software")
    run.bold = True
    run.font.name = "Aptos Display"
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(15, 118, 110)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(25)
    sub_run = subtitle.add_run("Sistema de Gestión y Planificación de Turnos de Guardia")
    sub_run.font.name = "Aptos"
    sub_run.font.size = Pt(13)
    sub_run.font.color.rgb = RGBColor(75, 85, 99)

    # Ficha técnica inicial
    metadata = document.add_table(rows=4, cols=2)
    metadata.alignment = WD_TABLE_ALIGNMENT.CENTER
    metadata.style = "Table Grid"
    set_table_borders(metadata, color="CBD5E1")
    meta_info = [
        ("Proyecto", "Sistema de Gestión de Turnos (TurnosApp)"),
        ("Tipo de Documento", "Especificación de Requerimientos de Software (ERS Simple)"),
        ("Plataforma", "Aplicación de Escritorio Windows (Standalone .exe)"),
        ("Fecha de Actualización", date.today().strftime("%d/%m/%Y")),
    ]
    for row, (k, v) in zip(metadata.rows, meta_info):
        set_cell_text(row.cells[0], k, bold=True, color="FFFFFF", size=9.5)
        set_cell_shading(row.cells[0], "0F766E")
        set_cell_text(row.cells[1], v, size=9.5)
        set_cell_shading(row.cells[1], "F8FAFC")
    for row in metadata.rows:
        row.cells[0].width = Inches(1.8)
        row.cells[1].width = Inches(5.2)

    p_space = document.add_paragraph()
    p_space.paragraph_format.space_after = Pt(12)

    # 1. Introducción y Propósito
    add_heading(document, "1. Introducción y Propósito", level=1)
    add_body(
        document,
        "El presente documento especifica de forma clara y directa los requerimientos funcionales, no funcionales y reglas de negocio para el Sistema de Gestión de Turnos de Guardia. El sistema tiene por finalidad automatizar la asignación rotativa semanal de turnos para el equipo de funcionarios, garantizando un reparto equitativo, trazabilidad de ausencias y continuidad entre períodos mensuales."
    )
    add_body(
        document,
        "El sistema reemplaza la confección manual en planillas aisladas, reduciendo el riesgo de omisiones, duplicidades o turnos asignados a personal no disponible."
    )

    # 2. Alcance del Sistema
    add_heading(document, "2. Alcance del Sistema", level=1)
    add_table(
        document,
        ["Área", "Descripción del Alcance"],
        [
            ("Dentro del Alcance", "• Planificación mensual con asignación rotativa semanal equitativa.\n• Gestión de excepciones y ausencias (DA, FL, LIC, OTR) con recálculo dinámico.\n• Asignación manual forzada por semana con opción de retorno al modo automático.\n• Previsualización no destructiva del mes antes de guardar.\n• Cierre formal del mes con avance de rotación e historial inmutable.\n• Vista gráfica de calendario mensual con códigos de color.\n• Exportación oficial a archivo Excel (.xlsx) con estilos y leyendas.\n• Administración de la nómina de personal (alta, edición, orden y baja).\n• Guardado atómico en archivo JSON local y respaldos automáticos fechados."),
            ("Fuera del Alcance", "• Autenticación con contraseñas o control de accesos por roles multiusuario.\n• Trabajo colaborativo concurrente en red simultáneo sobre el mismo archivo.\n• Conexión a bases de datos relacionales en la nube o servidores externos.\n• Notificaciones automáticas por correo electrónico o mensajería."),
        ],
        widths=[1.8, 5.2]
    )

    # 3. Actores del Sistema
    add_heading(document, "3. Actores del Sistema", level=1)
    add_bullets(document, [
        "Coordinador / Planificador de Turnos: Usuario principal que interactúa con el sistema para seleccionar períodos, registrar ausencias, asignar guardias, exportar calendarios en Excel y cerrar formalmente los meses.",
        "Personal de Guardia (Funcionarios): Miembros del equipo sujetos a la asignación de turnos y beneficiarios de la equidad en la rotación y el respeto a sus feriados y licencias.",
    ])

    # 4. Requerimientos Funcionales
    add_heading(document, "4. Requerimientos Funcionales (RF)", level=1)
    rf_data = [
        ("RF-01", "Selección de Período", "El sistema debe permitir elegir libremente el mes y año que se desea consultar o planificar mediante selectores de interfaz."),
        ("RF-02", "Rotación Automática Equitativa", "El sistema debe asignar las semanas de forma secuencial y circular según la lista ordenada del personal, asegurando un reparto justo de la carga."),
        ("RF-03", "Gestión de Compensaciones (Pendientes)", "Cuando un funcionario no pueda cumplir su turno debido a una ausencia registrada, el sistema debe incorporarlo a una lista de pendientes para otorgarle turno de forma prioritaria en la siguiente semana libre."),
        ("RF-04", "Registro de Excepciones y Ausencias", "El sistema debe permitir registrar ausencias por persona, fecha o rango de días (ej. 1-5, 12) categorizadas en: DA (Día Administrativo), FL (Feriado Legal), LIC (Licencia Médica) u OTR (Otro motivo), recalculando las asignaciones afectadas."),
        ("RF-05", "Asignación Manual por Semana", "El coordinador debe poder fijar manualmente a un funcionario específico en cualquier semana de la planificación (etiqueta 'MANUAL'), con la posibilidad de revertir la asignación a 'Auto' en cualquier momento."),
        ("RF-06", "Regla de Feriados Nacionales (Diciembre)", "En diciembre, el sistema debe verificar que ningún funcionario repita el mismo feriado chileno (ej. Navidad o Año Nuevo) si ya lo cubrió en el diciembre anterior registrado. Si no hay alternativas viables, asigna y emite una advertencia visual."),
        ("RF-07", "Previsualización No Destructiva", "El sistema debe permitir visualizar y simular el calendario del mes seleccionado sin alterar el puntero de la rotación ni modificar el historial guardado."),
        ("RF-08", "Cierre y Guardado de Mes", "El sistema debe permitir consolidar el mes revisado mediante la acción 'Guardar mes'. Esto traslada las asignaciones al historial permanente, actualiza el puntero de rotación y guarda el estado para el mes siguiente."),
        ("RF-09", "Vista de Calendario Mensual", "El sistema debe ofrecer una vista visual mensual donde se distingan claramente los días de guardia, las excepciones del personal y los fines de semana mediante códigos de color."),
        ("RF-10", "Exportación a Excel Oficial", "El sistema debe exportar el calendario completo a un archivo Excel (.xlsx) formateado con título, cabeceras de días, celdas de guardia coloreadas y una tabla de leyenda explicativa."),
        ("RF-11", "Administración de Personal", "El sistema debe permitir incorporar nuevos integrantes, modificar nombres, eliminarlos de la nómina y reordenar sus posiciones en la lista mediante botones de subir/bajar."),
        ("RF-12", "Configuración de Inicio y Mantenimiento", "El sistema debe permitir definir el funcionario que inicia la rotación y ofrecer la opción de reiniciar el historial con confirmación de seguridad y respaldo previo."),
    ]
    add_table(document, ["ID", "Nombre del Requerimiento", "Descripción Detallada"], rf_data, widths=[0.8, 2.0, 4.2])

    # 5. Requerimientos No Funcionales
    add_heading(document, "5. Requerimientos No Funcionales (RNF)", level=1)
    rnf_data = [
        ("RNF-01", "Rendimiento y Respuesta", "El recálculo y la previsualización del mes deben ejecutarse en menos de 1 segundo. La generación y guardado del archivo Excel debe completarse en menos de 2 segundos."),
        ("RNF-02", "Usabilidad e Interfaz", "Interfaz gráfica intuitiva en Modo Oscuro (Dark Mode), con avatares visuales, retroalimentación inmediata, mensajes de estado claros y confirmaciones en operaciones críticas."),
        ("RNF-03", "Portabilidad y Distribución", "Distribución empaquetada como ejecutable único para Windows (Sistema de Turnos.exe), funcionando de forma inmediata sin necesidad de instalar Python o paquetes adicionales."),
        ("RNF-04", "Operación Local (Offline)", "El sistema opera al 100% de manera local en el equipo del usuario, sin requerir conexión a internet ni dependencias de servicios externos."),
        ("RNF-05", "Integridad y Respaldos", "La persistencia se realiza en config.json mediante escritura atómica (archivo temporal previo) para evitar corrupción de datos, creando respaldos fechados en la carpeta /backups en cada guardado."),
        ("RNF-06", "Mantenibilidad y Arquitectura", "Diseño desacoplado bajo el patrón Modelo-Vista-Controlador (MVC), facilitando el soporte y futuras actualizaciones en la lógica de negocio o en la interfaz."),
    ]
    add_table(document, ["ID", "Categoría", "Criterio de Aceptación"], rnf_data, widths=[0.8, 1.8, 4.4])

    # 6. Reglas de Negocio Clave
    add_heading(document, "6. Reglas de Negocio Principales (RN)", level=1)
    rn_data = [
        ("RN-01", "Jerarquía Estricta de Asignación", "Al evaluar una semana, el sistema aplica la asignación en este orden de prioridad:\n1° Asignación Manual forzada por el usuario.\n2° Semanas fijas de inicio configuradas.\n3° Historial cerrado (salvo excepciones sobrevenidas).\n4° Lista de pendientes (recuperación de turnos adeudados).\n5° Rotación circular secuencial según la lista del personal."),
        ("RN-02", "Desacoplamiento Exportar vs Guardar", "Exportar a Excel genera un documento para revisión o difusión externa sin alterar el estado del sistema. Solo la acción explícita 'Guardar mes' avanza el puntero de la cola y consolida el historial."),
        ("RN-03", "Incompatibilidad de Guardia con Ausencias", "Un funcionario que mantenga una excepción activa (DA, FL, LIC, OTR) en los días de una semana no puede recibir el turno de guardia correspondiente a dicho período."),
    ]
    add_table(document, ["ID", "Regla de Negocio", "Definición y Comportamiento"], rn_data, widths=[0.8, 2.0, 4.2])

    # 7. Resumen de Aprobación
    add_heading(document, "7. Control del Documento y Aprobación", level=1)
    approval_table = document.add_table(rows=3, cols=3)
    approval_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    approval_table.style = "Table Grid"
    set_table_borders(approval_table, color="CBD5E1")

    headers_app = ["Rol", "Nombre / Responsable", "Firma y Fecha"]
    for i, h in enumerate(headers_app):
        set_cell_text(approval_table.rows[0].cells[i], h, bold=True, color="FFFFFF", size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(approval_table.rows[0].cells[i], "0F766E")

    roles = [
        ("Elaborado por", "Equipo de Desarrollo / Soporte", ""),
        ("Aprobado por", "Coordinador / Responsable de Turnos", ""),
    ]
    for row_idx, (rol, nom, f) in enumerate(roles, start=1):
        cells = approval_table.rows[row_idx].cells
        set_cell_text(cells[0], rol, bold=True, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_shading(cells[0], "F8FAFC")
        set_cell_text(cells[1], nom, size=9)
        set_cell_text(cells[2], f, size=9)

    for row in approval_table.rows:
        row.cells[0].width = Inches(2.0)
        row.cells[1].width = Inches(3.0)
        row.cells[2].width = Inches(2.0)

    document.save(OUTPUT)
    print(f"Documento generado exitosamente en: {OUTPUT}")


if __name__ == "__main__":
    build_requirements_document()
