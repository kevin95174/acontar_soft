import tkinter as tk
from tkinter import ttk
from db.query import mostrar_catalogo, mostrar_catalogo_criterio

class Window_fvehiculo(tk.Toplevel):
    def __init__(self, root=None):
        super().__init__(root)
    
        self.title("Acontar Especialistas Contables  AEC S.A.C.")
        self.iconbitmap('./img/favicon.ico')
        self.grab_set()
        self.focus_set()

        self.Frame1 = tk.Frame(self, bg='white', bd=12)
        self.Frame1.pack(fill='both', side='top')

        self.Frame2 = tk.Frame(self, bg='#e30613')
        self.Frame2.rowconfigure(0, weight=1)
        self.Frame2.columnconfigure(0, weight=1)
        self.Frame2.pack(fill="both", expand=True, side='bottom')
        self.widget_frame2()

    def iniciar_filtro(self):
        r = mostrar_catalogo()
        for i in r:
            self.tree.insert('', tk.END, values=i)

    def widget_frame1(self):
        self.crit = tk.StringVar()
        self.busc = tk.StringVar()

        self.l1 = ttk.Label(self.Frame1, text="Entidad").grid(row=0, column=0, padx=1, pady=1, sticky="ew")
        self.l2 = ttk.Label(self.Frame1, text="Denominación").grid(row=1, column=0, padx=1, pady=1, sticky="ew")
        self.l3 = ttk.Label(self.Frame1, text="N° Placa vehícular").grid(row=2, column=0, padx=1, pady=1, sticky="ew")
        self.l4 = ttk.Label(self.Frame1, text="Carroceria").grid(row=3, column=0, padx=1, pady=1, sticky="ew")
        self.l5 = ttk.Label(self.Frame1, text="Marca").grid(row=4, column=0, padx=1, pady=1, sticky="ew")
        self.l6 = ttk.Label(self.Frame1, text="Modelo").grid(row=5, column=0, padx=1, pady=1, sticky="ew")

        self.e1 = ttk.Entry(self.Frame1).grid(row=0, column=1, padx=1, pady=1, sticky="ew")
        self.e2 = ttk.Entry(self.Frame1).grid(row=1, column=1, padx=1, pady=1, sticky="ew")
        self.e3 = ttk.Entry(self.Frame1).grid(row=2, column=1, padx=1, pady=1, sticky="ew")
        self.e4 = ttk.Entry(self.Frame1).grid(row=3, column=1, padx=1, pady=1, sticky="ew")
        self.e5 = ttk.Entry(self.Frame1).grid(row=4, column=1, padx=1, pady=1, sticky="ew")
        self.e6 = ttk.Entry(self.Frame1).grid(row=5, column=1, padx=1, pady=1, sticky="ew")


        self.l7 = ttk.Label(self.Frame1, text="Categoria").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.l8 = ttk.Label(self.Frame1, text="N° de chasis (VIN)").grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        self.l9 = ttk.Label(self.Frame1, text="N° de ejes").grid(row=2, column=2, padx=5, pady=5, sticky="ew")
        self.l10 = ttk.Label(self.Frame1, text="N° de motor").grid(row=3, column=2, padx=5, pady=5, sticky="ew")
        self.l11 = ttk.Label(self.Frame1, text="N° de serie").grid(row=4, column=2, padx=5, pady=5, sticky="ew")
        self.l12 = ttk.Label(self.Frame1, text="Año de fabricación").grid(row=5, column=2, padx=5, pady=5, sticky="ew")

        self.e7 = ttk.Entry(self.Frame1).grid(row=0, column=3, padx=5, pady=1, sticky="ew")
        self.e8 = ttk.Entry(self.Frame1).grid(row=1, column=3, padx=5, pady=1, sticky="ew")
        self.e9 = ttk.Entry(self.Frame1).grid(row=2, column=3, padx=5, pady=1, sticky="ew")
        self.e10 = ttk.Entry(self.Frame1).grid(row=3, column=3, padx=5, pady=1, sticky="ew")
        self.e11 = ttk.Entry(self.Frame1).grid(row=4, column=3, padx=5, pady=1, sticky="ew")
        self.e12 = ttk.Entry(self.Frame1).grid(row=5, column=3, padx=5, pady=1, sticky="ew")


        self.l13 = ttk.Label(self.Frame1, text="Color").grid(row=0, column=4, padx=5, pady=1, sticky="ew")
        self.l14 = ttk.Label(self.Frame1, text="Combustible").grid(row=1, column=4, padx=5, pady=1, sticky="ew")
        self.l15 = ttk.Label(self.Frame1, text="Transmisión").grid(row=2, column=4, padx=5, pady=1, sticky="ew")
        self.l16 = ttk.Label(self.Frame1, text="Cilindrada").grid(row=3, column=4, padx=5, pady=1, sticky="ew")
        self.l17 = ttk.Label(self.Frame1, text="Kilometraje").grid(row=4, column=4, padx=5, pady=1, sticky="ew")
        self.l18 = ttk.Label(self.Frame1, text="N° de tarjeta de\nidentificación vehícular").grid(row=5, column=4, padx=5, pady=1, sticky="ew")

        self.e13 = ttk.Entry(self.Frame1).grid(row=0, column=5, padx=5, pady=1, sticky="ew")
        self.e14 = ttk.Entry(self.Frame1).grid(row=1, column=5, padx=5, pady=1, sticky="ew")
        self.e15 = ttk.Entry(self.Frame1).grid(row=2, column=5, padx=5, pady=1, sticky="ew")
        self.e16 = ttk.Entry(self.Frame1).grid(row=3, column=5, padx=5, pady=1, sticky="ew")
        self.e17 = ttk.Entry(self.Frame1).grid(row=4, column=5, padx=5, pady=1, sticky="ew")
        self.e18 = ttk.Entry(self.Frame1).grid(row=5, column=5, padx=5, pady=1, sticky="ew")

    def widget_frame2(self):
        # self.Drame2.columnconfigure(0, weight=1)

        # self.Frame2 = tk.Frame(self.Frame2)
        # self.Frame2.pack(fill="both", expand=True, side='left')

        # Crear un canvas para contener el frame
        canvas = tk.Canvas(self.Frame2)
        canvas.grid(row=0, column=0, sticky="nsew")

        # Crear un scrollbar para el canvas
        scrollbar = tk.Scrollbar(self.Frame2, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configurar la vinculación entre el scrollbar y el canvas
        canvas.config(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        # Crear un nuevo frame dentro del canvas
        inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        lblVal = ttk.Label(inner_frame, text="Valor de tasación (S/) o valor neto (S/)").grid(row=0, column=0, pady=0, sticky='w')
        lblDes = ttk.Label(inner_frame, text="DESCRIPCIÓN").grid(row=1, column=0, pady=0, sticky='w')
        lbl000 = ttk.Label(inner_frame, text="1. SISTEMA DE MOTOR").grid(row=2, column=0, pady=0, sticky='w')
        lbl001 = ttk.Label(inner_frame, text="Cilindros").grid(row=3, column=0, pady=0, sticky='w')
        lbl002 = ttk.Label(inner_frame, text="Carburador / carter").grid(row=4, column=0, pady=0, sticky='w')
        lbl003 = ttk.Label(inner_frame, text="Distribuidor / bomba de inyección").grid(row=5, column=0, pady=0, sticky='w')
        lbl004 = ttk.Label(inner_frame, text="Bomba de gasolina").grid(row=6, column=0, pady=0, sticky='w')
        lbl005 = ttk.Label(inner_frame, text="Purificador de aire").grid(row=7, column=0, pady=0, sticky='w')

        lbl006 = ttk.Label(inner_frame, text="2. SISTEMA DE FRENOS").grid(row=8, column=0, pady=0, sticky='w')
        lbl007 = ttk.Label(inner_frame, text="Bomba de frenos").grid(row=9, column=0, pady=0, sticky='w')
        lbl008 = ttk.Label(inner_frame, text="Zapatas y tambores").grid(row=10, column=0, pady=0, sticky='w')
        lbl009 = ttk.Label(inner_frame, text="Discos y pastillas").grid(row=11, column=0, pady=0, sticky='w')

        lbl010 = ttk.Label(inner_frame, text="3. SISTEMA DE REFRIGERACIÓN").grid(row=12, column=0, pady=0, sticky='w')
        lbl011 = ttk.Label(inner_frame, text="Radiador").grid(row=13, column=0, pady=0, sticky='w')
        lbl012 = ttk.Label(inner_frame, text="Ventilador").grid(row=14, column=0, pady=0, sticky='w')
        lbl013 = ttk.Label(inner_frame, text="Bomba de agua").grid(row=15, column=0, pady=0, sticky='w')
        
        lbl014 = ttk.Label(inner_frame, text="4. SISTEMA ELÉCTRICO").grid(row=16, column=0, pady=0, sticky='w')
        lbl015 = ttk.Label(inner_frame, text="Motor de arranque").grid(row=17, column=0, pady=0, sticky='w')
        lbl016 = ttk.Label(inner_frame, text="Bateria").grid(row=18, column=0, pady=0, sticky='w')
        lbl017 = ttk.Label(inner_frame, text="Alternador").grid(row=19, column=0, pady=0, sticky='w')
        lbl018 = ttk.Label(inner_frame, text="Bobina").grid(row=20, column=0, pady=0, sticky='w')
        lbl019 = ttk.Label(inner_frame, text="Relay de alternador").grid(row=21, column=0, pady=0, sticky='w')
        lbl020 = ttk.Label(inner_frame, text="Faros delanteros").grid(row=22, column=0, pady=0, sticky='w')
        lbl021 = ttk.Label(inner_frame, text="Direccionales delanteros").grid(row=23, column=0, pady=0, sticky='w')
        lbl022 = ttk.Label(inner_frame, text="Luces posteriores").grid(row=24, column=0, pady=0, sticky='w')
        lbl023 = ttk.Label(inner_frame, text="Direccionales posteriores").grid(row=25, column=0, pady=0, sticky='w')
        lbl024 = ttk.Label(inner_frame, text="Auto radio").grid(row=26, column=0, pady=0, sticky='w')
        lbl025 = ttk.Label(inner_frame, text="Parlantes").grid(row=27, column=0, pady=0, sticky='w')
        lbl026 = ttk.Label(inner_frame, text="Claxon").grid(row=28, column=0, pady=0, sticky='w')
        lbl027 = ttk.Label(inner_frame, text="Circuito de luces (faros, cableados)").grid(row=29, column=0, pady=0, sticky='w')
        
        lbl028 = ttk.Label(inner_frame, text="5. SISTEMA DE TRANSMICIÓN").grid(row=30, column=0, pady=0, sticky='w')
        lbl029 = ttk.Label(inner_frame, text="Caja de cambios").grid(row=31, column=0, pady=0, sticky='w')
        lbl030 = ttk.Label(inner_frame, text="Bomba de embrague").grid(row=32, column=0, pady=0, sticky='w')
        lbl031 = ttk.Label(inner_frame, text="Caja de transferencia").grid(row=33, column=0, pady=0, sticky='w')
        lbl032 = ttk.Label(inner_frame, text="Diferencial trasero").grid(row=34, column=0, pady=0, sticky='w')
        lbl033 = ttk.Label(inner_frame, text="Diferencial delantero (4x4)").grid(row=35, column=0, pady=0, sticky='w')

        lbl034 = ttk.Label(inner_frame, text="6. SISTEMA DE DIRECCIÓN").grid(row=36, column=0, pady=0, sticky='w')
        lbl035 = ttk.Label(inner_frame, text="Volante").grid(row=37, column=0, pady=0, sticky='w')
        lbl036 = ttk.Label(inner_frame, text="Caña de dirección").grid(row=38, column=0, pady=0, sticky='w')
        lbl037 = ttk.Label(inner_frame, text="Cremallera").grid(row=39, column=0, pady=0, sticky='w')
        lbl038 = ttk.Label(inner_frame, text="Rótulas").grid(row=40, column=0, pady=0, sticky='w')
        
        lbl039 = ttk.Label(inner_frame, text="7. SISTEMA DE SUSPENCIÓN").grid(row=41, column=0, pady=0, sticky='w')
        lbl040 = ttk.Label(inner_frame, text="Amortiguadores / muelles").grid(row=42, column=0, pady=0, sticky='w')
        lbl041 = ttk.Label(inner_frame, text="Barra de torsión").grid(row=43, column=0, pady=0, sticky='w')
        lbl042 = ttk.Label(inner_frame, text="Barra estabilizadora").grid(row=44, column=0, pady=0, sticky='w')
        lbl043 = ttk.Label(inner_frame, text="Llantas").grid(row=45, column=0, pady=0, sticky='w')


        # inner_frame = tk.Frame(inner_frame)
        # inner_frame.pack(fill="both", expand=True, side='right')
        etrVal = ttk.Entry(inner_frame).grid(row=0, column=1)
        lblApr = ttk.Label(inner_frame, text="APRECIACIÓN TÉCNICA DEL SISTEMA").grid(row=1, column=1)
        # 1 Motor
        lble00 = ttk.Label(inner_frame, text="").grid(row=2, column=1)
        txt001 = tk.Text(inner_frame, height=2, width=1).grid(row=3, column=1, rowspan=5, sticky="ew")
        # 2 Frenos
        lble01 = ttk.Label(inner_frame, text="").grid(row=8, column=1)
        txt002 = tk.Text(inner_frame, height=2, width=1).grid(row=9, column=1, rowspan=3, sticky="ew")
        # 3 Refrigeracion
        lble03 = ttk.Label(inner_frame, text="").grid(row=12, column=1)
        txt003 = tk.Text(inner_frame, height=2, width=1).grid(row=13, column=1, rowspan=3, sticky="ew")
        # 4 Electrico
        lble04 = ttk.Label(inner_frame, text="").grid(row=15, column=1)
        txt004 = tk.Text(inner_frame, height=2, width=1).grid(row=16, column=1, rowspan=13, sticky="ew")
        # 5 Transmicion
        lble03 = ttk.Label(inner_frame, text="").grid(row=30, column=1)
        txt003 = tk.Text(inner_frame, height=2, width=1).grid(row=31, column=1, rowspan=5, sticky="ew")
        # 6 Direccion
        lble03 = ttk.Label(inner_frame, text="").grid(row=36, column=1)
        txt003 = tk.Text(inner_frame, height=2, width=1).grid(row=37, column=1, rowspan=4)
        # 7 Suspencion
        lble03 = ttk.Label(inner_frame, text="").grid(row=41, column=1)
        txt003 = tk.Text(inner_frame, height=2, width=1).grid(row=42, column=1, rowspan=4)

        inner_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
    def buscar_criterio(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        r = mostrar_catalogo_criterio(self.crit.get(), self.busc.get())
        for i in r:
            self.tree.insert('', tk.END, values=i)

    def treeview(self):
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5,5,5,15))
        cab = (1, 2, 3, 4,5, 6, 7, 8)
        self.tree = ttk.Treeview(self.Frame2, height=25, columns=cab, show='headings')     
        self.tree.heading(1, text='Item', anchor="center")
        self.tree.heading(2, text='Código')
        self.tree.heading(3, text='Denominación (familia)')
        self.tree.heading(4, text='Unidad')
        self.tree.heading(5, text='Grupo')
        self.tree.heading(6, text='Clase')
        self.tree.heading(7, text='Resolucion')
        self.tree.heading(8, text='Estado')

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
