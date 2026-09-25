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
OUTPUT = os.path.join(ROOT, "Politicas_y_Seguridad_del_Sistema.docx")


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
    paragraph.paragraph_format.space_after = Pt(2.5)
    paragraph.paragraph_format.space_before = Pt(2.5)
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
        set_cell_text(table.rows[0].cells[index], header, bold=True, color="FFFFFF", size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
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
    document.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_heading(document, text, level=1):
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 9)
    paragraph.paragraph_format.space_after = Pt(4)
    return paragraph


def add_body(document, text, bold_lead=None):
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(5)
    paragraph.paragraph_format.line_spacing = 1.14
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
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.10
        if ":" in item and not item.startswith("http"):
            lead, rest = item.split(":", 1)
            paragraph.add_run(lead + ":").bold = True
            paragraph.add_run(rest)
        else:
            paragraph.add_run(item)


def add_callout(document, title, text, bg_color="F8FAFC", border_color="0F766E"):
    table = document.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    set_table_borders(table, color=border_color, size="12")
    cell = table.rows[0].cells[0]
    set_cell_shading(cell, bg_color)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.12
    run_t = p.add_run(title + "\n")
    run_t.bold = True
    run_t.font.name = "Aptos"
    run_t.font.size = Pt(9.5)
    run_t.font.color.rgb = RGBColor.from_string(border_color)
    run_b = p.add_run(text)
    run_b.font.name = "Aptos"
    run_b.font.size = Pt(8.5)
    run_b.font.color.rgb = RGBColor(31, 41, 55)
    document.add_paragraph().paragraph_format.space_after = Pt(2)


def configure_styles(document):
    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(9.5)
    normal.font.color.rgb = RGBColor(31, 41, 55)

    for name, size, color in (
        ("Title", 22, "115E59"),
        ("Heading 1", 13.5, "0F766E"),
        ("Heading 2", 11, "115E59"),
        ("Heading 3", 10, "0D9488"),
    ):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)


def add_header_footer(section):
    header = section.header.paragraphs[0]
    header.text = "DEPARTAMENTO DE PERSONAL | SISTEMA DE GESTIÓN DE TURNOS"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.runs[0].font.name = "Aptos"
    header.runs[0].font.size = Pt(8)
    header.runs[0].font.color.rgb = RGBColor(107, 114, 128)

    footer = section.footer.paragraphs[0]
    footer.text = "Documento Informativo Oficial para Usuarios — Seguridad, Privacidad y Garantía de Datos (2026)"
    footer.alignment = WD_ALIGN_PARAGRAPH.LEFT
    footer.runs[0].font.name = "Aptos"
    footer.runs[0].font.size = Pt(8)
    footer.runs[0].font.color.rgb = RGBColor(107, 114, 128)


