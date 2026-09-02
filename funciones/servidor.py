import socket
import json
from db.query import datos_codigo, datos_combinados, update_codigo, login_user_1, actualizar_registro, datos_telefono


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
            self.registrar(self.valor.get(), 9876)
            response_data = datos_telefono(9876)
            respuesta = json.dumps(response_data)
            client_socket.send(respuesta.encode('utf-8'))
            client_socket.close()

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('192.168.0.116', 62238))  # Escucha en la IP y el puerto especificados
    server_socket.listen()
    print("Servidor escuchando en el puerto 62238")

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

if __name__ == '__main__':
    iniciar_servidor()
