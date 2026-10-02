import csv
import json
import queue
import sqlite3
import threading
import time
import tkinter as tk
import qrcode
from utils.api_client import ApiManagerAcontarSacClient
from tkinter import ttk, Menu, PhotoImage, Toplevel
from PIL import ImageTk
from tkinter import messagebox as mb
from db.query import mostrar_datos, mostrar_d_personal, obtener_id_inventory_record, query_codpat, total_bienes, mostrar_datos_test, val_codigo
from db.query import registrar_inventario_local_pendiente, sincronizar_inventarios_pendientes
from db.query import registrar_codpat_test, total_bienes_f, buscar_bien, actualizar_registro, registrar_codint_test
from db.query import actualizar_detalles, mostrar_datos_criterio, mostrar_inventario, mostrar_datos_criterio_val1
from db.query import total_bienes_s
from datetime import datetime, date
from services.sync_service import SyncService
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
from gui.gui_connection_test import Window_connection_test
from gui.gui_view_data import Window_view_data
from label.label_gen import build_label
from services.local_print_server import LocalPrintServer
from label.label_no_cat import build_label_nc
from funciones.scanner_cam import Window_scanner
from funciones.socket import Window_server

class Frame(ttk.Frame):
    
    def __init__(self, root=None, user=None, Ndni=None, team=None, api_client=None, user_id=1):
        super().__init__(root)
        self.root = root
        self.user = user
        self.Ndni = Ndni
        self.team = team
        
        # 🔥 Guardar la instancia de ApiClient y el ID de usuario
        self.api_client = api_client or getattr(root, 'api_client', None)
        self.user_id = user_id
        # Evita que varios registros inicien sincronizaciones simultáneas.
        self._sync_outbox_lock = threading.Lock()
        
        self.pack(fill='both', expand=True)
        self.crear_menu()
        self.iconoBuscar = PhotoImage(file='img/lupa.png')
        self.iconoRegistrar = PhotoImage(file='img/registrar.png')

        self.sincronizar_en_segundo_plano()
        
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
        self.etrCodpat.bind("<Return>", lambda event: self.registrar(self.valor.get(), self.id.get()))
        self.tree.bind("<Double-Button-1>", self.mostrar_datos_)

        try:
            self.local_print_server = LocalPrintServer()
            self.local_print_server.start()
            self.root.after(100, self._procesar_impresiones_remotas)
        except OSError as exc:
            self.local_print_server = None
            mb.showerror(title="Impresión desde celular", message=f"No se pudo iniciar el servicio local:\n{exc}")

    def _procesar_impresiones_remotas(self):
        if not self.winfo_exists():
            return
        while True:
            try:
                job = self.local_print_server.jobs.get_nowait()
            except queue.Empty:
                break
            try:
                build_label(1, job["codigo"], job["acta"])
                job["result"] = (200, {"ok": True, "message": "Etiqueta enviada a la impresora"})
            except Exception as exc:
                job["result"] = (500, {"ok": False, "error": str(exc)})
            finally:
                job["done"].set()
        self.root.after(100, self._procesar_impresiones_remotas)

    def mostrar_conexion_movil(self):
        server = self.local_print_server
        if server is None:
            mb.showerror(title="Impresión desde celular", message="El servicio local no está disponible.")
            return
        url = f"http://{server.local_ip()}:{server.port}/api/imprimir"
        datos_qr = json.dumps({"url": url, "token": server.token})
        ventana = Toplevel(self.root)
        ventana.title("Conectar celular para imprimir")
        ventana.transient(self.root)
        ventana.grab_set()
        ttk.Label(ventana, text="Conecte el celular a la misma red Wi-Fi y use estos datos:").pack(padx=16, pady=(16, 8))
        qr_image = qrcode.make(datos_qr).resize((220, 220))
        qr_photo = ImageTk.PhotoImage(qr_image)
        qr_label = ttk.Label(ventana, image=qr_photo)
        qr_label.image = qr_photo
        qr_label.pack(padx=16, pady=8)
        ttk.Label(ventana, text=f"Dirección: {url}", wraplength=400).pack(padx=16, pady=4)
        ttk.Label(ventana, text=f"PIN de conexión: {server.token}", wraplength=400).pack(padx=16, pady=4)
        ttk.Label(ventana, text="El QR contiene la dirección y el PIN. Envíe codigo y acta al endpoint.", wraplength=400).pack(padx=16, pady=(4, 16))
        ttk.Button(ventana, text="Cerrar", command=ventana.destroy).pack(pady=(0, 12))

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
        self.frame1.pack(side='top', fill="both")

        self.frame1_1 = ttk.Frame(self.frame1, style='Frame2.TFrame')
        self.frame1_1.pack(side='left', fill="both")

        self.lblActa = ttk.Label(self.frame1_1, text="Nro de Ficha", font=("bold")).grid(column=0, row=0, padx=5, pady=1,sticky="ew")
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
        self.tree.heading(5, text='Anterior', command=lambda:sort_by(self.tree, 5, False))
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
        self.btnTot = ttk.Button(self.frame3, text='Detalle', command=lambda:Window_detalle(self, acta=self.valor.get(), valor=1, user=self.user, team=self.team)).grid(row=0, column=2, sticky="w")
        # self.lblInv = ttk.Label(self.frame3, text='Bienes Inventariados').grid(row=0, column=3, sticky="w")
        self.lblSob = ttk.Label(self.frame3, text='Bienes sobrantes').grid(row=0, column=3)
        self.etrSob = ttk.Entry(self.frame3, textvariable=self.totals, width=20, justify="center").grid(row=0, column=4, sticky="w")			
        self.btnSob = ttk.Button(self.frame3, text='Detalle', command=lambda:self.ver_sobrantes()).grid(row=0, column=5, sticky="w")
        # Entry Frame3
        self.lblFal = ttk.Label(self.frame3, text='Bienes Faltantes').grid(row=0, column=6, sticky="w")
        self.etrFal = ttk.Entry(self.frame3, textvariable=self.totalF, width=20, justify="center").grid(row=0, column=7, sticky="w")			
        self.btnFal = ttk.Button(self.frame3, text='Detalle', command=lambda:Window_detalle(self, acta=self.valor.get(), valor=2, user=self.user, team=self.team)).grid(row=0, column=8, sticky="w")

    def registrar(self, numero_ficha, codigo):
        # 1. Validaciones iniciales (Guard Clauses)
        if not numero_ficha:
            mb.showinfo(message="Ingrese un número de ficha", title="¡Atención!")
            return

        id_codigo = str(codigo[:12]).strip()
        if not id_codigo:
            mb.showinfo(message="Ingrese un código de inventario", title="¡Atención!")
            return

        id_codigo = self.etrCodpat.get().strip()  # 🔥 Asegurar .strip()
        resultado_val = val_codigo(id_codigo)

        print(f"DEBUG -> Código buscado: '{id_codigo}' | Resultado: {resultado_val} | Tipo: {type(resultado_val)}")

        if not resultado_val or str(resultado_val) not in ('1', 'True'):
            mb.showinfo(message="El código no existe", title="¡Atención!")
            self.etrCodpat.focus()
            self.etrCodpat.delete(0, 'end')
            return


        is_long_code = len(id_codigo) > 5

        # 3. Tratamiento especial para código corto "NO CATALOGADO"
        if not is_long_code:
            qcp = query_codpat(id_codigo)
            if qcp and qcp[0][0] == "NO CATALOGADO":
                detalle_window = Window_detalles(codigo=id_codigo)
                self.wait_window(detalle_window)
                if detalle_window.cancelar_codigo():
                    return  # Usuario canceló el formulario de detalles

        # 4. Obtener información del bien en la base de datos
        g = buscar_bien(id_codigo, 1)
        if not g:
            mb.showinfo(message="El código no existe en la base de datos", title="¡Atención!")
            self.etrCodpat.focus()
            self.etrCodpat.delete(0, 'end')
            return

        ubicacion_final_actual = g[0][1]  # Campo Inv (Acta donde ya se inventarió)
        acta_anterior = g[0][2]           # Campo ActaAnt (Ubicación inicial)
        nom_ubicacion = g[0][12]          # Descripción de la ubicación

        # 5. Validar si ya fue inventariado en la sesión/campaña actual
        if ubicacion_final_actual != "":
            mb.showinfo(
                message=f"El Código ya ha sido registrado en el Acta {ubicacion_final_actual} - {nom_ubicacion}",
                title="¡Atención!"
            )
            return

        # 6. Determinar en qué Acta se va a registrar
        acta_destino = numero_ficha 

        if str(numero_ficha) != str(acta_anterior):
            mb.showinfo(message="¡Atención!")
            v = mb.askyesnocancel(
                message=f"El código que intenta registrar ha sido inventariado anteriormente en el Acta {acta_anterior} - {nom_ubicacion}\n\n"
                        f"¿Desea inventariarlo en el acta actual ({numero_ficha})?\n"
                        f"- SÍ: Se inventariará en el acta actual.\n"
                        f"- NO: Se inventariará en el acta anterior ({acta_anterior}).\n"
                        f"- CANCELAR: Anular registro.",
                title="¡Atención!"
            )
            if v is True:
                acta_destino = numero_ficha
            elif v is False:
                acta_destino = acta_anterior
            else:
                # Opción Cancelar o cerrar cuadro de diálogo
                self.etrCodpat.delete(0, 'end')
                return

        # 7. Registrar primero en SQLite. La red nunca debe impedir el trabajo.
        record_id = obtener_id_inventory_record(id_codigo)

        if not record_id:
            mb.showerror(
                title="Error de Registro",
                message=f"No se encontró el registro del bien '{id_codigo}' en la tabla local inventory_records."
            )
            return

        # Recuperar user_id de forma segura (asigna 1 por defecto si no está definido o es None)
        raw_user_id = getattr(self, 'user_id', 1) or 1
        user_id = int(raw_user_id)

        es_no_catalogado = False
        if is_long_code:
            if not self.procesar_codigo(id_codigo):
                return
        else:
            qcp = query_codpat(id_codigo)
            es_no_catalogado = qcp and qcp[0][0] == "NO CATALOGADO"
            if not es_no_catalogado and not self.procesar_codigo(id_codigo):
                return

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        registro_local = registrar_inventario_local_pendiente(
            id_codigo, record_id, acta_destino, now_str,
            self.user, self.team, user_id
        )
        if not registro_local["success"]:
            mb.showerror(title="Error local", message=registro_local["message"])
            return

        # 8. Mostrar inmediatamente el registro nuevo. No se debe recargar toda
        # la lista, pues una ficha con muchos bienes vuelve lento cada registro.
        self.registro_co()
        self._sincronizar_registro_en_segundo_plano()

        # Generar la etiqueta solo cuando el usuario pidió imprimirla. Se agenda
        # después de actualizar la interfaz para que la fila sea visible primero.
        if self.cb.get():
            self.after_idle(
                self._generar_etiqueta,
                is_long_code, es_no_catalogado, id_codigo, acta_destino
            )

        if str(acta_destino) != str(numero_ficha):
            mb.showinfo(message="Se registró correctamente en el acta anterior", title="Acontar S.A.C.")
            self.etrCodpat.delete(0, 'end')
    
    def procesar_codigo(self, id):
        if self.ba.get() == False:
            detalle_window = Window_detalles(codigo=id)
            self.wait_window(detalle_window)
            if getattr(detalle_window, 'accion', None) == 1:
                return False
            try:
                if not self.winfo_exists():
                    return False
            except tk.TclError:
                # La ventana principal se cerró mientras estaba abierto el detalle.
                return False
            self.iniciar_filtro()
            return True
        else:
            return True
    
    def registro_co(self):
        self.add_reg()
        self.etrCodpat.focus()
        self.etrCodpat.delete(0, 'end')
        self.total_reg()
        self.tree.yview_moveto(1.0)

    def _sincronizar_registro_en_segundo_plano(self):
        """Envía la cola sin detener la interacción ni el refresco del Treeview."""
        if self.api_client is None or not self._sync_outbox_lock.acquire(blocking=False):
            return

        def _enviar():
            try:
                resultado = sincronizar_inventarios_pendientes(self.api_client, limite=1)
                if resultado.get("pending", 0):
                    print("⚠️ Registro guardado localmente; pendiente de sincronización.")
            except Exception as error:
                # El registro ya está en la cola local y se reintentará después.
                print(f"⚠️ No se pudo sincronizar el registro: {error}")
            finally:
                self._sync_outbox_lock.release()

        threading.Thread(target=_enviar, daemon=True).start()

    def _generar_etiqueta(self, is_long_code, es_no_catalogado, codigo, acta_destino):
        if is_long_code or not es_no_catalogado:
            build_label(1, codigo, acta_destino)
        else:
            build_label_nc(1, codigo, acta_destino)
    
    def add_reg(self):
        r = self.id.get().strip()
        b = mostrar_datos_test(r[0:12])
        if not b:
            print(f"⚠️ No se encontró el registro recién creado para '{r}'.")
            return

        g = list(b[0])
        g.insert(0, len(self.tree.get_children()) + 1)
        my_tag = 'normal' if str(g[4]).strip() == self.valor.get().strip() else 'fail'
        self.tree.insert('', tk.END, values=g, tags=(my_tag,))

    def iniciar_filtro(self):
        try:
            tree_disponible = hasattr(self, 'tree') and self.tree.winfo_exists()
        except tk.TclError:
            tree_disponible = False

        if not tree_disponible:
            print("⚠️ El Treeview 'self.tree' no está disponible en este frame.")
            return

        # Limpiar filas existentes de manera segura
        for item in self.tree.get_children():
            self.tree.delete(item)

        numero_ficha = self.valor.get().strip()

        if not numero_ficha:
            mb.showinfo(message="Ingrese un número de ficha", title="¡Atención!")
            return

        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            # 1. Obtener datos de personal (si devuelve None, asigna lista vacía [])
            datos_personal = mostrar_d_personal(numero_ficha) or []

            if not datos_personal:
                mb.showinfo(message="La ficha no existe", title="¡Atención!")
                self.focus_set()
                return

            fila = datos_personal[0]
            self.local.set(fila[1] if len(fila) > 1 and fila[1] else "")
            self.area.set(fila[2] if len(fila) > 2 and fila[2] else "")
            self.oficina.set(fila[3] if len(fila) > 3 and fila[3] else "")
            self.dni.set(fila[4] if len(fila) > 4 and fila[4] else "")
            self.resp.set(fila[5] if len(fila) > 5 and fila[5] else "")

            self.total_reg()

            # 2. Obtener lista de bienes (si devuelve None, se fuerza a [])
            lista_datos_registrados = mostrar_datos(numero_ficha) or []

            # 3. Iterar con seguridad
            for cell, contact in enumerate(lista_datos_registrados, 1):
                b = list(contact)
                b.insert(0, str(cell))
                my_tag = 'normal' if str(b[4]).strip() == numero_ficha else 'fail'
                self.tree.insert('', tk.END, values=b, tags=(my_tag,))

        except Exception as e:
            mb.showerror(message=f"Error en la aplicación: {e}", title="Error")
            print(f"❌ Error detallado: {e}")
                
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
        codigo_buscado = self.codi.get().strip()
        
        if not codigo_buscado:
            mb.showinfo(message="Ingrese un código para buscar", title="¡Atención!")
            return

        r = buscar_bien(codigo_buscado, 1)
        bi = buscar_bien(codigo_buscado, 2)

        # Validar que r contenga datos antes de acceder a r[0]
        if not r:
            mb.showinfo(message="El código ingresado no existe", title="¡Atención!")
            return

        try:
            fila = r[0]
            
            # Función auxiliar para evitar mostrar "None" si el campo es nulo
            def get_val(val):
                return str(val) if val is not None else ''

            self.deno.set(get_val(fila[0]))
            
            # Asignar ubicación final (bi)
            if bi and bi[0][0]:
                self.inve.set(get_val(bi[0][0]))
            else:
                self.inve.set('')

            # Concatenación segura de Acta Anterior + Ubicación
            acta_ant = get_val(fila[2])
            ubicacion = get_val(fila[12])
            self.acta.set(f"{acta_ant} - {ubicacion}" if acta_ant else ubicacion)

            self.marc.set(get_val(fila[3]))
            self.seri.set(get_val(fila[4]))
            self.mode.set(get_val(fila[5]))
            self.fech.set(get_val(fila[6]))
            self.dadq.set(get_val(fila[7]))
            self.colo.set(get_val(fila[8]))
            self.esta.set(get_val(fila[9]))
            self.dime.set(get_val(fila[10]))
            self.obse.set(get_val(fila[11]))
            self.otro.set(get_val(fila[13]))
            self.situ.set(get_val(fila[14]))
            self.codp.set(get_val(fila[15]))
            
            # Cargar campo Text
            self.txtNota.delete("1.0", "end")
            self.txtNota.insert("1.0", get_val(fila[16]))
            
            self.tipo.set(get_val(fila[17]))

        except Exception as e:
            mb.showerror(message=f"Error procesando los datos: {e}", title="Error")
            print(f"❌ Error en buscar_cod: {e}")
    
    def actualizar_cod(self):
        codigo = self.codi.get().strip()
        acta_destino = self.aact.get().strip()

        if not codigo:
            mb.showinfo(message="Ingrese un código para actualizar.", title="¡Atención!")
            return
        if not acta_destino:
            mb.showinfo(message="Ingrese el acta de destino.", title="¡Atención!")
            return
        if self.api_client is None:
            mb.showerror(
                message="No hay conexión configurada con el servidor.",
                title="Actualización"
            )
            return

        record_id = obtener_id_inventory_record(codigo)
        if not record_id:
            mb.showerror(
                message=f"No se encontró el registro de inventario para '{codigo}'.",
                title="Actualización"
            )
            return

        try:
            user_id = int(getattr(self, 'user_id', 1) or 1)
            respuesta = self.api_client.update_ultima_ubicacion(
                record_id, acta_destino, user_id
            )
            status = respuesta.get("status_code")
            cuerpo = respuesta.get("data", {})

            if status not in (200, 201):
                mensaje = cuerpo.get("message", "No fue posible actualizar la ubicación en el servidor.")
                if status == 409:
                    mensaje = f"{mensaje}\nSincronice la aplicación para consultar la ubicación vigente."
                mb.showerror(message=mensaje, title="Actualización")
                return

            # La actualización local se realiza únicamente después de que el
            # servidor confirma el cambio, evitando divergencias entre clientes.
            fecha_servidor = cuerpo.get("data", {}).get("fecha_inventariado")
            fecha = fecha_servidor or datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            actualizar_registro(codigo, [acta_destino, fecha, self.user, self.team])
            self.iniciar_filtro()
            self.buscar_cod()
            mb.showinfo(
                message="Ubicación final actualizada en el servidor y localmente.",
                title="Actualización"
            )
        except Exception as error:
            print(f"❌ Error al actualizar ubicación final: {error}")
            mb.showerror(
                message=f"Ocurrió un error al comunicarse con el servidor: {error}",
                title="Actualización"
            )

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
        barra_menu.add_cascade(label="Ubicaciones", menu=opc2_menu)
        opc2_menu.add_command(label="Ubicaciones", command=lambda:Window_personal())
        # opc2_menu.add_command(label="Sobrantes", command=lambda:Window_surplus())

        opc3_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Sobrantes", menu=opc3_menu)
        opc3_menu.add_command(label="Sobrantes", command=lambda:Window_surplus())

        opc4_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Etiquetas", menu=opc4_menu)
        opc4_menu.add_command(label="Imprimir", command=lambda:Window_print(valor=1))
        opc4_menu.add_command(label="Conectar celular", command=self.mostrar_conexion_movil)

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

        reportes_tecnicos = Menu(opc8_menu, tearoff=0)
        reportes_contables = Menu(opc8_menu, tearoff=0)

        opc8_menu.add_cascade(label="Reportes Técnicos", menu=reportes_tecnicos)
        opc8_menu.add_cascade(label="Reportes Contables", menu=reportes_contables)

        reportes_tecnicos.add_command(label="Bienes Ubicados", command=lambda:Window_reporte(valor=1))
        reportes_tecnicos.add_command(label="Bienes de otras entidades", command=lambda:Window_reporte(valor=2))
        reportes_tecnicos.add_command(label="Bienes que no coinciden con la descripción", command=lambda:Window_reporte(valor=3))
        reportes_tecnicos.add_command(label="Bienes para actualización de valor neto", command=lambda:Window_reporte(valor=4))
        reportes_tecnicos.add_command(label="Bienes en desuso o depositos", command=lambda:Window_reporte(valor=5))
        reportes_tecnicos.add_command(label="Bienes afectados en uso o prestamo", command=lambda:Window_reporte(valor=6))
        reportes_tecnicos.add_command(label="Bienes Faltantes", command=lambda:Window_reporte(valor=7))
        reportes_tecnicos.add_command(label="Bienes Sobrantes", command=lambda:Window_reporte(valor=8))
        reportes_tecnicos.add_command(label="Bienes dados de bajo sin disposición", command=lambda:Window_reporte(valor=9))
        reportes_tecnicos.add_command(label="Conciliacion de Inventario", command=lambda:Window_reporte(valor=10))
        reportes_tecnicos.add_command(label="Bienes que requieren actualización tecnica", command=lambda:Window_reporte(valor=11))

        reportes_contables.add_command(label="Bienes Ubicados por cuenta", command=lambda:Window_reporte(valor=12))
        reportes_contables.add_command(label="Bienes Faltantes por cuenta", command=lambda:Window_reporte(valor=13))
        
        opc9_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Ficha de levantamiento", menu=opc9_menu)
        opc9_menu.add_command(label="Generar", command=lambda:Window_Acta())

        opc10_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Conectar camara", menu=opc10_menu)
        opc10_menu.add_command(label="Iniciar camara", command=lambda:Window_scanner(self))

        opc11_menu=Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Servidor", menu=opc11_menu)
        opc11_menu.add_command(label="Probar conexión", command=lambda:Window_connection_test(self))
        opc11_menu.add_command(label="Iniciar servidor", command=lambda:Window_server(self))
        opc11_menu.add_command(label="ver tablas", command=lambda:Window_view_data(self))

    def sincronizar_en_segundo_plano(self, intervalo_minutos=15):
        """Ejecuta sync_changes al iniciar y luego automáticamente cada X minutos."""
        
        def _tarea():
            intervalo_segundos = intervalo_minutos * 60
            
            while True:
                try:
                    db_path = getattr(self.root, "db_path", "db/orap2022.db")
                    db_conn = sqlite3.connect(db_path)
                    
                    sync_service = SyncService(db_conn)
                    api_client = ApiManagerAcontarSacClient()

                    if sync_service.is_initial_sync_done():
                        print("⚡ Ejecutando actualización periódica en segundo plano...")
                        res = sync_service.execute_sync_changes(api_client)
                        print(f"✅ Sync periódico completado: {res.get('message')}")

                    db_conn.close()
                except Exception as e:
                    print(f"⚠️ Sync periódico omitido por error: {e}")

                # Espera el tiempo configurado antes de la siguiente sincronización
                time.sleep(intervalo_segundos)

        # daemon=True garantiza que el hilo finalice si el usuario cierra la aplicación
        threading.Thread(target=_tarea, daemon=True).start()
