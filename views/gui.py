import customtkinter as ctk
import os
import calendar
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image
from datetime import datetime, timedelta, date
import threading

ASSETS_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
SUCCESS_ICON = os.path.join(ASSETS_DIR, "success.png")
ERROR_ICON   = os.path.join(ASSETS_DIR, "error.png")
SAVE_ICON    = os.path.join(ASSETS_DIR, "save.png")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
P = {
    "bg_app":    "#111418",
    "bg_side":   "#171B20",
    "bg_card":   "#1C2228",
    "bg_card2":  "#232A31",
    "bg_input":  "#252D34",
    "bg_hdr":    "#0D1013",
    "bg_name":   "#181E23",
    "bg_row_e":  "#1C2228",
    "bg_row_o":  "#20272E",
    "bg_hover":  "#2A353D",
    "accent":    "#57C7B5",
    "accent_d":  "#16877D",
    "green":     "#34D399",
    "green_d":   "#059669",
    "red":       "#F87171",
    "red_d":     "#DC2626",
    "orange":    "#FBBF24",
    "purple":    "#C084FC",
    "turno":     "#991B1B",
    "turno_h":   "#DC2626",
    "da":        "#B45309",
    "fl":        "#5B21B6",
    "weekend":   "#171D22",
    "text":      "#F1F5F3",
    "text_s":    "#91A0A5",
    "text_a":    "#8DE1D2",
    "text_ok":   "#6EE7B7",
    "text_w":    "#FCD34D",
    "text_e":    "#FCA5A5",
    "border":    "#303A40",
    "border_h":  "#49636A",
    "today":     "#16877D",
    "today_bg":  "#124A46",
    "sep":       "#293137",
    "past_tint": "#0A0C1A",   # TEST ITER 3 — tinte para meses pasados
}

AVATAR_PAL = [
    "#1D4ED8","#047857","#92400E","#5B21B6","#9D174D",
    "#075985","#065F46","#78350F","#4C1D95","#881337",
    "#0C4A6E","#14532D","#431407","#2E1065","#4A044E","#1E3A8A",
]

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
DIAS  = ["L","M","X","J","V","S","D"]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _section_header(parent, text, row, pady_top=14):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.grid(row=row, column=0, sticky="ew", padx=16, pady=(pady_top, 4))
    ctk.CTkLabel(f, text=text.upper(),
                 font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
                 text_color=P["text_s"]).pack(side="left")
    ctk.CTkFrame(f, height=1, fg_color=P["border"]).pack(
        side="left", fill="x", expand=True, padx=(8, 0))


