import sqlite3
from sqlite3 import Error

def iniciar_conexion_sqlite():
    try:
        conn = sqlite3.connect("db/orap2022.db")
        return conn
    except Error as e:
        print("Error al conectar a Sqlite", e)
        return None
