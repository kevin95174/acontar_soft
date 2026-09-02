import tkinter as tk
from tkinter import ttk, PhotoImage
from reportes.faltantes import iniciar_reporte
from utils.order_utils import sort_by
from db.query import detalle_analisis, detalle_analisis_crit


class Window_d_analisis(tk.Toplevel):
    def __init__(self, root=None, acta=None, valor=None, analisis=None):
        super().__init__(root)
    
        self.title("Acontar Especialistas Contables  AEC S.A.C.")
        self.iconbitmap('./img/favicon.ico')
        self.acta = acta
        self.valor = valor
        self.analisis = analisis
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconobus = PhotoImage(file="./img/lupa.png")


        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both')
        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        self.focus_set()
        self.widget_frame1()
        self.tree_view()
        self.iniciar_filtro()

    def widget_frame1(self):

        self.btnPdf = ttk.Button(self.Frame1, text="Generar PDF", image=self.iconopdf, compound='left', command=lambda:iniciar_reporte(self.acta)).grid(row=1, column=4)
        # Treeview
        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblTit = tk.Label(self.Frame1, text='Titulo', anchor='center', font=('Helvetica', 15)).grid(row=0, column=0, pady=5, sticky='ew')
        lblCri = ttk.Label(self.Frame1, text="Criterio").grid(row=1, column=0, padx=5, pady=1, sticky="ew")
                
            # Combobox
#        cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", 
#        values=self.lista).grid(row=0, column=1, padx=5, pady=1, sticky="ew")

            # Entrys
        etrCrit = ttk.Entry(self.Frame1, textvariable=self.camp).grid(row=1, column=2, padx=5, pady=1, sticky="ew")
                # Buttons
        btnCrit = ttk.Button(self.Frame1, text="Buscar", command=lambda:self.filtrar(), image=self.iconobus, compound='left').grid(row=1, column=3, padx=5, pady=1, sticky="ew")

    def tree_view(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))

        cab = []
        
        # Análisis por ubicación
        if self.analisis == 1:
            self.arc = "Análisis por Ubicación "
            self.lista = ['Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                            'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs']
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i:sort_by(self.tree, i, False), anchor='center')
                if i == 11:
                    self.tree.column(11, width=100, stretch=False, anchor='e')
                else:
                    self.tree.column(i, width=100, stretch=False, anchor='w')

        # Análisis por cuenta contable
        elif self.analisis == 2:

            self.arc = "Análisis por cuenta contable "
            self.lista = ['Item', 'Cuenta', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Fecha de\nAdquisición',
                            'Nro. Doc.\nAdquisición', 'Valor de\nAdquisición']
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i:sort_by(self.tree, i, False), anchor='center')
            self.tree.column(1, width=70, stretch=False, anchor='w')
            self.tree.column(2, width=100, stretch=False, anchor='w')
            self.tree.column(3, width=100, stretch=False, anchor='w')
            self.tree.column(4, width=100, stretch=False, anchor='w')
            self.tree.column(5, width=400, stretch=False, anchor='w')
            self.tree.column(6, width=100, stretch=False, anchor='e')
            self.tree.column(7, width=100, stretch=False, anchor='w')
            self.tree.column(8, width=100, stretch=False, anchor='e')
        
        # Análisis por denominacion del bien
        elif self.analisis == 3:
            self.arc = "Análisis por Denominación"
            self.lista = ['Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                            'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs']
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i:sort_by(self.tree, i, False), anchor='center')
                if i == 11:
                    self.tree.column(11, width=100, stretch=False, anchor='w')    
                self.tree.column(i, width=100, stretch=False, anchor='e')

        # Análisis por usuario
        if self.analisis == 4:
            self.arc = "Análisis por Usuario "
            self.lista = ['Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Estado',
                            'Dimensión', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor de\nAdquisición', 'Obs']
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i:sort_by(self.tree, i, False), anchor='center')
                if i == 11:
                    self.tree.column(11, width=100, stretch=False, anchor='w')    
                self.tree.column(i, width=100, stretch=False, anchor='e')
        
        cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", 
        values=self.lista).grid(row=0, column=1, padx=5, pady=1, sticky="ew")
        
        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(column=1, row=0, sticky='ns')

    def iniciar_filtro(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if self.analisis == 1:
            criterio = self.valor[0]
        elif self.analisis == 2:
            criterio = self.valor[1]
        elif self.analisis == 3:
            criterio = self.valor[0]
        elif self.analisis == 4:
            criterio = self.valor[0]

        r = detalle_analisis(self.analisis, criterio)
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def buscar_criterio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = detalle_analisis_crit(self.acta, self.crit.get(), self.camp.get())
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def filtrar(self):
        columna = self.crit.get()
        valor = self.camp.get()
        fila = 1

        # Crear una lista con las filas que coinciden con el criterio de búsqueda
        filas_coinciden = []
        for item in self.tree.get_children():
            valores = self.tree.item(item)["values"]
            if valor.lower() in str(valores[self.lista.index(columna)]).lower():
                filas_coinciden.append((fila,) + tuple(valores[1:]))
                fila += 1
            else:
                self.tree.delete(item)

        # Limpiar el Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insertar las filas que coinciden con la búsqueda con la nueva numeración
        for valores in filas_coinciden:
            self.tree.insert("", "end", text="", values=valores)