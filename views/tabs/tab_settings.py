import os
import customtkinter as ctk

from views.theme import P
from views.components.widgets import _short_name, _make_row_hover
from views.components.dialogs import (
    CustomConfirmDialog, PersonFormDialog, SelectPersonDialog
)
from utils.email_notifier import (
    send_notification_webhook, send_email_smtp, is_valid_email,
    is_smtp_configured, test_smtp_connection, get_smtp_config
)
from utils.env_helper import get_env_var, set_env_var

class TabSettings:
    def __init__(self, parent_tab, app):
        self.parent = parent_tab
        self.app = app
        self.controller = app.controller

        self.starting_person_var = None
        self.starting_person_dropdown = None
        self.btn_save_start = None
        self.settings_status_label = None
        self.person_list_frame = None
        self.person_count_badge = None
        self.btn_copy_github = None
        self.backup_status_label = None
        self.audit_textbox = None
        self.btn_edit_smtp = None
        self.btn_save_smtp = None
        self.btn_test_smtp = None
        self.smtp_lock_label = None
        self._smtp_editing = False

        self._build_ui()

    def _build_ui(self):
        self.parent.configure(fg_color=P["bg_app"])
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        wrapper.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            wrapper, text="Ajustes",
            font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            wrapper,
            text="Configuración de rotación, personal del equipo y exportación de reportes.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=P["text_s"], anchor="w"
        ).grid(row=1, column=0, pady=(4, 20), sticky="w")

        # ── Card 1: Persona inicial de la rotación ───────────────────────────
        card1 = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        card1.grid(row=2, column=0, sticky="ew")
        card1.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card1, text="Persona inicial de la rotación",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            card1,
            text="Se usará para el próximo cálculo que no tenga un historial cerrado.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w", wraplength=620
        ).grid(row=1, column=0, padx=20, pady=(0, 14), sticky="w")

        self.starting_person_var = ctk.StringVar(value=self.controller.get_starting_person())
        self.starting_person_dropdown = ctk.CTkOptionMenu(
            card1, variable=self.starting_person_var,
            values=self.controller.get_personal_list(), width=420,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card2"]
        )
        self.starting_person_dropdown.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="w")

        self.btn_save_start = ctk.CTkButton(
            card1, text="Guardar punto de inicio", command=self.save_starting_person,
            height=38, width=220, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"]
        )
        self.btn_save_start.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="w")

        self.settings_status_label = ctk.CTkLabel(
            card1, text="Los cambios se guardan en config.json.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        )
        self.settings_status_label.grid(row=4, column=0, padx=20, pady=(0, 18), sticky="w")

        ctk.CTkLabel(
            wrapper,
            text="Nota: este ajuste no cambia el historial ni los meses ya guardados.\n"
                 "Si hay personas pendientes, esas se atienden antes de iniciar la rotación normal.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], justify="left", anchor="w"
        ).grid(row=3, column=0, pady=(14, 0), sticky="w")

        # ── Card 2: Gestión de Personal ───────────────────────────────────────
        person_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        person_card.grid(row=4, column=0, sticky="ew", pady=(20, 0))
        person_card.grid_columnconfigure(0, weight=1)

        header_p = ctk.CTkFrame(person_card, fg_color="transparent")
        header_p.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 4))
        header_p.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header_p, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box, text="Gestión de Personal",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).pack(side="left")

        self.person_count_badge = ctk.CTkLabel(
            title_box, text="",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=P["text_a"], anchor="w"
        )
        self.person_count_badge.pack(side="left", padx=(12, 0))

        btn_add = ctk.CTkButton(
            header_p, text="＋  Añadir Persona",
            command=self._on_add_person,
            height=32, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"]
        )
        btn_add.pack(side="right")

        self.person_list_frame = ctk.CTkScrollableFrame(
            person_card, fg_color="transparent", height=340,
            scrollbar_button_color=P["border_h"]
        )
        self.person_list_frame.grid(row=1, column=0, padx=10, pady=(10, 20), sticky="nsew")

        self.refresh_person_list()

        # ── Card 3: Configuración de Notificaciones por Correo ────────────────
        notif_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        notif_card.grid(row=5, column=0, sticky="ew", pady=(20, 0))
        notif_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            notif_card, text="📧  Notificaciones por Correo (SMTP)",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            notif_card,
            text="Al guardar el mes se enviará automáticamente el Excel con la planificación a todos\n"
                 "los funcionarios. Para Gmail, usa una Contraseña de Aplicación (no tu contraseña normal).",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w", justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        smtp_cfg = get_smtp_config()
        smtp_ok = is_smtp_configured()

        # Indicador de estado de conexión
        status_box = ctk.CTkFrame(notif_card, fg_color="transparent")
        status_box.grid(row=2, column=0, padx=20, pady=(0, 14), sticky="w")

        dot_text = "● SMTP Configurado" if smtp_ok else "○ SMTP No configurado"
        dot_color = P["text_ok"] if smtp_ok else P["text_w"]
        desc_text = (
            f"Servidor: {smtp_cfg['host']}:{smtp_cfg['port']} — Usuario: {smtp_cfg['user']}"
            if smtp_ok
            else "Configura las credenciales SMTP en los campos de abajo o en el archivo .env"
        )

        self.notif_badge_label = ctk.CTkLabel(
            status_box, text=dot_text,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=dot_color
        )
        self.notif_badge_label.pack(side="left")

        ctk.CTkLabel(
            status_box, text=f"  —  {desc_text}",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"]
        ).pack(side="left")

        # Campos de configuración SMTP
        smtp_form = ctk.CTkFrame(
            notif_card, fg_color=P["bg_card2"], corner_radius=8,
            border_width=1, border_color=P["border"]
        )
        smtp_form.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        smtp_form.grid_columnconfigure(1, weight=1)
        smtp_form.grid_columnconfigure(3, weight=1)

        lbl_font = ctk.CTkFont(family="Inter", size=12)
        entry_h = 34

        ctk.CTkLabel(smtp_form, text="Host SMTP:", font=lbl_font, text_color=P["text_s"]
        ).grid(row=0, column=0, padx=(14, 6), pady=(12, 4), sticky="w")
        self.smtp_host_entry = ctk.CTkEntry(
            smtp_form, height=entry_h, fg_color=P["bg_input"], border_color=P["border"],
            placeholder_text="smtp.gmail.com"
        )
        self.smtp_host_entry.grid(row=0, column=1, padx=(0, 14), pady=(12, 4), sticky="ew")
        if smtp_cfg["host"]:
            self.smtp_host_entry.insert(0, smtp_cfg["host"])

        ctk.CTkLabel(smtp_form, text="Puerto:", font=lbl_font, text_color=P["text_s"]
        ).grid(row=0, column=2, padx=(14, 6), pady=(12, 4), sticky="w")
        self.smtp_port_entry = ctk.CTkEntry(
            smtp_form, height=entry_h, width=80, fg_color=P["bg_input"], border_color=P["border"],
            placeholder_text="587"
        )
        self.smtp_port_entry.grid(row=0, column=3, padx=(0, 14), pady=(12, 4), sticky="w")
        if smtp_cfg["port"]:
            self.smtp_port_entry.insert(0, str(smtp_cfg["port"]))

        ctk.CTkLabel(smtp_form, text="Usuario:", font=lbl_font, text_color=P["text_s"]
        ).grid(row=1, column=0, padx=(14, 6), pady=4, sticky="w")
        self.smtp_user_entry = ctk.CTkEntry(
            smtp_form, height=entry_h, fg_color=P["bg_input"], border_color=P["border"],
            placeholder_text="tu_correo@gmail.com"
        )
        self.smtp_user_entry.grid(row=1, column=1, columnspan=3, padx=(0, 14), pady=4, sticky="ew")
        if smtp_cfg["user"]:
            self.smtp_user_entry.insert(0, smtp_cfg["user"])

        ctk.CTkLabel(smtp_form, text="Contraseña:", font=lbl_font, text_color=P["text_s"]
        ).grid(row=2, column=0, padx=(14, 6), pady=4, sticky="w")
        self.smtp_pass_entry = ctk.CTkEntry(
            smtp_form, height=entry_h, fg_color=P["bg_input"], border_color=P["border"],
            placeholder_text="Contraseña de Aplicación (16 caracteres)", show="•"
        )
        self.smtp_pass_entry.grid(row=2, column=1, columnspan=3, padx=(0, 14), pady=4, sticky="ew")
        if smtp_cfg["password"]:
            self.smtp_pass_entry.insert(0, smtp_cfg["password"])

        smtp_actions = ctk.CTkFrame(smtp_form, fg_color="transparent")
        smtp_actions.grid(row=3, column=0, columnspan=4, padx=14, pady=(8, 4), sticky="w")

        self.btn_edit_smtp = ctk.CTkButton(
            smtp_actions, text="✏️  Editar", command=self._toggle_edit_smtp,
            height=34, width=110, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["accent_d"], hover_color=P["accent"]
        )
        self.btn_edit_smtp.pack(side="left", padx=(0, 8))

        self.btn_save_smtp = ctk.CTkButton(
            smtp_actions, text="💾  Guardar", command=self._save_smtp_config,
            height=34, width=120, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"],
            state="disabled"
        )
        self.btn_save_smtp.pack(side="left", padx=(0, 8))

        self.btn_test_smtp = ctk.CTkButton(
            smtp_actions, text="🔌  Probar Conexión", command=self._test_smtp_connection,
            height=34, width=150, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["bg_card"], hover_color=P["border_h"]
        )
        self.btn_test_smtp.pack(side="left", padx=(0, 8))

        self.smtp_lock_label = ctk.CTkLabel(
            smtp_form,
            text="🔒 Configuración protegida. Pulsa 'Editar' para modificar los datos del servidor.",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=P["text_s"], anchor="w"
        )
        self.smtp_lock_label.grid(row=4, column=0, columnspan=4, padx=14, pady=(0, 10), sticky="w")

        # Iniciar con los campos bloqueados para evitar modificaciones accidentales
        self._smtp_editing = False
        self._set_smtp_fields_state(enabled=False)

        # Caja interactiva para probar envío con un correo
        test_box = ctk.CTkFrame(
            notif_card, fg_color=P["bg_card2"], corner_radius=8,
            border_width=1, border_color=P["border"]
        )
        test_box.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        test_box.grid_columnconfigure(0, weight=1)

        test_title = ctk.CTkLabel(
            test_box, text="Enviar un correo de prueba:",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=P["text"], anchor="w"
        )
        test_title.grid(row=0, column=0, columnspan=2, padx=14, pady=(12, 6), sticky="w")

        self.test_email_entry = ctk.CTkEntry(
            test_box,
            placeholder_text="Ingresa un correo para probar (ej: tu_correo@gmail.com)",
            height=36, fg_color=P["bg_input"], border_color=P["border"]
        )
        self.test_email_entry.grid(row=1, column=0, sticky="ew", padx=(14, 10), pady=(0, 10))

        self.btn_test_webhook = ctk.CTkButton(
            test_box, text="✉  Probar Envío", command=self._test_webhook,
            height=36, width=140, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["accent_d"], hover_color=P["accent"]
        )
        self.btn_test_webhook.grid(row=1, column=1, padx=(0, 14), pady=(0, 10))

        self.notif_status_label = ctk.CTkLabel(
            test_box, text="",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        )
        self.notif_status_label.grid(row=2, column=0, columnspan=2, padx=14, pady=(0, 10), sticky="w")

        # ── Card 4: Backups, auditoría y recuperación ───────────────────────
        operations_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        operations_card.grid(row=6, column=0, sticky="ew", pady=(20, 0))
        operations_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            operations_card, text="🛡  Recuperación y auditoría",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")
        ctk.CTkLabel(
            operations_card,
            text="Crea respaldos manuales, restaura una versión validada y revisa los últimos cambios.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        actions = ctk.CTkFrame(operations_card, fg_color="transparent")
        actions.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="w")
        ctk.CTkButton(
            actions, text="Crear respaldo", command=self._create_backup,
            width=140, height=34, fg_color=P["accent_d"], hover_color=P["accent"]
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions, text="Restaurar respaldo", command=self._restore_backup,
            width=150, height=34, fg_color=P["orange"], hover_color=P["da"],
            text_color="#111418"
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            actions, text="Actualizar auditoría", command=self._refresh_audit,
            width=160, height=34, fg_color=P["bg_card2"], hover_color=P["border_h"]
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Reintentar notificaciones",
            command=self._retry_pending_notifications,
            width=190, height=34, fg_color=P["bg_card2"], hover_color=P["border_h"]
        ).pack(side="left", padx=(8, 0))
        pending = len(self.app.notification_queue.list_pending())
        self.pending_notifications_label = ctk.CTkLabel(
            actions,
            text=f"Notificaciones pendientes: {pending}",
            text_color=P["text_w"] if pending else P["text_s"],
        )
        self.pending_notifications_label.pack(side="left", padx=(14, 0))

        self.backup_status_label = ctk.CTkLabel(
            operations_card, text="", text_color=P["text_s"], anchor="w"
        )
        self.backup_status_label.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="w")
        self.audit_textbox = ctk.CTkTextbox(
            operations_card, height=130, fg_color=P["bg_card2"],
            border_width=1, border_color=P["border"]
        )
        self.audit_textbox.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")
        self._refresh_audit()

        # ── Card 5: Repositorio GitHub ───────────────────────────────────────
        github_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        github_card.grid(row=7, column=0, sticky="ew", pady=(20, 24))
        github_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            github_card, text="🐙  Repositorio del Proyecto (GitHub)",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            github_card,
            text="Código fuente oficial, documentación y control de versiones del sistema.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).grid(row=1, column=0, padx=20, pady=(0, 14), sticky="w")

        link_box = ctk.CTkFrame(
            github_card, fg_color=P["bg_card2"], corner_radius=8,
            border_width=1, border_color=P["border"]
        )
        link_box.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        link_box.grid_columnconfigure(0, weight=1)

        github_url = "https://github.com/MartinLopez1011/Sistema-de-turnos.git"

        link_lbl = ctk.CTkLabel(
            link_box, text=github_url,
            font=ctk.CTkFont(family="Inter", size=12, underline=True),
            text_color=P["text_a"], anchor="w", cursor="hand2"
        )
        link_lbl.grid(row=0, column=0, padx=(14, 10), pady=12, sticky="w")
        link_lbl.bind("<Button-1>", lambda e: self._open_github())

        btn_box = ctk.CTkFrame(link_box, fg_color="transparent")
        btn_box.grid(row=0, column=1, padx=(0, 14), pady=10, sticky="e")

        self.btn_copy_github = ctk.CTkButton(
            btn_box, text="📋  Copiar", command=self._copy_github_link,
            height=32, width=90, corner_radius=6,
            font=ctk.CTkFont(family="Inter", size=12),
            fg_color=P["bg_input"], hover_color=P["border_h"], text_color=P["text"]
        )
        self.btn_copy_github.pack(side="left", padx=(0, 8))

        btn_open_github = ctk.CTkButton(
            btn_box, text="Abrir en GitHub ↗", command=self._open_github,
            height=32, width=140, corner_radius=6,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            fg_color=P["accent_d"], hover_color=P["accent"]
        )
        btn_open_github.pack(side="left")

    def _create_backup(self):
        path = self.controller.create_backup("respaldo_manual")
        if path:
            self.backup_status_label.configure(
                text=f"Respaldo creado: {os.path.basename(path)}",
                text_color=P["text_ok"],
            )
        else:
            self.backup_status_label.configure(
                text="No se pudo crear el respaldo.", text_color=P["text_e"]
            )

    @staticmethod
    def _format_backup_display_name(filename):
        """Formats a backup filename into a human-readable display name.
        
        Example: config_20260925_103900_guardar_septiembre_2026.json
                → 📁 25/09/2026 10:39 — Guardar Septiembre 2026
        """
        import re
        name = filename.replace("config_", "").replace(".json", "")
        # Extract timestamp: YYYYMMDD_HHMMSS
        match = re.match(r"(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})(?:_(.+))?", name)
        if not match:
            return filename
        y, mo, d, h, mi, _, tag = match.groups()
        date_str = f"{d}/{mo}/{y} {h}:{mi}"
        if tag:
            tag_display = tag.replace("_", " ").title()
        else:
            tag_display = "Respaldo"
        return f"📁 {date_str} — {tag_display}"

    def _restore_backup(self):
        backups = self.controller.list_backups()
        if not backups:
            self.backup_status_label.configure(
                text="No existen respaldos disponibles.", text_color=P["text_w"]
            )
            return
        # Build display names and mapping
        display_names = []
        display_to_path = {}
        for path in backups:
            basename = os.path.basename(path)
            display = self._format_backup_display_name(basename)
            display_names.append(display)
            display_to_path[display] = path

        selected = SelectPersonDialog.show(
            self.app,
            "Restaurar respaldo",
            "Selecciona el respaldo que deseas restaurar:",
            display_names,
        )
        if not selected:
            return
        selected_path = display_to_path.get(selected)
        if not selected_path:
            return
        if not CustomConfirmDialog.show(
            self.app,
            "Confirmar restauración",
            "Se creará un respaldo del estado actual antes de restaurar.\n¿Continuar?",
            is_danger=True,
            confirm_text="Restaurar",
        ):
            return
        success, message = self.controller.restore_backup(selected_path)
        self.backup_status_label.configure(
            text=message,
            text_color=P["text_ok"] if success else P["text_e"],
        )
        if success:
            self.refresh_person_list()
            self.app.load_personal()
            self._refresh_audit()

    def _refresh_audit(self):
        if not self.audit_textbox:
            return
        self.audit_textbox.configure(state="normal")
        self.audit_textbox.delete("1.0", "end")
        entries = self.controller.get_audit_entries()
        if not entries:
            self.audit_textbox.insert("end", "Sin operaciones registradas.")
        else:
            for entry in entries:
                self.audit_textbox.insert(
                    "end",
                    f"{entry.get('timestamp', '')}  {entry.get('action', '')}  "
                    f"{entry.get('period', '')}\n",
                )
        self.audit_textbox.configure(state="disabled")

    def _refresh_pending_notifications(self):
        pending = len(self.app.notification_queue.list_pending())
        self.pending_notifications_label.configure(
            text=f"Notificaciones pendientes: {pending}",
            text_color=P["text_w"] if pending else P["text_s"],
        )

    def _retry_pending_notifications(self):
        self.app._retry_pending_notifications()
        self._refresh_pending_notifications()

    def _open_github(self):
        import webbrowser
        webbrowser.open_new_tab("https://github.com/MartinLopez1011/Sistema-de-turnos.git")

    def _copy_github_link(self):
        url = "https://github.com/MartinLopez1011/Sistema-de-turnos.git"
        try:
            self.parent.clipboard_clear()
            self.parent.clipboard_append(url)
            if hasattr(self, "btn_copy_github") and self.btn_copy_github:
                self.btn_copy_github.configure(text="✓  Copiado", fg_color=P["green_d"])
                self.app.after(
                    2000,
                    lambda: self.btn_copy_github.configure(text="📋  Copiar", fg_color=P["bg_input"])
                    if hasattr(self, "btn_copy_github") and self.btn_copy_github
                    else None
                )
        except Exception:
            pass

    def save_starting_person(self):
        person = self.starting_person_var.get()
        if self.controller.set_starting_person(person):
            self.settings_status_label.configure(
                text=f"Punto de inicio guardado: {_short_name(person, 3)}",
                text_color=P["text_ok"]
            )
            self.app.set_status(f"Punto de inicio guardado: {_short_name(person, 3)}", "ok")
            self.app.refresh_plan_views()
            if self.btn_save_start:
                self.btn_save_start.configure(text="✓  ¡Guardado!", fg_color=P["green"])
                self.app.after(2000, lambda: self.btn_save_start.configure(text="Guardar punto de inicio", fg_color=P["green_d"]) if self.btn_save_start else None)
        else:
            self.settings_status_label.configure(
                text="No se pudo guardar la persona inicial.",
                text_color=P["text_e"]
            )

    def refresh_person_list(self):
        for w in self.person_list_frame.winfo_children():
            w.destroy()

        persons = self.controller.get_all_persons()
        if hasattr(self, "person_count_badge") and self.person_count_badge:
            count = len(persons)
            self.person_count_badge.configure(text=f"·  👥 {count} funcionario{'s' if count != 1 else ''} activo{'s' if count != 1 else ''}")
        for i, p in enumerate(persons):
            row_f = ctk.CTkFrame(self.person_list_frame, fg_color=P["bg_row_e"] if i % 2 == 0 else P["bg_row_o"])
            row_f.pack(fill="x", pady=2)

            info_f = ctk.CTkFrame(row_f, fg_color="transparent")
            info_f.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            ctk.CTkLabel(
                info_f, text=f"ID {p['id']}: {p['nombre']}", text_color=P["text"],
                font=ctk.CTkFont(family="Inter", size=13, weight="bold" if i == 0 else "normal")
            ).pack(side="left", padx=(0, 10))

            p_email = p.get('email', '')
            if p_email:
                ctk.CTkLabel(
                    info_f, text=f"✉ {p_email}", text_color=P["text_s"],
                    font=ctk.CTkFont(family="Inter", size=12)
                ).pack(side="left")
            else:
                ctk.CTkLabel(
                    info_f, text="⚠ Sin correo registrado", text_color=P["orange"],
                    font=ctk.CTkFont(family="Inter", size=11, weight="bold")
                ).pack(side="left")

            btn_del = ctk.CTkButton(
                row_f, text="Eliminar", width=60, height=24,
                fg_color=P["red_d"], hover_color=P["red"],
                command=lambda pid=p['id'], pname=p['nombre']: self._on_delete_person(pid, pname)
            )
            btn_del.pack(side="right", padx=10, pady=8)

            btn_edit = ctk.CTkButton(
                row_f, text="Editar", width=60, height=24,
                fg_color=P["accent_d"], hover_color=P["accent"],
                command=lambda pid=p['id'], pname=p['nombre']: self._on_edit_person(pid, pname)
            )
            btn_edit.pack(side="right", padx=10, pady=8)

            btn_down = ctk.CTkButton(
                row_f, text="⬇", width=28, height=24,
                fg_color=P["bg_card2"], hover_color=P["border_h"], text_color=P["text_s"],
                command=lambda pid=p['id']: self._on_move_down(pid)
            )
            btn_down.pack(side="right", padx=(2, 10), pady=8)
            if i == len(persons) - 1:
                btn_down.configure(state="disabled")

            btn_up = ctk.CTkButton(
                row_f, text="⬆", width=28, height=24,
                fg_color=P["bg_card2"], hover_color=P["border_h"], text_color=P["text_s"],
                command=lambda pid=p['id']: self._on_move_up(pid)
            )
            btn_up.pack(side="right", padx=(10, 2), pady=8)
            if i == 0:
                btn_up.configure(state="disabled")

            _make_row_hover(row_f, [(row_f, row_f.cget("fg_color"))])

        personal_names = self.controller.get_personal_list()
        if personal_names:
            self.starting_person_dropdown.configure(values=personal_names)
            if self.starting_person_var.get() not in personal_names:
                self.starting_person_var.set(personal_names[0])
        else:
            self.starting_person_dropdown.configure(values=["Sin personal disponible"])
            self.starting_person_var.set("Sin personal disponible")

    def _on_move_up(self, person_id):
        success, _ = self.controller.move_person_up(person_id)
        if success:
            self.refresh_person_list()
            self.app.load_personal()

    def _on_move_down(self, person_id):
        success, _ = self.controller.move_person_down(person_id)
        if success:
            self.refresh_person_list()
            self.app.load_personal()

    def _set_smtp_fields_state(self, enabled: bool):
        """Habilita o deshabilita los campos de edición SMTP."""
        state = "normal" if enabled else "disabled"
        self.smtp_host_entry.configure(state=state)
        self.smtp_port_entry.configure(state=state)
        self.smtp_user_entry.configure(state=state)
        self.smtp_pass_entry.configure(state=state)

    def _toggle_edit_smtp(self):
        """Alterna entre el modo de solo lectura y el modo de edición de SMTP."""
        if not self._smtp_editing:
            self._smtp_editing = True
            self._set_smtp_fields_state(enabled=True)
            self.btn_edit_smtp.configure(
                text="❌  Cancelar",
                fg_color=P["red_d"],
                hover_color=P["red"]
            )
            self.btn_save_smtp.configure(state="normal")
            self.smtp_lock_label.configure(
                text="🔓 Modo edición activo. Modifica los campos y pulsa 'Guardar'.",
                text_color=P["text_w"]
            )
            self.smtp_host_entry.focus()
        else:
            self._smtp_editing = False
            self._restore_smtp_fields()
            self._set_smtp_fields_state(enabled=False)
            self.btn_edit_smtp.configure(
                text="✏️  Editar",
                fg_color=P["accent_d"],
                hover_color=P["accent"]
            )
            self.btn_save_smtp.configure(state="disabled")
            self.smtp_lock_label.configure(
                text="🔒 Configuración protegida. Pulsa 'Editar' para modificar los datos del servidor.",
                text_color=P["text_s"]
            )

    def _restore_smtp_fields(self):
        """Restaura los valores de los campos SMTP desde la configuración guardada."""
        smtp_cfg = get_smtp_config()
        self._set_smtp_fields_state(enabled=True)
        self.smtp_host_entry.delete(0, "end")
        if smtp_cfg.get("host"):
            self.smtp_host_entry.insert(0, smtp_cfg["host"])

        self.smtp_port_entry.delete(0, "end")
        if smtp_cfg.get("port"):
            self.smtp_port_entry.insert(0, str(smtp_cfg["port"]))

        self.smtp_user_entry.delete(0, "end")
        if smtp_cfg.get("user"):
            self.smtp_user_entry.insert(0, smtp_cfg["user"])

        self.smtp_pass_entry.delete(0, "end")
        if smtp_cfg.get("password"):
            self.smtp_pass_entry.insert(0, smtp_cfg["password"])
        self._set_smtp_fields_state(enabled=False)

    def _save_smtp_config(self):
        """Guarda las credenciales SMTP en el archivo .env."""
        host = self.smtp_host_entry.get().strip()
        port = self.smtp_port_entry.get().strip()
        user = self.smtp_user_entry.get().strip()
        password = self.smtp_pass_entry.get().strip()

        if not host or not port or not user or not password:
            self.notif_status_label.configure(
                text="⚠ Completa todos los campos SMTP antes de guardar.",
                text_color=P["text_w"]
            )
            return

        try:
            int(port)
        except ValueError:
            self.notif_status_label.configure(
                text="⚠ El puerto debe ser un número (ej: 587).",
                text_color=P["text_e"]
            )
            return

        set_env_var("SMTP_HOST", host)
        set_env_var("SMTP_PORT", port)
        set_env_var("SMTP_USER", user)
        set_env_var("SMTP_PASSWORD", password)
        set_env_var("SMTP_USE_TLS", "true")

        # Bloquear nuevamente los campos tras guardar exitosamente
        self._smtp_editing = False
        self._set_smtp_fields_state(enabled=False)
        self.btn_edit_smtp.configure(
            text="✏️  Editar",
            fg_color=P["accent_d"],
            hover_color=P["accent"]
        )
        self.btn_save_smtp.configure(state="disabled")
        self.smtp_lock_label.configure(
            text="🔒 Configuración protegida y guardada correctamente.",
            text_color=P["text_ok"]
        )

        self.notif_status_label.configure(
            text="✓ Configuración SMTP guardada en .env correctamente.",
            text_color=P["text_ok"]
        )
        self.notif_badge_label.configure(
            text="● SMTP Configurado",
            text_color=P["text_ok"]
        )

    def _test_smtp_connection(self):
        """Prueba la conexión SMTP sin enviar correo."""
        # Si estaba en modo edición, guardamos primero
        if getattr(self, "_smtp_editing", False):
            self._save_smtp_config()

        if not is_smtp_configured():
            self.notif_status_label.configure(
                text="⚠ Configura las credenciales SMTP primero.",
                text_color=P["text_w"]
            )
            return

        import threading
        self.btn_test_smtp.configure(state="disabled", text="⏳  Probando...")
        self.notif_status_label.configure(
            text="Verificando conexión SMTP...",
            text_color=P["text_w"]
        )

        def run_test():
            ok, msg = test_smtp_connection()
            def update_ui():
                self.btn_test_smtp.configure(state="normal", text="🔌  Probar Conexión")
                if ok:
                    self.notif_status_label.configure(
                        text=f"✓ {msg}",
                        text_color=P["text_ok"]
                    )
                else:
                    self.notif_status_label.configure(
                        text=f"Error: {msg}",
                        text_color=P["text_e"]
                    )
            self.app.after(0, update_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def _test_webhook(self):
        test_email = self.test_email_entry.get().strip()
        if not test_email:
            self.notif_status_label.configure(
                text="⚠ Ingresa un correo de destino para realizar la prueba.",
                text_color=P["text_w"]
            )
            return

        if not is_valid_email(test_email):
            self.notif_status_label.configure(
                text="⚠ El formato del correo electrónico ingresado no es válido.",
                text_color=P["text_e"]
            )
            return

        use_smtp = is_smtp_configured()
        if not use_smtp:
            notif_cfg = self.controller.get_notification_settings()
            url = notif_cfg.get("webhook_url", "").strip()
            if not url:
                self.notif_status_label.configure(
                    text="⚠ No hay SMTP ni Webhook configurado.",
                    text_color=P["text_e"]
                )
                return

        import threading
        self.btn_test_webhook.configure(state="disabled", text="⏳  Enviando...")
        self.notif_status_label.configure(
            text=f"Enviando correo de prueba a {test_email}...",
            text_color=P["text_w"]
        )

        def run_test():
            subject = "[Sistema de Turnos] Prueba de Notificación Exitosa"
            body = (
                "Hola,\n\nEste es un correo de prueba enviado desde el Sistema de Turnos "
                "para verificar la correcta configuración del servicio de correo.\n\n"
                "El servicio está funcionando correctamente."
            )
            if use_smtp:
                ok, msg = send_email_smtp(
                    recipients=[test_email],
                    subject=subject,
                    body_text=body
                )
            else:
                notif_cfg = self.controller.get_notification_settings()
                url = notif_cfg.get("webhook_url", "").strip()
                ok, msg = send_notification_webhook(
                    url,
                    recipients=[test_email],
                    subject=subject,
                    body_text=body
                )
            def update_ui():
                self.btn_test_webhook.configure(state="normal", text="✉  Probar Envío")
                if ok:
                    self.notif_status_label.configure(
                        text=f"✓ Correo de prueba enviado con éxito a {test_email}.",
                        text_color=P["text_ok"]
                    )
                else:
                    self.notif_status_label.configure(
                        text=f"Error: {msg}",
                        text_color=P["text_e"]
                    )
            self.app.after(0, update_ui)

        threading.Thread(target=run_test, daemon=True).start()

    def _on_add_person(self):
        res = PersonFormDialog.show(self.app, "Añadir Funcionario")
        if res:
            name, email = res
            success, msg = self.controller.add_person(name, email=email)
            if success:
                self.settings_status_label.configure(text=msg, text_color=P["text_ok"])
                self.refresh_person_list()
                self.app.load_personal()
            else:
                self.settings_status_label.configure(text=msg, text_color=P["text_e"])

    def _on_edit_person(self, person_id, current_name):
        current_email = next((p.get('email', '') for p in self.controller.get_all_persons() if p['id'] == person_id), '')
        res = PersonFormDialog.show(
            self.app, "Editar Funcionario",
            initial_name=current_name, initial_email=current_email
        )
        if res:
            new_name, new_email = res
            success, msg = self.controller.edit_person(person_id, new_name, new_email=new_email)
            if success:
                self.settings_status_label.configure(text=msg, text_color=P["text_ok"])
                self.refresh_person_list()
                self.app.load_personal()
            else:
                self.settings_status_label.configure(text=msg, text_color=P["text_e"])

    def _on_delete_person(self, person_id, current_name):
        confirmed = CustomConfirmDialog.show(
            self.app, "Eliminar Persona",
            f"¿Estás seguro que deseas eliminar a {current_name}?\nEsto no afectará el historial pasado.",
            is_danger=True
        )
        if confirmed:
            success, msg = self.controller.remove_person(person_id)
            if success:
                self.settings_status_label.configure(text=msg, text_color=P["text_ok"])
                self.refresh_person_list()
                self.app.load_personal()
            else:
                self.settings_status_label.configure(text=msg, text_color=P["text_e"])
