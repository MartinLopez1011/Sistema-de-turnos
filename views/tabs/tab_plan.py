import calendar
from datetime import datetime, date
import customtkinter as ctk
from tkinter import messagebox

from views.theme import P, AVATAR_PAL, MESES, EXC_COLORS, EXC_ICONS
from views.components.widgets import _section_header, _short_name, _initials, _avatar_ctk
from views.components.dialogs import SelectPersonDialog, ChangeShiftDialog

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
        self.next_turno_frame = ctk.CTkFrame(
            sidebar, fg_color=P["bg_card2"], corner_radius=10,
            border_width=1, border_color=P["border"]
        )
        self.next_turno_frame.grid(row=5, column=0, padx=16, pady=(4, 6), sticky="ew")
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
            exc_form, variable=self.type_var, values=["DA", "FL", "LIC", "OTR"],
            fg_color=P["bg_input"],
            selected_color=P["accent_d"],
            selected_hover_color=P["accent"],
            unselected_color=P["bg_input"],
            unselected_hover_color=P["bg_hover"],
            text_color=P["text"],
            command=self._on_type_changed
        )
        self.type_segmented.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

        # Contenedor dinámico de motivo obligatorio para OTR
        self.reason_frame = ctk.CTkFrame(exc_form, fg_color="transparent")
        ctk.CTkLabel(
            self.reason_frame, text="Motivo / Justificación (obligatorio)",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"]
        ).pack(anchor="w", padx=12, pady=(0, 3))
        self.reason_entry = ctk.CTkEntry(
            self.reason_frame, placeholder_text="Ej: Comisión de servicio, Duelo...",
            fg_color=P["bg_input"], border_color=P["border"], border_width=1,
            height=36
        )
        self.reason_entry.pack(fill="x", padx=12, pady=(0, 10))
        self.reason_entry.bind("<Return>", lambda _: self.add_exception())
        self.reason_entry.bind("<Key>", lambda _: self.reason_entry.configure(border_color=P["border"]))

        self.type_var.trace_add("write", lambda *_: self._on_type_changed())

        ctk.CTkButton(
            exc_form, text="＋  Añadir",
            command=self.add_exception,
            fg_color=P["green_d"], hover_color=P["green"],
            height=36, corner_radius=6,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold")
        ).grid(row=4, column=0, padx=12, pady=(0, 12), sticky="ew")

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
                text_color=P["text"], font=ctk.CTkFont(family="Inter", size=12, weight="bold")
            ).pack()
            ctk.CTkLabel(
                empty_box, text="Usa el formulario lateral para añadir días de permiso o feriado legal.",
                text_color=P["text_s"], font=ctk.CTkFont(family="Inter", size=11),
                wraplength=200, justify="center"
            ).pack(padx=10, pady=(2, 12))
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

            if tipo == "OTR" and exc.get('motivo'):
                ctk.CTkLabel(
                    info,
                    text=f"📝 Motivo: {exc['motivo']}",
                    font=ctk.CTkFont(family="Inter", size=10, slant="italic"),
                    text_color=P["text_s"], anchor="w"
                ).pack(fill="x")

            ctk.CTkButton(
                row, text="✕", width=28, height=28,
                fg_color=P["bg_card"], hover_color=P["red_d"],
                font=ctk.CTkFont(size=12),
                command=lambda i=index: self.app.remove_exception(i)
            ).grid(row=0, column=1, padx=6, pady=6)

    def _on_type_changed(self, value=None):
        if not hasattr(self, 'reason_frame') or not hasattr(self, 'type_var'):
            return
        val = value if value is not None else self.type_var.get()
        if val == "OTR":
            self.reason_frame.grid(row=3, column=0, sticky="ew")
        else:
            self.reason_frame.grid_forget()
            if hasattr(self, 'reason_entry'):
                self.reason_entry.configure(border_color=P["border"])

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

            existing_map = {
                exc['fecha']: exc for exc in self.app.exceptions if exc['persona'] == person
            }

            new_exc = []
            updated_exc = []
            skipped_existing = []

            for day in raw_days:
                date_obj = datetime(year, month, day).date()
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
                self.days_entry.configure(border_color=P["orange"])
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

            self.days_entry.delete(0, 'end')
            if hasattr(self, 'reason_entry'):
                self.reason_entry.delete(0, 'end')
                self.reason_entry.configure(border_color=P["border"])
            self.days_entry.focus_set()

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
            self.app.set_status("Ingresa días o rangos válidos, ej: 1-5, 12 o 15, 20-25.", "error")
        except Exception as ex:
            self.app.set_status(f"Error inesperado: {str(ex)}", "error")

    def update_preview(self, shifts, year, month):
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
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                text_color=P["text"]
            ).pack()
            ctk.CTkLabel(
                empty_box, text="Selecciona un periodo válido o verifica el personal activo en Ajustes.",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=P["text_s"], justify="center"
            ).pack(padx=16, pady=(4, 16))
            self._render_next_turno_card(None, today, personal)
            return

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
                corner_radius=10,
                border_width=2 if is_current else 1,
                border_color=card_border
            )
            card.pack(fill="x", padx=4, pady=5)
            card.grid_columnconfigure(0, weight=1)

            crow = 0

            # Encabezado de la tarjeta semanal
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.grid(row=crow, column=0, sticky="ew", padx=12, pady=(10, 4))
            header.grid_columnconfigure(0, weight=1)
            crow += 1

            date_text = f"📅  {s.strftime('%d/%m')} → {e.strftime('%d/%m')}  ·  Semana {idx + 1}"
            ctk.CTkLabel(
                header, text=date_text,
                font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                text_color=P["text_a"] if not is_current else P["accent"]
            ).grid(row=0, column=0, sticky="w")

            badges_f = ctk.CTkFrame(header, fg_color="transparent")
            badges_f.grid(row=0, column=1, sticky="e")

            if is_current:
                cur_badge = ctk.CTkFrame(badges_f, fg_color=P["today_bg"], corner_radius=5)
                cur_badge.pack(side="left", padx=(0, 6))
                ctk.CTkLabel(
                    cur_badge, text=" ● ACTUAL ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color=P["accent"]
                ).pack(padx=4, pady=2)

            if is_manual:
                man_badge = ctk.CTkFrame(badges_f, fg_color="#065F46", corner_radius=5)
                man_badge.pack(side="left")
                ctk.CTkLabel(
                    man_badge, text=" 📌 MANUAL ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color="#A7F3D0"
                ).pack(padx=4, pady=2)
            else:
                auto_badge = ctk.CTkFrame(badges_f, fg_color=P["bg_input"], corner_radius=5)
                auto_badge.pack(side="left")
                ctk.CTkLabel(
                    auto_badge, text=" 🤖 AUTOMÁTICO ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color=P["text_s"]
                ).pack(padx=4, pady=2)

            # Fila de persona asignada y botones de acción
            body = ctk.CTkFrame(card, fg_color="transparent")
            body.grid(row=crow, column=0, sticky="ew", padx=12, pady=(4, 10))
            body.grid_columnconfigure(1, weight=1)
            crow += 1

            av = _avatar_ctk(body, _initials(person), av_color, size=34)
            av.grid(row=0, column=0, padx=(0, 10), sticky="w")

            name_lbl = ctk.CTkLabel(
                body, text=_short_name(person, 3),
                font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                text_color=P["text_ok"] if not is_manual else P["green"],
                anchor="w"
            )
            name_lbl.grid(row=0, column=1, sticky="w")

            actions_f = ctk.CTkFrame(body, fg_color="transparent")
            actions_f.grid(row=0, column=2, sticky="e")

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

            btn_change = ctk.CTkButton(
                actions_f, text="✏️ Cambiar",
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                fg_color=P["bg_input"], hover_color=P["bg_hover"],
                border_width=1, border_color=P["border_h"],
                text_color=P["text"], height=28, width=82,
                command=_on_change
            )
            btn_change.pack(side="left", padx=(0, 4))

            if is_manual:
                def _on_reset(wk=week_key):
                    self.app.clear_manual_assignment(wk)

                btn_reset = ctk.CTkButton(
                    actions_f, text="↺ Auto",
                    font=ctk.CTkFont(family="Inter", size=11),
                    fg_color=P["bg_card"], hover_color=P["red_d"],
                    border_width=1, border_color=P["border"],
                    text_color=P["text_s"], height=28, width=64,
                    command=_on_reset
                )
                btn_reset.pack(side="left")

                motive = self.app.get_manual_motive(week_key)
                if motive:
                    mf = ctk.CTkFrame(card, fg_color="transparent")
                    mf.grid(row=crow, column=0, padx=12, pady=(0, 4), sticky="ew")
                    crow += 1
                    ctk.CTkLabel(
                        mf, text=f"📝 Motivo: {motive}",
                        font=ctk.CTkFont(family="Inter", size=10, slant="italic"),
                        text_color=P["green"], wraplength=230, justify="left", anchor="w"
                    ).pack(anchor="w", padx=2)

            # Advertencias y saltados
            if sh.get("advertencias"):
                wf = ctk.CTkFrame(card, fg_color=P["orange"], corner_radius=6)
                wf.grid(row=crow, column=0, padx=12, pady=(0, 6), sticky="ew")
                crow += 1
                for w_item in sh["advertencias"]:
                    ctk.CTkLabel(
                        wf, text=f"⚠ {w_item['mensaje']} ({', '.join(w_item['feriados'])})",
                        font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                        text_color="#000"
                    ).pack(padx=8, pady=3, anchor="w")

            if salt:
                sf = ctk.CTkFrame(card, fg_color="transparent")
                sf.grid(row=crow, column=0, padx=12, pady=(0, 8), sticky="ew")
                crow += 1
                for sk in salt:
                    tipo = sk['tipo']
                    cc = EXC_COLORS.get(tipo, P["otr"])
                    icon = EXC_ICONS.get(tipo, "📌")
                    ctk.CTkLabel(
                        sf, text=f"↷ {icon} {_short_name(sk['persona'], 2)} ({tipo})",
                        font=ctk.CTkFont(family="Inter", size=10),
                        text_color=P["text_s"]
                    ).pack(anchor="w", padx=2)

        # Actualizar tarjeta de próximo turno
        first_shift = next((sh for sh in shifts if sh.get('persona') and sh['semana'][1] >= today), None)
        if not first_shift:
            first_shift = next((sh for sh in shifts if sh.get('persona')), None)

        self._render_next_turno_card(first_shift, today, personal)

    def _render_next_turno_card(self, first_shift, today, personal):
        for w in self.next_turno_frame.winfo_children():
            w.destroy()

        if not first_shift or not first_shift.get('persona') or first_shift.get('persona') == "NADIE DISPONIBLE":
            self.next_turno_lbl = ctk.CTkLabel(
                self.next_turno_frame,
                text="Sin turnos en este periodo",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color=P["text_s"]
            )
            self.next_turno_lbl.pack(padx=10, pady=12)
            return

        person = first_shift['persona']
        s_date = first_shift['semana'][0].strftime('%d/%m')
        e_date = first_shift['semana'][1].strftime('%d/%m')
        is_current = first_shift['semana'][0] <= today <= first_shift['semana'][1]

        badge_bg = P["today_bg"] if is_current else "#1E293B"
        badge_fg = P["accent"] if is_current else P["text_a"]
        badge_text = "● GUARDIA EN CURSO" if is_current else "⏳ PRÓXIMO TURNO"

        badge_f = ctk.CTkFrame(self.next_turno_frame, fg_color=badge_bg, corner_radius=5)
        badge_f.pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkLabel(
            badge_f, text=f" {badge_text} ",
            font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
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
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=P["text"], anchor="w"
        )
        self.next_turno_lbl.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            self.next_turno_frame,
            text=f"📅  Semana: {s_date} → {e_date}",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=P["text_s"], anchor="w"
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def save_month(self):
        self.app.save_month()
