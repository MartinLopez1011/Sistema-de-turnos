import customtkinter as ctk

from views.theme import P
from views.components.widgets import _short_name, _make_row_hover
from views.components.dialogs import CustomInputDialog, CustomConfirmDialog

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

        # ── Card 3: Zona de peligro — Reset historial ────────────────────────
        danger_card = ctk.CTkFrame(
            wrapper, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["red_d"]
        )
        danger_card.grid(row=5, column=0, sticky="ew", pady=(20, 0))
        danger_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            danger_card, text="⚠  Zona de peligro",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=P["red"], anchor="w"
        ).grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        ctk.CTkLabel(
            danger_card,
            text="Resetear el historial elimina las semanas cerradas, snapshots y excepciones guardadas.\n"
                 "Las semanas base ('inicio') y la lista de personal se conservan automáticamente. Se crea un respaldo previo.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w", wraplength=580, justify="left"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        ctk.CTkButton(
            danger_card, text="🗑  Resetear historial",
            command=self._reset_historial,
            height=36, width=200, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=P["red_d"], hover_color=P["red"]
        ).grid(row=2, column=0, padx=20, pady=(0, 20), sticky="w")

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

            ctk.CTkLabel(
                row_f, text=f"ID {p['id']}: {p['nombre']}", text_color=P["text"],
                font=ctk.CTkFont(family="Inter", size=13)
            ).pack(side="left", padx=10, pady=8)

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

    def _on_add_person(self):
        name = CustomInputDialog.show(self.app, "Añadir Persona", "Nombre de la persona:")
        if name and name.strip():
            success, msg = self.controller.add_person(name.strip())
            if success:
                self.settings_status_label.configure(text=msg, text_color=P["text_ok"])
                self.refresh_person_list()
                self.app.load_personal()
            else:
                self.settings_status_label.configure(text=msg, text_color=P["text_e"])

    def _on_edit_person(self, person_id, current_name):
        new_name = CustomInputDialog.show(
            self.app, "Editar Persona",
            f"Nuevo nombre para {current_name}:",
            initialvalue=current_name
        )
        if new_name and new_name.strip() and new_name.strip() != current_name:
            success, msg = self.controller.edit_person(person_id, new_name.strip())
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

    def _reset_historial(self):
        confirmed = CustomConfirmDialog.show(
            self.app, "Confirmar reseteo",
            "Estás a punto de resetear el historial y excepciones.\n"
            "Se creará una copia de respaldo automática y se preservarán las semanas base ('inicio').\n\n"
            "¿Deseas continuar?",
            is_danger=True
        )
        if not confirmed:
            self.settings_status_label.configure(text="Reseteo cancelado.", text_color=P["text_w"])
            return

        success, msg = self.controller.reset_historial(preserve_inicio=True)
        if success:
            self.settings_status_label.configure(text=msg, text_color=P["text_ok"])
            self.starting_person_var.set(self.controller.get_starting_person())
            self.app.load_personal()
            self.app.mark_clean()
            self.app.set_status("Historial reseteado correctamente.", "ok")
        else:
            self.settings_status_label.configure(text=msg, text_color=P["text_e"])
            self.app.set_status(f"Error al resetear: {msg}", "error")
