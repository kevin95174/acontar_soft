import tkinter as tk
from datetime import datetime
from tkinter import ttk, PhotoImage
from tkinter import messagebox as mb
from reportes.faltantes import iniciar_reporte
from label.label_gen import build_label
from data.exp_excel import exportar_excel
from utils.order_utils import sort_by
from db.query import detalle_bienes, detalle_bienes_faltantes, buscar_criterio_acta_ant, registrar_codpat_test

class Window_detalle(tk.Toplevel):
    def __init__(self, frame_app, root=None, acta=None, valor=None, user=None, team=None):
        super().__init__(root)
    
        self.frame_app = frame_app
        self.title("Detalle de bienes")
        self.iconbitmap('./img/favicon.ico')
        self.acta = acta
        self.valor = valor
        self.user = user
        self.team = team
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconodow = PhotoImage(file="./img/descargas.png")
        self.iconobus = PhotoImage(file="./img/buscar.png")

        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both')
        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        self.widget_frame1()
        self.tree_view()
        self.iniciar_filtro()

    def widget_frame1(self):
        
        self.cb = tk.IntVar()

        self.btnPdf = ttk.Button(self.Frame1, text="Generar PDF", image=self.iconopdf, compound='left', command=lambda:self.generar_pdf()).grid(row=0, column=4)
        self.btnXls = ttk.Button(self.Frame1, text="Exportar Excel", image=self.iconoxls, compound='left', command=lambda:self.exportar_datos()).grid(row=0, column=5)
        if self.valor == 2:
            self.btnReg = ttk.Button(self.Frame1, text="Registrar todo", command=lambda:self.registrar()).grid(row=0, column=6, padx=5)
            # Checkbotton
            self.checkB = ttk.Checkbutton(self.Frame1, text='Imprimir Etiquetas', variable=self.cb, onvalue=1, offvalue=0).grid(column=7, row=0)
        # Treeview
        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblCri = ttk.Label(self.Frame1, text="Criterio").grid(row=0, column=0, padx=5, pady=1, sticky="ew")
                
            # Combobox
        cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", 
        values=['CodInt', 'CodPat', 'DenBien', 'Estado', 'Dimension', 'Marca',
                'Modelo', 'Serie', 'Color', 'ValAdq', 'Obs']).grid(row=0, column=1, padx=5, pady=1, sticky="ew")

            # Entrys
        etrCrit = ttk.Entry(self.Frame1, textvariable=self.camp).grid(row=0, column=2, padx=5, pady=1, sticky="ew")
                # Buttons
        btnCrit = ttk.Button(self.Frame1, text="Buscar", image=self.iconobus, compound='left', command=lambda:self.buscar_criterio()).grid(row=0, column=3, padx=5, pady=1, sticky="ew")

    def tree_view(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        
        self.lista = ['Item', 'Inv. Anerior', 'Inventario', 'Código Interno', 'Código Patrimonial', 'Denominación',
                    'Estado', 'Dimension', 'Marca', 'Modelo', 'Serie', 'Color', 'Valor', 'Obs']
        cab = (1, 2, 3, 4,5, 6, 7, 8, 9, 10, 11, 12, 13, 14)
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')     
        self.tree.heading(1, text='Item', command=lambda:sort_by(self.tree, 1, False), anchor="center")
        self.tree.heading(2, text='Inv\nAnterior', command=lambda:sort_by(self.tree, 2, False))
        self.tree.heading(3, text='Inventario', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='  Cod\nInterno', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='      Cod\nPatrimonial', command=lambda:sort_by(self.tree, 5, False), anchor="center")
        self.tree.heading(6, text='Denominación', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Estado', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='Dimensión', command=lambda:sort_by(self.tree, 8, False))
        self.tree.heading(9, text='Marca', command=lambda:sort_by(self.tree, 9, False))
        self.tree.heading(10, text='Modelo', command=lambda:sort_by(self.tree, 10, False))
        self.tree.heading(11, text='Serie', command=lambda:sort_by(self.tree, 11, False))
        self.tree.heading(12, text='Color', command=lambda:sort_by(self.tree, 12, False))
        self.tree.heading(13, text='Valor', command=lambda:sort_by(self.tree, 13, False))
        self.tree.heading(14, text='Obs', command=lambda:sort_by(self.tree, 14, False))

        self.tree.column(1, width=50, stretch=False)
        self.tree.column(2, width=60, stretch=False)
        self.tree.column(3, width=60, stretch=False)
        self.tree.column(4, width=60, stretch=False)
        self.tree.column(5, width=90, stretch=False, anchor="center")
        self.tree.column(6, width=300, stretch=False)
        self.tree.column(7, width=60, stretch=False, anchor="center")
        self.tree.column(8, width=90, stretch=False)
        self.tree.column(9, width=90, stretch=False)
        self.tree.column(10, width=90, stretch=False)
        self.tree.column(11, width=90, stretch=False)
        self.tree.column(12, width=90, stretch=False)
        self.tree.column(13, width=90, stretch=False, anchor="e")
        self.tree.column(14, width=90, stretch=False)

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def iniciar_filtro(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.valor == 1:
            r = detalle_bienes(self.acta)
            for cell, contact in enumerate(r, 1):
                b = list(contact)
                b.insert(0, str(cell))
                self.tree.insert('', tk.END, values=b)
        elif self.valor == 2:
            r = detalle_bienes_faltantes(self.acta)
            for cell, contact in enumerate(r, 1):
                b = list(contact)
                b.insert(0, str(cell))
                self.tree.insert('', tk.END, values=b)

    def buscar_criterio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = buscar_criterio_acta_ant(self.acta, self.crit.get(), self.camp.get())
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def registrar(self):
        try:
            now = datetime.now()
            F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
            data = [self.acta, F_inv, self.user, self.team]            
            pregunta = mb.askokcancel(message="¿Seguro de registrar todo?", title="¡Atención!")
            if pregunta == True:
                dataTree = []
                for row_id in self.tree.get_children():
                    row = self.tree.item(row_id)['values']
                    dataTree.append(row)
                for i in dataTree:
                    codint = i[3]
                    registrar_codpat_test(codint, data)
                    if self.cb.get() == 1:
                        build_label(1, codint, self.acta)
                if self.frame_app:
                    self.frame_app.iniciar_filtro()
                mb.showinfo(message="Registrado correctamente", title="Acontar S.A.C.")

                if self.cb.get() == 1:
                    mb.showinfo(message="Imprimiendo", title="Aontar S.A.C.")
                for item in self.tree.get_children():
                    self.tree.delete(item)
                r = detalle_bienes_faltantes(self.acta)
                for cell, contact in enumerate(r, 1):
                    b = list(contact)
                    b.insert(0, str(cell))
                    self.tree.insert('', tk.END, values=b)
            self.focus_set()

        except Exception as e:
            print(e)
            mb.showerror(message="Ocurrio un error", title="Error")     

    def generar_pdf(self):
        try:
            iniciar_reporte(self.acta)
            mb.showinfo(message="Generado con exito", title="¡Atención!")
            self.focus_set()
        except Exception as e:
            mb.showerror(message=f"Error al generar el acta, Error {str(e)}")
            self.focus_set()
            print(e)

    def exportar_datos(self):
        datos = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            datos.append(values)
        exportar_excel('Detalle_', self.lista, datos)
        self.focus_set()