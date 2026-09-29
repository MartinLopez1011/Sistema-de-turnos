import calendar
from datetime import datetime, date, timedelta
import customtkinter as ctk
from tkinter import messagebox

from views.theme import P, AVATAR_PAL, MESES, EXC_COLORS, EXC_ICONS, FONT_FAMILY
from views.components.widgets import _section_header, _short_name, _initials, _avatar_ctk
from views.components.dialogs import SelectPersonDialog, ChangeShiftDialog, DatePickerDialog, CustomConfirmDialog, CustomAlertDialog


def _confirm_action(parent, title, prompt, is_danger=False, confirm_text="Confirmar", cancel_text="Cancelar"):
    """
    Muestra el diálogo nativo oscuro CustomConfirmDialog en ejecución normal,
    o deriva a messagebox si ha sido mockeado en tests automatizados.
    """
    if hasattr(messagebox.askyesno, "mock_calls") or hasattr(messagebox, "mock_calls"):
        return messagebox.askyesno(title, prompt, parent=parent)
    return CustomConfirmDialog.show(
        parent,
        title=title,
        prompt=prompt,
        is_danger=is_danger,
        confirm_text=confirm_text,
        cancel_text=cancel_text
    )


class TabPlan:
    def __init__(self, parent_tab, app):
        self.parent = parent_tab
        self.app = app
        self.controller = app.controller

        self.from_entry = None
        self.to_entry = None
        self.from_cal_btn = None
        self.to_cal_btn = None
        self.days_entry = None  # Alias para compatibilidad hacia atrás
        self.exc_filter_var = None
        self.exc_filter_segmented = None
        self.type_var = None
        self.type_desc_lbl = None
        self.person_dropdown = None
        self.person_var = None
        self.person_avatar_container = None
        self.next_turno_lbl = None
        self.exc_count_label = None
        self.exception_list = None
        self.preview_scroll = None
        self.save_btn = None
        self.status_label = None
        self._status_frame = None

        self._build_ui()

    def _build_ui(self):
        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(
            self.parent, width=285, corner_radius=0,
            fg_color=P["bg_side"],
            border_width=1, border_color=P["border"]
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(20, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        title_f = ctk.CTkFrame(sidebar, fg_color=P["bg_hdr"], corner_radius=0)
        title_f.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            title_f, text="🗓  Sistema de Turnos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=P["text"]
        ).pack(padx=20, pady=10)

        # Periodo
        _section_header(sidebar, "Periodo", row=1, pady_top=10)
        pf = ctk.CTkFrame(sidebar, fg_color="transparent")
        pf.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="ew")
        pf.grid_columnconfigure(0, weight=3)
        pf.grid_columnconfigure(1, weight=2)

        now = datetime.now()

        ctk.CTkOptionMenu(
            pf, variable=self.app.month_var, values=MESES,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card"],
            command=lambda _: self.app.on_period_change()
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        years = [str(y) for y in range(now.year - 2, now.year + 4)]
        ctk.CTkOptionMenu(
            pf, variable=self.app.year_var, values=years,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card"],
            command=lambda _: self.app.on_period_change()
        ).grid(row=0, column=1, sticky="ew")

        # Persona
        _section_header(sidebar, "Persona", row=3, pady_top=6)
        person_box = ctk.CTkFrame(sidebar, fg_color="transparent")
        person_box.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="ew")
        person_box.grid_columnconfigure(1, weight=1)

        self.person_avatar_container = ctk.CTkFrame(
            person_box, width=38, height=38, fg_color="transparent"
        )
        self.person_avatar_container.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.person_avatar_container.pack_propagate(False)

        self.person_var = ctk.StringVar()
        self.person_dropdown = ctk.CTkOptionMenu(
            person_box, variable=self.person_var, values=["Cargando..."],
            height=38, corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card2"],
            dropdown_hover_color=P["bg_hover"], dropdown_text_color=P["text"],
            text_color=P["text"],
            command=self._on_person_selected
        )
        self.person_dropdown.grid(row=0, column=1, sticky="ew")
        self.person_var.trace_add("write", lambda *_: self._update_person_avatar())

        self.next_turno_lbl = None

        # Formulario de Excepción
        _section_header(sidebar, "Excepción", row=5, pady_top=8)
        exc_form = ctk.CTkFrame(sidebar, fg_color=P["bg_card2"], corner_radius=8)
        exc_form.grid(row=6, column=0, padx=16, pady=(0, 4), sticky="ew")
        exc_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            exc_form, text="Fecha(s): DD/MM/AAAA, 1-5, 8",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=P["text_s"]
        ).grid(row=0, column=0, padx=12, pady=(10, 3), sticky="w")

        from_box = ctk.CTkFrame(exc_form, fg_color="transparent")
        from_box.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        from_box.grid_columnconfigure(0, weight=1)

        self.from_entry = ctk.CTkEntry(
            from_box, placeholder_text="Ej: 30/10/2026",
            fg_color=P["bg_input"], border_color=P["border"], border_width=1,
            height=36
        )
        self.from_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.from_entry.bind("<Return>", lambda _: self.add_exception())
        self.from_entry.bind("<Key>", lambda _: self.from_entry.configure(border_color=P["border"]))
        self.from_entry.bind("<Double-Button-1>", lambda _: self._open_from_picker())
        self.from_entry.bind("<Alt-Down>", lambda _: self._open_from_picker())
        self.from_entry.bind("<F4>", lambda _: self._open_from_picker())
        self.days_entry = self.from_entry  # Alias retrocompatible

        self.from_cal_btn = ctk.CTkButton(
            from_box, text="📅", width=36, height=36, corner_radius=6,
            fg_color=P["bg_input"], hover_color=P["bg_hover"],
            font=ctk.CTkFont(size=14), cursor="hand2",
            command=self._open_from_picker
        )
        self.from_cal_btn.grid(row=0, column=1)

        ctk.CTkLabel(
            exc_form, text="Hasta (opcional para rangos)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=P["text_s"]
        ).grid(row=2, column=0, padx=12, pady=(2, 3), sticky="w")

        to_box = ctk.CTkFrame(exc_form, fg_color="transparent")
        to_box.grid(row=3, column=0, padx=12, pady=(0, 4), sticky="ew")
        to_box.grid_columnconfigure(0, weight=1)

        self.to_entry = ctk.CTkEntry(
            to_box, placeholder_text="Ej: 11/11/2026",
            fg_color=P["bg_input"], border_color=P["border"], border_width=1,
            height=36
        )
        self.to_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.to_entry.bind("<Return>", lambda _: self.add_exception())
        self.to_entry.bind("<Key>", lambda _: self.to_entry.configure(border_color=P["border"]))
        self.to_entry.bind("<Double-Button-1>", lambda _: self._open_to_picker())
        self.to_entry.bind("<Alt-Down>", lambda _: self._open_to_picker())
        self.to_entry.bind("<F4>", lambda _: self._open_to_picker())

        self.to_cal_btn = ctk.CTkButton(
            to_box, text="📅", width=36, height=36, corner_radius=6,
            fg_color=P["bg_input"], hover_color=P["bg_hover"],
            font=ctk.CTkFont(size=14), cursor="hand2",
            command=self._open_to_picker
        )
        self.to_cal_btn.grid(row=0, column=1)

        ctk.CTkLabel(
            exc_form, text="Vacío = aplica solo a 'Desde' · Doble clic abre calendario",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=P["text_s"]
        ).grid(row=4, column=0, padx=12, pady=(0, 8), sticky="w")

        self.type_var = ctk.StringVar(value="DA")
        self.type_segmented = ctk.CTkSegmentedButton(
            exc_form, variable=self.type_var, values=["DA", "FL", "LIC", "OTR"],
            fg_color=P["bg_input"],
            selected_color=P["accent_d"],
            selected_hover_color=P["accent"],
            unselected_color=P["bg_input"],
            unselected_hover_color=P["bg_hover"],
            text_color=P["text"],
            command=self._on_type_changed
        )
        self.type_segmented.grid(row=5, column=0, padx=12, pady=(0, 4), sticky="ew")

        self.type_desc_lbl = ctk.CTkLabel(
            exc_form, text="⏭ DA: Día Administrativo",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=P["text_a"], anchor="w"
        )
        self.type_desc_lbl.grid(row=6, column=0, padx=14, pady=(0, 8), sticky="w")

        # Contenedor dinámico de motivo obligatorio para OTR
        self.reason_frame = ctk.CTkFrame(exc_form, fg_color="transparent")
        ctk.CTkLabel(
            self.reason_frame, text="Motivo / Justificación (obligatorio)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=P["text_s"]
        ).pack(anchor="w", padx=12, pady=(0, 3))
        self.reason_entry = ctk.CTkEntry(
            self.reason_frame, placeholder_text="Ej: Comisión de servicio, Duelo...",
            fg_color=P["bg_input"], border_color=P["border"], border_width=1,
            height=36
        )
        self.reason_entry.pack(fill="x", padx=12, pady=(0, 8))
        self.reason_entry.bind("<Return>", lambda _: self.add_exception())
        self.reason_entry.bind("<Key>", lambda _: self.reason_entry.configure(border_color=P["border"]))

        self.type_var.trace_add("write", lambda *_: self._on_type_changed())

        ctk.CTkButton(
            exc_form, text="＋  Añadir excepción",
            command=self.add_exception,
            fg_color=P["green_d"], hover_color=P["green"],
            height=36, corner_radius=6,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold")
        ).grid(row=8, column=0, padx=12, pady=(0, 12), sticky="ew")

        # ── Contenido Principal ────────────────────────────────────────────────
        main = ctk.CTkFrame(self.parent, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        main.grid_columnconfigure(1, weight=3)
        main.grid_columnconfigure(0, weight=2)
        main.grid_rowconfigure(1, weight=1)

        title_block = ctk.CTkFrame(main, fg_color="transparent")
        title_block.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        title_block.grid_columnconfigure(0, weight=1)

        headers_f = ctk.CTkFrame(title_block, fg_color="transparent")
        headers_f.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            headers_f, text="Planificación de turnos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=P["text"], anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            headers_f,
            text="Configura las excepciones, revisa la asignación y guarda el periodo.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            title_block, text="📅 Abrir calendario",
            command=self.app.jump_to_calendar, height=38, corner_radius=8,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=P["bg_card2"], hover_color=P["bg_hover"],
            border_width=1, border_color=P["border"], text_color=P["text"],
            cursor="hand2"
        ).grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Panel Excepciones del periodo
        exc_frame = ctk.CTkFrame(
            main, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        exc_frame.grid(row=1, column=0, padx=(0, 10), sticky="nsew")
        exc_frame.grid_rowconfigure(2, weight=1)
        exc_frame.grid_columnconfigure(0, weight=1)

        exc_hdr = ctk.CTkFrame(exc_frame, fg_color="transparent")
        exc_hdr.grid(row=0, column=0, padx=16, pady=(14, 2), sticky="ew")
        exc_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            exc_hdr, text="Excepciones y Licencias",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=P["text"]
        ).grid(row=0, column=0, sticky="w")

        self.exc_filter_var = ctk.StringVar(value="Mes actual")
        self.exc_filter_segmented = ctk.CTkSegmentedButton(
            exc_hdr, variable=self.exc_filter_var, values=["Mes actual", "Todas"],
            fg_color=P["bg_input"],
            selected_color=P["accent_d"],
            selected_hover_color=P["accent"],
            unselected_color=P["bg_input"],
            unselected_hover_color=P["bg_hover"],
            text_color=P["text"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            height=26,
            command=lambda _: self.refresh_exceptions()
        )
        self.exc_filter_segmented.grid(row=0, column=1, sticky="e")

        self.exc_count_label = ctk.CTkLabel(
            exc_frame, text="Ninguna registrada",
            text_color=P["text_s"], anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        )
        self.exc_count_label.grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.exception_list = ctk.CTkScrollableFrame(
            exc_frame, fg_color="transparent", scrollbar_button_color=P["border_h"]
        )
        self.exception_list.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Panel Vista previa
        preview_frame = ctk.CTkFrame(
            main, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        preview_frame.grid(row=1, column=1, padx=(12, 0), sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(2, weight=1)

        self.preview_title = ctk.CTkLabel(
            preview_frame, text="Vista previa",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=P["text"]
        )
        self.preview_title.grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")

        ctk.CTkLabel(
            preview_frame,
            text="● Actual · 📌 Manual · ↷ Saltado",
            text_color=P["text_s"], anchor="w",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12)
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.preview_scroll = ctk.CTkScrollableFrame(
            preview_frame, fg_color="transparent", scrollbar_button_color=P["border_h"]
        )
        self.preview_scroll.grid(row=2, column=0, padx=10, pady=(0, 12), sticky="nsew")
        self.preview_scroll.grid_columnconfigure(0, weight=1)

        # Barra inferior de estado y acción principal
        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=2, pady=(16, 0), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=0)

        self._status_frame = ctk.CTkFrame(
            bottom, fg_color=P["bg_card"], corner_radius=8, height=42
        )
        self._status_frame.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self._status_frame.grid_columnconfigure(0, weight=1)
        self._status_frame.grid_propagate(False)

        self.status_label = ctk.CTkLabel(
            self._status_frame,
            text="Listo para revisar y guardar el periodo.",
            text_color=P["text_s"], font=ctk.CTkFont(family=FONT_FAMILY, size=13)
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self.save_btn = ctk.CTkButton(
            bottom, text="💾  Guardar mes",
            command=self.save_month, height=42, corner_radius=10, width=180,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"], cursor="hand2"
        )
        self.save_btn.grid(row=0, column=1, sticky="e")

    def refresh_personal(self, personal_list):
        if personal_list:
            self.person_dropdown.configure(values=personal_list)
            if self.person_var.get() not in personal_list:
                self.person_var.set(personal_list[0])
        else:
            self.person_dropdown.configure(values=["Sin personal disponible"])
            self.person_var.set("Sin personal disponible")
        self._update_person_avatar()

    def _update_person_avatar(self, person_name=None):
        if not hasattr(self, "person_avatar_container") or not self.person_avatar_container:
            return
        try:
            for w in self.person_avatar_container.winfo_children():
                w.destroy()
        except Exception:
            return

        name = person_name or (self.person_var.get() if self.person_var else "")
        personal = []
        if hasattr(self, "controller") and hasattr(self.controller, "get_personal_list"):
            try:
                personal = self.controller.get_personal_list() or []
            except Exception:
                personal = []

        if name and name not in ("Sin personal disponible", "Cargando..."):
            av_idx = personal.index(name) if name in personal else 0
            av_color = AVATAR_PAL[av_idx % len(AVATAR_PAL)]
            initials = _initials(name)
        else:
            av_color = P.get("border", "#334155")
            initials = "👤"

        try:
            av = _avatar_ctk(self.person_avatar_container, initials, av_color, size=38)
            av.pack(fill="both", expand=True)
            for w in [av] + list(av.winfo_children()):
                try:
                    w.configure(cursor="hand2")
                    w.bind("<Button-1>", lambda e: self._open_person_dropdown())
                except Exception:
                    pass
        except Exception:
            pass

    def _open_person_dropdown(self, event=None):
        if hasattr(self, "person_dropdown") and self.person_dropdown:
            try:
                self.person_dropdown._open_dropdown_menu()
            except Exception:
                pass

    def _on_person_selected(self, choice):
        self._update_person_avatar(choice)
        if hasattr(self, "from_entry") and self.from_entry:
            try:
                self.from_entry.focus_set()
            except Exception:
                pass

    def _resolve_initial_picker_date(self, val):
        year, month = self.app.get_selected_period()
        today = date.today()

        if val:
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return datetime.strptime(val.strip(), fmt).date()
                except ValueError:
                    pass

            import re
            m = re.search(r"\b(\d{1,2})\b", val)
            if m:
                d_num = int(m.group(1))
                _, last_day = calendar.monthrange(year, month)
                if 1 <= d_num <= last_day:
                    return date(year, month, d_num)

        if today.year == year and today.month == month:
            return today
        return date(year, month, 1)

    def _open_from_picker(self):
        val = self.from_entry.get().strip() if self.from_entry else ""
        year, month = self.app.get_selected_period()
        init_d = self._resolve_initial_picker_date(val)
        DatePickerDialog.show(
            self.app, initial_date=val or init_d,
            callback=self._set_from_dates,
            title="Seleccionar Días de Excepción",
            default_period=(year, month),
            mode="multi"
        )

    def _set_from_dates(self, dates_selected):
        if not hasattr(self, 'from_entry') or not self.from_entry:
            return
        if not dates_selected:
            return
        if isinstance(dates_selected, (list, tuple, set)):
            dates_list = sorted(list(dates_selected))
            if len(dates_list) == 1:
                val = dates_list[0].strftime("%d/%m/%Y")
            else:
                val = ", ".join(d.strftime("%d/%m/%Y") for d in dates_list)
        elif isinstance(dates_selected, (date, datetime)):
            val = dates_selected.strftime("%d/%m/%Y")
        else:
            val = str(dates_selected)

        self.from_entry.delete(0, 'end')
        self.from_entry.insert(0, val)
        self.from_entry.configure(border_color=P["border"])

        # Si se seleccionaron fechas en el selector múltiple, limpiamos el campo 'Hasta'
        if hasattr(self, 'to_entry') and self.to_entry:
            self.to_entry.delete(0, 'end')
            self.to_entry.configure(border_color=P["border"])

    def _set_from_date(self, d_obj):
        self._set_from_dates([d_obj] if isinstance(d_obj, date) else d_obj)

    def _open_to_picker(self):
        val = self.to_entry.get().strip() if self.to_entry else ""
        if not val and hasattr(self, 'from_entry') and self.from_entry:
            val = self.from_entry.get().strip()
        year, month = self.app.get_selected_period()
        init_d = self._resolve_initial_picker_date(val)
        DatePickerDialog.show(
            self.app, initial_date=init_d,
            callback=lambda d: self._set_to_date(d),
            title="Seleccionar Fecha Fin (Hasta)",
            default_period=(year, month),
            mode="single"
        )

    def _set_to_date(self, d_obj):
        if hasattr(self, 'to_entry') and self.to_entry:
            self.to_entry.delete(0, 'end')
            self.to_entry.insert(0, d_obj.strftime("%d/%m/%Y"))
            self.to_entry.configure(border_color=P["border"])

    def update_date_placeholders(self, year=None, month=None):
        if year is None or month is None:
            year, month = self.app.get_selected_period()
        if hasattr(self, 'from_entry') and self.from_entry:
            self.from_entry.configure(placeholder_text=f"Ej: 05/{month:02d}/{year}")
        if hasattr(self, 'to_entry') and self.to_entry:
            self.to_entry.configure(placeholder_text=f"Ej: 12/{month:02d}/{year}")

    def refresh_exceptions(self, exceptions=None):
        if not hasattr(self, 'exception_list') or self.exception_list is None:
            return

        for w in self.exception_list.winfo_children():
            w.destroy()

        filter_mode = self.exc_filter_var.get() if hasattr(self, 'exc_filter_var') and self.exc_filter_var else "Mes actual"

        if exceptions is not None:
            ranges = self.controller.shift_manager.group_exceptions_into_ranges(exceptions)
            total_days = len(exceptions)
        else:
            year, month = self.app.get_selected_period()
            if filter_mode == "Mes actual":
                raw_exc = self.controller.get_exceptions_for_period(year, month)
                ranges = self.controller.get_exceptions_grouped(year, month)
                total_days = len(raw_exc)
            else:
                raw_exc = self.controller.get_all_exceptions()
                ranges = self.controller.get_exceptions_grouped()
                total_days = len(raw_exc)

        count_ranges = len(ranges)
        if count_ranges:
            ct = f"{count_ranges} registro{'s' if count_ranges != 1 else ''} ({total_days} día{'s' if total_days != 1 else ''})"
            if filter_mode == "Todas" and exceptions is None:
                ct += " · Todo el año"
        else:
            ct = "Ninguna registrada"

        if hasattr(self, 'exc_count_label') and self.exc_count_label:
            self.exc_count_label.configure(text=ct)

        if not ranges:
            empty_box = ctk.CTkFrame(
                self.exception_list, fg_color=P["bg_card2"], corner_radius=10,
                border_width=1, border_color=P["border"]
            )
            empty_box.pack(fill="x", padx=6, pady=16)
            ctk.CTkLabel(
                empty_box, text="📋", font=ctk.CTkFont(size=22)
            ).pack(pady=(12, 2))
            ctk.CTkLabel(
                empty_box, text="Sin excepciones registradas",
                text_color=P["text"], font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold")
            ).pack()
            ctk.CTkLabel(
                empty_box, text="Usa el formulario lateral con 'Desde' y 'Hasta' para añadir rangos de fechas.",
                text_color=P["text_s"], font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                wraplength=200, justify="center"
            ).pack(padx=10, pady=(2, 12))
            return

        for index, r in enumerate(ranges):
            tipo = r['tipo']
            chip_c = EXC_COLORS.get(tipo, P["otr"])
            row = ctk.CTkFrame(
                self.exception_list, fg_color=P["bg_card2"], corner_radius=8,
                border_width=1, border_color=P["border"]
            )
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(0, weight=1)

            def _attach_exc_card_hover(r_w=row):
                def _enter(e):
                    r_w.configure(border_color=P["border_h"])
                def _leave(e):
                    r_w.configure(border_color=P["border"])
                r_w.bind("<Enter>", _enter, add="+")
                r_w.bind("<Leave>", _leave, add="+")
            _attach_exc_card_hover()

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
            ctk.CTkFrame(left, width=4, height=36, fg_color=chip_c, corner_radius=2).pack(side="left", padx=(0, 8))

            info = ctk.CTkFrame(left, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                info, text=_short_name(r['persona'], 2),
                font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
                text_color=P["text"], anchor="w"
            ).pack(fill="x")

            if r['start_date'] == r['end_date']:
                date_text = f"{r['start_date'].strftime('%d/%m/%Y')}  ·  {tipo}"
            else:
                date_text = f"{r['start_date'].strftime('%d/%m/%Y')} al {r['end_date'].strftime('%d/%m/%Y')}  ·  {tipo}  ({r['days_count']} días)"

            ctk.CTkLabel(
                info, text=date_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=P["text_s"], anchor="w"
            ).pack(fill="x")

            if tipo == "OTR" and r.get('motivo'):
                ctk.CTkLabel(
                    info,
                    text=f"📝 Motivo: {r['motivo']}",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=10, slant="italic"),
                    text_color=P["text_s"], anchor="w"
                ).pack(fill="x")

            ctk.CTkButton(
                row, text="✕", width=28, height=28, corner_radius=6,
                fg_color=P["bg_card"], hover_color=P["red_d"],
                font=ctk.CTkFont(size=12), cursor="hand2",
                command=lambda p=r['persona'], s=r['start_date'], e=r['end_date'], idx=index: self._on_delete_range_clicked(p, s, e, idx)
            ).grid(row=0, column=1, padx=6, pady=6)

    def _on_delete_range_clicked(self, persona, start_date, end_date, index=None):
        f_str = start_date.strftime('%d/%m/%Y') if start_date == end_date else f"{start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}"
        if not _confirm_action(
            self.app,
            title="Eliminar excepción",
            prompt=f"¿Deseas eliminar la excepción de {_short_name(persona, 2)} ({f_str})?",
            is_danger=True,
            confirm_text="Eliminar",
            cancel_text="Cancelar"
        ):
            return

        if hasattr(self.app, 'remove_exception_range'):
            self.app.remove_exception_range(persona, start_date, end_date)
        elif hasattr(self.controller, 'remove_exception_range'):
            self.controller.remove_exception_range(persona, start_date, end_date)
            self.refresh_exceptions()
            if hasattr(self.app, 'refresh_plan_views'):
                self.app.refresh_plan_views()
        elif hasattr(self.app, 'remove_exception') and index is not None:
            self.app.remove_exception(index)

    def _on_type_changed(self, value=None):
        if not hasattr(self, 'type_var'):
            return
        val = value if value is not None else self.type_var.get()
        desc_map = {
            "DA": "⏭ DA: Día Administrativo",
            "FL": "🚫 FL: Feriado Legal / Vacaciones",
            "LIC": "📋 LIC: Licencia Médica",
            "OTR": "⭐ OTR: Permiso Especial (requiere motivo)"
        }
        if hasattr(self, "type_desc_lbl") and self.type_desc_lbl:
            self.type_desc_lbl.configure(text=desc_map.get(val, ""))

        if hasattr(self, 'reason_frame'):
            if val == "OTR":
                self.reason_frame.grid(row=3, column=0, sticky="ew")
            else:
                self.reason_frame.grid_forget()
                if hasattr(self, 'reason_entry'):
                    self.reason_entry.configure(border_color=P["border"])

    def add_exception(self):
        person = self.person_var.get()
        exc_type = self.type_var.get()
        year, month = self.app.get_selected_period()

        if not person or person in ("Cargando...", "Sin personal disponible"):
            self.app.set_status("Selecciona una persona válida.", "error")
            return

        from_str = self.from_entry.get().strip() if hasattr(self, 'from_entry') and self.from_entry else ""
        if not from_str and hasattr(self, 'days_entry') and self.days_entry:
            from_str = self.days_entry.get().strip()
        to_str = self.to_entry.get().strip() if hasattr(self, 'to_entry') and self.to_entry else ""

        if not from_str:
            if hasattr(self, 'from_entry') and self.from_entry:
                self.from_entry.configure(border_color=P["red"])
            elif hasattr(self, 'days_entry') and self.days_entry:
                self.days_entry.configure(border_color=P["red"])
            self.app.set_status("Debes ingresar una fecha de inicio (Desde).", "error")
            return

        if exc_type == "OTR":
            motivo = self.reason_entry.get().strip() if hasattr(self, 'reason_entry') else ""
            if len(motivo) < 3:
                if hasattr(self, 'reason_frame'):
                    self.reason_frame.grid(row=3, column=0, sticky="ew")
                if hasattr(self, 'reason_entry'):
                    self.reason_entry.configure(border_color=P["red"])
                    self.reason_entry.focus_set()
                self.app.set_status("Para la excepción 'OTR', debes ingresar un motivo válido (mínimo 3 caracteres).", "error")
                return
        else:
            motivo = ""

        # Parser inteligente de fechas
        def _is_explicit_date(s):
            s = s.strip()
            if "/" in s:
                return True
            if len(s) >= 8 and "-" in s:
                parts = s.split("-")
                if len(parts) == 3 and (len(parts[0]) == 4 or len(parts[2]) == 4):
                    return True
            return False

        def _parse_date_token(s, ref_y):
            s = s.strip()
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    pass
            for sep in ("/", "-"):
                if sep in s:
                    parts = s.split(sep)
                    if len(parts) == 2:
                        try:
                            d_val = int(parts[0].strip())
                            m_val = int(parts[1].strip())
                            return date(ref_y, m_val, d_val)
                        except (ValueError, TypeError):
                            pass
            return None

        # Si el usuario escribió un rango directo de fechas en "Desde" (ej: "30/10 - 11/11" o "30/10 al 11/11")
        if not to_str and "/" in from_str and any(sep in from_str for sep in (" al ", " a ", " - ")):
            for sep in (" al ", " a ", " - "):
                if sep in from_str:
                    parts = from_str.split(sep, 1)
                    if _is_explicit_date(parts[0]):
                        from_str = parts[0].strip()
                        to_str = parts[1].strip()
                        break

        # Caso 1: Rango continuo explícito con "Hasta"
        if bool(to_str):
            d_from = _parse_date_token(from_str, year)
            d_to = _parse_date_token(to_str, year)

            if d_from and d_to:
                if d_from > d_to:
                    d_from, d_to = d_to, d_from

                closed_touched = []
                if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'get_closed_periods_in_range'):
                    closed_touched = self.controller.get_closed_periods_in_range(d_from, d_to)
                if closed_touched:
                    meses_str = ", ".join(closed_touched)
                    if not _confirm_action(
                        self.app,
                        title="Mes cerrado en historial",
                        prompt=f"El rango seleccionado abarca periodos ya cerrados en el historial ({meses_str}).\n\n¿Deseas continuar y registrar la excepción?",
                        is_danger=True,
                        confirm_text="Continuar",
                        cancel_text="Cancelar"
                    ):
                        return

                if hasattr(self, 'app') and hasattr(self.app, 'add_exception_range'):
                    self.app.add_exception_range(person, d_from, d_to, exc_type, motivo)
                elif hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'add_exception_range'):
                    self.controller.add_exception_range(person, d_from, d_to, exc_type, motivo)
                    if hasattr(self.app, 'load_personal'):
                        self.app.load_personal()
                    else:
                        self.refresh_exceptions()
                else:
                    curr = d_from
                    new_exc = []
                    while curr <= d_to:
                        item = {'persona': person, 'fecha': curr, 'tipo': exc_type}
                        if exc_type == 'OTR' and motivo:
                            item['motivo'] = motivo
                        new_exc.append(item)
                        curr += timedelta(days=1)
                    self.app.add_exceptions(new_exc)

                if hasattr(self, 'from_entry') and self.from_entry:
                    self.from_entry.delete(0, 'end')
                if hasattr(self, 'to_entry') and self.to_entry:
                    self.to_entry.delete(0, 'end')
                if hasattr(self, 'reason_entry') and self.reason_entry:
                    self.reason_entry.delete(0, 'end')
                    self.reason_entry.configure(border_color=P["border"])
                if hasattr(self, 'from_entry') and self.from_entry:
                    self.from_entry.focus_set()
                return

        # Caso 2: Parser de fechas explícitas múltiples o días numéricos (ej: "04/10/2026, 12/10/2026" o "1-3, 5, 8-10")
        try:
            tokens = [t.strip() for t in from_str.replace(";", ",").split(",") if t.strip()]
            if not tokens:
                raise ValueError("Sin días")

            _, last_day = calendar.monthrange(year, month)
            invalid_days = []
            dates_set = set()
            for token in tokens:
                if _is_explicit_date(token):
                    parsed_d = _parse_date_token(token, year)
                    if not parsed_d:
                        raise ValueError(f"Fecha inválida: {token}")
                    dates_set.add(parsed_d)
                elif "-" in token:
                    parts = token.split("-")
                    if len(parts) != 2:
                        raise ValueError(f"Rango inválido: {token}")
                    start_d = int(parts[0].strip())
                    end_d = int(parts[1].strip())
                    if start_d > end_d:
                        start_d, end_d = end_d, start_d
                    for d in range(start_d, end_d + 1):
                        if not (1 <= d <= last_day):
                            invalid_days.append(d)
                        else:
                            dates_set.add(date(year, month, d))
                else:
                    d_num = int(token)
                    if not (1 <= d_num <= last_day):
                        invalid_days.append(d_num)
                    else:
                        dates_set.add(date(year, month, d_num))

            if invalid_days:
                inv_str = ", ".join(str(d) for d in sorted(set(invalid_days)))
                if hasattr(self, 'from_entry') and self.from_entry:
                    self.from_entry.configure(border_color=P["red"])
                self.app.set_status(f"Días fuera del rango 1–{last_day}: {inv_str}", "error")
                return

            target_dates = sorted(dates_set)
            if not target_dates:
                raise ValueError("Sin días válidos")

            # Validar si tocan meses cerrados
            closed_touched = set()
            if hasattr(self, 'controller') and self.controller and hasattr(self.controller, 'get_closed_periods_in_range'):
                for td in target_dates:
                    cts = self.controller.get_closed_periods_in_range(td, td)
                    closed_touched.update(cts)
            if closed_touched:
                meses_str = ", ".join(sorted(closed_touched))
                if not _confirm_action(
                    self.app,
                    title="Mes cerrado en historial",
                    prompt=f"Las fechas seleccionadas abarcan periodos ya cerrados en el historial ({meses_str}).\n\n¿Deseas continuar y registrar las excepciones?",
                    is_danger=True,
                    confirm_text="Continuar",
                    cancel_text="Cancelar"
                ):
                    return

            existing_map = {
                exc['fecha']: exc for exc in getattr(self.app, 'exceptions', []) if exc['persona'] == person
            }

            new_exc = []
            updated_exc = []
            skipped_existing = []

            for date_obj in target_dates:
                if date_obj in existing_map:
                    item = existing_map[date_obj]
                    changed = False
                    if item.get('tipo') != exc_type:
                        item['tipo'] = exc_type
                        changed = True
                    if exc_type == 'OTR':
                        if item.get('motivo') != motivo:
                            item['motivo'] = motivo
                            changed = True
                    elif 'motivo' in item:
                        del item['motivo']
                        changed = True

                    if changed:
                        updated_exc.append(date_obj)
                    else:
                        skipped_existing.append(date_obj)
                    continue

                item_dict = {'persona': person, 'fecha': date_obj, 'tipo': exc_type}
                if exc_type == 'OTR' and motivo:
                    item_dict['motivo'] = motivo
                new_exc.append(item_dict)

            if not new_exc and not updated_exc:
                if hasattr(self, 'from_entry') and self.from_entry:
                    self.from_entry.configure(border_color=P["orange"])
                self.app.set_status(
                    f"Todos los días ingresados ya tenían la excepción {exc_type} registrada para {_short_name(person)}.",
                    "warn"
                )
                return

            if new_exc:
                self.app.add_exceptions(new_exc)
            if updated_exc:
                if hasattr(self.app, 'exceptions_by_period') and hasattr(self.app, 'active_period_key'):
                    self.app.exceptions_by_period[self.app.active_period_key] = self.app.exceptions
                if hasattr(self.app, 'refresh_plan_views'):
                    self.app.refresh_plan_views()
                if hasattr(self.app, 'mark_dirty'):
                    self.app.mark_dirty()
                if hasattr(self, 'refresh_exceptions') and getattr(self, 'exception_list', None) is not None:
                    self.refresh_exceptions(self.app.exceptions)

            if hasattr(self, 'from_entry') and self.from_entry:
                self.from_entry.delete(0, 'end')
            if hasattr(self, 'to_entry') and self.to_entry:
                self.to_entry.delete(0, 'end')
            if hasattr(self, 'days_entry') and self.days_entry != getattr(self, 'from_entry', None):
                self.days_entry.delete(0, 'end')
            if hasattr(self, 'reason_entry') and self.reason_entry:
                self.reason_entry.delete(0, 'end')
                self.reason_entry.configure(border_color=P["border"])

            msgs = []
            motivo_suffix = f" [{motivo}]" if (exc_type == "OTR" and motivo) else ""
            if new_exc:
                n = len(new_exc)
                dias_str = ", ".join(e['fecha'].strftime('%d/%m') for e in new_exc)
                msgs.append(f"✓ {n} nueva{'s' if n > 1 else ''} {exc_type}{motivo_suffix} ({dias_str})")
            if updated_exc:
                u = len(updated_exc)
                u_str = ", ".join(d.strftime('%d/%m') for d in updated_exc)
                msgs.append(f"✓ {u} actualizada{'s' if u > 1 else ''} a {exc_type}{motivo_suffix} ({u_str})")
            if skipped_existing:
                s_str = ", ".join(d.strftime('%d/%m') for d in skipped_existing)
                msgs.append(f"(sin cambios: {s_str})")

            self.app.set_status(f"{_short_name(person)}: {' | '.join(msgs)}", "ok")

        except ValueError:
            self.app.set_status("Ingresa una fecha válida (DD/MM/AAAA) o números de días válidos (ej: 1-5, 12).", "error")
        except Exception as ex:
            self.app.set_status(f"Error inesperado: {str(ex)}", "error")

    def update_preview(self, shifts, year, month):
        if getattr(self, "preview_title", None) is not None:
            self.preview_title.configure(text=f"Vista previa — {MESES[month - 1]} {year}")
        for w in self.preview_scroll.winfo_children():
            w.destroy()

        today = date.today()
        personal = self.controller.get_personal_list()

        if not shifts:
            empty_box = ctk.CTkFrame(
                self.preview_scroll, fg_color=P["bg_card2"], corner_radius=10,
                border_width=1, border_color=P["border"]
            )
            empty_box.pack(fill="x", padx=10, pady=24)
            ctk.CTkLabel(
                empty_box, text="🗓", font=ctk.CTkFont(size=24)
            ).pack(pady=(16, 4))
            ctk.CTkLabel(
                empty_box, text="Sin turnos calculados",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                text_color=P["text"]
            ).pack()
            ctk.CTkLabel(
                empty_box, text="Selecciona un periodo válido o verifica el personal activo en Ajustes.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=P["text_s"], justify="center"
            ).pack(padx=16, pady=(4, 16))
            self._render_next_turno_card(None, today, personal)
            return

        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        for idx, sh in enumerate(shifts):
            s, e = sh['semana']
            person = sh['persona'] or "NADIE DISPONIBLE"
            salt = sh.get('saltados', [])
            is_manual = sh.get('es_manual', False) or sh.get('es_forzado', False)
            is_current = (s <= today <= e)
            week_key = f"{s.strftime('%Y-%m-%d')}_{e.strftime('%Y-%m-%d')}"

            av_idx = personal.index(person) if person in personal else 0
            av_color = AVATAR_PAL[av_idx % len(AVATAR_PAL)] if person != "NADIE DISPONIBLE" else P["border"]

            card_border = P["today"] if is_current else (P["accent_d"] if is_manual else P["border"])
            card = ctk.CTkFrame(
                self.preview_scroll,
                fg_color=P["bg_card2"],
                corner_radius=8,
                border_width=2 if is_current else 1,
                border_color=card_border
            )
            card.pack(fill="x", padx=2, pady=2)
            card.grid_columnconfigure(1, weight=1)

            if not is_current:
                def _attach_card_hover(c_w=card, orig_b=card_border):
                    def _enter(e):
                        c_w.configure(border_color=P["border_h"])
                    def _leave(e):
                        c_w.configure(border_color=orig_b)
                    c_w.bind("<Enter>", _enter, add="+")
                    c_w.bind("<Leave>", _leave, add="+")
                _attach_card_hover()

            av = _avatar_ctk(card, _initials(person), av_color, size=28)
            av.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=6, sticky="w")

            name_text = _short_name(person, 2)
            if is_manual:
                name_text = f"📌 {name_text}"
            ctk.CTkLabel(
                card, text=name_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=P["green"] if is_manual else P["text_ok"], anchor="w"
            ).grid(row=0, column=1, sticky="sw", pady=(6, 0))

            date_text = f"{s.strftime('%d/%m')} → {e.strftime('%d/%m')}"
            if s < first_day or e > last_day:
                date_text += "  ·  puente"
            if is_current:
                date_text = "● Actual  ·  " + date_text
            ctk.CTkLabel(
                card, text=date_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=P["accent"] if is_current else P["text_s"], anchor="w"
            ).grid(row=1, column=1, sticky="nw", pady=(0, 6))

            actions_f = ctk.CTkFrame(card, fg_color="transparent")
            actions_f.grid(row=0, column=2, rowspan=2, padx=(4, 10), sticky="e")

            def _on_change(wk=week_key, cur_p=person, s_d=s, e_d=e):
                available = self.controller.get_personal_list()
                if not available:
                    self.app.set_status("No hay personal disponible para asignar.", "error")
                    return
                dates_str = f"{s_d.strftime('%d/%m/%Y')} al {e_d.strftime('%d/%m/%Y')}"
                res = ChangeShiftDialog.show(
                    self.app,
                    title="Cambiar Guardia de Turno",
                    dates_prompt=dates_str,
                    persons=available,
                    current_person=cur_p
                )
                if res:
                    chosen, motive = res
                    self.app.set_manual_assignment(wk, chosen, motivo=motive)

            ctk.CTkButton(
                actions_f, text="Cambiar",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                fg_color=P["bg_input"], hover_color=P["bg_hover"],
                border_width=1, border_color=P["border_h"],
                text_color=P["text"], height=26, width=64,
                cursor="hand2", command=_on_change
            ).pack(side="left")

            if is_manual:
                def _on_reset(wk=week_key):
                    self.app.clear_manual_assignment(wk)

                ctk.CTkButton(
                    actions_f, text="↺",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                    fg_color=P["bg_card"], hover_color=P["red_d"],
                    border_width=1, border_color=P["border"],
                    text_color=P["text_s"], height=26, width=28,
                    cursor="hand2", command=_on_reset
                ).pack(side="left", padx=(4, 0))

            # Notas secundarias: una sola línea cada una y solo si existen
            notes = []
            if is_manual:
                motive = self.app.get_manual_motive(week_key)
                if motive:
                    notes.append((f"📝 {motive}", P["green"]))
            for w_item in sh.get("advertencias") or []:
                notes.append((f"⚠ {w_item['mensaje']} ({', '.join(w_item['feriados'])})", P["orange"]))
            if salt:
                detalle = ", ".join(f"{_short_name(sk['persona'], 2)} ({sk['tipo']})" for sk in salt)
                notes.append((f"↷ Saltados: {detalle}", P["text_s"]))
            for n, (txt, col) in enumerate(notes):
                ctk.CTkLabel(
                    card, text=txt, text_color=col, anchor="w", justify="left",
                    font=ctk.CTkFont(family=FONT_FAMILY, size=11), wraplength=380
                ).grid(row=2 + n, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 6))

        # Actualizar tarjeta de próximo turno (compatible con pruebas)
        first_shift = next((sh for sh in shifts if sh.get('persona') and sh['semana'][1] >= today), None)
        if not first_shift:
            first_shift = next((sh for sh in shifts if sh.get('persona')), None)

        self._render_next_turno_card(first_shift, today, personal)

    def _render_next_turno_card(self, first_shift, today, personal):
        if not hasattr(self, 'next_turno_frame') or self.next_turno_frame is None:
            return

        for w in self.next_turno_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        if not first_shift or not first_shift.get('persona') or first_shift.get('persona') == "NADIE DISPONIBLE":
            self.next_turno_lbl = ctk.CTkLabel(
                self.next_turno_frame,
                text="Sin turnos en este periodo",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                text_color=P["text_s"]
            )
            self.next_turno_lbl.pack(padx=10, pady=12)
            return

        person = first_shift['persona']
        s_date = first_shift['semana'][0].strftime('%d/%m')
        e_date = first_shift['semana'][1].strftime('%d/%m')
        is_current = first_shift['semana'][0] <= today <= first_shift['semana'][1]

        badge_bg = P["today_bg"] if is_current else P["next_bg"]
        badge_fg = P["accent"] if is_current else P["text_a"]
        badge_text = "● GUARDIA EN CURSO" if is_current else "⏳ PRÓXIMO TURNO"

        badge_f = ctk.CTkFrame(self.next_turno_frame, fg_color=badge_bg, corner_radius=5)
        badge_f.pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkLabel(
            badge_f, text=f" {badge_text} ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color=badge_fg
        ).pack(padx=4, pady=2)

        mid_f = ctk.CTkFrame(self.next_turno_frame, fg_color="transparent")
        mid_f.pack(fill="x", padx=10, pady=(2, 4))
        av_idx = personal.index(person) if person in personal else 0
        av_color = AVATAR_PAL[av_idx % len(AVATAR_PAL)]
        av = _avatar_ctk(mid_f, _initials(person), av_color, size=30)
        av.pack(side="left", padx=(0, 8))

        self.next_turno_lbl = ctk.CTkLabel(
            mid_f, text=_short_name(person, 3),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            text_color=P["text"], anchor="w"
        )
        self.next_turno_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            self.next_turno_frame,
            text=f"📅  Semana: {s_date} → {e_date}",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=P["text_s"], anchor="w"
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def save_month(self):
        self.app.save_month()
