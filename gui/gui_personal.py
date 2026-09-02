import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
from utils.order_utils import sort_by
from db.query import mostrar_personal, actualizar_personal, registrar_personal, delete_personal

class Window_personal(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
        self.title("Registrar usuario/ubicación")
        self.iconbitmap('./img/favicon.ico')
        self.transient(root)

        self.Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
        self.Frame1.pack(fill='x')

        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True)
        self.variables()
        self.widgets()
        self.mostrar()
        self.bind( "<Double-Button>", self.mostrar_datos)

    def variables(self):

        self.nomb = tk.StringVar()
        self.aPat = tk.StringVar()
        self.aMat = tk.StringVar()
        self.dni = tk.StringVar()

        self.acta = tk.StringVar()
        self.dep = tk.StringVar()
        self.prov = tk.StringVar()
        self.dist = tk.StringVar()
        self.local = tk.StringVar()
        self.area = tk.StringVar()
        self.oficina = tk.StringVar()
        self.equipo = tk.StringVar()

    def widgets(self):
                # Labels
        lblNomb = ttk.Label(self.Frame1, text="Nombres").grid(column=0, row=0, padx=5, pady=1, sticky="ew")
        lblAPat = ttk.Label(self.Frame1, text="Apellido Paterno").grid(column=0, row=1, padx=5, pady=1, sticky="ew")
        lblAMat = ttk.Label(self.Frame1, text="Apellido Materno").grid(column=0, row=2, padx=5, pady=1, sticky="ew")
        lblDni = ttk.Label(self.Frame1, text="DNI").grid(column=0, row=3, padx=5, pady=1, sticky="ew")

                # Entrys
        etrNomb = ttk.Entry(self.Frame1,textvariable= self.nomb).grid(column=1, row=0, padx=5, pady=1, sticky="ew")
        etrAPat = ttk.Entry(self.Frame1, textvariable= self.aPat).grid(column=1, row=1, padx=5, pady=1, sticky="ew")
        etrAMat = ttk.Entry(self.Frame1, textvariable= self.aMat).grid(column=1, row=2,padx=5, pady=1, sticky="ew")
        etrDni = ttk.Entry(self.Frame1, textvariable= self.dni).grid(column=1, row=3, padx=5, pady=1, sticky="ew")

                # Buttons
        btnReg = ttk.Button(self.Frame1, text="Modificar", command=lambda:self.modificar()).grid(column=7, row=0, padx=5, sticky="nsew")
        btnDel = ttk.Button(self.Frame1, text="Eliminar", command=lambda:self.eliminar_personal()).grid(column=7, row=1, padx=5,sticky="w")
        # btnCre = ttk.Button(self.Frame1, text="Agregar", command=lambda:crear_personal()).grid(column=2, row=3, padx=5, sticky="w")

        lblActa = ttk.Label(self.Frame1, text="Acta")
        lblActa.grid(column=2, row=0, padx=5, pady=1, sticky="ew")
        lblDep = ttk.Label(self.Frame1, text="Departamento")
        lblDep.grid(column=2, row=1, padx=5, pady=1, sticky="ew")
        lblProv = ttk.Label(self.Frame1, text="Provincia")
        lblProv.grid(column=2, row=2, padx=5, pady=1, sticky="ew")
        lblDist = ttk.Label(self.Frame1, text="Distrito")
        lblDist.grid(column=2, row=3, padx=5, pady=1, sticky="ew")
        lblLocal = ttk.Label(self.Frame1, text="Local")
        lblLocal.grid(column=4, row=0, padx=5, pady=1, sticky="ew")
        lblArea = ttk.Label(self.Frame1, text="Área")
        lblArea.grid(column=4, row=1, padx=5, pady=1, sticky="ew")
        lblOficina = ttk.Label(self.Frame1, text="Oficina")
        lblOficina.grid(column=4, row=2, padx=5, pady=1, sticky="ew")
        lblEInvetario = ttk.Label(self.Frame1, text="Equipo")
        lblEInvetario.grid(column=4, row=3, padx=5, pady=1, sticky="ew")

        etrActa = ttk.Entry(self.Frame1,textvariable= self.acta)
        etrActa.grid(column=3, row=0, padx=5, pady=1, sticky="ew")
        etrDep = ttk.Entry(self.Frame1, textvariable= self.dep)
        etrDep.grid(column=3, row=1, padx=5, pady=1, sticky="ew")
        etrProv = ttk.Entry(self.Frame1, textvariable= self.prov)
        etrProv.grid(column=3, row=2,padx=5, pady=1, sticky="ew")
        etrDist = ttk.Entry(self.Frame1, textvariable= self.dist)
        etrDist.grid(column=3, row=3, padx=5, pady=1, sticky="ew")
        etrLocal = ttk.Entry(self.Frame1,textvariable= self.local)
        etrLocal.grid(column=5, row=0, padx=5, pady=1, sticky="ew")
        etrArea = ttk.Entry(self.Frame1, textvariable= self.area)
        etrArea.grid(column=5, row=1, padx=5, pady=1, sticky="ew")
        etrOficina = ttk.Entry(self.Frame1, textvariable= self.oficina)
        etrOficina.grid(column=5, row=2,padx=5, pady=1, sticky="ew")
        etrEInvetario = ttk.Entry(self.Frame1, textvariable= self.equipo)
        etrEInvetario.grid(column=5, row=3,padx=5, pady=1, sticky="ew")

        btnRegN = ttk.Button(self.Frame1, text="Registrar", command=lambda:self.registrar_nuevo())
        btnRegN.grid(column=7, row=2, padx=5,sticky="ew")

                # Treeview
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        cab = (1, 2, 3, 4,5, 6, 7, 8, 9, 10, 11, 12)
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')     

        self.tree.heading(1, text='Acta', command=lambda:sort_by(self.tree, 1, False))
        self.tree.heading(2, text='Departamento', command=lambda:sort_by(self.tree, 2, False))
        self.tree.heading(3, text='Provincia', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='Distrito', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='Local', command=lambda:sort_by(self.tree, 5, False))
        self.tree.heading(6, text='Área', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Oficina', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='DNI', command=lambda:sort_by(self.tree, 8, False))
        self.tree.heading(9, text='Nombre', command=lambda:sort_by(self.tree, 9, False))
        self.tree.heading(10, text='Apellido\nPaterno', command=lambda:sort_by(self.tree, 10, False))
        self.tree.heading(11, text='Apellido\nMaterno', command=lambda:sort_by(self.tree, 11, False))
        self.tree.heading(12, text='Equipo\nInventario', command=lambda:sort_by(self.tree, 12, False))

        self.tree.column(1, width=45, stretch=False)
        self.tree.column(2, width=100, stretch=False)
        self.tree.column(3, width=100, stretch=False)
        self.tree.column(4, width=100, stretch=False)
        self.tree.column(5, width=200, stretch=False)
        self.tree.column(6, width=200, stretch=False)
        self.tree.column(7, width=200, stretch=False)
        self.tree.column(8, width=60, stretch=False)
        self.tree.column(9, width=150, stretch=False)
        self.tree.column(10, width=150, stretch=False)
        self.tree.column(11, width=150, stretch=False)
        self.tree.column(12, width=100, stretch=False)

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')
        
    def mostrar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)     
        r = mostrar_personal()
        for b in r:
            self.tree.insert('', tk.END, values=b)
            
    def modificar(self):

        # curActa = self.tree.focus()
        # self.acta = self.tree.item(curActa)['values'][0]

        vnomb = self.nomb.get()
        vaPat = self.aPat.get()
        vaMat = self.aMat.get()
        vndni = self.dni.get()

        departamento = self.dep.get()
        provincia = self.prov.get()
        distrito = self.dist.get()
        vlocal = self.local.get()
        varea = self.area.get()
        voficina = self.oficina.get()
        vequipo = self.equipo.get()

        data = [vnomb, vaPat, vaMat, vndni, departamento, provincia, distrito, vlocal, varea, voficina, vequipo]
        try:
            actualizar_personal(self.acta.get(), data)
            self.mostrar()
            mb.showinfo(message="Actualizado correctamente", title="Acontar S.A.C.")
            self.focus_set()
        except Exception as e:
            print(e)
            mb.showerror(message="Ocurrio un error", title="Error")
            self.focus_set()

    def registrar_nuevo(self):

        if self.acta.get()=="":
            mb.showinfo(message="Ingrese un número de Ficha", title="¡Atención!")
            self.focus_set()
        else:
            try:
                registrar_personal(self.acta.get(), self.dep.get(), self.prov.get(), self.dist.get(), self.local.get(), self.area.get(), self.oficina.get(), self.dni.get(), self.nomb.get(), self.aPat.get(), self.aMat.get())
                self.mostrar()
                mb.showinfo(message="Registrado correctamente", title="Acontar S.A.C.")
                self.focus_set()
            except Exception as e:
                print(e)
                mb.showerror(message="Ocurrio un error", title="Error")
                self.focus_set()

    def eliminar_personal(self):
        curItem = self.tree.focus()
        a = self.tree.item(curItem)['values'][0]
        try:
            delete_personal(a)
            self.mostrar()
            mb.showinfo(message="Eliminado correctamente", title="Acontar S.A.C.")
            self.focus_set()
        except Exception as e:
            print(e)
            mb.showinfo(message="Error", title="Acontar S.A.C.")
            self.focus_set()

    def mostrar_datos(self, event):

        curActa = self.tree.focus()

        self.acta.set(self.tree.item(curActa)['values'][0])
        self.dep.set(self.tree.item(curActa)['values'][1])
        self.prov.set(self.tree.item(curActa)['values'][2])
        self.dist.set(self.tree.item(curActa)['values'][3])
        self.local.set(self.tree.item(curActa)['values'][4])
        self.area.set(self.tree.item(curActa)['values'][5])
        self.oficina.set(self.tree.item(curActa)['values'][6])
        self.dni.set(self.tree.item(curActa)['values'][7])
        self.nomb.set(self.tree.item(curActa)['values'][8])
        self.aPat.set(self.tree.item(curActa)['values'][9])
        self.aMat.set(self.tree.item(curActa)['values'][10])
        self.equipo.set(self.tree.item(curActa)['values'][11])