import sqlite3
import threading
import tkinter as tk
import os
from tkinter import Toplevel, ttk
from PIL import ImageTk, Image
from tkinter import messagebox as mb
from db.query import login, login_register, login_user
from gui.gui_app import Frame
from services.sync_service import SyncService
from utils.api_client import ApiManagerAcontarSacClient
from utils.config_helper import set_config
from gui.gui_connection_test import Window_connection_test
from utils.helpers import resource_path


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

		self._crear_interfaz()

	# -------------------------------------------------------------------------
	# CONFIGURACIÓN DE VENTANA Y ESTILOS
	# -------------------------------------------------------------------------
	def _configurar_ventana_raiz(self):
		if not self.root:
			return
		try:
			self.root.configure(bg="#f8fafc")
			w, h = 880, 540
			self.root.update_idletasks()
			sw = self.root.winfo_screenwidth()
			sh = self.root.winfo_screenheight()
			x = (sw - w) // 2
			y = (sh - h) // 2
			self.root.geometry(f"{w}x{h}+{x}+{y}")
			self.root.minsize(780, 480)
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
	# CONSTRUCCIÓN DE INTERFAZ
	# -------------------------------------------------------------------------
	def _crear_interfaz(self):
		# Contenedor principal de dos columnas
		self.FrameU = tk.Frame(self, bg="#f8fafc")
		self.FrameU.pack(fill="both", expand=True)

		# =====================================================================
		# PANEL IZQUIERDO: IMAGEN CORPORATIVA Y BRANDING
		# =====================================================================
		self.Frame2 = tk.Frame(self.FrameU, bg="#0f172a", width=420)
		self.Frame2.pack(side="left", fill="both", expand=True)
		self.Frame2.pack_propagate(False)

		# Encabezado corporativo sobre el panel izquierdo
		f_brand = tk.Frame(self.Frame2, bg="#0f172a", padx=24, pady=20)
		f_brand.pack(fill="x", side="top")

		tk.Label(
			f_brand,
			text="ACONTAR S.A.C.",
			bg="#0f172a",
			fg="#ffffff",
			font=("Segoe UI", 15, "bold"),
			anchor="w"
		).pack(fill="x")

		tk.Label(
			f_brand,
			text="Especialistas en Gestión y Control Patrimonial",
			bg="#0f172a",
			fg="#94a3b8",
			font=("Segoe UI", 9),
			anchor="w"
		).pack(fill="x", pady=(2, 0))

		# Imagen de fondo/ilustración cargada de forma segura
		f_img_left = tk.Frame(self.Frame2, bg="#0f172a", padx=20, pady=10)
		f_img_left.pack(fill="both", expand=True)

		try:
			bkg_path = resource_path(os.path.join("img", "login_.jpg"))
			self.bkg = Image.open(bkg_path)
			self.resize_bkg = self.bkg.resize((380, 340), Image.Resampling.LANCZOS)
			self.img_bkg = ImageTk.PhotoImage(self.resize_bkg)
			self.lblbkg = tk.Label(f_img_left, image=self.img_bkg, bg="#0f172a", bd=0)
			self.lblbkg.pack(expand=True)
		except Exception:
			tk.Label(
				f_img_left,
				text="📦\nSistema de Inventario Físico",
				bg="#0f172a",
				fg="#cbd5e1",
				font=("Segoe UI", 14, "bold"),
				justify="center"
			).pack(expand=True)

		tk.Label(
			self.Frame2,
			text="© Acontar Especialistas Contables S.A.C.",
			bg="#0f172a",
			fg="#64748b",
			font=("Segoe UI", 8),
			pady=12
		).pack(side="bottom")

		# =====================================================================
		# PANEL DERECHO: TARJETA DE INICIO DE SESIÓN
		# =====================================================================
		self.Frame1 = tk.Frame(self.FrameU, bg="#ffffff", width=440, padx=42, pady=28)
		self.Frame1.pack(side="right", fill="both", expand=True)

		# Contenedor centrado verticalmente
		card_inner = tk.Frame(self.Frame1, bg="#ffffff")
		card_inner.pack(fill="x", expand=True)

		# Avatar / Icono de usuario
		self.Frame1_1 = tk.Frame(card_inner, bg="#ffffff")
		self.Frame1_1.pack(fill="x", pady=(0, 10))

		try:
			img_user_path = resource_path(os.path.join("img", "user.png"))
			self.image = Image.open(img_user_path)
			self.resize_img = self.image.resize((84, 84), Image.Resampling.LANCZOS)
			self.img = ImageTk.PhotoImage(self.resize_img)
			self.lblImg = tk.Label(self.Frame1_1, image=self.img, bg="#ffffff")
			self.lblImg.pack(anchor="center")
		except Exception:
			tk.Label(
				self.Frame1_1,
				text="👤",
				bg="#eff6ff",
				fg="#2563eb",
				font=("Segoe UI", 28),
				padx=16,
				pady=6
			).pack(anchor="center")

		tk.Label(
			self.Frame1_1,
			text="Iniciar Sesión",
			bg="#ffffff",
			fg="#0f172a",
			font=("Segoe UI", 16, "bold")
		).pack(anchor="center", pady=(8, 2))

		tk.Label(
			self.Frame1_1,
			text="Ingrese sus credenciales para continuar",
			bg="#ffffff",
			fg="#64748b",
			font=("Segoe UI", 9)
		).pack(anchor="center", pady=(0, 12))

		# Formulario de campos
		self.Frame1_2 = tk.Frame(card_inner, bg="#ffffff")
		self.Frame1_2.pack(fill="x")

		# Campo Usuario
		tk.Label(
			self.Frame1_2,
			text="Usuario",
			bg="#ffffff",
			fg="#334155",
			font=("Segoe UI", 9, "bold"),
			anchor="w"
		).pack(fill="x", pady=(4, 3))

		self.etrUser = ttk.Entry(self.Frame1_2, textvariable=self.user, font=("Segoe UI", 10))
		self.etrUser.pack(fill="x", ipady=4, pady=(0, 10))
		self.etrUser.bind("<Return>", lambda _e: self.etrPass.focus_set())

		# Campo Contraseña
		tk.Label(
			self.Frame1_2,
			text="Contraseña",
			bg="#ffffff",
			fg="#334155",
			font=("Segoe UI", 9, "bold"),
			anchor="w"
		).pack(fill="x", pady=(2, 3))

		self.etrPass = ttk.Entry(self.Frame1_2, textvariable=self.passw, show="●", font=("Segoe UI", 10))
		self.etrPass.pack(fill="x", ipady=4, pady=(0, 6))
		self.etrPass.bind("<Return>", lambda _e: self.validar_ingreso())

		# Checkbox Mostrar contraseña
		chk_pass = ttk.Checkbutton(
			self.Frame1_2,
			text="Mostrar contraseña",
			variable=self.mostrar_pass,
			command=self._toggle_password
		)
		chk_pass.pack(anchor="w", pady=(0, 14))

		# Botón Primario: Entrar
		self.btnEtr = tk.Button(
			self.Frame1_2,
			text="🔐  Ingresar al Sistema",
			bg="#2563eb",
			activebackground="#1d4ed8",
			fg="#ffffff",
			activeforeground="#ffffff",
			font=("Segoe UI", 10, "bold"),
			relief="flat",
			bd=0,
			pady=9,
			cursor="hand2",
			command=self.validar_ingreso
		)
		self.btnEtr.pack(fill="x", pady=(0, 8))

		# Fila de botones secundarios: Registrar y Sincronizar
		f_sec_btns = tk.Frame(self.Frame1_2, bg="#ffffff")
		f_sec_btns.pack(fill="x", pady=(2, 0))

		self.btnReg = tk.Button(
			f_sec_btns,
			text="➕ Registrar Usuario",
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
			text="🔄 Sincronizar Servidor",
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

		# Etiqueta de estado para sincronización automática en el primer login
		self.lblSyncStatus = tk.Label(
			self.Frame1_2,
			textvariable=self.sync_status_var,
			bg="#ffffff",
			fg="#2563eb",
			font=("Segoe UI", 9, "bold"),
			wraplength=350,
			justify="center"
		)
		self.lblSyncStatus.pack(fill="x", pady=(10, 0))

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

		db_path = getattr(self.root, "db_path", self.db_path or "db/orap2022.db")

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
		Frame(
			root=self.root,
			user=name,
			Ndni=Ndni,
			team=team,
			api_client=api_client,
			user_id=user_id
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
						db_path = getattr(self.root, "db_path", self.db_path or "db/orap2022.db")
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
				db_path = getattr(self.root, "db_path", self.db_path or "db/orap2022.db")
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
						user_id=user_id
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
