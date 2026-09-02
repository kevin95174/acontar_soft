import os
import sqlite3
import tkinter as tk
from db.init_db import init_db
from services.sync_service import SyncService
from gui.gui_login import Frame_login
from utils.api_client import ApiManagerAcontarSacClient as ApiClient

# 1. Definición de la ruta absoluta de la BD en CODIGO/db/orap2022.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "orap2022.db")
API_BASE_URL = "https://api.acontarsac.com"  # Reemplaza por la URL de tu API Laravel


def main():
    # 2. Asegurar que la carpeta 'db' exista e inicializar tablas
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    db_conn = sqlite3.connect(DB_PATH)
    init_db(db_conn)
    
    # 3. Verificar estado del Sync Inicial
    sync_service = SyncService(db_conn)
    sync_realizado = sync_service.is_initial_sync_done()
    db_conn.close()

    print(f"📁 BD conectada en: {DB_PATH}")
    print(f"🔄 ¿Sincronización inicial previa?: {sync_realizado}")

    # 4. Iniciar Interfaz Tkinter
    root = tk.Tk()
    root.title("Acontar Especialistas Contables  AEC S.A.C.")
    root.iconbitmap('img/favicon.ico')
    root.configure(background='white')

    # 🔥 5. Instanciar y vincular ApiClient a 'root'
    api_client = ApiClient(base_url=API_BASE_URL)
    root.api_client = api_client  # Queda accesible globalmente en Tkinter

    # 6. Pasar 'api_client' a la vista de login
    Frame_login(
        root=root, 
        db_path=DB_PATH, 
        sync_realizado=sync_realizado,
        api_client=api_client
    )
    
    root.mainloop()


if __name__ == "__main__":
    main()