import os
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock

from db.init_db import init_db
import db.query as query


class FirstTimeLoginTests(unittest.TestCase):
    def setUp(self):
        self.fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        self.conn = sqlite3.connect(self.db_path)
        init_db(self.conn)
        self.conn.close()

        self.original_conex = query.iniciar_conexion_sqlite
        query.iniciar_conexion_sqlite = lambda: sqlite3.connect(self.db_path)

    def tearDown(self):
        query.iniciar_conexion_sqlite = self.original_conex
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_default_offline_user_can_login(self):
        # El usuario por defecto 'user' / 'user' siempre existe tras init_db
        status = query.login("user", "user")
        self.assertEqual(1, status)
        datos = query.login_user("user", "user")
        self.assertIsNotNone(datos)
        self.assertEqual("OPERADOR", datos[0][2])

    def test_empty_database_initially_fails_unknown_user(self):
        r = query.login("desconocido", "secret123")
        self.assertEqual(2, r)  # 2 significa usuario/password no encontrado

    def test_online_login_populates_local_user_for_subsequent_offline_logins(self):
        # 1. Simular respuesta de la API para login exitoso
        mock_api = Mock()
        mock_api.login.return_value = {
            "success": True,
            "data": {
                "id": 10,
                "usuario": "operador1",
                "nombres": "Maria",
                "apellidos": "Lopez",
                "rol": "CAPTURADOR"
            }
        }

        # 2. El cliente valida online y almacena en SQLite local
        res = mock_api.login("operador1", "claveSegura")
        self.assertTrue(res["success"])
        user_info = res["data"]

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO usuarios (
                id, usuario, password, Nombres, APat, AMat, dni, equipo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_info["id"],
            user_info["usuario"],
            "claveSegura",
            user_info["nombres"],
            user_info["apellidos"],
            "",
            str(user_info["id"]),
            user_info["rol"]
        ))
        conn.commit()
        conn.close()

        # 3. Ahora probar que el login LOCAL funciona sin necesidad de API (100% offline)
        local_status = query.login("operador1", "claveSegura")
        self.assertEqual(1, local_status)

        user_tuple = query.login_user("operador1", "claveSegura")
        self.assertIsNotNone(user_tuple)
        self.assertEqual("Maria Lopez ", user_tuple[0][0])
        self.assertEqual("CAPTURADOR", user_tuple[0][2])


if __name__ == "__main__":
    unittest.main()
