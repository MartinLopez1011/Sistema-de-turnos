import calendar
from datetime import datetime, date
import customtkinter as ctk
from tkinter import messagebox

from views.theme import P, MESES, EXC_COLORS
from views.components.widgets import _section_header, _short_name

class TabPlan:
    def __init__(self, parent_tab, app):
        self.parent = parent_tab
        self.app = app
        self.controller = app.controller

        self.days_entry = None
        self.type_var = None
        self.person_dropdown = None
        self.person_var = None
        self.next_turno_lbl = None
        self.exc_count_label = None
        self.exception_list = None
        self.preview_textbox = None
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
            font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
            text_color=P["text"]
        ).pack(padx=20, pady=16)

        # Periodo
        _section_header(sidebar, "Periodo", row=1, pady_top=18)
        pf = ctk.CTkFrame(sidebar, fg_color="transparent")
        pf.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="ew")
        pf.grid_columnconfigure(0, weight=3)
        pf.grid_columnconfigure(1, weight=2)

        now = datetime.now()
        self.app.month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.app.year_var = ctk.StringVar(value=str(now.year))

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
        _section_header(sidebar, "Persona", row=3, pady_top=10)
        self.person_var = ctk.StringVar()
        self.person_dropdown = ctk.CTkOptionMenu(
            sidebar, variable=self.person_var, values=["Cargando..."],
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card"],
            command=lambda _: self.days_entry.focus_set() if self.days_entry else None
        )
        self.person_dropdown.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="ew")

        # Tarjeta Próximo Turno
        self.next_turno_frame = ctk.CTkFrame(sidebar, fg_color=P["bg_input"], corner_radius=8)
        self.next_turno_frame.grid(row=5, column=0, padx=16, pady=(4, 4), sticky="ew")
        self.next_turno_frame.grid_columnconfigure(0, weight=1)
        self.next_turno_lbl = ctk.CTkLabel(
            self.next_turno_frame,
            text="Calculando...",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], wraplength=220, justify="left", anchor="w"
        )
        self.next_turno_lbl.grid(row=0, column=0, padx=10, pady=8, sticky="ew")

        # Formulario de Excepción
        _section_header(sidebar, "Excepción", row=6, pady_top=10)
        exc_form = ctk.CTkFrame(sidebar, fg_color=P["bg_card2"], corner_radius=8)
        exc_form.grid(row=7, column=0, padx=16, pady=(0, 4), sticky="ew")
        exc_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            exc_form, text="Días del mes (ej: 1-5, 12, 19)",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"]
        ).grid(row=0, column=0, padx=12, pady=(10, 3), sticky="w")

        self.days_entry = ctk.CTkEntry(
            exc_form, placeholder_text="Ej: 1-5, 12 o 15, 20-25",
            fg_color=P["bg_input"], border_color=P["border"], border_width=1,
            height=36
        )
        self.days_entry.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.days_entry.bind("<Return>", lambda _: self.add_exception())
        self.days_entry.bind("<Key>", lambda _: self.days_entry.configure(border_color=P["border"]))

        self.type_var = ctk.StringVar(value="DA")
        self.type_segmented = ctk.CTkSegmentedButton(
            exc_form, variable=self.type_var, values=["DA", "FL", "LIC", "OTR", "FOR"],
            fg_color=P["bg_input"],
            selected_color=P["accent_d"],
            selected_hover_color=P["accent"],
            unselected_color=P["bg_input"],
            unselected_hover_color=P["bg_hover"],
            text_color=P["text"]
        )
        self.type_segmented.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

        ctk.CTkButton(
            exc_form, text="＋  Añadir",
            command=self.add_exception,
            fg_color=P["green_d"], hover_color=P["green"],
            height=36, corner_radius=6,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold")
        ).grid(row=3, column=0, padx=12, pady=(0, 12), sticky="ew")

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
            font=ctk.CTkFont(family="Inter", size=26, weight="bold"),
            text_color=P["text"], anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            headers_f,
            text="Configura las excepciones, revisa la asignación y guarda el periodo.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", pady=(4, 0))

        ctk.CTkButton(
            title_block, text="📅 Abrir calendario",
            command=self.app.jump_to_calendar, height=38, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=P["bg_card2"], hover_color=P["bg_hover"],
            border_width=1, border_color=P["border"], text_color=P["text"]
        ).grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Panel Excepciones del periodo
        exc_frame = ctk.CTkFrame(
            main, fg_color=P["bg_card"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        exc_frame.grid(row=1, column=0, padx=(0, 12), sticky="nsew")
        exc_frame.grid_rowconfigure(2, weight=1)
        exc_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            exc_frame, text="Excepciones del periodo",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=P["text"]
        ).grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")

        self.exc_count_label = ctk.CTkLabel(
            exc_frame, text="Ninguna registrada",
            text_color=P["text_s"], anchor="w",
            font=ctk.CTkFont(family="Inter", size=12)
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

        ctk.CTkLabel(
            preview_frame, text="Vista previa",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=P["text"]
        ).grid(row=0, column=0, padx=16, pady=(16, 2), sticky="w")

        ctk.CTkLabel(
            preview_frame,
            text="Se actualiza al cambiar el periodo o excepciones",
            text_color=P["text_s"], anchor="w",
            font=ctk.CTkFont(family="Inter", size=12)
        ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky="ew")

        self.preview_textbox = ctk.CTkTextbox(
            preview_frame, font=ctk.CTkFont(family="Courier", size=13),
            fg_color=P["bg_card2"], border_width=0, text_color=P["text"]
        )
        self.preview_textbox.grid(row=2, column=0, padx=10, pady=(0, 12), sticky="nsew")
        self.preview_textbox.configure(state="disabled")

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
            text_color=P["text_s"], font=ctk.CTkFont(family="Inter", size=13)
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=8, sticky="w")

        self.save_btn = ctk.CTkButton(
            bottom, text="💾  Guardar mes",
            command=self.save_month, height=42, corner_radius=10, width=180,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"]
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

    def refresh_exceptions(self, exceptions):
        for w in self.exception_list.winfo_children():
            w.destroy()

        count = len(exceptions)
        ct = (f"{count} excepción{'es' if count != 1 else ''} registrada{'s' if count != 1 else ''}"
              if count else "Ninguna registrada")
        self.exc_count_label.configure(text=ct)

        if not exceptions:
            ctk.CTkLabel(
                self.exception_list, text="Sin excepciones para este periodo.",
                text_color=P["text_s"], font=ctk.CTkFont(family="Inter", size=12),
                wraplength=220
            ).pack(padx=8, pady=12)
            return

        for index, exc in enumerate(exceptions):
            tipo = exc['tipo']
            chip_c = EXC_COLORS.get(tipo, P["otr"])
            row = ctk.CTkFrame(
                self.exception_list, fg_color=P["bg_card2"], corner_radius=8,
                border_width=1, border_color=P["border"]
            )
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(0, weight=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
            ctk.CTkFrame(left, width=4, height=36, fg_color=chip_c, corner_radius=2).pack(side="left", padx=(0, 8))

            info = ctk.CTkFrame(left, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                info, text=_short_name(exc['persona'], 2),
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=P["text"], anchor="w"
            ).pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"{exc['fecha'].strftime('%d/%m/%Y')}  ·  {tipo}",
                font=ctk.CTkFont(family="Inter", size=11),
                text_color=P["text_s"], anchor="w"
            ).pack(fill="x")

            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=P["bg_card"], hover_color=P["red_d"],
                font=ctk.CTkFont(size=12),
                command=lambda i=index: self.app.remove_exception(i)
            ).grid(row=0, column=1, padx=6, pady=6)

    def add_exception(self):
        person = self.person_var.get()
        days_str = self.days_entry.get()
        exc_type = self.type_var.get()
        year, month = self.app.get_selected_period()

        if not person or person in ("Cargando...", "Sin personal disponible"):
            self.app.set_status("Selecciona una persona válida.", "error")
            return
        if not days_str.strip():
            self.days_entry.configure(border_color=P["red"])
            self.app.set_status("Debes ingresar al menos un día.", "error")
            return

        today = date.today()
        if date(year, month, 1) < date(today.year, today.month, 1):
            if not messagebox.askyesno(
                "Mes pasado",
                f"Estás agregando una excepción en {MESES[month-1]} {year}, que ya pasó.\n¿Continuar de todas formas?",
                parent=self.app
            ):
                return

        try:
            tokens = [t.strip() for t in days_str.replace(";", ",").split(",") if t.strip()]
            if not tokens:
                raise ValueError("Sin días")

            days_set = set()
            for token in tokens:
                if "-" in token:
                    parts = token.split("-")
                    if len(parts) != 2:
                        raise ValueError(f"Rango inválido: {token}")
                    start_d = int(parts[0].strip())
                    end_d = int(parts[1].strip())
                    if start_d > end_d:
                        start_d, end_d = end_d, start_d
                    for d in range(start_d, end_d + 1):
                        days_set.add(d)
                else:
                    days_set.add(int(token))

            raw_days = sorted(days_set)
            if not raw_days:
                raise ValueError("Sin días")

            _, last_day = calendar.monthrange(year, month)
            invalid_days = [d for d in raw_days if not (1 <= d <= last_day)]
            if invalid_days:
                inv_str = ", ".join(str(d) for d in invalid_days)
                self.days_entry.configure(border_color=P["red"])
                self.app.set_status(f"Días fuera del rango 1–{last_day}: {inv_str}", "error")
                return

            existing_dates = {
                exc['fecha'] for exc in self.app.exceptions if exc['persona'] == person
            }

            new_exc = []
            skipped_existing = []

            for day in raw_days:
                date_obj = datetime(year, month, day).date()
                if date_obj in existing_dates:
                    skipped_existing.append(date_obj)
                    continue
                new_exc.append({'persona': person, 'fecha': date_obj, 'tipo': exc_type})

            if not new_exc:
                self.days_entry.configure(border_color=P["orange"])
                self.app.set_status(
                    f"Todos los días ingresados ya tenían excepción registrada para {_short_name(person)}.",
                    "warn"
                )
                return

            self.app.add_exceptions(new_exc)
            self.days_entry.delete(0, 'end')
            self.days_entry.focus_set()

            n = len(new_exc)
            dias_str = ", ".join(e['fecha'].strftime('%d/%m') for e in new_exc)
            skip_msg = ""
            if skipped_existing:
                skip_str = ", ".join(d.strftime('%d/%m') for d in skipped_existing)
                skip_msg = f" (omitidos por ya existir: {skip_str})"

            self.app.set_status(
                f"✓ {n} excepción{'es' if n > 1 else ''} {exc_type} para {_short_name(person)}: {dias_str}{skip_msg}",
                "ok"
            )

        except ValueError:
            self.app.set_status("Ingresa días o rangos válidos, ej: 1-5, 12 o 15, 20-25.", "error")
        except Exception as ex:
            self.app.set_status(f"Error inesperado: {str(ex)}", "error")

    def update_preview(self, shifts, year, month):
        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")

        self.preview_textbox.tag_config("header", foreground=P["accent"])
        self.preview_textbox.tag_config("date", foreground=P["text_s"])
        self.preview_textbox.tag_config("person", foreground=P["text_ok"])
        self.preview_textbox.tag_config("warning", foreground=P["orange"])
        self.preview_textbox.tag_config("skip", foreground=P["text_s"])
        self.preview_textbox.tag_config("current", background=P["bg_hover"], foreground=P["text"])

        self.preview_textbox.insert("end", f"{'─'*38}\n", "header")
        self.preview_textbox.insert("end", f"  {MESES[month-1].upper()} {year}\n", "header")
        self.preview_textbox.insert("end", f"{'─'*38}\n\n", "header")

        today = date.today()

        for sh in shifts:
            s, e = sh['semana']
            person = sh['persona'] or "NADIE DISPONIBLE"
            salt = sh.get('saltados', [])

            is_current = s <= today <= e
            if is_current:
                self.preview_textbox.insert("end", " ▶ SEMANA ACTUAL\n", "header")

            line_tags = ("current",) if is_current else ()
            date_tags = ("date", "current") if is_current else ("date",)
            person_tags = ("person", "current") if is_current else ("person",)

            self.preview_textbox.insert(
                "end", f"  📅 {s.strftime('%d/%m')} → {e.strftime('%d/%m')}\n", date_tags
            )
            self.preview_textbox.insert(
                "end", f"  👤 {_short_name(person, 2)}\n", person_tags
            )

            for warning in sh.get("advertencias", []):
                self.preview_textbox.insert(
                    "end", f"  ⚠ {warning['mensaje']} ({', '.join(warning['feriados'])})\n", "warning"
                )
            for sk in salt:
                self.preview_textbox.insert(
                    "end", f"     ↷ {_short_name(sk['persona'], 1)} ({sk['tipo']})\n", "skip"
                )
            self.preview_textbox.insert("end", "\n")

        self.preview_textbox.configure(state="disabled")

        # Actualizar tarjeta de próximo turno
        first_shift = next((sh for sh in shifts if sh.get('persona') and sh['semana'][1] >= today), None)
        if not first_shift:
            first_shift = next((sh for sh in shifts if sh.get('persona')), None)

        if first_shift:
            p_name = _short_name(first_shift['persona'], 3)
            s_date = first_shift['semana'][0].strftime('%d/%m')
            e_date = first_shift['semana'][1].strftime('%d/%m')
            prefix = "Actual" if first_shift['semana'][0] <= today <= first_shift['semana'][1] else "Próximo"
            self.next_turno_lbl.configure(text=f"{prefix}: {p_name}\nSemana: {s_date} - {e_date}")
        else:
            self.next_turno_lbl.configure(text="Sin turnos en este periodo")

    def save_month(self):
        self.app.save_month()
