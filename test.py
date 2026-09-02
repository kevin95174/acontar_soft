import os
import sqlite3
from db.init_db import init_db
from utils.api_client import ApiManagerAcontarSacClient
from services.sync_service import SyncService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "orap2022.db")

# 1. Conectar e inicializar tablas
db_conn = sqlite3.connect(DB_PATH)
init_db(db_conn)

# 2. Instanciar cliente API y servicio
client = ApiManagerAcontarSacClient()
sync_service = SyncService(db_conn)

# 3. Validar estado previo
print("¿Sync inicial realizado previo?:", sync_service.is_initial_sync_done())

# 4. Ejecutar Initial Sync
print("Iniciando descarga e inserción masiva...")
resultado = sync_service.execute_initial_sync(client)
print("Resultado:", resultado)

# 5. Confirmar estado posterior
print("¿Sync inicial realizado posterior?:", sync_service.is_initial_sync_done())

db_conn.close()