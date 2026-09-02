import csv
import tkinter as tk
from tkinter import ttk, Menu, PhotoImage
from tkinter import messagebox as mb
from db.query import mostrar_datos, mostrar_d_personal, query_codpat, total_bienes, mostrar_datos_test, val_codigo
from db.query import registrar_codpat_test, total_bienes_f, buscar_bien, actualizar_registro, registrar_codint_test
from db.query import actualizar_detalles, mostrar_datos_criterio, mostrar_inventario, mostrar_datos_criterio_val1
from db.query import total_bienes_s
from datetime import datetime, date
from utils.order_utils import sort_by
from reportes.ficha import iniciar_reporte
from gui.gui_sobrante import Window_surplus
from gui.gui_config import Window_config
from gui.gui_personal import Window_personal
from gui.gui_buscar import Window_buscar
from gui.gui_detalle import Window_detalle
from gui.gui_print import Window_print
from gui.gui_imp_exp import Window_inv
from gui.gui_catalogo import Window_catalogo
from gui.gui_detalles import Window_detalles
from gui.gui_vehiculos import Window_vehiculos
from gui.gui_analisis import Window_analisis
from gui.gui_reporte import Window_reporte
from gui.gui_ficha import Window_Acta
from label.label_gen import build_label
from label.label_no_cat import build_label_nc
from funciones.scanner_cam import Window_scanner
from funciones.socket import Window_server

