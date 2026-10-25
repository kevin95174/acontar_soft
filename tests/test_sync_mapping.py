import os
import sqlite3
import tempfile
import unittest

from db.init_db import init_db
from services.sync_service import SyncService


class SyncMappingTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        self.conn = sqlite3.connect(self.db_path)
        init_db(self.conn)
        self.sync_service = SyncService(self.conn)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_sync_all_tables_and_populate_operational_tables(self):
        sample_data = {
            "locations": [
                {
                    "id": 1,
                    "codigo_ubicacion": "101",
                    "local": "Sede Central",
                    "area": "Administracion",
                    "oficina": "Gerencia",
                    "piso": "2",
                    "direccion": "Av. Principal 123",
                    "codigo_personal": "PER-01",
                    "team_id": "EQ-01",
                    "created_at": "2026-01-01 10:00:00",
                    "updated_at": "2026-01-01 10:00:00"
                }
            ],
            "personnel": [
                {
                    "id": 1,
                    "codigo_personal": "PER-01",
                    "nombres": "Juan",
                    "apellidos": "Perez",
                    "cargo": "Gerente",
                    "oficina": "Gerencia",
                    "telefono": "987654321",
                    "email": "juan@example.com",
                    "estado": "ACTIVO",
                    "created_at": "2026-01-01 10:00:00",
                    "updated_at": "2026-01-01 10:00:00"
                }
            ],
            "assets": [
                {
                    "id": 1,
                    "codigo_interno": "1001",
                    "codigo_patrimonial": "PAT-1001",
                    "denominacion": "Laptop Dell",
                    "cuenta_contable": "1503.0201",
                    "denominacion_cuenta": "Equipos Computacionales",
                    "val_adq": 4500.0,
                    "dep_acumulada": 1500.0,
                    "valor_neto": 3000.0,
                    "estado": "Bueno",
                    "estado_conservacion": "Bueno",
                    "marca": "Dell",
                    "modelo": "Latitude",
                    "serie": "SN12345",
                    "codigo_ubicacion_inicial": 101,
                    "codigo_personal": "PER-01"
                }
            ],
            "inventory_records": [
                {
                    "id": 50,
                    "asset_id": 1,
                    "codigo_interno": "1001",
                    "codigo_patrimonial": "PAT-1001",
                    "denominacion": "Laptop Dell",
                    "cuenta_contable": "1503.0201",
                    "denominacion_cuenta": "Equipos Computacionales",
                    "nro_doc_adq": "FACT-999",
                    "fech_adq": "2024-05-10",
                    "val_adq": 4500.0,
                    "dep_acumulada": 1500.0,
                    "valor_neto": 3000.0,
                    "estado": "Bueno",
                    "estado_conservacion": "Bueno",
                    "marca": "Dell",
                    "modelo": "Latitude",
                    "serie": "SN12345",
                    "anio": "2024",
                    "nota": "Asignado a gerencia",
                    "observacion": "Operativo",
                    "codigo_personal": "PER-01",
                    "codigo_ubicacion_inicial": 101,
                    "codigo_ubicacion_final": 101,
                    "user_id": 5,
                    "fecha_inventariado": "2026-10-24 15:30:00",
                    "inventariado": 1,
                    "fecha_servidor": "2026-10-24 15:35:00"
                }
            ],
            "surplus": [
                {
                    "id": 1,
                    "codigo_interno": "S001",
                    "codigo_patrimonial": "PAT-SOB-01",
                    "codigo_ubicacion": 101,
                    "codigo_personal": 1,
                    "denominacion": "Monitor Extra LG",
                    "marca": "LG",
                    "modelo": "24MP",
                    "serie": "LG-9988",
                    "estado_conservacion": "Bueno"
                }
            ],
            "asset_photos": [
                {
                    "id": 1,
                    "asset_id": 1,
                    "codigo_interno": "1001",
                    "ruta_foto": "/photos/laptop1001.jpg",
                    "sincronizado": 1
                }
            ],
            "teams": [
                {
                    "id": 1,
                    "nombre": "Brigada Norte",
                    "capturador_id": 5,
                    "auxiliar_id": 6,
                    "estado": "ACTIVO"
                }
            ],
            "users": [
                {
                    "id": 5,
                    "nombres": "Carlos",
                    "apellidos": "Mendoza",
                    "correo": "carlos@acontarsac.com",
                    "usuario": "cmendoza",
                    "password_hash": "hashed_pass_123",
                    "rol": "CAPTURADOR",
                    "estado": 1
                },
                {
                    "id": 6,
                    "nombres": "Ana",
                    "apellidos": "Torres",
                    "correo": "ana@acontarsac.com",
                    "usuario": "atorres",
                    "password_hash": None,
                    "rol": "AUXILIAR",
                    "estado": 1
                }
            ],
            "inventory_assignments": [
                {
                    "id": 1,
                    "team_id": 1,
                    "location_id": 1,
                    "fecha_programada": "2026-10-25",
                    "estado": "PENDIENTE"
                }
            ]
        }

        # 1. Probar inserción masiva en tablas espejo
        res = self.sync_service.process_download_sync(sample_data)
        self.assertEqual("success", res.get("status"))

        cur = self.conn.cursor()

        # Verificar réplica de locations con team_id
        cur.execute("SELECT team_id FROM locations WHERE id = 1")
        self.assertEqual("EQ-01", cur.fetchone()[0])

        # Verificar réplica de surplus con codigo_patrimonial
        cur.execute("SELECT codigo_patrimonial FROM surplus WHERE id = 1")
        self.assertEqual("PAT-SOB-01", cur.fetchone()[0])

        # Verificar réplica de asset_photos, teams, users, inventory_assignments
        cur.execute("SELECT COUNT(*) FROM asset_photos")
        self.assertEqual(1, cur.fetchone()[0])
        cur.execute("SELECT nombre FROM teams WHERE id = 1")
        self.assertEqual("Brigada Norte", cur.fetchone()[0])
        cur.execute("SELECT usuario FROM users WHERE id = 5")
        self.assertEqual("cmendoza", cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM inventory_assignments")
        self.assertEqual(1, cur.fetchone()[0])

        # 2. Probar volcados a tablas operativas
        self.sync_service.populate_bienes_from_server()
        self.sync_service.populate_personal_from_server()
        self.sync_service.populate_sobrantes_from_server()
        self.sync_service.populate_usuarios_from_server()

        # Verificar tabla 'bienes'
        cur.execute("""
            SELECT CodInt, CodPat, ValAdq, DepAcum, ValNeto, CtaCont, Nota, Inv, Inventariador
            FROM bienes WHERE CodInt = 1001
        """)
        row_bien = cur.fetchone()
        self.assertIsNotNone(row_bien)
        self.assertEqual(1001, row_bien[0])
        self.assertEqual("PAT-1001", row_bien[1])
        self.assertEqual(4500.0, row_bien[2])
        self.assertEqual(1500.0, row_bien[3])
        self.assertEqual(3000.0, row_bien[4])
        self.assertEqual("1503.0201", row_bien[5])
        self.assertEqual("Asignado a gerencia", row_bien[6])
        self.assertEqual("101", row_bien[7])  # Inv final
        self.assertEqual("5", row_bien[8])    # Inventariador

        # Verificar tabla 'personal'
        cur.execute("SELECT Acta, local, nombre, apellidoPat, EquiInv FROM personal WHERE Acta = '101'")
        row_per = cur.fetchone()
        self.assertIsNotNone(row_per)
        self.assertEqual("Sede Central", row_per[1])
        self.assertEqual("Juan", row_per[2])
        self.assertEqual("Perez", row_per[3])

        # Verificar tabla 'sobrantes'
        cur.execute("SELECT den, acta, local, nota FROM sobrantes WHERE item = 1")
        row_sob = cur.fetchone()
        self.assertIsNotNone(row_sob)
        self.assertEqual("Monitor Extra LG", row_sob[0])
        self.assertEqual("101", row_sob[1])
        self.assertEqual("Sede Central", row_sob[2])
        self.assertEqual("PAT-SOB-01", row_sob[3])

        # Verificar tabla 'usuarios'
        cur.execute("SELECT usuario, password, Nombres, APat, equipo FROM usuarios WHERE id = 5")
        row_usr = cur.fetchone()
        self.assertIsNotNone(row_usr)
        self.assertEqual("cmendoza", row_usr[0])
        self.assertEqual("hashed_pass_123", row_usr[1])
        self.assertEqual("Carlos", row_usr[2])
        self.assertEqual("Mendoza", row_usr[3])
        self.assertEqual("CAPTURADOR", row_usr[4])


if __name__ == "__main__":
    unittest.main()
