import sqlite3
import threading
import tkinter as tk
import os
from tkinter import Toplevel, ttk
from PIL import ImageTk, Image, ImageOps, ImageDraw
from tkinter import messagebox as mb
from db.query import login, login_register, login_user
from gui.gui_app import Frame
from services.sync_service import SyncService
from utils.api_client import ApiManagerAcontarSacClient
from utils.config_helper import set_config
from gui.gui_connection_test import Window_connection_test
from utils.helpers import resource_path
from utils.project_manager import ProjectManager
from db.conex import set_database_path
from db.init_db import init_db


class Frame_login(ttk.Frame):
	"""Pantalla de inicio de sesión y sincronización inicial del sistema."""

	def __init__(self, root=None, db_path=None, sync_realizado=False, api_client=None, *args, **kwargs):
		super().__init__(root, *args, **kwargs)
		self.root = root
		self.db_path = db_path
		self.sync_realizado = sync_realizado
		self.api_client = api_client or getattr(root, 'api_client', None)

		self._configurar_ventana_raiz()
		self._configurar_estilos()
		self.pack(fill="both", expand=True)

		# Variables de registro de usuario
		self.vNomb = tk.StringVar()
		self.vApat = tk.StringVar()
		self.vAmat = tk.StringVar()
		self.vNdni = tk.StringVar()
		self.vUser = tk.StringVar()
		self.vPass = tk.StringVar()
		self.vEqui = tk.StringVar()

		# Variables de login
		self.user = tk.StringVar()
		self.passw = tk.StringVar()
		self.mostrar_pass = tk.BooleanVar(value=False)
		self.sync_status_var = tk.StringVar(value="")

		# Configuración multi-proyecto
		self.proyectos_dict = ProjectManager.load_projects()
		active_id = ProjectManager.get_active_project_id()
		nombre_activo = self.proyectos_dict.get(active_id, {}).get("name", "Proyecto 1 (api.acontarsac.com)")
		self.proyecto_activo_var = tk.StringVar(value=nombre_activo)

		self._crear_interfaz()

	# -------------------------------------------------------------------------
	# CONFIGURACIÓN DE VENTANA Y ESTILOS
	# -------------------------------------------------------------------------
	def _configurar_ventana_raiz(self):
		if not self.root:
			return
		try:
			self.root.configure(bg="#0f172a")
			w, h = 960, 580
			self.root.update_idletasks()
			sw = self.root.winfo_screenwidth()
			sh = self.root.winfo_screenheight()
			x = (sw - w) // 2
			y = (sh - h) // 2
			self.root.geometry(f"{w}x{h}+{x}+{y}")
			self.root.minsize(860, 520)
		except Exception:
			pass

	def _configurar_estilos(self):
		style = ttk.Style(self)
		style.configure("Login.TLabelframe",
			background="#ffffff",
			relief="solid",
			borderwidth=1,
			bordercolor="#e2e8f0"
		)
		style.configure("Login.TLabelframe.Label",
			background="#ffffff",
			foreground="#334155",
			font=("Segoe UI", 9, "bold")
		)

	# -------------------------------------------------------------------------
	# CONSTRUCCIÓN DE INTERFAZ (OPCIÓN 2: HERO BACKGROUND + FLOATING CARD)
	# -------------------------------------------------------------------------
	def _crear_interfaz(self):
		w_init, h_init = 960, 580

		# Canvas que ocupa el 100% de la ventana con la foto de fondo
		self.canvas_bg = tk.Canvas(
			self,
			width=w_init,
			height=h_init,
			bg="#0f172a",
			highlightthickness=0,
			bd=0
		)
		self.canvas_bg.pack(fill="both", expand=True)

		# Renderizado de fondo con la foto y efectos de contraste
		self._cargar_fondo_canvas(w_init, h_init)

		# Branding y propuesta de valor sobre la foto (lado izquierdo)
		self.txt_tag = self.canvas_bg.create_text(
			60, 140,
			text="SISTEMA DE CONTROL PATRIMONIAL",
			fill="#38bdf8",
			font=("Segoe UI", 9, "bold"),
			anchor="w"
		)
		self.txt_title = self.canvas_bg.create_text(
			60, 185,
			text="ACONTAR S.A.C.",
			fill="#ffffff",
			font=("Segoe UI", 26, "bold"),
			anchor="w"
		)
		self.txt_desc = self.canvas_bg.create_text(
			60, 235,
			text="Especialistas en Gestión, Inventario Físico\ny Conciliación Patrimonial de Activos.",
			fill="#e2e8f0",
			font=("Segoe UI", 12),
			anchor="w"
		)
		self.txt_feat1 = self.canvas_bg.create_text(
			60, 305,
			text="⚡  Toma de inventario rápida y sin errores",
			fill="#cbd5e1",
			font=("Segoe UI", 10),
			anchor="w"
		)
		self.txt_feat2 = self.canvas_bg.create_text(
			60, 340,
			text="🔄  Sincronización híbrida (Online / Offline)",
			fill="#cbd5e1",
			font=("Segoe UI", 10),
			anchor="w"
		)
		self.txt_feat3 = self.canvas_bg.create_text(
			60, 375,
			text="🏷️  Impresión y control de etiquetas de activos",
			fill="#cbd5e1",
			font=("Segoe UI", 10),
			anchor="w"
		)
		self.txt_copy = self.canvas_bg.create_text(
			60, 535,
			text="© Acontar Especialistas Contables S.A.C. Todos los derechos reservados.",
			fill="#94a3b8",
			font=("Segoe UI", 8),
			anchor="w"
		)

		# =====================================================================
		# TARJETA BLANCA FLOTANTE (LADO DERECHO)
		# =====================================================================
		card_w, card_h = 380, 520
		self.card = tk.Frame(
			self.canvas_bg,
			bg="#ffffff",
			padx=32,
			pady=22,
			highlightbackground="#cbd5e1",
			highlightthickness=1,
			bd=0
		)

		# Encabezado con avatar
		f_card_top = tk.Frame(self.card, bg="#ffffff")
		f_card_top.pack(fill="x", pady=(0, 6))

		try:
			img_user_path = resource_path(os.path.join("img", "user.png"))
			self.image = Image.open(img_user_path)
			self.resize_img = self.image.resize((60, 60), Image.Resampling.LANCZOS)
			self.img = ImageTk.PhotoImage(self.resize_img)
			self.lblImg = tk.Label(f_card_top, image=self.img, bg="#ffffff")
			self.lblImg.pack(anchor="center")
		except Exception:
			tk.Label(
				f_card_top,
				text="👤",
				bg="#eff6ff",
				fg="#2563eb",
				font=("Segoe UI", 22),
				padx=12,
				pady=2
			).pack(anchor="center")

		tk.Label(
			f_card_top,
			text="Iniciar Sesión",
			bg="#ffffff",
			fg="#0f172a",
			font=("Segoe UI", 15, "bold")
		).pack(anchor="center", pady=(4, 1))

		tk.Label(
			f_card_top,
			text="Ingrese sus credenciales para continuar",
			bg="#ffffff",
			fg="#64748b",
			font=("Segoe UI", 9)
		).pack(anchor="center", pady=(0, 4))

		# Campos del formulario
		f_card_body = tk.Frame(self.card, bg="#ffffff")
		f_card_body.pack(fill="x")

		# Selector de Proyecto / Servidor
		f_sel_proj = tk.Frame(f_card_body, bg="#ffffff")
		f_sel_proj.pack(fill="x", pady=(0, 5))

		tk.Label(
			f_sel_proj,
			text="Proyecto / Servidor:",
			bg="#ffffff",
			fg="#334155",
			font=("Segoe UI", 8, "bold"),
			anchor="w"
		).pack(fill="x", pady=(0, 2))

		proj_names = [p["name"] for p in self.proyectos_dict.values()]
		self.cb_proyecto = ttk.Combobox(
			f_sel_proj,
			textvariable=self.proyecto_activo_var,
			values=proj_names,
			state="readonly",
			font=("Segoe UI", 9)
		)
		self.cb_proyecto.pack(fill="x", ipady=2)
		self.cb_proyecto.bind("<<ComboboxSelected>>", self._al_cambiar_proyecto)

		# Etiqueta que muestra en pantalla la BD local activa
		db_actual_nombre = os.path.basename(self.db_path or ProjectManager.get_active_db_path())
		self.lbl_info_db = tk.Label(
			f_sel_proj,
			text=f"📁 Base local: db/{db_actual_nombre}",
			bg="#ffffff",
			fg="#2563eb",
			font=("Segoe UI", 8, "bold"),
			anchor="w"
		)
		self.lbl_info_db.pack(fill="x", pady=(3, 0))

		tk.Label(
			f_card_body,
			text="Usuario",
			bg="#ffffff",
			fg="#334155",
			font=("Segoe UI", 9, "bold"),
			anchor="w"
		).pack(fill="x", pady=(2, 2))

		self.etrUser = ttk.Entry(f_card_body, textvariable=self.user, font=("Segoe UI", 10))
		self.etrUser.pack(fill="x", ipady=4, pady=(0, 8))
		self.etrUser.bind("<Return>", lambda _e: self.etrPass.focus_set())

		tk.Label(
			f_card_body,
			text="Contraseña",
			bg="#ffffff",
			fg="#334155",
			font=("Segoe UI", 9, "bold"),
			anchor="w"
		).pack(fill="x", pady=(2, 3))

		self.etrPass = ttk.Entry(f_card_body, textvariable=self.passw, show="●", font=("Segoe UI", 10))
		self.etrPass.pack(fill="x", ipady=4, pady=(0, 5))
		self.etrPass.bind("<Return>", lambda _e: self.validar_ingreso())

		chk_pass = ttk.Checkbutton(
			f_card_body,
			text="Mostrar contraseña",
			variable=self.mostrar_pass,
			command=self._toggle_password
		)
		chk_pass.pack(anchor="w", pady=(0, 10))

		self.btnEtr = tk.Button(
			f_card_body,
			text="🔐  Ingresar al Sistema",
			bg="#2563eb",
			activebackground="#1d4ed8",
			fg="#ffffff",
			activeforeground="#ffffff",
			font=("Segoe UI", 10, "bold"),
			relief="flat",
			bd=0,
			pady=8,
			cursor="hand2",
			command=self.validar_ingreso
		)
		self.btnEtr.pack(fill="x", pady=(0, 8))

		f_sec_btns = tk.Frame(f_card_body, bg="#ffffff")
		f_sec_btns.pack(fill="x", pady=(2, 0))

		self.btnReg = tk.Button(
			f_sec_btns,
			text="➕ Registrar",
			bg="#f1f5f9",
			activebackground="#e2e8f0",
			fg="#334155",
			activeforeground="#0f172a",
			font=("Segoe UI", 9, "bold"),
			relief="solid",
			bd=1,
			pady=6,
			cursor="hand2",
			command=self.abrir_ventana
		)
		self.btnReg.pack(side="left", fill="x", expand=True, padx=(0, 4))

		self.btnSync = tk.Button(
			f_sec_btns,
			text="🔄 Sincronizar",
			bg="#1e293b",
			activebackground="#0f172a",
			fg="#ffffff",
			activeforeground="#ffffff",
			font=("Segoe UI", 9, "bold"),
			relief="flat",
			bd=0,
			pady=7,
			cursor="hand2",
			command=self.abrir_sincronizacion
		)
		self.btnSync.pack(side="right", fill="x", expand=True, padx=(4, 0))

		self.lblSyncStatus = tk.Label(
			f_card_body,
			textvariable=self.sync_status_var,
			bg="#ffffff",
			fg="#2563eb",
			font=("Segoe UI", 9, "bold"),
			wraplength=310,
			justify="center"
		)
		self.lblSyncStatus.pack(fill="x", pady=(8, 0))

		# Incrustar la tarjeta flotante sobre el canvas
		card_x = w_init - card_w - 50
		card_y = (h_init - card_h) // 2
		self.card_window = self.canvas_bg.create_window(card_x, card_y, window=self.card, anchor="nw")

		# Manejador dinámico de reposicionamiento
		self.canvas_bg.bind("<Configure>", self._al_redimensionar_canvas)

		self.etrUser.focus_set()

	def _cargar_fondo_canvas(self, w: int, h: int):
		"""Carga la foto como fondo panorámico ocupando toda la ventana con efectos de contraste."""
		try:
			bkg_path = resource_path(os.path.join("img", "login_.jpg"))
			if not os.path.exists(bkg_path):
				bkg_path = resource_path(os.path.join("img", "login__.jpg"))

			if os.path.exists(bkg_path):
				raw_img = Image.open(bkg_path).convert("RGBA")
				fitted = ImageOps.fit(raw_img, (w, h), method=Image.Resampling.LANCZOS)

				scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
				draw = ImageDraw.Draw(scrim)

				# Degradado horizontal: zona izquierda oscurecida para texto, zona derecha visible
				for x in range(w):
					if x < 520:
						alpha = int(210 - (135 * (x / 520)))
					else:
						alpha = 75
					draw.line([(x, 0), (x, h)], fill=(15, 23, 42, alpha))

				composited = Image.alpha_composite(fitted, scrim).convert("RGB")
				self.img_bkg = ImageTk.PhotoImage(composited)
				self.canvas_bg.create_image(0, 0, image=self.img_bkg, anchor="nw")
		except Exception as ex:
			print(f"Nota: No se pudo cargar el fondo panorámico: {ex}")

	def _al_redimensionar_canvas(self, event):
		if not self.winfo_exists() or not hasattr(self, "card_window"):
			return
		w, h = event.width, event.height
		card_w = 380
		card_x = max(w - card_w - 50, w // 2)
		card_y = max((h - 520) // 2, 20)
		self.canvas_bg.coords(self.card_window, card_x, card_y)
		if hasattr(self, "txt_copy"):
			self.canvas_bg.coords(self.txt_copy, 60, h - 30)

	def _al_cambiar_proyecto(self, _event=None):
		nombre_sel = self.proyecto_activo_var.get()
		target_proj = None
		for p in self.proyectos_dict.values():
			if p["name"] == nombre_sel:
				target_proj = p
				break

		if not target_proj:
			return

		# 1. Guardar proyecto activo en config.ini
		ProjectManager.set_active_project(target_proj["id"])

		# 2. Actualizar ruta de base de datos activa
		nueva_db = ProjectManager.get_active_db_path()
		self.db_path = nueva_db
		if self.root:
			self.root.db_path = nueva_db
		set_database_path(nueva_db)

		# 3. Inicializar esquema en la BD si no existe aún
		try:
			conn = sqlite3.connect(nueva_db)
			init_db(conn)
			sync_service = SyncService(conn)
			self.sync_realizado = sync_service.is_initial_sync_done()
			conn.close()
		except Exception as ex_db:
			print(f"Nota al inicializar BD de proyecto: {ex_db}")
			self.sync_realizado = False

		# 4. Actualizar cliente API con la nueva URL del proyecto
		self.api_client = ApiManagerAcontarSacClient(
			base_url=target_proj["api_url"],
			photos_base_url=target_proj.get("photos_url")
		)
		if self.root:
			self.root.api_client = self.api_client

		# 5. Notificar estado al usuario y actualizar etiqueta de BD local
		db_nombre = os.path.basename(nueva_db)
		if hasattr(self, 'lbl_info_db'):
			self.lbl_info_db.config(text=f"📁 Base local: db/{db_nombre}")

		if not self.sync_realizado:
			self.sync_status_var.set(f"🔄 Conectado a {target_proj['name']}.\nPrimer uso: se descargará la base de datos.")
		else:
			self.sync_status_var.set(f"✓ Conectado a: {target_proj['name']}")

		self.user.set("")
		self.passw.set("")
		self.etrUser.focus_set()

	def _toggle_password(self):
		self.etrPass.config(show="" if self.mostrar_pass.get() else "●")

	# -------------------------------------------------------------------------
	# LÓGICA DE SINCRONIZACIÓN Y AUTENTICACIÓN
	# -------------------------------------------------------------------------
	def abrir_sincronizacion(self):
		"""Abre la ventana de sincronización para conectar con el servidor directamente desde el login."""
		self.root.api_client = getattr(self, 'api_client', None) or getattr(self.root, 'api_client', None)
		win_sync = Window_connection_test(root=self.root)
		win_sync.grab_set()

	def _set_login_controls_state(self, state: str):
		"""Habilita o deshabilita los controles del login durante la sincronización inicial."""
		for widget in (self.etrUser, self.etrPass, self.btnEtr, self.btnReg, self.btnSync):
			try:
				widget.configure(state=state)
			except Exception:
				pass

	def _iniciar_initial_sync_automatico(self, name, Ndni, team, api_client, user_id):
		"""Ejecuta automáticamente el Initial Sync al loguearse por primera vez y luego abre el sistema."""
		self._set_login_controls_state("disabled")
		self.btnEtr.configure(text="⏳ Sincronizando base de datos...")
		self.sync_status_var.set("🔄 Primer inicio de sesión: descargando datos del servidor (Initial Sync)...")

		db_path = getattr(self.root, "db_path", None) or self.db_path or ProjectManager.get_active_db_path()

		def _worker():
			try:
				conn = sqlite3.connect(db_path)
				sync_service = SyncService(conn)
				client = api_client or ApiManagerAcontarSacClient(timeout=120)
				resultado = sync_service.execute_initial_sync(client)
				conn.close()
			except Exception as e:
				resultado = {"status": "error", "message": str(e)}

			if self.winfo_exists():
				self.after(0, lambda: self._finalizar_initial_sync_automatico(
					resultado, name, Ndni, team, api_client, user_id
				))

		threading.Thread(target=_worker, daemon=True).start()

	def _finalizar_initial_sync_automatico(self, resultado, name, Ndni, team, api_client, user_id):
		"""Completa la transición al sistema principal tras finalizar el Initial Sync automático."""
		if resultado.get("status") == "error":
			mb.showwarning(
				title="Aviso de Sincronización Inicial",
				message=f"No se pudo completar la descarga inicial automática:\n{resultado.get('message')}\n\n"
				        "Ingresando al sistema con los datos locales disponibles.",
				parent=self.root
			)

		self.pack_forget()
		active_db = getattr(self.root, "db_path", None) or self.db_path or ProjectManager.get_active_db_path()
		Frame(
			root=self.root,
			user=name,
			Ndni=Ndni,
			team=team,
			api_client=api_client,
			user_id=user_id,
			db_path=active_db
		)

	def validar_ingreso(self):
		u = self.user.get().strip()
		p = self.passw.get().strip()

		if not u or not p:
			mb.showwarning(message="Por favor ingrese usuario y contraseña.", title="Atención", parent=self.root)
			return

		try:
			r = login(u, p)
			if r != 1:
				# Si aún no está en la BD local (ej. primer login), validar en línea contra el servidor
				api_client = getattr(self, 'api_client', None) or getattr(self.root, 'api_client', None) or ApiManagerAcontarSacClient(timeout=20)
				try:
					res_api = api_client.validate_credentials(u, p)
					if res_api and res_api.get("success"):
						user_data = res_api.get("data", {})
						db_path = getattr(self.root, "db_path", None) or self.db_path or ProjectManager.get_active_db_path()
						conn = sqlite3.connect(db_path)
						cur = conn.cursor()
						cur.execute("""
							INSERT OR REPLACE INTO usuarios (
								id, usuario, password, Nombres, APat, AMat, dni, equipo
							) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
						""", (
							user_data.get("id"),
							user_data.get("usuario", u),
							p,
							user_data.get("nombres", ""),
							user_data.get("apellidos", ""),
							"",
							str(user_data.get("id", "")),
							user_data.get("rol", "")
						))
						conn.commit()
						conn.close()
						r = login(u, p)
				except Exception as ex_net:
					print(f"Intento de autenticación en línea no completado: {ex_net}")

			if r == 1:
				j = login_user(u, p)
				name = j[0][0]
				Ndni = j[0][1]
				team = j[0][2]
				user_id = j[0][3] if len(j[0]) > 3 else 1

				# 1. Obtener la referencia de api_client
				api_client = getattr(self, 'api_client', None) or getattr(self.root, 'api_client', None)

				# 2. Obtener la ruta de la BD registrada en root
				db_path = getattr(self.root, "db_path", None) or self.db_path or ProjectManager.get_active_db_path()
				db_conn = sqlite3.connect(db_path)

				# 3. Persistir usuario activo en app_config
				set_config(db_conn, "logged_user_name", str(name))
				set_config(db_conn, "logged_user_dni", str(Ndni))
				set_config(db_conn, "logged_user_team", str(team))
				set_config(db_conn, "logged_user_id", str(user_id))

				# 4. Evaluar estado de la sincronización inicial
				sync_service = SyncService(db_conn)
				sync_listo = sync_service.is_initial_sync_done()
				db_conn.close()

				# 5. Si es el primer login (no se ha hecho initial_sync), ejecutarlo automáticamente sin preguntar
				if not sync_listo:
					self._iniciar_initial_sync_automatico(name, Ndni, team, api_client, user_id)
				else:
					self.pack_forget()
					Frame(
						root=self.root,
						user=name,
						Ndni=Ndni,
						team=team,
						api_client=api_client,
						user_id=user_id,
						db_path=db_path
					)
			else:
				mb.showwarning(message="Usuario o contraseña incorrectos.", title="Atención", parent=self.root)

		except Exception as e:
			mb.showerror(message=f"Error inesperado al iniciar sesión:\n{str(e)}", title="Error", parent=self.root)

	# -------------------------------------------------------------------------
	# MODAL DE REGISTRO DE USUARIO
	# -------------------------------------------------------------------------
	def abrir_ventana(self):
		self.reg_win = Toplevel(self)
		self.reg_win.title("Registrar Nuevo Usuario — Acontar S.A.C.")
		self.reg_win.geometry("420x440")
		self.reg_win.resizable(False, False)
		self.reg_win.configure(bg="#f8fafc")
		self.reg_win.transient(self.root)
		self.reg_win.grab_set()

		try:
			self.reg_win.iconbitmap(resource_path("img/favicon.ico"))
		except Exception:
			pass

		# Centrar modal
		self.reg_win.update_idletasks()
		x = (self.reg_win.winfo_screenwidth() - 420) // 2
		y = (self.reg_win.winfo_screenheight() - 440) // 2
		self.reg_win.geometry(f"420x440+{x}+{y}")

		card = ttk.LabelFrame(
			self.reg_win,
			text=" 👤 Datos del Nuevo Usuario ",
			style="Login.TLabelframe",
			padding=16
		)
		card.pack(fill="both", expand=True, padx=14, pady=14)

		campos = [
			("Nombres:", self.vNomb, False),
			("Apellido Paterno:", self.vApat, False),
			("Apellido Materno:", self.vAmat, False),
			("DNI:", self.vNdni, False),
			("Usuario:", self.vUser, False),
			("Contraseña:", self.vPass, True),
			("Equipo:", self.vEqui, False),
		]

		for idx, (lbl_txt, var, es_pass) in enumerate(campos):
			ttk.Label(card, text=lbl_txt, font=("Segoe UI", 9)).grid(row=idx, column=0, padx=(2, 8), pady=6, sticky="w")
			etr = ttk.Entry(card, textvariable=var, show="●" if es_pass else "", font=("Segoe UI", 9))
			etr.grid(row=idx, column=1, padx=2, pady=6, sticky="ew")
			if idx == 0:
				etr.focus_set()

		card.columnconfigure(1, weight=1)

		f_btns = tk.Frame(card, bg="#ffffff")
		f_btns.grid(row=len(campos), column=0, columnspan=2, sticky="ew", pady=(16, 2))

		ttk.Button(f_btns, text="Cancelar", command=self.reg_win.destroy).pack(side="right", padx=(6, 0))
		ttk.Button(f_btns, text="💾 Registrar Usuario", command=self.registrar_user).pack(side="right")

	def registrar_user(self):
		u = self.vUser.get().strip()
		p = self.vPass.get().strip()
		nomb = self.vNomb.get().strip()

		if not u or not p or not nomb:
			mb.showwarning(
				title="Atención",
				message="Complete al menos Nombres, Usuario y Contraseña.",
				parent=getattr(self, "reg_win", self.root)
			)
			return

		try:
			login_register(
				u,
				p,
				nomb,
				self.vApat.get().strip(),
				self.vAmat.get().strip(),
				self.vNdni.get().strip(),
				self.vEqui.get().strip()
			)
			mb.showinfo(
				message="Usuario registrado exitosamente.",
				title="Acontar S.A.C.",
				parent=getattr(self, "reg_win", self.root)
			)
			for var in (self.vNomb, self.vApat, self.vAmat, self.vNdni, self.vUser, self.vPass, self.vEqui):
				var.set("")
			if hasattr(self, "reg_win") and self.reg_win.winfo_exists():
				self.reg_win.destroy()
		except Exception as e:
			mb.showerror(
				message=f"No se pudo registrar el usuario:\n{e}",
				title="¡Atención!",
				parent=getattr(self, "reg_win", self.root)
			)
