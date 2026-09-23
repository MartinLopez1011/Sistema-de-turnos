"""
Script para generar el Manual de Usuario en PDF del Sistema de Turnos.
Versión simplificada, amigable y comprensible para usuarios sin conocimientos informáticos.
"""

import os
import sys
import subprocess
from datetime import datetime

# Asegurar salida de consola UTF-8 en Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_OUTPUT = os.path.join(ROOT_DIR, "manual_usuario_documento.html")
PDF_OUTPUT = os.path.join(ROOT_DIR, "Manual_de_Usuario_Sistema_de_Turnos.pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def build_simple_html():
    now = datetime.now()
    meses_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    current_date = f"{now.day} de {meses_es[now.month - 1]} de {now.year}"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Manual de Usuario Fácil — Sistema de Turnos</title>
<style>
  @page {{
    size: letter portrait;
    margin: 1.6cm 1.5cm 1.8cm 1.5cm;
    @top-right {{
      content: "Guía de Usuario — Sistema de Turnos";
      font-size: 8pt;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #64748b;
    }}
    @bottom-center {{
      content: "Página " counter(page);
      font-size: 8.5pt;
      font-family: 'Segoe UI', Arial, sans-serif;
      color: #64748b;
      font-weight: bold;
    }}
  }}

  *, *:before, *:after {{
    box-sizing: border-box;
  }}

  body {{
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.6;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
  }}

  /* Portada Amigable */
  .cover-box {{
    page-break-after: always;
    min-height: 88vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 2.2cm 1.2cm 1.2cm 1.2cm;
    border-left: 10px solid #0f766e;
    padding-left: 2cm;
    background: linear-gradient(180deg, #f0fdfa 0%, #ffffff 40%);
  }}

  .badge-app {{
    display: inline-block;
    background-color: #0f766e;
    color: #ffffff;
    font-size: 9.5pt;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 6px;
    margin-bottom: 20px;
  }}

  .cover-title {{
    font-size: 27pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.2;
    margin: 0 0 14px 0;
  }}

  .cover-subtitle {{
    font-size: 13.5pt;
    font-weight: 400;
    color: #334155;
    line-height: 1.5;
    margin: 0 0 25px 0;
    max-width: 600px;
  }}

  .summary-card-hero {{
    background-color: #ffffff;
    border: 2px solid #ccfbf1;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 4px 15px rgba(15, 118, 110, 0.08);
    margin-bottom: 25px;
  }}

  .summary-card-hero h3 {{
    margin: 0 0 10px 0;
    color: #0f766e;
    font-size: 13pt;
    font-weight: 700;
  }}

  .summary-card-hero p {{
    margin: 0;
    color: #475569;
    font-size: 10pt;
    line-height: 1.5;
  }}

  .cover-footer {{
    border-top: 1px solid #e2e8f0;
    padding-top: 15px;
    font-size: 9pt;
    color: #64748b;
  }}

  /* Encabezados claros */
  h1 {{
    color: #0f766e;
    font-size: 17pt;
    font-weight: 800;
    border-bottom: 2px solid #99f6e4;
    padding-bottom: 6px;
    margin-top: 24pt;
    margin-bottom: 12pt;
    page-break-after: avoid;
    break-after: avoid;
  }}

  h2 {{
    color: #1e293b;
    font-size: 13pt;
    font-weight: 700;
    margin-top: 16pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
    break-after: avoid;
  }}

  h3 {{
    color: #334155;
    font-size: 11pt;
    font-weight: 700;
    margin-top: 12pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
    break-after: avoid;
  }}

  p {{
    margin: 0 0 10pt 0;
    text-align: left;
  }}

  /* Cajas de Pasos Numerados Grandes */
  .step-box {{
    display: flex;
    gap: 16px;
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 14px;
    align-items: flex-start;
    page-break-inside: avoid;
  }}

  .step-number {{
    background-color: #0f766e;
    color: #ffffff;
    font-size: 14pt;
    font-weight: 800;
    min-width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }}

  .step-content {{
    flex: 1;
  }}

  .step-content strong {{
    display: block;
    font-size: 11pt;
    color: #0f172a;
    margin-bottom: 4px;
  }}

  .step-content p {{
    margin: 0;
    font-size: 9.8pt;
    color: #475569;
  }}

  /* Cajas de Aviso / Notas */
  .note-box {{
    border-radius: 8px;
    padding: 12px 16px;
    margin: 14pt 0;
    font-size: 9.8pt;
    page-break-inside: avoid;
  }}

  .note-tip {{
    background-color: #ecfdf5;
    border-left: 5px solid #10b981;
    color: #065f46;
  }}

  .note-warn {{
    background-color: #fffbeb;
    border-left: 5px solid #f59e0b;
    color: #92400e;
  }}

  .note-alert {{
    background-color: #fef2f2;
    border-left: 5px solid #ef4444;
    color: #991b1b;
  }}

  .note-title {{
    font-weight: bold;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  /* Tarjetas de Alcance (Qué hace y qué no hace) */
  .scope-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin: 14pt 0;
    page-break-inside: avoid;
  }}

  .scope-card {{
    border-radius: 10px;
    padding: 16px;
  }}

  .scope-yes {{
    background-color: #f0fdf4;
    border: 1px solid #bbf7d0;
  }}

  .scope-no {{
    background-color: #fef2f2;
    border: 1px solid #fecaca;
  }}

  .scope-card h3 {{
    margin-top: 0;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .scope-yes h3 {{ color: #166534; }}
  .scope-no h3 {{ color: #991b1b; }}

  .scope-card ul {{
    margin: 0;
    padding-left: 18px;
    font-size: 9.5pt;
    color: #334155;
  }}

  .scope-card li {{
    margin-bottom: 6px;
  }}

  /* Tablas sencillas */
  table.simple-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }}

  table.simple-table th {{
    background-color: #0f766e;
    color: #ffffff;
    font-weight: 700;
    padding: 8px 12px;
    text-align: left;
    border: 1px solid #0d9488;
  }}

  table.simple-table td {{
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    vertical-align: middle;
  }}

  table.simple-table tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}

  /* Botones e insignias en el texto */
  .btn-sample {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 5px;
    font-size: 8.5pt;
    font-weight: bold;
    color: #ffffff;
    white-space: nowrap;
  }}

  .btn-save {{ background-color: #059669; }}
  .btn-change {{ background-color: #252d34; border: 1px solid #475569; color: #f1f5f3; }}
  .btn-excel {{ background-color: #059669; }}
  .btn-auto {{ background-color: #374151; color: #fca5a5; }}

  .badge-color {{
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 8pt;
    font-weight: bold;
    color: #ffffff;
    margin-right: 4px;
  }}

  .col-turno {{ background-color: #991b1b; }}
  .col-da {{ background-color: #b45309; }}
  .col-fl {{ background-color: #5b21b6; }}
  .col-lic {{ background-color: #0e7490; }}
  .col-otr {{ background-color: #374151; }}
  .col-fin {{ background-color: #64748b; }}

  /* Ilustración sencilla de pantalla */
  .screen-mock {{
    background-color: #111418;
    color: #f1f5f3;
    border-radius: 8px;
    border: 1px solid #303a40;
    padding: 14px;
    margin: 14pt 0;
    font-size: 9pt;
    page-break-inside: avoid;
  }}

  .screen-header {{
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #252d34;
    padding-bottom: 6px;
    margin-bottom: 10px;
    font-weight: bold;
    color: #57c7b5;
  }}

  .tabs-bar {{
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
  }}

  .tab-pill {{
    background-color: #1c2228;
    padding: 5px 12px;
    border-radius: 4px;
    font-size: 8pt;
    color: #91a0a5;
    font-weight: bold;
  }}

  .tab-pill.active {{
    background-color: #16877d;
    color: #ffffff;
  }}

  .mock-card {{
    background-color: #1c2228;
    border: 1px solid #303a40;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
  }}

  .page-break {{
    page-break-after: always;
    break-after: page;
  }}
</style>
</head>
<body>

<!-- PORTADA AMIGABLE -->
<div class="cover-box">
  <div>
    <div class="badge-app">Manual Rápido para el Usuario</div>
    <div class="cover-title">Sistema de Gestión de Turnos</div>
    <div class="cover-subtitle">
      Guía paso a paso y fácil de entender para organizar las guardias de turno de tu equipo, registrar permisos y sacar la hoja de Excel sin complicaciones.
    </div>

    <div class="summary-card-hero">
      <h3>¿Qué es este programa y para qué sirve?</h3>
      <p>
        Es un programa muy sencillo diseñado para que <strong>nunca más tengas que calcular los turnos a mano</strong> ni pelear con fechas. 
        El sistema sabe a quién le toca la guardia cada semana de forma justa y equitativa, salta automáticamente a las personas que estén con vacaciones o permiso, y te entrega una <strong>planilla de Excel lista para imprimir y firmar</strong> con un solo clic.
      </p>
    </div>
  </div>

  <div class="cover-footer">
    <strong>Guía Oficial de Usuario</strong> · Versión Simple · Fecha de actualización: {current_date}<br>
    <em>Diseñado para que cualquier persona pueda usarlo sin conocimientos de computación.</em>
  </div>
</div>

<!-- CAPÍTULO 1: RESUMEN RÁPIDO Y ALCANCE -->
<h1>1. Resumen en 1 Minuto: ¿Qué hace el programa?</h1>

<p>
Imagina que los funcionarios del equipo están sentados en una mesa redonda. Cada semana, la guardia pasa a la siguiente persona en el orden de la lista.
</p>
<p>
<strong>¿Qué hace el programa por ti?</strong>
</p>
<ul>
  <li><strong>Lleva la cuenta por ti:</strong> Sabe exactamente a quién le toca cada semana para que nadie trabaje el doble ni nadie se quede sin hacer turno.</li>
  <li><strong>Respeta los permisos y vacaciones:</strong> Si alguien pide un Día Administrativo (<span class="badge-color col-da">DA</span>), se va de vacaciones (<span class="badge-color col-fl">FL</span>) o tiene licencia médica (<span class="badge-color col-lic">LIC</span>), el programa no le da turno esa semana, busca al siguiente libre, y <em>le guarda su turno</em> para devolvérselo cuando regrese.</li>
  <li><strong>Cuida las fiestas de fin de año:</strong> En diciembre, se asegura de que si alguien trabajó en Navidad o Año Nuevo el año pasado, este año no le toque repetir la misma fecha.</li>
  <li><strong>Entrega el informe en Excel:</strong> Con un solo botón te genera la hoja con colores, títulos y los totales de cada funcionario lista para entregar a la jefatura.</li>
</ul>

<h2>El Alcance: ¿Qué hace y qué no hace el sistema?</h2>

<div class="scope-grid">
  <div class="scope-card scope-yes">
    <h3>✔ Lo que SÍ hace el programa</h3>
    <ul>
      <li>Calcula las semanas de lunes a domingo de todo el mes.</li>
      <li>Permite cambiar manualmente a alguien si hicieron una permuta o cambio de turno de palabra.</li>
      <li>Crea el archivo Excel con el calendario de todo el mes.</li>
      <li>Guarda la historia de los meses pasados para no perder la cuenta.</li>
      <li>Avisa por correo a los funcionarios si hubo un cambio forzado de última hora.</li>
      <li>Funciona de forma rápida y segura en tu computador.</li>
    </ul>
  </div>

  <div class="scope-card scope-no">
    <h3>✖ Lo que NO hace (ni necesitas)</h3>
    <ul>
      <li><strong>No necesitas internet</strong> para calcular los turnos ni para sacar la hoja de Excel.</li>
      <li><strong>No necesitas usuario ni contraseña:</strong> Lo abres y ya puedes trabajar.</li>
      <li><strong>No borra nada por error:</strong> Si te equivocas de mes, los meses anteriores ya guardados no se modifican.</li>
      <li><strong>No sobreescribe tus archivos abiertos:</strong> Te avisa con claridad si algo falta.</li>
    </ul>
  </div>
</div>

<div class="note-box note-tip">
  <div class="note-title">💡 La Regla de Oro: En 3 simples pasos</div>
  <strong>1.</strong> Eliges el mes y agregas si alguien tiene vacaciones o permiso.<br>
  <strong>2.</strong> Miras cómo quedó la lista de semanas y sacas el Excel.<br>
  <strong>3.</strong> Cuando esté todo listo y aprobado, pulsas el botón verde <strong>Guardar mes</strong>.
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 2: CÓMO ABRIR Y EMPEZAR -->
<h1>2. ¿Cómo abrir el programa y primeros pasos?</h1>

<div class="step-box">
  <div class="step-number">1</div>
  <div class="step-content">
    <strong>Abre la carpeta del programa</strong>
    <p>Busca la carpeta en tu computador donde guardaste el sistema (por ejemplo, en Documentos o en el Escritorio).</p>
  </div>
</div>

<div class="step-box">
  <div class="step-number">2</div>
  <div class="step-content">
    <strong>Haz doble clic en: Sistema de Turnos.exe</strong>
    <p>Es la aplicación con el ícono del calendario. Espera un par de segundos y se abrirá la ventana en tu pantalla.</p>
  </div>
</div>

<div class="step-box">
  <div class="step-number">3</div>
  <div class="step-content">
    <strong>Verás 3 pestañas principales en la parte de arriba:</strong>
    <p>
      • <strong>📋 Planificación:</strong> Es donde se prepara el mes y se registran permisos.<br>
      • <strong>📅 Ver Turnos del Mes:</strong> Es donde ves el calendario completo y sacas el Excel.<br>
      • <strong>⚙ Ajustes:</strong> Es donde ves la lista de compañeros y sus correos.
    </p>
  </div>
</div>

<!-- DIBUJO DE LA PANTALLA -->
<div class="screen-mock">
  <div class="screen-header">
    <span>🗓 Sistema de Turnos (Vista Principal)</span>
    <span>Ventana Principal</span>
  </div>

  <div class="tabs-bar">
    <div class="tab-pill active">📋 Planificación</div>
    <div class="tab-pill">📅 Ver Turnos del Mes</div>
    <div class="tab-pill">⚙ Ajustes</div>
  </div>

  <div style="display: grid; grid-template-columns: 200px 1fr; gap: 10px;">
    <div style="background: #171b20; padding: 10px; border-radius: 6px;">
      <strong style="color: #57c7b5; font-size: 8pt;">1. ELEGIR MES</strong><br>
      <div style="background: #252d34; padding: 4px; margin: 4px 0 8px 0; border-radius: 4px;">Septiembre 2026</div>

      <strong style="color: #57c7b5; font-size: 8pt;">2. AGREGAR PERMISO</strong><br>
      <div style="font-size: 7.5pt; color: #91a0a5; margin-bottom: 4px;">Seleccionar persona y días:</div>
      <div style="background: #252d34; padding: 4px; margin-bottom: 6px; border-radius: 4px;">Ej: 1-5 o 12, 19</div>
      <div class="btn-sample btn-save" style="width: 100%; text-align: center; font-size: 7.5pt;">＋ Añadir Permiso</div>
    </div>

    <div>
      <div class="mock-card">
        <strong style="color: #8de1d2; font-size: 8.5pt;">📅 Semana 1 (07/09 al 13/09)</strong>
        <div style="margin-top: 4px; font-weight: bold; color: #6ee7b7;">Le toca a: PRO VEGA NATALIA</div>
      </div>
      <div class="mock-card">
        <strong style="color: #8de1d2; font-size: 8.5pt;">📅 Semana 2 (14/09 al 20/09)</strong>
        <div style="margin-top: 4px; font-weight: bold; color: #6ee7b7;">Le toca a: PRO TAPIA KARINA</div>
      </div>
      <div style="text-align: right; margin-top: 6px;">
        <span class="btn-sample btn-save" style="padding: 6px 14px;">💾 Guardar mes</span>
      </div>
    </div>
  </div>
</div>

<div class="note-box note-warn">
  <div class="note-title">⚠️ Importante para cuidar tus datos</div>
  En esa misma carpeta verás un archivo llamado <code>config.json</code>. 
  <strong>Ese archivo es el "cuaderno" donde el programa anota todo.</strong> No lo borres ni le cambies el nombre para que el programa siempre recuerde los turnos anteriores.
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 3: CÓMO PLANIFICAR UN MES PASO A PASO -->
<h1>3. Cómo preparar el mes (Pestaña "Planificación")</h1>

<p>
Esta es la pestaña que más vas a usar. Sigue estos pasos en orden:
</p>

<h2>Paso 1: Elige el Mes y el Año</h2>
<p>
En el costado izquierdo, elige el <strong>mes</strong> y el <strong>año</strong> que quieres planificar. Al hacerlo, el programa te mostrará inmediatamente las semanas del mes en el panel derecho.
</p>

<h2>Paso 2: Marca si alguien tiene permiso o vacaciones</h2>
<p>
Si sabes que un compañero no va a estar disponible:
</p>
<ol>
  <li>En <strong>Persona</strong>, selecciona el nombre del funcionario.</li>
  <li>En <strong>Días del mes</strong>, escribe los días que va a faltar:
    <ul>
      <li>Si es un solo día: escribe <span style="background: #f1f5f9; padding: 2px 5px; font-weight: bold;">15</span></li>
      <li>Si son varios días sueltos: escribe <span style="background: #f1f5f9; padding: 2px 5px; font-weight: bold;">12, 19, 25</span></li>
      <li>Si es un período continuo de vacaciones: escribe <span style="background: #f1f5f9; padding: 2px 5px; font-weight: bold;">1-15</span> (del 1 al 15)</li>
    </ul>
  </li>
  <li>Elige el botón del tipo de ausencia:
    <div style="margin: 6px 0;">
      <span class="badge-color col-da">DA</span> <strong>Día Administrativo</strong> (Permiso personal con goce de sueldo)<br>
      <span class="badge-color col-fl">FL</span> <strong>Feriado Legal</strong> (Vacaciones anuales)<br>
      <span class="badge-color col-lic">LIC</span> <strong>Licencia Médica</strong> (Reposo por salud)<br>
      <span class="badge-color col-otr">OTR</span> <strong>Otro</strong> (Comisión de servicio, duelo, etc.)
    </div>
  </li>
  <li>Presiona el botón verde <strong>＋ Añadir</strong>.</li>
</ol>
<p>
<em>¿Qué pasa de inmediato?</em> El programa recalcula las semanas. Si a esa persona le tocaba guardia mientras estaba de permiso, el programa se la quita, pone a otro compañero disponible y deja anotado que a la persona ausente se le debe ese turno para devolvérselo cuando regrese.
</p>

<h2>Paso 3: ¿Qué pasa si hicieron un cambio o permuta de palabra?</h2>
<p>
A veces dos compañeros acuerdan cambiarse la guardia entre ellos. Para reflejarlo en el programa:
</p>
<ol>
  <li>En la tarjeta de la semana que quieres cambiar, pulsa el botón <span class="btn-sample btn-change">✏️ Cambiar</span>.</li>
  <li>Elige quién va a hacer la guardia en la lista desplegable.</li>
  <li><strong>Escribe el motivo del cambio</strong> (ejemplo: <em>"Permuta autorizada por asuntos familiares"</em>).</li>
  <li>Pulsa <strong>Asignar Guardia</strong>.</li>
  <li>La tarjeta se marcará con una etiqueta verde que dice <strong>📌 MANUAL</strong>.</li>
</ol>

<div class="note-box note-tip">
  <div class="note-title">💡 ¿Te equivocaste al cambiarlo a mano?</div>
  Si pulsas el botón <span class="btn-sample btn-auto">↺ Auto</span> que aparece en la tarjeta, el programa borra el cambio forzado y vuelve a calcular automáticamente la persona que le tocaba por lista.
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 4: CALENDARIO Y EXCEL -->
<h1>4. Cómo ver el calendario y sacar la hoja de Excel</h1>

<p>
Haz clic en la segunda pestaña arriba: <strong>📅 Ver Turnos del Mes</strong>.
</p>

<h2>¿Qué vas a ver aquí?</h2>
<p>
Verás una cuadrícula mensual como un calendario grande donde cada fila es una persona y cada columna es un día del 1 al 31:
</p>

<table class="simple-table">
  <thead>
    <tr>
      <th style="width: 25%;">Color o Símbolo</th>
      <th style="width: 25%;">Nombre</th>
      <th>¿Qué significa en la práctica?</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><span class="badge-color col-turno">■ Rojo</span></td>
      <td><strong>Turno Asignado</strong></td>
      <td>Esa persona está de guardia esa semana (días en rojo).</td>
    </tr>
    <tr>
      <td><span class="badge-color col-da">Naranja DA</span></td>
      <td><strong>Día Administrativo</strong></td>
      <td>Ese día tiene permiso administrativo.</td>
    </tr>
    <tr>
      <td><span class="badge-color col-fl">Violeta FL</span></td>
      <td><strong>Feriado Legal</strong></td>
      <td>Ese día está de vacaciones.</td>
    </tr>
    <tr>
      <td><span class="badge-color col-lic">Turquesa LIC</span></td>
      <td><strong>Licencia Médica</strong></td>
      <td>Ese día está con reposo médico.</td>
    </tr>
    <tr>
      <td><span class="badge-color col-fin">Gris Claro</span></td>
      <td><strong>Fin de Semana</strong></td>
      <td>Son los días sábado y domingo.</td>
    </tr>
  </tbody>
</table>

<h2>Cómo sacar la hoja de Excel para imprimir:</h2>
<div class="step-box">
  <div class="step-number">1</div>
  <div class="step-content">
    <strong>Revisa que el mes sea el correcto</strong>
    <p>Usa los botones <strong>‹ Anterior</strong> o <strong>Siguiente ›</strong> si necesitas cambiar de mes, o pulsa <strong>Hoy</strong> para volver al actual.</p>
  </div>
</div>

<div class="step-box">
  <div class="step-number">2</div>
  <div class="step-content">
    <strong>Pulsa el botón verde: 📊 Exportar Excel</strong>
    <p>Está arriba a la derecha de la barra de navegación del calendario.</p>
  </div>
</div>

<div class="step-box">
  <div class="step-number">3</div>
  <div class="step-content">
    <strong>Elige dónde guardarlo y pulsa "Guardar"</strong>
    <p>El programa te sugiere un nombre claro como <code>turnos_Septiembre_2026.xlsx</code>. Puedes guardarlo en tu Escritorio o donde prefieras.</p>
  </div>
</div>

<div class="note-box note-tip">
  <div class="note-title">📄 El archivo Excel ya viene listo para imprimir</div>
  El Excel viene con título formal, los nombres completos de todos los funcionarios, las columnas finales con el total de turnos de cada uno y la leyenda explicativa al pie. Está configurado de forma horizontal (apaisado) para que al imprimirlo no se corten las hojas.
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 5: CUÁNDO Y CÓMO CERRAR EL MES -->
<h1>5. Cuándo y cómo pulsar "Guardar mes"</h1>

<p>
Esta es la duda más común de los usuarios nuevos. Vamos a dejarla 100% clara:
</p>

<h2>¿Cuál es la diferencia entre "Exportar Excel" y "Guardar mes"?</h2>

<table class="simple-table">
  <thead>
    <tr>
      <th style="width: 30%;">Acción</th>
      <th style="width: 35%;">¿Qué hace?</th>
      <th>¿Cambia la cuenta de turnos?</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>📊 Exportar Excel</strong></td>
      <td>Crea un archivo Excel para mostrarlo, imprimirlo o revisarlo con el equipo.</td>
      <td><strong>NO.</strong> Puedes exportar 20 veces si quieres y la cola de turnos no se mueve ni se altera nada.</td>
    </tr>
    <tr>
      <td><strong>💾 Guardar mes</strong></td>
      <td>Es la <strong>firma definitiva</strong>. Le dice al programa: <em>"Este mes está cerrado y aprobado"</em>.</td>
      <td><strong>SÍ.</strong> Anota este mes en el historial y hace girar la rueda para que el próximo mes empiece quien corresponde.</td>
    </tr>
  </tbody>
</table>

<h2>Pasos para Guardar el Mes con Seguridad:</h2>
<ol>
  <li>Ve a la pestaña <strong>📋 Planificación</strong>.</li>
  <li>Revisa que todas las semanas estén como deben ser.</li>
  <li>Pulsa el botón verde grande abajo a la derecha: <strong>💾 Guardar mes</strong>.</li>
  <li>El programa te mostrará una ventana preguntando: <em>"¿Deseas guardar este mes en el historial?"</em>.</li>
  <li>Pulsa <strong>Sí</strong>.</li>
  <li>¡Listo! El programa guardará todo de forma segura y cambiará automáticamente al siguiente mes para que puedas seguir trabajando si lo necesitas.</li>
</ol>

<div class="note-box note-alert">
  <div class="note-title">⚠️ Si hiciste cambios manuales de guardia</div>
  Si cambiaste a mano alguna guardia con el botón <em>✏️ Cambiar</em>, al guardar el mes el programa:
  <ul style="margin: 6px 0 0 0; padding-left: 18px;">
    <li>Comprobará que tengas conexión a internet.</li>
    <li>Comprobará que todos los funcionarios tengan su correo anotado en Ajustes.</li>
    <li><strong>Enviará automáticamente un correo a todo el equipo</strong> avisando el cambio y el motivo que escribiste para que todos estén enterados.</li>
  </ul>
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 6: ADMINISTRAR EL PERSONAL -->
<h1>6. Cómo agregar o cambiar compañeros (Pestaña "Ajustes")</h1>

<p>
En la pestaña <strong>⚙ Ajustes</strong> puedes gestionar al equipo de trabajo de forma muy intuitiva:
</p>

<h2>1. Agregar un nuevo funcionario al equipo</h2>
<ol>
  <li>Haz clic en el botón verde <strong>＋ Añadir Persona</strong>.</li>
  <li>Escribe su <strong>Nombre Completo</strong> (ejemplo: <code>COM PEREZ JUAN</code> o <code>PRO SOTO MARIA</code>).</li>
  <li>Escribe su <strong>Correo Electrónico</strong> (ejemplo: <code>juan.perez@institucion.cl</code>).</li>
  <li>Pulsa <strong>Guardar</strong>. La persona se agregará automáticamente al final de la lista.</li>
</ol>

<h2>2. Modificar el nombre o correo de alguien</h2>
<p>
Si alguien cambió de correo o hubo un error en su nombre:
</p>
<ol>
  <li>Busca su nombre en la lista de personal.</li>
  <li>Pulsa el botón <strong>Editar</strong> a su derecha.</li>
  <li>Corrige los datos y pulsa <strong>Guardar</strong>.</li>
</ol>
<p>
<em>Tranquilidad:</em> Si cambias un nombre, el programa actualiza automáticamente todos los turnos anteriores para que los nombres en el historial queden impecables.
</p>

<h2>3. Cambiar el orden de la fila de turnos</h2>
<p>
Al lado de cada persona verás dos flechitas:
</p>
<ul>
  <li><strong>⬆ (Subir):</strong> Adelanta a esa persona una posición en la rotación.</li>
  <li><strong>⬇ (Bajar):</strong> Retrasa a esa persona una posición en la rotación.</li>
</ul>

<h2>4. Dar de baja a alguien que se fue del equipo</h2>
<p>
Si un compañero es trasladado o renuncia, pulsa el botón rojo <strong>Eliminar</strong> junto a su nombre.
</p>
<div class="note-box note-tip">
  <div class="note-title">💡 ¿Qué pasa con los turnos que ya hizo en meses pasados?</div>
  <strong>No se pierden.</strong> El programa conserva todo su historial en los meses ya cerrados para que los reportes viejos sigan siendo reales. Solo dejará de convocarlo para los meses futuros.
</div>

<div class="page-break"></div>

<!-- CAPÍTULO 7: PREGUNTAS FRECUENTES -->
<h1>7. Preguntas Frecuentes y Solución de Dudas</h1>

<table class="simple-table">
  <thead>
    <tr>
      <th style="width: 35%;">Pregunta o Problema</th>
      <th>¿Qué debo hacer? (Solución sencilla)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>"El programa me dice que no puede guardar el Excel porque está abierto"</strong></td>
      <td>Tienes el archivo Excel abierto en tu pantalla. Ciérralo en Excel y vuelve a presionar el botón <strong>Exportar Excel</strong> en el programa.</td>
    </tr>
    <tr>
      <td><strong>"Quiero cambiar una persona de una guardia pero no sé por qué"</strong></td>
      <td>El programa te pide obligatoriamente escribir un motivo para que quede constancia y transparencia para la jefatura y los compañeros.</td>
    </tr>
    <tr>
      <td><strong>"Un compañero se fue con licencia de improviso hoy"</strong></td>
      <td>Entra a <strong>Planificación</strong>, busca su nombre, escribe los días de su licencia, marca <strong>LIC</strong> y dale a <strong>＋ Añadir</strong>. El programa lo quitará de la guardia y pondrá a quien le corresponda.</td>
    </tr>
    <tr>
      <td><strong>"¿Se me pueden borrar los datos si se corta la luz?"</strong></td>
      <td><strong>No.</strong> El programa guarda la información con un sistema de seguridad que nunca toca el archivo original hasta asegurarse de que el nuevo se escribió perfecto. Además, crea respaldos automáticos en la carpeta <code>backups/</code>.</td>
    </tr>
    <tr>
      <td><strong>"¿Puedo volver a ver turnos de hace 4 meses?"</strong></td>
      <td><strong>Sí.</strong> Ve a <strong>Ver Turnos del Mes</strong> y navega con el botón <strong>‹ Anterior</strong> o elige el mes en el menú desplegable. Verás exactamente cómo quedó ese mes cerrado.</td>
    </tr>
  </tbody>
</table>

<div style="margin-top: 35pt; background: #f0fdf4; border: 2px solid #86efac; border-radius: 10px; padding: 18px; text-align: center;">
  <strong style="font-size: 12pt; color: #166534;">¡Todo listo para usar el sistema!</strong><br>
  <span style="font-size: 9.5pt; color: #1e293b;">
    Recuerda: Si tienes dudas, abre este manual, sigue los 3 pasos principales y apóyate siempre en la vista previa antes de guardar el mes.
  </span>
</div>

</body>
</html>
"""
    return html


def main():
    print("1. Construyendo Manual de Usuario Simple y Amigable en HTML...")
    html_content = build_simple_html()

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   [OK] Archivo HTML generado en: {HTML_OUTPUT}")

    print("2. Compilando a PDF mediante Chrome Headless...")
    if not os.path.exists(CHROME_PATH):
        print(f"   [!] Error: No se encontro Chrome en {CHROME_PATH}")
        sys.exit(1)

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={PDF_OUTPUT}",
        f"file:///{HTML_OUTPUT.replace(os.sep, '/')}"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   [!] Error al ejecutar Chrome: {result.stderr}")
        sys.exit(1)

    if os.path.exists(PDF_OUTPUT):
        size_kb = os.path.getsize(PDF_OUTPUT) / 1024
        print(f"   [OK] PDF generado exitosamente!")
        print(f"   - Archivo: {PDF_OUTPUT}")
        print(f"   - Tamano: {size_kb:.1f} KB")
    else:
        print("   [!] Error: No se genero el archivo PDF.")
        sys.exit(1)


if __name__ == "__main__":
    main()