def main():
    doc = Document()
    configure_styles(doc)

    for s in doc.sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        add_header_footer(s)

    # Encabezado institucional
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(2)
    run_meta = p_meta.add_run("DEPARTAMENTO DE PERSONAL — GESTIÓN OPERATIVA DE TURNOS")
    run_meta.font.bold = True
    run_meta.font.size = Pt(9.5)
    run_meta.font.color.rgb = RGBColor.from_string("0F766E")

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("GUÍA DE SEGURIDAD, PRIVACIDAD Y GARANTÍA DE DATOS")
    run_title.font.bold = True
    run_title.font.size = Pt(19)
    run_title.font.color.rgb = RGBColor.from_string("115E59")

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(10)
    run_sub = p_sub.add_run("Información oficial para el usuario final: funcionamiento 100% local, no filtración de datos, control de conexiones a Internet y cumplimiento de estándares de seguridad.")
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(75, 85, 99)

    add_table(
        doc,
        ["Código de Documento", "Versión", "Audiencia", "Estado de Seguridad"],
        [["SEG-USR-TURNOS-2026", "2.0 (Usuario Final)", "Usuarios Operativos, Jefaturas y Auditores", "100% Seguro / Datos No Filtrados"]],
        widths=[2.0, 1.4, 2.3, 1.8]
    )

    # Alerta destacada de No Filtración
    add_callout(
        doc,
        "✅ DECLARACIÓN OFICIAL: SUS DATOS ESTÁN SEGUROS Y NUNCA FUERON FILTRADOS",
        "Se certifica formalmente a todos los usuarios, funcionarios y jefaturas que los datos reales de dotación, nombres, turnos, correos y motivos de excepción NUNCA han sido filtrados, expuestos ni subidos a servidores públicos de Internet.\n\n"
        "El código publicado en plataformas de desarrollo contiene exclusivamente plantillas con datos de prueba ficticios ('Juan Perez', 'Maria Gonzalez') sin ninguna relación con el personal real. La información de trabajo reside única y exclusivamente dentro de este computador.",
        bg_color="F0FDF4",
        border_color="16A34A"
    )

    # 1. Funcionamiento 100% Local
    add_heading(doc, "1. ¿Dónde Viven sus Datos? Arquitectura 100% Local (Local-First)", level=1)
    add_body(doc, "Una de las mayores ventajas del Sistema de Gestión de Turnos es que fue concebido bajo el principio de Soberanía de Datos y Ejecución Local. A diferencia de las plataformas web en la nube donde la información se envía a servidores desconocidos, este sistema funciona en su propio computador:")
    add_bullets(doc, [
        "Base de Datos en su Computador: Toda la lista de personas, su historial de turnos y las excepciones guardadas se almacenan localmente en el archivo config.json (o en la carpeta privada de su usuario en Windows).",
        "Sin Servidores Externos que Almacenen sus Datos: No existe ningún servidor web intermedio ni base de datos remota donde se copien o guarden los registros del personal.",
        "Respaldos Automáticos en Disco: Cada vez que usted guarda o cierra un mes, el sistema genera una copia de seguridad en la carpeta local backups/ dentro de su propio equipo.",
        "Control Físico Absoluto: Nadie desde el exterior puede leer, modificar ni acceder a sus planillas sin tener acceso físico o de sesión a este equipo de trabajo."
    ])

    # 2. Conexión a Internet
    add_heading(doc, "2. ¿Cómo se Conecta a Internet y por qué NO Hay Peligro de Filtración?", level=1)
    add_body(doc, "Muchos usuarios se preguntan si tener el computador conectado a Internet puede poner en riesgo sus datos. La respuesta técnica es categórica: NO existe riesgo de filtración. A continuación explicamos de manera transparente y simple cómo interactúa el programa con la red:")

    net_headers = ["Aspecto de Red", "¿Cómo Funciona?", "Nivel de Seguridad", "Garantía para el Usuario"]
    net_rows = [
        ["¿El programa recibe conexiones?", "NO. El programa NO abre puertos ni actúa como servidor web.", "Máxima", "Es invisible e inmune a intentos de escaneo o intrusión externa por red."],
        ["¿Envía la base de datos a Internet?", "NO. Nunca se transmite la lista de personal completa ni los archivos del sistema.", "Máxima", "Solo viajan textos puntuales de avisos individuales cuando usted pulsa notificar."],
        ["Canal de Envío de Correos (SMTP)", "Conexión saliente cifrada de punto a punto (TLS 1.2+ en puerto 587) directamente hacia los servidores oficiales de correo.", "Bancaria / TLS", "Nadie en la red interna ni en Internet puede interceptar ni leer el contenido."],
        ["Copia Oculta (BCC)", "Al enviar notificaciones a la dotación, las direcciones van ocultas entre sí.", "Privacidad Total", "Ningún funcionario visualiza las direcciones de correo particulares de los demás."],
        ["¿Qué pasa si NO tengo Internet?", "El sistema funciona al 100% de manera desconectada (modo offline).", "Autónoma", "No se bloquea, no se detiene y guarda los cambios con total normalidad."]
    ]
    add_table(doc, net_headers, net_rows, widths=[1.5, 2.5, 1.2, 2.0])

    add_body(doc, "En resumen: El acceso a Internet se utiliza de manera exclusivamente saliente y solo cuando el operador decide voluntariamente despachar un aviso por correo electrónico institucional. En ningún momento el software sincroniza ni sube la base de datos a ningún servicio externo.")

    # 3. Desarrollo Seguro y Cumplimiento Normativo
    add_heading(doc, "3. Desarrollo Seguro y Cumplimiento de Normativas Legales", level=1)
    add_body(doc, "El desarrollo del Sistema de Gestión de Turnos fue ejecutado desde su primera línea de código aplicando rigurosos estándares de Ciberseguridad y en estricto apego al marco legal chileno vigente:")
    add_bullets(doc, [
        "Ley N° 19.628 sobre Protección de la Vida Privada (Chile): Cumple con los principios de licitud, consentimiento y finalidad. Los datos se utilizan estrictamente para organizar las guardias y no se comparten con terceros.",
        "Ley N° 21.663 Marco de Ciberseguridad: Adopción de medidas técnicas proactivas de protección, mitigación de riesgos y resguardo de la confidencialidad de la información operativa del personal.",
        "Directrices OWASP (Open Web Application Security Project): Implementación de diseño seguro (Secure by Design), control de configuraciones y prevención contra fuga de información confidencial.",
        "Separación Estricta de Entornos: El código fuente del proyecto no contiene nombres reales, correos ni credenciales personales. Se implementó una política de anonimización absoluta en los repositorios."
    ])

    # 4. Protección contra Fallas Eléctricas y Pérdida de Datos
    add_heading(doc, "4. Protección contra Fallas Técnicas y Cortes de Energía", level=1)
    add_body(doc, "Para garantizar que el trabajo del usuario final nunca se pierda ni se dañe accidentalmente, el motor del sistema cuenta con tres barreras automáticas de protección:")
    add_bullets(doc, [
        "Guardado Atómico (Anti-Cortes de Luz): Cuando usted presiona 'Guardar', el sistema escribe primero en un archivo temporal seguro, fuerza la escritura física en disco (fsync) y solo cuando el archivo está 100% íntegro reemplaza el original en una fracción de milisegundo. Si se corta la luz en medio del proceso, su información anterior no se corrompe.",
        "Copias de Seguridad Fechadas Automáticas: Cada cierre de mes o respaldo manual genera un archivo fechado e independiente en la carpeta backups/. Si necesita revisar el estado de un mes anterior, siempre tendrá el archivo disponible.",
        "Aislamiento de Errores: Si un archivo sufriera algún daño por causas externas al programa, el sistema automáticamente lo aísla como archivo de recuperación y restaura una base operativa limpia para permitir que el servicio continúe sin interrupciones."
    ])

    # 5. Preguntas Frecuentes del Usuario Final
    add_heading(doc, "5. Preguntas Frecuentes de los Usuarios (FAQ)", level=1)

    add_body(doc, "¿Puede alguien en Internet ver los nombres o los turnos de mi equipo?", "bold_lead=¿Puede alguien en Internet ver los nombres o los turnos de mi equipo? ")
    add_body(doc, "No. El software no publica nada en Internet. La información está almacenada en el disco local de su computadora. Nadie puede acceder sin iniciar sesión directamente en su equipo de trabajo.")

    add_body(doc, "¿Si abro el programa sin conexión a Internet, funciona?", "bold_lead=¿Si abro el programa sin conexión a Internet, funciona? ")
    add_body(doc, "Sí, al 100%. Usted puede planificar todo el año, rotar turnos, ingresar permisos y exportar a Excel sin tener ningún cable de red conectado.")

    add_body(doc, "¿Qué datos se enviaron a plataformas de desarrollo como GitHub?", "bold_lead=¿Qué datos se enviaron a plataformas de desarrollo como GitHub? ")
    add_body(doc, "Únicamente el código fuente de los botones, ventanas y algoritmos de rotación, acompañados de plantillas de ejemplo con nombres ficticios (Juan Perez, Maria Gonzalez). Ningún dato de funcionarios reales fue ni será subido.")

    # 6. Buenas Prácticas Recomendadas para el Operador
    add_heading(doc, "6. Buenas Prácticas de Seguridad para el Operador Final", level=1)
    add_body(doc, "Dado que la seguridad física de la estación de trabajo es el pilar principal de un software local, se recomienda a los operadores seguir estas sencillas pautas:")
    add_bullets(doc, [
        "Bloqueo de Pantalla: Presione la tecla Windows + L cada vez que se aleje de su puesto de trabajo para evitar que personas no autorizadas manipulen las planillas.",
        "Resguardo de Planillas Excel: Al exportar planillas mensuales a Excel, guárdelas en carpetas institucionales con acceso restringido para los miembros autorizados del departamento.",
        "Contraseñas de Correo Seguras: Nunca guarde contraseñas escritas en papeles o archivos de texto sin cifrar. El archivo .env del sistema cuenta con permisos locales protegidos."
    ])

    # Cierre y firmas
    doc.add_paragraph().paragraph_format.space_before = Pt(20)
    p_cert = doc.add_paragraph()
    p_cert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_cert = p_cert.add_run("DECLARACIÓN DE CONFORMIDAD Y SEGURIDAD TÉCNICA\nEl Sistema de Gestión de Turnos cumple con todas las exigencias de privacidad, funcionamiento local autónomo y desarrollo seguro vigentes a la fecha.")
    run_cert.font.italic = True
    run_cert.font.size = Pt(9)
    run_cert.font.color.rgb = RGBColor(75, 85, 99)

    doc.add_paragraph().paragraph_format.space_before = Pt(12)
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sign = p_sign.add_run("_____________________________________________\nDEPARTAMENTO DE PERSONAL\nGESTIÓN OPERATIVA Y SEGURIDAD DE LA INFORMACIÓN\nValidez Oficial — Periodo 2026 / 2027")
    run_sign.font.bold = True
    run_sign.font.size = Pt(9.5)
    run_sign.font.color.rgb = RGBColor(31, 41, 55)

    try:
        doc.save(OUTPUT)
        print(f"Documento de usuario final generado exitosamente en: {OUTPUT}")
    except PermissionError:
        fallback = os.path.join(ROOT, "Politicas_y_Seguridad_del_Sistema_Actualizado.docx")
        doc.save(fallback)
        print(f"El archivo principal estaba abierto en Word. Se guardó una copia actualizada en: {fallback}")


if __name__ == "__main__":
    main()

