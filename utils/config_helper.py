# utils/config_helper.py
import sqlite3

def ensure_config_table(connection: sqlite3.Connection):
    """Crea la tabla app_config si aún no existe."""
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    connection.commit()

def get_config(connection: sqlite3.Connection, key: str, default=None) -> str:
    ensure_config_table(connection)  # Asegura la existencia antes de consultar
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM app_config WHERE key = ?", (key,))
    row = cursor.fetchone()
    return row[0] if row else default

def set_config(connection: sqlite3.Connection, key: str, value: str):
    ensure_config_table(connection)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO app_config (key, value) 
        VALUES (?, ?)
    """, (key, value))
    connection.commit()