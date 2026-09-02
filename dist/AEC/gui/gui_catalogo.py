import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from utils.order_utils import sort_by
from db.query import mostrar_catalogo, mostrar_catalogo_criterio

class Window_catalogo(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
    
        self.title("Catalogo de bienes")
        self.iconbitmap('./img/favicon.ico')
        self.grab_set()
        self.focus_set()

        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both')
        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)

        self.widget_frame1()
        self.treeview()
        self.iniciar_filtro()

    def iniciar_filtro(self):
        r = mostrar_catalogo()
        for i in r:
            my_tag = 'normal' if str(i[7]) == str('ACTIVO') else 'fail'            
            self.tree.insert('', tk.END, values=i, tags=(my_tag))


    def widget_frame1(self):
        self.crit = tk.StringVar()
        self.busc = tk.StringVar()

        self.lblCri = ttk.Label(self.Frame1, text="Criterio").grid(row=0, column=0, padx=5, pady=1, sticky="ew")
        self.cbxCri = ttk.Combobox(self.Frame1, textvariable=self.crit, state="readonly", 
		values=['item', 'codigo', 'denominacion', 'unidad', 'grupo', 'clase', 'resolucion', 
        'estado']).grid(row=0, column=1, padx=5, pady=1, sticky="ew")
        self.etrBus = ttk.Entry(self.Frame1, textvariable=self.busc).grid(row=0, column=2, padx=5, pady=1, sticky="ew")
        self.btnBus = ttk.Button(self.Frame1, text="Buscar", command=lambda:self.buscar_criterio()).grid(row=0, column=3, padx=5, pady=1, sticky="ew")
        
    def buscar_criterio(self):
        if  self.crit.get()=='' or self.busc.get()=='':
            mb.showinfo(message="Ingrese un criterio para buscar", title="¡Atención!")
        else:
            for item in self.tree.get_children():
                self.tree.delete(item)
            r = mostrar_catalogo_criterio(self.crit.get(), self.busc.get())
            for i in r:
                my_tag = 'normal' if str(i[7]) == str('ACTIVO') else 'fail'   
                self.tree.insert('', tk.END, values=i, tags=(my_tag))

    def treeview(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))

        cab = (1, 2, 3, 4,5, 6, 7, 8)
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')
        self.tree.tag_configure('normal')
        self.tree.tag_configure('fail', foreground="red")  
        self.tree.heading(1, text='Item', command=lambda:sort_by(self.tree, 1, False), anchor="center")
        self.tree.heading(2, text='Código', command=lambda:sort_by(self.tree, 2, False))
        self.tree.heading(3, text='Denominación (familia)', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='Unidad', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='Grupo', command=lambda:sort_by(self.tree, 5, False))
        self.tree.heading(6, text='Clase', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Resolucion', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='Estado', command=lambda:sort_by(self.tree, 8, False))

        self.tree.column(1, width=50, stretch=False)
        self.tree.column(2, width=60, stretch=False)
        self.tree.column(3, width=250, stretch=False)
        self.tree.column(4, width=60, stretch=False)
        self.tree.column(5, width=250, stretch=False)
        self.tree.column(6, width=250, stretch=False)
        self.tree.column(7, width=200, stretch=False)
        self.tree.column(8, width=90, stretch=False)

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(column=1, row=0, sticky='ns')
