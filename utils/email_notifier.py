import re
import socket
import json
import urllib.request
import urllib.error
from datetime import datetime

from utils.logger import get_logger

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
    Intenta abrir un socket TCP a servidores DNS públicos conocidos (Google 8.8.8.8 o Cloudflare 1.1.1.1).
    """
    servers = [("8.8.8.8", 53), ("1.1.1.1", 53)]
    for host, port in servers:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, socket.timeout):
            continue
    return False


def format_plain_text_message(mes_nombre: str, anio: int, cambios: list) -> str:
    """
    Construye el cuerpo del correo en texto plano con viñetas claras.
    cambios es una lista de diccionarios:
    [
        {
            "semana_texto": "07/09/2026 al 13/09/2026",
            "anterior": "COM PEREZ JUAN",
            "nuevo": "SBC GONZALEZ MARIA",
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


def mask_url(url: str) -> str:
    """Enmascara la URL para evitar registrar IDs o tokens sensibles en archivos de log."""
    if not url:
        return ""
    if len(url) <= 35:
        return url
    return url[:30] + "..." + url[-8:]

class _GoogleAppsScriptRedirectHandler(urllib.request.HTTPRedirectHandler):
    """
    Maneja la redirección 302 típica de Google Apps Script convirtiendo la redirección a GET
    para recibir la respuesta final JSON.
    """
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        logger.info("[EMAIL] Redirección HTTP %s hacia: %s", code, mask_url(newurl))
        return urllib.request.Request(
            newurl,
            headers={"User-Agent": "SistemaDeTurnos/1.0", "Accept": "application/json"},
            origin_req_host=req.origin_req_host,
            unverifiable=True
        )


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
    """
    logger.info("=" * 60)
    logger.info("[EMAIL] Iniciando envío de notificación...")
    clean_url = webhook_url.strip() if webhook_url else ""
    logger.info("[EMAIL] URL Webhook destino: %s", mask_url(clean_url))

    if not clean_url:
        msg = "La URL del Webhook de notificaciones no está configurada."
        logger.error("[EMAIL] %s", msg)
        return False, msg

    valid_recipients = [r.strip() for r in recipients if is_valid_email(r)]
    logger.info("[EMAIL] Destinatarios válidos (%d): %s", len(valid_recipients), valid_recipients)
    if not valid_recipients:
        msg = "No hay destinatarios válidos con formato de correo correcto."
        logger.error("[EMAIL] %s", msg)
        return False, msg

    logger.info("[EMAIL] Asunto: '%s'", subject)
    logger.info("[EMAIL] Tamaño del cuerpo del correo: %d caracteres", len(body_text))

    payload = {
        "recipients": valid_recipients,
        "subject": subject,
        "body": body_text
    }

    data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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

    opener = urllib.request.build_opener(_GoogleAppsScriptRedirectHandler())

    try:
        logger.info("[EMAIL] Despachando petición POST...")
        with opener.open(req, timeout=timeout) as response:
            status_code = response.getcode()
            logger.info("[EMAIL] Respuesta recibida. Código HTTP: %d", status_code)
            if status_code not in (200, 201, 302):
                msg = f"El servidor respondió con código HTTP inesperado: {status_code}"
                logger.error("[EMAIL] %s", msg)
                return False, msg

            raw_res = response.read().decode("utf-8", errors="replace")
            logger.info("[EMAIL] Respuesta cruda del servidor (primeros 500 chars):\n%s", raw_res[:500])

            # Detectar si Google devolvió HTML (común si la Web App pide login o no está para 'Cualquier persona')
            if "<html" in raw_res.lower() or "<!doctype html" in raw_res.lower():
                msg = (
                    "Google Apps Script devolvió una página HTML en lugar de JSON. "
                    "Causa común: la aplicación web no tiene configurado "
                    "'Quién tiene acceso: Cualquier persona' en script.google.com o faltan autorizaciones."
                )
                logger.error("[EMAIL] %s", msg)
                return False, msg

            try:
                res_json = json.loads(raw_res)
                logger.info("[EMAIL] JSON procesado correctamente: %s", res_json)
                if isinstance(res_json, dict) and res_json.get("status") == "error":
                    err_remote = res_json.get("message", "Error devuelto por Google Apps Script.")
                    logger.error("[EMAIL] Error devuelto por Google Apps Script: %s", err_remote)
                    return False, err_remote
            except json.JSONDecodeError:
                logger.warning("[EMAIL] La respuesta no fue JSON pero devolvió HTTP %d.", status_code)

            logger.info("[EMAIL] [OK] Correo enviado exitosamente a todos los destinatarios.")
            return True, "Notificación enviada correctamente a todos los funcionarios."

    except urllib.error.HTTPError as e:
        err_body = ""
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        msg = f"Error HTTP {e.code}: {e.reason}"
        logger.error("[EMAIL] %s. Detalle: %s", msg, err_body)
        return False, f"{msg} ({err_body[:100]})" if err_body else msg

    except urllib.error.URLError as e:
        msg = f"Error de conexión con el servicio de correo: {e.reason}"
        logger.error("[EMAIL] %s", msg)
        return False, msg

    except TimeoutError:
        msg = "Tiempo de espera agotado al conectar con el servicio de notificaciones."
        logger.error("[EMAIL] %s", msg)
        return False, msg

    except Exception as e:
        msg = f"Error inesperado al enviar correo: {str(e)}"
        logger.error("[EMAIL] %s", msg, exc_info=True)
        return False, msg
