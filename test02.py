import os
import sqlite3
from db.init_db import init_db
from utils.api_client import ApiManagerAcontarSacClient
from services.sync_service import SyncService
from utils.config_helper import get_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "orap2022.db")

db_conn = sqlite3.connect(DB_PATH)
init_db(db_conn)

client = ApiManagerAcontarSacClient()
sync_service = SyncService(db_conn)

print("📌 Fecha de último sync almacenada:", get_config(db_conn, "last_sync_timestamp"))

# Ejecutar la sincronización diferencial
print("⚡ Consultando cambios en el servidor...")
resultado = sync_service.execute_sync_changes(client)

print("\n--- RESULTADO ---")
print(resultado)

print("\n📌 Nueva fecha de último sync:", get_config(db_conn, "last_sync_timestamp"))

db_conn.close()