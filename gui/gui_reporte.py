import tkinter as tk
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
from db.query import reporte_01
from reportes.reportes import iniciar_reporte
from reportes.conciliacion import iniciar_conciliacion
from reportes.reporte_contable import iniciar_reporte_contable
from data.exp_excel import exportar_excel
from utils.order_utils import sort_by

class Window_reporte(tk.Toplevel):
    def __init__(self, root=None, valor=None, user=None, team=None):
        super().__init__(root)
    
        self.title("Reportes")
        self.iconbitmap('./img/favicon.ico')
        self.user = user
        self.team = team
        self.valor = valor
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconobus = PhotoImage(file="./img/lupa.png")

        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both')

        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)
        self.widget_01()
        self.tree_view()
        self.realizar_query()

    def widget_01(self):

        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblCri = ttk.Label(self.Frame1, text="Criterio").grid(row=1, column=0, padx=5, pady=1, sticky='ew')
            # Entrys
        etrCrit = ttk.Entry(self.Frame1, textvariable=self.camp).grid(row=1, column=2, padx=5, pady=1, sticky='ew')
                # Buttons
        btnCrit = ttk.Button(self.Frame1, text="Buscar", image=self.iconobus, compound='left', command=lambda:self.filtrar()).grid(row=1, column=3, padx=5, pady=1, sticky='ew')

        btnDesf = ttk.Button(self.Frame1, text="...", width=3, command=lambda:self.realizar_query()).grid(row=1, column=4, padx=5, pady=1)

        btnCsv = ttk.Button(self.Frame1, text="Exportar Excel", image=self.iconoxls, compound='left', command=lambda:self.exportar_datos()).grid(row=1, column=5, padx=1, pady=5, sticky='ew')
        btnPdf = ttk.Button(self.Frame1, text="Exportar PDF", image=self.iconopdf, compound='left', command=lambda:self.exportar_pdf()).grid(row=1, column=6, padx=1, pady=5, sticky='ew')
    
    def tree_view(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))

        cab = []
        # Bienes Ubicados
        if self.valor == 1:
            self.arc = "REPORTE DE BIENES UBICADOS"
            self.lista = ['Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo',
                            'Serie', 'Color', 'Tipo', 'Dimensión', 'Estado', 'Ubicación']
            self.colwidths = [25, 40, 60, 160, 38, 62, 62, 62, 62, 62, 62]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                if i == 12:
                    self.tree.column(12, stretch=False, anchor='w', width=500)              
                else:
                    self.tree.column(i, width=100, stretch=False)              
        # Bienes de otras entidades
        elif self.valor == 2:
            self.arc = "REPORTE DE BIENES DE OTRAS ENTIDADES"
            self.lista = ['Item','Cod\nPatrimonial', 'Denominación', 'Ubicacion', 'Estado', 'Entidad afectante']
            self.colwidths = [28, 70, 170, 260, 38, 210]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Bienes que no coinciden con la descripción
        elif self.valor == 3:
            self.arc = "REPORTE DE BIENES QUE NO COINCIDEN CON LA DESCRIPCIÓN"
            self.lista = ['Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación registrada', 'Ubicación', 'Estado', 'Denominacion corregida']
            self.colwidths = [28, 40, 68, 160, 260, 38, 160]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Bienes para actualización de valor neto
        elif self.valor == 4:
            self.arc = "REPORTE DE BIENES PARA ACTUALIZACIÓN DE VALOR NETO"
            self.lista = ['Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Cuenta\nContable', 'Denominación\nCuenta contable', 'Documento de\nAdquisición', 'Fecha de\nAdquisición', 'Valor de\nAdquisición', 'Depreciación\nAcumulada', 'Valor Neto']
            self.colwidths = [28, 40, 65, 150, 60, 150, 65, 55, 62, 62, 62]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                if i in [9, 10, 11]:
                    self.tree.column(9, width=100, stretch=False, anchor='e')
                    self.tree.column(10, width=100, stretch=False, anchor='e')
                    self.tree.column(11, width=100, stretch=False, anchor='e')
                else:
                    self.tree.column(i, width=100, stretch=False)
        # Bienes en desuso o depositos
        elif self.valor == 5:
            self.arc = "REPORTE DE BIENES EN DESUSO O DEPOSITOS"
            self.lista = ['Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Ubicación', 'Estado', 'Marca', 'Modelo', 'Serie', 'Color', 'Situación']
            self.colwidths = [28, 40, 65, 150, 150, 40, 60, 60, 60, 60, 50]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Bienes afectados en uso o prestamo
        elif self.valor == 6:
            self.arc = "REPORTE DE BIENES AFECTADOS EN USO O PRESTAMO"
            self.lista = ['Item', 'Cod\nInterno', 'Cod\nPatrimonial', 'Denominación', 'Estado', 'Marca', 'Modelo', 'Serie', 'Color', 'Afectante o Beneficiario']
            self.colwidths = [28, 40, 68, 160, 38, 62, 62, 62, 62, 160]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Bienes Faltantes
        elif self.valor == 7:
            self.arc = "REPORTE DE BIENES FALTANTES"
            self.lista = ['Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo',
                            'Serie', 'Color', 'Tipo', 'Dimensión', 'Estado', 'Ubicación']
            self.colwidths = [25, 40, 60, 160, 38, 62, 62, 62, 62, 62, 62]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                if i == 12:
                    self.tree.column(12, stretch=False, anchor='w', width=500)              
                else:
                    self.tree.column(i, width=100, stretch=False)     
        # Bienes Sobrantes
        elif self.valor == 8:
            self.arc = "REPORTE DE BIENES SOBRANTES"
            self.lista = ['Nro', 'Ubicación', 'Denominación', 'Estado', 'Marca', 'Modelo', 'Serie', 'Tipo', 'Color', 'Dimensiones']
            self.colwidths = [28, 160, 160, 40, 60, 60, 60, 60, 60, 62]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Bienes dados de bajo sin disposición
        elif self.valor == 9:
            self.arc = "REPORTE DE BIENES DADOS DE BAJA SIN DISPOSICIÓN"
            self.lista = ['Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Ubicación', 'Estado', 'Marca', 'Modelo', 'Serie', 'Color', 'Tipo', 'Resolución']
            self.colwidths = [28, 40, 68, 160, 160, 60, 60, 60, 60, 60, 60]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                self.tree.column(i, width=100, stretch=False)
        # Conciliacion de Inventario
        elif self.valor == 10:
            self.arc = "CONCILIACIÓN DE INVENTARIO"
            self.lista = ['Cuenta', 'SubCuenta', 'Denominación', 'Registro\nPatrimonial\nValor',
                            'Cantidad\nRegistrados', 'Resultado\nde Inventario\nValor', 'Cantidad\nInventariados',
                            'Valor\nFaltantes', 'Cantidad\nFaltantes']
            self.colwidths = [28, 60, 200, 62, 62, 62, 62, 62, 62]
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
            self.tree.column(1, width=70, stretch=False, anchor='w')
            self.tree.column(2, width=100, stretch=False, anchor='w')
            self.tree.column(3, width=400, stretch=False, anchor='w')
            self.tree.column(4, width=100, stretch=False, anchor='e')
            self.tree.column(5, width=100, stretch=False, anchor='center')
            self.tree.column(6, width=100, stretch=False, anchor='e')
            self.tree.column(7, width=100, stretch=False, anchor='center')
            self.tree.column(8, width=100, stretch=False, anchor='e')
            self.tree.column(9, width=100, stretch=False, anchor='center')
        # Bienes que requieren actualización tecnica
        elif self.valor == 11:
            self.arc = "REPORTE DE BIENES QUE REQUIEREN ACTUALIZACIÓN TECNICA"
            self.lista = ['Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Detalle', 'Estado','Marca', 'Modelo', 'Tipo', 'Serie', 'Color', 'Dimensiones', 'Obs']
            self.colwidths = [25, 35, 60, 140, 56, 25, 60, 60, 60, 60, 60, 60, 60]
            # lblTit = ttk.Label(self.Frame1, text=self.arc, font=("Helvetica", 12, "bold")).grid(row=0, column=0, padx=5, pady=1)
            # self.cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, values=self.lista, state="readonly").grid(row=1, column=1, padx=5, pady=1, sticky='ew')
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                if i == 1 or 2 or 4:
                    self.tree.column(1, width=50, stretch=False)
                    self.tree.column(2, width=60, stretch=False)
                    self.tree.column(4, width=300, stretch=False)
                self.tree.column(i, width=100, stretch=False)

        # REPORTES CONTABLES
        # Bienes ubicados por cuenta contable
        elif self.valor == 12 or 13:
            if self.valor == 12:
                self.arc = "REPORTE DE BIENES UBICADOS POR CUENTA"
            elif self.valor == 13:
                self.arc = "REPORTE DE BIENES FALTANTES POR CUENTA"
            
            self.lista = ['Item', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Cuenta contable', 'Denominacion','Documenton\nAdquisición', 'Fecha\nAdquisición','Valor\nAdquisición']                
            self.colwidths = [25, 35, 60, 200, 56, 200, 56, 56, 56]
        
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False))
                if i == 1 or 2 or 4 or 9:
                    self.tree.column(1, width=50, stretch=False)
                    self.tree.column(2, width=60, stretch=False)
                    self.tree.column(4, width=300, stretch=False)
                    self.tree.column(6, width=300, stretch=False)
                    self.tree.column(9, width=50, stretch=False, anchor='e')
                self.tree.column(i, width=100, stretch=False)        


        lblTit = ttk.Label(self.Frame1, text=self.arc, font=("Helvetica", 12, "bold"), justify='left').grid(row=0, column=0, columnspan=5, padx=5, pady=1, sticky='w')
        self.cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, values=self.lista, state="readonly").grid(row=1, column=1, padx=5, pady=1, sticky='ew')

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)
        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def realizar_query(self):

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        r = reporte_01(self.valor)

        if self.valor == 10:
            for row in r:
                t01 = '{:,.2f}'.format(float(row[3]))
                t02 = '{:,.2f}'.format(float(row[5]))
                t03 = '{:,.2f}'.format(float(row[7]))
                valores = [row[0], row[1], row[2], t01, row[4], t02, row[6], t03, row[8]]
                self.tree.insert('', tk.END, values=valores)
            
            items = self.tree.get_children()
            # Suma de valores para total_01 y total_03
            total_01 = sum(float(self.tree.item(item, 'values')[3].replace(',', '')) for item in items)
            total_03 = sum(float(self.tree.item(item, 'values')[5].replace(',', '')) for item in items)
            total_05 = sum(float(self.tree.item(item, 'values')[7].replace(',', '')) for item in items)

            # Formateo de los valores con comas
            total_01_f = f"{total_01:,.2f}"
            total_03_f = f"{total_03:,.2f}"
            total_05_f = f"{total_05:,.2f}"

            # Suma de valores para total_02 y total_04
            total_02 = sum(int(self.tree.item(item, 'values')[4]) for item in items)
            total_04 = sum(int(self.tree.item(item, 'values')[6]) for item in items)
            total_06 = sum(int(self.tree.item(item, 'values')[8]) for item in items)

            self.tree.insert('', tk.END, values=['TOTALES', '', '', total_01_f, total_02, total_03_f, total_04, total_05_f, total_06])
        else:
            for cell, contact in enumerate(r, 1):
                self.b = list(contact)
                self.b.insert(0, str(cell))
                self.tree.insert('', tk.END, values=self.b)

    def exportar_datos(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)
        exportar_excel(self.arc, self.lista, datos)
        self.focus_set()        

    def exportar_pdf(self):

        file_path = filedialog.askdirectory(initialdir='report_actas/fichas_vehiculares/')
        if not file_path:            
            return
        datos = []
        datos_pdf = []
        
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)

        try:
            if self.valor in [1, 7]:
                for item in datos:
                    marca = 'MARCA: ' + item[4] if item[4] else ''
                    modelo = 'MODELO: ' + item[5] if item[5] else ''
                    serie = 'SERIE: ' + item[6] if item[6] else ''                   
                    color = 'COLOR: ' + item[7] if item[7] else ''
                    tipo = 'TIPO: ' + item[8] if item[8] else ''
                    dimension = 'DIMENSIÓN: ' + item[9] if item[9] else ''

                    detalles_tecnicos = ' - '.join(filter(None,[marca, modelo, serie, color, tipo, dimension]))
                    datos_pdf.append((item[0], item[1], item[2], item[3], detalles_tecnicos, item[10], item[11]))

                lista = ['Nro', 'Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Detalles tecnicos', 'Estado', 'Ubicación']
                colwidths = [25, 33, 60, 170, 200, 25, 200]
                iniciar_reporte(self.arc, lista, datos_pdf, colwidths, file_path)
            elif self.valor == 10:
                iniciar_conciliacion(self.arc, self.lista, datos, self.colwidths, file_path)
            elif self.valor > 11:
                iniciar_reporte_contable(self.arc, self.lista, datos, self.colwidths, file_path)
            else:    
                iniciar_reporte(self.arc, self.lista, datos, self.colwidths, file_path)
            mb.showinfo(title="Acontar S.A.C.", message="Generado con exito")
            self.focus_set()
        except Exception as e:
            mb.showerror(title="Error", message="Error: "+ str(e))
            print(e)
            self.focus_set()

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
    
