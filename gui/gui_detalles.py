import tkinter as tk
from datetime import datetime
from tkinter import ttk
from db.query import buscar_bien_d, actualizar_detalles, actualizar_registro, cambio_detalles, insertar_tabla2
from tkinter import messagebox as mb


class Window_detalles(tk.Toplevel):
	def __init__(self, root=None, user=None, team=None, codigo=None):
		super().__init__(root)

		self.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.resizable(0,0)
		self.root = root
		self.user = user
		self.team = team
		self.codigo = codigo
		self.accion = None
		self.title("Detalles")
		self.iconbitmap('./img/favicon.ico')
		style = ttk.Style()
		style.configure('Custom.TFrame', background='#ffffff')
		style.configure('Custom.TEntry')
		self.frameU = ttk.Frame(self, style='Custom.TFrame')
		self.frameU.pack(fill='both', expand=True, padx=10, pady=10)
		# self.grab_set()
		self.focus_set()
		self.variables()
		self.widgets()
		self.buscar_cod()
	
	def on_closing(self):
		pass

	def variables(self):
		self.codi = tk.StringVar()
		self.deno = tk.StringVar()
		self.inve = tk.StringVar()
		self.codp = tk.StringVar()
		self.acta = tk.StringVar()
		self.marc = tk.StringVar()
		self.seri = tk.StringVar()
		self.fech = tk.StringVar()
		self.dadq = tk.StringVar()
		self.mode = tk.StringVar()
		self.colo = tk.StringVar()			
		self.aact = tk.StringVar()
		self.esta = tk.StringVar()
		self.dime = tk.StringVar()
		self.obse = tk.StringVar()
		
		self.otro = tk.StringVar()
		self.situ = tk.StringVar()
		self.tipo = tk.StringVar()
		self.valo = tk.StringVar()
		self.ctac = tk.StringVar()
		self.cint = tk.StringVar()

	def widgets(self):


				# Frame top
		lblCod = ttk.Label(self.frameU, text="Código").grid(column=0, row=0, padx=3, pady=3, sticky="ew")
		etrCod = ttk.Entry(self.frameU, textvariable= self.codi, state='readonly').grid(column=1, row=0, padx=3, pady=3, sticky="ew")
		etrDen = ttk.Entry(self.frameU, textvariable= self.deno).grid(column=2, row=0, columnspan=4, padx=3, pady=3, sticky="ew")

				# Labels
		lblInve = ttk.Label(self.frameU, text="Inventario").grid(column=0, row=1, padx=3, pady=3, sticky="ew")
		lblActA = ttk.Label(self.frameU, text="Inv. Anterior").grid(column=0, row=2, padx=3, pady=3, sticky="ew")
		lblCtaC = ttk.Label(self.frameU, text='Cta. Cont.').grid(column=0, row=3, padx=3, pady=3, sticky='ew')
		lblCodP = ttk.Label(self.frameU, text="Cód. Pat.").grid(column=0, row=4, padx=3, pady=3, sticky="ew")
		lblCodI = ttk.Label(self.frameU, text="Cód. Int.").grid(column=0, row=5, padx=3, pady=3, sticky="ew")
		lblFecA = ttk.Label(self.frameU, text="Fecha Adqui.").grid(column=0, row=6, padx=3, pady=3, sticky="ew")
		lblDocA = ttk.Label(self.frameU, text="Doc. Adqui.").grid(column=0, row=7, padx=3, pady=3, sticky="ew")


				# Entrys
		etrInve = ttk.Entry(self.frameU, textvariable = self.inve, state='readonly').grid(column=1, row=1, columnspan=3, padx=3, pady=3, sticky="ew")
		etrActA = ttk.Entry(self.frameU, textvariable = self.acta, state='readonly').grid(column=1, row=2, columnspan=3, padx=3, pady=3, sticky="ew")
		etrCtaC = ttk.Entry(self.frameU, textvariable = self.ctac, state='readonly').grid(column=1, row=3, columnspan=3, padx=3, pady=3, sticky='ew')		
		etrCodP = ttk.Entry(self.frameU, textvariable = self.codp, state='readonly').grid(column=1, row=4, padx=3, pady=3, sticky="ew")
		etrCodI = ttk.Entry(self.frameU, textvariable = self.cint, state='readonly').grid(column=1, row=5, padx=3, pady=3, sticky="ew")
		etrFecA = ttk.Entry(self.frameU, textvariable = self.fech, state='readonly').grid(column=1, row=6, padx=3, pady=3, sticky="ew")
		etrDocA = ttk.Entry(self.frameU, textvariable = self.dadq, state='readonly').grid(column=1, row=7, padx=3, pady=3, sticky="ew")

		
		lblValo = ttk.Label(self.frameU, text='Valor Adqui.').grid(column=2, row=4, padx=3, pady=3, sticky='ew')
		lblOtro = ttk.Label(self.frameU, text="Otros").grid(column=2, row=5, padx=3, pady=3, sticky="ew")
		lblSitu = ttk.Label(self.frameU, text="Situacion").grid(column=2, row=6, padx=3, pady=3, sticky="ew")
		lblObse = ttk.Label(self.frameU, text="Obs").grid(column=2, row=7, padx=3, pady=3, sticky="ew")
				# Entrys

		etrValo = ttk.Entry(self.frameU, textvariable = self.valo, state='readonly', justify='right').grid(column=3, row=4, padx=3, pady=3, sticky='ew')
		etrOtro = ttk.Entry(self.frameU, textvariable= self.otro).grid(column=3, row=5, padx=3, pady=3, sticky="ew")
		etrSitu = ttk.Entry(self.frameU, textvariable= self.situ).grid(column=3, row=6, padx=3, pady=3, sticky="ew")
		etrObse = ttk.Entry(self.frameU, textvariable= self.obse).grid(column=3, row=7, padx=3, pady=3, sticky="ew")

		lblEsta = ttk.Label(self.frameU, text="Estado").grid(column=4, row=1, padx=3, pady=3, sticky="ew")
		lblMarc = ttk.Label(self.frameU, text="Marca").grid(column=4, row=2, padx=3, pady=3, sticky="ew")
		lblMode = ttk.Label(self.frameU, text="Modelo").grid(column=4, row=3, padx=3, pady=3, sticky="ew")
		lblSeri = ttk.Label(self.frameU, text="Serie").grid(column=4, row=4, padx=3, pady=3, sticky="ew")
		lblTipo = ttk.Label(self.frameU, text="Tipo").grid(column=4, row=5, padx=3, pady=3, sticky="ew")
		lblColo = ttk.Label(self.frameU, text="Color").grid(column=4, row=6, padx=3, pady=3, sticky="ew")
		lblDime = ttk.Label(self.frameU, text="Dimensión").grid(column=4, row=7, padx=3, pady=3, sticky="ew")

		etrEsta = tk.Entry(self.frameU, textvariable= self.esta, highlightbackground= "#e30613", highlightthickness=1)
		etrEsta.grid(column=5, row=1, padx=3, pady=3, sticky="ew")
		etrMarc = tk.Entry(self.frameU, textvariable= self.marc, highlightbackground= "#e30613", highlightthickness=1)
		etrMarc.grid(column=5, row=2, padx=3, pady=3, sticky="ew")
		etrMode = tk.Entry(self.frameU, textvariable= self.mode, highlightbackground= "#e30613", highlightthickness=1)
		etrMode.grid(column=5, row=3,padx=3, pady=3, sticky="ew")		
		etrSeri = tk.Entry(self.frameU, textvariable= self.seri, highlightbackground= "#e30613", highlightthickness=1)
		etrSeri.grid(column=5, row=4, padx=3, pady=3, sticky="ew")
		etrTipo = tk.Entry(self.frameU, textvariable= self.tipo, highlightbackground= "#e30613", highlightthickness=1)
		etrTipo.grid(column=5, row=5, padx=3, pady=3, sticky="ew")
		etrColo = tk.Entry(self.frameU, textvariable= self.colo, highlightbackground= "#e30613", highlightthickness=1)
		etrColo.grid(column=5, row=6, padx=3, pady=3, sticky="ew")
		etrDime = tk.Entry(self.frameU, textvariable= self.dime, highlightbackground= "#e30613", highlightthickness=1)
		etrDime.grid(column=5, row=7, padx=3, pady=3, sticky="ew")

		
		btnDeta = ttk.Button(self.frameU, text="Aceptar", command=lambda:self.actualizar_det()).grid(row=8, column=5, padx=3, pady=3, sticky="ew")
		btnCanc = ttk.Button(self.frameU, text="Cancelar", command=lambda:self.cancelar_codigo()).grid(row=9, column=5, padx=3, pady=3, sticky="ew")
		
		lblNota = ttk.Label(self.frameU, text="Nota").grid(row=8, column=0, padx=3, pady=3, sticky="ew")

		self.txtNota = tk.Text(self.frameU, height=3)
		self.txtNota.configure(font=('Arial', 9), bg='white', relief='solid')
		self.txtNota.grid(row=8, column=1, columnspan=4, rowspan=2, padx=3, pady=3, sticky='nsew')

	def cancelar_codigo(self):
		self.accion = 1
		self.destroy()
	
	def buscar_cod(self, *args):
		r = buscar_bien_d(1, self.codigo)
		self.codi.set(self.codigo)
		try:
			datos = ['deno', 'inve', 'acta', 'marc', 'seri', 'mode', 'fech', 'dadq', 'colo', 'esta', 
					'dime', 'obse', 'otro', 'situ', 'codp', 'txtNota', 'tipo', 'valo', 'ctac', 'cint']
			for i, dato in enumerate(datos):
				valor_original = r[0][i]
				valor = str(valor_original) if valor_original is not None else ''
				if dato == 'valo':
					# Los bienes antiguos pueden tener valor de adquisición NULL.
					valor = '{:,.2f}'.format(float(valor_original or 0))
					getattr(self, dato).set(valor)
				elif dato == 'txtNota':
					self.txtNota.delete("1.0", "end")
					self.txtNota.insert("1.0", valor)
				else:
					getattr(self, dato).set(valor)
		except Exception as e:
			mb.showinfo(message=f"El codigo no existe, Error: {str(e)} ", title="¡Atencion!")
			print(str(e))

	def actualizar_det(self):

		self.data = [self.marc.get(), self.mode.get(), self.colo.get(), self.seri.get(),
				self.esta.get(), self.dime.get(), self.obse.get(), self.otro.get(), 
				self.situ.get(), self.fech.get(), self.dadq.get(), self.txtNota.get("1.0", "end-1c"),
				self.tipo.get()]

		self.data_c = [self.marc.get(), self.mode.get(), self.colo.get(), self.seri.get(),
					self.esta.get(), self.dime.get(), self.tipo.get()]
	
		if self.marc.get()=="" or self.mode.get()=="" or self.colo.get()=="" or self.seri.get()=="" or self.esta.get()=="" or self.dime.get()=="" or self.tipo.get()=="":
			mb.showinfo(message="Los campos Marca, Modelo, Color, Tipo, Serie, Estado y Dimensiones son obligatorios", title="¡Atención!")
		else:
			try:
				self.validar_datos()				
				actualizar_detalles(self.codi.get(), self.data)
				self.buscar_cod()
				mb.showinfo(message="Se actualizo correctamente", title="Acontar S.A.C.")
				self.destroy()
			except Exception as e:
				mb.showerror(message=f"Error al actualizar, Error {str(e)}", title="Error")

	def actualizar_cod(self):
		j = self.codi.get()
		if j == "":
			mb.showinfo(message="Ingrese un número de acta", title="¡Atencion!")
		else:
			try:
				Acta = self.aact.get()
				now = datetime.now()
				F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
				data = [Acta, F_inv, self.user, self.team]

				actualizar_registro(self.codi.get(), data)
				self.buscar()
				self.buscar_cod()
				mb.showinfo(message="Se actualizo correctamente", title="Actualización")
			except:
				mb.showerror(message="Ocurrio un Error", title="Error")

	def validar_datos(self):
		r = buscar_bien_d(2, self.codigo)
		r_lista = list(r[0])
		if self.data_c == r_lista:
			print("Si coinciden")
		else:
			insertar = cambio_detalles(self.codigo)
			# print(insertar)
			try:
				insertar_tabla2(insertar)
			except Exception as e:
				print(f"Este es el error se duplican {str(e)}")	
			print("No coinciden")
