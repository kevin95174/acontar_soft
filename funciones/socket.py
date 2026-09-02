import tkinter as tk
import socket
import qrcode
import random
import threading
import json
from PIL import ImageTk
from db.query import datos_codigo, datos_combinados, update_codigo, login_user_1, actualizar_registro


class Window_server(tk.Toplevel):
    def __init__(self, frame_app=None, root=None):
        super().__init__(root)
        self.root = root
        self.frame_app = frame_app
        self.title("Escanea el código")
        self.iconbitmap('./img/favicon.ico')

        self.ip_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.ip_label.pack(pady=10)

        self.qr_label = tk.Label(self)
        self.qr_label.pack()

        self.generate_button = tk.Button(self, text="Generar QR", command=self.display_qr_code)
        self.generate_button.pack(pady=10)

        self.display_qr_code()

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

    def start_server(self, ip_address, port):
        server_thread = threading.Thread(target=self.run_server, args=(ip_address, port))
        server_thread.daemon = True
        server_thread.start()

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

    def get_random_port(self):
        return random.randint(49152, 65535)

    def run_server(self, ip_address, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ip_address, port))  # Escucha en la IP y el puerto especificados
        server_socket.listen()
        print("Servidor escuchando")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Conexión desde {addr}")
            
            # Recibir datos del cliente (si es necesario)
            data = client_socket.recv(1024).decode('utf-8')
            print(f"Recibido: {data}")
            
            try:
                request_data = json.loads(data)
                response_data = {}

                # Verificar el tipo de mensaje y preparar la respuesta adecuada
                if request_data.get("Type") == "Login":
                    # Lógica de autenticación
                    loguear = login_user_1(request_data.get("Usuario"), request_data.get("Contraseña"))
                    if loguear.get("Message") == 1:
                        response_data = loguear
                        print(response_data)
                        print(loguear)
                    else:
                        response_data = {"Message": 2}
                        print("esto")
                elif request_data.get("Type") == "scanned_code":
                    # Lógica para manejar el código escaneado
                    codigo = request_data.get("data")
                    response_data = datos_codigo(codigo)

                elif request_data.get("Type") == "Inventario":
                    codigo = request_data.get("CodInt")
                    data = [request_data.get("Inv"), request_data.get("FechaInv"), request_data.get("User"), request_data.get("Equipo")]
                    actualizar_registro(int(codigo), data)
                    response_data = "Registrado"

                elif request_data.get("Type") == "Update":
                    data = [request_data.get("Marca"), request_data.get("Modelo"), request_data.get("Serie"), request_data.get("Color"), request_data.get("Tipo"),
                            request_data.get("Dimension"), request_data.get("Estado"), request_data.get("Situacion")]
                    update_codigo(request_data.get("CodInt"), data)
                    # Lógica para manejar la actualización de datos
                    response_data = {"Message": "Data updated successfully"}
                
                elif request_data.get("Type") == "Ficha":
                    response_data = datos_combinados(request_data.get("NumFicha"))
                else:
                    # Respuesta para tipo de mensaje desconocido
                    response_data = {"Type": "error", "Message": "Unknown request type"}

                # Enviar la respuesta al cliente
                respuesta = json.dumps(response_data)
                client_socket.send(respuesta.encode('utf-8'))
            
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                response_data = {"Type": "error", "Message": "Invalid JSON format"}
                client_socket.send(json.dumps(response_data).encode('utf-8'))
            
            client_socket.close()