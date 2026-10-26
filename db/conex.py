import sqlite3
from sqlite3 import Error

_DB_INITIALIZED = False


def iniciar_conexion_sqlite():
    global _DB_INITIALIZED
    try:
        conn = sqlite3.connect("db/orap2022.db")
        if not _DB_INITIALIZED:
            _DB_INITIALIZED = True
            try:
                from db.init_db import init_db
                init_db(conn)
            except Exception as init_err:
                print("Advertencia al inicializar esquema unificado:", init_err)
        return conn
    except Error as e:
        print("Error al conectar a Sqlite", e)
        return None
