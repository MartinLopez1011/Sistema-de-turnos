import customtkinter as ctk

from views.theme import P
from views.components.widgets import _short_name, _make_row_hover
from views.components.dialogs import CustomInputDialog, CustomConfirmDialog, PersonFormDialog
from utils.email_notifier import send_notification_webhook, is_valid_email

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
            notif_card, text="📧  Notificaciones por Correo (Webhook Serverless)",
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(
            notif_card,
            text="Cuando se realicen cambios manuales en un turno y se guarde el mes, el sistema avisará\n"
                 "automáticamente a todos los funcionarios vía Google Apps Script (Gmail).",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w", justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        notif_cfg = self.controller.get_notification_settings()
        has_webhook = bool(notif_cfg.get("webhook_url", "").strip()) and notif_cfg.get("activo", True)

        # Indicador de estado de conexión
        status_box = ctk.CTkFrame(notif_card, fg_color="transparent")
        status_box.grid(row=2, column=0, padx=20, pady=(0, 14), sticky="w")

        dot_text = "● Conectado" if has_webhook else "○ No configurado"
        dot_color = P["text_ok"] if has_webhook else P["text_w"]
        desc_text = (
            "Servicio de Google Apps Script vinculado en config.json."
            if has_webhook
            else "Falta configurar webhook_url en config.json para habilitar envíos."
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

        # Caja interactiva para probar con un correo
        test_box = ctk.CTkFrame(
            notif_card, fg_color=P["bg_card2"], corner_radius=8,
            border_width=1, border_color=P["border"]
        )
        test_box.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")
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

        # ── Card 4: Repositorio GitHub ───────────────────────────────────────
        github_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        github_card.grid(row=6, column=0, sticky="ew", pady=(20, 24))
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

    def _test_webhook(self):
        notif_cfg = self.controller.get_notification_settings()
        url = notif_cfg.get("webhook_url", "").strip()
        if not url:
            self.notif_status_label.configure(
                text="⚠ El Webhook no está configurado en config.json.",
                text_color=P["text_e"]
            )
            return

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

        import threading
        self.btn_test_webhook.configure(state="disabled", text="⏳  Enviando...")
        self.notif_status_label.configure(
            text=f"Enviando correo de prueba a {test_email}...",
            text_color=P["text_w"]
        )

        def run_test():
            ok, msg = send_notification_webhook(
                url,
                recipients=[test_email],
                subject="[Sistema de Turnos] Prueba de Notificación Exitosa",
                body_text="Hola,\n\nEste es un correo de prueba enviado desde el Sistema de Turnos para verificar la correcta integración con Google Apps Script.\n\nEl servicio está funcionando correctamente."
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

