import customtkinter as ctk
from views.theme import P

def _section_header(parent, text, row, pady_top=14):
    """Genera un encabezado de sección con texto en mayúsculas y línea decorativa."""
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.grid(row=row, column=0, sticky="ew", padx=16, pady=(pady_top, 4))
    ctk.CTkLabel(
        f, text=text.upper(),
        font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
        text_color=P["text_s"]
    ).pack(side="left")
    ctk.CTkFrame(f, height=1, fg_color=P["border"]).pack(
        side="left", fill="x", expand=True, padx=(8, 0)
    )
    return f


def _avatar_ctk(parent, initials, color, size=32):
    """Genera un contenedor circular tipo avatar con las iniciales de la persona."""
    c = ctk.CTkFrame(
        parent, width=size, height=size,
        corner_radius=size // 2, fg_color=color
    )
    c.pack_propagate(False)
    ctk.CTkLabel(
        c, text=initials,
        font=ctk.CTkFont(family="Inter", size=max(9, size // 3), weight="bold"),
        text_color="#FFFFFF"
    ).pack(expand=True)
    return c


def _short_name(full, words=2):
    """
    Retorna una versión corta del nombre omitiendo rangos institucionales conocidos.
    Prefijos omitidos: COM, PRO, SBC, (A), (F).
    """
    if not full:
        return ""
    skip = {"COM", "PRO", "SBC", "(A)", "(F)"}
    parts = [p for p in str(full).strip().split() if p.upper() not in skip]
    return " ".join(parts[:words]) if parts else str(full)


def _initials(full):
    """
    Retorna 2 letras iniciales para el avatar, omitiendo prefijos institucionales.
    """
    if not full:
        return "??"
    skip = {"COM", "PRO", "SBC", "(A)", "(F)"}
    parts = [p for p in str(full).strip().split() if p.upper() not in skip]
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[1][0].upper()
    return parts[0][:2].upper() if parts else "??"


def _make_row_hover(ref_widget, row_widgets):
    """
    Efecto hover anti-parpadeo para filas compuestas de widgets.
    Usa debounce con after_cancel() para transitar suavemente entre widgets hijos.
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
            try:
                w.configure(bg=HOVER)
            except Exception:
                pass

    def _do_off():
        state['job'] = None
        state['on'] = False
        for w, orig in row_widgets:
            if orig not in hoverable_colors:
                continue
            try:
                w.configure(bg=orig)
            except Exception:
                pass

    def on_enter(e):
        if state['job'] is not None:
            try:
                ref_widget.after_cancel(state['job'])
            except Exception:
                pass
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
