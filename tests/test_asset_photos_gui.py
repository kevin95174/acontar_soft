import os
import sqlite3
import tempfile
import unittest

from db.init_db import init_db


class AssetPhotosDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        self.conn = sqlite3.connect(self.db_path)
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_insert_and_query_asset_photos_with_cross_join(self):
        cur = self.conn.cursor()

        # Insertar un bien de prueba
        cur.execute("""
            INSERT INTO assets (id, codigo_interno, codigo_patrimonial, denominacion)
            VALUES (1, '1001', 'PAT-1001', 'Impresora HP LaserJet')
        """)

        # Insertar foto de prueba
        cur.execute("""
            INSERT INTO asset_photos (asset_id, codigo_interno, ruta_foto, fecha, sincronizado)
            VALUES (1, '1001', 'uploads/photos/hp1001.jpg', '2026-10-25 10:00:00', 1)
        """)
        self.conn.commit()

        # Probar la misma consulta que usa Window_asset_photos
        sql = """
            SELECT 
                ap.id,
                COALESCE(ap.codigo_interno, ''),
                COALESCE(b.CodPat, ast.codigo_patrimonial, ''),
                COALESCE(b.DenBien, ast.denominacion, 'Bien sin denominación'),
                COALESCE(ap.ruta_foto, ''),
                COALESCE(ap.fecha, ''),
                COALESCE(ap.sincronizado, 0),
                COALESCE(ap.asset_id, 0)
            FROM asset_photos ap
            LEFT JOIN assets ast ON ast.id = ap.asset_id OR CAST(ast.codigo_interno AS TEXT) = CAST(ap.codigo_interno AS TEXT)
            LEFT JOIN bienes b ON CAST(b.CodInt AS TEXT) = CAST(ap.codigo_interno AS TEXT)
            WHERE ap.deleted_at IS NULL
            ORDER BY ap.id DESC
        """
        cur.execute(sql)
        row = cur.fetchone()

        self.assertIsNotNone(row)
        self.assertEqual("1001", row[1])
        self.assertEqual("PAT-1001", row[2])
        self.assertEqual("Impresora HP LaserJet", row[3])
        self.assertEqual("uploads/photos/hp1001.jpg", row[4])
        self.assertEqual(1, row[6])

    def test_pagination_limits_and_offset(self):
        cur = self.conn.cursor()
        # Insertar 120 fotos
        for i in range(1, 121):
            cur.execute("""
                INSERT INTO asset_photos (id, asset_id, codigo_interno, ruta_foto, sincronizado)
                VALUES (?, ?, ?, ?, 1)
            """, (i, i, f"COD-{i}", f"uploads/photos/img_{i}.jpg"))
        self.conn.commit()

        # Página 1 (50 registros)
        cur.execute("SELECT id FROM asset_photos ORDER BY id DESC LIMIT 50 OFFSET 0")
        p1 = cur.fetchall()
        self.assertEqual(50, len(p1))
        self.assertEqual(120, p1[0][0])  # Primer elemento en orden DESC

        # Página 2 (50 registros)
        cur.execute("SELECT id FROM asset_photos ORDER BY id DESC LIMIT 50 OFFSET 50")
        p2 = cur.fetchall()
        self.assertEqual(50, len(p2))
        self.assertEqual(70, p2[0][0])

        # Página 3 (los 20 restantes)
        cur.execute("SELECT id FROM asset_photos ORDER BY id DESC LIMIT 50 OFFSET 100")
        p3 = cur.fetchall()
        self.assertEqual(20, len(p3))
        self.assertEqual(20, p3[0][0])
        self.assertEqual(1, p3[-1][0])

    def test_search_by_codigo_interno_with_null_and_linked_asset(self):
        cur = self.conn.cursor()
        # Asset con codigo_interno = '10335'
        cur.execute("""
            INSERT INTO assets (id, codigo_interno, codigo_patrimonial, denominacion)
            VALUES (10038, '10335', '740878680045', 'MONITOR INTEGRADO')
        """)

        # Foto donde ap.codigo_interno es NULL pero asset_id es 10038
        cur.execute("""
            INSERT INTO asset_photos (id, asset_id, codigo_interno, ruta_foto, sincronizado)
            VALUES (1, 10038, NULL, 'uploads/photos/10038_foto.jpg', 1)
        """)

        # Otra foto de otro bien distinto
        cur.execute("""
            INSERT INTO assets (id, codigo_interno, codigo_patrimonial, denominacion)
            VALUES (20000, '99999', '111111111111', 'ESCRITORIO')
        """)
        cur.execute("""
            INSERT INTO asset_photos (id, asset_id, codigo_interno, ruta_foto, sincronizado)
            VALUES (2, 20000, '99999', 'uploads/photos/desk.jpg', 1)
        """)
        self.conn.commit()

        # Búsqueda por Cód. Interno '10335'
        query = "10335"
        like_val = f"%{query}%"
        sql = """
            SELECT ap.id, COALESCE(ap.codigo_interno, ast.codigo_interno, ''), ast.denominacion
            FROM asset_photos ap
            LEFT JOIN assets ast ON ast.id = ap.asset_id
            WHERE ap.deleted_at IS NULL AND (
                ap.codigo_interno LIKE ? OR 
                ast.codigo_interno LIKE ? OR 
                CAST(ap.asset_id AS TEXT) = ?
            )
        """
        cur.execute(sql, (like_val, like_val, query))
        rows = cur.fetchall()
        self.assertEqual(1, len(rows))
        self.assertEqual(1, rows[0][0])
        self.assertEqual("10335", rows[0][1])
        self.assertEqual("MONITOR INTEGRADO", rows[0][2])


if __name__ == "__main__":
    unittest.main()
