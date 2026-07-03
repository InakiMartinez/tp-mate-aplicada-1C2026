import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from util import Util
from zxcvbn import zxcvbn
import re

# Configuración estética global
ctk.set_appearance_mode("dark")  # Modo oscuro nativo
ctk.set_default_color_theme("green")  # Estilo verde para acentuar seguridad

class PasswordManagerGUI(ctk.CTk):
    CRITERIA_LABELS = {
        "length":  "Mínimo 12 caracteres",
        "lower":   "Al menos una minúscula",
        "upper":   "Al menos una mayúscula",
        "digit":   "Al menos un número",
        "special": "Al menos un carácter especial",
    }

    def __init__(self):
        super().__init__()

        self.util = Util("config.ini")
        # Guardamos la ruta del archivo de credenciales de la config original
        self.credentials_file = self.util.config['Files']['credentials']
        self.last_mtime = self.get_file_mtime()

        self.title("PassMan - Administrador Criptográfico de Contraseñas")
        self.resizable(False, False)

        # Centramos la ventana principal en la pantalla
        win_width, win_height = 950, 700
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)
        self.geometry(f"{win_width}x{win_height}+{x}+{y}")

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        if not self.util.pm.master_exists():
            self.show_setup_view()
        else:
            self.show_login_view()

        # Iniciamos el monitoreo en segundo plano
        self.start_file_watcher()

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def update_password_strength(self, password, progressbar, label):
        if not password:
            progressbar.set(0)
            label.configure(text="", text_color="gray")
            return

        score = zxcvbn(password)["score"]

        progressbar.set((score + 1) / 5)

        if score == 0:
            label.configure(text="🔴 Muy débil", text_color="#ff4d4d", font=("Verdana", 14))
        elif score == 1:
            label.configure(text="🟠 Débil", text_color="#ff9933", font=("Verdana", 14))
        elif score == 2:
            label.configure(text="🟡 Media", text_color="#ffd633", font=("Verdana", 14))
        elif score == 3:
            label.configure(text="🟢 Fuerte", text_color="#66cc66", font=("Verdana", 14))
        else:
            label.configure(text="🟢 Muy fuerte", text_color="#00cc66", font=("Verdana", 14))

    def create_criteria_checklist(self, parent):
        """Crea el frame con la lista de criterios y devuelve los labels para actualizarlos."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        labels = {}
        for key, text in self.CRITERIA_LABELS.items():
            lbl = ctk.CTkLabel(frame, text=f"❌ {text}", font=("Verdana", 13), text_color="#ff4d4d", anchor="w")
            lbl.pack(anchor="w", pady=4)
            labels[key] = lbl
        return frame, labels

    def create_toggle_password_entry(self, parent, placeholder="", width=320, height=44):
        """
        Crea un campo de contraseña con un boton de ojo integrado en el borde
        derecho de la misma barra (en vez de un checkbox aparte).
        """
        BTN_SIZE = 44  # El tamaño del botón que ya agrandamos

        container = ctk.CTkFrame(parent, width=width, height=height, fg_color="transparent")
        container.pack_propagate(False)

        entry = ctk.CTkEntry(container, placeholder_text=placeholder, show="*", font=("Verdana", 16))
        entry.place(x=0, y=0, relwidth=1, relheight=1)

        def toggle_reveal():
            if entry.cget("show") == "*":
                entry.configure(show="")
                btn_eye.configure(text="👁", width=BTN_SIZE, height=BTN_SIZE)
            else:
                entry.configure(show="*")
                btn_eye.configure(text="🙈", width=BTN_SIZE, height=BTN_SIZE)

        btn_eye = ctk.CTkButton(
            container, text="🙈", width=BTN_SIZE, height=BTN_SIZE,
            fg_color="transparent", hover_color="#3a3a3a",
            font=("Verdana", 18), command=toggle_reveal
        )
        btn_eye.place(relx=1.0, rely=0.5, anchor="e", x=-4)

        entry._eye_btn = btn_eye

        return container, entry

    def reapply_password_visibility(self, entry):
        """
        Corrige el bug de customtkinter: insert() programatico rompe el
        show="*" heredado. La reaplicamos segun el icono del boton de ojo,
        que siempre refleja el estado deseado por el usuario.
        """
        desired_show = "" if entry._eye_btn.cget("text") == "👁" else "*"
        entry.configure(show=desired_show)

    def update_criteria_checklist(self, password, labels):
        """Actualiza cada renglon del checklist segun el password actual."""
        criteria = self.util.evaluate_password_criteria(password)
        for key, ok in criteria.items():
            text = self.CRITERIA_LABELS[key]
            if ok:
                labels[key].configure(text=f"✅ {text}", text_color="#66cc66")
            else:
                labels[key].configure(text=f"❌ {text}", text_color="#ff4d4d")

    def get_file_mtime(self):
        """Obtiene la fecha de última modificación del archivo si existe."""
        import os
        if os.path.exists(self.credentials_file):
            return os.path.getmtime(self.credentials_file)
        return 0

    def start_file_watcher(self):
        """Lanza el hilo secundario para monitorear el archivo."""
        import threading
        import time

        def watch():
            while True:
                time.sleep(2)  # Revisa cada 2 segundos
                current_mtime = self.get_file_mtime()

                # Si el archivo cambió y el usuario ya está dentro del Dashboard
                if current_mtime != self.last_mtime:
                    self.last_mtime = current_mtime

                    # Verificamos si el contenedor actual es el dashboard analizando sus widgets
                    # (Si tiene el scroll_frame creado y activo, está en el dashboard)
                    if hasattr(self, 'scroll_frame') and self.scroll_frame.winfo_exists():
                        # Usamos .after() para que la actualización corra de forma segura en el hilo de Tkinter
                        self.after(0, self.refresh_credentials_list)

        watcher_thread = threading.Thread(target=watch, daemon=True)
        watcher_thread.start()

    # =========================================================================
    # VISTA 1: CONFIGURACIÓN INICIAL (Si no existe Master Password)
    # =========================================================================
    def show_setup_view(self):
        self.clear_container()

        # MODIFICADO: Aumentamos el ancho del frame principal de 680 a 760
        frame = ctk.CTkFrame(self.main_container, width=850, height=460)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)

        columns = ctk.CTkFrame(frame, fg_color="transparent")
        columns.pack(fill="both", expand=True, padx=10, pady=10)

        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(20, 10))

        # MODIFICADO: Aumentamos el ancho de la columna de requisitos de 260 a 300
        right_col = ctk.CTkFrame(columns, fg_color="#242424", corner_radius=12, width=300)
        right_col.pack(side="right", fill="y", padx=(10, 20), pady=10)
        right_col.pack_propagate(False) # Asegura que respete el ancho asignado

        # ---- Columna izquierda: controles principales ----
        lbl_title = ctk.CTkLabel(left_col, text="Configurar Master Password", font=("Verdana", 26, "bold"))
        lbl_title.pack(pady=(20, 8), anchor="w")

        lbl_desc = ctk.CTkLabel(
            left_col,
            text="Esta clave protege todas tus credenciales y no puede recuperarse.",
            font=("Verdana", 14), text_color="gray", justify="left"
        )
        lbl_desc.pack(pady=(0, 15), anchor="w")

        pass_row = ctk.CTkFrame(left_col, fg_color="transparent")
        pass_row.pack(pady=8, anchor="w")

        pass_container, self.entry_setup_pass = self.create_toggle_password_entry(
            pass_row, placeholder="Ingrese una contraseña fuerte", width=320, height=50
        )
        pass_container.pack(side="left")

        def copy_setup_password():
            self.clipboard_clear()
            self.clipboard_append(self.entry_setup_pass.get())
            messagebox.showinfo("Copiado", "Contraseña copiada al portapapeles.")

        btn_copy_setup = ctk.CTkButton(
            pass_row, text="Copiar", width=70, height=50, fg_color="#2b5329", hover_color="#386b35",
            font=("Verdana", 14, "bold"), command=copy_setup_password
        )
        btn_copy_setup.pack(side="left", padx=(8, 0))
        self.setup_progress = ctk.CTkProgressBar(left_col, width=320)
        self.setup_progress.pack(pady=(0, 5), anchor="w")
        self.setup_progress.set(0)

        self.setup_strength = ctk.CTkLabel(
            left_col,
            text="",
            font=("Verdana", 12)
        )
        self.setup_strength.pack(anchor="w")


        # ---- Fin ----

        btn_gen = ctk.CTkButton( left_col, text="Generar Clave Segura Automática", height=44, font=("Verdana", 16, "bold"), fg_color="#2b2b2b", hover_color="#3a3a3a", command=self.generate_setup_password )
        btn_gen.pack(pady=5, anchor="w")

        btn_save = ctk.CTkButton( left_col, text="Confirmar y Guardar", height=44, font=("Verdana", 16, "bold"), command=self.handle_setup )
        btn_save.pack(pady=(20, 10), anchor="w")

        # ---- Columna derecha: checklist de criterios ----
        lbl_criteria_title = ctk.CTkLabel( right_col, text="Requisitos", font=("Verdana", 18, "bold"))  
        lbl_criteria_title.pack(pady=(20, 10), padx=20)

        setup_criteria_frame, self.setup_criteria_labels = self.create_criteria_checklist(right_col)
        setup_criteria_frame.pack(padx=20, pady=(0, 20))
        # Pixel art label
        self.anim_label = ctk.CTkLabel(
            right_col,
            text="",
            font=("Courier New", 18, "bold"),
            justify="center"
        )
        self.anim_label.pack(pady=(10, 20))

        # iniciar animación
        self.animate_pixel_art(self.anim_label)

        self.entry_setup_pass.bind(
            "<KeyRelease>",
            lambda e: (
                self.update_password_strength(
                    self.entry_setup_pass.get(),
                    self.setup_progress,
                    self.setup_strength
                ),
                self.update_criteria_checklist(
                    self.entry_setup_pass.get(),
                    self.setup_criteria_labels
                )
            )
        )

    def generate_setup_password(self):
        strong_pass = self.util.get_strong_password()
        self.entry_setup_pass.delete(0, tk.END)
        self.entry_setup_pass.insert(0, strong_pass)

        # Corrige el bug de customtkinter: el insert programático
        # rompe el show="*" heredado.
        self.reapply_password_visibility(self.entry_setup_pass)

        self.update_password_strength(
            strong_pass,
            self.setup_progress,
            self.setup_strength
        )
        self.update_criteria_checklist(strong_pass, self.setup_criteria_labels)
        # messagebox.showinfo("Copia tu contraseña", f"Contraseña fuerte generada:\n\n{strong_pass}\n\nAsegúrate de guardarla en un lugar seguro.")

    def handle_setup(self):
        password = self.entry_setup_pass.get()
        if not password:
            messagebox.showerror("Error", "La contraseña no puede estar vacía.")
            return

        if self.util.is_password_strong(password):
            self.util.pm.create_master(password)
            messagebox.showinfo("Éxito", "¡Master Password configurada con éxito!")
            self.show_login_view()
        else:
            criteria = self.util.evaluate_password_criteria(password)
            missing = [self.CRITERIA_LABELS[k] for k, ok in criteria.items() if not ok]
            detalle = "\n".join(f"• {m}" for m in missing)
            messagebox.showerror(
                "Contraseña Débil",
                f"Te falta cumplir los siguientes criterios:\n\n{detalle}"
            )

    # =========================================================================
    # VISTA 2: DESBLOQUEO / LOGIN
    # =========================================================================
    def show_login_view(self):
        self.clear_container()

        frame = ctk.CTkFrame(self.main_container, width=520, height=380)
        frame.pack_propagate(False)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        lbl_title = ctk.CTkLabel(frame, text="Aplicación Bloqueada", font=("Verdana", 30, "bold"))
        lbl_title.pack(pady=(40, 10))

        lbl_sub = ctk.CTkLabel(frame, text="Ingrese su Master Password\npara descifrar el almacén", text_color="gray", font=("Verdana", 16) )
        lbl_sub.pack(pady=5)

        pass_container, self.entry_login_pass = self.create_toggle_password_entry(
            frame, placeholder="Master Password", width=300
        )
        pass_container.pack(pady=20)
        self.entry_login_pass.bind("<Return>", lambda event: self.handle_login())

        btn_unlock = ctk.CTkButton( frame, text="Desbloquear Almacén", height=44, font=("Verdana", 16, "bold"), command=self.handle_login )
        btn_unlock.pack(pady=(10, 30))

    def handle_login(self):
        password = self.entry_login_pass.get()
        if self.util.pm.verify_master(password):
            self.util.unlocked = True
            self.show_dashboard_view()
        else:
            messagebox.showerror("Error de autenticación", "Master password inválida.")

    # =========================================================================
    # VISTA 3: PANEL PRINCIPAL (DASHBOARD)
    # =========================================================================
    def show_dashboard_view(self):
        self.clear_container()

        # Header del Dashboard
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        lbl_welcome = ctk.CTkLabel(header_frame, text="🔑 Tus Credenciales Protegidas", font=("Verdana", 22, "bold"))
        lbl_welcome.pack(side="left")

        btn_lock = ctk.CTkButton( header_frame, text="🔒 Bloquear App", height=44, font=("Verdana", 16, "bold"), fg_color="#9e2a2b", hover_color="#bd3a42", command=self.handle_lock )
        btn_lock.pack(side="right", padx=5)

        btn_add = ctk.CTkButton( header_frame, text="➕ Agregar Credencial", height=44, font=("Verdana", 16, "bold"), command=self.open_credential_modal )
        btn_add.pack(side="right", padx=5)
                
        search_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self.search_var = tk.StringVar()

        search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text="🔍 Buscar credenciales...",
            width=400
        )
        search_entry.pack(side="left", padx=(5, 5))

        def do_search():
            self.refresh_credentials_list()

        search_btn = ctk.CTkButton(
            search_frame,
            text="🔎",
            width=40,
            height=40,
            fg_color="#2b2b2b",
            hover_color="#3a3a3a",
            command=do_search
        )
        search_btn.pack(side="left")

        # Enter también busca
        search_entry.bind("<Return>", lambda e: do_search())

        # búsqueda en vivo (la que ya tenías)
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_credentials_list())

        # Contenedor Scrolleable para las tarjetas de contraseñas
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#1e1e1e", border_width=1, border_color="#2d2d2d")
        self.scroll_frame.pack(fill="both", expand=True)

        self.refresh_credentials_list()

    def refresh_credentials_list(self):
        # Limpiar elementos anteriores dentro del scroll
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        credentials = dict(
            sorted(
                self.util.pm.load_credentials().items(),
                key=lambda item: item[1]["name"].lower()
            )
        )
        query = self.search_var.get().lower().strip() if hasattr(self, "search_var") else ""
        filtered = {
            cid: data for cid, data in credentials.items()
            if query in data["name"].lower()
        }
        if not filtered:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="No hay credenciales almacenadas todavía.", font=("Verdana", 14, "italic"), text_color="gray")
            lbl_empty.pack(pady=40)
            return

        for idx, (cred_id, data) in enumerate(filtered.items(), 1):
            # Tarjeta/Fila por cada credencial
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#262626", height=78, border_width=1, border_color="#333333")
            card.pack(fill="x", pady=6, padx=10)
            card.pack_propagate(False)

            # Nombre del servicio
            lbl_name = ctk.CTkLabel(card, text=f"{idx}. {data['name']}", font=("Verdana", 14, "bold"), anchor="w")
            lbl_name.pack(side="left", padx=20, fill="x", expand=True)

            # Campos y acciones asociadas por closure
            self.create_card_actions(card, cred_id, data)

    def create_card_actions(self, card, cred_id, data):
        entry_pass = ctk.CTkEntry(card, width=150, fg_color="#1a1a1a", border_width=0)
        entry_pass.insert(0, data['password'])
        entry_pass.configure(state="readonly", show="*")
        entry_pass.pack(side="left", padx=10)

        def toggle_reveal():
            if entry_pass.cget("show") == "*":
                entry_pass.configure(show="")
                btn_reveal.configure(text="👁️Ocultar")
            else:
                entry_pass.configure(show="*")
                btn_reveal.configure(text="👁️Ver")

        # MODIFICADO: Ahora copia estructura JSON clave:valor
        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(data['password'])
            self.update()  # Mantiene el contenido del portapapeles al cerrar la ventana
            messagebox.showinfo(
                "Copiado",
                f"La contraseña de '{data['name']}' fue copiada al portapapeles."
            )
        btn_reveal = ctk.CTkButton(card, text="👁️ Ver", width=90, height=40, fg_color="#3a3a3a", hover_color="#4a4a4a", command=toggle_reveal)
        btn_reveal.pack(side="left", padx=5)

        btn_copy = ctk.CTkButton(card, text="📋 Copiar", width=90, height=40, fg_color="#2b5329", hover_color="#386b35", command=copy_to_clipboard)
        btn_copy.pack(side="left", padx=5)

        btn_edit = ctk.CTkButton(card, text="✏️",width=40, height=40, fg_color="#1f3a60", hover_color="#2a4d7c", command=lambda: self.open_credential_modal(cred_id, data))
        btn_edit.pack(side="left", padx=5)

        btn_del = ctk.CTkButton( card, text="🗑️", width=40, height=40, corner_radius=8, fg_color="#5e1914", hover_color="#7a221b", font=("Segoe UI Emoji", 16), command=lambda: self.handle_delete(cred_id, data['name']) )
        btn_del.pack(side="left", padx=10)

    def handle_delete(self, cred_id, name):
        if messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de que deseas eliminar la credencial de '{name}'?"):
            credentials = self.util.pm.load_credentials()
            if cred_id in credentials:
                del credentials[cred_id]
                self.util.pm.save_credentials(credentials)
                self.refresh_credentials_list()

    def handle_lock(self):
        self.util.lock()
        self.show_login_view()

    # =========================================================================
    # VENTANA MODAL: ALTAS Y MODIFICACIONES
    # =========================================================================
    def open_credential_modal(self, cred_id=None, existing_data=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Agregar Credencial" if not cred_id else "Modificar Credencial")
        modal.geometry("600x600")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        # Centramos el modal respecto a la ventana principal
        self.update_idletasks()

        modal_width = 600
        modal_height = modal.winfo_reqheight() + 400
        x = self.winfo_x() + (self.winfo_width() // 2) - (modal_width // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (modal_height // 2)

        modal.geometry(f"{modal_width}x{modal_height}+{x}+{y}")

        lbl_title = ctk.CTkLabel(modal, text="Datos de la Credencial", font=("Verdana", 18, "bold"))
        lbl_title.pack(pady=(15, 10))

        lbl_name = ctk.CTkLabel(modal, text="Nombre del Sitio / Servicio:", font=("Verdana", 15))
        lbl_name.pack(anchor="w", padx=45)

        entry_name = ctk.CTkEntry(modal, width=500)
        entry_name.pack(pady=(5, 12))

        lbl_pass = ctk.CTkLabel(modal, text="Contraseña:", font=("Verdana", 15))
        lbl_pass.pack(anchor="w", padx=45)

        pass_container, entry_pass = self.create_toggle_password_entry(
            modal, placeholder="", width=500
        )
        pass_container.pack(pady=5)
        progress = ctk.CTkProgressBar(modal, width=500)
        progress.pack(pady=(0,5))
        progress.set(0)

        strength = ctk.CTkLabel(
            modal,
            text="",
            font=("Verdana",12)
        )
        strength.pack()

        modal_criteria_frame, modal_criteria_labels = self.create_criteria_checklist(modal)

        entry_pass.bind(
            "<KeyRelease>",
            lambda e: (
                self.update_password_strength(entry_pass.get(), progress, strength),
                self.update_criteria_checklist(entry_pass.get(), modal_criteria_labels)
            )
        )
        modal_criteria_frame.pack(pady=(8, 5), padx=45, anchor="w")

        if existing_data:
            entry_name.insert(0, existing_data['name'])
            entry_pass.insert(0, existing_data['password'])
            self.reapply_password_visibility(entry_pass)
            self.update_password_strength(
                existing_data['password'],
                progress,
                strength
            )
            self.update_criteria_checklist(existing_data['password'], modal_criteria_labels)

        def generate_modal_password():
            strong_p = self.util.get_strong_password()
            entry_pass.delete(0, tk.END)
            entry_pass.insert(0, strong_p)
            self.reapply_password_visibility(entry_pass)
            self.update_password_strength(strong_p, progress, strength)
            self.update_criteria_checklist(strong_p, modal_criteria_labels)

        btn_gen = ctk.CTkButton(modal, text="Generar Contraseña Fuerte",height=44, font=("Verdana", 16, "bold"), fg_color="#2b2b2b", hover_color="#3a3a3a", command=generate_modal_password)
        btn_gen.pack(pady=(5, 10))

        def save_modal_data():
            name = entry_name.get().strip()
            password = entry_pass.get()

            if not name or not password:
                messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=modal)
                return

            # Warning si la clave es débil, pero se permite continuar
            criteria = self.util.evaluate_password_criteria(password)
            missing = [self.CRITERIA_LABELS[k] for k, ok in criteria.items() if not ok]

            if missing:
                detalle = "\n".join(f"• {m}" for m in missing)
                confirm = messagebox.askyesno(
                    "Contraseña Débil",
                    f"Te falta cumplir los siguientes criterios:\n\n{detalle}\n\n¿Deseas guardarla igualmente?",
                    icon="warning",
                    parent=modal
                )
                if not confirm:
                    return  # El usuario eligió no guardar, se corta el flujo
                # Si confirma, sigue el flujo normal y guarda la contraseña débil

            credentials = self.util.pm.load_credentials()

            if cred_id:
                credentials[cred_id] = {"name": name, "password": password}
            else:
                import base64, os
                new_id = base64.b64encode(os.urandom(12)).decode()
                while credentials.get(new_id) is not None:
                    new_id = base64.b64encode(os.urandom(12)).decode()
                credentials[new_id] = {"name": name, "password": password}

            self.util.pm.save_credentials(credentials)
            # Actualizamos el mtime local para que este cliente sepa que este cambio fue suyo
            self.last_mtime = self.get_file_mtime()

            modal.destroy()
            self.refresh_credentials_list()

        btn_save = ctk.CTkButton( modal, text="Guardar Cambios", height=44, font=("Verdana", 16, "bold"), command=save_modal_data )
        btn_save.pack(pady=(10, 20))
    def animate_pixel_art(self, label, frame_index=0):
        if not hasattr(label, "winfo_exists") or not label.winfo_exists():
            return

        frame_a = (
            "   ▄████▄   \n"
            "  ██▀  ▀██  \n"
            "  ██    ██  \n"
            " █▀██████▀█ \n"
            " █ ██████ █ \n"
            " █▄██████▄█ "
        )

        frame_b = (
            " ✧ ▄████▄ ✧ \n"
            "  ██▀  ▀██  \n"
            "  ██ ░░ ██  \n"
            " █▀██████▀█ \n"
            " █ ██████ █ \n"
            " █▄██████▄█ "
        )

        if frame_index % 2 == 0:
            label.configure(text=frame_a, text_color="#66cc66")
        else:
            label.configure(text=frame_b, text_color="#00cc66")

        label.after(700, self.animate_pixel_art, label, frame_index + 1)

if __name__ == "__main__":
    app = PasswordManagerGUI()
    app.mainloop()