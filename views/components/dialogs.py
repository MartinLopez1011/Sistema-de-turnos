import customtkinter as ctk
from views.theme import P, EXC_COLORS
from views.components.widgets import _short_name

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
