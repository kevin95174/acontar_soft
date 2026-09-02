import tkinter as tk
from tkinter import ttk
from lector_barras.read_barcode import select_camera, start_detection

class Window_bar(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("AEC Leer códigos")
        self.iconbitmap("./img/favicon.ico")

        self.camara = tk.StringVar()

        self.lblCam = ttk.Label(self, text="Selecciona una cámara:")
        self.lblCam.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.cbxCam = ttk.Combobox(self, textvariable=self.camara, state="readonly")
        self.cbxCam.grid(row=0, column=1, padx=5, pady=5)

        self.btnCam = ttk.Button(self, text="Actualizar Cámaras", command=lambda:self.actualizar_camara())
        self.btnCam.grid(row=0, column=2, padx=5, pady=5)

        self.btnIni = ttk.Button(self, text="Iniciar Detección", command=lambda:start_detection(self.camara.get()))
        self.btnIni.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def actualizar_camara(self):
        num_cameras = select_camera()

        cameras = list(range(num_cameras))
        self.cbxCam['values'] = cameras
        self.cbxCam.current(0)

    def codigo_leido(self):
        pass
