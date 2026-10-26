import os
import sqlite3
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from services.db_mirror import (
    ensure_outbox_tables,
    reconciliar_tablas_locales_a_servidor,
    sincronizar_cola_completa,
)
from services.sync_service import SyncService
from utils.api_client import ApiManagerAcontarSacClient
from utils.helpers import resource_path


class Window_connection_test(tk.Toplevel):
    """Ventana de gestión de Sincronización Bidireccional (Offline-First)."""

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Centro de Sincronización con el Servidor - AEC S.A.C.")
        self.geometry("760x580")
        self.minsize(680, 480)
        self.resizable(True, True)
        self.configure(bg="#f8fafc")

        try:
            self.iconbitmap(resource_path("img/favicon.ico"))
        except Exception:
            pass

        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_db = os.path.join(base_dir, "..", "db", "orap2022.db")
        self.db_path = getattr(self.root, "db_path", os.path.normpath(default_db))

        self.status = tk.StringVar(value="Listo para sincronizar.")
        self.pending_summary = tk.StringVar(value="Cola pendiente: 0 cambios")

        self._configurar_estilos()
        self._build()
        self._centrar_ventana()
        self._actualizar_estado_inicial()

    def _configurar_estilos(self):
        style = ttk.Style(self)
        style.configure(
            "Sync.TLabelframe",
            background="#ffffff",
            bordercolor="#e2e8f0",
            relief="solid",
            borderwidth=1,
        )
        style.configure(
            "Sync.TLabelframe.Label",
            background="#ffffff",
            foreground="#1e293b",
            font=("Segoe UI", 9, "bold"),
        )

    def _centrar_ventana(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        main_frame = tk.Frame(self, bg="#f8fafc", padx=16, pady=14)
        main_frame.pack(fill="both", expand=True)

        # 1. Encabezado
        header = tk.Frame(main_frame, bg="#f8fafc")
        header.pack(fill="x", pady=(0, 10))

        title_col = tk.Frame(header, bg="#f8fafc")
        title_col.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_col,
            text="Sincronización Bidireccional App ↔ Servidor",
            bg="#f8fafc",
            fg="#0f172a",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            title_col,
            text="Sincroniza inventarios, detalles técnicos, bienes sobrantes, ubicaciones, personal y fotografías",
            bg="#f8fafc",
            fg="#64748b",
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        self.lbl_pending_chip = tk.Label(
            header,
            textvariable=self.pending_summary,
            bg="#eff6ff",
            fg="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=5,
            highlightbackground="#bfdbfe",
            highlightthickness=1,
        )
        self.lbl_pending_chip.pack(side="right", anchor="center")

        # 2. Tarjeta de Controles y Estado
        card_ctrl = ttk.LabelFrame(
            main_frame,
            text="  Acciones de Sincronización  ",
            style="Sync.TLabelframe",
            padding=(14, 10),
        )
        card_ctrl.pack(fill="x", pady=(0, 12))

        btn_row = tk.Frame(card_ctrl, bg="#ffffff")
        btn_row.pack(fill="x", pady=(0, 8))

        self.btn_sync = ttk.Button(
            btn_row,
            text="🔄 Sincronizar Todo (Subir y Descargar)",
            command=self.ejecutar_sincronizacion,
        )
        self.btn_sync.pack(side="left", padx=(0, 8))

        self.btn_push = ttk.Button(
            btn_row,
            text="📤 Enviar Cola Local",
            command=self.enviar_cola_local,
        )
        self.btn_push.pack(side="left", padx=(0, 8))

        self.btn_ping = ttk.Button(
            btn_row,
            text="📡 Probar Conexión",
            command=self.probar_conexion,
        )
        self.btn_ping.pack(side="left")

        status_row = tk.Frame(card_ctrl, bg="#f1f5f9", padx=10, pady=6)
        status_row.pack(fill="x")

        tk.Label(
            status_row,
            textvariable=self.status,
            bg="#f1f5f9",
            fg="#0f172a",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")

        # 3. Bitácora de operaciones
        card_log = ttk.LabelFrame(
            main_frame,
            text="  Bitácora de Operaciones  ",
            style="Sync.TLabelframe",
            padding=(10, 8),
        )
        card_log.pack(fill="both", expand=True)

        self.log_area = scrolledtext.ScrolledText(
            card_log,
            height=16,
            wrap="word",
            state="disabled",
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#ffffff",
            font=("Consolas", 9),
            relief="flat",
            padx=10,
            pady=8,
        )
        self.log_area.pack(fill="both", expand=True)

    def log(self, text):
        """Escribe mensajes en la bitácora de la interfaz."""
        if not self.winfo_exists():
            return
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{text}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _refrescar_conteo_cola(self, conn=None):
        """Actualiza el chip con el conteo de cambios pendientes en SQLite."""
        close_after = False
        try:
            if conn is None:
                conn = sqlite3.connect(self.db_path)
                close_after = True
            cur = conn.cursor()
            ensure_outbox_tables(cur)
            cur.execute("SELECT COUNT(*) FROM inventory_sync_outbox WHERE status = 'pending'")
            n_inv = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sync_mutations_outbox WHERE status = 'pending'")
            n_mut = cur.fetchone()[0]
            total = n_inv + n_mut
            self.pending_summary.set(f"📤 Cola pendiente: {total} ({n_inv} inv. / {n_mut} edic.)")
        except Exception:
            pass
        finally:
            if close_after and conn:
                conn.close()

    def _actualizar_estado_inicial(self):
        """Verifica la base de datos al abrir la ventana."""
        try:
            db_conn = sqlite3.connect(self.db_path)
            sync_service = SyncService(db_conn)
            self._refrescar_conteo_cola(db_conn)

            if sync_service.is_initial_sync_done():
                last_sync = sync_service.get_last_sync_timestamp()
                self.status.set(f"Estado: Base de datos sincronizada | Último sync: {last_sync}")
                self.log(f"✅ Base de datos inicializada previamente ({last_sync}).")
            else:
                self.status.set("Estado: Requiere Sincronización Inicial")
                self.log("⚠️ La base de datos local requiere Initial Sync. Presione 'Sincronizar Todo'.")

            db_conn.close()
        except Exception as e:
            self.log(f"❌ Error al consultar SQLite: {e}")

    def _set_buttons_state(self, state: str):
        for btn in (self.btn_sync, self.btn_push, self.btn_ping):
            btn.configure(state=state)

    def probar_conexion(self):
        """Lanza un hilo para verificar respuesta del servidor."""
        self._set_buttons_state("disabled")
        self.status.set("Comprobando servidor...")
        threading.Thread(target=self._hilo_ping, daemon=True).start()

    def _hilo_ping(self):
        try:
            client = ApiManagerAcontarSacClient(timeout=10)
            res = client.ping()
            self.after(0, lambda: self.log(f"📡 Respuesta servidor: {res}"))
            self.after(0, lambda: self.status.set("Servidor en línea."))
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Error de conexión: {e}"))
            self.after(0, lambda: self.status.set("Servidor no disponible."))
        finally:
            self.after(0, lambda: self._set_buttons_state("normal"))

    def enviar_cola_local(self):
        """Envía únicamente los cambios pendientes locales al servidor."""
        self._set_buttons_state("disabled")
        self.status.set("Enviando cambios locales pendientes al servidor...")
        threading.Thread(target=self._hilo_enviar_cola, daemon=True).start()

    def _hilo_enviar_cola(self):
        try:
            db_conn = sqlite3.connect(self.db_path)
            reconciliar_tablas_locales_a_servidor(db_conn)
            db_conn.close()

            client = ApiManagerAcontarSacClient(timeout=30)
            res = sincronizar_cola_completa(client, limite=200)
            synced = res.get("synced", 0)
            pending = res.get("pending", 0)

            self.after(0, self._refrescar_conteo_cola)
            if pending == 0:
                self.after(0, lambda: self.log(f"📤 Cola enviada con éxito ({synced} cambios sincronizados)."))
                self.after(0, lambda: self.status.set("Cola local enviada completamente."))
            else:
                self.after(0, lambda: self.log(f"⚠️ Se enviaron {synced} cambios; quedan {pending} pendientes."))
                self.after(0, lambda: self.status.set(f"Pendientes de envío: {pending} registros."))
        except Exception as e:
            self.after(0, lambda: self.log(f"❌ Error al enviar cola local: {e}"))
            self.after(0, lambda: self.status.set("Error al enviar cola local."))
        finally:
            self.after(0, lambda: self._set_buttons_state("normal"))

    def ejecutar_sincronizacion(self):
        """Bloquea botones e inicia el proceso de sincronización bidireccional."""
        self._set_buttons_state("disabled")
        threading.Thread(target=self._hilo_sincronizacion, daemon=True).start()

    def _hilo_sincronizacion(self):
        try:
            db_conn = sqlite3.connect(self.db_path)
            sync_service = SyncService(db_conn)
            client = ApiManagerAcontarSacClient(timeout=120)

            if not sync_service.is_initial_sync_done():
                self.after(0, lambda: self.status.set("Descargando catálogo completo (Initial Sync)..."))
                self.after(0, lambda: self.log("🚀 Iniciando descarga masiva e inserción en SQLite..."))
                resultado = sync_service.execute_initial_sync(client)
            else:
                self.after(0, lambda: self.status.set("Sincronizando cambios locales y descargando novedades..."))
                self.after(0, lambda: self.log("⚡ Subiendo cola local y consultando novedades en el servidor..."))
                resultado = sync_service.execute_sync_changes(client)

            db_conn.close()
            self.after(0, self._refrescar_conteo_cola)
            self.after(0, self._finalizar_sincronizacion, resultado)

        except Exception as e:
            error_res = {"status": "error", "message": f"Excepción en hilo: {str(e)}"}
            self.after(0, self._finalizar_sincronizacion, error_res)

    def _finalizar_sincronizacion(self, resultado):
        st = resultado.get("status")
        if st == "success":
            self.log(f"🎉 ¡ÉXITO! {resultado.get('message')}")
            self.status.set("Sincronización completada con éxito.")
        elif st == "deferred":
            self.log(f"⚠️ {resultado.get('message')}")
            self.status.set("Sincronización diferida: cambios locales pendientes.")
        else:
            self.log(f"❌ ERROR: {resultado.get('message')}")
            self.status.set("Error durante la sincronización.")

        self._set_buttons_state("normal")
