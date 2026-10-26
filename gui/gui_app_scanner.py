import json
import random
import socket
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import qrcode
from db.query import datos_telefono
from utils.helpers import resource_path


class Window_escanner(tk.Toplevel):
    """Ventana para vincular el teléfono móvil mediante código QR en red local."""

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Conexión de Escáner Móvil — AcontarSoft")
        self.geometry("460x550")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")
        if root:
            self.transient(root)

        self._server_socket = None
        self._current_endpoint = ""

        self._cargar_icono()
        self._centrar_ventana(460, 550)
        self._configurar_estilos()
        self._construir_interfaz()

        self.protocol("WM_DELETE_WINDOW", self._cerrar_ventana)
        self.display_qr_code()

    # -------------------------------------------------------------------------
    # CONFIGURACIÓN DE VENTANA Y ESTILOS
    # -------------------------------------------------------------------------
    def _cargar_icono(self):
        try:
            self.iconbitmap(resource_path("img/favicon.ico"))
        except Exception:
            pass

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.configure("Scanner.TLabelframe",
            background="#ffffff",
            relief="solid",
            borderwidth=1,
            bordercolor="#e2e8f0"
        )
        style.configure("Scanner.TLabelframe.Label",
            background="#ffffff",
            foreground="#334155",
            font=("Segoe UI", 9, "bold")
        )

    # -------------------------------------------------------------------------
    # CONSTRUCCIÓN DE INTERFAZ
    # -------------------------------------------------------------------------
    def _construir_interfaz(self):
        contenedor = tk.Frame(self, bg="#f8fafc")
        contenedor.pack(fill="both", expand=True, padx=16, pady=14)

        # Cabecera descriptiva
        header = tk.Frame(contenedor, bg="#ffffff", bd=1, relief="solid", padx=14, pady=10)
        header.pack(fill="x", pady=(0, 10))

        tk.Label(
            header,
            text="📱  Vincular Teléfono Móvil",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a",
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            header,
            text="Escanee el código QR desde la aplicación móvil en la misma red Wi-Fi",
            font=("Segoe UI", 8),
            bg="#ffffff",
            fg="#64748b",
            anchor="w"
        ).pack(fill="x", pady=(2, 0))

        # Card Central: Código QR y Datos de Red
        card = ttk.LabelFrame(
            contenedor,
            text=" 🔗 Código QR de Sincronización Local ",
            style="Scanner.TLabelframe",
            padding=14
        )
        card.pack(fill="both", expand=True)

        # Marco del QR
        qr_box = tk.Frame(card, bg="#f8fafc", bd=1, relief="solid", width=230, height=230)
        qr_box.pack_propagate(False)
        qr_box.pack(anchor="center", pady=(4, 12))

        self.qr_label = tk.Label(
            qr_box,
            text="Generando QR...",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 9)
        )
        self.qr_label.pack(fill="both", expand=True)

        # Chip con Dirección IP y Puerto
        info_box = tk.Frame(card, bg="#eff6ff", bd=1, relief="solid", padx=12, pady=8)
        info_box.pack(fill="x", pady=(0, 8))

        self.ip_label = tk.Label(
            info_box,
            text="Obteniendo dirección IP...",
            font=("Segoe UI", 10, "bold"),
            bg="#eff6ff",
            fg="#1d4ed8"
        )
        self.ip_label.pack(side="left", fill="x", expand=True)

        btn_copy = ttk.Button(info_box, text="📋 Copiar", width=9, command=self._copiar_endpoint)
        btn_copy.pack(side="right", padx=(6, 0))

        # Indicador de estado en vivo
        self.lbl_status = tk.Label(
            card,
            text="⏳ Iniciando servidor local...",
            font=("Segoe UI", 8, "italic"),
            bg="#ffffff",
            fg="#64748b"
        )
        self.lbl_status.pack(fill="x", pady=(2, 0))

        # Barra de botones inferior
        footer = tk.Frame(contenedor, bg="#f8fafc")
        footer.pack(fill="x", pady=(10, 0))

        self.generate_button = ttk.Button(
            footer,
            text="🔄 Generar Nuevo QR",
            command=self.display_qr_code
        )
        self.generate_button.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_cerrar = ttk.Button(footer, text="Cerrar", width=12, command=self._cerrar_ventana)
        btn_cerrar.pack(side="right")

    # -------------------------------------------------------------------------
    # LÓGICA DE RED Y SERVIDOR SOCKET
    # -------------------------------------------------------------------------
    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip_address = s.getsockname()[0]
        except Exception as e:
            print("No se pudo obtener la dirección IP:", e)
            ip_address = None
        finally:
            s.close()
        return ip_address

    def generate_qr_code(self, ip, port):
        data = f"{ip}:{port}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=3,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="white")
        return img

    def get_random_port(self):
        return random.randint(49152, 65535)

    def _copiar_endpoint(self):
        if self._current_endpoint:
            self.clipboard_clear()
            self.clipboard_append(self._current_endpoint)
            self.lbl_status.config(text=f"✅ Copiado al portapapeles: {self._current_endpoint}", fg="#16a34a")

    def display_qr_code(self):
        self._detener_servidor_previo()
        ip_address = self.get_ip_address()
        port = self.get_random_port()

        if ip_address:
            self._current_endpoint = f"{ip_address}:{port}"
            qr_img = self.generate_qr_code(ip_address, port)
            if hasattr(qr_img, "get_image"):
                pil_img = qr_img.get_image().resize((210, 210), Image.Resampling.NEAREST)
            else:
                pil_img = qr_img.resize((210, 210))
            tk_img = ImageTk.PhotoImage(pil_img)

            self.qr_label.config(image=tk_img, text="")
            self.qr_label.image = tk_img
            self.ip_label.config(text=f"🌐  IP: {ip_address}   |   Puerto: {port}")
            self.lbl_status.config(
                text=f"🟢 Escuchando conexiones en {ip_address}:{port}...",
                fg="#15803d"
            )
            print(ip_address)
            self.start_server(ip_address, port)
        else:
            self._current_endpoint = ""
            self.qr_label.config(image="", text="⚠️ Sin red local disponible")
            self.ip_label.config(text="No se pudo obtener la dirección IP", fg="#b91c1c")
            self.lbl_status.config(
                text="🔴 Verifique su conexión Wi-Fi o red de área local",
                fg="#b91c1c"
            )

    def _detener_servidor_previo(self):
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

    def _cerrar_ventana(self):
        self._detener_servidor_previo()
        self.destroy()

    def start_server(self, ip_address, port):
        server_thread = threading.Thread(target=self.run_server, args=(ip_address, port), daemon=True)
        server_thread.start()

    def run_server(self, ip_address, port):
        HOST = ip_address
        PORT = port

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                self._server_socket = server_socket
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((HOST, PORT))
                server_socket.listen()
                print(f"Servidor escuchando en {HOST}:{PORT}")

                while True:
                    client_socket, addr = server_socket.accept()
                    print(f"Conexión desde {addr}")
                    try:
                        if self.winfo_exists():
                            self.after(0, lambda a=addr: self.lbl_status.config(
                                text=f"📲 Dispositivo conectado desde {a[0]}",
                                fg="#2563eb"
                            ))
                    except Exception:
                        pass

                    data = client_socket.recv(1024).decode('utf-8')
                    print(data)
                    response_data = datos_telefono(9876)
                    respuesta = json.dumps(response_data)
                    client_socket.send(respuesta.encode('utf-8'))
                    client_socket.close()
        except OSError:
            # Socket cerrado al regenerar QR o cerrar la ventana
            pass
        except Exception as e:
            print(f"Error en servidor QR: {e}")
