import csv
import os
import tkinter as tk
from sqlite3 import Error
from db.conex import iniciar_conexion_sqlite
from datetime import date
from tkinter import ttk, filedialog, PhotoImage
from tkinter import messagebox as mb
from utils.order_utils import sort_by
from db.query import mostrar_inventario, importar_inventario

class Window_inv(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("AEC Importar/Exportar inventario")
        self.iconbitmap('./img/favicon.ico')
        self.iconoImportar = PhotoImage(file='img/subir.png')
        self.iconoCargar = PhotoImage(file='img/subir.png')
        self.iconoValidar = PhotoImage(file='img/validar.png')
        nbk = ttk.Notebook(self)
        self.tab1 = tk.Frame(nbk)
        self.tab2 = tk.Frame(nbk)
        nbk.add(self.tab1, text="Importar")
        nbk.add(self.tab2, text="Exportar")
        nbk.pack(fill="both", expand=True)
        self.tab1_()
        self.treeview()
        self.tab2_()

    def tab1_(self):

        self.Frame1 = tk.Frame(self.tab1, bg="black")
        self.Frame1.pack(fill="both", expand=True)

        self.Frame1_1 = tk.Frame(self.Frame1, bg="#fff")
        self.Frame1_1.pack(fill="both")
        
        self.Frame1_2 = tk.Frame(self.Frame1)
        self.Frame1_2.pack(fill="both", side='bottom', expand=True)

        self.actaIm = tk.StringVar()        
        btnCarg = ttk.Button(self.Frame1_1, text="Cargar", command=lambda:self.cargar_inv(), image=self.iconoImportar, compound='left').grid(row=0, column=0, padx=5, pady=1, sticky="ew")
        btnVali = ttk.Button(self.Frame1_1, text="Validar", command=lambda:self.val_inv(), image=self.iconoValidar, compound='left').grid(row=0, column=1, padx=5, pady=1, sticky="ew")
        lblAct = ttk.Label(self.Frame1_1, text="N° de acta de Inventario a Importar"). grid(row=0, column=2, padx=5, pady=1, sticky="ew")        
        etrActa = ttk.Entry(self.Frame1_1, textvariable=self.actaIm).grid(row=0, column=3, padx=5, pady=1, sticky="ew")

        btnImpo = ttk.Button(self.Frame1_1, text="Importar", command=lambda:self.imp_inv(), image=self.iconoImportar, compound='left').grid(row=0, column=4, padx=5, pady=1, sticky="ew")

    def treeview(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        cab = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
        self.tree = ttk.Treeview(self.Frame1_2, height=25, columns=cab, show='headings')
        self.tree.tag_configure('normal')
        self.tree.tag_configure('fail', foreground="red")
        self.tree.tag_configure('valid', foreground="green")
        self.tree.heading(1, text='Item', command=lambda:sort_by(self.tree, 1, False), anchor="center")
        self.tree.heading(2, text='Inventario', command=lambda:sort_by(self.tree, 2, False))
        self.tree.heading(3, text='Denominacion', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='Fecha de inventario', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='Marca', command=lambda:sort_by(self.tree, 5, False))
        self.tree.heading(6, text='Modelo', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Serie', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='Color', command=lambda:sort_by(self.tree, 8, False))
        self.tree.heading(9, text='Tipo', command=lambda:sort_by(self.tree, 9, False))
        self.tree.heading(10, text='Estado', command=lambda:sort_by(self.tree, 10, False))
        self.tree.heading(11, text='Dimensión', command=lambda:sort_by(self.tree, 11, False))
        self.tree.heading(12, text='Observaciones', command=lambda:sort_by(self.tree, 12, False))
        self.tree.heading(13, text='Otros', command=lambda:sort_by(self.tree, 13, False))
        self.tree.heading(14, text='Situacion', command=lambda:sort_by(self.tree, 14, False))
        self.tree.heading(15, text='NroDocAdq', command=lambda:sort_by(self.tree, 15, False))
        self.tree.heading(16, text='FechAdq', command=lambda:sort_by(self.tree, 16, False))
        self.tree.heading(17, text='Inventariador', command=lambda:sort_by(self.tree, 17, False))
        self.tree.heading(18, text='Equipo', command=lambda:sort_by(self.tree, 18, False))
        self.tree.heading(19, text='Nota', command=lambda:sort_by(self.tree, 19, False))
        self.tree.heading(20, text='Codigo Interno', command=lambda:sort_by(self.tree, 20, False))

        self.tree.column(1, width=50, stretch=False, anchor="center")
        self.tree.column(2, width=100, stretch=False, anchor="center")
        self.tree.column(3, width=250, stretch=False)
        self.tree.column(4, width=150, stretch=False)
        self.tree.column(5, width=80, stretch=False)
        self.tree.column(6, width=80, stretch=False)
        self.tree.column(7, width=80, stretch=False)
        self.tree.column(8, width=80, stretch=False)
        self.tree.column(9, width=80, stretch=False)
        self.tree.column(10, width=80, stretch=False, anchor="center")
        self.tree.column(11, width=80, stretch=False)
        self.tree.column(12, width=100, stretch=False)
        self.tree.column(13, width=100, stretch=False)
        self.tree.column(14, width=100, stretch=False)
        self.tree.column(15, width=100, stretch=False)
        self.tree.column(16, width=100, stretch=False)
        self.tree.column(17, width=100, stretch=False)
        self.tree.column(18, width=100, stretch=False)
        self.tree.column(19, width=100, stretch=False)
        self.tree.column(20, width=100, stretch=False)

        self.tree["displaycolumns"]=(1, 20, 2, 3, 4, 5, 6, 7, 8, 9 ,10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
        
        self.Frame1_2.rowconfigure(0, weight=1)
        self.Frame1_2.columnconfigure(0, weight=1)
        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame1_2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame1_2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def cargar_inv(self):

        filename = filedialog.askopenfilename(
            title = 'Abrir un archivo',
            initialdir = 'exportar/',
            filetypes = (('text files', '*.csv'), 
                        ('all files', '*.*')))
        
        self.last_folder = os.path.dirname(filename)
        
        with open(filename, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            self.datos = list(map(tuple, csv_reader))

        for item in self.tree.get_children():
            self.tree.delete(item)
        for cell, contact in enumerate(self.datos, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)
        self.focus_set()

    def val_inv(self):
        
        comparar = []

        for i in self.datos:
            conn = iniciar_conexion_sqlite()
            sql = f"""SELECT Inv FROM bienes WHERE CodInt = {i[18]}"""
            try:
                cur = conn.cursor()
                cur.execute(sql)
                books = cur.fetchall()
                comparar.append(books)
            except Error as e:
                print("Error selecting mostrar datos: " + str(e))
            finally:
                if conn:
                    cur.close()
                    conn.close()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.fila = 0
            
        for cell, contact in enumerate(self.datos, 1):
            b = list(contact)
            b.insert(0, str(cell))
            my_tag = 'valid'
            # if comparar[cell-1][0][0] == '' or str(b[1]) == comparar[cell-1][0][0]:
            if comparar[cell-1][0][0] != '':
                self.fila += 1
                my_tag = 'fail'
            self.tree.insert('', tk.END, values=b, tag=(my_tag))
        
        if self.fila > 0:
            mb.showinfo(message=f"Existen {str(self.fila)} registros que ya han sido inventariados", title="¡Atención!")
            self.focus_set()
        else:
            mb.showinfo(message="Todo en orden", title="Acontar S.A.C.")
            self.focus_set()

    def imp_inv(self, *args):
        if self.actaIm.get() == "":
            mb.showinfo(message="Ingrese un número de acta para importar datos", title="¡Atención!")
            self.focus_set()
        else:
            if self.fila > 0:
                mb.showinfo(message="Existen registros que ya han sido inventariados", title="¡Atención!")
                self.focus_set()
            else:
                r = mb.askyesno(message="Desea importar el inventario", title="¡Atención!")
                if r == True:
                    try:
                        importar_inventario(self.datos)
                        mb.showinfo(message="Importado con exito", title="Acontar S.A.C.")
                        self.focus_set()
                    except:
                        mb.showerror(message="Ocurrio un error al momento de importar el inventario", title="Error")
                        self.focus_set()

    def tab2_(self):
        self.Frame1 = tk.Frame(self.tab2, bg="black")
        self.Frame1.pack(fill="both")
        self.Frame1_1 = tk.Frame(self.Frame1, bg="#fff")
        self.Frame1_1.pack(fill="both")
        self.Frame1_2 = tk.Frame(self.Frame1)
        self.Frame1_2.pack(fill="both")

        # exportar
        actaEx = tk.StringVar()        
        lblAct = ttk.Label(self.Frame1_1, text="N° de acta de Inventario que desea Exportar"). grid(row=0, column=0, padx=5, pady=1, sticky="ew")
                
        etrActa = ttk.Entry(self.Frame1_1, textvariable=actaEx).grid(row=0, column=1, padx=5, pady=1, sticky="ew")

        # btnCarg = ttk.Button(self.Frame1_1, text="Cargar", command=lambda:self.cargar_inv()).grid(row=0, column=2, padx=5, pady=1, sticky="ew")
        btnExpo = ttk.Button(self.Frame1_1, text="Exportar", command=lambda:exp_inv(actaEx.get())).grid(row=0, column=2, padx=5, pady=1, sticky="ew")

        def exp_inv(acta):
            try:
                r = mostrar_inventario(acta)
                #r = [(row[0], row[1], row[2].strftime('%d/%m/%Y %H:%M:%S'), row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], row[11], row[12], row[13], row[14], row[15], row[16]) for row in r]
                today = date.today()
                archivo = str(acta)+"_"+today.strftime("%d_%m_%Y")+".csv"
                with open("exportar/"+archivo, "w", newline="") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=",")
                    csv_writer.writerows(r)
                mb.showinfo(message="Inventario exportado con exito", title="¡Atención!")
                self.focus_set()
            except Exception as e:
                print(e)
                mb.showerror(message="Ha ocurrido un error al exportar el inventario", title="Error")