class Frame(ttk.Frame):
    
    def __init__(self, root=None, user=None, Ndni=None, team=None):
        super().__init__(root)
        self.root = root
        self.user = user
        self.Ndni = Ndni
        self.team = team
        self.pack(fill='both', expand=True)
        self.crear_menu()
        self.iconoBuscar = PhotoImage(file='img/lupa.png')
        self.iconoRegistrar = PhotoImage(file='img/registrar.png')		
        
        s = ttk.Style()

        s.configure('Frame1.TFrame', background='green')
        s.configure('Frame2.TFrame', background='#ffffff')
        s.configure('Frame3.TFrame', background='#e30613')
        s.configure('TLabel', background='#ffffff', foreground='black', font=('Helvetica', 10))
        s.configure('TButton', background='#ffffff', font=('Helvetica', 10))
        s.configure('White.TCheckbutton', background='white')

        self.style='Frame1.TFrame'

        self.variables()
        self.frame_datos()
        self.frame_tree()
        self.frame_botton()
        self.widgets_buscar()
        # self.etrCodpat.bind("<Return>", self.registrar(self.valor.get(), self.id.get()))
        self.etrCodpat.bind("<Return>", lambda event: self.registrar(self.valor.get(), self.id.get()))

        try:
            self.tree.bind("<Double-Button-1>", self.mostrar_datos_)
        except:
            pass		

    def variables(self):
        self.valor = tk.StringVar()
        self.id = tk.StringVar()
        self.local = tk.StringVar()
        self.area = tk.StringVar()
        self.oficina = tk.StringVar()
        self.resp = tk.StringVar()
        self.dni = tk.StringVar()
        self.totalb = tk.IntVar()
        self.totals = tk.IntVar()
        self.totalF = tk.IntVar()
        self.narch = tk.StringVar()
        self.cb = tk.IntVar()
        self.ba = tk.IntVar()

        self.codi = tk.StringVar()
        self.deno = tk.StringVar()
        self.inve = tk.StringVar()
        self.codp = tk.StringVar()
        self.acta = tk.StringVar()
        self.marc = tk.StringVar()
        self.seri = tk.StringVar()
        self.fech = tk.StringVar()
        self.dadq = tk.StringVar()
        self.mode = tk.StringVar()
        self.colo = tk.StringVar()			
        self.aact = tk.StringVar()
        self.esta = tk.StringVar()
        self.dime = tk.StringVar()
        self.obse = tk.StringVar()
        
        self.otro = tk.StringVar()
        self.situ = tk.StringVar()
        self.tipo = tk.StringVar()

    def frame_datos(self):
        # Labels
        self.frame1 = ttk.Frame(self, style='Frame2.TFrame')
        self.frame1.pack(side='top', fill='x')

        self.frame1_1 = ttk.Frame(self.frame1, style='Frame2.TFrame')
        self.frame1_1.pack(side='left')

        self.lblActa = ttk.Label(self.frame1_1, text="Nro de Acta", font=("bold")).grid(column=0, row=0, padx=5, pady=1,sticky="ew")
        self.lblLocal = ttk.Label(self.frame1_1, text="Local", borderwidth="2").grid(column=0, row=1, padx=5, pady=1, sticky="ew")
        self.lblArea = ttk.Label(self.frame1_1, text="Área").grid(column=0, row=2, padx=5, pady=1, sticky="ew")
        self.lblOficina = ttk.Label(self.frame1_1, text="Oficina").grid(column=0, row=3, padx=5, pady=1, sticky="ew")
        self.lblResp = ttk.Label(self.frame1_1, text="Responsable").grid(column=4, row=1, padx=5, pady=1, sticky="ew")
        self.lblDni = ttk.Label(self.frame1_1, text="DNI").grid(column=4, row=2, padx=5, pady=1, sticky="ew")
        self.lblCodpat = ttk.Label(self.frame1_1, text="Código patrimonial\nInterno").grid(column=0, row=4, padx=5, pady=1, sticky="ew")

        # Entrys
        self.etrnActa = ttk.Entry(self.frame1_1, textvariable= self.valor, width=7, justify="center")
        self.etrnActa.grid(column=1, row=0, padx=5, pady=1, sticky="ew")
        self.etrLocal = ttk.Entry(self.frame1_1, textvariable= self.local, state='readonly').grid(column=1, row=1, columnspan=3,padx=5, pady=1, sticky="ew")
        self.etrArea = ttk.Entry(self.frame1_1, textvariable= self.area, state='readonly').grid(column=1, row=2, columnspan=3, padx=5, pady=1, sticky="ew")
        self.etrOficina = ttk.Entry(self.frame1_1, textvariable= self.oficina, state='readonly').grid(column=1, columnspan=3,row=3, padx=5, pady=1, sticky="ew")
        self.etrResp = ttk.Entry(self.frame1_1, textvariable= self.resp, state='readonly').grid(column=5, row=1, padx=5, pady=1, sticky="ew")
        self.etrDni = ttk.Entry(self.frame1_1, textvariable= self.dni, state='readonly').grid(column=5, row=2, padx=5, pady=1, sticky="ew")
        self.etrCodpat = ttk.Entry(self.frame1_1, textvariable= self.id)
        self.etrCodpat.grid(column=1, row=4, columnspan=3,padx=5, pady=10, sticky="ew")

        # Buttons
        self.btnbuscar = ttk.Button(self.frame1_1, text="Buscar", width=10, command=lambda:self.iniciar_filtro(), image=self.iconoBuscar, compound='left').grid(column=2, row=0, sticky="ew")
        # self.btnpuntos = ttk.Button(self.frame1_1, text="...", width=3, command=lambda:self.window_escanner(self)).grid(column=3, row=0, sticky="w")
        self.btnreg = ttk.Button(self.frame1_1, text="Registrar", width=8, command=lambda:self.registrar(self.valor.get(), self.id.get()), image=self.iconoRegistrar, compound='left').grid(column=4, row=4, padx=3, pady=1, sticky="ew")
        # self.btnacta = ttk.Button(self.frame1_1, text="Acta", width=8).grid(column=5, row=4, padx=3, pady=2, sticky="ew")
        
        # checkButton
        self.checkBar = ttk.Checkbutton(self.frame1_1, text='Inventario al Barrer', variable=self.ba, onvalue=1, offvalue=0, style='White.TCheckbutton').grid(column=5, row=3, sticky='sew')
        self.checkImp = ttk.Checkbutton(self.frame1_1, text='Imprimir Etiquetas', variable=self.cb, onvalue=1, offvalue=0, style='White.TCheckbutton').grid(column=5, row=4, sticky='ew')

        self.crit = tk.StringVar()
        self.camp = tk.StringVar()

        lblCri = ttk.Label(self.frame1_1, text="Criterio").grid(row=5, column=0, padx=5, pady=1, sticky="ew")
                
            # Combobox
        cbxCri = ttk.Combobox(self.frame1_1, textvariable=self.crit, state="readonly", 
        values=['CodInt', 'CodPat', 'DenBien', 'ActaAnt', 'Estado', 'Dimension', 'Marca', 'Modelo',
                'Serie', 'Color', 'ValAdq', 'Obs', 'Otros', 'Situacion', 'FechInv', 'Inventariador', 'Equipo']).grid(row=5, column=1, columnspan=3, padx=5, pady=1, sticky="ew")

            # Entrys
        etrCrit = ttk.Entry(self.frame1_1, textvariable=self.camp).grid(row=5, column=4, padx=5, pady=1, sticky="ew")
                # Buttons
        btnCrit = ttk.Button(self.frame1_1, text="Buscar", command=lambda:self.buscar_criterio(), image=self.iconoBuscar, compound='left').grid(row=5, column=5, padx=5, pady=1, sticky="ew")
    
    def frame_tree(self):
        
        # Treeview
        self.frame2 = ttk.Frame(self, style='Frame3.TFrame')
        self.frame2.pack(fill='both', expand=True)
        self.frame2.rowconfigure(0, weight=1)
        self.frame2.columnconfigure(0, weight=1)
        ttk.Style().configure('Treeview.Heading',font=('Arial', 10), padding=(5, 5, 5, 15))
        cab = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23)
        self.tree = ttk.Treeview(self.frame2, height=15, columns=cab, show='headings')

        self.tree.tag_configure('normal')
        self.tree.tag_configure('fail', foreground="red")

        self.tree.heading(1, text='Item', command=lambda:sort_by(self.tree, 1, False), anchor="center")
        self.tree.heading(2, text='      Cod\nPatrimonial', command=lambda:sort_by(self.tree, 2, False), anchor="center")
        self.tree.heading(3, text='  Cod\nInterno', command=lambda:sort_by(self.tree, 3, False))
        self.tree.heading(4, text='Denominación', command=lambda:sort_by(self.tree, 4, False))
        self.tree.heading(5, text='  Acta\nAnterior', command=lambda:sort_by(self.tree, 5, False))
        self.tree.heading(6, text='Sede', command=lambda:sort_by(self.tree, 6, False))
        self.tree.heading(7, text='Área', command=lambda:sort_by(self.tree, 7, False))
        self.tree.heading(8, text='Oficina', command=lambda:sort_by(self.tree, 8, False))
        self.tree.heading(9, text='Responsable', command=lambda:sort_by(self.tree, 9, False))
        self.tree.heading(10, text='Estado', command=lambda:sort_by(self.tree, 10, False))
        self.tree.heading(11, text='Dimensión', command=lambda:sort_by(self.tree, 11, False))
        self.tree.heading(12, text='Marca', command=lambda:sort_by(self.tree, 12, False))
        self.tree.heading(13, text='Modelo', command=lambda:sort_by(self.tree, 13, False))
        self.tree.heading(14, text='Serie', command=lambda:sort_by(self.tree, 14, False))
        self.tree.heading(15, text='Color', command=lambda:sort_by(self.tree, 15, False))
        self.tree.heading(16, text='Tipo', command=lambda:sort_by(self.tree, 16, False))
        self.tree.heading(17, text='Valor', command=lambda:sort_by(self.tree, 17, False))
        self.tree.heading(18, text='Obs', command=lambda:sort_by(self.tree, 18, False))		
        self.tree.heading(19, text='Otros', command=lambda:sort_by(self.tree, 19, False))		
        self.tree.heading(20, text='Situacion', command=lambda:sort_by(self.tree, 20, False))		
        self.tree.heading(21, text='Fecha Inv', command=lambda:sort_by(self.tree, 21, False))
        self.tree.heading(22, text='Inventariador', command=lambda:sort_by(self.tree, 22, False))
        self.tree.heading(23, text='Equipo', command=lambda:sort_by(self.tree, 23, False))

        self.tree.column(1, width=50, stretch=False)
        self.tree.column(2, width=100, stretch=False, anchor="center")
        self.tree.column(3, width=70, stretch=False)
        self.tree.column(4, width=330, stretch=False)
        self.tree.column(5, width=70, stretch=False, anchor="center")
        self.tree.column(6, width=110, stretch=False)
        self.tree.column(7, width=110, stretch=False)
        self.tree.column(8, width=110, stretch=False)
        self.tree.column(9, width=235, stretch=False)
        self.tree.column(10, width=60, stretch=False, anchor="center")
        self.tree.column(11, width=90, stretch=False)
        self.tree.column(12, width=90, stretch=False)
        self.tree.column(13, width=90, stretch=False)
        self.tree.column(14, width=90, stretch=False)
        self.tree.column(15, width=90, stretch=False)
        self.tree.column(16, width=90, stretch=False)
        self.tree.column(17, width=90, stretch=False, anchor="e")
        self.tree.column(18, width=90, stretch=False)
        self.tree.column(19, width=70, stretch=False)
        self.tree.column(20, width=75, stretch=False, anchor="center")
        self.tree.column(21, width=120, stretch=False)
        self.tree.column(22, width=235, stretch=False)
        self.tree.column(23, width=60, stretch=False, anchor="center")

        self.tree.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set)
        self.tree.configure(xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def frame_botton(self):		
        self.frame3= ttk.Frame(self, style='Frame2.TFrame')
        self.frame3.pack(fill='x', expand=False)
        # self.frame3.rowconfigure(0, weight=1)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.columnconfigure(1, weight=1)
        self.frame3.columnconfigure(2, weight=1)
        self.frame3.columnconfigure(3, weight=1)
        self.frame3.columnconfigure(4, weight=1)
        self.frame3.columnconfigure(5, weight=1)
        self.frame3.columnconfigure(6, weight=1)
        self.frame3.columnconfigure(7, weight=1)
        self.frame3.columnconfigure(8, weight=1)

        # label Frame3
        self.lblTot = ttk.Label(self.frame3, text='Total Bienes').grid(row=0, column=0, sticky="w")
        self.etrTot = ttk.Entry(self.frame3, textvariable=self.totalb, width=20, justify="center").grid(row=0, column=1, sticky="w", pady=5)
        self.btnTot = ttk.Button(self.frame3, text='Detalle', command=lambda:Window_detalle(acta=self.valor.get(), valor=1, user=self.user, team=self.team)).grid(row=0, column=2, sticky="w")
        # self.lblInv = ttk.Label(self.frame3, text='Bienes Inventariados').grid(row=0, column=3, sticky="w")
        self.lblSob = ttk.Label(self.frame3, text='Bienes sobrantes').grid(row=0, column=3)
        self.etrSob = ttk.Entry(self.frame3, textvariable=self.totals, width=20, justify="center").grid(row=0, column=4, sticky="w")			
        self.btnSob = ttk.Button(self.frame3, text='Detalle', command=lambda:self.ver_sobrantes()).grid(row=0, column=5, sticky="w")
        # Entry Frame3
        self.lblFal = ttk.Label(self.frame3, text='Bienes Faltantes').grid(row=0, column=6, sticky="w")
        self.etrFal = ttk.Entry(self.frame3, textvariable=self.totalF, width=20, justify="center").grid(row=0, column=7, sticky="w")			
        self.btnFal = ttk.Button(self.frame3, text='Detalle', command=lambda:Window_detalle(self, acta=self.valor.get(), valor=2, user=self.user, team=self.team)).grid(row=0, column=8, sticky="w")

    def registrar(self, numero_ficha, codigo):
        if numero_ficha == "":
            mb.showinfo(message="Ingrese un número de Acta", title="¡Atención!")
        elif codigo == "":
            mb.showinfo(message="Ingrese un código de inventario", title="¡Atención!")
        else:
            Acta = numero_ficha
            now = datetime.now()
            F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
            data = [Acta, F_inv, self.user, self.team]
            id = codigo[0:12]
            y = len(id)
            
            if y > 5:
                r = val_codigo(id)
                if r == 1:
                    g = buscar_bien(id, 1)
                    if g[0][1] != "":
                        mb.showinfo(message=f"El Código ya ha sido registrado en el Acta {g[0][1]} - {g[0][12]}", title="¡Atención!")
                    else:
                        if str(numero_ficha) == str(g[0][2]):
                            if self.procesar_codigo(id):
                                registrar_codpat_test(id, data)
                                self.registro_co()
                                build_label(self.cb.get(), id, numero_ficha)
                        else:
                            mb.showinfo(message="¡Atención!")
                            v = mb.askyesnocancel(message=f"El código que intenta registrar ha sido inventariado anteriormente en el Acta {g[0][2]} - {g[0][12]} ¿Desea inventariarlo en el acta actual?, si presiona NO se inventariara en el acta anterior", title="¡Atención!")
                            if v == True:
                                if self.procesar_codigo(id):
                                    registrar_codpat_test(id, data)
                                    self.registro_co()
                                    build_label(self.cb.get(), id, numero_ficha)
                            elif v == False:
                                na = g[0][2]
                                now = datetime.now()
                                F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
                                data_a = [na, F_inv, self.user, self.team]
                                if self.procesar_codigo(id):
                                    registrar_codpat_test(id, data_a)
                                    build_label(self.cb.get(), id, na)
                                    mb.showinfo(message="Se registro correctamente", title="Acontar S.A.C.")
                                    self.etrCodpat.delete(0, 'end')
                            else:
                                self.etrCodpat.delete(0, 'end')
                else:
                    mb.showinfo(message="EL código no existe", title="¡Atención!")
                    self.etrCodpat.focus()
                    self.etrCodpat.delete(0, 'end')
            else:
                r = val_codigo(id)
                if r == 1:
                    qcp = query_codpat(id)
                    cp = qcp[0][0]
                    if cp == "NO CATALOGADO":
                        g = buscar_bien(id, 1)
                        if g[0][1] != "":
                            mb.showinfo(message=f"El Código ya ha sido registrado en el Acta {g[0][1]} - {g[0][12]}", title="¡Atención!")
                        else:
                            detalle_window = Window_detalles(codigo=id)
                            self.wait_window(detalle_window)
                            if detalle_window.cancelar_codigo():
                                pass
                            else:
                                if str(numero_ficha) == str(g[0][2]):
                                    registrar_codint_test(id, data)
                                    self.registro_co()
                                    build_label_nc(self.cb.get(), id, numero_ficha)
                                else:
                                    mb.showinfo(message="¡Atención!")
                                    v = mb.askyesnocancel(message=f"El código que intenta registrar ha sido inventariado anteriormente en el Acta {g[0][2]} - {g[0][12]} ¿Desea inventariarlo en el acta actual?, si presiona NO se inventariara en el acta anterior", title="¡Atención!")
                                    if v == True:
                                        registrar_codint_test(id, data)
                                        self.registro_co()
                                        build_label_nc(self.cb.get(), id, numero_ficha)
                                    elif v == False:
                                        na = g[0][2]
                                        now = datetime.now()
                                        F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
                                        data_a = [na, F_inv, self.user, self.team]
                                        registrar_codint_test(id, data_a)
                                        build_label_nc(self.cb.get(), id, na)
                                        mb.showinfo(message="Se registro correctamente", title="Acontar S.A.C.")
                                        self.etrCodpat.delete(0, 'end')
                                    else:
                                        self.etrCodpat.delete(0, 'end')
                    else:
                        g = buscar_bien(id, 1)
                        if g[0][1] != "":
                            mb.showinfo(message=f"El Código ya ha sido registrado en el Acta {g[0][1]} - {g[0][12]}", title="¡Atención!")
                        else:
                            if str(numero_ficha) == str(g[0][2]):
                                if self.procesar_codigo(id):
                                    registrar_codint_test(id, data)
                                    self.registro_co()
                                    build_label(self.cb.get(), id, numero_ficha)
                            else:
                                mb.showinfo(message="¡Atención!")
                                v = mb.askyesnocancel(message=f"El código que intenta registrar ha sido inventariado anteriormente en el Acta {g[0][2]} - {g[0][12]} ¿Desea inventariarlo en el acta actual?, si presiona NO se inventariara en el acta anterior", title="¡Atención!")
                                if v == True:
                                    if self.procesar_codigo(id):                            
                                        registrar_codint_test(id, data)
                                        self.registro_co()
                                        build_label(self.cb.get(), id, numero_ficha)
                                elif v == False:
                                    if self.procesar_codigo(id):
                                        na = g[0][2]
                                        now = datetime.now()
                                        F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
                                        data_a = [na, F_inv, self.user, self.team]
                                        registrar_codint_test(id, data_a)
                                        build_label(self.cb.get(), id, na)
                                        mb.showinfo(message="Se registro correctamente", title="Acontar S.A.C.")
                                else:
                                    self.etrCodpat.delete(0, 'end')
                else:
                    mb.showinfo(message="EL código no existe", title="¡Atención!")
                    self.etrCodpat.focus()
                    self.etrCodpat.delete(0, 'end')
    
    def procesar_codigo(self, id):
        if self.ba.get() == False:
            detalle_window = Window_detalles(codigo=id)
            self.wait_window(detalle_window)
            self.iniciar_filtro()
            if detalle_window.accion == 1:
                return False
            else:
                return True
        else:
            return True
    
    def registro_co(self):
        self.add_reg()
        self.etrCodpat.focus()
        self.etrCodpat.delete(0, 'end')
        self.total_reg()
        self.tree.yview((self.tree.index(self.tree.get_children()[-1])))
        self.iniciar_filtro()
    
    def add_reg(self):
        try:
            c = self.tree.get_children()[-1]
            i = self.tree.item(c)['values'][0]
            r = self.id.get()
            b = mostrar_datos_test(r[0:12])
            g = list(b[0])
            g.insert(0,i+1)
            my_tag = 'normal' if str(g[4]) == str(self.valor.get()) else 'fail'
            self.tree.insert('', tk.END, values=g, tags=(my_tag))
        except:
            r = self.id.get()
            b = mostrar_datos_test(r[0:12])
            g = list(b[0])
            g.insert(0,1)
            my_tag = 'normal' if str(g[4]) == str(self.valor.get()) else 'fail'
            self.tree.insert('', tk.END, values=g, tags=(my_tag))

    def iniciar_filtro(self):
        r = self.valor.get()
        if r == "":
            mb.showinfo(message="Ingrese un número de acta", title="¡Atencion!")
        else:
            for item in self.tree.get_children():
                self.tree.delete(item)
            try:
                j = mostrar_d_personal(self.valor.get())
                v2 = j[0][1]
                v3 = j[0][2]
                v4 = j[0][3]
                v5 = j[0][4]
                v6 = j[0][5]
                self.local.set(v2)
                self.area.set(v3)
                self.oficina.set(v4)
                self.resp.set(v6)
                self.dni.set(v5)
                self.total_reg()
                o = mostrar_datos(r)
                # print(o)			
                for cell, contact in enumerate(o, 1):
                    b = list(contact)
                    b.insert(0, str(cell))
                    my_tag = 'normal' if str(b[4]) == str(self.valor.get()) else 'fail'
                    self.tree.insert('', tk.END, values=b, tags=(my_tag))
            except Exception as e:
                mb.showinfo(message="El acta no existe", title="¡Atencion!")
                self.focus_set()
                print(str(e))
                
    def total_reg(self):		
        rr = total_bienes(self.valor.get())
        self.totalb.set(rr)
        # ss = len(self.tree.get_children())
        # self.totalI.set(ss)
        ss = total_bienes_s(self.valor.get())
        self.totals.set(ss[0])
        bf = total_bienes_f(self.valor.get())
        rtf = int(rr[0][0])-int(bf[0][0])
        self.totalF.set(int(rr[0][0])-int(rtf))
        
    def widgets_buscar(self):
        self.frame1_2 = ttk.Frame(self.frame1, style='Frame2.TFrame')
        self.frame1_2.pack(fill='y', expand=True, side='right')
        
        self.frame1_2_1 = ttk.Frame(self.frame1_2, style='Frame2.TFrame')
        self.frame1_2_1.pack(fill='x', expand=True, side='top')
        
        self.frame1_2_2 = ttk.Frame(self.frame1_2, style='Frame2.TFrame')
        self.frame1_2_2.pack(fill='x', expand=True, side='bottom')
        
                # Frame top
        lblCod = ttk.Label(self.frame1_2_1, text="Código").grid(column=0, row=0, padx=1, pady=1, sticky="ew")
        etrCod = ttk.Entry(self.frame1_2_1, textvariable= self.codi, width=13).grid(column=1, row=0, padx=1, pady=1, sticky="ew")
        btnBus = ttk.Button(self.frame1_2_1, text="Buscar", command=lambda:self.buscar_cod()).grid(column=2, row=0, padx=1, sticky="ew")
        etrAct = ttk.Entry(self.frame1_2_1, textvariable= self.aact, width=7).grid(column=3, row=0, padx=1, pady=1, sticky="ew")
        btnAct = ttk.Button(self.frame1_2_1, text="Actualizar", command=lambda:self.actualizar_cod()).grid(column=4, row=0, padx=1,sticky="w")
        etrDen = ttk.Entry(self.frame1_2_1, textvariable= self.deno, width=45, state='readonly').grid(column=5, row=0, columnspan=2, padx=1, pady=1, sticky="ew")

                # Labels
        lblInve = ttk.Label(self.frame1_2_2, text="Inventario").grid(column=0, row=0, padx=1, pady=1, sticky="ew")
        lblActA = ttk.Label(self.frame1_2_2, text="Inv. Anterior").grid(column=0, row=1, padx=1, pady=1, sticky="ew")
        lblCodP = ttk.Label(self.frame1_2_2, text="Cód. Patrimonial").grid(column=0, row=2, padx=1, pady=1, sticky="ew")
        lblMarc = ttk.Label(self.frame1_2_2, text="Marca").grid(column=0, row=3, padx=1, pady=1, sticky="ew")
        lblSeri = ttk.Label(self.frame1_2_2, text="Serie").grid(column=0, row=4, padx=1, pady=1, sticky="ew")

                # Entrys
        etrInve = ttk.Entry(self.frame1_2_2,textvariable= self.inve, state='readonly').grid(column=1, row=0, columnspan=3, padx=1, pady=1, sticky="ew")
        etrActA = ttk.Entry(self.frame1_2_2, textvariable= self.acta, state='readonly').grid(column=1, row=1, columnspan=3, padx=1, pady=1, sticky="ew")
        etrCodP = ttk.Entry(self.frame1_2_2, textvariable= self.codp, state='readonly').grid(column=1, row=2, padx=1, pady=1, sticky="ew")
        etrMarc = ttk.Entry(self.frame1_2_2, textvariable= self.marc).grid(column=1, row=3, padx=1, pady=1, sticky="ew")
        etrSeri = ttk.Entry(self.frame1_2_2, textvariable= self.seri).grid(column=1, row=4, padx=1, pady=1, sticky="ew")


        lblOtro = ttk.Label(self.frame1_2_2, text="Otros").grid(column=2, row=2, padx=1, pady=1, sticky="ew")
        # lblFecA = ttk.Label(self.frame1_2_2, text="Fecha Adqui.").grid(column=2, row=3, padx=1, pady=1, sticky="ew")
        # lblDocA = ttk.Label(self.frame1_2_2, text="Doc. Adqui.").grid(column=2, row=2, padx=1, pady=1, sticky="ew")
        lblMode = ttk.Label(self.frame1_2_2, text="Modelo").grid(column=2, row=3, padx=1, pady=1, sticky="ew")
        lblColo = ttk.Label(self.frame1_2_2, text="Color").grid(column=2, row=4, padx=1, pady=1, sticky="ew")

                # Entrys
        etrOtro = ttk.Entry(self.frame1_2_2, textvariable= self.otro).grid(column=3, row=2, padx=1, pady=1, sticky="ew")
        # etrFecA = ttk.Entry(self.frame1_2_2, textvariable= self.fech, state='readonly').grid(column=3, row=1, padx=1, pady=1, sticky="ew")
        # etrDocA = ttk.Entry(self.frame1_2_2, textvariable= self.dadq, state='readonly').grid(column=3, row=2, padx=1, pady=1, sticky="ew")
        etrMode = ttk.Entry(self.frame1_2_2, textvariable= self.mode).grid(column=3, row=3,padx=1, pady=1, sticky="ew")
        etrColo = ttk.Entry(self.frame1_2_2, textvariable= self.colo).grid(column=3, row=4, padx=1, pady=1, sticky="ew")


        lblTipo = ttk.Label(self.frame1_2_2, text="Tipo").grid(column=4, row=0, padx=1, pady=1, sticky="ew")
        lblSitu = ttk.Label(self.frame1_2_2, text="Situacion").grid(column=4, row=1, padx=1, pady=1, sticky="ew")
        lblEsta = ttk.Label(self.frame1_2_2, text="Estado").grid(row=2, column=4, padx=1, pady=1, sticky="ew")
        lblDime = ttk.Label(self.frame1_2_2, text="Dimensión").grid(row=3, column=4, padx=1, pady=1, sticky="ew")
        lblObse = ttk.Label(self.frame1_2_2, text="Obs").grid(row=4, column=4, padx=1, pady=1, sticky="ew")

        etrTipo = ttk.Entry(self.frame1_2_2, textvariable= self.tipo).grid(column=5, row=0, padx=1, pady=1, sticky="ew")
        etrSitu = ttk.Entry(self.frame1_2_2, textvariable= self.situ).grid(column=5, row=1, padx=1, pady=1, sticky="ew")
        etrEsta = ttk.Entry(self.frame1_2_2, textvariable= self.esta).grid(row=2, column=5, padx=1, pady=1, sticky="ew")
        etrDime = ttk.Entry(self.frame1_2_2, textvariable= self.dime).grid(row=3, column=5, padx=1, pady=1, sticky="ew")
        etrObse = ttk.Entry(self.frame1_2_2, textvariable= self.obse).grid(row=4, column=5, padx=1, pady=1, sticky="ew")
        
        btnDeta = ttk.Button(self.frame1_2_2, text="Modificar", command=lambda:self.actualizar_det()).grid(row=5, column=5, padx=1, pady=1, sticky="ew")	
        lblNota = ttk.Label(self.frame1_2_2, text="Nota").grid(row=5, column=0, padx=1, pady=1, sticky="ew")

        self.txtNota = tk.Text(self.frame1_2_2, height=2, width=1)
        self.txtNota.configure(font=('Arial', 9), bg='white', relief='solid')
        self.txtNota.grid(row=5, column=1, columnspan=4, padx=1, pady=1, sticky="ew")

    def buscar_cod(self, *args):
        j = self.codi.get()
        # print(j)
        if j == "":
            mb.showinfo(message="Ingrese un código para buscar", title="¡Atencion!")
        else:
            r = buscar_bien(j, 1)
            bi = buscar_bien(j, 2)
            # print(bi)
            try:
                self.deno.set(str(r[0][0]))
                if bi:
                    self.inve.set(str(bi[0][0]))
                else:
                    self.inve.set('')
                self.acta.set(str(r[0][2]) + ' - ' + r[0][12])
                self.marc.set(str(r[0][3]))
                self.seri.set(str(r[0][4]))
                self.mode.set(str(r[0][5]))
                self.fech.set(str(r[0][6]))
                self.dadq.set(str(r[0][7]))
                self.colo.set(str(r[0][8]))
                self.esta.set(str(r[0][9]))
                self.dime.set(str(r[0][10]))
                self.obse.set(str(r[0][11]))
                self.otro.set(str(r[0][13]))
                self.situ.set(str(r[0][14]))
                self.codp.set(str(r[0][15]))
                self.txtNota.delete("1.0", "end")
                self.txtNota.insert("1.0", str(r[0][16]))
                self.tipo.set(str(r[0][17]))
            except Exception as e:
                mb.showinfo(message="El codigo no existe", title="¡Atencion!")
                print(e)
    
    def actualizar_cod(self):
        j = self.codi.get()
        if j == "":
            mb.showinfo(message="Ingrese un número de acta", title="¡Atencion!")
        else:
            try:
                Acta = self.aact.get()
                now = datetime.now()
                F_inv = now.strftime("%d/%m/%Y %H:%M:%S")
                data = [Acta, F_inv, self.user, self.team]
                actualizar_registro(self.codi.get(), data)
                self.iniciar_filtro()
                self.buscar_cod()
                mb.showinfo(message="Se actualizo correctamente", title="Actualización")
            except:
                mb.showerror(message="Ocurrio un Error", title="Error")

    def actualizar_det(self):
        data = [self.marc.get(), self.mode.get(), self.colo.get(), self.seri.get(),
                self.esta.get(), self.dime.get(), self.obse.get(), self.otro.get(), 
                self.situ.get(), self.fech.get(), self.dadq.get(), self.txtNota.get("1.0", "end-1c"),
                self.tipo.get()]
        try:
            actualizar_detalles(self.codi.get(), data)
            if self.crit.get()=="" or self.camp.get()=="":
                self.iniciar_filtro()
            else:
                self.buscar_criterio()
            mb.showinfo(message="Se actualizo correctamente", title="Acontar S.A.C.")
        except:
            mb.showerror(message="Error al actualizar", title="Error")

    def buscar_criterio(self):
        if self.crit.get()=="" or self.valor.get()=="" or self.camp.get()=="":
            mb.showinfo(message="Ingrese un criterio y valor para buscar", title="¡Atención!")
        else:	
            for item in self.tree.get_children():
                self.tree.delete(item)
            if self.crit.get()=="ValAdq":
                r = mostrar_datos_criterio_val1(self.valor.get(), self.crit.get(), self.camp.get())
            else:
                r = mostrar_datos_criterio(self.valor.get(), self.crit.get(), self.camp.get())
            for cell, contact in enumerate(r, 1):
                b = list(contact)
                b.insert(0, str(cell))

                my_tag = 'normal' if str(b[4]) == str(self.valor.get()) else 'fail'
            # self.tree.insert('', tk.END, values=g, tags=(my_tag))

                self.tree.insert('', tk.END, values=b, tags=(my_tag))

    def exportar_inv(self):
        if self.valor.get() == "":
            mb.showerror(message="Ingrese un número de acta", title="¡Atención!")
        else:
            try:
                r = mostrar_inventario(self.valor.get())
                today = date.today()
                archivo = str(self.valor.get())+"_"+today.strftime("%d_%m_%Y")+".csv"
                with open("exportar/"+archivo, "w", newline="") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=",")
                    csv_writer.writerows(r)
                mb.showinfo(message="Inventario exportado con exito", title="¡Atención!")
            except:
                mb.showerror(message="Ha ocurrido un error al exportar el inventario", title="Error")

    def generar_acta(self):
        try:
            iniciar_reporte(self.valor.get(), self.user, self.Ndni, self.team)
            mb.showinfo(message="El acta se generó con exito", title="Acontar S.A.C.")
        except Exception as e:
            mb.showerror(message=f"Ocurrio un error al generar el acta", title="Error")
            print(str(e))

    def mostrar_datos_(self, *args):
        try:
            curActa = self.tree.focus()
            vnb = self.tree.item(curActa)['values']
            j = vnb[2]
            self.codi.set(j)
            self.buscar_cod()
            # Window_detalles(codigo=j)
            self.iniciar_filtro
        except Exception as e:
            print(e)

    def ver_sobrantes(self):
        ventana = Window_surplus(valor=self.valor.get())
        ventana.buscar()

    def crear_menu(self):
        barra_menu = Menu(self.root)
        self.root.config(menu = barra_menu)

        # cof_menu = Menu(barra_menu, tearoff=0)
        # barra_menu.add_cascade(label="Configuración", menu=cof_menu)
        # cof_menu.add_command(label="Datos", command=lambda:Window_datos_ini())

        opc_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Opciones", menu=opc_menu)
        opc_menu.add_command(label="Datos", command=lambda:Window_config())
        opc_menu.add_command(label="Buscar", command=lambda:Window_buscar())
        opc_menu.add_command(label="Catalogo", command=lambda:Window_catalogo())
        opc_menu.add_command(label="Salir", command=self.root.destroy)

        opc2_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Registrar", menu=opc2_menu)
        opc2_menu.add_command(label="Ubicación/\nPersonal", command=lambda:Window_personal())
        opc2_menu.add_command(label="Sobrantes", command=lambda:Window_surplus())

        # opc3_menu=Menu(barra_menu, tearoff=0)
        # barra_menu.add_cascade(label="Acta", menu=opc3_menu)
        # opc3_menu.add_command(label="Acta", command=lambda:Window_acta())

        opc4_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Etiquetas", menu=opc4_menu)
        opc4_menu.add_command(label="Imprimir", command=lambda:Window_print())

        opc5_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Inventario", menu=opc5_menu)
        opc5_menu.add_command(label="Imp/exp", command=lambda:Window_inv())

        opc6_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Vehiculos", menu=opc6_menu)
        opc6_menu.add_command(label="Ficha Vehicular", command=lambda:Window_vehiculos())

        opc7_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Análisis", menu=opc7_menu)
        # opc7_menu.add_command(label="Por estado de conservación", command=lambda:Window_analisis(valor=1))
        opc7_menu.add_command(label="Por Ubicación", command=lambda:Window_analisis(valor=1))
        opc7_menu.add_command(label="Por Cta Contable", command=lambda:Window_analisis(valor=2))
        opc7_menu.add_command(label="Por DenBien", command=lambda:Window_analisis(valor=3))
        opc7_menu.add_command(label="Por Usuario", command=lambda:Window_analisis(valor=4))

        opc8_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Reportes", menu=opc8_menu)
        opc8_menu.add_command(label="Bienes Ubicados", command=lambda:Window_reporte(valor=1))
        opc8_menu.add_command(label="Bienes de otras entidades", command=lambda:Window_reporte(valor=2))
        opc8_menu.add_command(label="Bienes que no coinciden con la descripción", command=lambda:Window_reporte(valor=3))
        opc8_menu.add_command(label="Bienes para actualización de valor neto", command=lambda:Window_reporte(valor=4))
        opc8_menu.add_command(label="Bienes en desuso o depositos", command=lambda:Window_reporte(valor=5))
        opc8_menu.add_command(label="Bienes afectados en uso o prestamo", command=lambda:Window_reporte(valor=6))
        opc8_menu.add_command(label="Bienes Faltantes", command=lambda:Window_reporte(valor=7))
        opc8_menu.add_command(label="Bienes Sobrantes", command=lambda:Window_reporte(valor=8))
        opc8_menu.add_command(label="Bienes dados de bajo sin disposición", command=lambda:Window_reporte(valor=9))
        opc8_menu.add_command(label="Conciliacion de Inventario", command=lambda:Window_reporte(valor=10))
        opc8_menu.add_command(label="Bienes que requieren actualización tecnica", command=lambda:Window_reporte(valor=11))

        opc9_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Ficha de levantamiento", menu=opc9_menu)
        opc9_menu.add_command(label="Generar", command=lambda:Window_Acta())

        opc10_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Conectar camara", menu=opc10_menu)
        opc10_menu.add_command(label="Iniciar camara", command=lambda:Window_scanner(self))

        opc11_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Servidor", menu=opc11_menu)
        opc11_menu.add_command(label="Iniciar servidor", command=lambda:Window_server(self))
