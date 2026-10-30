import csv
import json
import os
import queue
import sqlite3
import threading
import time
import tkinter as tk
import qrcode
import urllib.request
from utils.api_client import ApiManagerAcontarSacClient
from tkinter import ttk, Menu, PhotoImage, Toplevel, filedialog
from PIL import Image, ImageTk
from tkinter import messagebox as mb
from db.query import (
    mostrar_datos,
    mostrar_d_personal,
    buscar_oficinas_predictivo,
    obtener_id_inventory_record,
    query_codpat,
    total_bienes,
    mostrar_datos_test,
    val_codigo,
    registrar_inventario_local_pendiente,
    sincronizar_inventarios_pendientes,
    registrar_codpat_test,
    total_bienes_f,
    buscar_bien,
    actualizar_registro,
    registrar_codint_test,
    actualizar_detalles,
    mostrar_datos_criterio,
    mostrar_inventario,
    mostrar_datos_criterio_val1,
    total_bienes_s,
    obtener_fotos_bien,
    agregar_foto_bien,
    eliminar_foto_bien,
    obtener_mapa_conteo_fotos,
)
from datetime import datetime, date
from services.sync_service import SyncService
from utils.order_utils import sort_by
from utils.helpers import resource_path
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
from gui.gui_asset_photos import Window_asset_photos
from gui.gui_estadisticas import Window_estadisticas
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
        
        # Guardar la instancia de ApiClient y el ID de usuario
        self.api_client = api_client or getattr(root, 'api_client', None) or ApiManagerAcontarSacClient()
        self.user_id = user_id
        # Evita que varios registros inicien sincronizaciones simultáneas.
        self._sync_outbox_lock = threading.Lock()

        # Directorio de fotos y estado sutil de fotografías del bien seleccionado
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.photos_dir = os.path.normpath(os.path.join(base_dir, "..", "photos"))
        os.makedirs(self.photos_dir, exist_ok=True)
        self.fotos_bien_actual = []
        self.foto_idx_actual = 0
        self._select_debounce_job = None
        self._popup_oficinas = None
        self._listbox_oficinas = None
        self._lbl_popup_info = None
        self._resultados_oficinas_actuales = []
        self._entry_activo_oficina = None
        
        self.pack(fill='both', expand=True)
        self.crear_menu()

        # Cargar iconos de forma segura
        self.iconoBuscar = self._cargar_icono('img/lupa.png')
        self.iconoRegistrar = self._cargar_icono('img/registrar.png')

        self.sincronizar_en_segundo_plano()
        
        # Estilos modernos TTK
        self._configurar_estilos()

        self.variables()
        self.frame_datos()
        self.widgets_buscar()
        self.frame_tree()
        self.frame_botton()

        # Enlaces de teclado y eventos
        self.etrCodpat.bind("<Return>", lambda event: self.registrar(self.valor.get(), self.id.get()))
        self.etrnActa.bind("<Return>", lambda event: self.iniciar_filtro())
        self.etrnActa.bind("<KeyRelease>", lambda _e: self._cerrar_popup_oficinas())
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select_sutil)
        self.tree.bind("<Double-Button-1>", self.mostrar_datos_)

        try:
            self.local_print_server = LocalPrintServer()
            self.local_print_server.start()
            self.root.after(100, self._procesar_impresiones_remotas)
        except OSError as exc:
            self.local_print_server = None
            mb.showerror(title="Impresión desde celular", message=f"No se pudo iniciar el servicio local:\n{exc}")

    def _cargar_icono(self, rel_path):
        """Carga un PhotoImage usando resource_path de forma segura."""
        full_path = resource_path(rel_path)
        if os.path.exists(full_path):
            try:
                return PhotoImage(file=full_path)
            except Exception:
                return None
        return None

    def _configurar_estilos(self):
        s = ttk.Style()

        # Paleta general moderna
        s.configure('Frame1.TFrame', background='#f8fafc')
        s.configure('Frame2.TFrame', background='#ffffff')
        s.configure('Frame3.TFrame', background='#ffffff')
        s.configure('White.TCheckbutton', background='#ffffff', font=('Segoe UI', 9))

        s.configure('Card.TLabelframe', background='#ffffff', relief='solid', borderwidth=1, bordercolor='#e2e8f0')
        s.configure('Card.TLabelframe.Label', background='#ffffff', foreground='#0f172a', font=('Segoe UI', 10, 'bold'))

        s.configure('StatCard.TLabelframe', background='#ffffff', relief='solid', borderwidth=1, bordercolor='#e2e8f0')
        s.configure('StatCard.TLabelframe.Label', background='#ffffff', foreground='#475569', font=('Segoe UI', 9, 'bold'))

        # Labels generales
        s.configure('TLabel', background='#ffffff', foreground='#334155', font=('Segoe UI', 9))
        s.configure('Bold.TLabel', background='#ffffff', foreground='#0f172a', font=('Segoe UI', 9, 'bold'))

        # Botones
        s.configure('TButton', font=('Segoe UI', 9), padding=(6, 3))
        s.configure('Primary.TButton', font=('Segoe UI', 9, 'bold'), padding=(8, 4))
        s.configure('Success.TButton', font=('Segoe UI', 9, 'bold'), padding=(10, 5))

        # Treeview
        s.configure(
            'Treeview',
            font=('Segoe UI', 9),
            rowheight=26,
            background='#ffffff',
            fieldbackground='#ffffff',
            bordercolor='#e2e8f0',
            borderwidth=1
        )
        s.configure(
            'Treeview.Heading',
            font=('Segoe UI', 9, 'bold'),
            background='#f1f5f9',
            foreground='#1e293b',
            padding=(5, 6)
        )
        s.map('Treeview', background=[('selected', '#2563eb')], foreground=[('selected', '#ffffff')])

        self.style = 'Frame1.TFrame'

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
        self.totalb = tk.IntVar(value=0)
        self.totals = tk.IntVar(value=0)
        self.totalF = tk.IntVar(value=0)
        self.narch = tk.StringVar()
        self.cb = tk.IntVar(value=0)
        self.ba = tk.IntVar(value=0)

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
        self.crit = tk.StringVar(value="DenBien")
        self.camp = tk.StringVar()
        self.filtro_fotos_var = tk.StringVar(value="Todos")
        self.resumen_fotos_acta_var = tk.StringVar(value="")
        self.busqueda_oficina_var = tk.StringVar(value="")

    def frame_datos(self):
        # Contenedor superior (Frame1)
        self.frame1 = tk.Frame(self, bg='#f8fafc')
        self.frame1.pack(side='top', fill="x", padx=10, pady=(8, 4))
        self.frame1.columnconfigure(0, weight=1)
        self.frame1.columnconfigure(1, weight=1)

        # ---- Panel Izquierdo: Ficha y Registro ----
        self.card_ficha = ttk.LabelFrame(
            self.frame1,
            text=" 📍 Ficha de Ubicación y Registro de Inventario ",
            style='Card.TLabelframe',
            padding=(10, 8)
        )
        self.card_ficha.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.frame1_1 = tk.Frame(self.card_ficha, bg='#ffffff')
        self.frame1_1.pack(fill="both", expand=True)
        self.frame1_1.columnconfigure(2, weight=1)
        self.frame1_1.columnconfigure(4, weight=1)

        # Fila 0: Nro de Ficha y Búsqueda + Buscador Predictivo de Oficina
        lblActa = ttk.Label(self.frame1_1, text="Nro de Ficha:", style='Bold.TLabel')
        lblActa.grid(column=0, row=0, padx=(2, 6), pady=4, sticky="w")
        self.lblActa = lblActa

        self.etrnActa = ttk.Entry(self.frame1_1, textvariable=self.valor, width=9, justify="center", font=('Segoe UI', 9, 'bold'))
        self.etrnActa.grid(column=1, row=0, padx=(0, 6), pady=4, sticky="w")

        self.btnbuscar = ttk.Button(
            self.frame1_1,
            text=" Buscar Ficha",
            width=13,
            command=self.iniciar_filtro,
            image=self.iconoBuscar if self.iconoBuscar else None,
            compound='left',
            style='Primary.TButton'
        )
        self.btnbuscar.grid(column=2, row=0, padx=(2, 10), pady=4, sticky="w")

        lblBuscarOfi = ttk.Label(self.frame1_1, text="Buscar Oficina:", style='Bold.TLabel')
        lblBuscarOfi.grid(column=3, row=0, padx=(2, 6), pady=4, sticky="w")

        box_buscar_ofi = tk.Frame(self.frame1_1, bg='#ffffff')
        box_buscar_ofi.grid(column=4, row=0, columnspan=2, padx=(0, 2), pady=4, sticky="ew")

        self.etrBuscarOficina = ttk.Entry(
            box_buscar_ofi,
            textvariable=self.busqueda_oficina_var,
            font=('Segoe UI', 9)
        )
        self.etrBuscarOficina.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.etrBuscarOficina.bind(
            "<FocusIn>",
            lambda _e: self.etrBuscarOficina.after_idle(
                lambda: self.etrBuscarOficina.select_range(0, tk.END)
            )
        )

        self.btnDesplegarOfi = ttk.Button(
            box_buscar_ofi,
            text="▼",
            width=3,
            command=lambda: self._desplegar_todas_oficinas(self.etrBuscarOficina)
        )
        self.btnDesplegarOfi.pack(side="left")

        # Fila 1: Local y Responsable
        lblLocal = ttk.Label(self.frame1_1, text="Local:")
        lblLocal.grid(column=0, row=1, padx=(2, 6), pady=3, sticky="w")
        self.lblLocal = lblLocal
        self.etrLocal = ttk.Entry(self.frame1_1, textvariable=self.local, state='readonly')
        self.etrLocal.grid(column=1, row=1, columnspan=2, padx=(0, 10), pady=3, sticky="ew")

        lblResp = ttk.Label(self.frame1_1, text="Responsable:")
        lblResp.grid(column=3, row=1, padx=(2, 6), pady=3, sticky="w")
        self.lblResp = lblResp
        self.etrResp = ttk.Entry(self.frame1_1, textvariable=self.resp, state='readonly')
        self.etrResp.grid(column=4, row=1, columnspan=2, padx=(0, 2), pady=3, sticky="ew")

        # Fila 2: Área y DNI
        lblArea = ttk.Label(self.frame1_1, text="Área:")
        lblArea.grid(column=0, row=2, padx=(2, 6), pady=3, sticky="w")
        self.lblArea = lblArea
        self.etrArea = ttk.Entry(self.frame1_1, textvariable=self.area, state='readonly')
        self.etrArea.grid(column=1, row=2, columnspan=2, padx=(0, 10), pady=3, sticky="ew")

        lblDni = ttk.Label(self.frame1_1, text="DNI:")
        lblDni.grid(column=3, row=2, padx=(2, 6), pady=3, sticky="w")
        self.lblDni = lblDni
        self.etrDni = ttk.Entry(self.frame1_1, textvariable=self.dni, state='readonly')
        self.etrDni.grid(column=4, row=2, columnspan=2, padx=(0, 2), pady=3, sticky="ew")

        # Fila 3: Oficina (también con búsqueda predictiva) y Checkbox "Al Barrer"
        lblOficina = ttk.Label(self.frame1_1, text="Oficina:")
        lblOficina.grid(column=0, row=3, padx=(2, 6), pady=3, sticky="w")
        self.lblOficina = lblOficina
        self.etrOficina = ttk.Entry(self.frame1_1, textvariable=self.oficina, font=('Segoe UI', 9))
        self.etrOficina.grid(column=1, row=3, columnspan=2, padx=(0, 10), pady=3, sticky="ew")

        self._vincular_busqueda_predictiva_oficina(self.etrBuscarOficina)
        self._vincular_busqueda_predictiva_oficina(self.etrOficina)

        self.checkBar = ttk.Checkbutton(
            self.frame1_1,
            text='Inventario al Barrer',
            variable=self.ba,
            onvalue=1,
            offvalue=0,
            style='White.TCheckbutton'
        )
        self.checkBar.grid(column=3, row=3, columnspan=3, sticky='w', padx=2, pady=3)

        # Fila 4: Escaneo de Código de Barras (Destacado) y Registrar
        lblCodpat = ttk.Label(self.frame1_1, text="Escanear Código:", style='Bold.TLabel')
        lblCodpat.grid(column=0, row=4, padx=(2, 6), pady=(8, 4), sticky="w")
        self.lblCodpat = lblCodpat

        self.etrCodpat = ttk.Entry(self.frame1_1, textvariable=self.id, font=('Segoe UI', 10, 'bold'))
        self.etrCodpat.grid(column=1, row=4, columnspan=2, padx=(0, 10), pady=(8, 4), sticky="ew")

        self.btnreg = ttk.Button(
            self.frame1_1,
            text=" Registrar",
            command=lambda: self.registrar(self.valor.get(), self.id.get()),
            image=self.iconoRegistrar if self.iconoRegistrar else None,
            compound='left',
            style='Success.TButton'
        )
        self.btnreg.grid(column=3, row=4, padx=(0, 8), pady=(8, 4), sticky="ew")

        self.checkImp = ttk.Checkbutton(
            self.frame1_1,
            text='Imprimir Etiquetas',
            variable=self.cb,
            onvalue=1,
            offvalue=0,
            style='White.TCheckbutton'
        )
        self.checkImp.grid(column=4, row=4, columnspan=2, sticky='w', pady=(8, 4))

        # Fila 5: Filtro rápido en la tabla
        lblCri = ttk.Label(self.frame1_1, text="Filtrar tabla:")
        lblCri.grid(row=5, column=0, padx=(2, 6), pady=(6, 2), sticky="w")

        cbxCri = ttk.Combobox(
            self.frame1_1,
            textvariable=self.crit,
            state="readonly",
            values=['CodInt', 'CodPat', 'DenBien', 'ActaAnt', 'Estado', 'Dimension', 'Marca', 'Modelo',
                    'Serie', 'Color', 'ValAdq', 'Obs', 'Otros', 'Situacion', 'FechInv', 'Inventariador', 'Equipo'],
            width=11,
            font=('Segoe UI', 9)
        )
        cbxCri.grid(row=5, column=1, padx=(0, 6), pady=(6, 2), sticky="w")

        etrCrit = ttk.Entry(self.frame1_1, textvariable=self.camp, font=('Segoe UI', 9))
        etrCrit.grid(row=5, column=2, padx=(0, 8), pady=(6, 2), sticky="ew")
        etrCrit.bind("<Return>", lambda e: self.buscar_criterio())

        btnCrit = ttk.Button(
            self.frame1_1,
            text="Filtrar",
            command=self.buscar_criterio,
            image=self.iconoBuscar if self.iconoBuscar else None,
            compound='left',
            style='Action.TButton'
        )
        btnCrit.grid(row=5, column=3, padx=2, pady=(6, 2), sticky="w")

        # Filtro sutil por estado fotográfico + contador discreto
        fotos_filter_box = tk.Frame(self.frame1_1, bg="#ffffff")
        fotos_filter_box.grid(row=5, column=4, columnspan=2, padx=(6, 2), pady=(6, 2), sticky="e")

        ttk.Label(fotos_filter_box, text="Fotos:").pack(side="left", padx=(0, 3))
        self.cbxFiltroFotosApp = ttk.Combobox(
            fotos_filter_box,
            textvariable=self.filtro_fotos_var,
            state="readonly",
            values=["Todos", "Sin foto", "Con foto"],
            width=8,
            font=('Segoe UI', 8)
        )
        self.cbxFiltroFotosApp.pack(side="left", padx=(0, 4))
        self.cbxFiltroFotosApp.bind("<<ComboboxSelected>>", lambda _e: self._aplicar_filtro_fotos_tabla())

        self.lbl_resumen_fotos_acta = tk.Label(
            fotos_filter_box,
            textvariable=self.resumen_fotos_acta_var,
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 8)
        )
        self.lbl_resumen_fotos_acta.pack(side="left")

    def widgets_buscar(self):
        # ---- Panel Derecho: Inspección y Edición de Bien ----
        self.card_inspector = ttk.LabelFrame(
            self.frame1,
            text=" 🔍 Detalle y Edición del Bien Seleccionado ",
            style='Card.TLabelframe',
            padding=(10, 8)
        )
        self.card_inspector.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.frame1_2 = tk.Frame(self.frame1_2 if hasattr(self, 'frame1_2') else self.card_inspector, bg='#ffffff')
        self.frame1_2.pack(fill='both', expand=True)

        # Barra superior de búsqueda de bien
        self.frame1_2_1 = tk.Frame(self.frame1_2, bg='#ffffff')
        self.frame1_2_1.pack(fill='x', side='top', pady=(0, 6))

        ttk.Label(self.frame1_2_1, text="Cód. Bien:", style='Bold.TLabel').pack(side='left', padx=(0, 4))
        etrCod = ttk.Entry(self.frame1_2_1, textvariable=self.codi, width=12, font=('Segoe UI', 9, 'bold'))
        etrCod.pack(side='left', padx=(0, 6))
        etrCod.bind("<Return>", lambda e: self.buscar_cod())

        btnBus = ttk.Button(self.frame1_2_1, text="Buscar", command=self.buscar_cod, style='Action.TButton')
        btnBus.pack(side='left', padx=(0, 10))

        ttk.Label(self.frame1_2_1, text="Acta Destino:").pack(side='left', padx=(0, 4))
        etrAct = ttk.Entry(self.frame1_2_1, textvariable=self.aact, width=8, justify="center")
        etrAct.pack(side='left', padx=(0, 6))

        btnAct = ttk.Button(self.frame1_2_1, text="Actualizar Acta", command=self.actualizar_cod, style='Action.TButton')
        btnAct.pack(side='left')

        # Fila de Denominación
        den_frame = tk.Frame(self.frame1_2, bg='#ffffff')
        den_frame.pack(fill='x', pady=(0, 6))
        ttk.Label(den_frame, text="Denominación:").pack(side='left', padx=(0, 4))
        etrDen = ttk.Entry(den_frame, textvariable=self.deno, state='readonly', font=('Segoe UI', 9))
        etrDen.pack(side='left', fill='x', expand=True)

        # Cuadrícula de detalles del bien (frame1_2_2)
        self.frame1_2_2 = tk.Frame(self.frame1_2, bg='#ffffff')
        self.frame1_2_2.pack(fill='both', expand=True)

        # Columna 0 y 1: Identificación básica
        ttk.Label(self.frame1_2_2, text="Inventario:").grid(column=0, row=0, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.inve, state='readonly', width=14).grid(column=1, row=0, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Inv. Anterior:").grid(column=0, row=1, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.acta, state='readonly', width=14).grid(column=1, row=1, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Cód. Patrim.:").grid(column=0, row=2, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.codp, state='readonly', width=14).grid(column=1, row=2, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Marca:").grid(column=0, row=3, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.marc, width=14).grid(column=1, row=3, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Serie:").grid(column=0, row=4, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.seri, width=14).grid(column=1, row=4, padx=(0, 8), pady=2, sticky="ew")

        # Columna 2 y 3: Características
        ttk.Label(self.frame1_2_2, text="Modelo:").grid(column=2, row=0, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.mode, width=14).grid(column=3, row=0, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Color:").grid(column=2, row=1, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.colo, width=14).grid(column=3, row=1, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Otros:").grid(column=2, row=2, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.otro, width=14).grid(column=3, row=2, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Tipo:").grid(column=2, row=3, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.tipo, width=14).grid(column=3, row=3, padx=(0, 8), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Situación:").grid(column=2, row=4, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.situ, width=14).grid(column=3, row=4, padx=(0, 8), pady=2, sticky="ew")

        # Columna 4 y 5: Estado, Dimensiones y Control Sutil de Fotos
        ttk.Label(self.frame1_2_2, text="Estado:").grid(row=0, column=4, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.esta, width=14).grid(row=0, column=5, padx=(0, 2), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Dimensión:").grid(row=1, column=4, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.dime, width=14).grid(row=1, column=5, padx=(0, 2), pady=2, sticky="ew")

        ttk.Label(self.frame1_2_2, text="Obs:").grid(row=2, column=4, padx=(0, 4), pady=2, sticky="w")
        ttk.Entry(self.frame1_2_2, textvariable=self.obse, width=14).grid(row=2, column=5, padx=(0, 2), pady=2, sticky="ew")

        # Fila 3 y 4 en Columnas 4 y 5: Indicador sutil de Fotos + Acciones rápidas (Ver / + / Eliminar)
        ttk.Label(self.frame1_2_2, text="Fotos:").grid(row=3, column=4, padx=(0, 4), pady=2, sticky="w")
        fotos_sutil_box = tk.Frame(self.frame1_2_2, bg="#ffffff")
        fotos_sutil_box.grid(row=3, column=5, rowspan=2, padx=(0, 2), pady=2, sticky="ew")

        self.lbl_foto_sutil = tk.Label(
            fotos_sutil_box,
            text="📷 —",
            bg="#f1f5f9",
            fg="#64748b",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=2,
            relief="solid",
            bd=1,
            cursor="hand2"
        )
        self.lbl_foto_sutil.pack(side="left", fill="x", expand=True, padx=(0, 3))
        self.lbl_foto_sutil.bind("<Button-1>", lambda _e: self._abrir_visor_sutil_fotos())

        self.btn_add_foto_sutil = ttk.Button(
            fotos_sutil_box,
            text="➕",
            width=3,
            command=self._agregar_foto_sutil
        )
        self.btn_add_foto_sutil.pack(side="left", padx=(0, 2))

        self.btn_del_foto_sutil = ttk.Button(
            fotos_sutil_box,
            text="🗑️",
            width=3,
            command=self._eliminar_foto_sutil,
            state="disabled"
        )
        self.btn_del_foto_sutil.pack(side="left")

        # Fila 5: Nota y Botón Modificar
        ttk.Label(self.frame1_2_2, text="Nota:").grid(row=5, column=0, padx=(0, 4), pady=(6, 2), sticky="w")
        self.txtNota = tk.Text(self.frame1_2_2, height=2, width=28, font=('Segoe UI', 9), bg='#ffffff', relief='solid', bd=1)
        self.txtNota.grid(row=5, column=1, columnspan=4, padx=(0, 8), pady=(6, 2), sticky="ew")

        btnDeta = ttk.Button(self.frame1_2_2, text="💾 Modificar", command=self.actualizar_det, style='Primary.TButton')
        btnDeta.grid(row=5, column=5, padx=(0, 2), pady=(6, 2), sticky="ew")

    def frame_tree(self):
        # Treeview Container
        self.frame2 = tk.Frame(self, bg='#ffffff', bd=1, relief='solid')
        self.frame2.pack(fill='both', expand=True, padx=10, pady=(4, 6))
        self.frame2.rowconfigure(0, weight=1)
        self.frame2.columnconfigure(0, weight=1)

        cab = tuple(range(1, 25))
        self.tree = ttk.Treeview(self.frame2, height=14, columns=cab, show='headings')

        # Tags para resaltado
        self.tree.tag_configure('normal', foreground="#0f172a")
        self.tree.tag_configure('fail', foreground="#dc2626", background="#fee2e2")

        columnas_cfg = [
            (1,  'Item', 45, "center"),
            (2,  'Cód. Patrimonial', 105, "center"),
            (3,  'Cód. Interno', 80, "center"),
            (4,  'Denominación del Bien', 295, "w"),
            (5,  'Fotos', 58, "center"),
            (6,  'Anterior', 70, "center"),
            (7,  'Sede', 100, "w"),
            (8,  'Área', 100, "w"),
            (9,  'Oficina', 100, "w"),
            (10, 'Responsable', 190, "w"),
            (11, 'Estado', 60, "center"),
            (12, 'Dimensión', 85, "w"),
            (13, 'Marca', 85, "w"),
            (14, 'Modelo', 85, "w"),
            (15, 'Serie', 85, "w"),
            (16, 'Color', 85, "w"),
            (17, 'Tipo', 85, "w"),
            (18, 'Valor', 85, "e"),
            (19, 'Obs', 90, "w"),
            (20, 'Otros', 75, "w"),
            (21, 'Situación', 75, "center"),
            (22, 'Fecha Inv.', 120, "w"),
            (23, 'Inventariador', 175, "w"),
            (24, 'Equipo', 65, "center")
        ]

        for col_id, titulo, ancho, alineacion in columnas_cfg:
            self.tree.heading(col_id, text=titulo, command=lambda c=col_id: sort_by(self.tree, c, False))
            self.tree.column(col_id, width=ancho, minwidth=40, stretch=(col_id == 4), anchor=alineacion)

        self.tree.grid(column=0, row=0, padx=4, pady=4, sticky="nsew")
        scrollbarV = ttk.Scrollbar(self.frame2, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbarH = ttk.Scrollbar(self.frame2, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbarV.set, xscroll=scrollbarH.set)

        scrollbarV.grid(column=1, row=0, sticky='ns')
        scrollbarH.grid(column=0, row=1, sticky='ew')

    def frame_botton(self):
        # Barra inferior con tarjetas de estadísticas
        self.frame3 = tk.Frame(self, bg='#f8fafc')
        self.frame3.pack(fill='x', padx=10, pady=(0, 8))
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.columnconfigure(1, weight=1)
        self.frame3.columnconfigure(2, weight=1)
        self.frame3.columnconfigure(3, weight=1)

        # Card 1: Total Bienes
        card_tot = ttk.LabelFrame(self.frame3, text=" 📦 Total Bienes ", style='StatCard.TLabelframe', padding=(12, 6))
        card_tot.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        box_tot = tk.Frame(card_tot, bg='#ffffff')
        box_tot.pack(fill='x')
        self.lbl_tot_num = tk.Label(box_tot, textvariable=self.totalb, font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#0284c7')
        self.lbl_tot_num.pack(side='left', padx=(0, 10))
        self.btnTot = ttk.Button(
            box_tot,
            text='Ver Detalle',
            style='Action.TButton',
            command=lambda: Window_detalle(self, acta=self.valor.get(), valor=1, user=self.user, team=self.team)
        )
        self.btnTot.pack(side='right')

        # Card 2: Bienes Sobrantes
        card_sob = ttk.LabelFrame(self.frame3, text=" ➕ Bienes Sobrantes ", style='StatCard.TLabelframe', padding=(12, 6))
        card_sob.grid(row=0, column=1, sticky="ew", padx=(2, 2))

        box_sob = tk.Frame(card_sob, bg='#ffffff')
        box_sob.pack(fill='x')
        self.lbl_sob_num = tk.Label(box_sob, textvariable=self.totals, font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#7c3aed')
        self.lbl_sob_num.pack(side='left', padx=(0, 10))
        self.btnSob = ttk.Button(
            box_sob,
            text='Ver Detalle',
            style='Action.TButton',
            command=self.ver_sobrantes
        )
        self.btnSob.pack(side='right')

        # Card 3: Bienes Faltantes
        card_fal = ttk.LabelFrame(self.frame3, text=" ⚠️ Bienes Faltantes ", style='StatCard.TLabelframe', padding=(12, 6))
        card_fal.grid(row=0, column=2, sticky="ew", padx=(2, 2))

        box_fal = tk.Frame(card_fal, bg='#ffffff')
        box_fal.pack(fill='x')
        self.lbl_fal_num = tk.Label(box_fal, textvariable=self.totalF, font=('Segoe UI', 12, 'bold'), bg='#ffffff', fg='#dc2626')
        self.lbl_fal_num.pack(side='left', padx=(0, 10))
        self.btnFal = ttk.Button(
            box_fal,
            text='Ver Detalle',
            style='Action.TButton',
            command=lambda: Window_detalle(self, acta=self.valor.get(), valor=2, user=self.user, team=self.team)
        )
        self.btnFal.pack(side='right')

        # Card 4: Estadísticas Globales del Inventario
        card_est = ttk.LabelFrame(self.frame3, text=" 📊 Estadísticas Globales ", style='StatCard.TLabelframe', padding=(12, 6))
        card_est.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        box_est = tk.Frame(card_est, bg='#ffffff')
        box_est.pack(fill='x')
        tk.Label(box_est, text="Dashboard", font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#059669').pack(side='left', padx=(0, 6))
        btnEst = ttk.Button(
            box_est,
            text='Ver Estadísticas',
            style='Action.TButton',
            command=lambda: Window_estadisticas(self)
        )
        btnEst.pack(side='right')

    def registrar(self, numero_ficha, codigo):
        # 1. Validaciones iniciales (Guard Clauses)
        if not numero_ficha:
            mb.showinfo(message="Ingrese un número de ficha", title="¡Atención!")
            return

        id_codigo = self.etrCodpat.get().strip()
        if not id_codigo:
            mb.showinfo(message="Ingrese un código de inventario", title="¡Atención!")
            return

        resultado_val = val_codigo(id_codigo)

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
                self.etrCodpat.delete(0, 'end')
                return

        # 7. Registrar primero en SQLite.
        record_id = obtener_id_inventory_record(id_codigo)

        if not record_id:
            mb.showerror(
                title="Error de Registro",
                message=f"No se encontró el registro del bien '{id_codigo}' en la tabla local inventory_records."
            )
            return

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

        # 8. Mostrar inmediatamente el nuevo registro
        self.registro_co()
        self._sincronizar_registro_en_segundo_plano()

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
                print(f"⚠️ No se pudo sincronizar el registro: {error}")
            finally:
                self._sync_outbox_lock.release()

        threading.Thread(target=_enviar, daemon=True).start()

    def _generar_etiqueta(self, is_long_code, es_no_catalogado, codigo, acta_destino):
        if is_long_code or not es_no_catalogado:
            build_label(1, codigo, acta_destino)
        else:
            build_label_nc(1, codigo, acta_destino)
    
    def _formatear_fila_tree_con_fotos(self, idx_item, contact, mapa_fotos):
        """Inserta el número de ítem y el conteo sutil de fotografías en la posición 4 (Columna 5 'Fotos')."""
        b = list(contact)
        cod_int_str = str(b[1] if len(b) > 1 else "").strip()
        num_fotos = int(mapa_fotos.get(cod_int_str, 0))
        foto_txt = f"📷 {num_fotos}" if num_fotos > 0 else "0"
        acta_ant_str = str(b[3] if len(b) > 3 else "").strip()
        b.insert(0, str(idx_item))
        b.insert(4, foto_txt)
        return b, num_fotos, acta_ant_str

    def _actualizar_resumen_fotos_acta(self, filas_crudas, mapa_fotos):
        total = len(filas_crudas)
        if total == 0:
            self.resumen_fotos_acta_var.set("")
            return
        con_foto = sum(
            1 for r in filas_crudas if int(mapa_fotos.get(str(r[1] if len(r) > 1 else "").strip(), 0)) > 0
        )
        sin_foto = total - con_foto
        self.resumen_fotos_acta_var.set(f"📷 {con_foto}  |  ⚠️ {sin_foto} s/f")

    def _poblar_tree_con_filtro_fotos(self, filas_crudas):
        for item in self.tree.get_children():
            self.tree.delete(item)

        numero_ficha = self.valor.get().strip()
        mapa_fotos = obtener_mapa_conteo_fotos()
        self._actualizar_resumen_fotos_acta(filas_crudas, mapa_fotos)

        modo_fotos = self.filtro_fotos_var.get()
        cell = 0
        for contact in filas_crudas:
            cod_int_str = str(contact[1] if len(contact) > 1 else "").strip()
            n_fotos = int(mapa_fotos.get(cod_int_str, 0))
            if modo_fotos == "Sin foto" and n_fotos > 0:
                continue
            if modo_fotos == "Con foto" and n_fotos == 0:
                continue
            cell += 1
            b, _, acta_ant_str = self._formatear_fila_tree_con_fotos(cell, contact, mapa_fotos)
            my_tag = 'normal' if acta_ant_str == numero_ficha else 'fail'
            self.tree.insert('', tk.END, values=b, tags=(my_tag,))

    def _aplicar_filtro_fotos_tabla(self):
        if not self.valor.get().strip():
            return
        if self.camp.get().strip():
            self.buscar_criterio()
        else:
            self.iniciar_filtro()

    def add_reg(self):
        r = self.id.get().strip()
        b = mostrar_datos_test(r[0:12])
        if not b:
            print(f"⚠️ No se encontró el registro recién creado para '{r}'.")
            return

        mapa_fotos = obtener_mapa_conteo_fotos()
        idx_nuevo = len(self.tree.get_children()) + 1
        fila_tree, _, acta_ant_str = self._formatear_fila_tree_con_fotos(idx_nuevo, b[0], mapa_fotos)
        my_tag = 'normal' if acta_ant_str == self.valor.get().strip() else 'fail'
        self.tree.insert('', tk.END, values=fila_tree, tags=(my_tag,))

    # -------------------------------------------------------------------------
    # BUSCADOR DE FICHA POR NOMBRE DE OFICINA CON TEXTO PREDICTIVO
    # -------------------------------------------------------------------------
    def _vincular_busqueda_predictiva_oficina(self, entry_widget):
        entry_widget.bind("<KeyRelease>", lambda e, w=entry_widget: self._on_keyrelease_oficina(e, w))
        entry_widget.bind("<Down>", lambda e, w=entry_widget: self._navegar_popup_oficina(1, w))
        entry_widget.bind("<Up>", lambda e, w=entry_widget: self._navegar_popup_oficina(-1, w))
        entry_widget.bind("<Next>", lambda e, w=entry_widget: self._navegar_popup_oficina(5, w))
        entry_widget.bind("<Prior>", lambda e, w=entry_widget: self._navegar_popup_oficina(-5, w))
        entry_widget.bind("<Return>", lambda e, w=entry_widget: self._confirmar_oficina_predictiva(w))
        entry_widget.bind("<Escape>", lambda e: self._cerrar_popup_oficinas())
        entry_widget.bind("<FocusOut>", lambda e: self.after(180, self._verificar_foco_popup_oficinas))

    def _formatear_item_oficina_predictiva(self, fila):
        acta, local, area, oficina, _dni, full_name = fila
        ofi_txt = oficina or "(Sin nombre de oficina)"
        detalles = []
        if area:
            detalles.append(area)
        if local and local != area:
            detalles.append(local)
        ubic_txt = f" — {' / '.join(detalles)}" if detalles else ""
        resp_txt = f"  |  👤 {full_name}" if full_name else ""
        return f"🏢 {ofi_txt}   [Ficha: {acta}]{ubic_txt}{resp_txt}"

    def _on_keyrelease_oficina(self, event, entry_widget):
        teclas_ignorar = {
            "Up", "Down", "Left", "Right", "Return", "Escape", "Tab",
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
            "Caps_Lock", "Prior", "Next", "Home", "End"
        }
        if event.keysym in teclas_ignorar:
            return

        termino = entry_widget.get().strip()
        if not termino:
            self._cerrar_popup_oficinas()
            return

        resultados = buscar_oficinas_predictivo(termino, limite=35)
        if not resultados:
            self._mostrar_popup_oficinas(entry_widget, [], termino)
            return

        self._mostrar_popup_oficinas(entry_widget, resultados, termino)

    def _desplegar_todas_oficinas(self, entry_widget=None):
        target = entry_widget or self.etrBuscarOficina
        if self._popup_oficinas is not None and self._popup_oficinas.winfo_exists():
            self._cerrar_popup_oficinas()
            return
        termino = target.get().strip()
        # Si el texto actual coincide exactamente con la oficina ya cargada, mostrar todas para facilitar cambiar
        if termino and termino == self.oficina.get().strip():
            resultados = buscar_oficinas_predictivo("", limite=60)
        else:
            resultados = buscar_oficinas_predictivo(termino, limite=60)
        target.focus_set()
        self._mostrar_popup_oficinas(target, resultados, termino)

    def _mostrar_popup_oficinas(self, entry_widget, resultados, termino=""):
        self._resultados_oficinas_actuales = list(resultados)
        self._entry_activo_oficina = entry_widget

        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            popup = Toplevel(self.root)
            popup.wm_overrideredirect(True)
            popup.transient(self.root)
            popup.configure(bg="#2563eb")

            contenedor = tk.Frame(popup, bg="#ffffff", bd=0)
            contenedor.pack(fill="both", expand=True, padx=1, pady=1)

            header = tk.Frame(contenedor, bg="#eff6ff", padx=8, pady=4)
            header.pack(fill="x")

            self._lbl_popup_info = tk.Label(
                header,
                text="",
                bg="#eff6ff",
                fg="#1e40af",
                font=("Segoe UI", 8, "bold"),
                anchor="w"
            )
            self._lbl_popup_info.pack(side="left", fill="x", expand=True)

            lbl_Cerrar = tk.Label(
                header,
                text="✕",
                bg="#eff6ff",
                fg="#64748b",
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
                padx=4
            )
            lbl_Cerrar.pack(side="right")
            lbl_Cerrar.bind("<Button-1>", lambda _e: self._cerrar_popup_oficinas())

            body = tk.Frame(contenedor, bg="#ffffff")
            body.pack(fill="both", expand=True)

            scrollbar = ttk.Scrollbar(body, orient=tk.VERTICAL)
            listbox = tk.Listbox(
                body,
                font=("Segoe UI", 9),
                bg="#ffffff",
                fg="#0f172a",
                selectbackground="#2563eb",
                selectforeground="#ffffff",
                activestyle="none",
                highlightthickness=0,
                bd=0,
                yscrollcommand=scrollbar.set,
                cursor="hand2"
            )
            scrollbar.config(command=listbox.yview)
            listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=2)
            scrollbar.pack(side="right", fill="y", pady=2)

            listbox.bind("<ButtonRelease-1>", self._seleccionar_item_popup_oficina)
            listbox.bind("<Return>", self._seleccionar_item_popup_oficina)
            listbox.bind("<Escape>", lambda _e: self._cerrar_popup_oficinas())
            listbox.bind("<Motion>", self._on_hover_popup_oficina)

            self._popup_oficinas = popup
            self._listbox_oficinas = listbox

        listbox = self._listbox_oficinas
        listbox.delete(0, tk.END)

        if not resultados:
            self._lbl_popup_info.config(
                text=f"⚠️ Sin coincidencias para '{termino}'",
                fg="#b91c1c"
            )
            listbox.insert(tk.END, "  No se encontraron oficinas que coincidan con la búsqueda.")
            listbox.config(height=2, fg="#64748b")
        else:
            n = len(resultados)
            primera = resultados[0]
            self._lbl_popup_info.config(
                text=f"✨ {n} {'oficina encontrada' if n == 1 else 'oficinas encontradas'} — ↑↓ navegar | Enter o clic: cargar [Ficha {primera[0]}]",
                fg="#1e40af"
            )
            listbox.config(fg="#0f172a")
            for fila in resultados:
                listbox.insert(tk.END, self._formatear_item_oficina_predictiva(fila))
            listbox.config(height=min(max(n, 2), 9))
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(0)
            listbox.activate(0)

        self._posicionar_popup_oficinas(entry_widget)

    def _posicionar_popup_oficinas(self, entry_widget):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            return
        try:
            self.update_idletasks()
            x = entry_widget.winfo_rootx()
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 2
            ancho = max(entry_widget.winfo_width() + 34, 480)
            sw = self.winfo_screenwidth()
            if x + ancho > sw - 12:
                x = max(8, sw - ancho - 12)
            self._popup_oficinas.geometry(f"{ancho}x{self._popup_oficinas.winfo_reqheight()}+{x}+{y}")
            self._popup_oficinas.lift()
        except Exception:
            pass

    def _on_hover_popup_oficina(self, event):
        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            return
        idx = self._listbox_oficinas.nearest(event.y)
        if 0 <= idx < len(self._resultados_oficinas_actuales):
            self._listbox_oficinas.selection_clear(0, tk.END)
            self._listbox_oficinas.selection_set(idx)
            self._listbox_oficinas.activate(idx)
            fila = self._resultados_oficinas_actuales[idx]
            if self._lbl_popup_info is not None:
                self._lbl_popup_info.config(
                    text=f"✨ Seleccionar: {fila[3] or fila[2]} [Ficha {fila[0]}] — Enter o clic para cargar"
                )

    def _navegar_popup_oficina(self, delta, entry_widget):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            self._desplegar_todas_oficinas(entry_widget)
            return "break"

        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            return "break"

        sel = self._listbox_oficinas.curselection()
        actual = int(sel[0]) if sel else 0
        nuevo = max(0, min(len(self._resultados_oficinas_actuales) - 1, actual + delta))
        self._listbox_oficinas.selection_clear(0, tk.END)
        self._listbox_oficinas.selection_set(nuevo)
        self._listbox_oficinas.activate(nuevo)
        self._listbox_oficinas.see(nuevo)

        fila = self._resultados_oficinas_actuales[nuevo]
        if self._lbl_popup_info is not None:
            self._lbl_popup_info.config(
                text=f"✨ Seleccionar: {fila[3] or fila[2]} [Ficha {fila[0]}] — Presione Enter para cargar"
            )
        return "break"

    def _seleccionar_item_popup_oficina(self, _event=None):
        if not self._resultados_oficinas_actuales or self._listbox_oficinas is None:
            self._cerrar_popup_oficinas()
            return "break"

        sel = self._listbox_oficinas.curselection()
        idx = int(sel[0]) if sel else 0
        if 0 <= idx < len(self._resultados_oficinas_actuales):
            fila = self._resultados_oficinas_actuales[idx]
            self._aplicar_oficina_seleccionada(fila)
        return "break"

    def _confirmar_oficina_predictiva(self, entry_widget=None):
        target = entry_widget or self.etrBuscarOficina
        if (
            self._popup_oficinas is not None
            and self._popup_oficinas.winfo_exists()
            and self._resultados_oficinas_actuales
        ):
            return self._seleccionar_item_popup_oficina()

        termino = target.get().strip()
        if not termino:
            return "break"

        resultados = buscar_oficinas_predictivo(termino, limite=35)
        if not resultados:
            mb.showinfo(
                title="Búsqueda de Oficina",
                message=f"No se encontró ninguna oficina que coincida con '{termino}'."
            )
            return "break"

        if len(resultados) == 1:
            self._aplicar_oficina_seleccionada(resultados[0])
        else:
            self._mostrar_popup_oficinas(target, resultados, termino)
        return "break"

    def _aplicar_oficina_seleccionada(self, fila_personal):
        acta, local, area, oficina, dni, full_name = fila_personal
        self._cerrar_popup_oficinas()
        self.valor.set(str(acta or "").strip())
        self.local.set(local or "")
        self.area.set(area or "")
        self.oficina.set(oficina or "")
        self.busqueda_oficina_var.set(oficina or "")
        self.dni.set(dni or "")
        self.resp.set(full_name or "")
        self.iniciar_filtro()
        self.etrCodpat.focus_set()

    def _verificar_foco_popup_oficinas(self):
        if self._popup_oficinas is None or not self._popup_oficinas.winfo_exists():
            return
        try:
            foco = self.root.focus_get()
            if foco in (self.etrBuscarOficina, self.etrOficina, self._listbox_oficinas, self.btnDesplegarOfi):
                return
        except Exception:
            pass
        self._cerrar_popup_oficinas()

    def _cerrar_popup_oficinas(self, _event=None):
        if self._popup_oficinas is not None:
            try:
                if self._popup_oficinas.winfo_exists():
                    self._popup_oficinas.destroy()
            except Exception:
                pass
        self._popup_oficinas = None
        self._listbox_oficinas = None
        self._lbl_popup_info = None
        self._resultados_oficinas_actuales = []

    def iniciar_filtro(self):
        try:
            tree_disponible = hasattr(self, 'tree') and self.tree.winfo_exists()
        except tk.TclError:
            tree_disponible = False

        if not tree_disponible:
            return

        if (
            self._popup_oficinas is not None
            and self._popup_oficinas.winfo_exists()
            and self._resultados_oficinas_actuales
        ):
            self._seleccionar_item_popup_oficina()
            return

        self._cerrar_popup_oficinas()
        numero_ficha = self.valor.get().strip()

        if not numero_ficha:
            termino_ofi = self.busqueda_oficina_var.get().strip() or self.oficina.get().strip()
            if termino_ofi:
                coincidencias = buscar_oficinas_predictivo(termino_ofi, limite=35)
                if len(coincidencias) == 1:
                    self._aplicar_oficina_seleccionada(coincidencias[0])
                    return
                elif len(coincidencias) > 1:
                    self._mostrar_popup_oficinas(self.etrBuscarOficina, coincidencias, termino_ofi)
                    return
                else:
                    mb.showinfo(
                        message=f"No se encontró ninguna oficina que coincida con '{termino_ofi}'.",
                        title="¡Atención!"
                    )
                    return
            mb.showinfo(message="Ingrese un número de ficha o busque por nombre de oficina", title="¡Atención!")
            return

        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            datos_personal = mostrar_d_personal(numero_ficha) or []

            if not datos_personal:
                mb.showinfo(message="La ficha no existe", title="¡Atención!")
                self.focus_set()
                return

            fila = datos_personal[0]
            self.local.set(fila[1] if len(fila) > 1 and fila[1] else "")
            self.area.set(fila[2] if len(fila) > 2 and fila[2] else "")
            ofi_val = fila[3] if len(fila) > 3 and fila[3] else ""
            self.oficina.set(ofi_val)
            self.busqueda_oficina_var.set(ofi_val)
            self.dni.set(fila[4] if len(fila) > 4 and fila[4] else "")
            self.resp.set(fila[5] if len(fila) > 5 and fila[5] else "")

            self.total_reg()

            lista_datos_registrados = mostrar_datos(numero_ficha) or []
            self._poblar_tree_con_filtro_fotos(lista_datos_registrados)

        except Exception as e:
            mb.showerror(message=f"Error en la aplicación: {e}", title="Error")
            print(f"❌ Error detallado: {e}")
                
    def total_reg(self):		
        rr = total_bienes(self.valor.get())
        if rr and len(rr) > 0 and len(rr[0]) > 0:
            try:
                tot_val = int(rr[0][0])
                self.totalb.set(tot_val)
            except Exception:
                self.totalb.set(0)
        else:
            self.totalb.set(0)

        ss = total_bienes_s(self.valor.get())
        if ss and len(ss) > 0:
            try:
                self.totals.set(int(ss[0]))
            except Exception:
                self.totals.set(0)
        else:
            self.totals.set(0)

        bf = total_bienes_f(self.valor.get())
        if rr and bf and len(rr) > 0 and len(bf) > 0:
            try:
                tot_val = int(rr[0][0])
                bf_val = int(bf[0][0])
                rtf = tot_val - bf_val
                self.totalF.set(tot_val - rtf)
            except Exception:
                self.totalF.set(0)
        else:
            self.totalF.set(0)
        
    def buscar_cod(self, *args, silencioso=False):
        codigo_buscado = self.codi.get().strip()
        
        if not codigo_buscado:
            if not silencioso:
                mb.showinfo(message="Ingrese un código para buscar", title="¡Atención!")
            return

        r = buscar_bien(codigo_buscado, 1)
        bi = buscar_bien(codigo_buscado, 2)

        if not r:
            if not silencioso:
                mb.showinfo(message="El código ingresado no existe", title="¡Atención!")
            return

        try:
            fila = r[0]
            
            def get_val(val):
                return str(val) if val is not None else ''

            self.deno.set(get_val(fila[0]))
            
            if bi and bi[0][0]:
                self.inve.set(get_val(bi[0][0]))
            else:
                self.inve.set('')

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
            
            self.txtNota.delete("1.0", "end")
            self.txtNota.insert("1.0", get_val(fila[16]))
            
            self.tipo.set(get_val(fila[17]))

            self._cargar_fotos_bien_sutil()

        except Exception as e:
            if not silencioso:
                mb.showerror(message=f"Error procesando los datos: {e}", title="Error")
            print(f"❌ Error en buscar_cod: {e}")
    
    def actualizar_cod(self):
        codigo = self.codi.get().strip()
        acta_destino = self.aact.get().strip()

        if not codigo:
            mb.showinfo(message="Ingrese un código para actualizar.", title="¡Atención!")
            return

        # Si el acta de destino está vacía o es '0', permitir des-inventariar el bien
        if not acta_destino or acta_destino == "0":
            confirmar = mb.askyesno(
                title="Des-inventariar Bien",
                message=(
                    f"El campo 'Acta Destino' está vacío.\n\n"
                    f"¿Desea quitar el bien '{codigo}' del inventario actual (des-inventariar)?"
                ),
            )
            if not confirmar:
                return
            try:
                actualizar_registro(codigo, ["", "", "", ""])
                self.iniciar_filtro()
                self.buscar_cod(silencioso=True)
                mb.showinfo(
                    message="Bien liberado del inventario localmente y encolado para sincronizar con el servidor.",
                    title="Des-inventariado",
                )
            except Exception as error:
                mb.showerror(message=f"Error al des-inventariar: {error}", title="Error")
            return

        try:
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            actualizar_registro(codigo, [acta_destino, fecha, self.user, self.team])
            self.iniciar_filtro()
            self.buscar_cod(silencioso=True)
            mb.showinfo(
                message="Ubicación final actualizada localmente y enviada a la cola de sincronización del servidor.",
                title="Actualización",
            )
        except Exception as error:
            print(f"❌ Error al actualizar ubicación final: {error}")
            mb.showerror(
                message=f"Ocurrió un error al actualizar la ubicación: {error}",
                title="Actualización",
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
            mb.showinfo(message="Se actualizó correctamente", title="Acontar S.A.C.")
        except Exception as e:
            mb.showerror(message=f"Error al actualizar: {e}", title="Error")

    def buscar_criterio(self):
        if self.crit.get()=="" or self.valor.get()=="" or self.camp.get()=="":
            mb.showinfo(message="Ingrese un criterio y valor para buscar", title="¡Atención!")
        else:	
            if self.crit.get()=="ValAdq":
                r = mostrar_datos_criterio_val1(self.valor.get(), self.crit.get(), self.camp.get()) or []
            else:
                r = mostrar_datos_criterio(self.valor.get(), self.crit.get(), self.camp.get()) or []
            self._poblar_tree_con_filtro_fotos(r)

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
                mb.showinfo(message="Inventario exportado con éxito", title="¡Atención!")
            except Exception as e:
                mb.showerror(message=f"Ha ocurrido un error al exportar el inventario: {e}", title="Error")

    def generar_acta(self):
        try:
            iniciar_reporte(self.valor.get(), self.user, self.Ndni, self.team)
            mb.showinfo(message="El acta se generó con éxito", title="Acontar S.A.C.")
        except Exception as e:
            mb.showerror(message="Ocurrió un error al generar el acta", title="Error")
            print(str(e))

    def _on_tree_select_sutil(self, _event=None):
        if self._select_debounce_job is not None:
            try:
                self.after_cancel(self._select_debounce_job)
            except Exception:
                pass
        self._select_debounce_job = self.after(90, lambda: self.mostrar_datos_(silencioso=True))

    def mostrar_datos_(self, *args, silencioso=False):
        try:
            curActa = self.tree.focus()
            if not curActa:
                sel = self.tree.selection()
                curActa = sel[0] if sel else ""
            if not curActa:
                return
            vnb = self.tree.item(curActa)['values']
            if vnb and len(vnb) > 2:
                j = vnb[2]
                self.codi.set(j)
                self.buscar_cod(silencioso=silencioso)
        except Exception as e:
            print(e)

    # -------------------------------------------------------------------------
    # GESTIÓN SUTIL DE FOTOGRAFÍAS (INDICADOR COMPACTO + VISOR EMERGENTE)
    # -------------------------------------------------------------------------
    def _cargar_fotos_bien_sutil(self):
        codigo = self.codi.get().strip()
        if not codigo:
            self.fotos_bien_actual = []
            self.foto_idx_actual = 0
            self.lbl_foto_sutil.config(text="📷 —", bg="#f1f5f9", fg="#64748b")
            self.btn_del_foto_sutil.config(state="disabled")
            return

        self.fotos_bien_actual = obtener_fotos_bien(codigo)
        self.foto_idx_actual = 0
        n = len(self.fotos_bien_actual)
        if n == 0:
            self.lbl_foto_sutil.config(text="⚠️ 0 (Sin foto)", bg="#fef2f2", fg="#b91c1c")
            self.btn_del_foto_sutil.config(state="disabled")
        else:
            self.lbl_foto_sutil.config(
                text=f"📷 {n} {'foto' if n == 1 else 'fotos'} (Ver)",
                bg="#dcfce7",
                fg="#15803d"
            )
            self.btn_del_foto_sutil.config(state="normal")

    def _refrescar_celda_foto_en_tree(self, codigo, nuevo_total):
        cod_str = str(codigo).strip()
        modo_fotos = self.filtro_fotos_var.get()
        if (modo_fotos == "Sin foto" and nuevo_total > 0) or (modo_fotos == "Con foto" and nuevo_total == 0):
            self._aplicar_filtro_fotos_tabla()
            return

        foto_txt = f"📷 {nuevo_total}" if nuevo_total > 0 else "0"
        for item_id in self.tree.get_children():
            vals = list(self.tree.item(item_id, "values"))
            if len(vals) >= 5 and (str(vals[2]).strip() == cod_str or str(vals[1]).strip() == cod_str):
                vals[4] = foto_txt
                self.tree.item(item_id, values=vals)
                break

        if self.valor.get().strip():
            filas_acta = mostrar_datos(self.valor.get().strip()) or []
            self._actualizar_resumen_fotos_acta(filas_acta, obtener_mapa_conteo_fotos())

    def _agregar_foto_sutil(self):
        codigo = self.codi.get().strip()
        if not codigo:
            mb.showinfo("Seleccione un bien", "Seleccione una fila de la tabla o busque un Cód. Bien primero.", parent=self)
            return

        archivos = filedialog.askopenfilenames(
            title=f"Adjuntar Fotografía(s) al Bien {codigo}",
            filetypes=[("Imágenes", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"), ("Todos los archivos", "*.*")],
            parent=self
        )
        if not archivos:
            return

        for arc in archivos:
            try:
                agregar_foto_bien(codigo, arc, photos_dir=self.photos_dir)
            except Exception as e:
                mb.showerror("Error al guardar foto", str(e), parent=self)

        self._cargar_fotos_bien_sutil()
        self._refrescar_celda_foto_en_tree(codigo, len(self.fotos_bien_actual))

    def _eliminar_foto_sutil(self):
        if not self.fotos_bien_actual:
            return
        codigo = self.codi.get().strip()
        foto = self.fotos_bien_actual[self.foto_idx_actual]
        nombre = os.path.basename(foto.get("ruta_foto", "")) or f"ID #{foto.get('id')}"
        if not mb.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar la fotografía '{nombre}' del bien '{codigo}'?",
            parent=self
        ):
            return
        if eliminar_foto_bien(foto["id"]):
            self._cargar_fotos_bien_sutil()
            self._refrescar_celda_foto_en_tree(codigo, len(self.fotos_bien_actual))

    def _resolver_ruta_foto_local(self, ruta):
        if not ruta:
            return None
        ruta_clean = str(ruta).replace("\\", "/")
        if os.path.isabs(ruta) and os.path.exists(ruta):
            return ruta
        nombre = os.path.basename(ruta_clean)
        for c in (
            os.path.join(self.photos_dir, nombre),
            os.path.join(self.photos_dir, ruta_clean),
            os.path.join(self.photos_dir, f"code_{nombre}"),
        ):
            if os.path.exists(c):
                return c
        return None

    def _abrir_visor_sutil_fotos(self):
        codigo = self.codi.get().strip()
        if not codigo:
            return
        if not self.fotos_bien_actual:
            if mb.askyesno(
                "Sin fotografías",
                f"El bien '{codigo}' aún no tiene fotografías.\n¿Desea agregar una foto ahora?",
                parent=self
            ):
                self._agregar_foto_sutil()
            return

        visor = Toplevel(self.root)
        denom = self.deno.get().strip()
        visor.title(f"Fotografías del Bien [{codigo}] — {denom}")
        visor.geometry("760x560")
        visor.minsize(580, 420)
        visor.configure(bg="#0f172a")
        visor.transient(self.root)

        top_f = tk.Frame(visor, bg="#1e293b", padx=12, pady=8)
        top_f.pack(fill="x")

        lbl_info = tk.Label(top_f, text="", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 9, "bold"), anchor="w")
        lbl_info.pack(side="left", fill="x", expand=True)

        lbl_meta = tk.Label(top_f, text="", bg="#1e293b", fg="#38bdf8", font=("Segoe UI", 8, "bold"))
        lbl_meta.pack(side="right")

        canvas_f = tk.Frame(visor, bg="#0f172a")
        canvas_f.pack(fill="both", expand=True, padx=10, pady=8)

        lbl_img = tk.Label(canvas_f, bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 9))
        lbl_img.pack(fill="both", expand=True)

        bot_f = tk.Frame(visor, bg="#1e293b", padx=12, pady=8)
        bot_f.pack(fill="x")

        btn_ant = ttk.Button(bot_f, text="◀ Anterior")
        btn_ant.pack(side="left", padx=(0, 6))

        lbl_pag = tk.Label(bot_f, text="1 / 1", bg="#1e293b", fg="#f8fafc", font=("Segoe UI", 9, "bold"))
        lbl_pag.pack(side="left", padx=8)

        btn_sig = ttk.Button(bot_f, text="Siguiente ▶")
        btn_sig.pack(side="left", padx=(6, 12))

        def _render_foto_visor():
            if not visor.winfo_exists():
                return
            if not self.fotos_bien_actual:
                visor.destroy()
                return
            total = len(self.fotos_bien_actual)
            if self.foto_idx_actual >= total:
                self.foto_idx_actual = total - 1
            foto = self.fotos_bien_actual[self.foto_idx_actual]
            ruta = foto.get("ruta_foto", "")
            sinc = "✅ Sincronizada" if foto.get("sincronizado") == 1 else "⏳ Local"
            lbl_info.config(text=f"📦 [{codigo}] {denom}   —   {os.path.basename(ruta)}")
            lbl_meta.config(text=f"{foto.get('fecha') or ''}   |   {sinc}")
            lbl_pag.config(text=f"{self.foto_idx_actual + 1} / {total}")
            btn_ant.config(state="normal" if self.foto_idx_actual > 0 else "disabled")
            btn_sig.config(state="normal" if self.foto_idx_actual < total - 1 else "disabled")

            local_p = self._resolver_ruta_foto_local(ruta)
            if local_p and os.path.exists(local_p):
                try:
                    visor.update_idletasks()
                    w = max(400, canvas_f.winfo_width() - 20)
                    h = max(300, canvas_f.winfo_height() - 20)
                    with Image.open(local_p) as im:
                        im_c = im.copy()
                        im_c.thumbnail((w, h), Image.Resampling.LANCZOS)
                        visor._tk_im = ImageTk.PhotoImage(im_c)
                        lbl_img.config(image=visor._tk_im, text="")
                except Exception as ex:
                    lbl_img.config(image="", text=f"No se pudo mostrar la imagen:\n{ex}")
            elif ruta:
                lbl_img.config(image="", text="⬇️ Descargando foto desde el servidor...")

                def _dl():
                    try:
                        url = self.api_client.get_photo_url(ruta)
                        destino = os.path.join(self.photos_dir, os.path.basename(str(ruta).replace("\\", "/")))
                        req = urllib.request.Request(
                            url, headers={"User-Agent": "Mozilla/5.0 AcontarSoft/1.0"}
                        )
                        with urllib.request.urlopen(req, timeout=20) as resp, open(destino, "wb") as out:
                            out.write(resp.read())
                        if visor.winfo_exists():
                            visor.after(0, _render_foto_visor)
                    except Exception:
                        if visor.winfo_exists():
                            visor.after(0, lambda: lbl_img.config(image="", text="📷 Foto en servidor (sin conexión)"))

                threading.Thread(target=_dl, daemon=True).start()

        def _prev():
            if self.foto_idx_actual > 0:
                self.foto_idx_actual -= 1
                _render_foto_visor()

        def _next():
            if self.foto_idx_actual < len(self.fotos_bien_actual) - 1:
                self.foto_idx_actual += 1
                _render_foto_visor()

        def _add():
            self._agregar_foto_sutil()
            if visor.winfo_exists():
                _render_foto_visor()

        def _del():
            self._eliminar_foto_sutil()
            if visor.winfo_exists():
                _render_foto_visor()

        btn_ant.config(command=_prev)
        btn_sig.config(command=_next)

        ttk.Button(bot_f, text="🗑️ Eliminar", command=_del).pack(side="right", padx=(6, 0))
        ttk.Button(bot_f, text="➕ Agregar Foto", command=_add).pack(side="right", padx=6)

        visor.bind("<Configure>", lambda _e: visor.after_idle(_render_foto_visor))
        visor.after(40, _render_foto_visor)

    def ver_sobrantes(self):
        ventana = Window_surplus(valor=self.valor.get())
        ventana.buscar()

    def crear_menu(self):
        barra_menu = Menu(self.root)
        self.root.config(menu=barra_menu)

        opc_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Opciones", menu=opc_menu)
        opc_menu.add_command(label="Configuración / Datos", command=lambda: Window_config())
        opc_menu.add_command(label="Buscar Bienes", command=lambda: Window_buscar())
        opc_menu.add_command(label="Catálogo SBN", command=lambda: Window_catalogo())
        opc_menu.add_separator()
        opc_menu.add_command(label="Salir del Sistema", command=self.root.destroy)

        opc2_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Ubicaciones", menu=opc2_menu)
        opc2_menu.add_command(label="Gestión de Personal / Ubicaciones", command=lambda: Window_personal())

        opc3_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Sobrantes", menu=opc3_menu)
        opc3_menu.add_command(label="Bienes Sobrantes", command=lambda: Window_surplus())

        opc4_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Etiquetas", menu=opc4_menu)
        opc4_menu.add_command(label="Imprimir Etiquetas", command=lambda: Window_print(valor=1))
        opc4_menu.add_command(label="Conectar celular para imprimir", command=self.mostrar_conexion_movil)

        opc5_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Inventario", menu=opc5_menu)
        opc5_menu.add_command(label="Importar / Exportar Inventario", command=lambda: Window_inv())
        opc5_menu.add_command(label="📊 Estadísticas del Inventario", command=lambda: Window_estadisticas(self))

        opc6_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Vehículos", menu=opc6_menu)
        opc6_menu.add_command(label="Ficha Vehicular", command=lambda: Window_vehiculos())

        # Menú Estadísticas
        opc_est_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="📊 Estadísticas", menu=opc_est_menu)
        opc_est_menu.add_command(label="📊 Panel General de Estadísticas y Dashboard", command=lambda: Window_estadisticas(self))
        opc_est_menu.add_separator()
        opc_est_menu.add_command(label="Avance por Ubicación", command=lambda: Window_analisis(valor=1))
        opc_est_menu.add_command(label="Avance por Cuenta Contable", command=lambda: Window_analisis(valor=2))

        opc7_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Análisis", menu=opc7_menu)
        opc7_menu.add_command(label="📊 Panel de Estadísticas y Dashboard", command=lambda: Window_estadisticas(self))
        opc7_menu.add_separator()
        opc7_menu.add_command(label="Por Ubicación", command=lambda: Window_analisis(valor=1))
        opc7_menu.add_command(label="Por Cuenta Contable", command=lambda: Window_analisis(valor=2))
        opc7_menu.add_command(label="Por Denominación", command=lambda: Window_analisis(valor=3))
        opc7_menu.add_command(label="Por Usuario / Inventariador", command=lambda: Window_analisis(valor=4))

        opc8_menu = Menu(barra_menu, tearoff=0)        
        barra_menu.add_cascade(label="Reportes", menu=opc8_menu)

        reportes_tecnicos = Menu(opc8_menu, tearoff=0)
        reportes_contables = Menu(opc8_menu, tearoff=0)

        opc8_menu.add_cascade(label="Reportes Técnicos", menu=reportes_tecnicos)
        opc8_menu.add_cascade(label="Reportes Contables", menu=reportes_contables)

        reportes_tecnicos.add_command(label="Bienes Ubicados", command=lambda: Window_reporte(valor=1))
        reportes_tecnicos.add_command(label="Bienes de otras entidades", command=lambda: Window_reporte(valor=2))
        reportes_tecnicos.add_command(label="Bienes que no coinciden con la descripción", command=lambda: Window_reporte(valor=3))
        reportes_tecnicos.add_command(label="Bienes para actualización de valor neto", command=lambda: Window_reporte(valor=4))
        reportes_tecnicos.add_command(label="Bienes en desuso o depósitos", command=lambda: Window_reporte(valor=5))
        reportes_tecnicos.add_command(label="Bienes afectados en uso o préstamo", command=lambda: Window_reporte(valor=6))
        reportes_tecnicos.add_command(label="Bienes Faltantes", command=lambda: Window_reporte(valor=7))
        reportes_tecnicos.add_command(label="Bienes Sobrantes", command=lambda: Window_reporte(valor=8))
        reportes_tecnicos.add_command(label="Bienes dados de baja sin disposición", command=lambda: Window_reporte(valor=9))
        reportes_tecnicos.add_command(label="Conciliación de Inventario", command=lambda: Window_reporte(valor=10))
        reportes_tecnicos.add_command(label="Bienes que requieren actualización técnica", command=lambda: Window_reporte(valor=11))

        reportes_contables.add_command(label="Bienes Ubicados por cuenta", command=lambda: Window_reporte(valor=12))
        reportes_contables.add_command(label="Bienes Faltantes por cuenta", command=lambda: Window_reporte(valor=13))
        
        opc9_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Ficha Técnica", menu=opc9_menu)
        opc9_menu.add_command(label="Generar Ficha de Levantamiento", command=lambda: Window_Acta())

        opc10_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Cámara", menu=opc10_menu)
        opc10_menu.add_command(label="Escanear con Cámara", command=lambda: Window_scanner(self))

        opc11_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Servidor", menu=opc11_menu)
        opc11_menu.add_command(label="Probar Conexión", command=lambda: Window_connection_test(self))
        opc11_menu.add_command(label="Iniciar Servidor Socket", command=lambda: Window_server(self))
        opc11_menu.add_command(label="Visualizar Tablas", command=lambda: Window_view_data(self))
        opc11_menu.add_command(label="Fotos del Servidor (asset_photos)", command=lambda: Window_asset_photos(self))

        opc12_menu = Menu(barra_menu, tearoff=0)
        barra_menu.add_cascade(label="Fotos", menu=opc12_menu)
        opc12_menu.add_command(label="Galería de Fotos", command=lambda: Window_asset_photos(self))
        opc12_menu.add_command(label="Asociar / Subir Foto", command=lambda: Window_asset_photos(self).dialogo_asociar_foto())

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

                time.sleep(intervalo_segundos)

        threading.Thread(target=_tarea, daemon=True).start()
