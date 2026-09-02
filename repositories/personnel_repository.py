# repositories/PersonnelRepository.py
class PersonnelRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def save_all(self, personnel_list):
        cursor = self.db.cursor()
        for person in personnel_list:
            cursor.execute("""
                INSERT OR REPLACE INTO personnel(
                    id, codigo_personal, nombres, apellidos, cargo,
                    oficina, telefono, email, estado, created_at,
                    updated_at, deleted_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                person.get("id"),
                person["codigo_personal"],
                person["nombres"],
                person["apellidos"],
                person.get("cargo"),
                person.get("oficina"),
                person.get("telefono"),
                person.get("email"),
                person.get("estado", 1),
                person.get("created_at"),
                person.get("updated_at"),
                person.get("deleted_at")
            ))
        self.db.commit()

    def get_all(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM personnel WHERE deleted_at IS NULL")
        return cursor.fetchall()