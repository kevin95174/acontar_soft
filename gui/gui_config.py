import os
import tkinter as tk
import configparser
from tkinter import ttk, PhotoImage
from tkinter import filedialog
from tkinter import messagebox as mb
from PIL import Image, ImageTk
from db.query import mostrar_personal, mostrar_datos_bienes, delete_table, exportar_data
from db.query import datos_iniciales, actualizar_datos
from data.config_db import exportar_inv
from data.exp_excel import exportar_excel
from data.config_db import crear, importar

class Window_config(tk.Toplevel):
	def __init__(self, root=None):
		super().__init__(root)
		self.root = root
		self.title("Exportar / Importar datos")
		self.iconbitmap('./img/favicon.ico')
		self.config_path = 'config.ini'
		self.config = configparser.ConfigParser()
		self.img_label_path = None
		self.img_ficha_path = None
		self.iconoSubir = PhotoImage(file="img/subir.png")
		self.iconoBajar = PhotoImage(file="img/bajar.png")
		self.iconoBorrar = PhotoImage(file="img/borrar.png")
		self.iconoCSV = PhotoImage(file="img/csv.png")
		self.iconoSelec = PhotoImage(file="img/seleccion.png")
		self.iconoExcel = PhotoImage(file="img/excel.png")
		self.iconoLupa = PhotoImage(file="img/lupa.png")

		nbk = ttk.Notebook(self)
		self.tab1 = tk.Frame(nbk)
		self.tab2 = tk.Frame(nbk)
		self.tab3 = tk.Frame(nbk)
		nbk.add(self.tab1, text="Datos")
		nbk.add(self.tab2, text="Importar")
		nbk.add(self.tab3, text="Exportar")
		nbk.pack(fill="both", expand=True)

		self.tab1_()
		self.tab2_()
		self.tab3_()
		self.tree_view()
		self.load_config()
		self.cargar_imagen_guardada()
		self.mostrar_datos()

	def tab1_(self):
		self.Frame1 = tk.Frame(self.tab1, bg="#ffffff")
		self.Frame1.pack(fill='both')

		self.ent = tk.StringVar()
		self.per = tk.StringVar()
		self.fec = tk.StringVar()

		lblEnt = ttk.Label(self.Frame1, text="Entidad").grid(row=0, column=0, sticky="w")
		lblPer = ttk.Label(self.Frame1, text="Periodo").grid(row=1, column=0, sticky="w")
		lblFec = ttk.Label(self.Frame1, text="Fecha de Inventario").grid(row=2, column=0, sticky="w")
		self.img_label = tk.Label(self.Frame1)
		self.img_label.grid(row=4, column=0, columnspan=2)
		
		self.img_ficha = tk.Label(self.Frame1)
		self.img_ficha.grid(row=6, column=0, columnspan=2)

		etrEnt = ttk.Entry(self.Frame1, textvariable=self.ent).grid(row=0, column=1, sticky="ew", pady=5)
		cbxPer = ttk.Combobox(self.Frame1, values=[2020, 2021, 2022, 2023, 2024, 2025], textvariable=self.per, state="readonly").grid(row=1, column=1, sticky="ew", pady=5)
		etrFec = ttk.Entry(self.Frame1, textvariable=self.fec).grid(row=2, column=1, sticky="ew", pady=5)

		btnCon = ttk.Button(self.Frame1, text="Configurar", command=lambda:self.actualizar()).grid(row=3, column=1)
		btnLEt = ttk.Button(self.Frame1, text="Seleccionar logo Etiquetas", command=lambda:self.abrir_logo(1)).grid(row=5, column=0, sticky="ew")
		btnLFi = ttk.Button(self.Frame1, text="Seleccionar logo Ficha", command=lambda:self.abrir_logo(2)).grid(row=7, column=0, sticky="ew")

	def abrir_logo(self, valor):
		filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")])
		if filepath:
			if valor == 1:
				self.img_label_path = filepath
				image_widget = self.img_label
			elif valor == 2:
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
		
	def tab2_(self):
		# tab para la importacion de datos
		self.Frame1 = tk.Frame(self.tab2, bg="#ffffff")
		self.Frame1.pack(fill='both', expand=True)
		Frame1_1 = tk.Frame(self.Frame1)
		Frame1_1.pack(fill='both', side='top')
		
		self.nbase = tk.StringVar()
		self.narch = tk.StringVar()
		self.selecIm = tk.StringVar()
		lblImpor = ttk.Label(Frame1_1, text="Importar").grid(row=0, column=0, sticky="ew")
		cbxExinv = ttk.Combobox(Frame1_1, textvariable=self.selecIm, state="readonly",
								values=["personal", "bienes", "bienes afectados"]).grid(row=0, column=1)
		btnPunto = ttk.Button(Frame1_1, text="...", width=2.5, image=self.iconoLupa, compound='center', command=lambda:self.test()).grid(row=0, column=2)
		
		etrIminv = ttk.Entry(Frame1_1, textvariable = self.narch, width=40).grid(row=0, column=3)
		btnSeinv = ttk.Button(Frame1_1, text="Seleccionar archivo csv", image=self.iconoSelec, compound='left', command=lambda:self.select_file()).grid(row=0, column=4, sticky="w")
		btnExinv = ttk.Button(Frame1_1, text="Importar datos", image=self.iconoSubir, compound='left', command=lambda:self.importar_bd()).grid(row=0, column=5, sticky="w")
		btnBorra = ttk.Button(Frame1_1, text="Borrar datos", image=self.iconoBorrar, compound='left', command=lambda:self.borrar_datos()).grid(row=0, column=6)

	def tab3_(self):
		# Tab para la exportacion de datos
		Frame1 = tk.Frame(self.tab3, bg="#ffffff")
		Frame1.pack(fill='both')
		
		Frame1_1 = tk.Frame(Frame1)
		Frame1_1.pack(fill='both')

		self.selec = tk.StringVar()

		lblExinv = ttk.Label(Frame1_1, text="Exportar datos").grid(row=0, column=0)
		cbxExinv = ttk.Combobox(Frame1_1, textvariable=self.selec, state="readonly",
								values=["personal", "bienes", "sobrantes", "users"]).grid(row=0, column=1)
		btnExinv = ttk.Button(Frame1_1, text="Exportar CSV", image=self.iconoCSV, compound='left', command=lambda:self.exportar_csv()).grid(row=0, column=2, padx=5,sticky="ew")
		btnExinv = ttk.Button(Frame1_1, text="Exportar Excel", image=self.iconoExcel, compound='left', command=lambda:self.exportar_bd()).grid(row=0, column=3, padx=5,sticky="ew")

	def tree_view(self):
				# Treeview
		self.Frame1_2 = tk.Frame(self.Frame1)
		self.Frame1_2.pack(fill='both', side="bottom", expand=True)
		self.Frame1_2.rowconfigure(0, weight=1)
		self.Frame1_2.columnconfigure(0, weight=1)

		ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
		
		cab = []
		if self.selecIm.get() == "bienes":

			lista = ["CodInt", "ActaAnt", "Inv", "CodPat", "DenBien", "NroDocAdq", "FechAdq"
					, "ValAdq", "DepAcum", "ValNeto", "CtaCont", "DenCta", "Estado", "Marca", "Modelo", "Tipo", "Color"
					, "Serie", "Dimension", "Placa", "NroMotor", "NroChasis", "Matricula", "AñoFab"
					, "Nota", "Obs", "FechInv", "Otros", "Situacion"]
			
			for i in range(1, int(len(lista)+1)):
				cab.append(i)

			self.tree = ttk.Treeview(self.Frame1_2, height=25, columns=cab, show='headings')


			for i, val in enumerate(lista, start=1):
				self.tree.heading(i, text=val)
				self.tree.column(i, width=100, stretch=False)
		else:
			for i in range(1, 12):
				cab.append(i)
			
			self.tree = ttk.Treeview(self.Frame1_2, height=25, columns=cab, show='headings')
			lista = ["Acta", "dep", "prov", "dist", "local", "area", "oficina",
					"dni", "nombre", "apellidoPat", "apellidoMat"]

			for i, val in enumerate(lista, start=1):
				self.tree.heading(i, text=val)
				self.tree.column(i, width=100, stretch=False)
		

		self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
		scrollbarV = ttk.Scrollbar(self.Frame1_2, orient=tk.VERTICAL, command=self.tree.yview)
		scrollbarH = ttk.Scrollbar(self.Frame1_2, orient=tk.HORIZONTAL, command=self.tree.xview)
		self.tree.configure(yscroll=scrollbarV.set)
		self.tree.configure(xscroll=scrollbarH.set)

		scrollbarV.grid(column=1, row=0, sticky='ns')
		scrollbarH.grid(column=0, row=1, sticky='ew')
		
	def select_file(self):
		filetypes = (
			('text files', '*.csv'), 
			('all files', '*.*')
			)

		initialdir = self.last_folder if hasattr(self, 'last_folder') else '/'

		filename = filedialog.askopenfilename(
            title = 'Abrir un archivo',
            initialdir = initialdir,
            filetypes = filetypes
        )

		self.last_folder = os.path.dirname(filename)

		self.narch.set(filename)
		self.focus_set()
		return filename
		
	def importar_bd(self):
		j = self.selecIm.get()
		# print(j)
		try:
			if j == "personal":
				r = self.narch.get()
				importar(r, 1)
				self.Frame1_2.pack_forget()
				j = mostrar_personal()
				self.tree_view()
				self.show_data(j)
				
			else:
				r = self.narch.get()
				importar(r, 2)
				self.Frame1_2.pack_forget()
				j = mostrar_datos_bienes()
				self.tree_view()
				self.show_data(j)

			mb.showinfo(message="Se importo con exito", title="Acontar SAC")
			self.focus_set()
		except Exception as e:
			print(e)
			mb.showerror(message=f"""Error: {str(e)}""", title="Error")

	def exportar_csv(self):
		try:
			exportar_inv(self.selec.get())
			mb.showinfo(message='Exportado con exito', title='Acontar S.A.C.')
			self.focus_set()
		except Exception as e:
			mb.showerror(message=f'Ocurrio un error, Error {str(e)}', title='Error')
			self.focus_set()
			print(str(e))
	
	def exportar_bd(self):
		tabla = self.selec.get()
		lista = ['CodInt','ActaAnt', 'Inv', 'CodPat', 'DenBien', 'NroDocAdq', 'FechAdq', 'ValAdq', 'CtaCont', 'DenCta',        
				'Estado', 'Marca', 'Modelo', 'Tipo', 'Color', 'Serie', 'Dimension', 'Placa', 'NroMotor', 'NroChasis',     
				'Matricula', 'AñoFab', 'Nota', 'Obs', 'FechInv', 'Otros', 'Situacion', 'Inventariador', 'Equipo']
				
		try:
			data_expo = exportar_data(tabla)
			exportar_excel(tabla, data_expo[0], data_expo[1])
			self.focus_set()
		except Exception as e:
			print(e)
			mb.showerror(message="Error al exportar", title="Error")
			self.focus_set()

	def crear_bd(self):
		r = self.nbase.get()
		crear(r)
	
	def show_data(self, j):
		# j = mostrar_datos_bienes()
		
		for item in self.tree.get_children():
				self.tree.delete(item)
		for b in j:
			self.tree.insert('', tk.END, values=b)
	
	def borrar_datos(self):
		try:
			r = mb.askyesno(message="¿Esta seguro que desea eliminar todos los datos?", title="¡Atención!")
			if r == True:
				delete_table(self.selecIm.get())
				self.test()
				mb.showinfo(message="Los datos se han borrado", title='Acontar S.A.C.')
				self.focus_set()
		except:
			mb.showerror(message="Ocurrio un error al borrar")
			self.focus_set()

	def test(self):
		if self.selecIm.get() == "bienes":
			self.Frame1_2.pack_forget()
			self.tree_view()
			j = mostrar_datos_bienes()
			for item in self.tree.get_children():
					self.tree.delete(item)
			for b in j:
				self.tree.insert('', tk.END, values=b)
		else:
			self.Frame1_2.pack_forget()
			self.tree_view()
			j = mostrar_personal()
			for item in self.tree.get_children():
					self.tree.delete(item)
			for b in j:
				self.tree.insert('', tk.END, values=b)