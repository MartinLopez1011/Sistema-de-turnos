import re
import socket
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from utils.logger import get_logger
from utils.env_helper import get_env_var

logger = get_logger("email_notifier")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+$")


def is_valid_email(email: str) -> bool:
    """Verifica si una cadena tiene una sintaxis de correo electrónico válida."""
    if not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def check_internet_connection(timeout: float = 3.0) -> bool:
    """
    Verifica de manera rápida la conectividad a Internet.
    Intenta abrir un socket TCP a puertos HTTPS estándar (443) de Google y Cloudflare.
    El puerto 443 es el estándar para tráfico web y evita bloqueos de cortafuegos en el puerto 53 (DNS).
    """
    servers = [("8.8.8.8", 443), ("1.1.1.1", 443), ("www.google.com", 443)]
    for host, port in servers:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, socket.timeout):
            continue
    return False


def get_smtp_config() -> dict:
    """Obtiene la configuración SMTP desde variables de entorno (.env)."""
    host = get_env_var("SMTP_HOST", "smtp.gmail.com").strip()
    raw_password = get_env_var("SMTP_PASSWORD", "").strip()
    # Si es Gmail y tiene espacios (formato "xxxx xxxx xxxx xxxx"), eliminamos los espacios
    # ya que Google los genera agrupados para lectura pero el servidor SMTP prefiere las 16 letras continuas.
    if "gmail.com" in host.lower():
        password = raw_password.replace(" ", "")
    else:
        password = raw_password

    return {
        "host": host,
        "port": int(get_env_var("SMTP_PORT", "587")),
        "user": get_env_var("SMTP_USER", "").strip(),
        "password": password,
        "use_tls": get_env_var("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes"),
        "from_name": get_env_var("SMTP_FROM_NAME", "Sistema de Turnos").strip(),
    }


def is_smtp_configured() -> bool:
    """Verifica si las credenciales SMTP están configuradas."""
    cfg = get_smtp_config()
    return bool(cfg["host"] and cfg["user"] and cfg["password"])


def test_smtp_connection() -> tuple[bool, str]:
    """Prueba la conexión SMTP sin enviar correo. Retorna (exito, mensaje)."""
    cfg = get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        return False, "Faltan credenciales SMTP. Configura SMTP_USER y SMTP_PASSWORD en el archivo .env."

    try:
        logger.info("[SMTP] Probando conexión a %s:%d...", cfg["host"], cfg["port"])
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15)

        server.login(cfg["user"], cfg["password"])
        server.quit()
        logger.info("[SMTP] Conexión exitosa.")
        return True, "Conexión SMTP verificada correctamente."
    except smtplib.SMTPAuthenticationError:
        msg = "Error de autenticación SMTP. Verifica usuario y contraseña (usa una Contraseña de Aplicación para Gmail)."
        logger.error("[SMTP] %s", msg)
        return False, msg
    except smtplib.SMTPConnectError as e:
        msg = f"No se pudo conectar al servidor SMTP: {e}"
        logger.error("[SMTP] %s", msg)
        return False, msg
    except socket.timeout:
        msg = "Tiempo de espera agotado al conectar con el servidor SMTP."
        logger.error("[SMTP] %s", msg)
        return False, msg
    except Exception as e:
        msg = f"Error inesperado al probar SMTP: {str(e)}"
        logger.error("[SMTP] %s", msg, exc_info=True)
        return False, msg


def format_plain_text_message(mes_nombre: str, anio: int, cambios: list) -> str:
    """
    Construye el cuerpo del correo en texto plano con viñetas claras.
    cambios es una lista de diccionarios:
    [
        {
            "semana_texto": "07/09/2026 al 13/09/2026",
            "anterior": "JUAN PEREZ",
            "nuevo": "MARIA GONZALEZ",
            "motivo": "Permuta acordada",
            "fecha_registro": "22/09/2026 16:30" (opcional)
        },
        ...
    ]
    """
    ahora_str = datetime.now().strftime("%d/%m/%Y a las %H:%M hrs")
    cant_cambios = len(cambios)
    plur_cambio = "modificación" if cant_cambios == 1 else "modificaciones"

    lineas = [
        "SISTEMA DE GESTIÓN DE TURNOS — AVISO DE CAMBIO DE GUARDIA",
        "=" * 56,
        f"Periodo: {mes_nombre} {anio}",
        f"Fecha de notificación: {ahora_str}",
        "",
        f"Se informa al personal que se ha registrado {cant_cambios} {plur_cambio} manual en la planificación de turnos de guardia:",
        ""
    ]

    for i, c in enumerate(cambios, 1):
        semana = c.get("semana_texto", "Semana no especificada")
        anterior = c.get("anterior", "No especificado")
        nuevo = c.get("nuevo", "No especificado")
        motivo = c.get("motivo", "No especificado")
        fecha_reg = c.get("fecha_registro", ahora_str)

        lineas.append(f"• CAMBIO #{i} — Semana {semana}:")
        lineas.append(f"  - Guardia programada original: {anterior}")
        lineas.append(f"  - Nueva guardia asignada:      {nuevo}")
        lineas.append(f"  - Motivo del cambio:           {motivo}")
        lineas.append(f"  - Registrado en sistema:       {fecha_reg}")
        lineas.append("")

    lineas.extend([
        "-" * 56,
        "Este es un aviso automático generado por el Sistema de Gestión de Turnos.",
        "Favor tomar conocimiento para la debida coordinación de los servicios."
    ])

    return "\n".join(lineas)


