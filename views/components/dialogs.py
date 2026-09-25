import customtkinter as ctk
from views.theme import P, EXC_COLORS
from views.components.widgets import _short_name
from utils.email_notifier import is_valid_email

class CustomInputDialog:
    @classmethod
    def show(cls, parent, title, prompt, initialvalue=""):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("400x210")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        ctk.CTkLabel(
            dialog, text=prompt,
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=P["text"]
        ).pack(pady=(20, 12))

        entry = ctk.CTkEntry(
            dialog, width=300, height=36,
            fg_color=P["bg_input"], border_color=P["border"]
        )
        entry.pack(pady=(0, 20))
        if initialvalue:
            entry.insert(0, initialvalue)
        entry.focus()

        def submit():
            result[0] = entry.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40)
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color=P["bg_card2"], hover_color=P["border_h"],
            text_color=P["text"], command=cancel, width=130, height=36
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Aceptar",
            fg_color=P["accent_d"], hover_color=P["accent"],
            text_color=P["text"], command=submit, width=130, height=36
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: cancel())

        parent.wait_window(dialog)
        return result[0]


class CustomConfirmDialog:
    @classmethod
    def show(cls, parent, title, prompt, is_danger=False, confirm_text="Confirmar", cancel_text="Cancelar"):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("420x210")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        result = [False]

        ctk.CTkLabel(
            dialog, text=prompt,
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=P["text"], wraplength=370, justify="center"
        ).pack(pady=(28, 20))

        def submit():
            result[0] = True
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40)

        confirm_color = P["red_d"] if is_danger else P["accent_d"]
        confirm_hover = P["red"] if is_danger else P["accent"]

        ctk.CTkButton(
            btn_frame, text=cancel_text,
            fg_color=P["bg_card2"], hover_color=P["border_h"],
            text_color=P["text"], command=cancel, width=130, height=36
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text=confirm_text,
            fg_color=confirm_color, hover_color=confirm_hover,
            command=submit, width=130, height=36
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: cancel())

        parent.wait_window(dialog)
        return result[0]


class AddExceptionDialog:
    @classmethod
    def show(cls, parent, persona, day, callback):
        dialog = ctk.CTkToplevel(parent)
        dialog.title("Añadir Excepción")
        dialog.geometry("320x190")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(
            dialog,
            text=f"Añadir excepción para\n{_short_name(persona, 3)} el día {day}",
            font=ctk.CTkFont(family="Inter", size=14, weight="bold"),
            text_color=P["text"]
        ).pack(pady=(16, 8))

        def on_select(tipo):
            dialog.destroy()
            callback(tipo)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_frame, text="DA (Día Admin)", fg_color=P["orange"], hover_color=P["da"],
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            command=lambda: on_select("DA")
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="FL (Feriado Legal)", fg_color=P["purple"], hover_color=P["fl"],
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            command=lambda: on_select("FL")
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="LIC (Licencia)", fg_color=P["lic"], hover_color=P["lic"],
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            command=lambda: on_select("LIC")
        ).grid(row=1, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="OTR (Otro)", fg_color=P["otr"], hover_color=P["border"],
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            command=lambda: on_select("OTR")
        ).grid(row=1, column=1, padx=4, pady=4, sticky="ew")


class SelectPersonDialog:
    @classmethod
    def show(cls, parent, title, prompt, persons, current_person=None):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("440x230")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        ctk.CTkLabel(
            dialog, text=prompt,
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=P["text"], wraplength=380, justify="center"
        ).pack(pady=(20, 10))

        initial_val = current_person if current_person in persons else (persons[0] if persons else "")
        selected_var = ctk.StringVar(value=initial_val)
        dropdown = ctk.CTkOptionMenu(
            dialog, variable=selected_var, values=persons, width=360, height=36,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family="Inter", size=12)
        )
        dropdown.pack(pady=(0, 20))

        def submit():
            result[0] = selected_var.get()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=40)
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color=P["bg_card2"], hover_color=P["border_h"],
            text_color=P["text"], command=cancel, width=140, height=36
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Asignar Guardia",
            fg_color=P["green_d"], hover_color=P["green"],
            text_color=P["text"], command=submit, width=140, height=36,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: cancel())

        parent.wait_window(dialog)
        return result[0]