def _avatar_ctk(parent, initials, color, size=32):
    c = ctk.CTkFrame(parent, width=size, height=size,
                     corner_radius=size // 2, fg_color=color)
    c.pack_propagate(False)
    ctk.CTkLabel(c, text=initials,
                 font=ctk.CTkFont(family="Inter", size=max(9, size // 3), weight="bold"),
                 text_color="#FFFFFF").pack(expand=True)
    return c


def _short_name(full, words=2):
    skip = {"COM", "PRO", "SBC", "(A)", "(F)"}
    parts = [p for p in full.strip().split() if p.upper() not in skip]
    return " ".join(parts[:words]) if parts else full


def _initials(full):
    skip = {"COM", "PRO", "SBC", "(A)", "(F)"}
    parts = [p for p in full.strip().split() if p.upper() not in skip]
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[1][0].upper()
    return parts[0][:2].upper() if parts else "??"


def _make_row_hover(ref_widget, row_widgets):
    """
    Fix hover flickering con debounce + bind recursivo.
    El after_cancel() previene el parpadeo al transitar entre
    widgets hijos de la misma fila.
    """
    state = {'job': None, 'on': False}
    HOVER = P["bg_hover"]
    hoverable_colors = {
        P["bg_name"], P["bg_row_e"], P["bg_row_o"],
        "#0C0E1C", "#0E1020", "#0A0C1E"
    }

    def _do_on():
        state['on'] = True
        for w, orig in row_widgets:
            if orig not in hoverable_colors:
                continue
            try:   w.configure(bg=HOVER)
            except Exception: pass

    def _do_off():
        state['job'] = None
        state['on'] = False
        for w, orig in row_widgets:
            if orig not in hoverable_colors:
                continue
            try:   w.configure(bg=orig)
            except Exception: pass

    def on_enter(e):
        if state['job'] is not None:
            try:   ref_widget.after_cancel(state['job'])
            except Exception: pass
            state['job'] = None
        if not state['on']:
            _do_on()

    def on_leave(e):
        if state['job'] is None:
            state['job'] = ref_widget.after(18, _do_off)

    def _bind_tree(w):
        w.bind("<Enter>", on_enter, add="+")
        w.bind("<Leave>", on_leave, add="+")
        for child in w.winfo_children():
            _bind_tree(child)

    for w, _ in row_widgets:
        _bind_tree(w)


# ══════════════════════════════════════════════════════════════════════════════
#  APP PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class TurnosApp(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.title("Sistema de Turnos")
        self.geometry("1240x760")
        self.minsize(1040, 620)
        self.configure(fg_color=P["bg_app"])
        self.bind("<Control-r>", lambda _: self.render_turnos_view())
        self.bind("<Alt-Left>", lambda _: self._prev_month())
        self.bind("<Alt-Right>", lambda _: self._next_month())

        self.exceptions           = []
        self.exceptions_by_period = {}
        self.active_period_key    = None
        self.is_exporting         = False
        self.plan_period_dirty    = False
        self.calendar_period_override = None

        def _ico(path, s):
            return ctk.CTkImage(light_image=Image.open(path), size=s) if os.path.exists(path) else None
        self.img_success = _ico(SUCCESS_ICON, (18, 18))
        self.img_error   = _ico(ERROR_ICON,   (18, 18))

        self._setup_ui()
        self.load_personal()

    # ──────────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # FIX ITER 1: usar command= en CTkTabview (no sobreescribir segmented_button)
        self.tabview = ctk.CTkTabview(
            self, anchor="nw",
            fg_color=P["bg_app"],
            segmented_button_fg_color=P["bg_hdr"],
            segmented_button_selected_color=P["accent_d"],
            segmented_button_selected_hover_color=P["accent"],
            segmented_button_unselected_color=P["bg_hdr"],
            segmented_button_unselected_hover_color=P["bg_card"],
            command=self._on_tab_change)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        self.tab_plan  = self.tabview.add("  📋  Planificación  ")
        self.tab_vista = self.tabview.add("  📅  Ver Turnos del Mes  ")
        self.tab_ajustes = self.tabview.add("  ⚙  Ajustes  ")

        self._build_tab_plan(self.tab_plan)
        self._build_tab_vista(self.tab_vista)
        self._build_tab_ajustes(self.tab_ajustes)

    def _on_tab_change(self, tab_name=None):
        """Callback DESPUÉS de que CTkTabview cambió la pestaña (no la reemplaza)."""
        current = tab_name or self.tabview.get()
        if "Ver Turnos" in current:
            if self.plan_period_dirty:
                self.v_month_var.set(self.month_var.get())
                self.v_year_var.set(self.year_var.get())
                self.plan_period_dirty = False
            self.render_turnos_view()

    # ══════════════════════════════════════════════════════════════════════════
    #  PESTAÑA 1 — PLANIFICACIÓN
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_plan(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────────────
        sidebar = ctk.CTkFrame(parent, width=285, corner_radius=0,
                               fg_color=P["bg_side"],
                               border_width=1, border_color=P["border"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(20, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar = sidebar

        title_f = ctk.CTkFrame(sidebar, fg_color=P["bg_hdr"], corner_radius=0)
        title_f.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(title_f, text="🗓  Sistema de Turnos",
                     font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
                     text_color=P["text"]).pack(padx=20, pady=16)

        _section_header(sidebar, "Periodo", row=1, pady_top=18)
        pf = ctk.CTkFrame(sidebar, fg_color="transparent")
        pf.grid(row=2, column=0, padx=16, pady=(0, 4), sticky="ew")
        pf.grid_columnconfigure(0, weight=3)
        pf.grid_columnconfigure(1, weight=2)

        now = datetime.now()
        self.month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.year_var  = ctk.StringVar(value=str(now.year))

        ctk.CTkOptionMenu(pf, variable=self.month_var, values=MESES,
                          fg_color=P["bg_input"], button_color=P["accent_d"],
                          button_hover_color=P["accent"],
                          dropdown_fg_color=P["bg_card"],
                          command=lambda _: self.on_period_change()
                          ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        years = [str(y) for y in range(now.year - 2, now.year + 4)]
        ctk.CTkOptionMenu(pf, variable=self.year_var, values=years,
                          fg_color=P["bg_input"], button_color=P["accent_d"],
                          button_hover_color=P["accent"],
                          dropdown_fg_color=P["bg_card"],
                          command=lambda _: self.on_period_change()
                          ).grid(row=0, column=1, sticky="ew")

        self.active_period_key = self.get_selected_period_key()

        _section_header(sidebar, "Persona", row=3, pady_top=10)
        self.person_var = ctk.StringVar()
        self.person_dropdown = ctk.CTkOptionMenu(
            sidebar, variable=self.person_var, values=["Cargando..."],
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card"])
        self.person_dropdown.grid(row=4, column=0, padx=16, pady=(0, 4), sticky="ew")

        _section_header(sidebar, "Excepción", row=5, pady_top=10)
        ctk.CTkLabel(sidebar, text="Días del mes (ej: 5, 12, 19)",
                     font=ctk.CTkFont(family="Inter", size=12),
                     text_color=P["text_s"]).grid(row=6, column=0, padx=16, pady=(0, 3), sticky="w")
        self.days_entry = ctk.CTkEntry(sidebar, placeholder_text="Separados por coma",
                                       fg_color=P["bg_input"],
                                       border_color=P["border"], border_width=1,
                                       height=36)
        self.days_entry.grid(row=7, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.days_entry.bind("<Return>", lambda _: self.add_exception())
        self.days_entry.bind("<Key>", lambda _: self.days_entry.configure(border_color=P["border"]))

        self.type_var = ctk.StringVar(value="DA")
        rf = ctk.CTkFrame(sidebar, fg_color=P["bg_input"], corner_radius=8)
        rf.grid(row=8, column=0, padx=16, pady=(0, 4), sticky="ew")
        rf.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkRadioButton(rf, text="Día Admin (DA)", variable=self.type_var, value="DA",
                           fg_color=P["orange"], hover_color=P["da"]
                           ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkRadioButton(rf, text="Feriado (FL)", variable=self.type_var, value="FL",
                           fg_color=P["purple"], hover_color=P["fl"]
                           ).grid(row=0, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkButton(sidebar, text="＋  Añadir excepción",
                      command=self.add_exception,
                      fg_color=P["green_d"], hover_color=P["green"],
                      height=38, corner_radius=8,
                      font=ctk.CTkFont(family="Inter", size=14, weight="bold")
                      ).grid(row=9, column=0, padx=16, pady=(6, 4), sticky="ew")



        # ── Main content ──────────────────────────────────────────────────────
        main = ctk.CTkFrame(parent, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(1, weight=3)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        self.main_frame = main

        title_block = ctk.CTkFrame(main, fg_color="transparent")
        title_block.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(title_block, text="Planificación de turnos",
                 font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
                 text_color=P["text"], anchor="w").pack(fill="x")
        ctk.CTkLabel(title_block,
             text="Configura las excepciones, revisa la asignación y exporta y guarda el periodo.",
                 font=ctk.CTkFont(family="Inter", size=12),
                 text_color=P["text_s"], anchor="w").pack(fill="x", pady=(3, 0))

        exc_frame = ctk.CTkFrame(main, fg_color=P["bg_card"], corner_radius=12,
                                 border_width=1, border_color=P["border"])
        exc_frame.grid(row=1, column=0, padx=(0, 12), sticky="nsew")
        exc_frame.grid_rowconfigure(2, weight=1)
        exc_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(exc_frame, text="Excepciones del periodo",
                     font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                     text_color=P["text"]).grid(row=0, column=0, padx=14, pady=(14, 2), sticky="w")
        self.exc_count_label2 = ctk.CTkLabel(exc_frame, text="Ninguna registrada",
                                             text_color=P["text_s"], anchor="w",
                                             font=ctk.CTkFont(family="Inter", size=12))
        self.exc_count_label2.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        self.exception_list2 = ctk.CTkScrollableFrame(
            exc_frame, fg_color="transparent", scrollbar_button_color=P["border_h"])
        self.exception_list2.grid(row=2, column=0, padx=8, pady=(0, 10), sticky="nsew")

        preview_frame = ctk.CTkFrame(main, fg_color=P["bg_card"], corner_radius=12,
                                     border_width=1, border_color=P["border"])
        preview_frame.grid(row=1, column=1, padx=(12, 0), sticky="nsew")
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(preview_frame, text="Vista previa",
                     font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                     text_color=P["text"]).grid(row=0, column=0, padx=14, pady=(14, 2), sticky="w")
        ctk.CTkLabel(preview_frame,
                     text="Se actualiza al cambiar el periodo o excepciones",
                     text_color=P["text_s"], anchor="w",
                     font=ctk.CTkFont(family="Inter", size=12)
                     ).grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        self.preview_textbox = ctk.CTkTextbox(
            preview_frame, font=ctk.CTkFont(family="Courier", size=13),
            fg_color=P["bg_card2"], border_width=0, text_color=P["text"])
        self.preview_textbox.grid(row=2, column=0, padx=8, pady=(0, 10), sticky="nsew")
        self.preview_textbox.configure(state="disabled")

        bottom = ctk.CTkFrame(main, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=2, pady=(16, 0), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self._status_frame = ctk.CTkFrame(
            bottom, fg_color=P["bg_card"], corner_radius=8, height=36)
        self._status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._status_frame.grid_columnconfigure(0, weight=1)
        self._status_frame.grid_propagate(False)
        self.status_label = ctk.CTkLabel(
            self._status_frame,
            text="Listo para revisar, exportar y guardar el periodo.",
            text_color=P["text_s"], font=ctk.CTkFont(family="Inter", size=13))
        self.status_label.grid(row=0, column=0, padx=14, pady=4)

        btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew")
        btn_row.grid_columnconfigure(0, weight=3)
        btn_row.grid_columnconfigure(1, weight=1)

        self.save_export_btn = ctk.CTkButton(
            btn_row, text="📤  Exportar y guardar",
            command=self.save_and_export, height=42, corner_radius=10,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"])
        self.save_export_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(btn_row, text="📅 Abrir calendario",
                      command=self._jump_to_vista, height=42, corner_radius=10,
                  font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                      fg_color=P["accent_d"], hover_color=P["accent"]
                      ).grid(row=0, column=1, sticky="ew")

    def _jump_to_vista(self):
        if self.calendar_period_override is not None:
            year, month = self.calendar_period_override
            self.v_month_var.set(MESES[month - 1])
            self.v_year_var.set(str(year))
            self.calendar_period_override = None
        else:
            self.v_month_var.set(self.month_var.get())
            self.v_year_var.set(self.year_var.get())
        self.plan_period_dirty = False
        self.tabview.set("  📅  Ver Turnos del Mes  ")
        self._on_tab_change("  📅  Ver Turnos del Mes  ")

    # ── Helpers de estado de sesión ──────────────────────────────────────────────
    def _mark_dirty(self):
        """Indica en el título que hay cambios sin guardar."""
        if not self.title().startswith("●"):
            self.title("●  Sistema de Turnos")

    def _mark_clean(self):
        """Elimina el indicador de cambios sin guardar del título."""
        self.title("Sistema de Turnos")

    def _show_shortcuts(self):
        """Panel flotante con los atajos de teclado disponibles."""
        if hasattr(self, '_shortcuts_win') and self._shortcuts_win.winfo_exists():
            self._shortcuts_win.focus()
            return
        win = ctk.CTkToplevel(self)
        win.title("Atajos de teclado")
        win.geometry("380x250")
        win.configure(fg_color=P["bg_card"])
        win.resizable(False, False)
        win.grab_set()
        self._shortcuts_win = win

        ctk.CTkLabel(win, text="⌨  Atajos de teclado",
                     font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                     text_color=P["text"]).pack(padx=20, pady=(16, 10))

        shortcuts = [
            ("Ctrl + R",  "Actualizar vista de turnos"),
            ("Alt + ←",   "Mes anterior"),
            ("Alt + →",   "Mes siguiente"),
            ("Enter",     "Añadir excepción (campo de días)"),
        ]
        for key, desc in shortcuts:
            f = ctk.CTkFrame(win, fg_color=P["bg_card2"], corner_radius=6)
            f.pack(fill="x", padx=16, pady=3)
            f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(f, text=key,
                         font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
                         text_color=P["accent"], width=120, anchor="center"
                         ).grid(row=0, column=0, padx=10, pady=7)
            ctk.CTkLabel(f, text=desc,
                         font=ctk.CTkFont(family="Inter", size=11),
                         text_color=P["text_s"], anchor="w"
                         ).grid(row=0, column=1, padx=(0, 10), pady=7, sticky="w")

        ctk.CTkButton(win, text="Cerrar", width=100,
                      fg_color=P["accent_d"], hover_color=P["accent"],
                      command=win.destroy).pack(pady=(8, 16))

    def _reset_historial(self):
        """Resetea el historial con confirmación explícita del usuario."""
        result = simpledialog.askstring(
            "⚠  Confirmar reseteo de historial",
            "ATENCION: Esta accion eliminara TODO el historial,\n"
            "snapshots, pendientes y excepciones guardadas.\n\n"
            "Esta operacion NO se puede deshacer.\n\n"
            "Escribe  RESETEAR  para confirmar:",
            parent=self)
        if result is None:
            return  # Usuario canceló el diálogo
        if result.strip() != "RESETEAR":
            self.settings_status_label.configure(
                text="Reseteo cancelado (texto incorrecto).",
                text_color=P["text_w"])
            return
        try:
            sm = self.controller.shift_manager
            sm.historial   = {}
            sm.snapshots   = {}
            sm.pendientes  = []
            sm.excepciones = {}
            # Recalcular siguiente_id desde el inicio inmutable
            if sm.inicio:
                ultima_llave  = sorted(sm.inicio.keys())[-1]
                ultimo_nombre = sm.inicio[ultima_llave]
                ultimo_id = 1
                for p in sm.personal:
                    if p["nombre"] == ultimo_nombre:
                        ultimo_id = p["id"]
                        break
                siguiente = ultimo_id + 1
                if siguiente > len(sm.personal):
                    siguiente = 1
                sm.siguiente_id = siguiente
            else:
                sm.siguiente_id = 1
            sm.save_config()
            # Refrescar estado de la GUI
            self.starting_person_var.set(self.controller.get_starting_person())
            self.exceptions = []
            self.exceptions_by_period = {}
            self.load_personal()
            self._mark_clean()
            self.settings_status_label.configure(
                text="Historial reseteado correctamente.",
                text_color=P["text_ok"])
        except Exception as e:
            self.settings_status_label.configure(
                text=f"Error al resetear: {str(e)}",
                text_color=P["text_e"])

    def _build_tab_ajustes(self, parent):
        parent.configure(fg_color=P["bg_app"])
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=0, column=0, padx=28, pady=28, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(wrapper, text="Ajustes",
                     font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
                     text_color=P["text"], anchor="w").grid(
                         row=0, column=0, sticky="w")
        ctk.CTkLabel(
            wrapper,
            text="Define desde qué persona continuará la rotación de turnos.",
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=P["text_s"], anchor="w").grid(
                row=1, column=0, pady=(4, 20), sticky="w")

        card = ctk.CTkFrame(wrapper, fg_color=P["bg_card"], corner_radius=12,
                            border_width=1, border_color=P["border"])
        card.grid(row=2, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Persona inicial de la rotación",
                     font=ctk.CTkFont(family="Inter", size=16, weight="bold"),
                     text_color=P["text"], anchor="w").grid(
                         row=0, column=0, padx=20, pady=(20, 4), sticky="w")
        ctk.CTkLabel(
            card,
            text="Se usará para el próximo cálculo que no tenga un historial cerrado.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w", wraplength=620).grid(
                row=1, column=0, padx=20, pady=(0, 14), sticky="w")

        self.starting_person_var = ctk.StringVar(
            value=self.controller.get_starting_person())
        self.starting_person_dropdown = ctk.CTkOptionMenu(
            card, variable=self.starting_person_var,
            values=self.controller.get_personal_list(), width=420,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card2"])
        self.starting_person_dropdown.grid(row=2, column=0, padx=20, pady=(0, 16),
                                           sticky="w")

        ctk.CTkButton(
            card, text="Guardar punto de inicio", command=self.save_starting_person,
            height=38, width=220, corner_radius=8,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color=P["green_d"], hover_color=P["green"]).grid(
                row=3, column=0, padx=20, pady=(0, 20), sticky="w")

        self.settings_status_label = ctk.CTkLabel(
            card, text="Los cambios se guardan en config.json.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w")
        self.settings_status_label.grid(row=4, column=0, padx=20, pady=(0, 18),
                                        sticky="w")

        ctk.CTkLabel(
            wrapper,
            text="Nota: este ajuste no cambia el historial ni los meses ya guardados.\n"
                 "Si hay personas pendientes, esas se atienden antes de iniciar la rotación normal.",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], justify="left", anchor="w").grid(
                row=3, column=0, pady=(14, 0), sticky="w")

        # ── Zona de peligro — Reset historial ────────────────────────────────────
        danger_card = ctk.CTkFrame(wrapper, fg_color=P["bg_card"], corner_radius=12,
                                   border_width=1, border_color=P["red_d"])
        danger_card.grid(row=4, column=0, sticky="ew", pady=(20, 0))
        danger_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(danger_card, text="⚠  Zona de peligro",
                     font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                     text_color=P["red"], anchor="w").grid(
                         row=0, column=0, padx=20, pady=(16, 4), sticky="w")
        ctk.CTkLabel(danger_card,
                     text="Resetear el historial elimina todas las semanas cerradas, "
                          "snapshots y excepciones guardadas. No se puede deshacer.",
                     font=ctk.CTkFont(family="Inter", size=12),
                     text_color=P["text_s"], anchor="w", wraplength=580, justify="left").grid(
                         row=1, column=0, padx=20, pady=(0, 12), sticky="w")
        ctk.CTkButton(danger_card, text="🗑  Resetear historial",
                      command=self._reset_historial,
                      height=36, width=200, corner_radius=8,
                      font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                      fg_color=P["red_d"], hover_color=P["red"]).grid(
                          row=2, column=0, padx=20, pady=(0, 20), sticky="w")

    def save_starting_person(self):
        person = self.starting_person_var.get()
        if self.controller.set_starting_person(person):
            self.set_status(f"Punto de inicio guardado: {_short_name(person, 3)}", "ok")
        else:
            self.set_status("No se pudo guardar la persona inicial.", "error")

    # ══════════════════════════════════════════════════════════════════════════
    #  PESTAÑA 2 — VER TURNOS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_vista(self, parent):
        parent.configure(fg_color=P["bg_app"])
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        nav = ctk.CTkFrame(parent, fg_color=P["bg_hdr"], corner_radius=12,
                           border_width=1, border_color=P["border"])
        nav.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        nav.grid_columnconfigure(3, weight=1)

        now = datetime.now()
        self.v_month_var = ctk.StringVar(value=MESES[now.month - 1])
        self.v_year_var  = ctk.StringVar(value=str(now.year))

        ctk.CTkButton(nav, text="‹  Anterior", width=88, height=36, corner_radius=8,
                  fg_color=P["bg_card"], hover_color=P["border_h"],
                  font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                  command=self._prev_month
                      ).grid(row=0, column=0, padx=(14, 4), pady=12)

        ctk.CTkOptionMenu(nav, variable=self.v_month_var, values=MESES, width=140,
                          fg_color=P["bg_card"], button_color=P["accent_d"],
                          button_hover_color=P["accent"],
                          dropdown_fg_color=P["bg_card2"],
                          font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                          command=lambda _: self.render_turnos_view()
                          ).grid(row=0, column=1, padx=4, pady=12)

        years = [str(y) for y in range(now.year - 2, now.year + 4)]
        ctk.CTkOptionMenu(nav, variable=self.v_year_var, values=years, width=88,
                          fg_color=P["bg_card"], button_color=P["accent_d"],
                          button_hover_color=P["accent"],
                          dropdown_fg_color=P["bg_card2"],
                          font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                          command=lambda _: self.render_turnos_view()
                          ).grid(row=0, column=2, padx=(4, 4), pady=12)

        ctk.CTkButton(nav, text="Siguiente  ›", width=92, height=36, corner_radius=8,
                  fg_color=P["bg_card"], hover_color=P["border_h"],
                  font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                  command=self._next_month
                      ).grid(row=0, column=5, padx=(4, 8), pady=12)

        ctk.CTkButton(nav, text="Hoy", width=54, height=36, corner_radius=8,
                      fg_color=P["accent_d"], hover_color=P["accent"],
                      font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                      command=self._go_to_today
                      ).grid(row=0, column=4, padx=(4, 4), pady=12)

        legend = ctk.CTkFrame(nav, fg_color=P["bg_card"], corner_radius=8)
        legend.grid(row=0, column=3, padx=12, sticky="e", pady=10)
        for i, (lbl, col) in enumerate([("■ Turno", P["turno"]), ("DA", P["da"]),
                         ("FL", P["fl"]), ("Finde", P["weekend"]),
                         ("Actual", P["today_bg"])]):
            cf = ctk.CTkFrame(legend, fg_color=col, corner_radius=6)
            cf.grid(row=0, column=i, padx=4, pady=6, ipadx=6, ipady=2)
            ctk.CTkLabel(cf, text=lbl, text_color="#FFF",
                         font=ctk.CTkFont(family="Inter", size=10, weight="bold")
                         ).pack(padx=2)

        ctk.CTkButton(nav, text="Actualizar", width=86, height=36, corner_radius=8,
                      fg_color=P["accent_d"], hover_color=P["accent"],
                  font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                  command=self.render_turnos_view
                  ).grid(row=0, column=6, padx=(0, 6), pady=12)

        ctk.CTkButton(nav, text="⌨ Atajos", width=76, height=36, corner_radius=8,
                      fg_color=P["bg_card"], hover_color=P["border_h"],
                      font=ctk.CTkFont(family="Inter", size=11),
                      command=self._show_shortcuts
                      ).grid(row=0, column=7, padx=(0, 14), pady=12)

        self.vista_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=P["bg_app"], corner_radius=0,
            scrollbar_button_color=P["border_h"],
            scrollbar_button_hover_color=P["border"])
        self.vista_scroll.grid(row=1, column=0, sticky="nsew")
        self.vista_scroll.grid_columnconfigure(0, weight=1)

        self.after(250, self.render_turnos_view)

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

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDER — Vista del mes
    #  TEST ITER 1: mejor validación de agregar días + excepción UX
    #  TEST ITER 2: estado "sin datos" + indicador de historial vs activo
    #  TEST ITER 3: tinte visual meses pasados + separador columna nombre
    # ══════════════════════════════════════════════════════════════════════════
    def render_turnos_view(self):
        for w in self.vista_scroll.winfo_children():
            w.destroy()

        month = MESES.index(self.v_month_var.get()) + 1
        year  = int(self.v_year_var.get())
        today = date.today()

        # TEST ITER 3 — Clasificar el mes que se está viendo
        viewing_key  = f"{year}-{month:02d}"
        is_cur_mo    = (today.year == year and today.month == month)
        is_past_mo   = date(year, month, 1) < date(today.year, today.month, 1)
        is_future_mo = date(year, month, 1) > date(today.year, today.month, 1)

        # Obtener excepciones del período visto
        # TEST ITER 1: sincronizar correctamente con active_period_key
        exceptions = self.exceptions_by_period.get(viewing_key, [])
        if viewing_key == self.active_period_key:
            exceptions = self.exceptions  # estado en vivo (no guardado aún)

        shifts = self.controller.preview_shifts(year, month, exceptions)

        exc_map = {}
        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                exc_map[(exc['persona'], exc['fecha'].day)] = exc['tipo']

        turno_days = {}
        for sh in shifts:
            p = sh['persona']
            if not p: continue
            s, e = sh['semana']
            cur = s
            while cur <= e:
                if cur.month == month and cur.year == year:
                    turno_days.setdefault(p, set()).add(cur.day)
                cur += timedelta(days=1)

        for exc in exceptions:
            if exc['fecha'].month == month and exc['fecha'].year == year:
                turno_days.get(exc['persona'], set()).discard(exc['fecha'].day)

        # Semana actual
        cur_week_days: set = set()
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

        personal   = self.controller.get_personal_list()
        _, days_in = calendar.monthrange(year, month)

        # El calendario solo necesita mostrar el total de excepciones.
        stats_row_offset = 0
        n_exc        = len(exceptions)
        exception_summary = ctk.CTkFrame(
            self.vista_scroll, fg_color="transparent", height=28)
        exception_summary.grid(row=stats_row_offset, column=0, sticky="ew",
                               padx=20, pady=(6, 0))
        exception_summary.grid_propagate(False)
        ctk.CTkLabel(
            exception_summary,
            text=f"⚠  {n_exc} excepción{'es' if n_exc != 1 else ''} registrada{'s' if n_exc != 1 else ''}",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=P["text_w"], anchor="w").pack(side="left")

        # ── Título del calendario ─────────────────────────────────────────────
        hl = ctk.CTkFrame(self.vista_scroll, fg_color="transparent")
        hl.grid(row=stats_row_offset + 1, column=0, sticky="ew", padx=20, pady=(6, 2))
        hl.grid_columnconfigure(0, weight=1)

        # TEST ITER 3: título refleja el estado del mes
        if is_past_mo:
            titulo_color = P["text_s"]
            titulo_txt   = f"🗄  Historial — {MESES[month-1]} {year}"
        elif is_future_mo:
            titulo_color = P["text_a"]
            titulo_txt   = f"🔮  Previsualización — {MESES[month-1]} {year}"
        else:
            titulo_color = P["text"]
            titulo_txt   = f"Calendario — {MESES[month-1]} {year}"

        ctk.CTkLabel(hl, text=titulo_txt,
                     font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                     text_color=titulo_color).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hl,
                     text="■ Turno  ·  DA Día Admin  ·  FL Feriado  ·  "
                         "Sombreado = fin de semana  ·  Azul = semana actual",
                     font=ctk.CTkFont(family="Inter", size=11),
                     text_color=P["text_s"]).grid(row=1, column=0, sticky="w")

        # ── TEST ITER 2: Estado vacío ─────────────────────────────────────────
        if not shifts:
            empty_f = ctk.CTkFrame(self.vista_scroll, fg_color=P["bg_card"],
                                   corner_radius=12, border_width=1, border_color=P["border"])
            empty_f.grid(row=stats_row_offset + 2, column=0, sticky="ew",
                         padx=16, pady=(4, 16))
            ctk.CTkLabel(empty_f,
                         text="📭  Sin turnos generados para este periodo",
                         font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
                         text_color=P["text_s"]).pack(pady=(20, 6))
            ctk.CTkLabel(empty_f,
                         text="Asegúrate de haber exportado el mes desde la pestaña Planificación.",
                         font=ctk.CTkFont(family="Inter", size=12),
                         text_color=P["text_s"]).pack(pady=(0, 20))
            return

        # ══════════════════════════════════════════════════════════════════════
        #  GRILLA UNIFICADA — header y filas en el MISMO grid (cal_table)
        # ══════════════════════════════════════════════════════════════════════
        CELL_W = 30
        CELL_H = 46
        HDR_H  = 58
        NAME_W = 186

        # TEST ITER 3: tinte más oscuro para meses pasados
        card_bg = P["past_tint"] if is_past_mo else P["bg_card"]

        cal_outer = ctk.CTkFrame(self.vista_scroll, fg_color=card_bg,
                                 corner_radius=12, border_width=1,
                                 border_color=P["border"] if not is_past_mo else "#141830")
        cal_outer.grid(row=stats_row_offset + 2, column=0, sticky="ew",
                       padx=16, pady=(4, 16))
        cal_outer.grid_columnconfigure(0, weight=1)
        cal_outer.grid_rowconfigure(0, weight=1)

        h_sb = tk.Scrollbar(cal_outer, orient="horizontal",
                            bg=card_bg, troughcolor=P["bg_hdr"],
                            activebackground=P["border_h"])
        h_sb.grid(row=1, column=0, sticky="ew")

        canvas = tk.Canvas(cal_outer, bg=card_bg,
                           highlightthickness=0, bd=0,
                           xscrollcommand=h_sb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        h_sb.config(command=canvas.xview)

        cal_table = tk.Frame(canvas, bg=card_bg)
        win_id = canvas.create_window((0, 0), window=cal_table, anchor="nw")

        def _tbl_cfg(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.configure(height=cal_table.winfo_reqheight())
        cal_table.bind("<Configure>", _tbl_cfg)

        def _cvs_cfg(e):
            if cal_table.winfo_reqwidth() < e.width:
                canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _cvs_cfg)

        cal_table.grid_columnconfigure(0, minsize=NAME_W)
        for c in range(1, days_in + 1):
            cal_table.grid_columnconfigure(c, minsize=CELL_W)

        # ── Header ────────────────────────────────────────────────────────────
        hdr_bg = P["bg_hdr"] if not is_past_mo else "#0A0C14"
        corner = tk.Frame(cal_table, bg=hdr_bg, width=NAME_W, height=HDR_H)
        corner.grid(row=0, column=0, sticky="nsew")
        corner.grid_propagate(False)
        tk.Label(corner, text="PERSONAL", bg=hdr_bg, fg=P["text_s"],
                 font=("Inter", 9, "bold"), anchor="w"
                 ).place(x=14, rely=0.5, anchor="w")
        tk.Frame(corner, bg=P["border"], width=1).place(
            relx=1.0, rely=0, anchor="ne", relheight=1.0)

        for d in range(1, days_in + 1):
            wd       = date(year, month, d).weekday()
            is_we    = wd >= 5
            is_today = is_cur_mo and today.day == d
            in_cw    = d in cur_week_days

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

            tc_n = "#FFF" if is_today else (P["text_a"] if in_cw else
                                             (P["text_s"] if is_we else "#CBD5E1"))
            # TEST ITER 3: texto más tenue en meses pasados
            if is_past_mo and not is_today:
                tc_n = "#3A4260"

            tk.Label(df, text=DIAS[wd], bg=bg,
                     fg=P["text_s"] if not is_today else "#93C5FD",
                     font=("Inter", 8)).place(relx=0.5, rely=0.28, anchor="center")
            tk.Label(df, text=str(d), bg=bg, fg=tc_n,
                     font=("Inter", 12, "bold" if is_today or in_cw else "normal")
                     ).place(relx=0.5, rely=0.68, anchor="center")

        tk.Frame(cal_table, bg=P["border_h"], height=2
                 ).grid(row=1, column=0, columnspan=days_in + 1, sticky="ew")

        # ── Filas de personas ─────────────────────────────────────────────────
        row_bg_e = P["bg_row_e"] if not is_past_mo else "#0C0E1C"
        row_bg_o = P["bg_row_o"] if not is_past_mo else "#0E1020"
        name_bg  = P["bg_name"]  if not is_past_mo else "#0A0C1E"

        for ri, persona in enumerate(personal):
            p_turno  = turno_days.get(persona, set())
            av_color = AVATAR_PAL[ri % len(AVATAR_PAL)]
            row_bg   = row_bg_e if ri % 2 == 0 else row_bg_o
            rnum     = ri + 2

            row_widgets = []

            name_f = tk.Frame(cal_table, bg=name_bg, width=NAME_W, height=CELL_H)
            name_f.grid(row=rnum, column=0, sticky="nsew")
            name_f.grid_propagate(False)
            row_widgets.append((name_f, name_bg))

            AV = 28
            av_c = tk.Canvas(name_f, width=AV, height=AV,
                             bg=name_bg, highlightthickness=0)
            av_c.place(x=8, rely=0.5, anchor="w")
            av_c.create_oval(0, 0, AV, AV, fill=av_color, outline="")
            av_c.create_text(AV // 2, AV // 2, text=_initials(persona),
                             fill="#FFF", font=("Inter", 8, "bold"))
            row_widgets.append((av_c, name_bg))

            lbl_n = tk.Label(name_f, text=_short_name(persona, 2),
                             bg=name_bg, fg=P["text"] if not is_past_mo else P["text_s"],
                             font=("Inter", 11, "bold"), anchor="w")
            lbl_n.place(x=AV + 14, rely=0.5, anchor="w", width=NAME_W - AV - 20)
            row_widgets.append((lbl_n, name_bg))

            border_line = tk.Frame(name_f, bg=P["border"], width=1)
            border_line.place(relx=1.0, x=-1, rely=0, anchor="ne", relheight=1.0)

            for d in range(1, days_in + 1):
                wd       = date(year, month, d).weekday()
                is_we    = wd >= 5
                exc_tipo = exc_map.get((persona, d))
                has_t    = d in p_turno
                in_cw    = d in cur_week_days

                if exc_tipo == "DA":
                    bg, txt, tc, bold = P["da"],     "DA", "#FFF", True
                elif exc_tipo == "FL":
                    bg, txt, tc, bold = P["fl"],     "FL", "#FFF", True
                elif has_t:
                    # Turno: más brillante en semana actual, atenuado en meses pasados
                    if is_past_mo:
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

                if txt:
                    lbl = tk.Label(cf, text=txt, bg=bg, fg=tc,
                                   font=("Inter", 10, "bold" if bold else "normal"))
                    lbl.place(relx=0.5, rely=0.5, anchor="center")

            _make_row_hover(cal_table, row_widgets)

            if ri < len(personal) - 1:
                tk.Frame(cal_table, bg=P["sep"], height=1
                         ).grid(row=rnum, column=0, columnspan=days_in + 1, sticky="s")

        # ── Tarjetas de semanas ───────────────────────────────────────────────
        ctk.CTkLabel(self.vista_scroll, text="Detalle por semana",
                     font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
                     text_color=P["text"] if not is_past_mo else P["text_s"]
                     ).grid(row=stats_row_offset + 3, column=0,
                            padx=20, pady=(12, 4), sticky="w")

        co = ctk.CTkFrame(self.vista_scroll, fg_color="transparent")
        co.grid(row=stats_row_offset + 4, column=0, sticky="ew", padx=16, pady=(0, 24))
        co.grid_columnconfigure(0, weight=1)
        co.grid_columnconfigure(1, weight=1)

        for idx, shift in enumerate(shifts):
            s_date, e_date = shift['semana']
            persona  = shift['persona'] or "NADIE DISPONIBLE"
            saltados = shift.get('saltados', [])
            is_cw    = (s_date <= today <= e_date)
            av_idx   = personal.index(persona) if persona in personal else 0
            av_color = AVATAR_PAL[av_idx % len(AVATAR_PAL)] if persona != "NADIE DISPONIBLE" else P["border"]

            # TEST ITER 3: tarjetas atenuadas para meses pasados
            card_fg  = P["past_tint"] if is_past_mo else P["bg_card2"]
            card_bdr = P["today"] if is_cw else (P["border"] if not is_past_mo else "#141830")

            card = ctk.CTkFrame(co, fg_color=card_fg, corner_radius=12,
                                border_width=2 if is_cw else 1,
                                border_color=card_bdr)
            card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            crow = 0

            if is_cw:
                top_bar = ctk.CTkFrame(card, fg_color=P["today"], height=4, corner_radius=0)
                top_bar.grid(row=crow, column=0, sticky="ew")
                crow += 1
                bf = ctk.CTkFrame(card, fg_color=P["today_bg"], corner_radius=6)
                bf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(bf, text="  ● SEMANA ACTUAL  ",
                             font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                             text_color=P["accent"]).pack(padx=2, pady=3)
                crow += 1

            # TEST ITER 2: badge "HISTORIAL" para semanas de meses pasados
            if is_past_mo:
                hf = ctk.CTkFrame(card, fg_color="#1A1505", corner_radius=6)
                hf.grid(row=crow, column=0, padx=12, pady=(8, 0), sticky="w")
                ctk.CTkLabel(hf, text="  🗄 HISTORIAL  ",
                             font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                             text_color=P["text_w"]).pack(padx=2, pady=3)
                crow += 1

            ctk.CTkLabel(card,
                         text=f"{s_date.strftime('%d %b')} — {e_date.strftime('%d %b')}".upper(),
                         font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                         text_color=P["text_a"] if not is_past_mo else P["text_s"]
                         ).grid(row=crow, column=0, padx=14,
                                pady=(10 if not (is_cw or is_past_mo) else 6, 4), sticky="w")
            crow += 1

            badge = ctk.CTkFrame(card, fg_color=P["bg_card"], corner_radius=10,
                                 border_width=1, border_color=P["border_h"])
            badge.grid(row=crow, column=0, padx=10, pady=(0, 8), sticky="ew")
            badge.grid_columnconfigure(1, weight=1)
            crow += 1

            av = _avatar_ctk(badge, _initials(persona), av_color, size=40)
            av.grid(row=0, column=0, padx=(10, 8), pady=10)

            info_c = ctk.CTkFrame(badge, fg_color="transparent")
            info_c.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=8)
            ctk.CTkLabel(info_c, text=_short_name(persona, 4),
                         font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
                         text_color=P["text"], anchor="w", wraplength=260
                         ).pack(fill="x")

            dias = []
            cur = s_date
            while cur <= e_date:
                if cur.month == month and cur.year == year:
                    dias.append(str(cur.day))
                cur += timedelta(days=1)
            if dias:
                ctk.CTkLabel(info_c, text="📌  Días: " + ", ".join(dias),
                             font=ctk.CTkFont(family="Inter", size=11),
                             text_color=P["text_s"], anchor="w").pack(fill="x")

            if saltados:
                ef = ctk.CTkFrame(card, fg_color="transparent")
                ef.grid(row=crow, column=0, padx=10, pady=(0, 10), sticky="ew")
                ef.grid_columnconfigure(0, weight=1)
                crow += 1
                for si, exc_info in enumerate(saltados):
                    tipo  = exc_info['tipo']
                    cc    = P["da"] if tipo == "DA" else P["fl"]
                    icon  = "⏭" if tipo == "DA" else "🚫"
                    cf2   = ctk.CTkFrame(ef, fg_color=cc, corner_radius=8)
                    cf2.grid(row=si, column=0, sticky="ew", pady=2)
                    ctk.CTkLabel(cf2,
                                 text=f"{icon}  {_short_name(exc_info['persona'], 2)}  ·  {tipo}",
                                 font=ctk.CTkFont(family="Inter", size=11),
                                 text_color="#FFF").pack(padx=10, pady=5)
            else:
                ctk.CTkFrame(card, height=6, fg_color="transparent").grid(row=crow, column=0)

    # ══════════════════════════════════════════════════════════════════════════
    #  LÓGICA DE NEGOCIO
    # ══════════════════════════════════════════════════════════════════════════
    def load_personal(self):
        self.exceptions_by_period = self.controller.get_saved_exceptions()
        self.active_period_key = self.get_selected_period_key()
        self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
        personal = self.controller.get_personal_list()
        if personal:
            self.person_dropdown.configure(values=personal)
            self.person_var.set(personal[0])
        else:
            self.person_dropdown.configure(values=["Sin personal disponible"])
            self.person_var.set("Sin personal disponible")
            self.set_status("No hay personal disponible.", "error")
        self.update_preview()

    def get_selected_period(self):
        year  = int(self.year_var.get())
        month = MESES.index(self.month_var.get()) + 1
        return year, month

    def get_selected_period_key(self):
        year, month = self.get_selected_period()
        return f"{year}-{month:02d}"

    def on_period_change(self):
        if self.active_period_key is not None:
            self.exceptions_by_period[self.active_period_key] = self.exceptions
        self.active_period_key = self.get_selected_period_key()
        self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
        self.plan_period_dirty = True
        self.refresh_exception_list()
        self.update_preview()

    def set_status(self, text, level="info"):
        cfg = {
            "info":  (P["text_s"],  P["bg_card"]),
            "ok":    (P["text_ok"], "#063616"),
            "warn":  (P["text_w"],  "#2C1A00"),
            "error": (P["text_e"],  "#2A0808"),
        }
        tc, bg = cfg.get(level, cfg["info"])
        self._status_frame.configure(fg_color=bg)
        self.status_label.configure(text=text, text_color=tc)

    def refresh_exception_list(self):
        for w in self.exception_list2.winfo_children():
            w.destroy()

        count = len(self.exceptions)
        ct = (f"{count} excepción{'es' if count != 1 else ''} registrada{'s' if count != 1 else ''}"
              if count else "Ninguna registrada")
        self.exc_count_label2.configure(text=ct)

        if not self.exceptions:
            ctk.CTkLabel(self.exception_list2, text="Sin excepciones para este periodo.",
                         text_color=P["text_s"],
                         font=ctk.CTkFont(family="Inter", size=12),
                         wraplength=220).pack(padx=8, pady=12)
            return

        for index, exc in enumerate(self.exceptions):
            tipo   = exc['tipo']
            chip_c = P["da"] if tipo == "DA" else P["fl"]
            row = ctk.CTkFrame(self.exception_list2, fg_color=P["bg_card2"], corner_radius=8,
                               border_width=1, border_color=P["border"])
            row.pack(fill="x", padx=4, pady=3)
            row.grid_columnconfigure(0, weight=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
            ctk.CTkFrame(left, width=4, height=36, fg_color=chip_c,
                         corner_radius=2).pack(side="left", padx=(0, 8))
            info = ctk.CTkFrame(left, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(info, text=_short_name(exc['persona'], 2),
                         font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
                         text_color=P["text"], anchor="w").pack(fill="x")
            ctk.CTkLabel(info,
                         text=f"{exc['fecha'].strftime('%d/%m/%Y')}  ·  {tipo}",
                         font=ctk.CTkFont(family="Inter", size=11),
                         text_color=P["text_s"], anchor="w").pack(fill="x")

            ctk.CTkButton(row, text="✕", width=28, height=28,
                          fg_color=P["bg_card"], hover_color=P["red_d"],
                          font=ctk.CTkFont(size=12),
                          command=lambda i=index: self.remove_exception(i)
                          ).grid(row=0, column=1, padx=6, pady=6)

    def remove_exception(self, index):
        removed = self.exceptions.pop(index)
        self.exceptions_by_period[self.active_period_key] = self.exceptions
        self.refresh_exception_list()
        self.update_preview()
        self._mark_dirty()
        self.set_status(f"Excepción eliminada: {removed['fecha'].strftime('%d/%m/%Y')}", "warn")

    def add_exception(self):
        """
        TEST ITER 1 — Mejoras de validación:
        1. Mensaje de error más específico para días fuera de rango
        2. Se muestra cuántos días se agregaron exitosamente
        3. Se previene agregar días en meses pasados (warning)
        UX MEJORA: borde rojo en campo de días al fallar validación
        """
        person   = self.person_var.get()
        days_str = self.days_entry.get()
        exc_type = self.type_var.get()
        year, month = self.get_selected_period()

        if not person or person in ("Cargando...", "Sin personal disponible"):
            self.set_status("Selecciona una persona válida.", "error"); return
        if not days_str.strip():
            self.days_entry.configure(border_color=P["red"])
            self.set_status("Debes ingresar al menos un día.", "error"); return

        # TEST ITER 1: advertencia si el mes ya pasó
        today = date.today()
        if date(year, month, 1) < date(today.year, today.month, 1):
            if not messagebox.askyesno(
                "Mes pasado",
                f"Estás agregando una excepción en {MESES[month-1]} {year}, "
                f"que ya pasó.\n¿Continuar de todas formas?",
                parent=self):
                return

        try:
            raw_days = [int(d.strip()) for d in days_str.split(",") if d.strip()]
            if not raw_days: raise ValueError("Sin días")

            # TEST ITER 1 FIX: validar rango del mes antes de crear la fecha
            _, last_day = calendar.monthrange(year, month)
            invalid_days = [d for d in raw_days if not (1 <= d <= last_day)]
            if invalid_days:
                inv_str = ", ".join(str(d) for d in invalid_days)
                self.days_entry.configure(border_color=P["red"])
                self.set_status(
                    f"Días fuera del rango 1–{last_day}: {inv_str}", "error")
                return

            new_exc = []
            for day in raw_days:
                date_obj  = datetime(year, month, day).date()
                candidate = {'persona': person, 'fecha': date_obj, 'tipo': exc_type}
                existing_dates = {
                    (exc['persona'], exc['fecha']) for exc in self.exceptions + new_exc
                }
                if (person, date_obj) in existing_dates:
                    self.days_entry.configure(border_color=P["orange"])
                    self.set_status(
                        f"Ya existe excepción para {_short_name(person)} "
                        f"el {date_obj.strftime('%d/%m/%Y')}.", "warn")
                    return
                new_exc.append(candidate)

            self.exceptions.extend(new_exc)
            self.exceptions_by_period[self.active_period_key] = self.exceptions
            self.refresh_exception_list()
            self.days_entry.delete(0, 'end')
            self.days_entry.focus_set()
            self.update_preview()
            self._mark_dirty()
            n = len(new_exc)
            # TEST ITER 1: mensaje más descriptivo con días y tipo
            dias_str = ", ".join(e['fecha'].strftime('%d/%m') for e in new_exc)
            self.set_status(
                f"✓ {n} excepción{'es' if n > 1 else ''} {exc_type} "
                f"para {_short_name(person)}: {dias_str}", "ok")

        except ValueError as ve:
            self.set_status("Ingresa números de día válidos, ej: 1, 15, 22.", "error")
        except Exception as ex:
            self.set_status(f"Error inesperado: {str(ex)}", "error")

    def save_and_export(self):
        if self.is_exporting: return
        year, month = self.get_selected_period()

        # #1 — Diálogo de confirmación con resumen antes de exportar
        shifts_preview = self.controller.preview_shifts(year, month, self.exceptions)
        n_semanas = len(shifts_preview)
        n_exc     = len(self.exceptions)
        confirmed = messagebox.askyesno(
            "Confirmar exportación",
            f"¿Exportar {MESES[month-1]} {year}?\n\n"
            f"  \u2022 {n_semanas} semana{'s' if n_semanas != 1 else ''} calculada{'s' if n_semanas != 1 else ''}\n"
            f"  \u2022 {n_exc} excepción{'es' if n_exc != 1 else ''} registrada{'s' if n_exc != 1 else ''}\n\n"
            "Se generará el archivo Excel.\n"
            "Luego podrás decidir si guardar en historial.",
            parent=self)
        if not confirmed:
            return

        self.is_exporting = True
        self.save_export_btn.configure(state="disabled", text="⏳  Exportando...")
        self.set_status("Generando archivo Excel...", "warn")

        # #8 — Exportación en hilo secundario para no bloquear la UI
        exceptions_snapshot = list(self.exceptions)

        def _on_export_done(ok, msg):
            """Callback ejecutado en el hilo principal vía self.after."""
            self.is_exporting = False
            self.save_export_btn.configure(state="normal", text="📤  Exportar y guardar")
            if not ok:
                self.set_status(f"Error: {msg}", "error")
                return

            advance = messagebox.askyesno(
                "Exportación completada",
                "El archivo Excel se generó correctamente.\n\n"
                "¿Guardar este mes en el historial JSON y avanzar la cola?",
                parent=self)
            if not advance:
                self.set_status("Excel exportado. El mes sigue abierto.", "ok")
                return

            self.save_export_btn.configure(state="disabled", text="Cerrando mes...")
            ok2, msg2 = self.controller.advance_queue(year, month, exceptions_snapshot)
            if not ok2:
                self.save_export_btn.configure(state="normal", text="📤  Exportar y guardar")
                self.set_status(f"Excel exportado, pero no se pudo cerrar: {msg2}", "warn")
                return

            self.set_status("Mes exportado y guardado en el historial JSON.", "ok")
            self._mark_clean()
            self.exceptions = []
            self.exceptions_by_period[self.active_period_key] = []

            y, m = self.get_selected_period()
            m = m % 12 + 1
            if m == 1: y += 1
            self.month_var.set(MESES[m - 1])
            self.year_var.set(str(y))
            self.calendar_period_override = (year, month)
            self.active_period_key = self.get_selected_period_key()
            self.exceptions = self.exceptions_by_period.get(self.active_period_key, []).copy()
            self.refresh_exception_list()
            self.load_personal()
            self.save_export_btn.configure(state="normal", text="📤  Exportar y guardar")

        def _thread_worker():
            result = self.controller.process_generation(year, month, exceptions_snapshot)
            self.after(0, lambda: _on_export_done(*result))

        threading.Thread(target=_thread_worker, daemon=True).start()

    def update_preview(self):
        if not hasattr(self, 'year_var'): return
        year, month = self.get_selected_period()
        shifts = self.controller.preview_shifts(year, month, self.exceptions)

        self.preview_textbox.configure(state="normal")
        self.preview_textbox.delete("0.0", "end")
        self.preview_textbox.insert("end", f"{'─'*38}\n")
        self.preview_textbox.insert("end", f"  {MESES[month-1].upper()} {year}\n")
        self.preview_textbox.insert("end", f"{'─'*38}\n\n")

        for sh in shifts:
            s, e   = sh['semana']
            person = sh['persona'] or "NADIE DISPONIBLE"
            salt   = sh.get('saltados', [])
            self.preview_textbox.insert("end",
                f"  {s.strftime('%d/%m')} → {e.strftime('%d/%m')}\n"
                f"  👤 {_short_name(person, 2)}\n")
            for sk in salt:
                self.preview_textbox.insert("end",
                    f"     ↷ {_short_name(sk['persona'], 1)} ({sk['tipo']})\n")
            self.preview_textbox.insert("end", "\n")

        self.preview_textbox.configure(state="disabled")
