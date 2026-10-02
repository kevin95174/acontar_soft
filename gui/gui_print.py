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
		self._codigo_consultado = None
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
			self.etrCod = ttk.Entry(self.Frame1_1, textvariable=self.codi, width=20)
			self.etrCod.grid(column=1, row=0, padx=5, pady=1, sticky=EW)
			self.etrCod.bind("<Return>", self.enter_codigo)
			self.codi.trace_add("write", self._codigo_modificado)
			self.etrAct = ttk.Entry(self.Frame1_1, textvariable= self.acta).grid(column=1, row=1, padx=5, pady=1, sticky=EW)
			
			self.etrDen = ttk.Entry(self.Frame1_1, textvariable= self.deno).grid(column=1, row=2, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrCodI = ttk.Entry(self.Frame1_1, textvariable= self.codI).grid(column=1, row=3, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrCodP = ttk.Entry(self.Frame1_1, textvariable= self.codP).grid(column=1, row=4, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrInv = ttk.Entry(self.Frame1_1, textvariable= self.inve).grid(column=1, row=5, columnspan=3, padx=5, pady=1, sticky=EW)
			self.etrUbi = ttk.Entry(self.Frame1_1, textvariable= self.ubic).grid(column=1, row=6, columnspan=3, padx=5, pady=1, sticky=EW)

					# Buttons
			self.btnBus = ttk.Button(self.Frame1_1, text="Buscar", command=lambda:self.buscar()).grid(column=2, row=0, columnspan=2, padx=5, sticky="nsew")
			self.btnPre = ttk.Button(self.Frame1_1, text="Previsualizar", command=lambda:self.preview_pdf()).grid(column=2, row=1, columnspan=2, padx=5, sticky="nsew")
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
		codigo = self.codi.get().strip()
		acta = self.acta.get().strip()
		if not codigo or not acta:
			mb.showerror(title="Atención", message="Ingrese un código y un número de Acta.")
			return False
		inventario = self.inve.get().strip()
		if inventario and inventario.casefold() != "no inventariado":
			if not mb.askyesno(title="Bien ya inventariado", message=f"Este bien ya figura inventariado en:\n{inventario}\n\n¿Desea imprimir la etiqueta de todas formas?"):
				return False
		try:
			build_label(1, codigo, acta)
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo imprimir la etiqueta:\n{e}")
			return False
	def _codigo_modificado(self, *_args):
		# Un código distinto siempre debe consultarse antes de imprimir.
		if self.codi.get().strip() != self._codigo_consultado:
			self._codigo_consultado = None

	def enter_codigo(self, _event=None):
		codigo = self.codi.get().strip()
		if not codigo:
			return "break"

		if self._codigo_consultado == codigo:
			if self.print_():
				self.codi.set("")
				self._codigo_consultado = None
		else:
			if self.buscar():
				self.preview_pdf()
		return "break"

	def print_sobrante(self):
		if not all(value.get().strip() for value in (self.loca, self.area, self.ofic, self.deno)):
			mb.showerror(title="Atención", message="Busque un bien sobrante antes de imprimir.")
			return False
		try:
			build_label_sobrante(1, self.loca.get(), self.area.get(), self.ofic.get(), self.deno.get())
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo imprimir la etiqueta:\n{e}")
			return False

	def buscar(self):
		codigo = self.codi.get().strip()
		self._codigo_consultado = None
		self._limpiar_datos_inventario()
		if not codigo:
			mb.showerror(title="Atención", message="Ingrese un código.")
			return False
		try:
			r = mostrar_datos_print(codigo)
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudieron consultar los datos:\n{e}")
			return False
		if not r:
			mb.showerror(title="Error", message="No se encontraron datos para el código ingresado.")
			return False
		self.deno.set(r[0])
		self.codI.set(r[1])
		self.codP.set(r[2])
		self.inve.set(r[3])
		self.ubic.set(r[4])
		self._codigo_consultado = codigo
		return True

	def _limpiar_datos_inventario(self):
		for variable in (self.deno, self.codI, self.codP, self.inve, self.ubic):
			variable.set("")

	def buscar_sobrante(self):
		codigo = self.codi.get().strip()
		if not codigo:
			mb.showerror(title="Atención", message="Ingrese un código de bien sobrante.")
			return False
		try:
			r = mostrar_datos_sobrante(codigo)
			if not r:
				mb.showerror(title="Error", message="No se encontraron datos para el código ingresado.")
				return False
			self.loca.set(str(r[0]))
			self.area.set(str(r[1]))
			self.ofic.set(str(r[2]))
			self.deno.set(str(r[3]))
			pdf_path = build_label_sobrante(0, self.loca.get(), self.area.get(), self.ofic.get(), self.deno.get())
			self._mostrar_pdf(pdf_path)
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo generar la vista previa:\n{e}")
			return False

	def preview_pdf(self):
		codigo = self.codi.get().strip()
		acta = self.acta.get().strip()
		if not codigo or not acta:
			mb.showerror(title="Atención", message="Ingrese un código y un número de Acta.")
			return False
		try:
			pdf_path = build_label(0, codigo, acta)
			self._mostrar_pdf(pdf_path)
			return True
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo generar la vista previa:\n{e}")
			return False

	def _mostrar_pdf(self, pdf_path):
		for widget in self.Frame1_2.winfo_children():
			widget.destroy()
		with fitz.open(pdf_path) as pdf_document:
			if not pdf_document.page_count:
				raise ValueError("El PDF no contiene páginas.")
			pix = pdf_document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
		pil_image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
		image = ImageTk.PhotoImage(pil_image)
		label = tk.Label(self.Frame1_2, image=image, bg="#b6b6b6")
		label.image = image
		label.pack(fill="y", expand=True)
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
		try:
			self._mostrar_pdf("img/label_preview.pdf")
		except Exception as e:
			mb.showerror(title="Error", message=f"No se pudo cargar la etiqueta de ejemplo:\n{e}")
