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
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.space_before = Pt(2)
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
        paragraph.paragraph_format.space_after = Pt(3)
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.line_spacing = 1.08
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
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
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
        ("Title", 24, "115E59"),
        ("Heading 1", 14, "0F766E"),
        ("Heading 2", 11, "115E59"),
        ("Heading 3", 10, "0D9488"),
    ):
        style = styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)

    if "Subtitle" in styles:
        styles["Subtitle"].font.name = "Aptos"
        styles["Subtitle"].font.size = Pt(11)
        styles["Subtitle"].font.color.rgb = RGBColor(75, 85, 99)


def add_header_footer(section):
    header = section.header.paragraphs[0]
    header.text = "DEPARTAMENTO DE PERSONAL | SISTEMA DE GESTIÓN DE TURNOS"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.runs[0].font.name = "Aptos"
    header.runs[0].font.size = Pt(8)
    header.runs[0].font.color.rgb = RGBColor(107, 114, 128)

    footer = section.footer.paragraphs[0]
    footer.text = "Confidencial / Políticas de Seguridad y Privacidad de la Información (POL-SEG-2026)"
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

    # Portada / Encabezado
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(2)
    run_meta = p_meta.add_run("DEPARTAMENTO DE PERSONAL — GESTIÓN OPERATIVA DE TURNOS")
    run_meta.font.bold = True
    run_meta.font.size = Pt(9.5)
    run_meta.font.color.rgb = RGBColor.from_string("0F766E")

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(4)
    run_title = p_title.add_run("POLÍTICAS DE SEGURIDAD DE LA INFORMACIÓN Y PROTECCIÓN DE DATOS")
    run_title.font.bold = True
    run_title.font.size = Pt(20)
    run_title.font.color.rgb = RGBColor.from_string("115E59")

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("Estándares de confidencialidad, sanitización en repositorios Git/GitHub, custodia de secretos y cumplimiento normativo.")
    run_sub.font.size = Pt(10.5)
    run_sub.font.color.rgb = RGBColor(75, 85, 99)

    add_table(
        doc,
        ["Código de Documento", "Versión", "Vigencia", "Clasificación de Seguridad"],
        [["POL-SEG-TURNOS-2026-01", "1.0", "Septiembre 2026 - 2027", "Confidencial / Uso Institucional y Técnico"]],
        widths=[2.0, 1.0, 1.8, 2.0]
    )

    # 1. Objetivo y Alcance
    add_heading(doc, "1. Objetivo y Alcance", level=1)
    add_body(doc, "El presente documento formaliza las normas, directrices técnicas y salvaguardas obligatorias destinadas a asegurar la integridad, confidencialidad y disponibilidad de la información operada por el Sistema de Gestión de Turnos. Su cumplimiento es mandatorio para todo desarrollador, mantenedor, administrador del sistema y personal con acceso al código fuente o al entorno de despliegue.")
    add_body(doc, "El alcance comprende el software cliente de escritorio, las planillas y bases de datos locales, el control de versiones en plataformas públicas o privadas (GitHub), los canales de notificación automatizados (SMTP/Gmail y Google Apps Script) y la cadena de suministros de software.")

    # 2. Marco Legal
    add_heading(doc, "2. Marco Legal y Cumplimiento Normativo", level=1)
    add_body(doc, "Las directrices establecidas se alinean de manera irrestricta con el marco normativo chileno e internacional:")
    add_bullets(doc, [
        "Ley N° 19.628 sobre Protección de la Vida Privada (Chile): Regula el tratamiento automatizado de datos nominativos y sensibles en organismos públicos. Exige consentimiento expreso o habilitación legal, principio de finalidad y reserva estricta.",
        "Ley N° 21.663 Marco de Ciberseguridad e Infraestructura Crítica: Establece deberes de seguridad de la información, notificación de incidentes y aplicación de medidas preventivas en sistemas operativos de soporte institucional.",
        "Principio de Proporcionalidad y Minimización: Los sistemas deben procesar exclusivamente los datos mínimos necesarios para el cumplimiento de las funciones operativas de guardia.",
        "Estándares OWASP Top 10: Prevención de fugas de datos de configuración (A01: Broken Access Control, A02: Cryptographic Failures y A05: Security Misconfiguration)."
    ])

    # 3. Clasificación de Información
    add_heading(doc, "3. Clasificación de la Información y Niveles de Riesgo", level=1)
    add_body(doc, "Para efectos de este proyecto, los activos de datos se categorizan en cuatro niveles:")

    class_headers = ["Categoría", "Elementos Comprendidos", "Nivel de Riesgo", "Medida Obligatoria de Protección"]
    class_rows = [
        ["Datos Personales (PII)", "Nombres y apellidos, grados institucionales (COM, SBC, PRO), identificadores internos y asignaciones.", "Alto", "Prohibido almacenar en Git. En desarrollo/demos usar únicamente nombres ficticios ('Funcionario 1')."],
        ["Datos de Contacto", "Correos electrónicos institucionales (@institucion.cl), correos particulares, teléfonos móviles.", "Crítico", "Exclusión estricta de repositorios remotos. En plantillas emplear dominios de ejemplo ('usuario@ejemplo.com')."],
        ["Datos Médicos y Personales", "Motivos de licencias médicas (LIC), duelos familiares, reposos por accidentes o situaciones personales (OTR).", "Crítico", "Confidencialidad médica reforzada. Nunca incluir texto de motivos reales en ejemplos ni archivos de prueba."],
        ["Secretos y Credenciales", "Contraseñas de Aplicación Google (16 caracteres), URLs de Webhooks Apps Script (/exec), parámetros SMTP.", "Crítico", "Custodia exclusiva en archivo local .env. Prohibido su commit o exposición en código fuente o capturas."],
        ["Historial y Auditoría", "Historial de turnos asignados, bitácora auditoria[] y archivos de registro turnos.log.", "Medio / Alto", "Almacenamiento local restringido. Exclusión del control de versiones mediante .gitignore."]
    ]
    add_table(doc, class_headers, class_rows, widths=[1.4, 2.3, 1.0, 2.1])

    # 4. Política Git y Repositorios
    add_heading(doc, "4. Política de Control de Versiones y Repositorio en GitHub", level=1)
    add_body(doc, "El repositorio en GitHub debe mantenerse como un activo de software seguro, limpio y transferible, apto para escrutinio público o institucional sin riesgo de filtración de información reservada:")
    add_bullets(doc, [
        "Principio de Configuración 'Solo la Idea': El repositorio nunca versionará config.json ni respaldos reales. En su reemplazo, se mantiene config.example.json como plantilla canónica representativa del esquema v2.",
        "Aislamiento de Entornos Locales: Los archivos operativos reales (config.json, config.privado.json, .env y turnos.log) residen exclusivamente en el equipo de la estación de trabajo y están estrictamente ignorados por .gitignore.",
        "Exclusión de Artefactos Compilados: No se admiten ejecutables compilados (*.exe), cachés (__pycache__), ejecutables PyInstaller (build/, dist/) ni planillas Excel con datos reales en el árbol de Git."
    ])

    add_callout(
        doc,
        "REGLA DE ORO DE SEGURIDAD EN GIT",
        "Ningún commit debe contener información personal identificable (PII), secretos de autenticación o datos de dotación real. Si un archivo sensible se añade a Git por error, un commit posterior que lo elimine NO borra la información del historial de GitHub. Se requerirá un procedimiento de reescritura forense.",
        bg_color="FEF2F2",
        border_color="B91C1C"
    )

    # 5. Gestión de Secretos y Comunicaciones
    add_heading(doc, "5. Gestión de Secretos, Credenciales y Comunicaciones", level=1)
    add_body(doc, "El sistema implementa mecanismos de comunicación externa (notificaciones por correo SMTP y Webhook de Google Sheets/Drive). Dichos canales deben regirse por las siguientes directrices:")
    add_bullets(doc, [
        "Prohibición de Contraseñas Maestras: Queda terminantemente prohibido utilizar la contraseña principal de la cuenta de correo institucional o personal. Es obligatorio el uso de Contraseñas de Aplicación (App Passwords) de 16 caracteres de Google.",
        "Cifrado de Canal (TLS 1.2+): Todas las transmisiones SMTP deben forzarse mediante TLS en el puerto 587 (SMTP_USE_TLS=true). Las invocaciones de webhook deben viajar únicamente por HTTPS seguro (puerto 443).",
        "Protección de la Privacidad de los Destinatarios (CCO/BCC): En todo despacho de correos masivos a la dotación, las direcciones de destino deben ir en Copia Oculta (BCC) para evitar que terceros recopilen el directorio de funcionarios.",
        "Resiliencia de Red y Fallo Seguro: Antes de iniciar peticiones de red, el sistema realiza sondeos socket de baja latencia. Si no hay conectividad, la aplicación almacena los eventos en pending_notifications.json sin bloquear la interfaz de usuario."
    ])

    # 6. Copias de Seguridad y Resiliencia
    add_heading(doc, "6. Política de Copias de Seguridad (Backups) y Almacenamiento Seguro", level=1)
    add_body(doc, "La continuidad operativa y la prevención ante pérdida de datos se garantiza mediante los siguientes controles técnicos implementados en el núcleo del sistema:")
    add_bullets(doc, [
        "Escritura Atómica en Disco: Para evitar que un corte de suministro eléctrico o congelamiento corrompa la base de datos, el guardado de configuración escribe primero en un archivo temporal (config.json.tmp), fuerza la sincronización a disco físico mediante os.fsync() y realiza un reemplazo atómico mediante os.replace().",
        "Detección y Aislamiento de Corrupción: Si se detecta un archivo de configuración malformado o ilegible, el sistema lo aísla automáticamente renombrándolo a config.corrupted_TIMESTAMP.json y genera una estructura limpia para mantener el servicio activo.",
        "Rotación Automática de Respaldos: Cada operación de cierre mensual o guardado manual genera un respaldo fechado en la carpeta local backups/. Dicha carpeta está estrictamente excluida de Git.",
        "Copia Privada de Seguridad Local: El archivo config.privado.json se mantiene en el equipo como respaldo de contingencia de la dotación real, fuera del alcance de cualquier sincronización remota."
    ])

    # 7. Respuesta ante Incidentes
    add_heading(doc, "7. Procedimiento de Respuesta ante Incidentes de Seguridad", level=1)
    add_body(doc, "En caso de detectar la exposición inadvertida de credenciales, nombres reales o respaldos en un repositorio Git local o remoto en GitHub, se debe proceder de inmediato de acuerdo con las siguientes 3 fases:")

    steps_headers = ["Fase", "Acción Inmediata", "Responsable", "Evidencia Generada"]
    steps_rows = [
        ["Fase 1: Contención", "Revocar inmediatamente la Contraseña de Aplicación en Google Accounts (myaccount.google.com/apppasswords) y deshabilitar la implementación del Webhook en script.google.com.", "Oficial de Seguridad / Desarrollador", "Registro de revocación en panel de Google."],
        ["Fase 2: Purga Forense", "Ejecutar git-filter-repo para reescribir el árbol de commits, eliminando permanentemente los archivos comprometidos (backups/, config.json antiguos, correos de autor internos). Forzar sincronización con git push --force --all.", "Administrador Git", "Historial Git verificado sin cadenas sensibles."],
        ["Fase 3: Rotación y Cierre", "Generar nuevas credenciales SMTP y nueva URL de Webhook, actualizar el archivo local .env, registrar el incidente en la bitácora interna y notificar el cierre del evento.", "Jefatura de Turnos / Soporte", "Reporte de incidente cerrado y firmado."]
    ]
    add_table(doc, steps_headers, steps_rows, widths=[1.2, 2.7, 1.4, 1.5])

    # 8. Checklist de Despliegue
    add_heading(doc, "8. Lista de Verificación (Checklist) para Desarrolladores y Administradores", level=1)
    add_body(doc, "Antes de autorizar cualquier pull request, commit o despliegue en producción, se debe verificar el cumplimiento del 100% de los siguientes puntos:")
    add_bullets(doc, [
        "[ ] ¿Se verificó con 'git status' que ningún archivo con PII real (config.json, backups/, *.xlsx reales) esté en el área de preparación (staged)?",
        "[ ] ¿El archivo config.example.json contiene únicamente funcionarios ficticios ('Funcionario 1') y estructura limpia sin historial de fechas reales?",
        "[ ] ¿El archivo .env.example no contiene contraseñas reales ni identificadores de scripts institucionales privados?",
        "[ ] ¿Las pruebas unitarias (test suite) se ejecutan con datos sintéticos y finalizan con 100% de éxito?",
        "[ ] ¿El archivo .gitignore contiene todas las exclusiones requeridas (.env, config.json, config.privado.json, backups/, *.log)?",
        "[ ] ¿La documentación técnica y manuales de usuario utilizan capturas de pantalla con dotación de prueba anonimizada?"
    ])

    # Firma institucional
    doc.add_paragraph().paragraph_format.space_before = Pt(18)
    p_sign = doc.add_paragraph()
    p_sign.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sign = p_sign.add_run("_____________________________________________\nDEPARTAMENTO DE PERSONAL\nSISTEMA DE GESTIÓN Y PLANIFICACIÓN DE TURNOS\nAprobación Técnica y de Ciberseguridad")
    run_sign.font.bold = True
    run_sign.font.size = Pt(9.5)
    run_sign.font.color.rgb = RGBColor(75, 85, 99)

    doc.save(OUTPUT)
    print(f"Documento generado exitosamente en: {OUTPUT}")


if __name__ == "__main__":
    main()