def format_save_month_message(mes_nombre: str, anio: int) -> str:
    """
    Construye el cuerpo del correo para el envío mensual del Excel (sin cambios manuales).
    """
    ahora_str = datetime.now().strftime("%d/%m/%Y a las %H:%M hrs")

    lineas = [
        "SISTEMA DE GESTIÓN DE TURNOS — PLANIFICACIÓN MENSUAL",
        "=" * 56,
        f"Periodo: {mes_nombre} {anio}",
        f"Fecha de generación: {ahora_str}",
        "",
        "Se adjunta el archivo Excel con la planificación de turnos de guardia",
        f"correspondiente al mes de {mes_nombre} {anio}.",
        "",
        "Favor revisar y tomar conocimiento para la debida coordinación de los servicios.",
        "",
        "-" * 56,
        "Este es un aviso automático generado por el Sistema de Gestión de Turnos.",
    ]

    return "\n".join(lineas)


def send_email_smtp(
    recipients: list,
    subject: str,
    body_text: str,
    attachment_path: str = None,
    timeout: float = 30.0
) -> tuple[bool, str]:
    """
    Envía un correo electrónico vía SMTP con soporte para adjuntos.
    Retorna (exito, mensaje_error_o_confirmacion).
    """
    logger.info("=" * 60)
    logger.info("[SMTP] Iniciando envío de correo...")

    cfg = get_smtp_config()
    if not cfg["user"] or not cfg["password"]:
        msg = "Las credenciales SMTP no están configuradas. Configura SMTP_USER y SMTP_PASSWORD en el archivo .env."
        logger.error("[SMTP] %s", msg)
        return False, msg

    valid_recipients = [r.strip() for r in recipients if is_valid_email(r)]
    logger.info("[SMTP] Destinatarios válidos: %d", len(valid_recipients))
    if not valid_recipients:
        msg = "No hay destinatarios válidos con formato de correo correcto."
        logger.error("[SMTP] %s", msg)
        return False, msg

    logger.info("[SMTP] Asunto: '%s'", subject)
    logger.info("[SMTP] Servidor: %s:%d (TLS=%s)", cfg["host"], cfg["port"], cfg["use_tls"])

    try:
        # Construir el mensaje
        msg = MIMEMultipart()
        msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
        msg["To"] = ", ".join(valid_recipients)
        msg["Subject"] = subject

        # Cuerpo del mensaje
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # Adjuntar archivo si existe
        if attachment_path and os.path.isfile(attachment_path):
            filename = os.path.basename(attachment_path)
            logger.info("[SMTP] Adjuntando archivo: %s (%d bytes)", filename, os.path.getsize(attachment_path))
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)

        # Conectar y enviar
        logger.info("[SMTP] Conectando al servidor...")
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=timeout)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=timeout)

        server.login(cfg["user"], cfg["password"])
        logger.info("[SMTP] Autenticación exitosa. Enviando correo...")

        server.sendmail(cfg["user"], valid_recipients, msg.as_string())
        server.quit()

        logger.info("[SMTP] [OK] Correo enviado exitosamente a %d destinatario(s).", len(valid_recipients))
        return True, "Correo enviado correctamente a todos los funcionarios."

    except smtplib.SMTPAuthenticationError:
        msg = "Error de autenticación SMTP. Verifica usuario y contraseña (usa una Contraseña de Aplicación para Gmail)."
        logger.error("[SMTP] %s", msg)
        return False, msg

    except smtplib.SMTPRecipientsRefused as e:
        msg = f"Destinatarios rechazados por el servidor: {e}"
        logger.error("[SMTP] %s", msg)
        return False, msg

    except smtplib.SMTPException as e:
        msg = f"Error SMTP: {str(e)}"
        logger.error("[SMTP] %s", msg)
        return False, msg

    except socket.timeout:
        msg = "Tiempo de espera agotado al conectar con el servidor SMTP."
        logger.error("[SMTP] %s", msg)
        return False, msg

    except ConnectionRefusedError:
        msg = f"Conexión rechazada por el servidor {cfg['host']}:{cfg['port']}. Verifica host y puerto."
        logger.error("[SMTP] %s", msg)
        return False, msg

    except Exception as e:
        msg = f"Error inesperado al enviar correo: {str(e)}"
        logger.error("[SMTP] %s", msg, exc_info=True)
        return False, msg


