# repositories/AssetsRepository.py
class AssetsRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def save_all(self, assets):
        """Guarda o actualiza masivamente los registros de la tabla assets en SQLite."""
        if not assets:
            return

        cursor = self.db.cursor()

        sql = """
            INSERT OR REPLACE INTO assets (
                id, codigo_interno, codigo_patrimonial, denominacion,
                cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
                val_adq, dep_acumulada, valor_neto, estado, situacion,
                estado_conservacion, marca, modelo, tipo, color, serie,
                dimension, placa, nro_motor, nro_chasis, matricula, anio,
                nota, observacion, otros, codigo_ubicacion, codigo_personal,
                created_at, updated_at, deleted_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?
            )
        """

        data = [
            (
                asset.get("id"),
                asset.get("codigo_interno"),
                asset.get("codigo_patrimonial"),
                asset.get("denominacion"),
                asset.get("cuenta_contable"),
                asset.get("denominacion_cuenta"),
                asset.get("nro_doc_adq"),
                asset.get("fech_adq"),
                asset.get("val_adq"),
                asset.get("dep_acumulada"),
                asset.get("valor_neto"),
                asset.get("estado"),
                asset.get("situacion"),
                asset.get("estado_conservacion"),
                asset.get("marca"),
                asset.get("modelo"),
                asset.get("tipo"),
                asset.get("color"),
                asset.get("serie"),
                asset.get("dimension"),
                asset.get("placa"),
                asset.get("nro_motor"),
                asset.get("nro_chasis"),
                asset.get("matricula"),
                asset.get("anio"),
                asset.get("nota"),
                asset.get("observacion"),
                asset.get("otros"),
                asset.get("codigo_ubicacion"),
                asset.get("codigo_personal"),
                asset.get("created_at"),
                asset.get("updated_at"),
                asset.get("deleted_at")
            )
            for asset in assets
        ]

        cursor.executemany(sql, data)
        self.db.commit()

    def get_all(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM assets WHERE deleted_at IS NULL")
        return cursor.fetchall()