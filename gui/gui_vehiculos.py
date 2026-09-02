import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as mb
from db.query import rep_vehiculos, registrar_vehiculo, selec_vehiculos, selec_vehiculos_tab1
from db.query import actualizar_vehiculo
from reportes.ficha_vehicular import iniciar_reporte
from gui.gui_detalles import Window_detalles

class Window_vehiculos(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)

        self.title("Vehiculos")
        self.iconbitmap('./img/favicon.ico')

        self.notebook = ttk.Notebook(self)
        self.tab1 = tk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Pestaña 1")

        self.tab2 = tk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Pestaña 2")
        
        self.notebook.pack(fill='both', expand=True)
    
        self.tab1_()
        self.mostra_datos()
        # self.tab2_()

    def tab1_(self):
        self.frameU = tk.Frame(self.tab1)
        self.frameU.pack(fill='both', expand=True)

        self.frame1 = tk.Frame(self.frameU, bg='white')
        self.frame1.pack(fill='both', side='top')
        
        self.frame2 = tk.Frame(self.frameU, bg='#e30613')
        self.frame2.pack(fill='both', side='bottom', expand=True)
        
        self.frame2.rowconfigure(0, weight=1)
        self.frame2.columnconfigure(0, weight=1)

        self.widget_frame1()
        self.tree_view()

        self.tree.bind("<Double-Button-1>", self.mostrar_datos_)
        self.tree.bind("<Triple-Button-1>", self.mostrar_detalles_)
        
    def widget_frame1(self):
        
        self.codi = tk.StringVar()

        self.lblCod = ttk.Label(self.frame1, text='Código').grid(row=0, column=0, padx=1, pady=1, sticky='ew')
        self.etrCod = ttk.Entry(self.frame1, textvariable=self.codi).grid(row=0, column=1, padx=1, pady=1, sticky='ew')
        self.btnBus = ttk.Button(self.frame1, text='Buscar', command=lambda:self.buscar_codigo(self.codi.get())).grid(row=0, column=2, padx=1, pady=1, sticky='ew')
        self.btnAct = ttk.Button(self.frame1, text='Actualizar', command=lambda:self.actualizar()).grid(row=0, column=3, padx=1, pady=1, sticky='ew')
        self.btnPdf = ttk.Button(self.frame1, text='Generar ficha', command=lambda:self.generar_ficha()).grid(row=0,  column=4, padx=1, pady=1, sticky='ew')

        self.v = []
        for i in range(18):
            string_var = tk.StringVar()
            self.v.append(string_var)

        self.l1 = ttk.Label(self.frame1, text="Entidad").grid(row=1, column=0, padx=1, pady=1, sticky='ew')
        self.l2 = ttk.Label(self.frame1, text="Denominación").grid(row=2, column=0, padx=1, pady=1, sticky='ew')
        self.l3 = ttk.Label(self.frame1, text="N° Placa vehícular").grid(row=3, column=0, padx=1, pady=1, sticky='ew')
        self.l4 = ttk.Label(self.frame1, text="Carroceria").grid(row=4, column=0, padx=1, pady=1, sticky='ew')
        self.l5 = ttk.Label(self.frame1, text="Marca").grid(row=5, column=0, padx=1, pady=1, sticky='ew')
        self.l6 = ttk.Label(self.frame1, text="Modelo").grid(row=6, column=0, padx=1, pady=1, sticky='ew')

        self.e1 = ttk.Entry(self.frame1, textvariable=self.v[0]).grid(row=1, column=1, padx=1, pady=1, sticky='ew')
        self.e2 = ttk.Entry(self.frame1, textvariable=self.v[1]).grid(row=2, column=1, padx=1, pady=1, sticky='ew')
        self.e3 = ttk.Entry(self.frame1, textvariable=self.v[2]).grid(row=3, column=1, padx=1, pady=1, sticky='ew')
        self.e4 = ttk.Entry(self.frame1, textvariable=self.v[3]).grid(row=4, column=1, padx=1, pady=1, sticky='ew')
        self.e5 = ttk.Entry(self.frame1, textvariable=self.v[4]).grid(row=5, column=1, padx=1, pady=1, sticky='ew')
        self.e6 = ttk.Entry(self.frame1, textvariable=self.v[5]).grid(row=6, column=1, padx=1, pady=1, sticky='ew')


        self.l7 = ttk.Label(self.frame1, text="Categoria").grid(row=1, column=2, padx=5, pady=1, sticky='ew')
        self.l8 = ttk.Label(self.frame1, text="N° de chasis (VIN)").grid(row=2, column=2, padx=5, pady=1, sticky='ew')
        self.l9 = ttk.Label(self.frame1, text="N° de ejes").grid(row=3, column=2, padx=5, pady=1, sticky='ew')
        self.l10 = ttk.Label(self.frame1, text="N° de motor").grid(row=4, column=2, padx=5, pady=1, sticky='ew')
        self.l11 = ttk.Label(self.frame1, text="N° de serie").grid(row=5, column=2, padx=5, pady=1, sticky='ew')
        self.l12 = ttk.Label(self.frame1, text="Año de fabricación").grid(row=6, column=2, padx=5, pady=1, sticky='ew')

        self.e7 = ttk.Entry(self.frame1, textvariable=self.v[6]).grid(row=1, column=3, padx=5, pady=1, sticky='ew')
        self.e8 = ttk.Entry(self.frame1, textvariable=self.v[7]).grid(row=2, column=3, padx=5, pady=1, sticky='ew')
        self.e9 = ttk.Entry(self.frame1, textvariable=self.v[8]).grid(row=3, column=3, padx=5, pady=1, sticky='ew')
        self.e10 = ttk.Entry(self.frame1, textvariable=self.v[9]).grid(row=4, column=3, padx=5, pady=1, sticky='ew')
        self.e11 = ttk.Entry(self.frame1, textvariable=self.v[10]).grid(row=5, column=3, padx=5, pady=1, sticky='ew')
        self.e12 = ttk.Entry(self.frame1, textvariable=self.v[11]).grid(row=6, column=3, padx=5, pady=1, sticky='ew')


        self.l13 = ttk.Label(self.frame1, text="Color").grid(row=1, column=4, padx=5, pady=1, sticky='ew')
        self.l14 = ttk.Label(self.frame1, text="Combustible").grid(row=2, column=4, padx=5, pady=1, sticky='ew')
        self.l15 = ttk.Label(self.frame1, text="Transmisión").grid(row=3, column=4, padx=5, pady=1, sticky='ew')
        self.l16 = ttk.Label(self.frame1, text="Cilindrada").grid(row=4, column=4, padx=5, pady=1, sticky='ew')
        self.l17 = ttk.Label(self.frame1, text="Kilometraje").grid(row=5, column=4, padx=5, pady=1, sticky='ew')
        self.l18 = ttk.Label(self.frame1, text="N° de tarjeta de\nidentificación vehícular").grid(row=6, column=4, padx=5, pady=1, sticky='ew')

        self.e13 = ttk.Entry(self.frame1, textvariable=self.v[12]).grid(row=1, column=5, padx=5, pady=1, sticky='ew')
        self.e14 = ttk.Entry(self.frame1, textvariable=self.v[13]).grid(row=2, column=5, padx=5, pady=1, sticky='ew')
        self.e15 = ttk.Entry(self.frame1, textvariable=self.v[14]).grid(row=3, column=5, padx=5, pady=1, sticky='ew')
        self.e16 = ttk.Entry(self.frame1, textvariable=self.v[15]).grid(row=4, column=5, padx=5, pady=1, sticky='ew')
        self.e17 = ttk.Entry(self.frame1, textvariable=self.v[16]).grid(row=5, column=5, padx=5, pady=1, sticky='ew')
        self.e18 = ttk.Entry(self.frame1, textvariable=self.v[17]).grid(row=6, column=5, padx=5, pady=1, sticky='ew')

        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblCri = ttk.Label(self.frame1, text="Criterio").grid(row=7, column=0, padx=5, pady=1, sticky='ew')
            
            # Entrys
        etrCrit = ttk.Entry(self.frame1, textvariable=self.camp).grid(row=7, column=2, padx=5, pady=1, sticky='ew')
                # Buttons
        btnCrit = ttk.Button(self.frame1, text="Buscar", command=lambda:self.filtrar()).grid(row=7, column=3, padx=5, pady=1, sticky='ew')

        btnDesf = ttk.Button(self.frame1, text="...", width=3, command=lambda:self.mostra_datos()).grid(row=7, column=4, padx=5, pady=1, sticky='w')

    def generar_ficha(self):
        try:
            file_path = filedialog.askdirectory(initialdir='report_actas/fichas_vehiculares/')
            if file_path:
                iniciar_reporte(self.codi.get(), file_path)
                mb.showinfo(message="La Ficha se gereró con exito", title='Acontar S.A.C.')
                self.focus_set()
        except Exception as e:
            print(str(e))
            mb.showerror(message=f"Ocurrió un error al generar la ficha, Error {str(e)}", title='¡Atención!')
            self.focus_set()

    def actualizar(self):
        data = []        
        for i in range(18):
            data.append(self.v[i].get())
        actualizar_vehiculo(self.codi.get(), data)
        for item in self.tree.get_children():
                self.tree.delete(item)

        r = rep_vehiculos()
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def buscar_codigo(self, buscar):
        k = selec_vehiculos_tab1(buscar)
        # print(k)
        for i in range(18):
            self.v[i].set(k[0][i])

    def tree_view(self):
            ttk.Style().configure('Treeview.Heading', font=('Arial', 10), padding=(5, 5, 5, 15))

            self.lista = ['Item', 'Cod\nInterno', 'Acta', 'Ubicación','Entidad', 'Cod\nPatrimonial', 'Denominación', 'Nro de Placa', 'Carroceria', 'Marca',
                'Modelo', 'Categoria', 'Nro Chasis', 'Nro de Ejes', 'Nro de Motor', 'Nro de Serie', 'Año\nFabricación',
                'Color', 'Combustible', 'Transmición', 'Cilindrada', 'Kilometraje', 'Nro de tarjeta\nVehicular']
            self.cbxCri = ttk.Combobox(self.frame1, textvariable=self.crit, values=self.lista, state="readonly").grid(row=7, column=1, padx=5, pady=1, sticky='ew')
            cab = []
            for i in range(1, int(len(self.lista)+1)):
                cab.append(i)

            self.tree = ttk.Treeview(self.frame2, height=25, columns=cab, show='headings')

            for i, header in enumerate(self.lista):
                self.tree.heading(i+1, text=header, anchor='center')
                self.tree.column(i+1, width=100, stretch=False)
            
            self.tree.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
            scrollbarV = ttk.Scrollbar(self.frame2, orient=tk.VERTICAL, command=self.tree.yview)
            scrollbarH = ttk.Scrollbar(self.frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
            self.tree.configure(yscroll=scrollbarV.set)
            self.tree.configure(xscroll=scrollbarH.set)
            scrollbarV.grid(column=1, row=0, sticky='ns')
            scrollbarH.grid(column=0, row=1, sticky='ew')
    
    def mostra_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = rep_vehiculos()
        for cell, contact in enumerate(r, 1):
            b = list(contact)
            b.insert(0, str(cell))
            self.tree.insert('', tk.END, values=b)

    def tab2_(self):
        self.frameU = tk.Frame(self.tab2, bg="black")
        self.frameU.pack(fill='both', expand=True)

        self.frame1 = tk.Frame(self.frameU, bg='red')
        self.frame1.pack(fill='x', side='top')

        self.frame2 = tk.Frame(self.frameU, bg='blue')
        self.frame2.pack(fill='both', side='bottom', expand=True)
        
        self.frame2.rowconfigure(0, weight=1)
        self.frame2.columnconfigure(0, weight=1)

        self.widgets_tab2()

    def widgets_tab2(self):
        var = tk.StringVar()

        lbl00 = ttk.Label(self.frame1, text="Código Patrimonial o interno").grid(row=0, column=0, padx=1, pady=3, sticky='ew')
        etr00 = ttk.Entry(self.frame1, textvariable=var).grid(row=0, column=1, padx=1, pady=3, sticky='ew')
        btn00 = ttk.Button(self.frame1,text='Buscar', command=lambda:mostrar()).grid(row=0, column=2, padx=1, pady=3, sticky='ew')
        btn00 = ttk.Button(self.frame1,text='Registrar', command=lambda:registrar()).grid(row=0, column=3, padx=1, pady=3, sticky='ew')
        btn00 = ttk.Button(self.frame1,text='Actualizar').grid(row=0, column=4, padx=1, pady=3, sticky='ew')
        
        canvas = tk.Canvas(self.frame2)
        canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(self.frame2, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        canvas.config(yscrollcommand=scrollbar.set)

        inner_frame = tk.Frame(canvas, bg='white')
        inner_frame.pack(fill='both', expand=True)
        inner_frame.rowconfigure(0, weight=1)
        inner_frame.columnconfigure(0, weight=1)

        canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        canvas.config(scrollregion=canvas.bbox('all'), bg='white')
        
        # Crear los widgets
        lbl01 = ttk.Label(inner_frame, text='1. SISTEMA DE MOTOR\n-Cilindros, -Carburador/carter, -Distribuidor/bomba de inyección, -Bomba de gasolina\n-Purificador de aire')
        lbl02 = ttk.Label(inner_frame, text='2. SISTEMA DE FRENOS\n-Bomba de frenos, -Zapatas y tambores, -Discos y pastillas')
        lbl03 = ttk.Label(inner_frame, text='3. SISTEMA DE REFRIGERACIÓN\nRadiador Ventilador Bomba de agua')
        lbl04 = ttk.Label(inner_frame, text='4. SISTEMA ELÉCTRICO\n-Motor de arranque -Bateria, -Alternador, -Bobina, -Relay de alternador, -Faros delanteros\n-Direcionales delanteros, -Luces posteriores, -Direcionales posteriores, -Auto radio\n-Parlantes, -Claxon, -Circuito de luces (faros, cableados)')
        lbl05 = ttk.Label(inner_frame, text='5. SISTEMA DE TRANSMICIÓN\n-Caja de cambios, -Bomba de embrague, -Caja de transferencia, -Diferencial trasero\n-Diferencial delantero(4x4)')
        lbl06 = ttk.Label(inner_frame, text='6. SISTEMA DE DIRECCIÓN\n-Volante, -Caña de dirección, -Cremallera, -Rótulas')
        
        txt01 = tk.Text(inner_frame, height=6, width=40)
        txt02 = tk.Text(inner_frame, height=6, width=40)
        txt03 = tk.Text(inner_frame, height=6, width=40)
        txt04 = tk.Text(inner_frame, height=6, width=40)
        txt05 = tk.Text(inner_frame, height=6, width=40)
        txt06 = tk.Text(inner_frame, height=6, width=40)

        lbl07 = ttk.Label(inner_frame, text='7. SISTEMA DE SUSPENSIÓN\nAmortiguadores/muelles, -Barra de torsión, -Barra estabilizadora, -Llantas')
        lbl08 = ttk.Label(inner_frame, text='8. CARROCERÍA\n-Capot del motor, -Capot de maletera, -Parachoques delantero, -Parachoques posterior\n-Lunas laterales, -Lunas cortaviento, -Parabrisas delantero, -Parabrisas posterior\n-Tanque de combustible, -Puertas, -Asientos')
        lbl09 = ttk.Label(inner_frame, text='9. ACCESORIOS\n-Aire acondicionado, -Alarma, -Plumillas, -Espejos, -Cinturones de seguridad, -Antena')
        lbl10 = ttk.Label(inner_frame, text='10. OTRAS CARACTERÍSTICAS RELEVANTES\n')
        lbl11 = ttk.Label(inner_frame, text='11. APRECIACIÓN TÉCNICA GENERAL\n')
        
        txt07 = tk.Text(inner_frame, height=6, width=40)
        txt08 = tk.Text(inner_frame, height=6, width=40)
        txt09 = tk.Text(inner_frame, height=6, width=40)
        txt10 = tk.Text(inner_frame, height=6, width=40)
        txt11 = tk.Text(inner_frame, height=6, width=40)

        # Posicionar los widgets en la cuadrícula
        lbl01.grid(row=0, column=0, sticky='ew')
        txt01.grid(row=1, column=0, padx=10, sticky='ew')
        lbl03.grid(row=2, column=0, sticky='ew')
        txt03.grid(row=3, column=0, padx=10, sticky='ew')
        lbl05.grid(row=4, column=0, sticky='ew')
        txt05.grid(row=5, column=0, padx=10, sticky='ew')
        lbl07.grid(row=6, column=0, sticky='ew')
        txt07.grid(row=7, column=0, padx=10, sticky='ew')
        lbl09.grid(row=8, column=0, sticky='ew')
        txt09.grid(row=9, column=0, padx=10, sticky='ew')
        lbl11.grid(row=10, column=0, sticky='ew')
        txt11.grid(row=11, column=0, padx=10, sticky='ew')


        lbl02.grid(row=0, column=2, sticky='ew')
        txt02.grid(row=1, column=2, padx=10, sticky='ew')
        lbl04.grid(row=2, column=2, sticky='ew')
        txt04.grid(row=3, column=2, padx=10, sticky='ew')
        lbl06.grid(row=4, column=2, sticky='ew')
        txt06.grid(row=5, column=2, padx=10, sticky='ew')
        lbl08.grid(row=6, column=2, sticky='ew')
        txt08.grid(row=7, column=2, padx=10, sticky='ew')
        lbl10.grid(row=8, column=2, sticky='ew')
        txt10.grid(row=9, column=2, padx=10, sticky='ew')
        
        
        texts01 = [txt01, txt03, txt05, txt07, txt09, txt11]

        for i, text in enumerate(texts01):
            row = i * 2 + 1
            scroll = ttk.Scrollbar(inner_frame, command=text.yview)
            scroll.grid(row=row, column=1, sticky='ns')
            text.configure(yscrollcommand=scroll.set, font=('Arial', 9), bg='white', relief='solid')

        texts02 = [txt02, txt04, txt06, txt08, txt10]

        for i, text in enumerate(texts02):
            row = i * 2 + 1
            scroll = ttk.Scrollbar(inner_frame, command=text.yview)
            scroll.grid(row=row, column=3, sticky='ns')
            text.configure(yscrollcommand=scroll.set, font=('Arial', 9), bg='white', relief='solid')
        # self.txtNota.configure(font=('Arial', 9), bg='white', relief='solid')
        
        inner_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        # inner_frame.pack(fill='both', expand=True)

        
        def registrar():
            try:
                var01 = txt01.get('1.0', 'end')
                var02 = txt02.get('1.0', 'end')
                var03 = txt03.get('1.0', 'end')
                var04 = txt04.get('1.0', 'end')
                var05 = txt05.get('1.0', 'end')
                var06 = txt06.get('1.0', 'end')
                var07 = txt07.get('1.0', 'end')
                var08 = txt08.get('1.0', 'end')
                var09 = txt09.get('1.0', 'end')
                var10 = txt10.get('1.0', 'end')
                var11 = txt11.get('1.0', 'end')

                data = [var01, var02, var03, var04, var05, var06, var07, var08, var09, var10, var11]
                # print(var.get())
                registrar_vehiculo(var.get(), data)
                mb.showinfo(message='Se registro correctamente', title='Acontar S.A.C.')
                self.focus_set()
            except Exception as e:
                mb.showerror(message=f'Error al registrar, Error {str(e)}')
                self.focus_set()
                print(e)

        def mostrar():
            j = selec_vehiculos(var.get())
            # print(j)

            widgets = [txt01, txt02, txt03, txt04, txt05, txt06, txt07, txt08, txt09, txt10, txt11]
            datos = j[0]
            for widget, dato in zip(widgets, datos):
                widget.delete('1.0', 'end')
                widget.insert('end', dato)

    def mostrar_datos_(self, *args):
        fila = self.tree.focus()
        vnb = self.tree.item(fila)['values']
        self.j = vnb[1]
        self.codi.set(self.j)
        self.buscar_codigo(self.j)

    def mostrar_detalles_(self):
        fila = self.tree.focus()
        vnb = self.tree.item(fila)['values']
        self.j = vnb[1]
        self.codi.set(self.j)
        self.buscar_codigo(self.j)
        ventana = Window_detalles(codigo=self.j)
        ventana.wait_window(ventana)
        self.focus_set()
        self.after(0, self.mostra_datos())

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