# ── Compatibilidad: mantener la función webhook como fallback ─────────────────

def mask_url(url: str) -> str:
    """Enmascara la URL para evitar registrar IDs o tokens sensibles en archivos de log."""
    if not url:
        return ""
    if len(url) <= 35:
        return url
    return url[:30] + "..." + url[-8:]


def send_notification_webhook(
    webhook_url: str,
    recipients: list,
    subject: str,
    body_text: str,
    timeout: float = 35.0
) -> tuple[bool, str]:
    """
    Envía una petición POST JSON al Webhook de Google Apps Script con logging detallado.
    Retorna (exito, mensaje_error_o_confirmacion).

    NOTA: Este método se mantiene como fallback. El método principal es send_email_smtp().
    """
    import json
    import urllib.request
    import urllib.error

    logger.info("=" * 60)
    logger.info("[WEBHOOK] Iniciando envío de notificación (modo legacy)...")
    clean_url = webhook_url.strip() if webhook_url else ""
    logger.info("[WEBHOOK] URL Webhook destino: %s", mask_url(clean_url))

    if not clean_url:
        msg = "La URL del Webhook de notificaciones no está configurada."
        logger.error("[WEBHOOK] %s", msg)
        return False, msg

    valid_recipients = [r.strip() for r in recipients if is_valid_email(r)]
    logger.info("[WEBHOOK] Destinatarios válidos: %d", len(valid_recipients))
    if not valid_recipients:
        msg = "No hay destinatarios válidos con formato de correo correcto."
        logger.error("[WEBHOOK] %s", msg)
        return False, msg

    logger.info("[WEBHOOK] Asunto: '%s'", subject)

    payload = {
        "recipients": valid_recipients,
        "subject": subject,
        "body": body_text
    }

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    class _RedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg_r, headers, newurl):
            logger.info("[WEBHOOK] Redirección HTTP %s hacia: %s", code, mask_url(newurl))
            return urllib.request.Request(
                newurl,
                headers={"User-Agent": "SistemaDeTurnos/1.0", "Accept": "application/json"},
                origin_req_host=req.origin_req_host,
                unverifiable=True
            )

    req = urllib.request.Request(
        clean_url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "SistemaDeTurnos/1.0",
            "Accept": "application/json"
        },
        method="POST"
    )

    opener = urllib.request.build_opener(_RedirectHandler())

    prev_default_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        logger.info("[WEBHOOK] Despachando petición POST...")
        with opener.open(req, timeout=timeout) as response:
            status_code = response.getcode()
            logger.info("[WEBHOOK] Respuesta recibida. Código HTTP: %d", status_code)
            if status_code not in (200, 201, 302):
                msg = f"El servidor respondió con código HTTP inesperado: {status_code}"
                logger.error("[WEBHOOK] %s", msg)
                return False, msg

            raw_res = response.read().decode("utf-8", errors="replace")
            logger.info("[WEBHOOK] Respuesta cruda (primeros 500 chars):\n%s", raw_res[:500])

            if "<html" in raw_res.lower() or "<!doctype html" in raw_res.lower():
                msg = (
                    "Google Apps Script devolvió una página HTML en lugar de JSON. "
                    "Causa común: la aplicación web no tiene configurado "
                    "'Quién tiene acceso: Cualquier persona' en script.google.com o faltan autorizaciones."
                )
                logger.error("[WEBHOOK] %s", msg)
                return False, msg

            try:
                res_json = json.loads(raw_res)
                logger.info("[WEBHOOK] JSON procesado correctamente: %s", res_json)
                if isinstance(res_json, dict) and res_json.get("status") == "error":
                    err_remote = res_json.get("message", "Error devuelto por Google Apps Script.")
                    logger.error("[WEBHOOK] Error devuelto por Google Apps Script: %s", err_remote)
                    return False, err_remote
            except json.JSONDecodeError:
                logger.warning("[WEBHOOK] La respuesta no fue JSON pero devolvió HTTP %d.", status_code)

            logger.info("[WEBHOOK] [OK] Correo enviado exitosamente a todos los destinatarios.")
            return True, "Notificación enviada correctamente a todos los funcionarios."

    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        msg = f"Error HTTP {e.code}: {e.reason}"
        logger.error("[WEBHOOK] %s. Detalle: %s", msg, err_body)
        return False, f"{msg} ({err_body[:100]})" if err_body else msg

    except urllib.error.URLError as e:
        msg = f"Error de conexión con el servicio de correo: {e.reason}"
        logger.error("[WEBHOOK] %s", msg)
        return False, msg

    except TimeoutError:
        msg = "Tiempo de espera agotado al conectar con el servicio de notificaciones."
        logger.error("[WEBHOOK] %s", msg)
        return False, msg

    except Exception as e:
        msg = f"Error inesperado al enviar correo: {str(e)}"
        logger.error("[WEBHOOK] %s", msg, exc_info=True)
        return False, msg
    finally:
        socket.setdefaulttimeout(prev_default_timeout)
