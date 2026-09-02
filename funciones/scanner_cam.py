import tkinter as tk
import cv2
import pygame
import os
from pyzbar.pyzbar import decode
from PIL import Image, ImageTk
from tkinter import ttk
from funciones.data_exif import insertar_metadatos
from db.query import buscar_bien

class Window_scanner(tk.Toplevel):
    def __init__(self, frame_app=None, root= None):
        super().__init__(root)
        self.root = root
        self.frame_app = frame_app
        self.title("Escanear el Código")
        self.iconbitmap('./img/favicon.ico')

        frame_u = tk.Frame(self)
        frame_u.pack()

        frame_1 = tk.Frame(frame_u)
        frame_1.pack(side='top')

        frame_2 = tk.Frame(frame_u)
        frame_2.pack(side='bottom', fill='x')

        self.nun_cam = tk.StringVar()

        lblCam = ttk.Label(frame_2, text="Seleccione una camara")
        lblCam.grid(column=0, row=0, padx=5, pady=1)
        self.cbxCam = ttk.Combobox(frame_2, textvariable=self.nun_cam)
        self.cbxCam.grid(column=1, row=0, padx=5, pady=1)
        btnSel = ttk.Button(frame_2, text="Seleccionar", command=lambda:self.init_camera())
        btnSel.grid(column=2, row=0, padx=5, pady=1)

        self.seleccionar_camara()

        # Crear un widget Label para mostrar el fotograma de OpenCV
        self.opencv_label = tk.Label(frame_1)
        self.opencv_label.pack()
        self.is_running = False
        self.bind("<KeyPress>", self.on_enter_press)

    def seleccionar_camara(self):
        
        cant_camaras = 0
        while True:
            camara = cv2.VideoCapture(cant_camaras)
            if not camara.isOpened():
                break
            cant_camaras += 1
            camara.release()
        camaras = list(range(cant_camaras))
        self.cbxCam['values'] = camaras

    def init_camera(self):
        # Obtener el número de cámara seleccionado
        selected_camera = int(self.nun_cam.get())
        # Liberar la cámara actual si existe
        if self.is_running:
            self.camera.release()
            cv2.destroyAllWindows()
        
        # Inicializar la nueva cámara
        self.camera = cv2.VideoCapture(selected_camera)
        if not self.is_running:
            self.is_running = True
            # Iniciar la función para mostrar el fotograma de la cámara
            self.show_frame()

    # Función para mostrar el fotograma de la cámara y detectar códigos de barras
    def show_frame(self):
        if self.is_running:
            # ret: Es un valor booleano que indica si la captura fue exitosa o no. 
            # Si la captura fue exitosa, ret será True; de lo contrario, será False.
            # frame: Es un objeto que representa el cuadro de video capturado. 
            # Este objeto puede ser una matriz de píxeles (por ejemplo, si estás usando OpenCV, 
            # frame sería un objeto de tipo numpy.ndarray que contiene la imagen capturada).
            
            ret, frame = self.camera.read()
            if ret:
                frame, barcode_info = self.process_frame(frame)
                if barcode_info:
                    self.frame_app.id.set(barcode_info)
                    self.frame_app.registrar(self.frame_app.valor.get(), barcode_info)
                    self.focus_set()
                    self.is_running = False
                
                cv2.rectangle(frame, (100, 100), (540, 380), (255, 0, 0), 2)

                # Convierte el fotograma de OpenCV a una imagen compatible con Tkinter
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                
                # Actualiza el widget Label con el nuevo fotograma
                self.opencv_label.imgtk = imgtk
                self.opencv_label.configure(image=imgtk)
            
                # Programar la siguiente actualización del fotograma
                self.after(10, self.show_frame)

    # Reanudar la lectura al presionar la tecla Enter
    def on_enter_press(self, event):
        if not self.is_running and event.keysym == "Return":
            self.is_running = True
            self.show_frame()

    def process_frame(self, frame):		
        # Procesar el fotograma y detectar códigos de barras
        barcodes = decode(frame)
        # Inicializar barcode_info
        barcode_info = None
        # Verificar si se han detectado códigos de barras
        if not barcodes:
            # Si no se detectan códigos de barras, mostrar un mensaje en el fotograma
            cv2.putText(frame, "Escanear codigo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            # Si se detectan códigos de barras, iterar sobre cada uno
            for barcode in barcodes:
                # Obtener las coordenadas y dimensiones del rectángulo del código de barras
                x, y, w, h = barcode.rect
                # Obtener la información del código de barras (contenido)
                barcode_info = barcode.data.decode('utf-8')
                # Dibujar un rectángulo alrededor del código de barras en el fotograma
                cv2.rectangle(frame, (x, y),(x+w, y+h), (0, 255, 0), 2)
                # Configurar la fuente para el texto
                font = cv2.FONT_HERSHEY_DUPLEX
                # Escribir el contenido del código de barras sobre el fotograma
                cv2.putText(frame, barcode_info, (x + 6, y - 6), font, 0.5, (255, 0, 255), 1)				
                # Reproducir un sonido al leer un código de barras
                play_sound("./sound/beep.mp3")
                img_name = self.descripcion(frame, barcode_info)
                insertar_metadatos(barcode_info, img_name)
        return frame, barcode_info

    def descripcion(self, frame, barcode_info):
        data = buscar_bien(barcode_info, 1)
        if data:
            # Definir la leyenda en múltiples líneas
            description = f"Descripcion: {data[0][0]}"
            location = f"Lugar: {data[0][12]}"
            ID = f"ID: {data[0][15]}"
        else:
            # Definir la leyenda en múltiples líneas
            description = f"Descripción: ---"
            location = f"Lugar: ---"
            ID = f"ID: ---"
        
        # Coordenadas de inicio para dibujar las líneas de texto
        x, y = 10, frame.shape[0] - 10
        # Espacio vertical entre líneas de texto
        line_spacing = 20
        # Dibujar cada línea de texto por separado
        cv2.putText(frame, description, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, location, (x, y - line_spacing), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, ID, (x, y - 2 * line_spacing), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Guardar la imagen del fotograma con el código de barras
        save_path = "./photos/"
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        image_name = os.path.join(save_path, f"code_{barcode_info}.jpg")
        cv2.imwrite(image_name, frame)
        
        # Mostrar un mensaje indicando que se ha leído correctamente un código de barras
        cv2.putText(frame, "Código leído correctamente", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return image_name

# def iniciar_con_camara_seleccionada():

#     # Obtener el índice de la cámara seleccionada
#     selected_camera = int(self.cbxCam.get())
#     # Iniciar la detección con la cámara seleccionada
#     start_detection(selected_camera)

def play_sound(sound_file):
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(20)