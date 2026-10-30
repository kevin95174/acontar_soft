import os
import sqlite3
import tkinter as tk
from tkinter import messagebox as mb
import sys
import traceback

from utils.helpers import resource_path

# 1. Definición de la ruta base y del entorno de ejecución
if getattr(sys, 'frozen', False):
    # Ejecutándose como ejecutable compilado con PyInstaller
    BASE_DIR = os.path.dirname(sys.executable)
    # Asegurar que el directorio de trabajo activo sea la carpeta del ejecutable
    os.chdir(BASE_DIR)
else:
    # Ejecutándose en entorno de desarrollo Python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "db", "orap2022.db")
API_BASE_URL = "https://api.acontarsac.com"


def main():
    # 2. Asegurar que las carpetas requeridas existan en el directorio del programa
    carpetas_necesarias = [
        os.path.join(BASE_DIR, "db"),
        os.path.join(BASE_DIR, "photos"),
        os.path.join(BASE_DIR, "exportar"),
        os.path.join(BASE_DIR, "labels"),
        os.path.join(BASE_DIR, "fichas_inventario"),
        os.path.join(BASE_DIR, "reportes"),
        os.path.join(BASE_DIR, "report_actas")
    ]
    for c in carpetas_necesarias:
        os.makedirs(c, exist_ok=True)

    # 3. Inicializar base de datos y migraciones
    from db.init_db import init_db
    from services.sync_service import SyncService
    from gui.gui_login import Frame_login
    from utils.api_client import ApiManagerAcontarSacClient as ApiClient

    db_conn = sqlite3.connect(DB_PATH)
    init_db(db_conn)

    # 4. Verificar estado del Sync Inicial
    sync_service = SyncService(db_conn)
    sync_realizado = sync_service.is_initial_sync_done()
    db_conn.close()

    print(f"✓ BD conectada en: {DB_PATH}")
    print(f"✓ Sincronización inicial previa: {sync_realizado}")

    # 5. Iniciar Interfaz Tkinter
    root = tk.Tk()
    root.title("Acontar Especialistas Contables  AEC S.A.C.")

    # Cargar ícono de la aplicación
    icon_path = resource_path(os.path.join("img", "favicon.ico"))
    if not os.path.exists(icon_path):
        icon_path = os.path.join(BASE_DIR, "img", "favicon.ico")

    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception as e_ico:
            print(f"Advertencia al cargar ícono: {e_ico}")
    else:
        print(f"ADVERTENCIA: No se encontró el ícono en {icon_path}")

    root.configure(background='white')

    # 6. Instanciar y vincular ApiClient a 'root'
    api_client = ApiClient(base_url=API_BASE_URL)
    root.api_client = api_client

    # 7. Pasar 'api_client' a la vista de login
    Frame_login(
        root=root,
        db_path=DB_PATH,
        sync_realizado=sync_realizado,
        api_client=api_client
    )

    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err_msg = traceback.format_exc()
        try:
            log_path = os.path.join(BASE_DIR, "error_startup.log")
            with open(log_path, "w", encoding="utf-8") as f_err:
                f_err.write(err_msg)
        except Exception:
            pass

        try:
            mb.showerror(
                "Error Crítico al Iniciar AEC",
                f"Ocurrió un error inesperado al iniciar la aplicación:\n\n{e}\n\n"
                "Se ha generado un archivo 'error_startup.log' con el detalle técnico."
            )
        except Exception:
            pass
        sys.exit(1)
