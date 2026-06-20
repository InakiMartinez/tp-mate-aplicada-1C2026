import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from util import Util

# Configuración estética global
ctk.set_appearance_mode("dark")  # Modo oscuro nativo
ctk.set_default_color_theme("green")  # Estilo verde para acentuar seguridad

class PasswordManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.util = Util("config.ini")
        # Guardamos la ruta del archivo de credenciales de la config original
        self.credentials_file = self.util.config['Files']['credentials']
        self.last_mtime = self.get_file_mtime()
        
        self.title("PassMan - Administrador Criptográfico de Contraseñas")
        self.geometry("750x550")
        self.resizable(False, False)
        
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
        
        frame = ctk.CTkFrame(self.main_container, width=500, height=400)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        lbl_title = ctk.CTkLabel(frame, text="Configurar Master Password", font=("Arial", 22, "bold"))
        lbl_title.pack(pady=(30, 10))
        
        lbl_desc = ctk.CTkLabel(
            frame, 
            text="Esta clave protege todas tus credenciales y no puede recuperarse.\nDebe ser una contraseña fuerte (score 4).",
            font=("Arial", 12), text_color="gray"
        )
        lbl_desc.pack(pady=10, padx=20)
        
        self.entry_setup_pass = ctk.CTkEntry(frame, placeholder_text="Ingrese una contraseña fuerte", show="*", width=340)
        self.entry_setup_pass.pack(pady=15)
        
        btn_gen = ctk.CTkButton(frame, text="Generar Clave Segura Automática", fg_color="#2b2b2b", hover_color="#3a3a3a", command=self.generate_setup_password)
        btn_gen.pack(pady=5)
        
        btn_save = ctk.CTkButton(frame, text="Confirmar y Guardar", font=("Arial", 14, "bold"), command=self.handle_setup)
        btn_save.pack(pady=(25, 30))

    def generate_setup_password(self):
        strong_pass = self.util.get_strong_password()
        self.entry_setup_pass.delete(0, tk.END)
        self.entry_setup_pass.insert(0, strong_pass)
        messagebox.showinfo("Copia tu contraseña", f"Contraseña fuerte generada:\n\n{strong_pass}\n\nAsegúrate de guardarla en un lugar seguro.")

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
            messagebox.showerror(
                "Contraseña Débil", 
                "La contraseña no cumple los requisitos mínimos de fortaleza.\n\n"
                "Debe contener:\n- Al menos 12 caracteres.\n- Mayúsculas y minúsculas.\n- Números y caracteres especiales."
            )

    # =========================================================================
    # VISTA 2: DESBLOQUEO / LOGIN
    # =========================================================================
    def show_login_view(self):
        self.clear_container()
        
        frame = ctk.CTkFrame(self.main_container, width=450, height=350)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        lbl_title = ctk.CTkLabel(frame, text="Aplicación Bloqueada", font=("Arial", 24, "bold"))
        lbl_title.pack(pady=(40, 10))
        
        lbl_sub = ctk.CTkLabel(frame, text="Ingrese su Master Password \n para descifrar el almacén", text_color="gray")
        lbl_sub.pack(pady=5)
        
        self.entry_login_pass = ctk.CTkEntry(frame, placeholder_text="Master Password", show="*", width=300)
        self.entry_login_pass.pack(pady=20)
        self.entry_login_pass.bind("<Return>", lambda event: self.handle_login())
        
        btn_unlock = ctk.CTkButton(frame, text="Desbloquear Almacén", font=("Arial", 14, "bold"), command=self.handle_login)
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
        
        lbl_welcome = ctk.CTkLabel(header_frame, text="🔑 Tus Credenciales Protegidas", font=("Arial", 22, "bold"))
        lbl_welcome.pack(side="left")
        
        btn_lock = ctk.CTkButton(header_frame, text="🔒 Bloquear App", width=100, fg_color="#9e2a2b", hover_color="#bd3a42", command=self.handle_lock)
        btn_lock.pack(side="right", padx=5)
        
        btn_add = ctk.CTkButton(header_frame, text="➕ Agregar Credencial", command=self.open_credential_modal)
        btn_add.pack(side="right", padx=5)
        
        # Contenedor Scrolleable para las tarjetas de contraseñas
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_container, fg_color="#1e1e1e", border_width=1, border_color="#2d2d2d")
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.refresh_credentials_list()

    def refresh_credentials_list(self):
        # Limpiar elementos anteriores dentro del scroll
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        credentials = self.util.pm.load_credentials()
        
        if not credentials:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="No hay credenciales almacenadas todavía.", font=("Arial", 14, "italic"), text_color="gray")
            lbl_empty.pack(pady=40)
            return

        for idx, (cred_id, data) in enumerate(credentials.items(), 1):
            # Tarjeta/Fila por cada credencial
            card = ctk.CTkFrame(self.scroll_frame, fg_color="#262626", height=60, border_width=1, border_color="#333333")
            card.pack(fill="x", pady=6, padx=10)
            card.pack_propagate(False)
            
            # Nombre del servicio
            lbl_name = ctk.CTkLabel(card, text=f"{idx}. {data['name']}", font=("Arial", 14, "bold"), anchor="w")
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
                btn_reveal.configure(text="👁️ Ocultar")
            else:
                entry_pass.configure(show="*")
                btn_reveal.configure(text="👁️ Ver")
                
        # MODIFICADO: Ahora copia estructura JSON clave:valor
        def copy_to_clipboard():
            import json
            formato_json = {
                "nombre": data['name'],
                "password": data['password']
            }
            json_string = json.dumps(formato_json, ensure_ascii=False)
            
            self.clipboard_clear()
            self.clipboard_append(json_string)
            messagebox.showinfo("Copiado", f"Datos de '{data['name']}' copiados en formato JSON al portapapeles.")

        btn_reveal = ctk.CTkButton(card, text="👁️ Ver", width=70, fg_color="#3a3a3a", hover_color="#4a4a4a", command=toggle_reveal)
        btn_reveal.pack(side="left", padx=5)
        
        btn_copy = ctk.CTkButton(card, text="📋 Copiar", width=70, fg_color="#2b5329", hover_color="#386b35", command=copy_to_clipboard)
        btn_copy.pack(side="left", padx=5)
        
        btn_edit = ctk.CTkButton(card, text="✏️", width=35, fg_color="#1f3a60", hover_color="#2a4d7c", command=lambda: self.open_credential_modal(cred_id, data))
        btn_edit.pack(side="left", padx=5)
        
        btn_del = ctk.CTkButton(card, text="🗑️", width=35, fg_color="#5e1914", hover_color="#7a221b", command=lambda: self.handle_delete(cred_id, data['name']))
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
        modal.geometry("450x380")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()
        
        lbl_title = ctk.CTkLabel(modal, text="Datos de la Credencial", font=("Arial", 18, "bold"))
        lbl_title.pack(pady=20)
        
        lbl_name = ctk.CTkLabel(modal, text="Nombre del Sitio / Servicio:", font=("Arial", 12))
        lbl_name.pack(anchor="w", padx=45)
        
        entry_name = ctk.CTkEntry(modal, width=360)
        entry_name.pack(pady=(5, 15))
        
        lbl_pass = ctk.CTkLabel(modal, text="Contraseña:", font=("Arial", 12))
        lbl_pass.pack(anchor="w", padx=45)
        
        entry_pass = ctk.CTkEntry(modal, width=360)
        entry_pass.pack(pady=5)
        
        if existing_data:
            entry_name.insert(0, existing_data['name'])
            entry_pass.insert(0, existing_data['password'])
            
        def generate_modal_password():
            strong_p = self.util.get_strong_password()
            entry_pass.delete(0, tk.END)
            entry_pass.insert(0, strong_p)
            
        btn_gen = ctk.CTkButton(modal, text="Generar Contraseña Fuerte", fg_color="#2b2b2b", hover_color="#3a3a3a", command=generate_modal_password)
        btn_gen.pack(pady=5)
        
        def save_modal_data():
            name = entry_name.get().strip()
            password = entry_pass.get()
            
            if not name or not password:
                messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=modal)
                return
                
            # MODIFICADO: Bloqueo estricto con los tips si la clave es débil
            if not self.util.is_password_strong(password):
                messagebox.showwarning(
                    "Contraseña Débil", 
                    "La contraseña ingresada es débil.\n\n"
                    "Una contraseña fuerte consiste de:\n"
                    "- Una longitud mayor o igual a 12.\n"
                    "- Uno o más números.\n"
                    "- Uno o más caracteres en minúscula.\n"
                    "- Uno o más caracteres en mayúscula.\n"
                    "- Uno o más caracteres especiales (ej: !<=>*()+,-)",
                    parent=modal
                )
                return  # Interrumpe el flujo y no permite guardar
            
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
            
        btn_save = ctk.CTkButton(modal, text="Guardar Cambios", font=("Arial", 14, "bold"), command=save_modal_data)
        btn_save.pack(pady=25)


if __name__ == "__main__":
    app = PasswordManagerGUI()
    app.mainloop()