class PersonFormDialog:
    @classmethod
    def show(cls, parent, title, initial_name="", initial_email=""):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("450x300")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        ctk.CTkLabel(
            dialog, text=title,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=P["text"]
        ).pack(pady=(16, 12))

        # Nombre
        ctk.CTkLabel(
            dialog, text="Nombre completo del funcionario:",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", padx=30, pady=(0, 2))

        name_entry = ctk.CTkEntry(
            dialog, width=390, height=34,
            fg_color=P["bg_input"], border_color=P["border"]
        )
        name_entry.pack(padx=30, pady=(0, 8))
        if initial_name:
            name_entry.insert(0, initial_name)

        # Correo
        ctk.CTkLabel(
            dialog, text="Correo electrónico (obligatorio para notificaciones):",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", padx=30, pady=(0, 2))

        email_entry = ctk.CTkEntry(
            dialog, width=390, height=34,
            placeholder_text="ejemplo: funcionario@correo.cl",
            fg_color=P["bg_input"], border_color=P["border"]
        )
        email_entry.pack(padx=30, pady=(0, 4))
        if initial_email:
            email_entry.insert(0, initial_email)

        error_lbl = ctk.CTkLabel(
            dialog, text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=P["red"], anchor="w"
        )
        error_lbl.pack(fill="x", padx=30, pady=(0, 8))

        name_entry.focus()

        def submit():
            name_val = name_entry.get().strip()
            email_val = email_entry.get().strip()

            if not name_val:
                error_lbl.configure(text="El nombre no puede estar vacío.")
                return

            if email_val and not is_valid_email(email_val):
                error_lbl.configure(text="Formato de correo inválido (ej: nombre@dominio.cl).")
                return

            result[0] = (name_val, email_val)
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 14))
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color=P["bg_card2"], hover_color=P["border_h"],
            text_color=P["text"], command=cancel, width=150, height=36
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Guardar",
            fg_color=P["green_d"], hover_color=P["green"],
            text_color=P["text"], command=submit, width=150, height=36,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: cancel())

        parent.wait_window(dialog)
        return result[0]


class ChangeShiftDialog:
    @classmethod
    def show(cls, parent, title, dates_prompt, persons, current_person=None):
        dialog = ctk.CTkToplevel(parent)
        dialog.title(title)
        dialog.geometry("490x380")
        dialog.configure(fg_color=P["bg_card"])
        dialog.transient(parent)
        dialog.grab_set()

        dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        # Banner de advertencia obligatoria
        warn_frame = ctk.CTkFrame(
            dialog, fg_color=P["bg_card2"], corner_radius=8,
            border_width=1, border_color=P["orange"]
        )
        warn_frame.pack(fill="x", padx=24, pady=(16, 10))

        ctk.CTkLabel(
            warn_frame,
            text="⚠ AVISO OBLIGATORIO DE TRANSPARENCIA\n"
                 "Al asignar manualmente este turno y guardar el mes, se enviará una "
                 "notificación automática por correo a TODOS los funcionarios del equipo.",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color=P["orange"], wraplength=420, justify="center"
        ).pack(padx=12, pady=10)

        # Semana afectada
        ctk.CTkLabel(
            dialog, text=f"Semana de guardia: {dates_prompt}",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color=P["text"], anchor="w"
        ).pack(fill="x", padx=24, pady=(4, 6))

        # Selector de persona
        ctk.CTkLabel(
            dialog, text="Nuevo funcionario asignado a la guardia:",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 2))

        initial_val = current_person if current_person in persons else (persons[0] if persons else "")
        selected_var = ctk.StringVar(value=initial_val)
        dropdown = ctk.CTkOptionMenu(
            dialog, variable=selected_var, values=persons, width=440, height=34,
            fg_color=P["bg_input"], button_color=P["accent_d"],
            button_hover_color=P["accent"], dropdown_fg_color=P["bg_card2"],
            font=ctk.CTkFont(family="Inter", size=12)
        )
        dropdown.pack(padx=24, pady=(0, 8))

        # Motivo obligatorio
        ctk.CTkLabel(
            dialog, text="Motivo del cambio (Obligatorio para la notificación):",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 2))

        motive_entry = ctk.CTkEntry(
            dialog, width=440, height=34,
            placeholder_text="Ej: Permuta con Juan Pérez / Solicitud por fuerza mayor",
            fg_color=P["bg_input"], border_color=P["border"]
        )
        motive_entry.pack(padx=24, pady=(0, 4))
        motive_entry.focus()

        error_lbl = ctk.CTkLabel(
            dialog, text="",
            font=ctk.CTkFont(family="Inter", size=11),
            text_color=P["red"], anchor="w"
        )
        error_lbl.pack(fill="x", padx=24, pady=(0, 6))

        def submit():
            motive_val = motive_entry.get().strip()
            if not motive_val:
                error_lbl.configure(text="Debes ingresar obligatoriamente el motivo del cambio.")
                motive_entry.focus()
                return

            chosen = selected_var.get()
            result[0] = (chosen, motive_val)
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(0, 14))
        ctk.CTkButton(
            btn_frame, text="Cancelar",
            fg_color=P["bg_card2"], hover_color=P["border_h"],
            text_color=P["text"], command=cancel, width=170, height=36
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="Aceptar y Registrar",
            fg_color=P["green_d"], hover_color=P["green"],
            text_color=P["text"], command=submit, width=170, height=36,
            font=ctk.CTkFont(family="Inter", size=12, weight="bold")
        ).pack(side="right")

        dialog.bind("<Return>", lambda e: submit())
        dialog.bind("<Escape>", lambda e: cancel())

        parent.wait_window(dialog)
        return result[0]


