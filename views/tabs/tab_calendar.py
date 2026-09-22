import calendar
from datetime import datetime, date, timedelta
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

from views.theme import P, AVATAR_PAL, MESES, DIAS, EXC_COLORS, EXC_ICONS
from views.components.widgets import _short_name, _initials, _avatar_ctk, _make_row_hover
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

        self._build_ui()

    def _build_ui(self):
        self.parent.configure(fg_color=P["bg_app"])
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(
            self.parent, fg_color=P["bg_hdr"], corner_radius=12,
            border_width=1, border_color=P["border"]
        )
        nav.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        nav.grid_columnconfigure(3, weight=1)

        now = datetime.now()
        self.v_month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.v_year_var = ctk.StringVar(value=str(now.year))

        ctk.CTkButton(
            nav, text="‹  Anterior", width=88, height=36, corner_radius=8,
            fg_color=P["bg_card"], hover_color=P["border_h"],
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            command=self._prev_month
        ).grid(row=0, column=0, padx=(14, 4), pady=12)

        ctk.CTkOptionMenu(
            nav, variable=self.v_month_var, values=MESES, width=140,
            fg_color=P["bg_card"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            command=lambda _: self.render_turnos_view()
        ).grid(row=0, column=1, padx=4, pady=12)

        years = [str(y) for y in range(now.year - 2, now.year + 4)]
        ctk.CTkOptionMenu(
            nav, variable=self.v_year_var, values=years, width=88,
            fg_color=P["bg_card"], button_color=P["accent_d"],
            button_hover_color=P["accent"],
            dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            command=lambda _: self.render_turnos_view()
        ).grid(row=0, column=2, padx=(4, 4), pady=12)

        legend = ctk.CTkFrame(nav, fg_color=P["bg_card"], corner_radius=8)
        legend.grid(row=0, column=3, padx=12, sticky="e", pady=10)
        items = [
            ("■ Turno", P["turno"]), ("DA", P["da"]),
            ("FL", P["fl"]), ("Finde", P["weekend"]),
            ("Actual", P["today_bg"])
        ]
        for i, (lbl, col) in enumerate(items):
            cf = ctk.CTkFrame(legend, fg_color=col, corner_radius=6)
            cf.grid(row=0, column=i, padx=4, pady=6, ipadx=6, ipady=2)
            ctk.CTkLabel(
                cf, text=lbl, text_color="#FFF",
                font=ctk.CTkFont(family="Inter", size=10, weight="bold")
            ).pack(padx=2)

        self.btn_hoy = ctk.CTkButton(
            nav, text="Hoy", width=54, height=36, corner_radius=8,
            fg_color=P["accent_d"], hover_color=P["accent"],
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            command=self._go_to_today
        )
        self.btn_hoy.grid(row=0, column=4, padx=(4, 4), pady=12)

        ctk.CTkButton(
            nav, text="Siguiente  ›", width=92, height=36, corner_radius=8,
            fg_color=P["bg_card"], hover_color=P["border_h"],
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            command=self._next_month
        ).grid(row=0, column=5, padx=(4, 4), pady=12)

        ctk.CTkButton(
            nav, text="Actualizar", width=86, height=36, corner_radius=8,
            fg_color=P["accent_d"], hover_color=P["accent"],
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            command=self.render_turnos_view
        ).grid(row=0, column=6, padx=(4, 4), pady=12)

        self.btn_exportar = ctk.CTkButton(
            nav, text="📊  Exportar Excel", width=125, height=36, corner_radius=8,
            fg_color=P["green_d"], hover_color=P["green"],
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            command=self.app.export_calendar_excel
        )
        self.btn_exportar.grid(row=0, column=7, padx=(4, 14), pady=12)

        self.vista_scroll = ctk.CTkScrollableFrame(
            self.parent, fg_color=P["bg_app"], corner_radius=0,
            scrollbar_button_color=P["border_h"],
            scrollbar_button_hover_color=P["border"]
        )
        self.vista_scroll.grid(row=1, column=0, sticky="nsew")
        self.vista_scroll.grid_columnconfigure(0, weight=1)

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

        exceptions = self.app.exceptions_by_period.get(viewing_key, [])
        if viewing_key == self.app.active_period_key:
            exceptions = self.app.exceptions

        manual_assignments = self.app.manual_assignments_by_period.get(viewing_key, {})
        if viewing_key == self.app.active_period_key:
            manual_assignments = self.app.manual_assignments

        shifts = self.controller.preview_shifts(
            year, month, exceptions, manual_assignments=manual_assignments)
        generation_warnings = self.controller.shift_manager.last_warnings
        if generation_warnings:
            self.app.set_status(f"⚠ {len(generation_warnings)} feriado repetido por falta de alternativa.", "warn")

        exc_map = {}
        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                exc_map[(exc['persona'], exc['fecha'].day)] = exc['tipo']

        turno_days = {}
        warning_days = {}
        for sh in shifts:
            p = sh['persona']
            if not p:
                continue
            s, e = sh['semana']
            cur = s
            while cur <= e:
                if cur.month == month and cur.year == year:
                    turno_days.setdefault(p, set()).add(cur.day)
                    if sh.get('advertencias'):
                        warning_days.setdefault(p, set()).add(cur.day)
                cur += timedelta(days=1)

        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                turno_days.get(exc['persona'], set()).discard(exc['fecha'].day)

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
        ctk.CTkLabel(
            exception_summary,
            text=f"⚠  {n_exc} excepción{'es' if n_exc != 1 else ''} registrada{'s' if n_exc != 1 else ''}",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=P["text_w"], anchor="w"
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
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=titulo_color
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            hl,
            text="■ Turno  ·  DA Día Admin  ·  FL Feriado  ·  Sombreado = fin de semana  ·  Azul = semana actual",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=P["text_s"]
        ).grid(row=1, column=0, sticky="w")

        if is_closed and is_past_mo:
            banner_f = ctk.CTkFrame(
                hl, fg_color="#1A1505", corner_radius=8,
                border_width=1, border_color="#403010"
            )
            banner_f.grid(row=2, column=0, sticky="ew", pady=(6, 0))
            ctk.CTkLabel(
                banner_f,
                text="🗄  Mes cerrado — Datos correspondientes al historial guardado",
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
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
                font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                text_color=P["text_s"]
            ).pack(pady=(20, 6))
            ctk.CTkLabel(
                empty_f, text="Asegúrate de haber configurado el mes desde la pestaña Planificación.",
                font=ctk.CTkFont(family="Inter", size=12), text_color=P["text_s"]
            ).pack(pady=(0, 20))
            return

        # ── GRILLA ────────────────────────────────────────────────────────────
        CELL_W = 34
        CELL_H = 50
        HDR_H = 62
        NAME_W = 240

        card_bg = P["past_tint"] if is_past_mo else P["bg_card"]
        cal_outer = ctk.CTkFrame(
            self.vista_scroll, fg_color=card_bg, corner_radius=12,
            border_width=1, border_color=P["border"] if not is_past_mo else "#141830"
        )
        cal_outer.grid(row=stats_row_offset + 2, column=0, sticky="ew", padx=16, pady=(4, 16))
        cal_outer.grid_columnconfigure(0, weight=1)
        cal_outer.grid_rowconfigure(0, weight=1)

        cal_table = tk.Frame(cal_outer, bg=card_bg)
        cal_table.grid(row=0, column=0, sticky="nsew")
        cal_table.grid_columnconfigure(0, minsize=NAME_W)
        for c in range(1, days_in + 1):
            cal_table.grid_columnconfigure(c, minsize=CELL_W, weight=1, uniform="days")
        cal_table.grid_columnconfigure(days_in + 1, weight=0)

        # Header de la tabla
        hdr_bg = P["bg_hdr"] if not is_past_mo else "#0A0C14"
        corner = tk.Frame(cal_table, bg=hdr_bg, width=NAME_W, height=HDR_H)
        corner.grid(row=0, column=0, sticky="nsew")
        corner.grid_propagate(False)
        tk.Label(
            corner, text="PERSONAL", bg=hdr_bg, fg=P["text_s"],
            font=("Inter", 9, "bold"), anchor="w"
        ).place(x=14, rely=0.5, anchor="w")
        tk.Frame(corner, bg=P["border"], width=1).place(relx=1.0, rely=0, anchor="ne", relheight=1.0)

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

            df = tk.Frame(cal_table, bg=bg, width=CELL_W, height=HDR_H)
            df.grid(row=0, column=d, sticky="nsew", padx=1, pady=2)
            df.grid_propagate(False)

            tc_n = "#FFF" if is_today else (P["text_a"] if in_cw else (P["text_s"] if is_we else "#CBD5E1"))
            if is_past_mo and not is_today:
                tc_n = "#3A4260"

            tk.Label(
                df, text=DIAS[wd], bg=bg,
                fg=P["text_s"] if not is_today else "#93C5FD",
                font=("Inter", 8)
            ).place(relx=0.5, rely=0.28, anchor="center")
            tk.Label(
                df, text=str(d), bg=bg, fg=tc_n,
                font=("Inter", 12, "bold" if is_today or in_cw else "normal")
            ).place(relx=0.5, rely=0.68, anchor="center")

        tk.Frame(cal_table, bg=P["border_h"], height=2).grid(row=1, column=0, columnspan=days_in + 1, sticky="ew")

        # Filas de personal
        row_bg_e = P["bg_row_e"] if not is_past_mo else "#0C0E1C"
        row_bg_o = P["bg_row_o"] if not is_past_mo else "#0E1020"
        name_bg = P["bg_name"] if not is_past_mo else "#0A0C1E"

        for ri, persona in enumerate(all_personas):
            is_deleted = persona not in personal
            p_turno = turno_days.get(persona, set())
            av_color = AVATAR_PAL[ri % len(AVATAR_PAL)]
            row_bg = row_bg_e if ri % 2 == 0 else row_bg_o
            rnum = ri + 2

            row_widgets = []

            name_f = tk.Frame(cal_table, bg=name_bg, width=NAME_W, height=CELL_H)
            name_f.grid(row=rnum, column=0, sticky="nsew")
            name_f.grid_propagate(False)
            row_widgets.append((name_f, name_bg))

            AV = 28
            av_c = tk.Canvas(name_f, width=AV, height=AV, bg=name_bg, highlightthickness=0)
            av_c.place(x=8, rely=0.5, anchor="w")
            av_c.create_oval(0, 0, AV, AV, fill=av_color, outline="")
            av_c.create_text(AV // 2, AV // 2, text=_initials(persona), fill="#FFF", font=("Inter", 8, "bold"))
            row_widgets.append((av_c, name_bg))

            display_name = _short_name(persona, 4)
            if is_deleted:
                display_name += " (Eliminado)"

            lbl_n = tk.Label(
                name_f, text=display_name,
                bg=name_bg, fg=P["text"] if not is_past_mo else P["text_s"],
                font=("Inter", 10, "bold" if not is_deleted else "italic"), anchor="w"
            )
            lbl_n.place(x=AV + 14, rely=0.5, anchor="w", width=NAME_W - AV - 18)
            row_widgets.append((lbl_n, name_bg))

            border_line = tk.Frame(name_f, bg=P["border"], width=1)
            border_line.place(relx=1.0, x=-1, rely=0, anchor="ne", relheight=1.0)

            for d in range(1, days_in + 1):
                wd = date(year, month, d).weekday()
                is_we = wd >= 5
                exc_tipo = exc_map.get((persona, d))
                has_t = d in p_turno
                in_cw = d in cur_week_days

                if exc_tipo == "DA":
                    bg, txt, tc, bold = P["da"], "DA", "#FFF", True
                elif exc_tipo == "FL":
                    bg, txt, tc, bold = P["fl"], "FL", "#FFF", True
                elif exc_tipo == "LIC":
                    bg, txt, tc, bold = P["lic"], "LIC", "#FFF", True
                elif exc_tipo == "OTR":
                    bg, txt, tc, bold = P["otr"], "OTR", "#FFF", True
                elif exc_tipo == "FOR":
                    bg, txt, tc, bold = P["for"], "FOR", "#FFF", True
                elif has_t:
                    if d in warning_days.get(persona, set()):
                        bg = P["orange"]
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

                cf = tk.Frame(cal_table, bg=bg, width=CELL_W, height=CELL_H)
                cf.grid(row=rnum, column=d, sticky="nsew", padx=1, pady=2)
                cf.grid_propagate(False)
                row_widgets.append((cf, bg))

                lbl = None
                if txt:
                    lbl = tk.Label(
                        cf, text=txt, bg=bg, fg=tc,
                        font=("Inter", 10, "bold" if bold else "normal")
                    )
                    lbl.place(relx=0.5, rely=0.5, anchor="center")

                if not is_deleted and not is_past_mo and not is_closed:
                    def make_handler(p, day, exc, y=year, m=month):
                        return lambda e: self._handle_calendar_click(p, day, exc, y, m)
                    handler = make_handler(persona, d, exc_tipo)
                    cf.bind("<Button-1>", handler)
                    if lbl:
                        lbl.bind("<Button-1>", handler)

            _make_row_hover(cal_table, row_widgets)

            if ri < len(personal) - 1:
                tk.Frame(cal_table, bg=P["sep"], height=1).grid(
                    row=rnum, column=0, columnspan=days_in + 1, sticky="s"
                )

        # ── Detalle por semana ────────────────────────────────────────────────
        ctk.CTkLabel(
            self.vista_scroll, text="Detalle por semana",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=P["text"] if not is_past_mo else P["text_s"]
        ).grid(row=stats_row_offset + 3, column=0, padx=20, pady=(12, 4), sticky="w")

        co = ctk.CTkFrame(self.vista_scroll, fg_color="transparent")
        co.grid(row=stats_row_offset + 4, column=0, sticky="ew", padx=16, pady=(0, 24))
        co.grid_columnconfigure(0, weight=1)
        co.grid_columnconfigure(1, weight=1)

        for idx, shift in enumerate(shifts):
            s_date, e_date = shift['semana']
            persona = shift['persona'] or "NADIE DISPONIBLE"
            saltados = shift.get('saltados', [])
            is_cw = (s_date <= today <= e_date)
            av_idx = personal.index(persona) if persona in personal else 0
            av_color = AVATAR_PAL[av_idx % len(AVATAR_PAL)] if persona != "NADIE DISPONIBLE" else P["border"]

            card_fg = P["past_tint"] if is_past_mo else P["bg_card2"]
            card_bdr = (
                P["orange"] if shift.get("advertencias") else
                P["today"] if is_cw else
                (P["border"] if not is_past_mo else "#141830")
            )

            card = ctk.CTkFrame(
                co, fg_color=card_fg, corner_radius=12,
                border_width=2 if is_cw else 1, border_color=card_bdr
            )
            card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            crow = 0

            if is_cw:
                top_bar = ctk.CTkFrame(card, fg_color=P["today"], height=4, corner_radius=0)
                top_bar.grid(row=crow, column=0, sticky="ew")
                crow += 1
                bf = ctk.CTkFrame(card, fg_color=P["today_bg"], corner_radius=6)
                bf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(
                    bf, text="  ● SEMANA ACTUAL  ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color=P["accent"]
                ).pack(padx=2, pady=3)
                crow += 1

            if is_past_mo:
                hf = ctk.CTkFrame(card, fg_color="#1A1505", corner_radius=6)
                hf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(
                    hf, text="  🗄 HISTORIAL  ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color=P["text_w"]
                ).pack(padx=2, pady=3)
                crow += 1

            if shift.get("advertencias"):
                wf = ctk.CTkFrame(card, fg_color=P["orange"], corner_radius=6)
                wf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="ew")
                ctk.CTkLabel(
                    wf, text="⚠ REPETICIÓN DE FERIADO POR FALTA DE ALTERNATIVA",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color="#FFF"
                ).pack(padx=8, pady=4)
                crow += 1

            if shift.get("es_recuperacion"):
                rf = ctk.CTkFrame(card, fg_color="#1E3A8A", corner_radius=6)
                rf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(
                    rf, text="  🔄 TURNO RECUPERADO  ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color="#93C5FD"
                ).pack(padx=2, pady=3)
                crow += 1

            if shift.get("es_manual") or shift.get("es_forzado"):
                mf = ctk.CTkFrame(card, fg_color="#065F46", corner_radius=6)
                mf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(
                    mf, text="  📌 ASIGNACIÓN MANUAL  ",
                    font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                    text_color="#A7F3D0"
                ).pack(padx=2, pady=3)
                crow += 1

            week_counter = f"Sem. {idx + 1}/{len(shifts)}"
            ctk.CTkLabel(
                card,
                text=f"{s_date.strftime('%d %b')} — {e_date.strftime('%d %b')}  ·  {week_counter}".upper(),
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color=P["text_a"] if not is_past_mo else P["text_s"]
            ).grid(
                row=crow, column=0, padx=14,
                pady=(10 if not (is_cw or is_past_mo) else 6, 4), sticky="w"
            )
            crow += 1

            badge = ctk.CTkFrame(
                card, fg_color=P["bg_card"], corner_radius=10,
                border_width=1, border_color=P["border_h"]
            )
            badge.grid(row=crow, column=0, padx=10, pady=(0, 8), sticky="ew")
            badge.grid_columnconfigure(1, weight=1)
            crow += 1

            av = _avatar_ctk(badge, _initials(persona), av_color, size=40)
            av.grid(row=0, column=0, padx=(10, 8), pady=10)

            info_c = ctk.CTkFrame(badge, fg_color="transparent")
            info_c.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)
            is_deleted = persona not in personal and persona != "NADIE DISPONIBLE"
            display_name = _short_name(persona, 4)
            if is_deleted:
                display_name += " (Eliminado)"

            ctk.CTkLabel(
                info_c, text=display_name,
                font=ctk.CTkFont(family="Inter", size=13, weight="bold" if not is_deleted else "normal"),
                text_color=P["text"] if not is_deleted else P["text_s"],
                anchor="w", wraplength=260
            ).pack(fill="x")

            dias = []
            cur = s_date
            while cur <= e_date:
                if cur.month == month and cur.year == year:
                    dias.append(str(cur.day))
                cur += timedelta(days=1)
            if dias:
                ctk.CTkLabel(
                    info_c, text="📌  Días: " + ", ".join(dias),
                    font=ctk.CTkFont(family="Inter", size=11),
                    text_color=P["text_s"], anchor="w"
                ).pack(fill="x")

            if saltados:
                ef = ctk.CTkFrame(card, fg_color="transparent")
                ef.grid(row=crow, column=0, padx=10, pady=(0, 10), sticky="ew")
                ef.grid_columnconfigure(0, weight=1)
                crow += 1
                for si, exc_info in enumerate(saltados):
                    tipo = exc_info['tipo']
                    cc = EXC_COLORS.get(tipo, P["otr"])
                    icon = EXC_ICONS.get(tipo, "📌")
                    cf2 = ctk.CTkFrame(ef, fg_color=cc, corner_radius=8)
                    cf2.grid(row=si, column=0, sticky="ew", pady=2)
                    ctk.CTkLabel(
                        cf2,
                        text=f"{icon}  {_short_name(exc_info['persona'], 2)}  ·  {tipo}",
                        font=ctk.CTkFont(family="Inter", size=11), text_color="#FFF"
                    ).pack(padx=10, pady=5)
            else:
                ctk.CTkFrame(card, height=6, fg_color="transparent").grid(row=crow, column=0)

    def _handle_calendar_click(self, persona, day, exc_tipo, c_year, c_month):
        active_year, active_month = self.app.get_selected_period()

        if active_year != c_year or active_month != c_month:
            self.app.month_var.set(MESES[c_month - 1])
            self.app.year_var.set(str(c_year))
            self.app.on_period_change()
            active_year, active_month = c_year, c_month

        if exc_tipo:
            if messagebox.askyesno(
                "Eliminar excepción",
                f"¿Eliminar la excepción {exc_tipo} de {_short_name(persona, 2)} el día {day}?",
                parent=self.app
            ):
                for i, exc in enumerate(self.app.exceptions):
                    if (exc['persona'] == persona and exc['fecha'].day == day and
                            exc['fecha'].month == active_month and exc['fecha'].year == active_year):
                        self.app.remove_exception(i)
                        break
        else:
            AddExceptionDialog.show(
                self.app, persona, day,
                callback=lambda tipo: self._on_exception_added_from_calendar(persona, day, tipo, active_year, active_month)
            )

    def _on_exception_added_from_calendar(self, persona, day, tipo, year, month):
        date_obj = date(year, month, day)
        new_exc = [{'persona': persona, 'fecha': date_obj, 'tipo': tipo}]
        self.app.add_exceptions(new_exc)
