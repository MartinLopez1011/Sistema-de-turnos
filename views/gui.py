import os
import sys
import threading
from datetime import datetime, date
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

from views.theme import P, MESES
from views.tabs.tab_plan import TabPlan
from views.tabs.tab_calendar import TabCalendar
from views.tabs.tab_settings import TabSettings
from views.components.dialogs import LoadingModal
from utils.logger import get_logger
from utils.email_notifier import (
    check_internet_connection, format_plain_text_message, format_save_month_message,
    send_notification_webhook, send_email_smtp, is_smtp_configured
)
from utils.notification_queue import NotificationQueue

logger = get_logger("gui")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TurnosApp(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.notification_queue = NotificationQueue(controller.root_path)
        self.title("Sistema de Turnos")
        self.geometry("1280x700")
        self.minsize(1100, 580)
        self.configure(fg_color=P["bg_app"])
        self._setup_icon()

        # Maximizar automáticamente en pantallas pequeñas (ej: laptops 1366x768)
        try:
            if self.winfo_screenwidth() <= 1366 or self.winfo_screenheight() <= 768:
                self.after(150, lambda: self.state('zoomed'))
        except Exception:
            pass

        self.exceptions = []
        self.exceptions_by_period = {}
        self.manual_assignments = {}
        self.manual_assignments_by_period = {}
        self.manual_motives = {}
        self.manual_motives_by_period = {}
        self.active_period_key = None
        self.is_exporting = False
        self.plan_period_dirty = False
        self.calendar_period_override = None
        self._status_fade_job = None

        now = datetime.now()
        self.month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.year_var = ctk.StringVar(value=str(now.year))

        self._setup_ui()
        self.load_personal()
        self.after(500, self._retry_pending_notifications)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        logger.info("Aplicación Sistema de Turnos iniciada correctamente.")

    def _retry_pending_notifications(self):
        pending = self.notification_queue.list_pending()
        if not pending:
            return

        def worker():
            for item in pending:
                success, message = send_notification_webhook(
                    item.get("webhook_url", ""),
                    item.get("recipients", []),
                    item.get("subject", ""),
                    item.get("body", ""),
                )
                if success:
                    self.notification_queue.remove(item.get("queued_at"))
            self.after(
                0,
                lambda: self.set_status(
                    "Notificaciones pendientes procesadas.",
                    "ok",
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _setup_icon(self):
        """Configura el icono de la ventana para desarrollo y producción empaquetada."""
        try:
            possible_paths = []
            if hasattr(sys, '_MEIPASS'):
                possible_paths.append(os.path.join(sys._MEIPASS, "assets", "app_icon.ico"))
                possible_paths.append(os.path.join(sys._MEIPASS, "assets", "app_icon.png"))

            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            possible_paths.append(os.path.join(root_dir, "assets", "app_icon.ico"))
            possible_paths.append(os.path.join(root_dir, "assets", "app_icon.png"))

            if hasattr(self, 'controller') and getattr(self.controller, 'root_path', None):
                possible_paths.append(os.path.join(self.controller.root_path, "assets", "app_icon.ico"))
                possible_paths.append(os.path.join(self.controller.root_path, "assets", "app_icon.png"))

            for path in possible_paths:
                if os.path.exists(path):
                    if path.endswith(".ico"):
                        try:
                            self.iconbitmap(default=path)
                            return
                        except Exception:
                            self.iconbitmap(path)
                            return
                    elif path.endswith(".png"):
                        try:
                            from PIL import ImageTk, Image
                            img = Image.open(path)
                            photo = ImageTk.PhotoImage(img)
                            self.iconphoto(False, photo)
                            self._icon_photo_ref = photo
                            return
                        except Exception:
                            pass
        except Exception as e:
            logger.warning("No se pudo cargar el icono de la ventana: %s", e)

    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(
            self, anchor="nw",
            fg_color=P["bg_app"],
            segmented_button_fg_color=P["bg_hdr"],
            segmented_button_selected_color=P["accent_d"],
            segmented_button_selected_hover_color=P["accent"],
            segmented_button_unselected_color=P["bg_hdr"],
            segmented_button_unselected_hover_color=P["bg_card"],
            command=self._on_tab_change
        )
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Pestañas
        self.raw_tab_plan = self.tabview.add("  📋  Planificación  ")
        self.raw_tab_vista = self.tabview.add("  📅  Ver Turnos del Mes  ")
        self.raw_tab_ajustes = self.tabview.add("  ⚙  Ajustes  ")

        # Controladores modulares de pestaña
        self.tab_plan = TabPlan(self.raw_tab_plan, self)
        self.tab_calendar = TabCalendar(self.raw_tab_vista, self)
        self.tab_settings = TabSettings(self.raw_tab_ajustes, self)

    def _on_tab_change(self, tab_name=None):
        current = tab_name or self.tabview.get()
        if "Ver Turnos" in current:
            if self.plan_period_dirty:
                self.tab_calendar.set_view_period(*self.get_selected_period())
                self.plan_period_dirty = False
            self.tab_calendar.render_turnos_view()

    def jump_to_calendar(self):
        if self.calendar_period_override is not None:
            self.tab_calendar.set_view_period(*self.calendar_period_override)
            self.calendar_period_override = None
        else:
            self.tab_calendar.set_view_period(*self.get_selected_period())

        self.plan_period_dirty = False
        self.tabview.set("  📅  Ver Turnos del Mes  ")
        self._on_tab_change("  📅  Ver Turnos del Mes  ")

    # ── Gestión de Periodo y Excepciones ──────────────────────────────────────
    def get_selected_period(self):
        year = int(self.year_var.get())
        month = MESES.index(self.month_var.get()) + 1
        return year, month

    def get_selected_period_key(self):
        year, month = self.get_selected_period()
        return f"{year}-{month:02d}"

    def _set_ui_locked(self, locked):
        """Bloquea o desbloquea los controles interactivos durante operaciones async."""
        state = "disabled" if locked else "normal"
        try:
            # Bloquear selectores de periodo en sidebar
            for widget in self.tab_plan.parent.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkOptionMenu):
                            child.configure(state=state)
            # Bloquear botón de excepción y entrada de días
            if self.tab_plan.days_entry:
                self.tab_plan.days_entry.configure(state=state)
        except Exception:
            pass

    def on_period_change(self):
        if self.is_exporting:
            return
        if self.active_period_key is not None:
            self.exceptions_by_period[self.active_period_key] = self.exceptions
            self.manual_assignments_by_period[self.active_period_key] = self.manual_assignments
            self.manual_motives_by_period[self.active_period_key] = self.manual_motives
        self.active_period_key = self.get_selected_period_key()
        self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
        self.manual_assignments = self.manual_assignments_by_period.get(self.active_period_key, {}).copy()
        self.manual_motives = self.manual_motives_by_period.get(self.active_period_key, {}).copy()
        self.plan_period_dirty = True
        self.tab_plan.refresh_exceptions(self.exceptions)
        self.refresh_plan_views()

    def load_personal(self):
        self.exceptions_by_period = self.controller.get_saved_exceptions()
        self.manual_assignments_by_period = self.controller.get_saved_manual_assignments()
        self.active_period_key = self.get_selected_period_key()
        self.manual_motives_by_period[self.active_period_key] = self.controller.get_all_manual_motives(self.active_period_key)
        self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
        self.manual_assignments = self.manual_assignments_by_period.get(self.active_period_key, {}).copy()
        self.manual_motives = self.manual_motives_by_period.get(self.active_period_key, {}).copy()

        personal = self.controller.get_personal_list()
        self.tab_plan.refresh_personal(personal)
        self.tab_plan.refresh_exceptions(self.exceptions)
        self.refresh_plan_views()

    def add_exceptions(self, new_exceptions):
        self.exceptions.extend(new_exceptions)
        self.exceptions_by_period[self.active_period_key] = self.exceptions
        self.tab_plan.refresh_exceptions(self.exceptions)
        self.refresh_plan_views()
        self.mark_dirty()

    def remove_exception(self, index):
        if 0 <= index < len(self.exceptions):
            removed = self.exceptions.pop(index)
            self.exceptions_by_period[self.active_period_key] = self.exceptions
            self.tab_plan.refresh_exceptions(self.exceptions)
            self.refresh_plan_views()
            self.mark_dirty()
            self.set_status(f"Excepción eliminada: {removed['fecha'].strftime('%d/%m/%Y')}", "warn")

    def set_manual_assignment(self, week_key, person_name, motivo=""):
        self.manual_assignments[week_key] = person_name
        self.manual_assignments_by_period[self.active_period_key] = self.manual_assignments
        if motivo and str(motivo).strip():
            self.manual_motives[week_key] = str(motivo).strip()
            self.manual_motives_by_period[self.active_period_key] = self.manual_motives
        self.refresh_plan_views()
        self.mark_dirty()
        self.set_status(f"Guardia asignada manualmente: {person_name}", "ok")

    def get_manual_motive(self, week_key):
        return self.manual_motives.get(week_key, "")

    def clear_manual_assignment(self, week_key):
        if week_key in self.manual_assignments:
            del self.manual_assignments[week_key]
            self.manual_assignments_by_period[self.active_period_key] = self.manual_assignments
        if week_key in self.manual_motives:
            del self.manual_motives[week_key]
            self.manual_motives_by_period[self.active_period_key] = self.manual_motives
        self.refresh_plan_views()
        self.mark_dirty()
        self.set_status("Asignación manual revertida a rotación automática.", "info")

    def refresh_plan_views(self):
        year, month = self.get_selected_period()
        shifts = self.controller.preview_shifts(
            year, month, self.exceptions, manual_assignments=self.manual_assignments)
        self.tab_plan.update_preview(shifts, year, month)
        if hasattr(self, "tab_calendar") and self.tab_calendar.vista_scroll:
            self.tab_calendar.render_turnos_view()

    # ── Feedback y Estado ─────────────────────────────────────────────────────
    def set_status(self, text, level="info"):
        if self._status_fade_job is not None:
            try:
                self.after_cancel(self._status_fade_job)
            except Exception:
                pass
            self._status_fade_job = None

        cfg = {
            "info":  (P["text_s"],  P["bg_card"]),
            "ok":    (P["text_ok"], "#063616"),
            "warn":  (P["text_w"],  "#2C1A00"),
            "error": (P["text_e"],  "#2A0808"),
        }
        tc, bg = cfg.get(level, cfg["info"])
        if hasattr(self.tab_plan, "_status_frame") and self.tab_plan._status_frame:
            self.tab_plan._status_frame.configure(fg_color=bg)
            self.tab_plan.status_label.configure(text=text, text_color=tc)

        if level == "ok":
            self._status_fade_job = self.after(
                5000,
                lambda: self.set_status("Listo para revisar y guardar el periodo.", "info")
            )

    def mark_dirty(self):
        if not self.title().startswith("●"):
            self.title("●  Sistema de Turnos")
        if self.tab_plan.save_btn:
            self.tab_plan.save_btn.configure(text="💾  Guardar mes  ●")

    def mark_clean(self):
        self.title("Sistema de Turnos")
        if self.tab_plan.save_btn:
            self.tab_plan.save_btn.configure(text="💾  Guardar mes")

    def _on_close(self):
        if self.is_exporting:
            messagebox.showwarning(
                "Operación en curso",
                "Hay una operación de guardado o envío de correo en curso.\nEspera a que termine antes de cerrar.",
                parent=self
            )
            return
        if self.title().startswith("●"):
            if not messagebox.askyesno(
                "Cambios sin guardar",
                "Hay cambios sin guardar en el periodo actual.\n¿Deseas salir de todas formas?",
                parent=self
            ):
                return
        self.destroy()

    # ── Acciones de Negocio ───────────────────────────────────────────────────
    def save_month(self):
        if self.is_exporting:
            return

        year, month = self.get_selected_period()
        exceptions_snapshot = list(self.exceptions)
        manual_snapshot = dict(self.manual_assignments)
        motives_snapshot = dict(self.manual_motives)

        has_manual = len(manual_snapshot) > 0
        smtp_available = is_smtp_configured()
        webhook_url = ""

        validation_errors = self.controller.validate_month(
            year, month, exceptions_snapshot, manual_assignments=manual_snapshot
        )
        if validation_errors:
            messagebox.showerror(
                "No se puede cerrar el mes",
                "\n".join(f"• {error}" for error in validation_errors),
                parent=self
            )
            return

        if has_manual:
            # 1. Validar que haya un medio de envío configurado (SMTP o Webhook)
            notif_cfg = self.controller.get_notification_settings()
            webhook_url = notif_cfg.get("webhook_url", "").strip()
            if not smtp_available and not webhook_url:
                messagebox.showerror(
                    "Configuración Requerida",
                    "Existen asignaciones manuales en este mes.\n\n"
                    "Para guardar un cambio manual de turno es obligatorio notificar a todos los funcionarios, "
                    "pero no hay ningún servicio de correo configurado.\n\n"
                    "Configura las credenciales SMTP en la pestaña 'Ajustes' o en el archivo .env.",
                    parent=self
                )
                return

            # 2. Validar que el 100% de los funcionarios activos tengan correo
            all_emails_ok, missing_emails = self.controller.validate_all_emails_registered()
            if not all_emails_ok:
                nombres_str = "\n".join(f"  • {nom}" for nom in missing_emails)
                messagebox.showerror(
                    "Correos Incompletos",
                    "Existen asignaciones manuales en este mes y la notificación es obligatoria para todo el equipo.\n\n"
                    f"Los siguientes funcionarios no tienen correo registrado o es inválido:\n{nombres_str}\n\n"
                    "Ingresa a la pestaña 'Ajustes > Gestión de Personal' y completa los correos antes de guardar.",
                    parent=self
                )
                return

            # 3. Validar conexión a Internet
            if not check_internet_connection():
                messagebox.showerror(
                    "Sin Conexión a Internet",
                    "No se puede guardar el mes con cambios manuales sin conexión a Internet.\n\n"
                    "Es obligatorio enviar la notificación de aviso a los funcionarios. "
                    "Verifica tu conexión a Internet e inténtalo nuevamente.",
                    parent=self
                )
                return

        # Determinar si se enviará correo (SMTP disponible = siempre enviar; si no, solo con cambios manuales)
        will_send_email = smtp_available or has_manual
        aviso_correo = ""
        if will_send_email and smtp_available:
            aviso_correo = "\n\n📧 Se enviará el Excel por correo a TODOS los funcionarios."
        elif has_manual:
            aviso_correo = "\n\n⚠ Se enviará una notificación por correo a TODOS los funcionarios."

        confirmed = messagebox.askyesno(
            "Guardar mes",
            f"¿Guardar {MESES[month-1]} {year} en el historial?\n\n"
            f"  • {len(exceptions_snapshot)} excepción{'es' if len(exceptions_snapshot) != 1 else ''} registrada{'s' if len(exceptions_snapshot) != 1 else ''}.\n"
            f"  • {len(manual_snapshot)} asignación{'es' if len(manual_snapshot) != 1 else ''} manual{'es' if len(manual_snapshot) != 1 else ''}."
            f"{aviso_correo}\n\n"
            "La cola avanzará al siguiente mes.",
            parent=self
        )
        if not confirmed:
            return

        self.is_exporting = True
        self._set_ui_locked(True)
        self.tab_plan.save_btn.configure(state="disabled", text="⏳  Guardando...")

        # Modal de carga animado que acompaña todo el proceso
        loading = LoadingModal(
            self,
            title="Guardando mes",
            message=f"Registrando {MESES[month - 1]} {year} en el historial...",
            icon="💾"
        )

        def _commit_and_advance():
            try:
                ok, msg = self.controller.advance_queue(
                    year, month, exceptions_snapshot,
                    manual_assignments=manual_snapshot,
                    manual_motives=motives_snapshot
                )
                if not ok:
                    self.set_status(f"Error: {msg}", "error")
                    return False

                self.exceptions_by_period[self.active_period_key] = exceptions_snapshot
                self.manual_assignments_by_period[self.active_period_key] = manual_snapshot
                self.manual_motives_by_period[self.active_period_key] = motives_snapshot
                self.calendar_period_override = (year, month)
                self.mark_clean()

                # Avanzar el selector al siguiente mes
                next_month = month + 1
                next_year = year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                self.month_var.set(MESES[next_month - 1])
                self.year_var.set(str(next_year))
                self.active_period_key = self.get_selected_period_key()
                self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
                self.manual_assignments = self.manual_assignments_by_period.get(self.active_period_key, {}).copy()
                self.manual_motives = self.manual_motives_by_period.get(self.active_period_key, {}).copy()

                self.tab_plan.refresh_exceptions(self.exceptions)
                self.refresh_plan_views()
                self.set_status("Mes guardado en el historial y cola avanzada.", "ok")
                return True
            except Exception as e:
                logger.error("Error en _commit_and_advance: %s", e, exc_info=True)
                self.set_status(f"Error inesperado al guardar: {e}", "error")
                return False

        # Preparar datos del correo
        recipients = [p['email'].strip() for p in self.controller.get_all_persons() if p.get('email')]

        if has_manual:
            shifts_auto = self.controller.preview_shifts(year, month, exceptions_snapshot, manual_assignments={})
            cambios_detalle = []
            for sh in shifts_auto:
                s_d, e_d = sh['semana']
                wk = f"{s_d.isoformat()}_{e_d.isoformat()}"
                if wk in manual_snapshot:
                    cambios_detalle.append({
                        "semana_texto": f"{s_d.strftime('%d/%m/%Y')} al {e_d.strftime('%d/%m/%Y')}",
                        "anterior": sh.get('persona', 'Sin asignar'),
                        "nuevo": manual_snapshot[wk],
                        "motivo": motives_snapshot.get(wk, "No especificado"),
                        "fecha_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
                    })
            subject = f"[Sistema de Turnos] Modificación de Guardia - {MESES[month - 1]} {year}"
            body_text = format_plain_text_message(MESES[month - 1], year, cambios_detalle)
        else:
            subject = f"[Sistema de Turnos] Planificación {MESES[month - 1]} {year}"
            body_text = format_save_month_message(MESES[month - 1], year)

        # El cierre local es la fuente de verdad.
        self.set_status("Guardando el mes en el historial...", "warn")
        if not _commit_and_advance():
            loading.close()
            self.is_exporting = False
            self._set_ui_locked(False)
            self.tab_plan.save_btn.configure(state="normal", text="💾  Guardar mes")
            return

        if not will_send_email or not recipients:
            loading.close()
            self.is_exporting = False
            self._set_ui_locked(False)
            self.tab_plan.save_btn.configure(state="normal", text="💾  Guardar mes")
            messagebox.showinfo(
                "Mes guardado",
                f"El mes {MESES[month - 1]} {year} ha sido guardado exitosamente en el historial.",
                parent=self
            )
            return

        self.set_status("Mes guardado. Generando Excel y enviando correo...", "warn")
        loading.update_status(
            icon="📊",
            title="Preparando archivo Excel",
            message="Generando la planilla oficial de turnos..."
        )

        def _worker():
            import tempfile
            excel_path = None
            success_send = False
            send_msg = ""
            try:
                # Generar Excel temporal para adjuntar
                nombre_mes = MESES[month - 1]
                temp_dir = tempfile.mkdtemp(prefix="turnos_")
                excel_path = os.path.join(temp_dir, f"turnos_{nombre_mes}_{year}.xlsx")
                self.controller.process_generation(
                    year, month, exceptions_snapshot,
                    manual_assignments=manual_snapshot,
                    target_path=excel_path,
                    manual_motives=motives_snapshot
                )

                dest_desc = f"{len(recipients)} funcionario{'s' if len(recipients) != 1 else ''}"
                loading.update_status(
                    icon="📧",
                    title="Enviando correos",
                    message=f"Enviando correo con Excel adjunto a {dest_desc}..."
                )

                # Intentar envío por SMTP (preferido) o Webhook (fallback)
                if smtp_available:
                    success_send, send_msg = send_email_smtp(
                        recipients, subject, body_text,
                        attachment_path=excel_path
                    )
                else:
                    success_send, send_msg = send_notification_webhook(
                        webhook_url, recipients, subject, body_text
                    )
            except Exception as gen_err:
                logger.error("Error en proceso de generación/envío de correos: %s", gen_err, exc_info=True)
                success_send = False
                send_msg = f"Error en generación o envío: {gen_err}"
            finally:
                # Limpiar archivo temporal
                if excel_path:
                    try:
                        os.remove(excel_path)
                        os.rmdir(os.path.dirname(excel_path))
                    except OSError:
                        pass

            def _on_finish():
                loading.close()
                self.is_exporting = False
                self._set_ui_locked(False)
                self.tab_plan.save_btn.configure(state="normal", text="💾  Guardar mes")

                if not success_send:
                    notif_cfg_inner = self.controller.get_notification_settings()
                    wh_url = notif_cfg_inner.get("webhook_url", "").strip()
                    self.notification_queue.enqueue(
                        wh_url, recipients, subject, body_text, send_msg
                    )
                    self.set_status(f"Error al enviar correo: {send_msg}", "error")
                    messagebox.showwarning(
                        "Mes guardado; notificación pendiente",
                        f"El mes {MESES[month - 1]} {year} fue guardado correctamente, pero no se pudo enviar el aviso:\n\n{send_msg}",
                        parent=self
                    )
                    return

                self.set_status("Mes guardado y correo enviado a todos los funcionarios.", "ok")
                messagebox.showinfo(
                    "Mes guardado y notificado",
                    f"✓ El mes {MESES[month - 1]} {year} fue guardado correctamente en el historial.\n\n"
                    f"✓ Se envió la planilla Excel por correo a {len(recipients)} funcionario{'s' if len(recipients) != 1 else ''}.",
                    parent=self
                )

            self.after(0, _on_finish)

        threading.Thread(target=_worker, daemon=True).start()

    def export_calendar_excel(self):
        if self.is_exporting:
            return

        year, month = self.tab_calendar.get_current_view_period()
        period_key = f"{year}-{month:02d}"
        exceptions = self.exceptions_by_period.get(period_key, [])
        manual_assignments = self.manual_assignments_by_period.get(period_key, {})
        motives = self.manual_motives_by_period.get(period_key, {})
        if period_key == self.active_period_key:
            exceptions = self.exceptions
            manual_assignments = self.manual_assignments
            motives = self.manual_motives
        exceptions_snapshot = list(exceptions)
        manual_snapshot = dict(manual_assignments)
        motives_snapshot = dict(motives)

        nombre_mes = MESES[month - 1]
        default_filename = f"turnos_{nombre_mes}_{year}.xlsx"

        target_file = filedialog.asksaveasfilename(
            parent=self,
            title=f"Guardar calendario Excel - {nombre_mes} {year}",
            initialfile=default_filename,
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel (*.xlsx)", "*.xlsx")]
        )
        if not target_file:
            return

        self.is_exporting = True
        if hasattr(self.tab_calendar, "btn_exportar") and self.tab_calendar.btn_exportar:
            self.tab_calendar.btn_exportar.configure(state="disabled", text="Exportando...")
        self.set_status("Generando archivo Excel...", "warn")

        def _on_export_done(ok, msg):
            self.is_exporting = False
            if hasattr(self.tab_calendar, "btn_exportar") and self.tab_calendar.btn_exportar:
                self.tab_calendar.btn_exportar.configure(state="normal", text="📊  Exportar Excel")
            if ok:
                self.set_status(f"✓ {msg}", "ok")
                messagebox.showinfo("Exportación exitosa", f"Archivo generado:\n{target_file}", parent=self)
            else:
                self.set_status(f"Error: {msg}", "error")
                messagebox.showerror("Error al exportar", msg, parent=self)

        def _thread_worker():
            result = self.controller.process_generation(
                year, month, exceptions_snapshot,
                manual_assignments=manual_snapshot,
                target_path=target_file,
                manual_motives=motives_snapshot
            )
            self.after(0, lambda: _on_export_done(*result))

        threading.Thread(target=_thread_worker, daemon=True).start()
