# repositories/InventoryRepository.py
class InventoryRepository:
    def __init__(self, db_connection):
        self.db = db_connection

    def save_all(self, records):
        """Guarda o actualiza masivamente los registros de inventory_records en SQLite."""
        if not records:
            return

        cursor = self.db.cursor()

        sql = """
            INSERT OR REPLACE INTO inventory_records (
                id, asset_id, codigo_interno, codigo_patrimonial, denominacion,
                cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq, val_adq,
                dep_acumulada, valor_neto, marca, modelo, tipo, color, serie,
                dimension, otros, situacion, estado_conservacion, observacion,
                codigo_personal, codigo_ubicacion_inicial, codigo_ubicacion_final,
                user_id, foto_url, fecha_inventariado, inventariado, fecha_servidor,
                created_at, updated_at, deleted_at, estado, placa, nro_motor,
                nro_chasis, matricula, anio
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """

        data = [
            (
                record.get("id"),
                record.get("asset_id"),
                record.get("codigo_interno"),
                record.get("codigo_patrimonial"),
                record.get("denominacion"),
                record.get("cuenta_contable"),
                record.get("denominacion_cuenta"),
                record.get("nro_doc_adq"),
                record.get("fech_adq"),
                record.get("val_adq"),
                record.get("dep_acumulada"),
                record.get("valor_neto"),
                record.get("marca"),
                record.get("modelo"),
                record.get("tipo"),
                record.get("color"),
                record.get("serie"),
                record.get("dimension"),
                record.get("otros"),
                record.get("situacion"),
                record.get("estado_conservacion"),
                record.get("observacion"),
                record.get("codigo_personal"),
                record.get("codigo_ubicacion_inicial"),
                record.get("codigo_ubicacion_final"),
                record.get("user_id"),
                record.get("foto_url"),
                record.get("fecha_inventariado"),
                record.get("inventariado", 0),
                record.get("fecha_servidor"),
                record.get("created_at"),
                record.get("updated_at"),
                record.get("deleted_at"),
                record.get("estado"),
                record.get("placa"),
                record.get("nro_motor"),
                record.get("nro_chasis"),
                record.get("matricula"),
                record.get("anio")
            )
            for record in records
        ]

        cursor.executemany(sql, data)
        self.db.commit()

    def get_pending_sync(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM inventory_records WHERE inventariado = 0 AND deleted_at IS NULL")
        return cursor.fetchall()