import sqlite3
import sys
import os
from sqlite3 import Error

_DB_INITIALIZED = False


def get_database_path():
    """Retorna la ruta absoluta al archivo SQLite tanto en desarrollo como en ejecutable PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, "db", "orap2022.db")


def iniciar_conexion_sqlite():
    global _DB_INITIALIZED
    try:
        db_path = get_database_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        if not _DB_INITIALIZED:
            _DB_INITIALIZED = True
            try:
                from db.init_db import init_db
                init_db(conn)
            except Exception as init_err:
                print("Advertencia al inicializar esquema unificado:", init_err)
        return conn
    except Error as e:
        print("Error al conectar a Sqlite:", e)
        return None
