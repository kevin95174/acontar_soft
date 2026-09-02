# repositories/SurplusRepository.py
class SurplusRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def save_all(self, surplus_list):
        cursor = self.db.cursor()
        for item in surplus_list:
            cursor.execute("""
                INSERT OR REPLACE INTO surplus(
                    id, codigo_ubicacion, codigo_personal, denominacion,
                    marca, modelo, tipo, color, serie, dimension, otros,
                    situacion, estado_conservacion, observacion,
                    created_at, updated_at, deleted_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                item.get("id"),
                item.get("codigo_ubicacion"),
                item.get("codigo_personal"),
                item["denominacion"],
                item.get("marca"),
                item.get("modelo"),
                item.get("tipo"),
                item.get("color"),
                item.get("serie"),
                item.get("dimension"),
                item.get("otros"),
                item.get("situacion"),
                item.get("estado_conservacion"),
                item.get("observacion"),
                item.get("created_at"),
                item.get("updated_at"),
                item.get("deleted_at")
            ))
        self.db.commit()

    def get_all(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM surplus WHERE deleted_at IS NULL")
        return cursor.fetchall()