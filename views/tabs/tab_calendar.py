import calendar
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
from tkinter import messagebox

from views.theme import P, AVATAR_PAL, MESES, DIAS, EXC_COLORS, EXC_ICONS, FONT_FAMILY
from views.components.widgets import _short_name, _initials, _avatar_ctk
from views.components.dialogs import AddExceptionDialog

class TabCalendar:
    def __init__(self, parent_tab, app):
        self.parent = parent_tab
        self.app = app
        self.controller = app.controller

        self.v_month_var = None
        self.v_year_var = None
        self.btn_hoy = None
        self.btn_exportar = None
        self.vista_scroll = None
        self._status_leave_job = None

        self._build_ui()

    def _on_cell_enter(self, msg):
        if self._status_leave_job is not None:
            try:
                self.parent.after_cancel(self._status_leave_job)
            except Exception:
                pass
            self._status_leave_job = None
        self.app.set_status(msg, "info")

    def _on_cell_leave(self):
        if self._status_leave_job is not None:
            try:
                self.parent.after_cancel(self._status_leave_job)
            except Exception:
                pass
        self._status_leave_job = self.parent.after(
            80,
            lambda: self.app.set_status(
                "💡 Pasa el cursor sobre los días o haz clic en una celda para gestionar excepciones.",
                "info"
            )
        )

    def _build_ui(self):
        self.parent.configure(fg_color=P["bg_app"])
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(
            self.parent, fg_color=P["bg_hdr"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        nav.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        nav.grid_columnconfigure(5, weight=1)

        def _on_nav_wheel(event):
            if event.delta > 0:
                self._prev_month()
            elif event.delta < 0:
                self._next_month()
        nav.bind("<MouseWheel>", _on_nav_wheel)

        now = datetime.now()
        self.v_month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.v_year_var = ctk.StringVar(value=str(now.year))

        ctk.CTkButton(
            nav, text="‹  Anterior", width=82, height=36, corner_radius=8,
            fg_color=P["bg_card"], hover_color=P["border_h"], cursor="hand2",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._prev_month
        ).grid(row=0, column=0, padx=(14, 4), pady=12)

        ctk.CTkOptionMenu(
            nav, variable=self.v_month_var, values=MESES, width=132,
            fg_color=P["bg_card"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            command=lambda _: self.render_turnos_view()
        ).grid(row=0, column=1, padx=4, pady=12)

        years = [str(y) for y in range(now.year - 2, now.year + 4)]
        ctk.CTkOptionMenu(
            nav, variable=self.v_year_var, values=years, width=82,
            fg_color=P["bg_card"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            command=lambda _: self.render_turnos_view()
        ).grid(row=0, column=2, padx=4, pady=12)

        ctk.CTkButton(
            nav, text="Siguiente  ›", width=84, height=36, corner_radius=8,
            fg_color=P["bg_card"], hover_color=P["border_h"], cursor="hand2",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._next_month
        ).grid(row=0, column=3, padx=4, pady=12)

        self.btn_hoy = ctk.CTkButton(
            nav, text="Hoy", width=50, height=36, corner_radius=8,
            fg_color=P["accent_d"], hover_color=P["accent"], cursor="hand2",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self._go_to_today
        )
        self.btn_hoy.grid(row=0, column=4, padx=(4, 8), pady=12)

        legend = ctk.CTkFrame(nav, fg_color=P["bg_card"], corner_radius=8)
        legend.grid(row=0, column=6, padx=(8, 6), sticky="e", pady=10)
        items = [
            ("■ Turno", P["turno"]),
            ("■ Cambio", P["for"]),
            ("DA", P["da"]),
            ("FL", P["fl"]),
            ("LIC", P["lic"]),
            ("OTR", P["otr"]),
            ("Finde", P["weekend"]),
            ("Actual", P["today_bg"])
        ]
        for i, (lbl, col) in enumerate(items):
            cf = ctk.CTkFrame(legend, fg_color=col, corner_radius=6)
            cf.grid(row=0, column=i, padx=3, pady=5, ipadx=5, ipady=2)
            ctk.CTkLabel(
                cf, text=lbl, text_color="#FFF",
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold")
            ).pack(padx=2)

        ctk.CTkButton(
            nav, text="Actualizar", width=84, height=36, corner_radius=8,
            fg_color=P["accent_d"], hover_color=P["accent"], cursor="hand2",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self.render_turnos_view
        ).grid(row=0, column=7, padx=4, pady=12)

        self.btn_exportar = ctk.CTkButton(
            nav, text="📊  Exportar Excel", width=125, height=36, corner_radius=8,
            fg_color=P["green_d"], hover_color=P["green"], cursor="hand2",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            command=self.app.export_calendar_excel
        )
        self.btn_exportar.grid(row=0, column=8, padx=(4, 14), pady=12)

        self.vista_scroll = ctk.CTkScrollableFrame(
            self.parent, fg_color=P["bg_app"], corner_radius=0,
            scrollbar_button_color=P["border_h"],
            scrollbar_button_hover_color=P["border"]
        )
        self.vista_scroll.grid(row=1, column=0, sticky="nsew")
        self.vista_scroll.grid_columnconfigure(0, weight=1)

        # Barra inferior informativa y de estado interactivo
        self.cal_bottom = ctk.CTkFrame(
            self.parent, fg_color=P["bg_card"], height=38, corner_radius=8,
            border_width=1, border_color=P["border"]
        )
        self.cal_bottom.grid(row=2, column=0, sticky="ew", padx=16, pady=(4, 10))
        self.cal_bottom.grid_columnconfigure(0, weight=1)
        self.cal_bottom.grid_propagate(False)

        self.cal_status_lbl = ctk.CTkLabel(
            self.cal_bottom,
            text="💡 Pasa el cursor sobre los días o haz clic en una celda para gestionar excepciones.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=P["text_s"], anchor="w"
        )
        self.cal_status_lbl.grid(row=0, column=0, padx=14, pady=6, sticky="w")

        self.cal_shortcut_lbl = ctk.CTkLabel(
            self.cal_bottom,
            text="⌨ Alt+←/→ Mes · Ctrl+1/2/3 Pestañas · F5 Refrescar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=P["border_h"], anchor="e"
        )
        self.cal_shortcut_lbl.grid(row=0, column=1, padx=14, pady=6, sticky="e")

    def _prev_month(self):
        m = MESES.index(self.v_month_var.get())
        y = int(self.v_year_var.get())
        m, y = (11, y - 1) if m == 0 else (m - 1, y)
        self.v_month_var.set(MESES[m])
        self.v_year_var.set(str(y))
        self.render_turnos_view()

    def _next_month(self):
        m = MESES.index(self.v_month_var.get())
        y = int(self.v_year_var.get())
        m, y = (0, y + 1) if m == 11 else (m + 1, y)
        self.v_month_var.set(MESES[m])
        self.v_year_var.set(str(y))
        self.render_turnos_view()

    def _go_to_today(self):
        today = date.today()
        self.v_month_var.set(MESES[today.month - 1])
        self.v_year_var.set(str(today.year))
        self.render_turnos_view()

    def get_current_view_period(self):
        month = MESES.index(self.v_month_var.get()) + 1
        year = int(self.v_year_var.get())
        return year, month

    def set_view_period(self, year, month):
        self.v_month_var.set(MESES[month - 1])
        self.v_year_var.set(str(year))

    def render_turnos_view(self):
        if self._status_leave_job is not None:
            try:
                self.parent.after_cancel(self._status_leave_job)
            except Exception:
                pass
            self._status_leave_job = None

        for w in self.vista_scroll.winfo_children():
            w.destroy()

        year, month = self.get_current_view_period()
        today = date.today()

        viewing_key = f"{year}-{month:02d}"
        is_cur_mo = (today.year == year and today.month == month)
        is_past_mo = date(year, month, 1) < date(today.year, today.month, 1)
        is_future_mo = date(year, month, 1) > date(today.year, today.month, 1)

        month_prefix = f"{year}-{month:02d}-"
        is_closed = any(k.startswith(month_prefix) for k in self.controller.shift_manager.historial)

        if self.btn_hoy:
            if is_cur_mo:
                self.btn_hoy.configure(state="disabled", fg_color=P["border"], hover_color=P["border"])
            else:
                self.btn_hoy.configure(state="normal", fg_color=P["accent_d"], hover_color=P["accent"])

        if viewing_key == self.app.active_period_key:
            exceptions = self.app.exceptions
        else:
            exceptions = self.controller.get_exceptions_for_period(year, month)

        manual_assignments = self.app.manual_assignments_by_period.get(viewing_key, {})
        if viewing_key == self.app.active_period_key:
            manual_assignments = self.app.manual_assignments

        shifts = self.controller.preview_shifts(
            year, month, exceptions, manual_assignments=manual_assignments)
        generation_warnings = self.controller.shift_manager.last_warnings
        if generation_warnings:
            self.app.set_status(f"⚠ {len(generation_warnings)} feriado repetido por falta de alternativa.", "warn")

        exc_map = {}
        exc_motives = {}
        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                exc_map[(exc['persona'], exc['fecha'].day)] = exc['tipo']
                if exc.get('motivo'):
                    exc_motives[(exc['persona'], exc['fecha'].day)] = exc['motivo']

        turno_days = {}
        warning_days = {}
        manual_shift_days = {}
        manual_shift_motives = {}

        # Identificar motivos manuales del periodo
        manual_motives = self.app.manual_motives_by_period.get(viewing_key, {})
        if viewing_key == self.app.active_period_key:
            manual_motives = self.app.manual_motives
        if not manual_motives and hasattr(self.controller, 'get_all_manual_motives'):
            manual_motives = self.controller.get_all_manual_motives(viewing_key)

        for sh in shifts:
            p = sh.get('persona')
            if not p:
                continue
            s, e = sh['semana']
            wk = f"{s.isoformat()}_{e.isoformat()}"
            is_manual = bool(
                sh.get('es_manual') or
                sh.get('es_forzado') or
                (manual_assignments and wk in manual_assignments)
            )
            mot = (manual_motives.get(wk) if manual_motives else None) or sh.get('motivo')

            cur = s
            while cur <= e:
                if cur.month == month and cur.year == year:
                    turno_days.setdefault(p, set()).add(cur.day)
                    if is_manual:
                        manual_shift_days.setdefault(p, set()).add(cur.day)
                        if mot:
                            manual_shift_motives[(p, cur.day)] = mot
                    if sh.get('advertencias'):
                        warning_days.setdefault(p, set()).add(cur.day)
                cur += timedelta(days=1)

        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                turno_days.get(exc['persona'], set()).discard(exc['fecha'].day)
                manual_shift_days.get(exc['persona'], set()).discard(exc['fecha'].day)

        cur_week_days = set()
        if is_cur_mo:
            for sh in shifts:
                s, e = sh['semana']
                if s <= today <= e:
                    cur = s
                    while cur <= e:
                        if cur.month == month:
                            cur_week_days.add(cur.day)
                        cur += timedelta(days=1)
                    break

        personal = self.controller.get_personal_list()
        assigned_names = {sh['persona'] for sh in shifts if sh.get('persona')}
        for exc in exceptions:
            assigned_names.add(exc['persona'])

        all_personas = list(personal)
        for name in assigned_names:
            if name not in all_personas and name != "NADIE DISPONIBLE":
                all_personas.append(name)

        _, days_in = calendar.monthrange(year, month)

        stats_row_offset = 0
        n_exc = len(exceptions)
        exception_summary = ctk.CTkFrame(self.vista_scroll, fg_color="transparent", height=28)
        exception_summary.grid(row=stats_row_offset, column=0, sticky="ew", padx=20, pady=(6, 0))
        exception_summary.grid_propagate(False)
        if n_exc > 0:
            exc_text = f"⚠  {n_exc} excepción{'es' if n_exc != 1 else ''} registrada{'s' if n_exc != 1 else ''}"
            exc_color = P["text_w"]
        else:
            exc_text = "✓  Sin excepciones en este periodo"
            exc_color = P["text_ok"]

        ctk.CTkLabel(
            exception_summary,
            text=exc_text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=exc_color, anchor="w"
        ).pack(side="left")

        hl = ctk.CTkFrame(self.vista_scroll, fg_color="transparent")
        hl.grid(row=stats_row_offset + 1, column=0, sticky="ew", padx=20, pady=(6, 2))
        hl.grid_columnconfigure(0, weight=1)

        if is_past_mo:
            titulo_color = P["text_s"]
            titulo_txt = f"🗄  Historial — {MESES[month-1]} {year}"
        elif is_future_mo:
            titulo_color = P["text_a"]
            titulo_txt = f"🔮  Previsualización — {MESES[month-1]} {year}"
        else:
            titulo_color = P["text"]
            titulo_txt = f"Calendario — {MESES[month-1]} {year}"

        ctk.CTkLabel(
            hl, text=titulo_txt,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=titulo_color
        ).grid(row=0, column=0, sticky="w")
        if is_closed and is_past_mo:
            banner_f = ctk.CTkFrame(
                hl, fg_color="#1A1505", corner_radius=8,
                border_width=1, border_color="#403010"
            )
            banner_f.grid(row=2, column=0, sticky="ew", pady=(6, 0))
            ctk.CTkLabel(
                banner_f,
                text="🗄  Mes cerrado — Datos correspondientes al historial guardado",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                text_color=P["text_w"]
            ).pack(padx=12, pady=5, side="left")

        if not shifts:
            empty_f = ctk.CTkFrame(
                self.vista_scroll, fg_color=P["bg_card"],
                corner_radius=12, border_width=1, border_color=P["border"]
            )
            empty_f.grid(row=stats_row_offset + 2, column=0, sticky="ew", padx=16, pady=(4, 16))
            ctk.CTkLabel(
                empty_f, text="📭  Sin turnos generados para este periodo",
                font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                text_color=P["text_s"]
            ).pack(pady=(20, 6))
            ctk.CTkLabel(
                empty_f, text="Asegúrate de haber configurado el mes desde la pestaña Planificación.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=P["text_s"]
            ).pack(pady=(0, 20))
            return

        # ── GRILLA (un único Canvas: ~8 items por persona en vez de ~35 widgets) ──
        CELL_W = 33
        CELL_H = 48
        HDR_H = 56
        NAME_W = 220
        AV = 28

        card_bg = P["past_tint"] if is_past_mo else P["bg_card"]
        cal_outer = ctk.CTkFrame(
            self.vista_scroll, fg_color=card_bg, corner_radius=12,
            border_width=1, border_color=P["border"] if not is_past_mo else "#141830"
        )
        cal_outer.grid(row=stats_row_offset + 2, column=0, sticky="ew", padx=16, pady=(4, 16))
        cal_outer.grid_columnconfigure(0, weight=1)

        hdr_bg = P["bg_hdr"] if not is_past_mo else "#0A0C14"
        row_bg_e = P["bg_row_e"] if not is_past_mo else "#0C0E1C"
        row_bg_o = P["bg_row_o"] if not is_past_mo else "#0E1020"
        name_bg = P["bg_name"] if not is_past_mo else "#0A0C1E"

        top = HDR_H + 2
        canvas = tk.Canvas(
            cal_outer, bg=card_bg, highlightthickness=0,
            width=NAME_W + 20 * days_in, height=top + len(all_personas) * CELL_H
        )
        canvas.grid(row=0, column=0, sticky="ew", padx=1, pady=1)

        # Modelo de datos de la grilla (se dibuja en _draw; sin widgets por celda)
        header_days = []
        for d in range(1, days_in + 1):
            wd = date(year, month, d).weekday()
            is_we = wd >= 5
            is_today = is_cur_mo and today.day == d
            in_cw = d in cur_week_days
            if is_today:
                bg = P["today"]
            elif in_cw:
                bg = "#162040"
            elif is_we:
                bg = P["weekend"] if not is_past_mo else "#0D0F1E"
            else:
                bg = hdr_bg
            tc_n = "#FFF" if is_today else (P["text_a"] if in_cw else (P["text_s"] if is_we else "#CBD5E1"))
            if is_past_mo and not is_today:
                tc_n = "#3A4260"
            header_days.append((d, DIAS[wd], bg, tc_n, "#93C5FD" if is_today else P["text_s"],
                                "bold" if (is_today or in_cw) else "normal"))

        interactive = not is_past_mo and not is_closed
        rows = []
        cell_map = {}
        for ri, persona in enumerate(all_personas):
            is_deleted = persona not in personal
            display_name = _short_name(persona, 4) + (" (Eliminado)" if is_deleted else "")
            row_bg = row_bg_e if ri % 2 == 0 else row_bg_o
            rows.append({
                "initials": _initials(persona), "name": display_name,
                "av": AVATAR_PAL[ri % len(AVATAR_PAL)], "deleted": is_deleted,
            })
            p_turno = turno_days.get(persona, set())
            p_manual = manual_shift_days.get(persona, set())
            p_warn = warning_days.get(persona, set())
            p_short = _short_name(persona, 2)

            for d in range(1, days_in + 1):
                is_we = date(year, month, d).weekday() >= 5
                exc_tipo = exc_map.get((persona, d))
                has_t = d in p_turno
                in_cw = d in cur_week_days
                is_man = d in p_manual

                if exc_tipo in ("DA", "FL", "LIC", "OTR", "FOR"):
                    bg = P[exc_tipo.lower()]
                    txt, tc, bold = exc_tipo, "#FFF", True
                elif has_t:
                    if d in p_warn:
                        bg = P["orange"]
                    elif is_man:
                        bg = "#064E3B" if is_past_mo else ("#10B981" if in_cw else P["for"])
                    elif is_past_mo:
                        bg = "#5A1010"
                    elif in_cw:
                        bg = P["turno_h"]
                    else:
                        bg = P["turno"]
                    txt, tc, bold = "■", "#FFF", True
                elif in_cw:
                    bg, txt, tc, bold = "#162040", "", P["text_s"], False
                elif is_we:
                    bg = P["weekend"] if not is_past_mo else "#0D0F1E"
                    txt, tc, bold = "·", "#2D3564", False
                else:
                    bg, txt, tc, bold = row_bg, "", P["text_s"], False

                m_text = None
                if has_t:
                    if is_man:
                        mot = manual_shift_motives.get((persona, d), "Cambio manual registrado")
                        m_text = f"📌 Guardia manual de turno: {p_short} (Día {d}) — Motivo: {mot}"
                    else:
                        m_text = f"🗓 Guardia de turno regular: {p_short} (Día {d})"
                elif exc_tipo == "DA":
                    m_text = f"⏭ Día Administrativo (DA): {p_short} (Día {d})"
                elif exc_tipo == "FL":
                    m_text = f"🚫 Feriado Legal (FL): {p_short} (Día {d})"
                elif exc_tipo == "LIC":
                    m_text = f"📋 Licencia Médica (LIC): {p_short} (Día {d})"
                elif exc_tipo == "OTR":
                    mot = exc_motives.get((persona, d), "")
                    mot_str = f" — Motivo: {mot}" if mot else ""
                    m_text = f"⭐ Permiso especial (OTR): {p_short} (Día {d}){mot_str}"
                elif not is_deleted and interactive:
                    m_text = f"➕ Clic para registrar excepción a {p_short} el día {d}"

                if has_t:
                    if d in p_warn:
                        hov = "#EA580C"
                    elif is_man:
                        hov = "#10B981"
                    elif is_past_mo:
                        hov = "#7F1D1D"
                    else:
                        hov = P["turno_h"]
                elif exc_tipo == "DA":
                    hov = "#D97706"
                elif exc_tipo == "FL":
                    hov = "#7C3AED"
                elif exc_tipo == "LIC":
                    hov = "#0891B2"
                elif exc_tipo == "OTR":
                    hov = "#4B5563"
                elif exc_tipo == "FOR":
                    hov = "#10B981"
                elif in_cw:
                    hov = "#202E54"
                elif is_we:
                    hov = "#222938"
                else:
                    hov = P["bg_hover"]

                cell_map[(ri, d)] = {
                    "bg": bg, "txt": txt, "tc": tc, "bold": bold, "hov": hov, "msg": m_text,
                    "click": (persona, d, exc_tipo) if (not is_deleted and interactive) else None,
                }

        name_font = tkfont.Font(family=FONT_FAMILY, size=10, weight="bold")
        name_fg = P["text"] if not is_past_mo else P["text_s"]
        st = {"w": 0, "cw": CELL_W, "hover": None, "rect": {}}

        def _fit(text, maxw):
            if name_font.measure(text) <= maxw:
                return text
            while text and name_font.measure(text + "…") > maxw:
                text = text[:-1]
            return text + "…"

        def _draw(width):
            canvas.delete("all")
            st["rect"].clear()
            st["hover"] = None
            st["w"] = width
            cw = max(20, (width - NAME_W) / days_in)
            st["cw"] = cw
            canvas.create_rectangle(0, 0, NAME_W, HDR_H, fill=hdr_bg, outline="")
            canvas.create_text(14, HDR_H / 2, text="PERSONAL", anchor="w",
                               fill=P["text_s"], font=(FONT_FAMILY, 9, "bold"))
            for d, dia, bg, tc_n, tc_d, wgt in header_days:
                x0 = NAME_W + (d - 1) * cw
                canvas.create_rectangle(x0 + 1, 2, x0 + cw - 1, HDR_H - 2, fill=bg, outline="")
                canvas.create_text(x0 + cw / 2, 18, text=dia, fill=tc_d, font=(FONT_FAMILY, 8))
                canvas.create_text(x0 + cw / 2, 39, text=str(d), fill=tc_n, font=(FONT_FAMILY, 12, wgt))
            canvas.create_rectangle(0, HDR_H, width, top, fill=P["border_h"], outline="")

            for ri, row in enumerate(rows):
                y0 = top + ri * CELL_H
                st["rect"][("n", ri)] = canvas.create_rectangle(0, y0, NAME_W, y0 + CELL_H, fill=name_bg, outline="")
                canvas.create_oval(8, y0 + CELL_H / 2 - AV / 2, 8 + AV, y0 + CELL_H / 2 + AV / 2,
                                   fill=row["av"], outline="")
                canvas.create_text(8 + AV / 2, y0 + CELL_H / 2, text=row["initials"], fill="#FFF",
                                   font=(FONT_FAMILY, 8, "bold"))
                canvas.create_text(AV + 14, y0 + CELL_H / 2, anchor="w", text=_fit(row["name"], NAME_W - AV - 22),
                                   fill=name_fg, font=(FONT_FAMILY, 10, "italic" if row["deleted"] else "bold"))
                if ri < len(rows) - 1:
                    canvas.create_rectangle(0, y0 + CELL_H - 1, width, y0 + CELL_H, fill=P["sep"], outline="")
                for d in range(1, days_in + 1):
                    c = cell_map[(ri, d)]
                    x0 = NAME_W + (d - 1) * cw
                    st["rect"][("c", ri, d)] = canvas.create_rectangle(
                        x0 + 1, y0 + 2, x0 + cw - 1, y0 + CELL_H - 2, fill=c["bg"], outline="")
                    if c["txt"]:
                        canvas.create_text(x0 + cw / 2, y0 + CELL_H / 2, text=c["txt"], fill=c["tc"],
                                           font=(FONT_FAMILY, 10, "bold" if c["bold"] else "normal"))
            canvas.create_rectangle(NAME_W - 1, 0, NAME_W, top + len(rows) * CELL_H, fill=P["border"], outline="")

        def _target(ev):
            if ev.y < top:
                return None
            ri = int((ev.y - top) // CELL_H)
            if ri >= len(rows):
                return None
            if ev.x < NAME_W:
                return ("n", ri)
            d = int((ev.x - NAME_W) // st["cw"]) + 1
            return ("c", ri, d) if 1 <= d <= days_in else None

        def _apply(target, on):
            rid = st["rect"].get(target)
            if rid is None:
                return None
            if target[0] == "n":
                canvas.itemconfigure(rid, fill=P["bg_hover"] if on else name_bg)
                return None
            c = cell_map[(target[1], target[2])]
            canvas.itemconfigure(rid, fill=c["hov"] if on else c["bg"])
            return c

        def _set_hover(target):
            old = st["hover"]
            if target == old:
                return
            if old is not None:
                c = _apply(old, False)
                if c and c["msg"]:
                    self._on_cell_leave()
            st["hover"] = target
            cursor = ""
            if target is not None:
                c = _apply(target, True)
                if c:
                    if c["msg"]:
                        self._on_cell_enter(c["msg"])
                    if c["click"]:
                        cursor = "hand2"
            canvas.configure(cursor=cursor)

        def _on_click(ev):
            t = _target(ev)
            if t and t[0] == "c":
                c = cell_map[(t[1], t[2])]
                if c["click"]:
                    persona, day, exc = c["click"]
                    self._handle_calendar_click(persona, day, exc, year, month)

        def _on_configure(ev):
            if int(ev.width) != st["w"]:
                _draw(int(ev.width))

        canvas.bind("<Motion>", lambda ev: _set_hover(_target(ev)))
        canvas.bind("<Leave>", lambda ev: _set_hover(None))
        canvas.bind("<Button-1>", _on_click)
        canvas.bind("<Configure>", _on_configure)
        _draw(int(canvas.cget("width")))


    def _handle_calendar_click(self, persona, day, exc_tipo, c_year, c_month):
        active_year, active_month = self.app.get_selected_period()

        if active_year != c_year or active_month != c_month:
            self.app.month_var.set(MESES[c_month - 1])
            self.app.year_var.set(str(c_year))
            self.app.on_period_change()
            active_year, active_month = c_year, c_month

        if exc_tipo:
            exc_found = None
            exc_idx = -1
            for i, exc in enumerate(self.app.exceptions):
                if (exc['persona'] == persona and exc['fecha'].day == day and
                        exc['fecha'].month == active_month and exc['fecha'].year == active_year and
                        exc.get('tipo') == exc_tipo):
                    exc_found = exc
                    exc_idx = i
                    break

            motivo_str = ""
            if exc_found and exc_found.get('motivo'):
                motivo_str = f" (Motivo: {exc_found['motivo']})"

            if messagebox.askyesno(
                "Eliminar excepción",
                f"¿Eliminar la excepción {exc_tipo}{motivo_str} de {_short_name(persona, 2)} el día {day}?",
                parent=self.app
            ):
                if exc_idx >= 0:
                    self.app.remove_exception(exc_idx)
        else:
            AddExceptionDialog.show(
                self.app, persona, day,
                callback=lambda tipo, motivo="": self._on_exception_added_from_calendar(
                    persona, day, tipo, active_year, active_month, motivo=motivo
                )
            )

    def _on_exception_added_from_calendar(self, persona, day, tipo, year, month, motivo=""):
        date_obj = date(year, month, day)
        exc_item = {'persona': persona, 'fecha': date_obj, 'tipo': tipo}
        if tipo == 'OTR' and motivo:
            exc_item['motivo'] = motivo
        new_exc = [exc_item]
        self.app.add_exceptions(new_exc)
