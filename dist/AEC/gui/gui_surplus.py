import tkinter as tk
from tkinter import CENTER, W, EW, NSEW, ttk, PhotoImage
from tkinter import messagebox as mb
from db.query import delete_sobrante, registrar_sobrantes, mostrar_sobrantes, mostrar_d_personal, actualizar_sobrante
from label.label_sobrante import build_label_sobrante

class Window_surplus(tk.Toplevel):

	def __init__(self, root=None, valor=None):
		super().__init__(root)
		self.title("Sobrantes")
		self.iconbitmap('./img/favicon.ico')
		self.Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
		self.Frame1.pack(fill='x')
		self.Frame2 = tk.Frame(self, bg='#e30613')
		self.Frame2.rowconfigure(0, weight=1)
		self.Frame2.columnconfigure(0, weight=1)
		self.Frame2.pack(fill="both", expand=True)
		self.iconoBuscar = PhotoImage(file='img/buscar.png')
		self.iconoRegistrar = PhotoImage(file='img/registrar.png')
		self.iconoModificar = PhotoImage(file='img/modificar.png')
		self.iconoEliminar = PhotoImage(file='img/borrar.png')

		self.variables()
		self.widgets_01()
		self.tree_view()
		self.bind( "<Double-Button>", self.mostrar_datos)
		self.bind( "<Return>", self.registrar)
		if valor:
			self.acta.set(valor)

	def variables(self):
		self.acta = tk.StringVar()
		self.local = tk.StringVar()
		self.area = tk.StringVar()
		self.oficina = tk.StringVar()
		self.den = tk.StringVar()
		self.estado = tk.StringVar()
		self.marca = tk.StringVar()
		self.modelo = tk.StringVar()
		self.serie = tk.StringVar()
		self.color = tk.StringVar()
		self.dim = tk.StringVar()
		self.obs = tk.StringVar()
		self.tip = tk.StringVar()
		self.otr = tk.StringVar()
		self.sit = tk.StringVar()
		self.cb = tk.IntVar()

	def widgets_01(self):
			# Labels

		lblAct = ttk.Label(self.Frame1, text="Acta").grid(column=0, row=0, padx=5, pady=1, sticky=EW)
		lblLoc = ttk.Label(self.Frame1, text="Local").grid(column=0, row=1, padx=5, pady=1, sticky=EW)
		lblAre = ttk.Label(self.Frame1, text="Área").grid(column=0, row=2, padx=5, pady=1, sticky=EW)
		lblOfi = ttk.Label(self.Frame1, text="Oficina").grid(column=0, row=3, padx=5, pady=1, sticky=EW)

		lblDen = ttk.Label(self.Frame1, text="Denominación").grid(column=3, row=0, padx=5, pady=1, sticky=EW)
		lblEst = ttk.Label(self.Frame1, text="Estado").grid(column=3, row=1, padx=5, pady=1, sticky=EW)
		lblMar = ttk.Label(self.Frame1, text="Marca").grid(column=3, row=2, padx=5, pady=1, sticky=EW)
		lblMod = ttk.Label(self.Frame1, text="Modelo").grid(column=3, row=3, padx=5, pady=1, sticky=EW)

		lblSer = ttk.Label(self.Frame1, text="Serie").grid(column=5, row=0, padx=5, pady=1, sticky=EW)
		lblTip = ttk.Label(self.Frame1, text="Tipo").grid(column=5, row=1, padx=5, pady=1, sticky=EW)
		lblCol = ttk.Label(self.Frame1, text="Color").grid(column=5, row=2, padx=5, pady=1, sticky=EW)
		lblDim = ttk.Label(self.Frame1, text="Dimensión").grid(column=5, row=3, padx=5, pady=1, sticky=EW)

		lblOtr = ttk.Label(self.Frame1, text="Otros").grid(column=7, row=0, padx=5, pady=1, sticky=EW)
		lblSit = ttk.Label(self.Frame1, text="Situación").grid(column=7, row=1, padx=5, pady=1, sticky=EW)
		lblObs = ttk.Label(self.Frame1, text="Observaciones").grid(column=7, row=2, padx=5, pady=1, sticky=EW)
		lblNota = ttk.Label(self.Frame1, text="Nota").grid(row=3, column=7, padx=5, pady=1, sticky=EW)

			# Entrys
		etrnAct = ttk.Entry(self.Frame1, textvariable= self.acta, width=7, justify="center")
		etrnAct.grid(column=1, row=0, padx=5, pady=1, sticky=W)
		etrLoca = ttk.Entry(self.Frame1, textvariable= self.local).grid(column=1, columnspan=2, row=1,padx=5, pady=1, sticky=EW)
		etrArea = ttk.Entry(self.Frame1, textvariable= self.area).grid(column=1, columnspan=2, row=2, padx=5, pady=1, sticky=EW)
		etrOfic = ttk.Entry(self.Frame1, textvariable= self.oficina).grid(column=1, columnspan=2,row=3, padx=5, pady=1, sticky=EW)
		
		etrDeno = ttk.Entry(self.Frame1, textvariable= self.den).grid(column=4, row=0, padx=5, pady=1, sticky=EW)
		etrEsta = ttk.Entry(self.Frame1, textvariable= self.estado).grid(column=4, row=1, padx=5, pady=1, sticky=EW)
		etrMarc = ttk.Entry(self.Frame1, textvariable= self.marca).grid(column=4, row=2, padx=5, pady=1, sticky=EW)
		etrMode = ttk.Entry(self.Frame1, textvariable= self.modelo).grid(column=4, row=3, padx=5, pady=1, sticky=EW)
		
		etrSeri = ttk.Entry(self.Frame1, textvariable= self.serie).grid(column=6, row=0, padx=5, pady=1, sticky=EW)
		etrTipo = ttk.Entry(self.Frame1, textvariable= self.tip).grid(column=6, row=1, padx=5, pady=1, sticky=EW)
		etrColo = ttk.Entry(self.Frame1, textvariable= self.color).grid(column=6, row=2, padx=5, pady=1, sticky=EW)
		etrDime = ttk.Entry(self.Frame1, textvariable= self.dim).grid(column=6, row=3, padx=5, pady=1, sticky=EW)
		
		etrOtro = ttk.Entry(self.Frame1, textvariable= self.otr).grid(column=8, row=0, padx=5, pady=1, sticky=EW)
		etrSitu = ttk.Entry(self.Frame1, textvariable= self.sit).grid(column=8, row=1, padx=5, pady=1, sticky=EW)
		etrObse = ttk.Entry(self.Frame1, textvariable= self.obs).grid(column=8, row=2, padx=5, pady=1, sticky=EW)

		self.txtNota = tk.Text(self.Frame1, height=2, width=1)
		self.txtNota.configure(font=('Arial', 9), bg='white', relief='solid')
		self.txtNota.grid(row=3, column=8, columnspan=2, rowspan=2, padx=5, pady=1, sticky=EW)

			# Buttons
		btnBusc = ttk.Button(self.Frame1, text="Buscar", command=lambda:self.buscar(), image=self.iconoBuscar, compound='left').grid(column=2, row=0)		
		btnReg = ttk.Button(self.Frame1, text="Registrar", command=lambda:self.registrar(),image=self.iconoRegistrar, compound='left').grid(column=9, row=0, sticky=W)
		btnMod = ttk.Button(self.Frame1, text="Modificar", command=lambda:self.modificar(), image=self.iconoModificar, compound='left').grid(column=9, row=1, sticky=W)
		btnDel = ttk.Button(self.Frame1, text="Eliminar", command=lambda:self.eliminar(), image=self.iconoEliminar, compound='left').grid(column=9, row=2, sticky=W)
		btnImp = ttk.Button(self.Frame1, text="Imprimir", command=lambda:self.etiqueta()).grid(column=10, row=0, sticky=W)

		self.marca.set("S/M")
		self.modelo.set("S/M")
		self.serie.set("S/S")
		self.dim.set("S/D")
		self.obs.set("N/A")
		self.tip.set("S/T")

	def etiqueta(self):
		build_label_sobrante(self.acta.get(), self.local.get(), self.area.get(), self.oficina.get(), self.den.get(), 1)
		self.focus_set()

	def tree_view(self):
			# Treeview
		ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
		cab = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18)
		self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')

		self.tree.heading(1, text='Item', anchor=CENTER)
		self.tree.heading(2, text='')
		self.tree.heading(3, text='Acta')
		self.tree.heading(4, text='Local', anchor=CENTER)
		self.tree.heading(5, text='Área', anchor=CENTER)
		self.tree.heading(6, text='Oficina')
		self.tree.heading(7, text='Denominación')
		self.tree.heading(8, text='Estado')
		self.tree.heading(9, text='Marca')
		self.tree.heading(10, text='Modelo')
		self.tree.heading(11, text='Serie')
		self.tree.heading(12, text='Tipo')
		self.tree.heading(13, text='Color')
		self.tree.heading(14, text='Dimension')
		self.tree.heading(15, text='Otros')
		self.tree.heading(16, text='Situación')
		self.tree.heading(17, text='Observaciones')
		self.tree.heading(18, text='Nota')

		self.tree.column(1, width=45, stretch=False)
		self.tree.column(2, width=0, stretch=False)
		self.tree.column(3, width=45, stretch=False)
		self.tree.column(4, width=100, stretch=False)
		self.tree.column(5, width=100, stretch=False)
		self.tree.column(6, width=100, stretch=False)
		self.tree.column(7, width=280, stretch=False)
		self.tree.column(8, width=60, stretch=False)
		self.tree.column(9, width=100, stretch=False)
		self.tree.column(10, width=100, stretch=False)
		self.tree.column(11, width=100, stretch=False)
		self.tree.column(12, width=100, stretch=False)
		self.tree.column(13, width=100, stretch=False)
		self.tree.column(14, width=100, stretch=False)
		self.tree.column(15, width=100, stretch=False)
		self.tree.column(16, width=100, stretch=False)
		self.tree.column(17, width=100, stretch=False)
		self.tree.column(18, width=100, stretch=False)

		# self.tree["displaycolumns"]=(1, 2, 3, 4, 5, 6, 7, 8, 9 ,10, 11, 12, 13, 14)

		self.tree.grid(column=0, row=0, padx=5, pady=5, sticky=NSEW)
		scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
		scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
		self.tree.configure(yscroll=scrollbarV.set)
		self.tree.configure(xscroll=scrollbarH.set)

		scrollbarV.grid(column=1, row=0, sticky='ns')
		scrollbarH.grid(column=0, row=1, sticky='ew')

	def buscar(self):
		try:
			r = mostrar_d_personal(self.acta.get())
			self.local.set(r[0][1])
			self.area.set(r[0][2])
			self.oficina.set(r[0][3])
			for item in self.tree.get_children():
				self.tree.delete(item)
			r = mostrar_sobrantes(self.acta.get())
			for cell, lista in enumerate(r, 1):
				b = list(lista)
				b.insert(0, str(cell))
				self.tree.insert('', tk.END, values=b)
		except:
			mb.showerror(message="El acta no existe", title="Error")
			self.focus_set()
	
	def datos(self):
		build_label_sobrante(self.item, self.local.get(), self.area.get(), self.oficina.get(), self.den.get(), 1)
	
	def registrar(self, *args):

		aa = str(self.acta.get())
		bb = str(self.local.get())
		cc = str(self.area.get())
		dd = str(self.oficina.get())
		ee = str(self.den.get())
		ff = str(self.estado.get())
		gg = str(self.dim.get())
		hh = str(self.marca.get())
		ii = str(self.modelo.get())
		jj = str(self.serie.get())
		kk = str(self.color.get())
		ll = str(self.obs.get())
		mm = str(self.tip.get())
		nn = str(self.otr.get())
		oo = str(self.sit.get())
		pp = self.txtNota.get("1.0", "end-1c")
		registrar_sobrantes(aa, bb, cc, dd, ee, ff, gg, hh, ii, jj, kk, ll, mm, nn, oo, pp)
		# for item in tree.get_children():
		# 	tree.delete(item)
		r = self.acta.get()
		r = mostrar_sobrantes(r)
		for cell, lista in enumerate(r, 1):
			b = list(lista)
		b.insert(0, str(cell))
		self.tree.insert('', tk.END, values=b)			
		# build_label_sobrante(aa, bb, cc, dd, ee, self.cb.get())
		self.limpiar()

	def mostrar(self):
		for item in self.tree.get_children():
			self.tree.delete(item)
		r = self.acta.get()
		r = mostrar_sobrantes(r)
		for cell, lista in enumerate(r, 1):
			b = list(lista)
			b.insert(0, str(cell))
			self.tree.insert('', tk.END, values=b)

	def eliminar(self, *args):
		try:
			curItem = self.tree.focus()
			g = self.tree.item(curItem)['values'][1]
			# print(g)
			delete_sobrante(g)
			# print("Emininado exitosamente")
		except:
			print("No se borro nadas supuestamente")
			self.focus_set()
		self.mostrar()

	def modificar(self):
		curActa = self.tree.focus()
		vnb = self.tree.item(curActa)['values'][1]
		v1 = self.acta.get()
		v2 = self.local.get()
		v3 = self.area.get()
		v4 = self.oficina.get()
		v5 = self.den.get()
		v6 = self.estado.get()
		v7 = self.dim.get()
		v8 = self.marca.get()
		v9 = self.modelo.get()
		v10 = self.serie.get()
		v11 = self.color.get()
		v12 = self.obs.get()
		v13 = self.tip.get()
		v14 = self.otr.get()
		v15 = self.sit.get()
		v16 = self.txtNota.get("1.0", "end-1c")

		data = [v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16]
		
		actualizar_sobrante(vnb, data)
		self.limpiar()
		self.buscar()			
		mb.showinfo(message="Registro actualizado correctamente", title="Acontar S.A.C.")
		self.focus_set()

	def limpiar(self):
		self.den.set("")
		self.estado.set("")
		self.marca.set("S/M")
		self.modelo.set("S/M")
		self.serie.set("S/S")
		self.color.set("")
		self.dim.set("S/D")
		self.obs.set("N/A")
		self.tip.set("S/T")
	
	def mostrar_datos(self, *args):
		curActa = self.tree.focus()
		vnb = self.tree.item(curActa)['values']
		self.item = vnb[1]
		self.acta.set(vnb[2])
		self.local.set(vnb[3])
		self.area.set(vnb[4])
		self.oficina.set(vnb[5])
		self.den.set(vnb[6])
		self.estado.set(vnb[7])
		self.marca.set(vnb[8])
		self.modelo.set(vnb[9])
		self.serie.set(vnb[10])
		self.tip.set(vnb[11])
		self.color.set(vnb[12])
		self.dim.set(vnb[13])
		self.otr.set(vnb[14])
		self.sit.set(vnb[15])
		self.obs.set(vnb[16])
		self.txtNota.delete("1.0", "end")
		self.txtNota.insert("1.0", vnb[17])

