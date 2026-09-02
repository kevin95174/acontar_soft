import tkinter as tk
from tkinter import messagebox as mb
from tkinter import ttk
from datetime import datetime
from utils.order_utils import sort_by
from data.exp_excel import exportar_excel
from db.query import buscar_data, buscar_bien_d, actualizar_detalles, actualizar_registro
from db.query import cambio_detalles, insertar_tabla2

class Window_buscar(tk.Toplevel):
	def __init__(self, root=None, user=None, team=None):
		super().__init__(root)
		self.root = root
		self.user = user
		self.team = team
		self.title("Buscar")
		self.iconbitmap('./img/favicon.ico')
		self.frame_u = tk.Frame(self)
		self.frame_u.pack(fill='both', expand=True)
		self.variables()
		self.widgets()
		self.widget_field_botton()
		self.buscar()
		self.focus_set()
		self.tree.bind("<Double-Button-1>", self.mostrar_datos_)	

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

		frame_1 = tk.Frame(self.frame_u)
		frame_1.pack(fill="both", side='top')
		frame_1.config(bg="#ffffff")
		
		frame_1_1 = tk.Frame(frame_1)
		frame_1_1.pack(fill="both", side="top")
		frame_1_1.config(bg="#ffffff")

				# Frame top
		lblCod = ttk.Label(frame_1_1, text="Código").grid(column=0, row=0, padx=3, pady=3, sticky="ew")
		etrCod = ttk.Entry(frame_1_1, textvariable= self.codi).grid(column=1, row=0, padx=3, pady=3, sticky="ew")
		etrDen = ttk.Entry(frame_1_1, textvariable= self.deno).grid(column=2, row=0, columnspan=3, padx=3, pady=3, sticky="ew")
		btnBus = ttk.Button(frame_1_1, text="Buscar", command=lambda:self.buscar_cod()).grid(column=5, row=0, padx=3, pady=3, sticky="ew")

				# Labels
		lblInve = ttk.Label(frame_1_1, text="Inventario").grid(column=0, row=1, padx=3, pady=3, sticky="ew")
		lblActA = ttk.Label(frame_1_1, text="Inv. Anterior").grid(column=0, row=2, padx=3, pady=3, sticky="ew")
		lblCtaC = ttk.Label(frame_1_1, text='Cta. Cont.').grid(column=0, row=3, padx=3, pady=3, sticky='ew')
		lblCodP = ttk.Label(frame_1_1, text="Cód. Pat.").grid(column=0, row=4, padx=3, pady=3, sticky="ew")
		lblCodI = ttk.Label(frame_1_1, text="Cód. Int.").grid(column=0, row=5, padx=3, pady=3, sticky="ew")
		lblFecA = ttk.Label(frame_1_1, text="Fecha Adqui.").grid(column=0, row=6, padx=3, pady=3, sticky="ew")
		lblDocA = ttk.Label(frame_1_1, text="Doc. Adqui.").grid(column=0, row=7, padx=3, pady=3, sticky="ew")


				# Entrys
		etrInve = ttk.Entry(frame_1_1, textvariable = self.inve).grid(column=1, row=1, columnspan=2, padx=3, pady=3, sticky="ew")
		etrActA = ttk.Entry(frame_1_1, textvariable = self.acta, state='readonly').grid(column=1, row=2, columnspan=3, padx=3, pady=3, sticky="ew")
		etrCtaC = ttk.Entry(frame_1_1, textvariable = self.ctac, state='readonly').grid(column=1, row=3, columnspan=3, padx=3, pady=3, sticky='ew')		
		etrCodP = ttk.Entry(frame_1_1, textvariable = self.codp, state='readonly').grid(column=1, row=4, padx=3, pady=3, sticky="ew")
		etrCodI = ttk.Entry(frame_1_1, textvariable = self.cint, state='readonly').grid(column=1, row=5, padx=3, pady=3, sticky="ew")
		etrFecA = ttk.Entry(frame_1_1, textvariable = self.fech, state='readonly').grid(column=1, row=6, padx=3, pady=3, sticky="ew")
		etrDocA = ttk.Entry(frame_1_1, textvariable = self.dadq, state='readonly').grid(column=1, row=7, padx=3, pady=3, sticky="ew")

		
		lblValo = ttk.Label(frame_1_1, text='Valor Adqui.').grid(column=2, row=4, padx=3, pady=3, sticky='ew')
		lblOtro = ttk.Label(frame_1_1, text="Otros").grid(column=2, row=5, padx=3, pady=3, sticky="ew")
		lblSitu = ttk.Label(frame_1_1, text="Situacion").grid(column=2, row=6, padx=3, pady=3, sticky="ew")
		lblObse = ttk.Label(frame_1_1, text="Obs").grid(column=2, row=7, padx=3, pady=3, sticky="ew")
				# Entrys

		etrValo = ttk.Entry(frame_1_1, textvariable = self.valo, state='readonly', justify='right').grid(column=3, row=4, padx=3, pady=3, sticky='ew')
		etrOtro = ttk.Entry(frame_1_1, textvariable= self.otro).grid(column=3, row=5, padx=3, pady=3, sticky="ew")
		etrSitu = ttk.Entry(frame_1_1, textvariable= self.situ).grid(column=3, row=6, padx=3, pady=3, sticky="ew")
		etrObse = ttk.Entry(frame_1_1, textvariable= self.obse).grid(column=3, row=7, padx=3, pady=3, sticky="ew")

		lblEsta = ttk.Label(frame_1_1, text="Estado").grid(column=4, row=1, padx=3, pady=3, sticky="ew")
		lblMarc = ttk.Label(frame_1_1, text="Marca").grid(column=4, row=2, padx=3, pady=3, sticky="ew")
		lblMode = ttk.Label(frame_1_1, text="Modelo").grid(column=4, row=3, padx=3, pady=3, sticky="ew")
		lblSeri = ttk.Label(frame_1_1, text="Serie").grid(column=4, row=4, padx=3, pady=3, sticky="ew")
		lblTipo = ttk.Label(frame_1_1, text="Tipo").grid(column=4, row=5, padx=3, pady=3, sticky="ew")
		lblColo = ttk.Label(frame_1_1, text="Color").grid(column=4, row=6, padx=3, pady=3, sticky="ew")
		lblDime = ttk.Label(frame_1_1, text="Dimensión").grid(column=4, row=7, padx=3, pady=3, sticky="ew")

		etrEsta = tk.Entry(frame_1_1, textvariable= self.esta, highlightbackground= "#e30613", highlightthickness=1)
		etrEsta.grid(column=5, row=1, padx=3, pady=3, sticky="ew")
		etrMarc = tk.Entry(frame_1_1, textvariable= self.marc, highlightbackground= "#e30613", highlightthickness=1)
		etrMarc.grid(column=5, row=2, padx=3, pady=3, sticky="ew")
		etrMode = tk.Entry(frame_1_1, textvariable= self.mode, highlightbackground= "#e30613", highlightthickness=1)
		etrMode.grid(column=5, row=3,padx=3, pady=3, sticky="ew")		
		etrSeri = tk.Entry(frame_1_1, textvariable= self.seri, highlightbackground= "#e30613", highlightthickness=1)
		etrSeri.grid(column=5, row=4, padx=3, pady=3, sticky="ew")
		etrTipo = tk.Entry(frame_1_1, textvariable= self.tipo, highlightbackground= "#e30613", highlightthickness=1)
		etrTipo.grid(column=5, row=5, padx=3, pady=3, sticky="ew")
		etrColo = tk.Entry(frame_1_1, textvariable= self.colo, highlightbackground= "#e30613", highlightthickness=1)
		etrColo.grid(column=5, row=6, padx=3, pady=3, sticky="ew")
		etrDime = tk.Entry(frame_1_1, textvariable= self.dime, highlightbackground= "#e30613", highlightthickness=1)
		etrDime.grid(column=5, row=7, padx=3, pady=3, sticky="ew")

		
		btnDeta = ttk.Button(frame_1_1, text="Actualizar", command=lambda:self.actualizar_det()).grid(row=8, column=5, padx=3, pady=3, sticky="ew")
		btnInve = ttk.Button(frame_1_1, text="Inventariar", command=lambda:self.actualizar_cod()).grid(row=1, column=3, padx=3, pady=3, sticky="ew")
		# btnCanc = ttk.Button(frame_1_1, text="Cancelar", command=lambda:self.cancelar_codigo()).grid(row=9, column=5, padx=3, pady=3, sticky="ew")
		
		lblNota = ttk.Label(frame_1_1, text="Nota").grid(row=8, column=0, padx=3, pady=3, sticky="ew")

		self.txtNota = tk.Text(frame_1_1, height=3)
		self.txtNota.configure(font=('Arial', 9), bg='white', relief='solid')
		self.txtNota.grid(row=8, column=1, columnspan=4, rowspan=2, padx=3, pady=3, sticky='nsew')

		self.bien = tk.StringVar()
		self.crit = tk.StringVar()

		lblcrit = ttk.Label(frame_1_1, text="Criterio").grid(row=10, column=0, padx=5, pady=1, sticky="ew")
		cbxCrit = ttk.Combobox(frame_1_1, textvariable=self.crit, state="readonly", 
		values=["CodInt", "ActaAnt", "Inv", "CodPat", "DenBien", "Estado", "Dimension", "Marca", "Modelo", 
            "Serie", "Color", "CtaCont", "ValAdq", "Obs"]).grid(row=10, column=1, padx=1, pady=1, sticky="ew")

		lblBien = ttk.Label(frame_1_1, text="Campo", anchor='center').grid(row=10, column=2, padx=1, pady=1, sticky="ew")
		etrBien = ttk.Entry(frame_1_1, textvariable=self.bien).grid(row=10, column=3, padx=1, pady=1, sticky="ew")
		btnBien = ttk.Button(frame_1_1, text="Buscar", command=lambda:self.buscar()).grid(row=10, column=4, padx=1, pady=1, sticky="ew")
		btnExpo = ttk.Button(frame_1_1, text="Exportar Excel", command=lambda:self.exportar()).grid(row=10, column=5, padx=1, pady=1, sticky="ew")

	def widget_field_botton(self):
		frame_2 = tk.Frame(self.frame_u)
		frame_2.pack(fill="both", side="bottom", expand=True)
		
		frame_2_2 = tk.Frame(frame_2)
		frame_2_2.pack(fill='both', expand=True)
		frame_2_2.rowconfigure(0, weight=1)
		frame_2_2.columnconfigure(0, weight=1)
		frame_2_2.config(bg="#e30613")

		ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
		cab = (1, 2, 3, 4,5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15)
		self.tree = ttk.Treeview(frame_2_2, columns=cab, height=25, show='headings')     
		self.tree.heading(1, text='Item', command=lambda:sort_by(self.tree, 1, False), anchor="center")
		self.tree.heading(2, text='Código\nInterno', command=lambda:sort_by(self.tree, 2, False))
		self.tree.heading(3, text='Acta\nAnt', command=lambda:sort_by(self.tree, 3, False))
		self.tree.heading(4, text='Inv', command=lambda:sort_by(self.tree, 4, False))
		self.tree.heading(5, text='   Código\nPatrimonial', command=lambda:sort_by(self.tree, 5, False), anchor="center")
		self.tree.heading(6, text='Denominación', command=lambda:sort_by(self.tree, 6, False))
		self.tree.heading(7, text='Estado', command=lambda:sort_by(self.tree, 7, False))
		self.tree.heading(8, text='Dimensión', command=lambda:sort_by(self.tree, 8, False))
		self.tree.heading(9, text='Marca', command=lambda:sort_by(self.tree, 9, False))
		self.tree.heading(10, text='Modelo', command=lambda:sort_by(self.tree, 10, False))
		self.tree.heading(11, text='Serie', command=lambda:sort_by(self.tree, 11, False))
		self.tree.heading(12, text='Color', command=lambda:sort_by(self.tree, 12, False))
		self.tree.heading(13, text='Cuenta\nContable', command=lambda:sort_by(self.tree, 13, False))
		self.tree.heading(14, text='Valor', command=lambda:sort_by(self.tree, 14, False))
		self.tree.heading(15, text='Obs', command=lambda:sort_by(self.tree, 15, False))

		self.tree.column(1, width=50, stretch=False)
		self.tree.column(2, width=60, stretch=False)
		self.tree.column(3, width=60, stretch=False)
		self.tree.column(4, width=60, stretch=False)
		self.tree.column(5, width=90, stretch=False, anchor="center")
		self.tree.column(6, width=300, stretch=False)
		self.tree.column(7, width=60, stretch=False)
		self.tree.column(8, width=60, stretch=False, anchor="center")
		self.tree.column(9, width=90, stretch=False)
		self.tree.column(10, width=90, stretch=False)
		self.tree.column(11, width=90, stretch=False)
		self.tree.column(12, width=90, stretch=False)
		self.tree.column(13, width=90, stretch=False)
		self.tree.column(14, width=90, stretch=False, anchor="e")
		self.tree.column(15, width=120, stretch=False)

		self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")

		vscrollbar = ttk.Scrollbar(frame_2_2, orient='vertical', command=self.tree.yview)
		self.tree.configure(yscrollcommand=vscrollbar.set)
		vscrollbar.grid(column=1, row=0, sticky='ns')
		
		hscrollbar = ttk.Scrollbar(frame_2_2, orient='horizontal', command=self.tree.xview)
		self.tree.configure(xscrollcommand=hscrollbar.set)
		hscrollbar.grid(column=0, row=1, sticky='ew')

	def buscar(self):
		for item in self.tree.get_children():
			self.tree.delete(item)
		r = buscar_data(self.crit.get(), self.bien.get())
		for cell, contact in enumerate(r, 1):
			b = list(contact)
			b.insert(0, str(cell))
			self.tree.insert('', tk.END, values=b)
		
	def mostrar_datos_(self, *args):
		curActa = self.tree.focus()
		vnb = self.tree.item(curActa)['values']
		j = vnb[1]
		self.codi.set(j)
		self.buscar_cod()

	def buscar_cod(self, *args):
		r = buscar_bien_d(1, self.codi.get())
		# self.codi.set(self.codi)
		try:
			datos = ['deno', 'inve', 'acta', 'marc', 'seri', 'mode', 'fech', 'dadq', 'colo', 'esta', 
					'dime', 'obse', 'otro', 'situ', 'codp', 'txtNota', 'tipo', 'valo', 'ctac', 'cint']
			for i, dato in enumerate(datos):
				valor = str(r[0][i])
				if dato == 'valo':
					valor = '{:,.2f}'.format(float(valor))
					getattr(self, dato).set(valor)
				elif dato == 'txtNota':
					self.txtNota.delete("1.0", "end")
					self.txtNota.insert("1.0", valor)
				else:
					getattr(self, dato).set(valor)
		except Exception as e:
			mb.showinfo(message=f"El codigo no existe, Error: {str(e)} ", title="¡Atencion!")
			self.focus_set()
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
			self.focus_set()
		else:
			try:
				self.validar_datos()				
				actualizar_detalles(self.codi.get(), self.data)
				self.buscar_cod()
				mb.showinfo(message="Se actualizo correctamente", title="Acontar S.A.C.")
				self.focus_set()
			except Exception as e:
				mb.showerror(message=f"Error al actualizar, Error {str(e)}", title="Error")
				self.focus_set()

	def actualizar_cod(self):
		j = self.inve.get()
		if j == "":
			mb.showinfo(message="Ingrese un número de acta", title="¡Atencion!")
			self.focus_set()
		else:
			try:
				Acta = self.inve.get()
				now = datetime.now()
				F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
				data = [Acta, F_inv, self.user, self.team]

				actualizar_registro(self.codi.get(), data)
				self.buscar()
				self.buscar_cod()
				mb.showinfo(message="Se actualizo correctamente", title="Actualización")
				self.focus_set()
			except:
				mb.showerror(message="Ocurrio un Error", title="Error")
	
	def exportar(self):
		self.lista = ['Item', 'Código interno', 'Acta Ant', 'Inv', 'Código patrimonial', 'Denominación',
				'Estado', 'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Cuenta Contable', 'Valor', 'Obs']
		datos = []
		for item in self.tree.get_children():
			values = self.tree.item(item, "values")
			datos.append(values)
		exportar_excel("Buscar", self.lista, datos)
		self.focus_set()   

	def validar_datos(self):
		r = buscar_bien_d(2, self.codi.get())
		r_lista = list(r[0])
		if self.data_c == r_lista:
			print("Si coinciden")
		else:
			insertar = cambio_detalles(self.codi.get())
			# print(insertar)
			try:
				insertar_tabla2(insertar)
			except Exception as e:
				print(f"Este es el error se duplican {str(e)}")	
			print("No coinciden")