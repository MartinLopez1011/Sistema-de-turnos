/**
 * =========================================================================
 * SISTEMA DE TURNOS — WEBHOOK SERVERLESS PARA NOTIFICACIONES DE CORREO
 * =========================================================================
 * 
 * Este script se ejecuta en Google Apps Script (100% gratuito) y utiliza
 * la cuota de envío de Gmail para despachar notificaciones automáticas.
 * 
 * INSTRUCCIONES DE INSTALACIÓN (3 minutos):
 * -----------------------------------------
 * 1. Ve a https://script.google.com/ e inicia sesión con la cuenta de Gmail
 *    o Google Workspace que enviará los correos.
 * 2. Haz clic en "Nuevo proyecto" (arriba a la izquierda).
 * 3. Ponle un nombre al proyecto, por ejemplo: "Webhook Sistema Turnos".
 * 4. Borra todo el código que aparece en el editor y pega este archivo completo.
 * 5. Haz clic en "Implementar" (botón azul arriba a la derecha) > "Nueva implementación".
 * 6. En el engranaje "Seleccionar tipo", elige "Aplicación web".
 * 7. Configura los siguientes campos:
 *    - Descripción: "Notificaciones Turnos"
 *    - Ejecutar como: "Yo (<tu_correo@gmail.com>)"
 *    - Quién tiene acceso: "Cualquier persona" (IMPORTANTE: para que la app de escritorio pueda enviar el POST)
 * 8. Haz clic en "Implementar", autoriza los permisos requeridos por Google.
 * 9. Copia la "URL de la aplicación web" (termina en /exec) y pégala en
 *    la pestaña "Ajustes" del Sistema de Turnos.
 */

function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "ok",
    service: "Sistema de Turnos Webhook",
    message: "Servicio Webhook de Notificaciones activo y operativo."
  })).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "No se recibieron datos en la petición."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    var payload = JSON.parse(e.postData.contents);
    var recipients = payload.recipients;
    var subject = payload.subject || "[Sistema de Turnos] Notificación de Cambio de Guardia";
    var body = payload.body || "";

    if (!recipients || !Array.isArray(recipients) || recipients.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Lista de destinatarios vacía o inválida."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // Filtrar correos válidos
    var validRecipients = recipients.filter(function(email) {
      return typeof email === 'string' && email.indexOf('@') > 0;
    });

    if (validRecipients.length === 0) {
      return ContentService.createTextOutput(JSON.stringify({
        status: "error",
        message: "Ninguno de los destinatarios proporcionados tiene formato de correo válido."
      })).setMimeType(ContentService.MimeType.JSON);
    }

    // Generar versión HTML profesional para evitar filtros de spam y mejorar legibilidad
    var htmlContent = payload.html_body || buildHtmlTemplate(body, subject);

    // Preparar lista de copia oculta (BCC) si hay más de 1 destinatario
    var bccList = validRecipients.length > 1 ? validRecipients.slice(1).join(',') : null;

    // Intentar envío prioritario con GmailApp (mejor reputación, firma DKIM nativa y registro en 'Enviados')
    var enviadoConExito = false;
    var metodoUsado = "GmailApp";

    try {
      var gmailOptions = {
        name: "Sistema de Gestión de Turnos",
        htmlBody: htmlContent
      };
      if (bccList) {
        gmailOptions.bcc = bccList;
      }
      GmailApp.sendEmail(validRecipients[0], subject, body, gmailOptions);
      enviadoConExito = true;
    } catch (eGmail) {
      Logger.log("GmailApp no disponible o sin permisos (" + eGmail.toString() + "). Reintentando con MailApp...");
      metodoUsado = "MailApp";
      var mailOptions = {
        to: validRecipients[0],
        subject: subject,
        body: body,
        htmlBody: htmlContent,
        name: "Sistema de Gestión de Turnos"
      };
      if (bccList) {
        mailOptions.bcc = bccList;
      }
      MailApp.sendEmail(mailOptions);
      enviadoConExito = true;
    }

    return ContentService.createTextOutput(JSON.stringify({
      status: "ok",
      method: metodoUsado,
      sent_to_count: validRecipients.length,
      recipients: validRecipients,
      message: "Correo enviado exitosamente vía " + metodoUsado + " a " + validRecipients.length + " destinatario(s)."
    })).setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: err.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Función auxiliar para pruebas directas dentro del editor de Apps Script
function testEnvio() {
  var miCorreo = Session.getActiveUser().getEmail();
  var fakeEvent = {
    postData: {
      contents: JSON.stringify({
        recipients: [miCorreo],
        subject: "Prueba de Conexión - Sistema de Turnos",
        body: "Hola, este es un correo de prueba para verificar que el Webhook de Google Apps Script funciona correctamente."
      })
    }
  };
  var res = doPost(fakeEvent);
  Logger.log(res.getContent());
}

/**
 * Convierte el mensaje en un correo HTML estructurado, limpio y corporativo.
 * Esto reduce la tasa de clasificación como spam en Gmail y Outlook.
 */
function buildHtmlTemplate(text, subject) {
  var escaped = String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  var lines = escaped.split('\n');
  var contentHtml = '';

  for (var i = 0; i < lines.length; i++) {
    var line = lines[i].trim();
    if (!line) {
      contentHtml += '<div style="height: 10px;"></div>';
    } else if (line.indexOf('• CAMBIO') === 0) {
      contentHtml += '<div style="margin-top: 14px; margin-bottom: 6px; font-weight: bold; color: #1e3a8a; font-size: 14px; background: #eff6ff; padding: 6px 10px; border-left: 4px solid #3b82f6; border-radius: 4px;">' + line + '</div>';
    } else if (line.indexOf('- ') === 0) {
      contentHtml += '<div style="margin-left: 14px; margin-bottom: 4px; color: #334155; font-size: 13px;">' + line + '</div>';
    } else if (line.indexOf('====') === 0 || line.indexOf('----') === 0) {
      contentHtml += '<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 14px 0;">';
    } else {
      contentHtml += '<div style="margin-bottom: 4px; color: #1e293b; font-size: 13px;">' + line + '</div>';
    }
  }

  return '<!DOCTYPE html>' +
    '<html>' +
    '<head>' +
      '<meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width, initial-scale=1.0">' +
    '</head>' +
    '<body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">' +
      '<div style="max-width: 620px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;">' +
        '<div style="background-color: #0f172a; padding: 18px 24px; border-bottom: 3px solid #2563eb;">' +
          '<h2 style="color: #ffffff; margin: 0; font-size: 17px; font-weight: 600;">' + subject + '</h2>' +
          '<p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 12px;">Sistema de Gestión y Planificación de Turnos</p>' +
        '</div>' +
        '<div style="padding: 24px; line-height: 1.55;">' +
          contentHtml +
        '</div>' +
        '<div style="background-color: #f8fafc; padding: 14px 24px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b; text-align: center;">' +
          'Aviso automático emitido para conocimiento de la dotación. Favor no responder a esta casilla.' +
        '</div>' +
      '</div>' +
    '</body>' +
    '</html>';
}
