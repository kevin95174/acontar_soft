# repositories/LocationsRepository.py
class LocationsRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def save_all(self, locations):
        cursor = self.db.cursor()
        for location in locations:
            cursor.execute("""
            INSERT OR REPLACE INTO locations(
                id,
                codigo_ubicacion,
                local,
                area,
                oficina,
                piso,
                direccion,
                codigo_personal,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            location.get("id"),
            location.get("codigo_ubicacion"),
            location.get("local"),
            location.get("area"),
            location.get("oficina"),
            location.get("piso"),
            location.get("direccion"),
            location.get("codigo_personal"),
            location.get("created_at"),
            location.get("updated_at"),
            location.get("deleted_at")
        ))
        self.db.commit()