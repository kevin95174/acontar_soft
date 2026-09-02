import tkinter as tk
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
from db.query import analisis_1
from reportes.analisis import iniciar_reporte
from data.exp_excel import exportar_excel
from gui.gui_detalle_analisis import Window_d_analisis
from utils.order_utils import sort_by

class Window_analisis(tk.Toplevel):
    def __init__(self, root=None, valor=None):
        super().__init__(root)
        self.root = root
        self.title("Análisis de resultados")
        self.iconbitmap('./img/favicon.ico')
        self.valor = valor
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconodow = PhotoImage(file="./img/descargas.png")
        self.iconobus = PhotoImage(file="./img/lupa.png")

        self.Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
        self.Frame1.pack(fill='both')
        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)
        self.widget_01()
        self.tree_view()
        # self.realizar_query()
        self.tree.bind("<Double-Button-1>", self.mostrar_datos)

    def realizar_query(self):
        r = analisis_1(self.valor)
        if self.valor == 1:
            for row in r:
                self.tree.insert('', tk.END, values=row)
            items = self.tree.get_children()
            total_bienes = 0
            total_inventariados = 0
            total_faltantes = 0
            total_sobrantes = 0
            for item in items:
                total_bienes += int(self.tree.item(item, 'values')[4])
                total_inventariados += int(self.tree.item(item, 'values')[5])
                total_faltantes += int(self.tree.item(item, 'values')[6])
                total_sobrantes += int(self.tree.item(item, 'values')[7])
            self.tree.insert('', tk.END, values=['TOTALES', '', '', '', total_bienes, total_inventariados, total_faltantes, total_sobrantes])

        elif self.valor == 2:
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

    #         # Formateo de los valores con comas
            total_01_f = f"{total_01:,.2f}"
            total_03_f = f"{total_03:,.2f}"
            total_05_f = f"{total_05:,.2f}"

    #         # Suma de valores para total_02 y total_04
            total_02 = sum(int(self.tree.item(item, 'values')[4]) for item in items)
            total_04 = sum(int(self.tree.item(item, 'values')[6]) for item in items)
            total_06 = sum(int(self.tree.item(item, 'values')[8]) for item in items)

            self.tree.insert('', tk.END, values=['TOTALES', '', '', total_01_f, total_02, total_03_f, total_04, total_05_f, total_06])

        elif self.valor == 3:
            for row in r:
                t01 = '{:,.2f}'.format(float(row[1]))
                t02 = '{:,.2f}'.format(float(row[3]))
                t03 = '{:,.2f}'.format(float(row[5]))
                valores = [row[0], t01, row[2], t02, row[4], t03, row[6]]
                self.tree.insert('', tk.END, values=valores)
            
            items = self.tree.get_children()
            # Suma de valores para total_01 y total_03
            total_01 = sum(float(self.tree.item(item, 'values')[1].replace(',', '')) for item in items)
            total_03 = sum(float(self.tree.item(item, 'values')[3].replace(',', '')) for item in items)
            total_05 = sum(float(self.tree.item(item, 'values')[5].replace(',', '')) for item in items)

            # Formateo de los valores con comas
            total_01_f = f"{total_01:,.2f}"
            total_03_f = f"{total_03:,.2f}"
            total_05_f = f"{total_05:,.2f}"

            # Suma de valores para total_02 y total_04
            total_02 = sum(int(self.tree.item(item, 'values')[2]) for item in items)
            total_04 = sum(int(self.tree.item(item, 'values')[4]) for item in items)
            total_06 = sum(int(self.tree.item(item, 'values')[6]) for item in items)

            self.tree.insert('', tk.END, values=['TOTALES', total_01_f, total_02, total_03_f, total_04, total_05_f, total_06])

        elif self.valor == 4:
            for row in r:
                self.tree.insert('', tk.END, values=row)
            items = self.tree.get_children()
            total_bienes = 0
            total_inventariados = 0
            total_faltantes = 0
            total_sobrantes = 0
            for item in items:
                total_bienes += int(self.tree.item(item, 'values')[4])
                total_inventariados += int(self.tree.item(item, 'values')[5])
                total_faltantes += int(self.tree.item(item, 'values')[6])
                total_sobrantes += int(self.tree.item(item, 'values')[7])
            self.tree.insert('', tk.END, values=['TOTALES', '', '', '', total_bienes, total_inventariados, total_faltantes, total_sobrantes])

    def widget_01(self):
        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblCri = ttk.Label(self.Frame1, text="Criterio").grid(row=1, column=0, padx=5, pady=1, sticky='ew')
                
            # Combobox

            # Entrys
        etrCrit = ttk.Entry(self.Frame1, textvariable=self.camp).grid(row=1, column=2, padx=5, pady=1, sticky='ew')
                # Buttons
        btnCrit = ttk.Button(self.Frame1, text="Buscar", image=self.iconobus, compound="left",command=lambda:self.filtrar()).grid(row=1, column=3, padx=5, pady=1, sticky='ew')      
        btnCsv = ttk.Button(self.Frame1, text="Exportar Excel", image=self.iconoxls, compound="left", command=lambda:self.exportar_datos()).grid(row=1, column=4, padx=1, pady=5, sticky='ew')
        btnPdf = ttk.Button(self.Frame1, text="Exportar PDF", image=self.iconopdf, compound="left", command=lambda:self.generar_pdf()).grid(row=1, column=5, padx=1, pady=5, sticky='ew')
    
    def tree_view(self):

        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))

        cab = []
        # análisis por ubicación
        if self.valor == 1:
            self.arc = "ANÁLISIS POR UBICACIÓN "
            self.lista = ['Acta', 'Local', 'Área', 'Oficina', 'Total\nBienes', 'Total\nInventariados', 'Total\nFaltantes', 'Total\nSobrantes']
            self.colWidths = [30, 160, 160, 160, 60, 60, 60, 60]
            self.orientacion = 0
            self.columna = 4
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False), anchor='center')
                # self.tree.heading(i, text=val, command=lambda:sort_by(i, False), anchor='center')
            self.tree.column(1, width=50, stretch=False)
            self.tree.column(2, width=120, stretch=False)
            self.tree.column(3, width=130, stretch=False)
            self.tree.column(4, width=150, stretch=False)
            self.tree.column(5, width=100, anchor='center', stretch=False)
            self.tree.column(6, width=100, anchor='center', stretch=False)
            self.tree.column(7, width=100, anchor='center', stretch=False)
            self.tree.column(8, width=100, anchor='center', stretch=False)
        # Por cuenta contable
        elif self.valor == 2:
            self.arc = "ANÁLISIS POR CUENTA CONTABLE "
            self.lista = ['Cuenta', 'SubCuenta', 'Denominación', 'Registro\nPatrimonial\nValor',
                            'Cantidad\nRegistrados', 'Resultado\nde Inventario\nValor', 'Cantidad\nInventariados',
                            'Valor\nFaltantes', 'Cantidad\nFaltantes']
            self.colWidths = [55, 70, 180, 75, 65, 75, 65, 75, 65]
            self.orientacion = 0
            self.columna = 3
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False), anchor='center')
                # self.tree.heading(i, text=val, command=lambda:sort_by(i, False), anchor='center')
            self.tree.column(1, width=70, stretch=False, anchor='w')
            self.tree.column(2, width=100, stretch=False, anchor='w')
            self.tree.column(3, width=400, stretch=False, anchor='w')
            self.tree.column(4, width=100, stretch=False, anchor='e')
            self.tree.column(5, width=100, stretch=False, anchor='center')
            self.tree.column(6, width=100, stretch=False, anchor='e')
            self.tree.column(7, width=100, stretch=False, anchor='center')
            self.tree.column(8, width=100, stretch=False, anchor='e')
            self.tree.column(9, width=100, stretch=False, anchor='center')
        # Por denominación del bien
        elif self.valor == 3:
            self.arc = "ANÁLISIS POR BIEN "
            self.lista = ['Denominación', 'Registro\nPatrimonial\nValor',
                            'Cantidad\nRegistrados', 'Resultado\nde Inventario\nValor', 'Cantidad\nInventariados',
                            'Valor\nFaltantes', 'Cantidad\nFaltantes']
            self.colWidths = [160, 60, 60, 60, 60, 60, 60]
            self.orientacion = 1
            self.columna = 1
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)
            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.lista, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False), anchor='center')

            self.tree.column(1, width=400, stretch=False, anchor='w')
            self.tree.column(2, width=100, stretch=False, anchor='e')
            self.tree.column(3, width=100, stretch=False, anchor='center')
            self.tree.column(4, width=100, stretch=False, anchor='e')
            self.tree.column(5, width=100, stretch=False, anchor='center')
            self.tree.column(6, width=100, stretch=False, anchor='e')
            self.tree.column(7, width=100, stretch=False, anchor='center')
        # Analisis por usuario
        elif self.valor == 4:
            self.arc = "ANÁLISIS POR USUARIO "
            self.listaT = ['Usuario', 'Local', 'Área', 'Oficina', 'Total\nBienes', 'Total\nInventariados', 'Total\nFaltantes', 'Total\nSobrantes']
            self.lista = ['Usuario', 'Ubicación', 'Total\nBienes', 'Total\nInventariados', 'Total\nFaltantes', 'Total\nSobrantes']
            
            self.colWidths = [150, 300, 60, 60, 60, 60]
            self.orientacion = 0
            self.columna = 2
            for i in range(1, int(len(self.listaT)+1)):
                cab.append(i)

            self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
            for i, val in enumerate(self.listaT, start=1):
                self.tree.heading(i, text=val, command=lambda i=i: sort_by(self.tree, i, False), anchor='center')
                # self.tree.heading(i, text=val, command=lambda:sort_by(i, False), anchor='center')
            self.tree.column(1, width=160, stretch=False)
            self.tree.column(2, width=120, stretch=False)
            self.tree.column(3, width=130, stretch=False)
            self.tree.column(4, width=150, stretch=False)
            self.tree.column(5, width=100, anchor='center', stretch=False)
            self.tree.column(6, width=100, anchor='center', stretch=False)
            self.tree.column(7, width=100, anchor='center', stretch=False)
            self.tree.column(8, width=100, anchor='center', stretch=False)

        cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", 
        values=self.lista).grid(row=1, column=1, padx=5, pady=1, sticky='ew')
        lblTit = ttk.Label(self.Frame1, text=self.arc, font=("Helvetica", 12, "bold"), justify='left').grid(row=0, column=0, columnspan=5, padx=5, pady=1, sticky='w')
        
        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)
        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')
        self.tree.tag_configure('Treeview.Cell', font=('Arial', 15))
        # self.realizar_query()

    def generar_pdf(self):
        try:
            data = []
            for row_id in self.tree.get_children():
                row = self.tree.item(row_id)['values']
                if self.valor == 4:
                    ubicacion = f"{row[1]} - {row[2]} - {row[3]}"
                    row[1] = ubicacion
                    row = [row[0]] + [row[1]] + row[4:]
                data.append(row)
            file_path = filedialog.askdirectory(initialdir='report_actas/reporte_analisis/')
            if file_path:
                iniciar_reporte(data, file_path, self.colWidths, self.arc, self.lista, self.orientacion, self.columna)
                mb.showinfo(message="Exportado con exito", title="¡Atención!")
        except Exception as e:
            mb.showerror(message="Ha ocurrido un error al exportar", title="Error")
            print(str(e))
        self.focus_set()
    
    def exportar_datos(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)
        exportar_excel(self.arc, self.lista, datos)
        self.focus_set()

    def mostrar_datos(self, *args):
            curActa = self.tree.focus()
            vnb = self.tree.item(curActa)['values']
            # print(vnb)
            Window_d_analisis(valor=vnb, analisis=self.valor)

    def filtrar(self):
        columna = self.crit.get()
        valor = self.camp.get()
        fila = 1

        if columna or valor == '':
            self.realizar_query()
        else:
            # Crear una lista con las filas que coinciden con el criterio de búsqueda
            filas_coinciden = []
            for item in self.tree.get_children():
                valores = self.tree.item(item)["values"]
                if valor.lower() in str(valores[self.lista.index(columna)]).lower():
                    filas_coinciden.append(tuple(valores))
                    fila += 1
                else:
                    self.tree.delete(item)
            # Limpiar el Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Insertar las filas que coinciden con la búsqueda con la nueva numeración
            for valores in filas_coinciden:
                self.tree.insert("", "end", text="", values=valores)