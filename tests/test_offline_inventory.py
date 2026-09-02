import os
import sqlite3
import tempfile
import unittest

from db.init_db import init_db
import db.query as query


class OfflineInventoryTests(unittest.TestCase):
    def setUp(self):
        descriptor, self.path = tempfile.mkstemp(suffix=".db")
        os.close(descriptor)
        conn = sqlite3.connect(self.path)
        init_db(conn)
        conn.execute(
            "INSERT INTO bienes (CodInt, ActaAnt, Inv, CodPat, DenBien) "
            "VALUES (1, 'A-ANT', '', 'P-001', 'Bien')"
        )
        conn.execute(
            "INSERT INTO inventory_records "
            "(id, codigo_interno, codigo_patrimonial, denominacion, estado_conservacion) "
            "VALUES (10, '1', 'P-001', 'Bien', 'Bueno')"
        )
        conn.commit()
        conn.close()
        self.original_connection = query.iniciar_conexion_sqlite
        query.iniciar_conexion_sqlite = lambda: sqlite3.connect(self.path)

    def tearDown(self):
        query.iniciar_conexion_sqlite = self.original_connection
        os.unlink(self.path)

    def test_local_registration_is_preserved_and_later_synced(self):
        result = query.registrar_inventario_local_pendiente(
            "P-001", 10, "A-NEW", "2026-08-13 12:00:00", "Ana", "T1", 7
        )
        self.assertTrue(result["success"])

        conn = sqlite3.connect(self.path)
        self.assertEqual("A-NEW", conn.execute(
            "SELECT Inv FROM bienes WHERE CodInt = 1"
        ).fetchone()[0])
        self.assertEqual(1, conn.execute(
            "SELECT inventariado FROM inventory_records WHERE id = 10"
        ).fetchone()[0])
        self.assertEqual(1, conn.execute(
            "SELECT COUNT(*) FROM inventory_sync_outbox WHERE status = 'pending'"
        ).fetchone()[0])
        conn.close()

        class OnlineClient:
            def update_ubicacion_final(self, *args):
                return {"status_code": 200, "data": {}}

        sync_result = query.sincronizar_inventarios_pendientes(OnlineClient())
        self.assertEqual(1, sync_result["synced"])
        self.assertEqual(0, sync_result["pending"])


if __name__ == "__main__":
    unittest.main()
