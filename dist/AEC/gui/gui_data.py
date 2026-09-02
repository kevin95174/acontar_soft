import tkinter as tk
from tkinter import ttk
from tkinter import ttk, PhotoImage
from tkinter import messagebox as mb
from gui.gui_detalle import Window_detalle
from data.exp_excel import exportar_excel
from utils.order_utils import sort_by
from db.query import estado_inventario, buscar_estado

class Window_data(tk.Toplevel):

    def __init__(self, root=None):
        super().__init__(root)
        self.title("Análisis por Local")
        self.iconbitmap('./img/favicon.ico')
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconodow = PhotoImage(file="./img/descargas.png")
        self.Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
        self.Frame1.pack(fill='x')

        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        self.criterio = tk.StringVar()
        self.cbx = tk.StringVar()
        self.widget_frame1()
        self.tree_view()
        self.mostrar()
        self.tree.bind("<Double-Button-1>", self.mostrar_datos)

    def widget_frame1(self):
                # Labels
        lblCrit = ttk.Label(self.Frame1, text="Criterio").grid(row=0, column=0, padx=5, pady=1, sticky="ew")
                # Combo
        CbxCrit = ttk.Combobox(self.Frame1, textvariable = self.cbx, state="readonly",
                values=['acta', 'local', 'area', 'oficina']).grid(row=0, column=1, padx=5, pady=1, sticky="ew")
                # Entrys
        etrCrit = ttk.Entry(self.Frame1,textvariable= self.criterio).grid(row=0, column=2, padx=5, pady=1, sticky="ew")
                # Buttons
        btnCrit = ttk.Button(self.Frame1, text='Buscar', command=lambda:self.buscar()).grid(row=0, column=3, padx=5, pady=1, sticky="ew")
        btnExpE = ttk.Button(self.Frame1, text="Exportar Excel", image=self.iconoxls,compound='left' , command=lambda:self.exp_estado()).grid(row=0, column=4, padx=5, pady=1, sticky="ew")
                
    def tree_view(self):                
                # Treeview
        self.arc = "Análisis_por_ubicación"
        self.lista = ['Acta', 'Local', 'Área', 'Oficina', 'Total Bienes', 'Total Inventariados', 'Total Faltantes', 'Total Sobrantes']
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        cab = (1, 2, 3, 4,5, 6, 7, 8)
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')     

        self.tree.heading(1, text='Acta', command=lambda:sort_by(self.tree, 1, False))
        self.tree.heading(2, text='Local', command=lambda:sort_by(self.tree, 2, False))
        self.tree.heading(3, text='Área', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='Oficina', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='Total\nBienes', command=lambda:sort_by(self.tree, 5, False))
        self.tree.heading(6, text='Total\nInventariados', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Total\nFaltantes', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='Total\nSobrantes', command=lambda:sort_by(self.tree, 8, False))

        self.tree.column(1, width=50)
        self.tree.column(2, width=120)
        self.tree.column(3, width=130)
        self.tree.column(4, width=150)
        self.tree.column(5, width=100, anchor='center')
        self.tree.column(6, width=100, anchor='center')
        self.tree.column(7, width=100, anchor='center')
        self.tree.column(8, width=100, anchor='center')

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')
        scrollbar = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(column=1, row=0, sticky='ns')

    def mostrar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = estado_inventario()
        for b in r:
            self.tree.insert('', tk.END, values=b)
        self.sumar()

    def buscar(self):
        if self.cbx.get()=="":
            mb.showinfo(message="Seleccione un criterio", title="¡Atención!")
        elif self.criterio.get()=="":
            mb.showinfo(message="Escriba un criterio de busqueda", title="¡Atención!")
        else:
            for item in self.tree.get_children():
                self.tree.delete(item)
            r = buscar_estado(self.cbx.get(), self.criterio.get())
            for b in r:
                self.tree.insert('', tk.END, values=b)
            self.sumar()

    def mostrar_datos(self, *args):
            curActa = self.tree.focus()
            vnb = self.tree.item(curActa)['values'][0]
            Window_detalle(acta=vnb, valor=2)

    def sumar(self):
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
        self.tree.insert('', tk.END, values=['', '', '', 'TOTALES', total_bienes, total_inventariados, total_faltantes, total_sobrantes])

    def exp_estado(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)
        exportar_excel(self.arc, self.lista, datos)
        self.focus_set()

