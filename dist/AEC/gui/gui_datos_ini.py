import tkinter as tk
import os
import configparser
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import messagebox as mb
from tkinter import ttk, PhotoImage
from db.query import datos_iniciales, actualizar_datos

class Window_datos_ini(tk.Toplevel):
	def __init__(self, root=None):
		super().__init__(root)
		self.title("Configuración inicial")
		self.iconbitmap('./img/favicon.ico')
		self.config_path = 'config.ini'
		self.config = configparser.ConfigParser()
		self.img_label_path = None
		self.img_ficha_path = None
		self.iconoBorrar = PhotoImage("img/borrar.png")
		self.widgets()
		self.load_config()
		self.cargar_imagen_guardada()
		self.mostrar_datos()

	def widgets(self):
		Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
		Frame1.pack(fill='both')

		self.ent = tk.StringVar()
		self.per = tk.StringVar()
		self.fec = tk.StringVar()

		lblEnt = ttk.Label(Frame1, text="Entidad").grid(row=0, column=0, sticky="w")
		lblPer = ttk.Label(Frame1, text="Periodo").grid(row=1, column=0, sticky="w")
		lblFec = ttk.Label(Frame1, text="Fecha de Inventario").grid(row=2, column=0, sticky="w")
		self.img_label = tk.Label(Frame1)
		self.img_label.grid(row=4, column=0, columnspan=2)
		
		self.img_ficha = tk.Label(Frame1)
		self.img_ficha.grid(row=6, column=0, columnspan=2)

		etrEnt = ttk.Entry(Frame1, textvariable=self.ent).grid(row=0, column=1, columnspan=3, sticky="ew", pady=5)
		cbxPer = ttk.Combobox(Frame1, values=[2020, 2021, 2022, 2023, 2024, 2025], textvariable=self.per, state="readonly").grid(row=1, column=1, sticky="ew", pady=5)
		etrFec = ttk.Entry(Frame1, textvariable=self.fec).grid(row=2, column=1, sticky="ew", pady=5)

		btnCon = ttk.Button(Frame1, text="Configurar", command=lambda:self.actualizar()).grid(row=3, column=1)
		btnLEt = ttk.Button(Frame1, text="Seleccionar logo Etiquetas", command=lambda:self.abrir_logo(1)).grid(row=5, column=0, sticky="ew")
		btnLFi = ttk.Button(Frame1, text="Seleccionar logo Ficha", command=lambda:self.abrir_logo(2)).grid(row=7, column=0, sticky="ew")

	def abrir_logo(self, valor):
		filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")])
		if filepath:
			if valor == 1:
				self.img_label_path = filepath
				image_widget = self.img_label
			else:
				self.img_ficha_path = filepath
				image_widget = self.img_ficha

			self.save_config()
			image = Image.open(filepath)
			image.thumbnail((200, 200))
			photo = ImageTk.PhotoImage(image)
			image_widget.config(image=photo)
			image_widget.photo = photo
			self.focus_set()

	def load_config(self):
		if os.path.exists(self.config_path):
			self.config.read(self.config_path)
			if 'Settings' in self.config:
				self.img_label_path = self.config['Settings'].get('img_label_path', '')
				self.img_ficha_path = self.config['Settings'].get('img_ficha_path', '')

	def save_config(self):
		if not self.config.has_section('Settings'):
			self.config.add_section('Settings')
		self.config.set('Settings', 'img_label_path', self.img_label_path)
		self.config.set('Settings', 'img_ficha_path', self.img_ficha_path)
		self.config.set('Settings', 'entidad', self.ent.get())
		self.config.set('Settings', 'periodo', self.per.get())
		with open(self.config_path, 'w') as config_file:
			self.config.write(config_file)

	def cargar_imagen_guardada(self):
		if self.img_label_path and os.path.exists(self.img_label_path):
			image = Image.open(self.img_label_path)
			image.thumbnail((200, 200))
			self.photo = ImageTk.PhotoImage(image)
			self.img_label.config(image=self.photo)

		if self.img_ficha_path and os.path.exists(self.img_ficha_path):
			image = Image.open(self.img_ficha_path)
			image.thumbnail((200, 200))
			self.photo2 = ImageTk.PhotoImage(image)
			self.img_ficha.config(image=self.photo2)
		
	def mostrar_datos(self):
		r = datos_iniciales()
		self.ent.set(r[1])
		self.per.set(r[2])
		self.fec.set(r[3])
	
	def actualizar(self):
		lista = [self.ent.get(), self.per.get(), self.fec.get()]
		try:
			actualizar_datos(1, lista)
			mb.showinfo(title="Acontar S.A.C.", message="¡Actualizado con exito!")
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrio un error: "+ str(e))
		finally:
			self.focus_set()


