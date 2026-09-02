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

        Frame1 = tk.Frame(self, bg='#ffffff', bd=12)
        Frame1.pack(fill='x')

        Frame2 = tk.Frame(self, bg='#e30613')
        Frame2.rowconfigure(0, weight=1)
        Frame2.columnconfigure(0, weight=1)
        Frame2.pack(fill="both", expand=True)
        

        nomb = tk.StringVar()
        aPat = tk.StringVar()
        aMat = tk.StringVar()
        dni = tk.StringVar()

        acta = tk.StringVar()
        dep = tk.StringVar()
        prov = tk.StringVar()
        dist = tk.StringVar()
        local = tk.StringVar()
        area = tk.StringVar()
        oficina = tk.StringVar()
        ndni = tk.StringVar()
        vnomb = tk.StringVar()
        vaPat = tk.StringVar()
        vaMat = tk.StringVar()

                # Labels
        lblNomb = ttk.Label(Frame1, text="Nombres").grid(column=0, row=0, padx=5, pady=1, sticky="ew")
        lblAPat = ttk.Label(Frame1, text="Apellido Paterno").grid(column=0, row=1, padx=5, pady=1, sticky="ew")
        lblAMat = ttk.Label(Frame1, text="Apellido Materno").grid(column=0, row=2, padx=5, pady=1, sticky="ew")
        lblDni = ttk.Label(Frame1, text="DNI").grid(column=0, row=3, padx=5, pady=1, sticky="ew")

                # Entrys
        etrNomb = ttk.Entry(Frame1,textvariable= nomb).grid(column=1, row=0, padx=5, pady=1, sticky="ew")
        etrAPat = ttk.Entry(Frame1, textvariable= aPat).grid(column=1, row=1, padx=5, pady=1, sticky="ew")
        etrAMat = ttk.Entry(Frame1, textvariable= aMat).grid(column=1, row=2,padx=5, pady=1, sticky="ew")
        etrDni = ttk.Entry(Frame1, textvariable= dni).grid(column=1, row=3, padx=5, pady=1, sticky="ew")

                # Buttons
        btnReg = ttk.Button(Frame1, text="Modificar", command=lambda:modificar()).grid(column=2, row=0, padx=5, sticky="nsew")
        btnDel = ttk.Button(Frame1, text="Eliminar", command=lambda:eliminar_personal()).grid(column=2, row=1, padx=5,sticky="w")
        btnCre = ttk.Button(Frame1, text="Agregar", command=lambda:crear_personal()).grid(column=2, row=3, padx=5, sticky="w")

                # Treeview
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        cab = (1, 2, 3, 4,5, 6, 7, 8, 9, 10, 11)
        tree = ttk.Treeview(Frame2, height=25, columns=cab, show='headings')     

        tree.heading(1, text='Acta', command=lambda:sort_by(self.tree, 1, False))
        tree.heading(2, text='Departamento', command=lambda:sort_by(self.tree, 2, False))
        tree.heading(3, text='Provincia', command=lambda:sort_by(self.tree, 3, False))
        tree.heading(4, text='Distrito', command=lambda:sort_by(self.tree, 4, False))
        tree.heading(5, text='Local', command=lambda:sort_by(self.tree, 5, False))
        tree.heading(6, text='Área', command=lambda:sort_by(self.tree, 6, False))
        tree.heading(7, text='Oficina', command=lambda:sort_by(self.tree, 7, False))
        tree.heading(8, text='DNI', command=lambda:sort_by(self.tree, 8, False))
        tree.heading(9, text='Nombre', command=lambda:sort_by(self.tree, 9, False))
        tree.heading(10, text='Apellido\nPaterno', command=lambda:sort_by(self.tree, 10, False))
        tree.heading(11, text='Apellido\nMaterno', command=lambda:sort_by(self.tree, 11, False))

        tree.column(1, width=45, stretch=False)
        tree.column(2, width=100, stretch=False)
        tree.column(3, width=100, stretch=False)
        tree.column(4, width=100, stretch=False)
        tree.column(5, width=200, stretch=False)
        tree.column(6, width=200, stretch=False)
        tree.column(7, width=200, stretch=False)
        tree.column(8, width=60, stretch=False)
        tree.column(9, width=150, stretch=False)
        tree.column(10, width=150, stretch=False)
        tree.column(11, width=150, stretch=False)

        tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(Frame2, orient=tk.VERTICAL, command=tree.yview)
        scrollbarH = ttk.Scrollbar(Frame2, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscroll=scrollbarV.set)
        tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')
        
        def mostrar():
                for item in tree.get_children():
                        tree.delete(item)     
                r = mostrar_personal()
                for b in r:
                        tree.insert('', tk.END, values=b)
                
        def modificar():
                try:
                        curActa = tree.focus()
                        acta = tree.item(curActa)['values'][0]
                        vnomb = nomb.get()
                        vaPat = aPat.get()
                        vaMat = aMat.get()
                        vndni = dni.get()
                        data = [vnomb, vaPat, vaMat, vndni]
                        actualizar_personal(str(acta), data)
                        mostrar()
                        mb.showinfo(message="Actualido correctamente", title="Acontar S.A.C.")
                except:
                        mb.showerror(message="Ocurrio un error", title="Error")

        def crear_personal():
                lblActa = ttk.Label(Frame1, text="Acta")
                lblActa.grid(column=3, row=0, padx=5, pady=1, sticky="ew")
                lblDep = ttk.Label(Frame1, text="Departamento")
                lblDep.grid(column=3, row=1, padx=5, pady=1, sticky="ew")
                lblProv = ttk.Label(Frame1, text="Provincia")
                lblProv.grid(column=3, row=2, padx=5, pady=1, sticky="ew")
                lblDist = ttk.Label(Frame1, text="Distrito")
                lblDist.grid(column=3, row=3, padx=5, pady=1, sticky="ew")
                lblLocal = ttk.Label(Frame1, text="Local")
                lblLocal.grid(column=5, row=0, padx=5, pady=1, sticky="ew")
                lblArea = ttk.Label(Frame1, text="Area")
                lblArea.grid(column=5, row=1, padx=5, pady=1, sticky="ew")
                lblOficina = ttk.Label(Frame1, text="Oficina")
                lblOficina.grid(column=5, row=2, padx=5, pady=1, sticky="ew")
                lblnDni = ttk.Label(Frame1, text="DNI")
                lblnDni.grid(column=5, row=3, padx=5, pady=1, sticky="ew")
                lblnNomb = ttk.Label(Frame1, text="Nombre")
                lblnNomb.grid(column=7, row=0, padx=5, pady=1, sticky="ew")
                lblnAPat = ttk.Label(Frame1, text="A. Paterno")
                lblnAPat.grid(column=7, row=1, padx=5, pady=1, sticky="ew")
                lblnAMat = ttk.Label(Frame1, text="A. Materno")
                lblnAMat.grid(column=7, row=2, padx=5, pady=1, sticky="ew")

                etrActa = ttk.Entry(Frame1,textvariable= acta)
                etrActa.grid(column=4, row=0, padx=5, pady=1, sticky="ew")
                etrDep = ttk.Entry(Frame1, textvariable= dep)
                etrDep.grid(column=4, row=1, padx=5, pady=1, sticky="ew")
                etrProv = ttk.Entry(Frame1, textvariable= prov)
                etrProv.grid(column=4, row=2,padx=5, pady=1, sticky="ew")
                etrDist = ttk.Entry(Frame1, textvariable= dist)
                etrDist.grid(column=4, row=3, padx=5, pady=1, sticky="ew")
                etrLocal = ttk.Entry(Frame1,textvariable= local)
                etrLocal.grid(column=6, row=0, padx=5, pady=1, sticky="ew")
                etrArea = ttk.Entry(Frame1, textvariable= area)
                etrArea.grid(column=6, row=1, padx=5, pady=1, sticky="ew")
                etrOficina = ttk.Entry(Frame1, textvariable= oficina)
                etrOficina.grid(column=6, row=2,padx=5, pady=1, sticky="ew")
                etrnDni = ttk.Entry(Frame1, textvariable= ndni)
                etrnDni.grid(column=6, row=3, padx=5, pady=1, sticky="ew")
                etrnNomb = ttk.Entry(Frame1, textvariable= vnomb)
                etrnNomb.grid(column=8, row=0, padx=5, pady=1, sticky="ew")
                etrnApat = ttk.Entry(Frame1, textvariable= vaPat)
                etrnApat.grid(column=8, row=1, padx=5, pady=1, sticky="ew")
                etrnAmat = ttk.Entry(Frame1, textvariable= vaMat)
                etrnAmat.grid(column=8, row=2, padx=5, pady=1, sticky="ew")
                btnRegN = ttk.Button(Frame1, text="Registrar", command=lambda:registrar_nuevo())
                btnRegN.grid(column=8, row=3, padx=5,sticky="ew")

                def registrar_nuevo():
                        try:
                                if acta.get()=="":
                                        mb.showinfo(message="Ingrese un número de acta", title="¡Atención!")
                                else:
                                        registrar_personal(acta.get(), dep.get(), prov.get(), dist.get(), local.get(), area.get(), oficina.get(), ndni.get(), vnomb.get(), vaPat.get(), vaMat.get())
                                        mostrar()
                                        mb.showinfo(message="Registrado correctamente", title="Acontar S.A.C.")
                        except:
                                mb.showerror(message="Ocurrio un error", title="Error")

        def eliminar_personal():
                curItem = tree.focus()
                a = tree.item(curItem)['values'][0]
                delete_personal(a)
                mostrar()
                
        def mostrar_datos(*args):
                curActa = tree.focus()
                vnb = tree.item(curActa)['values'][8]
                vap = tree.item(curActa)['values'][9]
                vam = tree.item(curActa)['values'][10]
                vnd = tree.item(curActa)['values'][7]
                nomb.set(vnb)
                aPat.set(vap)
                aMat.set(vam)
                dni.set(vnd)

        self.bind( "<Double-Button>", mostrar_datos)
        mostrar()