class LoadingModal:
    """
    Modal de carga no bloqueante para operaciones en segundo plano
    (ej: guardar mes, generar planilla Excel y enviar correos).
    Muestra título, icono de estado, mensaje descriptivo y barra de progreso animada.
    """
    def __init__(self, parent, title="Procesando...", message="Por favor, espere un momento...", icon="⏳"):
        self.parent = parent
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("440x220")
        self.dialog.configure(fg_color=P["bg_card"])
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)

        # Evitar cerrar con la 'X' mientras se ejecuta la tarea
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        try:
            self.dialog.lift()
            self.dialog.attributes("-topmost", True)
        except Exception:
            pass

        try:
            self.dialog.grab_set()
        except Exception:
            pass

        # Centrar sobre la ventana padre
        self.dialog.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 440) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 220) // 2
            self.dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        # Contenedor interior estilizado
        inner = ctk.CTkFrame(
            self.dialog, fg_color=P["bg_card2"],
            corner_radius=12, border_width=1, border_color=P["border"]
        )
        inner.pack(fill="both", expand=True, padx=14, pady=14)

        self.lbl_icon = ctk.CTkLabel(
            inner, text=icon,
            font=ctk.CTkFont(size=28),
            text_color=P["accent"]
        )
        self.lbl_icon.pack(pady=(16, 4))

        self.lbl_title = ctk.CTkLabel(
            inner, text=title,
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color=P["text"]
        )
        self.lbl_title.pack(pady=(0, 4))

        self.lbl_message = ctk.CTkLabel(
            inner, text=message,
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=P["text_s"], wraplength=380, justify="center"
        )
        self.lbl_message.pack(pady=(0, 16))

        self.progressbar = ctk.CTkProgressBar(
            inner, mode="indeterminate",
            width=340, height=8, corner_radius=4,
            fg_color=P["bg_input"], progress_color=P["accent"]
        )
        self.progressbar.pack(pady=(0, 14))
        self.progressbar.start()

        try:
            self.dialog.update()
        except Exception:
            pass

    def update_status(self, message=None, title=None, icon=None):
        """Actualiza el texto y estado del modal de forma segura entre hilos."""
        def _apply():
            try:
                if not self.dialog.winfo_exists():
                    return
                if icon is not None:
                    self.lbl_icon.configure(text=icon)
                if title is not None:
                    self.lbl_title.configure(text=title)
                if message is not None:
                    self.lbl_message.configure(text=message)
                self.dialog.update_idletasks()
            except Exception:
                pass

        if self.parent:
            self.parent.after(0, _apply)

    def close(self):
        """Cierra el modal de forma segura."""
        def _destroy():
            try:
                self.progressbar.stop()
            except Exception:
                pass
            try:
                if self.dialog.winfo_exists():
                    self.dialog.grab_release()
                    self.dialog.destroy()
            except Exception:
                pass

        if self.parent:
            self.parent.after(0, _destroy)

