import os
import sqlite3
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from services.sync_service import SyncService
from utils.api_client import ApiManagerAcontarSacClient


class Window_connection_test(tk.Toplevel):
    """Ventana de gestión de Sincronización (Offline-First)."""

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Sincronización de Datos - AcontarSoft")
        self.geometry("640x500")
        self.resizable(True, True)

        # Obtener ruta de BD desde root o usar ruta por defecto en CODIGO/db/orap2022.db
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_db = os.path.join(base_dir, "..", "db", "orap2022.db")
        self.db_path = getattr(self.root, "db_path", os.path.normpath(default_db))

        self.status = tk.StringVar(value="Listo para sincronizar.")

        self._build()
        self._actualizar_estado_inicial()

    def _build(self):
        content = ttk.Frame(self, padding=15)
        content.pack(fill="both", expand=True)

        # Panel superior de control
        frame_controls = ttk.Frame(content)
        frame_controls.pack(fill="x", pady=(0, 10))

        self.btn_sync = ttk.Button(
            frame_controls, text="🔄 Sincronizar Datos", command=self.ejecutar_sincronizacion
        )
        self.btn_sync.pack(side="left", padx=(0, 5))

        self.btn_ping = ttk.Button(
            frame_controls, text="📡 Probar Conexión", command=self.probar_conexion
        )
        self.btn_ping.pack(side="left")

        # Estado actual
        ttk.Label(content, textvariable=self.status, font=("Arial", 9, "bold")).pack(
            anchor="w", pady=(5, 5)
        )

        # Consola de registros / resultados
        ttk.Label(content, text="Bitácora de operaciones:").pack(anchor="w", pady=(5, 2))
        self.log_area = scrolledtext.ScrolledText(content, height=18, wrap="word", state="disabled")
        self.log_area.pack(fill="both", expand=True)

    def log(self, text):
        """Escribe mensajes en el cuadro de texto de la interfaz."""
        self.log_area.configure(state="normal")
        self.log_area.insert("end", f"{text}\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")

    def _actualizar_estado_inicial(self):
        """Verifica la base de datos al abrir la ventana."""
        try:
            db_conn = sqlite3.connect(self.db_path)
            sync_service = SyncService(db_conn)
            
            if sync_service.is_initial_sync_done():
                last_sync = sync_service.get_last_sync_timestamp()
                self.status.set(f"Estado: Base de datos lista | Último sync: {last_sync}")
                self.log(f"✅ Base de datos inicializada previamente ({last_sync}).")
            else:
                self.status.set("Estado: Requiere Sincronización Inicial")
                self.log("⚠️ La base de datos local está vacía. Presione 'Sincronizar Datos'.")
            
            db_conn.close()
        except Exception as e:
            self.log(f"❌ Error al consultar SQLite: {e}")

    def probar_conexion(self):
        """Lanza un hilo para verificar respuesta del servidor."""
        self.btn_ping.configure(state="disabled")
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
            self.after(0, lambda: self.btn_ping.configure(state="normal"))

    def ejecutar_sincronizacion(self):
        """Bloquea la UI e inicia el proceso de sincronización en segundo plano."""
        self.btn_sync.configure(state="disabled")
        self.btn_ping.configure(state="disabled")
        threading.Thread(target=self._hilo_sincronizacion, daemon=True).start()

    def _hilo_sincronizacion(self):
        try:
            db_conn = sqlite3.connect(self.db_path)
            sync_service = SyncService(db_conn)
            client = ApiManagerAcontarSacClient(timeout=120)

            # EVALUACIÓN AUTOMÁTICA
            if not sync_service.is_initial_sync_done():
                self.after(0, lambda: self.status.set("Descargando catálogo completo (Initial Sync)..."))
                self.after(0, lambda: self.log("🚀 Iniciando descarga masiva e inserción en SQLite..."))
                
                resultado = sync_service.execute_initial_sync(client)
            else:
                self.after(0, lambda: self.status.set("Buscando cambios recientes (Sync Changes)..."))
                self.after(0, lambda: self.log("⚡ Consultando novedades en el servidor..."))
                
                resultado = sync_service.execute_sync_changes(client)

            db_conn.close()

            # Mostrar resultado final en la interfaz
            self.after(0, self._finalizar_sincronizacion, resultado)

        except Exception as e:
            error_res = {"status": "error", "message": f"Excepción en hilo: {str(e)}"}
            self.after(0, self._finalizar_sincronizacion, error_res)

    def _finalizar_sincronizacion(self, resultado):
        if resultado.get("status") == "success":
            self.log(f"🎉 ¡ÉXITO! {resultado.get('message')}")
            self.status.set("Sincronización completada con éxito.")
        else:
            self.log(f"❌ ERROR: {resultado.get('message')}")
            self.status.set("Error durante la sincronización.")

        self.btn_sync.configure(state="normal")
        self.btn_ping.configure(state="normal")