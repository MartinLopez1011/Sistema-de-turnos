---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# External Integrations

**Analysis Date:** 2026-10-06

## APIs & External Services

**Email / SMTP:**
- SMTP Mail Server - Direct email transmission with Excel report attachments to staff members
  - SDK/Client: Python standard library `smtplib`, `email.mime` in `utils/email_notifier.py`
  - Auth: `SMTP_USER`, `SMTP_PASSWORD` via `.env`

**Webhook Notifications:**
- Google Apps Script Webhook - Serverless alternative to trigger email delivery via Google Workspace / Gmail
  - SDK/Client: `urllib.request` in `utils/email_notifier.py`
  - Deployment source: `scripts/google_apps_script.js`
  - Auth: Webhook URL token (`config.json["notificaciones"]["webhook_url"]`)

**Holiday Calendar Engine:**
- Chilean National Holidays - Algorithmic public holiday computation
  - SDK/Client: `holidays` Python package (`utils/chilean_holidays.py`)
  - Auth: None (local algorithmic calculation)

## Data Storage

**Databases:**
- Single JSON document store (`config.json`)
  - Connection: Local filesystem via `models/config_repository.py`
  - Client: Python standard library `json` with atomic write pattern (`.tmp` -> `fsync` -> `os.replace`)

**File Storage:**
- Local filesystem only (`%APPDATA%/Sistema de Turnos` or portable directory adjacent to `.exe`)
- Automated rotated JSON backups (`backups/config_YYYYMMDD_HHMMSS_*.json`) via `ShiftManager.save_config()`
- Offline notification queue (`pending_notifications.json`) via `utils/notification_queue.py`

**Caching:**
- In-memory LRU cache (`functools.lru_cache`) for Chilean holiday calculations (`utils/chilean_holidays.py:16`) and week range string parsing (`models/shift_manager.py:30`)

## Authentication & Identity

**Auth Provider:**
- Custom / Local OS desktop execution (Single-user workstation model)
  - Implementation: No per-user login credentials required; relies on workstation OS login security

## Monitoring & Observability

**Error Tracking:**
- Local logging with global GUI exception handler
  - Implementation: `sys.excepthook` and `TurnosApp.report_callback_exception` in `main.py` routing unhandled errors to `turnos.log` and graphical `messagebox.showerror`

**Logs:**
- Rotating file logging via `logging.handlers.RotatingFileHandler`
  - Location: `turnos.log` (2 MB max size, 3 backup files kept)
  - Handlers: Dual stream (Console `sys.stdout` + UTF-8 `RotatingFileHandler`) in `utils/logger.py`

## CI/CD & Deployment

**Hosting:**
- On-premise / Local client distribution (Windows desktop application)

**CI Pipeline:**
- None configured in repository (manual build via `pyinstaller "Sistema de Turnos.spec"`)

## Environment Configuration

**Required env vars:**
- `SMTP_HOST`: Hostname of the mail server (default: `smtp.gmail.com`)
- `SMTP_PORT`: Port number (default: `587`)
- `SMTP_USER`: Account username / email address
- `SMTP_PASSWORD`: App password or account credential
- `SMTP_USE_TLS`: Boolean TLS flag (`true`/`false`)
- `SMTP_FROM_NAME`: Sender display name (default: `Sistema de Turnos`)
- `VPN_PROVEEDOR`: Telecom / VPN provider name for automated notices
- `VPN_FORMULARIO_URL`: Link to official VPN application form
- `VPN_CORREO_SOPORTE`: Helpdesk contact address

**Secrets location:**
- `.env` file in the application data directory (never committed to git)
- `config.privado.json` for private deployment parameters (gitignored)

## Webhooks & Callbacks

**Incoming:**
- None (client desktop application)

**Outgoing:**
- Google Apps Script Webhook: Dispatches POST JSON payload containing `{ subject, body, recipients, fileName, fileBase64 }` for serverless email dispatch

---

*Integration audit: 2026-10-06*
