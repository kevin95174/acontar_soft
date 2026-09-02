import tkinter as tk
from PIL import ImageTk
import qrcode
import socket
import random
import threading
import json
from db.query import datos_telefono

class Window_escanner(tk.Toplevel):
    
    def __init__(self, root=None):
        super().__init__(root)
        self.title("Conectar al telefono movil")
        self.iconbitmap('./img/favicon.ico')

        self.ip_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.ip_label.pack(pady=10)

        self.qr_label = tk.Label(self)
        self.qr_label.pack()

        self.generate_button = tk.Button(self, text="Generar QR", command=self.display_qr_code)
        self.generate_button.pack(pady=10)

        self.display_qr_code()

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
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def get_random_port(self):
        return random.randint(49152, 65535)

    def display_qr_code(self):
        ip_address = self.get_ip_address()
        port = self.get_random_port()
        if ip_address:
            img = self.generate_qr_code(ip_address, port)
            img = img.resize((200, 200))
            img = ImageTk.PhotoImage(img)
            self.qr_label.config(image=img)
            self.qr_label.image = img
            self.ip_label.config(text=f"Dirección IP: {ip_address}, Puerto: {port}")
            print(ip_address)
            self.start_server(ip_address, port)
        else:
            self.ip_label.config(text="No se pudo obtener la dirección IP.")

    def start_server(self, ip_address, port):
        server_thread = threading.Thread(target=self.run_server, args=(ip_address, port))
        server_thread.daemon = True
        server_thread.start()

    def run_server(self, ip_address, port):
        # Define la función run_server que toma la dirección IP y el puerto como parámetros
        HOST = ip_address
        PORT = port
        # Asigna la dirección IP y el puerto a las variables HOST y PORT respectivamente

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # Crea un socket utilizando la familia de direcciones AF_INET y el tipo de socket SOCK_STREAM (TCP)
            server_socket.bind((HOST, PORT))
            # Asocia el socket a la dirección IP y el puerto especificados
            server_socket.listen()
            # Pone el socket en modo de escucha para aceptar conexiones entrantes
            print(f"Servidor escuchando en {HOST}:{PORT}")
            # Imprime un mensaje indicando que el servidor está escuchando en la dirección IP y el puerto especificados

            while True:
                # Inicia un bucle infinito para aceptar y manejar conexiones entrantes
                client_socket, addr = server_socket.accept()
                # Acepta una conexión entrante, devolviendo un nuevo socket y la dirección del cliente
                print(f"Conexión desde {addr}")
                data = client_socket.recv(1024).decode('utf-8')

                
                print(data)
                response_data = datos_telefono(9876)
                respuesta = json.dumps(response_data)
                client_socket.send(respuesta.encode('utf-8'))
                client_socket.close()





