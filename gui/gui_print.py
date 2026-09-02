import os
import configparser
import tkinter as tk
import fitz
from tkinter import EW, ttk
from tkinter import messagebox as mb
from PIL import Image, ImageTk
from db.query import mostrar_datos_print
from label.label_gen import build_label
from label.label_sobrante import build_label_sobrante
from db.query import datos_iniciales, actualizar_datos, mostrar_datos_sobrante

class Window_print(tk.Toplevel):
	def __init__(self, root=None, valor=None):
		super().__init__(root)
		self.root = root
		self.valor = valor
		self.title("Imprimir etiqueta")
		self.iconbitmap('./img/favicon.ico')
		self.config_path = 'config.ini'
		self.config = configparser.ConfigParser()
		self.img_label_path = None
		self.grab_set()
		self.focus_set()

		self.nbk = ttk.Notebook(self)
		self.tab1 = ttk.Frame(self.nbk)
		self.tab2 = tk.Frame(self.nbk)

		self.nbk.add(self.tab1, text="Inventario")
		self.nbk.add(self.tab2, text="Ajustes")
		self.nbk.pack(fill="both", expand=True)
		
		self.tab_1()
		self.tab_2()
		self.test()
		self.load_config()
		self.cargar_imagen_guardada()

	def tab_1(self):
		self.Frame1 = tk.Frame(self.tab1, bg="#ffffff")
		self.Frame1.pack(fill='both')
		self.Frame1.columnconfigure(0, weight=1)
		self.Frame1.columnconfigure(1, weight=1)
		self.Frame1.columnconfigure(2, weight=1)

		self.Frame1_1 = tk.Frame(self.Frame1, bg="#ffffff")
		self.Frame1_1.pack(fill='both', side="left")

		self.Frame1_2 = tk.Frame(self.Frame1)
		self.Frame1_2.pack(fill='both', side='right')

		self.acta = tk.StringVar()
		self.codi = tk.StringVar()
		self.deno = tk.StringVar()
		self.codI = tk.StringVar()
		self.inve = tk.StringVar()
		self.codP = tk.StringVar()
		self.ubic = tk.StringVar()
		self.enti = tk.StringVar()

		self.loca = tk.StringVar()
		self.area = tk.StringVar()
		self.ofic = tk.StringVar()

				# Labels
		if self.valor == 1:
			self.lblCod = ttk.Label(self.Frame1_1, text="Codigo Pat/Int").grid(column=0, row=0, padx=5, pady=1, sticky=EW)
			self.lblAct = ttk.Label(self.Frame1_1, text="Ficha").grid(column=0, row=1, padx=5, pady=1, sticky=EW)
			
			self.lblDen = ttk.Label(self.Frame1_1, text="Denominación").grid(column=0, row=2, padx=5, pady=1, sticky=EW)
			self.lblCodI = ttk.Label(self.Frame1_1, text="Codigo Interno").grid(column=0, row=3, padx=5, pady=1, sticky=EW)
			self.lblCodP = ttk.Label(self.Frame1_1, text="Codigo Patrimonial").grid(column=0, row=4, padx=5, pady=1, sticky=EW)
			self.lblInv = ttk.Label(self.Frame1_1, text="Ubicacion actual").grid(column=0, row=5, padx=5, pady=1, sticky=EW)
			self.lblUbi = ttk.Label(self.Frame1_1, text="Ubicación anterior").grid(column=0, row=6, padx=5, pady=1, sticky=EW)
					
					# Entrys
			self.etrCod = ttk.Entry(self.Frame1_1, textvariable= self.codi, width=20).grid(column=1, row=0, padx=5, pady=1, sticky=EW)
			self.etrAct = ttk.Entry(self.Frame1_1, textvariable= self.acta).grid(column=1, row=1, padx=5, pady=1, sticky=EW)
			
			self.etrDen = ttk.Entry(self.Frame1_1, textvariable= self.deno).grid(column=1, row=2, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrCodI = ttk.Entry(self.Frame1_1, textvariable= self.codI).grid(column=1, row=3, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrCodP = ttk.Entry(self.Frame1_1, textvariable= self.codP).grid(column=1, row=4, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrInv = ttk.Entry(self.Frame1_1, textvariable= self.inve).grid(column=1, row=5, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrUbi = ttk.Entry(self.Frame1_1, textvariable= self.ubic).grid(column=1, row=6, columnspan=3, padx=5, pady=1, sticky=EW)

					# Buttons
			self.btnBus = ttk.Button(self.Frame1_1, text="Buscar", command=lambda:self.buscar()).grid(column=2, row=0, columnspan=2, padx=5, sticky="nsew")
			self.btnPre = ttk.Button(self.Frame1_1, text="Previzualizar", command=lambda:self.preview_pdf()).grid(column=2, row=1, columnspan=2, padx=5, sticky="nsew")
			self.btnImp = ttk.Button(self.Frame1_1, text="Imprimir", command=lambda:self.print_()).grid(column=1, row=10, columnspan=3, padx=5, sticky="nsew")			
			
		elif self.valor == 2:
			self.lblIte = ttk.Label(self.Frame1_1, text="Item").grid(column=0, row=0, padx=5, pady=1, sticky=EW)
			self.lblLoc = ttk.Label(self.Frame1_1, text="Local").grid(column=0, row=1, padx=5, pady=1, sticky=EW)
			self.lblAre = ttk.Label(self.Frame1_1, text="Área").grid(column=0, row=2, padx=5, pady=1, sticky=EW)
			self.lblOfi = ttk.Label(self.Frame1_1, text="Oficina").grid(column=0, row=3, padx=5, pady=1, sticky=EW)
			self.lblDen = ttk.Label(self.Frame1_1, text="Denominación").grid(column=0, row=4, padx=5, pady=1, sticky=EW)
					
					# Entrys
			self.etrIte = ttk.Entry(self.Frame1_1, textvariable= self.codi, width=20).grid(column=1, row=0, padx=5, pady=1, sticky=EW)
			self.etrLoc = ttk.Entry(self.Frame1_1, textvariable= self.loca).grid(column=1, row=1, padx=5, pady=1, sticky=EW)			
			self.etrAre = ttk.Entry(self.Frame1_1, textvariable= self.area).grid(column=1, row=2, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrOfi = ttk.Entry(self.Frame1_1, textvariable= self.ofic).grid(column=1, row=3, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrDen = ttk.Entry(self.Frame1_1, textvariable= self.deno).grid(column=1, row=4, columnspan=3, padx=5, pady=1, sticky=EW)

			self.btnBus = ttk.Button(self.Frame1_1, text="Buscar", command=lambda:self.buscar_sobrante()).grid(column=2, row=0, columnspan=2, padx=5, sticky="nsew")
			self.btnPre = ttk.Button(self.Frame1_1, text="Imprimir", command=lambda:self.print_sobrante()).grid(column=2, row=1, columnspan=2, padx=5, sticky="nsew")

	def tab_2(self):
		# self.Frame1_tab_2 = tk.Frame(self.tab2, bg="blue")
		# self.Frame1_tab_2.pack(fill="both")

		# self.Frame1_tab_2.columnconfigure(0, weight=1)
		# self.Frame1_tab_2.rowconfigure(0, weight=1)
		self.ent = tk.StringVar()
		self.per = tk.StringVar()

		self.Frame1_1_tab_2 = tk.Frame(self.tab2, bg="#ffffff")
		self.Frame1_1_tab_2.pack(fill='both', side='left')

		lblEnt = ttk.Label(self.Frame1_1_tab_2, text="Entidad").grid(row=0, column=0)
		etrEnt = ttk.Entry(self.Frame1_1_tab_2, textvariable=self.ent).grid(row=0, column=1, sticky="ew", pady=5, padx=5)

		lblPer = ttk.Label(self.Frame1_1_tab_2, text="Periodo").grid(row=1,  column=0)
		cbxPer = ttk.Combobox(self.Frame1_1_tab_2, values=[2020, 2021, 2022, 2023, 2024, 2025], textvariable=self.per, state="readonly").grid(row=1, column=1, sticky="ew", pady=5, padx=5)

		self.Frame1_2_tab_2 = tk.Frame(self.tab2, bg="red")
		self.Frame1_2_tab_2.pack(fill='both', side='right')

		self.img_label = tk.Label(self.Frame1_2_tab_2)
		self.img_label.grid(row=0, column=0)

	def load_config(self):
		if os.path.exists(self.config_path):
			self.config.read(self.config_path)
			if 'Settings' in self.config:
				self.img_label_path = self.config['Settings'].get('img_label_path', '')

	def cargar_imagen_guardada(self):
		if self.img_label_path and os.path.exists(self.img_label_path):
			image = Image.open(self.img_label_path)
			image.thumbnail((200, 200))
			self.photo = ImageTk.PhotoImage(image)
			self.img_label.config(image=self.photo)

	def print_(self):
		codigo = self.codi.get()
		acta = self.acta.get()
		if codigo == "":
			mb.showerror(message="Ingrese un código", title="¡Atención!")
		elif acta == "":
			mb.showerror(message="Ingrese un número de Acta", title="¡Atención!")
		else:
			build_label(1, codigo, acta)

	def print_sobrante(self):

		try:
			build_label_sobrante(1, self.loca.get(), self.area.get(), self.ofic.get(), self.deno.get())
		except Exception as e:
			print(e)
			mb.showerror(message="Ingrese un número de Acta", title="¡Atención!")

	def buscar(self):
		r = mostrar_datos_print(self.codi.get())
		# print(r)
		try:
			self.deno.set(r[0])
			self.codI.set(r[1])
			self.codP.set(r[2])
			self.inve.set(r[3])
			self.ubic.set(r[4])
		except:
			mb.showerror(message="Error", title="Error")

	def buscar_sobrante(self):
		print(self.codi.get())
		r = mostrar_datos_sobrante(self.codi.get())
		try:
			self.loca.set(str(r[0]))
			self.area.set(str(r[1]))
			self.ofic.set(str(r[2]))
			self.deno.set(str(r[3]))

			for widget in self.Frame1_2.winfo_children():
				widget.destroy()
			
			r = build_label_sobrante(0, self.loca.get(), self.area.get(), self.ofic.get(), self.deno.get())
			pdf_document = fitz.open(r)	
			page = pdf_document[0]
			pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
			width, height = pix.width, pix.height
			img_bytes = pix.samples
			pil_image = Image.frombytes('RGB', (width, height), img_bytes)
			image = ImageTk.PhotoImage(pil_image)
			label = tk.Label(self.Frame1_2)
			label.pack(fill="y", expand=True)
			label.config(image=image, bg="#b6b6b6")
			label.image = image
		except Exception as e:
			print(e)
			mb.showerror(message="Error", title="Error")
		
	def preview_pdf(self):
		for widget in self.Frame1_2.winfo_children():
			widget.destroy()
		
		r = build_label(0, self.codi.get(), self.acta.get())
		pdf_document = fitz.open(r)	
		page = pdf_document[0]
		pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
		width, height = pix.width, pix.height

		img_bytes = pix.samples

		pil_image = Image.frombytes('RGB', (width, height), img_bytes)

		image = ImageTk.PhotoImage(pil_image)

		label = tk.Label(self.Frame1_2)
		label.pack(fill="y", expand=True)
		label.config(image=image, bg="#b6b6b6")
		label.image = image

	def mostrar_datos(self):
		r = datos_iniciales()
		self.ent.set(r[1])
		self.per.set(r[2])

	def actualizar(self):
		lista = [self.ent.get(), self.per.get(), self.fec.get()]
		try:
			actualizar_datos(1, lista)
			mb.showinfo(title="Acontar S.A.C.", message="¡Actualizado con exito!")
		except Exception as e:
			mb.showerror(title="Error", message=f"Ocurrio un error: "+ str(e))
		finally:
			self.focus_set()

	def test(self):
		pdf_document = fitz.open("img/label_preview.pdf")
			
		page = pdf_document[0]
		pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
		width, height = pix.width, pix.height

		img_bytes = pix.samples

		pil_image = Image.frombytes('RGB', (width, height), img_bytes)

		image = ImageTk.PhotoImage(pil_image)

		label = tk.Label(self.Frame1_2)
		label.pack(fill="y", expand=True)
		label.config(image=image, bg="#b6b6b6")
		label.image = image
		