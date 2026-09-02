import tkinter as tk
from datetime import date
from tkinter import ttk, PhotoImage, filedialog
from tkinter import messagebox as mb
from reportes.ficha import iniciar_reporte
from gui.gui_detalles import Window_detalles
from db.query import buscar_criterio_acta_ant, ficha_levantamiento, analisis_ficha
from db.query import mostrar_d_personal, inventariador, select_inventariador, select_equipo

class Window_Acta(tk.Toplevel):
    def __init__(self, root=None, acta=None, valor=None, user=None, team=None):
        super().__init__(root)
    
        self.title("Ficha de levantamiento de información")
        self.iconbitmap('./img/favicon.ico')
        self.acta = acta
        self.valor = valor
        self.user = user
        self.team = team
        self.iconoxls = PhotoImage(file="./img/excel.png")
        self.iconopdf = PhotoImage(file="./img/pdf.png")
        self.iconodow = PhotoImage(file="./img/descargas.png")

        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both', side='top')
        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True, side='bottom')
        self.variables()
        self.widget_frame1()
        self.tree_view()
        self.tree.bind("<Double-Button-1>", self.mostrar_datos_)
        

    def variables(self):
        self.acta = tk.StringVar()
        self.ubic = tk.StringVar()   
        self.usua = tk.StringVar()
        self.ndni = tk.StringVar()
        self.inve = tk.StringVar()
        self.idni = tk.StringVar()
        self.equi = tk.StringVar()
        self.fech = tk.StringVar()
        self.crit = tk.StringVar()
        self.camp = tk.StringVar()
        self.nuev = tk.StringVar()
        self.buen = tk.StringVar()
        self.regu = tk.StringVar()
        self.malo = tk.StringVar()
        self.test = tk.StringVar()
        self.euso = tk.StringVar()
        self.desu = tk.StringVar()
        self.tsit = tk.StringVar()
        
        self.Tban = tk.StringVar()
        self.Tida = tk.StringVar()
        self.Tiea = tk.StringVar()
        self.Tfal = tk.StringVar()
        self.Tsob = tk.StringVar()
        self.Tinv = tk.StringVar()

        self.Best = tk.StringVar()
        self.Bsit = tk.StringVar()

        self.nacta = tk.StringVar()

        self.ba = tk.IntVar()

    def widget_frame1(self):
            Frame1_1 = tk.Frame(self.Frame1, bg='#fff')
            Frame1_1.pack(fill='both', expand=True, side='left')

            lista = inventariador()
            personal = []
            for i in lista:
                    personal.append(i[0])
            today = date.today()
            fecha = today.strftime("%d/%m/%Y")

                # Labels
            lblActa = ttk.Label(Frame1_1, text="Nro de Ficha").grid(column=0, row=0, padx=5, pady=5, sticky="ew")
            lblUbic = ttk.Label(Frame1_1, text="Ubicación").grid(column=0, row=1, padx=5, pady=1, sticky="ew")
            lblUsua = ttk.Label(Frame1_1, text="Usuario").grid(column=0, row=2, padx=5, pady=1, sticky="ew")
            lblNdni = ttk.Label(Frame1_1, text="D.N.I.").grid(column=0, row=3, padx=5, pady=1, sticky="ew")
            lblInve = ttk.Label(Frame1_1, text="Inventariador").grid(column=0, row=4, padx=5, pady=1, sticky="ew")
            lblIdni = ttk.Label(Frame1_1, text="D.N.I.").grid(column=0, row=5, padx=5, pady=1, sticky="ew")
            lblEqui = ttk.Label(Frame1_1, text="Equipo").grid(column=2, row=5, padx=5, pady=1, sticky="ew")
            lblFech = ttk.Label(Frame1_1, text='Fecha de Inv.').grid(column=0, row=6, padx=5, pady=1, sticky="ew")

            # checkBar = ttk.Checkbutton(Frame1_1, text='Ficha', variable=self.ba, onvalue=1, offvalue=0, style='White.TCheckbutton').grid(column=0, row=7, padx=5, pady=1, sticky="ew")

            lblCri = ttk.Label(Frame1_1, text="Criterio").grid(column=0, row=8, padx=5, pady=(5,1), sticky="ew")
                    
                # Combobox
            cbxCri = ttk.Combobox(Frame1_1, textvariable=self.crit, state="readonly", 
            values=['Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo', 'Tipo', 'Color', 'Serie', 'Dimensiones',
                    'Otros', 'Situacion', 'Estado de\nConservación', 'Observaciones']).grid(row=8, column=1, padx=5, pady=(5,1), sticky="ew")

                # Entrys
            self.etrnAct = ttk.Entry(Frame1_1, textvariable= self.acta, width=7, justify="center")
            self.etrnAct.grid(column=1, row=0, padx=5, pady=(5,1), sticky="w")
            etrUbic = ttk.Entry(Frame1_1, textvariable= self.ubic).grid(column=1, row=1, columnspan=3, padx=5, pady=1, sticky="ew")
            etrUsua = ttk.Entry(Frame1_1, textvariable= self.usua).grid(column=1, row=2, columnspan=3, padx=5, pady=1, sticky="ew")
            etrNdni = ttk.Entry(Frame1_1, textvariable= self.ndni).grid(column=1,row=3, padx=5, pady=1, sticky="ew")
            cbxInve = ttk.Combobox(Frame1_1, textvariable= self.inve, state='readonly', values=personal)
            cbxInve.grid(column=1, row=4, columnspan=3, padx=5, pady=1, sticky="ew")
            etrIdni = ttk.Entry(Frame1_1, textvariable= self.idni).grid(column=1, row=5, padx=5, pady=1, sticky="ew")
            etrEqui = ttk.Entry(Frame1_1, textvariable= self.equi, justify='center').grid(column=3, row=5, padx=5, pady=1, sticky="ew")
            etrFech = ttk.Entry(Frame1_1, textvariable=self.fech, justify='center').grid(column=1, row=6, padx=5, pady=1, sticky="ew")
            
            # checkBar = ttk.Checkbutton(Frame1_1, text='Código interno', variable=self.ba, onvalue=1, offvalue=0, style='White.TCheckbutton').grid(column=3, row=6, sticky='sew')            

            # etrActa = ttk.Entry(Frame1_1, textvariable=self.nacta, justify= 'center').grid(column=3, row=3, padx=5, pady=1, sticky="ew")
            
            etrCrit = ttk.Entry(Frame1_1, textvariable=self.camp).grid(column=2, row=8, padx=5, pady=1, sticky="ew")
            
                    # Buttons
            btnBusc = ttk.Button(Frame1_1, text="Buscar", width=10, command=lambda:self.iniciar_filtro()).grid(column=2, row=0, sticky='ew')
            btnGene = ttk.Button(Frame1_1, text="PDF", width=5, command=lambda:self.acta_inventario()).grid(column=3, row=0, sticky='ew')
            btnCrit = ttk.Button(Frame1_1, text="Filtrar", command=lambda:self.filtrar()).grid(row=8, column=3, padx=5, pady=(5,1), sticky='ew')

            self.fech.set(fecha)

            Frame1_2 = tk.Frame(self.Frame1, background='#fff')
            Frame1_2.pack(fill='both', side='right', expand=True)

            lblNuev = ttk.Label(Frame1_2, text='Nuevos').grid(column=0, row=0, padx=5, pady=1, sticky='ew')
            lblBuen = ttk.Label(Frame1_2, text='Buenos').grid(column=0, row=1, padx=5, pady=1, sticky='ew')
            lblRegu = ttk.Label(Frame1_2, text='Regulares').grid(column=0, row=2, padx=5, pady=1, sticky='ew')
            lblMalo = ttk.Label(Frame1_2, text='Malos').grid(column=0, row=3, padx=5, pady=1, sticky='ew')
            lblSest = ttk.Label(Frame1_2, text='Blanco').grid(column=0, row=4, padx=5, pady=1, sticky='ew')
            lblTest = ttk.Label(Frame1_2, text='Total').grid(column=0, row=5, padx=5, pady=(5, 1), sticky='ew')

            etrNuev = ttk.Entry(Frame1_2, textvariable=self.nuev, justify='center').grid(column=1, row=0, padx=5, pady=1, sticky='ew')
            etrBuen = ttk.Entry(Frame1_2, textvariable=self.buen, justify='center').grid(column=1, row=1, padx=5, pady=1, sticky='ew')
            etrRegu = ttk.Entry(Frame1_2, textvariable=self.regu, justify='center').grid(column=1, row=2, padx=5, pady=1, sticky='ew')
            etrMalo = ttk.Entry(Frame1_2, textvariable=self.malo, justify='center').grid(column=1, row=3, padx=5, pady=1, sticky='ew')
            etrSest = ttk.Entry(Frame1_2, textvariable=self.Best, justify='center').grid(column=1, row=4, padx=5, pady=1, sticky='ew')
            etrTest = ttk.Entry(Frame1_2, textvariable=self.test, justify='center').grid(column=1, row=5, padx=5, pady=1, sticky='ew')

            lblEUso = ttk.Label(Frame1_2, text='En Uso').grid(column=2, row=0, padx=5, pady=1, sticky='ew')
            lblEDes = ttk.Label(Frame1_2, text='En Desuso').grid(column=2, row=1, padx=5, pady=1, sticky='ew')
            lblSsit = ttk.Label(Frame1_2, text='Blanco').grid(column=2, row=2, padx=5, pady=1, sticky='ew')
            lblTsit = ttk.Label(Frame1_2, text='Total').grid(column=2, row=5, padx=5, pady=1, sticky='ew')

            etrEUso = ttk.Entry(Frame1_2, textvariable=self.euso, justify='center').grid(column=3, row=0, padx=5, pady=1, sticky='ew')
            etrEDes = ttk.Entry(Frame1_2, textvariable=self.desu, justify='center').grid(column=3, row=1, padx=5, pady=1, sticky='ew')
            etrSsit = ttk.Entry(Frame1_2, textvariable=self.Bsit, justify='center').grid(column=3, row=2, padx=5, pady=1, sticky='ew')
            etrTsit = ttk.Entry(Frame1_2, textvariable=self.tsit, justify='center').grid(column=3, row=5, padx=5, pady=1, sticky='ew')

            lblTban = ttk.Label(Frame1_2, text='Total Inv. Ant.').grid(column=4, row=0, padx=5, pady=1, sticky='ew')
            lblTida = ttk.Label(Frame1_2, text='De otras areas').grid(column=4, row=1, padx=5, pady=1, sticky='ew')
            lblTiea = ttk.Label(Frame1_2, text='En otras areas').grid(column=4, row=2, padx=5, pady=1, sticky='ew')
            lblTfal = ttk.Label(Frame1_2, text='Faltantes').grid(column=4, row=3, padx=5, pady=1, sticky='ew')
            lblTsob = ttk.Label(Frame1_2, text='Sobrantes').grid(column=4, row=4, padx=5, pady=1, sticky='ew')
            lblTinv = ttk.Label(Frame1_2, text='Total Inventariados').grid(column=4, row=5, padx=5, pady=1, sticky='ew')

            etrTban = ttk.Entry(Frame1_2, textvariable=self.Tban, justify='center').grid(column=5, row=0, padx=5, pady=1, sticky='ew')
            etrTida = ttk.Entry(Frame1_2, textvariable=self.Tida, justify='center').grid(column=5, row=1, padx=5, pady=1, sticky='ew')
            etrTiea = ttk.Entry(Frame1_2, textvariable=self.Tiea, justify='center').grid(column=5, row=2, padx=5, pady=1, sticky='ew')
            etrTfal = ttk.Entry(Frame1_2, textvariable=self.Tfal, justify='center').grid(column=5, row=3, padx=5, pady=1, sticky='ew')
            etrTsob = ttk.Entry(Frame1_2, textvariable=self.Tsob, justify='center').grid(column=5, row=4, padx=5, pady=1, sticky='ew')
            etrTinv = ttk.Entry(Frame1_2, textvariable=self.Tinv, justify='center').grid(column=5, row=5, padx=5, pady=1, sticky='ew')
            
            cbxInve.bind("<<ComboboxSelected>>", self.actualizar_entry)

    def tree_view(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        
        cab = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        self.lista = ['','Item','Código\nInterno', 'Código\nPatrimonial', 'Denominación', 'Marca', 'Modelo', 'Tipo', 'Color', 'Serie', 'Dimensiones',
                    'Otros', 'Situacion', 'Estado de\nConservación', 'Observaciones']
        
        
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')     
        
        self.tree.heading(1, text='', anchor="center")
        self.tree.heading(2, text='Item', anchor="center")
        self.tree.heading(3, text='Código\nInterno')
        self.tree.heading(4, text='Código\nPatrimonial')
        self.tree.heading(5, text='Denominación',  anchor="center")
        self.tree.heading(6, text='Marca')
        self.tree.heading(7, text='Modelo')
        self.tree.heading(8, text='Tipo')
        self.tree.heading(9, text='Color')
        self.tree.heading(10, text='Serie')
        self.tree.heading(11, text='Dimensión')
        self.tree.heading(12, text='Otros')
        self.tree.heading(13, text='Situación')
        self.tree.heading(14, text='Estado de\nConservación')
        self.tree.heading(15, text='Observaciones')

        self.tree.column(1, width=0, stretch=False, anchor='center')
        self.tree.column(2, width=50, stretch=False, anchor='center')
        self.tree.column(3, width=90, stretch=False)
        self.tree.column(4, width=90, stretch=False)
        self.tree.column(5, width=300, stretch=False)
        self.tree.column(6, width=100, stretch=False)
        self.tree.column(7, width=100, stretch=False)
        self.tree.column(8, width=100, stretch=False)
        self.tree.column(9, width=100, stretch=False)
        self.tree.column(10, width=100, stretch=False)
        self.tree.column(11, width=100, stretch=False)
        self.tree.column(12, width=100, stretch=False)
        self.tree.column(13, width=100, stretch=False, anchor='center')
        self.tree.column(14, width=100, stretch=False, anchor='center')
        self.tree.column(15, width=100, stretch=False)

        #self.tree["displaycolumns"]=(1, 2, 3, 4, 5, 6, 7, 8, 9 ,10, 11, 12, 13, 14)

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky='nsew')
        scrollbarV = ttk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.Frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def iniciar_filtro(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = ficha_levantamiento(self.acta.get())
        for row in r:
            self.tree.insert('', tk.END, values=row)
        
        # SELECT Acta, local, area, oficina, dni, nombre ||' '|| apellidoPat ||' '|| apellidoMat AS fullName FROM personal WHERE Acta = "{id}" 
        datos_usu = mostrar_d_personal(self.acta.get())
        self.ubic.set(datos_usu[0][1]+' - '+datos_usu[0][2]+' - '+datos_usu[0][3])
        self.ndni.set(datos_usu[0][4])
        self.usua.set(datos_usu[0][5])
        
        # print(self.acta.get())
        # print(datos_usu)

        equipo = select_equipo(datos_usu[0][6])
        self.inve.set(equipo[0][0])
        self.idni.set(equipo[0][1])
        self.equi.set(equipo[0][2])

        analisis = analisis_ficha(self.acta.get())
        self.nuev.set(analisis[1])
        self.buen.set(analisis[2])
        self.regu.set(analisis[3])
        self.malo.set(analisis[4])
        self.test.set(analisis[13])
        self.euso.set(analisis[5])
        self.desu.set(analisis[6])
        self.tsit.set(analisis[14])
        self.Tban.set(analisis[7])
        self.Tida.set(analisis[8])
        self.Tiea.set(analisis[9])
        self.Tfal.set(analisis[10])
        self.Tsob.set(analisis[11])
        self.Tinv.set(analisis[12])
        self.Best.set(analisis[15])
        self.Bsit.set(analisis[16])

    def buscar_criterio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = buscar_criterio_acta_ant(self.acta, self.crit.get(), self.camp.get())
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def acta_inventario(self):
        try:
            file_path = filedialog.askdirectory(initialdir='fichas_inventario')
            if file_path:
                iniciar_reporte(self.acta.get(), file_path, self.inve.get(), self.idni.get(), self.equi.get(), self.ba.get(),self.fech.get(), self.acta.get())
                mb.showinfo(message="Generado con exito", title="¡Atención!")
                self.focus_set()
            self.focus_set()
        except Exception as e:
            mb.showerror(message=f"Error al generar el acta, Error {str(e)}")
            self.focus_set()
            print(e)

    def mostrar_datos_(self, *args):
        try:
            curActa = self.tree.focus()
            vnb = self.tree.item(curActa)['values']
            dato = vnb[2]
            ventana_detalles = Window_detalles(codigo=dato)
            ventana_detalles.wait_window(ventana_detalles)
            self.focus_set()
            self.after(0, self.iniciar_filtro)
        except Exception as e:
            self.focus_set()
            print(e)
        
    def actualizar_entry(self, event):
        # Obtenemos el valor seleccionado del combobox
        
        resultado = select_inventariador(self.inve.get())
        # Actualizamos el texto en el entry
        self.idni.set(resultado[0])
        self.equi.set(resultado[1])
    
    def filtrar(self):
        columna = self.crit.get()
        valor = self.camp.get()
        fila = 1
        # Crear una lista con las filas que coinciden con el criterio de búsqueda
        filas_coinciden = []
        for item in self.tree.get_children():
            valores = self.tree.item(item)["values"]         
            if valor.lower() in str(valores[self.lista.index(columna)]).lower():
                filas_coinciden.append(tuple(valores))
                fila += 1
            else:
                self.tree.delete(item)

        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insertar las filas que coinciden con la búsqueda con la nueva numeración
        for valores in filas_coinciden:
            self.tree.insert("", "end", text="", values=valores)
