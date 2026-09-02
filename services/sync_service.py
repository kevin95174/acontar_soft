# services/sync_service.py
from datetime import datetime
from db.query import sincronizar_inventarios_pendientes
from utils.config_helper import get_config, set_config


class SyncService:
    def __init__(self, db_connection):
        self.db = db_connection

    def is_initial_sync_done(self) -> bool:
        """Verifica si la carga inicial ya se realizó previamente."""
        val = get_config(self.db, "initial_sync_done", "false")
        return val.lower() == "true"

    def get_last_sync_timestamp(self) -> str:
        """Devuelve el último timestamp registrado."""
        return get_config(self.db, "last_sync_timestamp", None)

    def process_download_sync(self, data: dict) -> dict:
        """
        Guarda o actualiza todos los registros recibidos de la API en SQLite 
        usando INSERT OR REPLACE.
        """
        try:
            cursor = self.db.cursor()

            # 1. Locations
            for loc in data.get("locations", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO locations (
                        id, codigo_ubicacion, local, area, oficina, piso, direccion, codigo_personal, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    loc.get("id"), loc.get("codigo_ubicacion"), loc.get("local"),
                    loc.get("area"), loc.get("oficina"), loc.get("piso"),
                    loc.get("direccion"), loc.get("codigo_personal"), loc.get("updated_at")
                ))

            # 2. Personnel
            for per in data.get("personnel", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO personnel (
                        id, codigo_personal, nombres, apellidos, cargo, oficina, telefono, email, estado, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    per.get("id"), per.get("codigo_personal"), per.get("nombres"),
                    per.get("apellidos"), per.get("cargo"), per.get("oficina"),
                    per.get("telefono"), per.get("email"), per.get("estado", 1), per.get("updated_at")
                ))

            # 3. Assets
            for ast in data.get("assets", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO assets (
                        id, codigo_interno, codigo_patrimonial, denominacion, nro_doc_adq, fech_adq,
                        val_adq, estado, situacion, estado_conservacion, marca, modelo, tipo, color,
                        serie, dimension, placa, nro_motor, nro_chasis, matricula, anio, nota,
                        observacion, otros, codigo_ubicacion, codigo_personal, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ast.get("id"), ast.get("codigo_interno"), ast.get("codigo_patrimonial"),
                    ast.get("denominacion"), ast.get("nro_doc_adq"), ast.get("fech_adq"),
                    ast.get("val_adq"), ast.get("estado"), ast.get("situacion"),
                    ast.get("estado_conservacion"), ast.get("marca"), ast.get("modelo"),
                    ast.get("tipo"), ast.get("color"), ast.get("serie"), ast.get("dimension"),
                    ast.get("placa"), ast.get("nro_motor"), ast.get("nro_chasis"),
                    ast.get("matricula"), ast.get("anio"), ast.get("nota"),
                    ast.get("observacion"), ast.get("otros"), ast.get("codigo_ubicacion"),
                    ast.get("codigo_personal"), ast.get("updated_at")
                ))

            # 4. Inventory Records
            for inv in data.get("inventory_records", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO inventory_records (
                        id, asset_id, codigo_interno, codigo_patrimonial, denominacion, marca, modelo,
                        tipo, color, serie, dimension, otros, situacion, estado_conservacion, observacion,
                        codigo_personal, codigo_ubicacion_inicial, codigo_ubicacion_final, user_id, foto_url,
                        fecha_inventariado, inventariado, fecha_servidor, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inv.get("id"), inv.get("asset_id"), inv.get("codigo_interno"),
                    inv.get("codigo_patrimonial"), inv.get("denominacion"), inv.get("marca"),
                    inv.get("modelo"), inv.get("tipo"), inv.get("color"), inv.get("serie"),
                    inv.get("dimension"), inv.get("otros"), inv.get("situacion"),
                    inv.get("estado_conservacion"), inv.get("observacion"), inv.get("codigo_personal"),
                    inv.get("codigo_ubicacion_inicial"), inv.get("codigo_ubicacion_final"),
                    inv.get("user_id"), inv.get("foto_url"), inv.get("fecha_inventariado"),
                    inv.get("inventariado", 0), inv.get("fecha_servidor"), inv.get("updated_at")
                ))

            # 5. Surplus
            for sur in data.get("surplus", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO surplus (
                        id, codigo_ubicacion, codigo_personal, denominacion, marca, modelo,
                        tipo, color, serie, dimension, otros, situacion, estado_conservacion,
                        observacion, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sur.get("id"), sur.get("codigo_ubicacion"), sur.get("codigo_personal"),
                    sur.get("denominacion"), sur.get("marca"), sur.get("modelo"),
                    sur.get("tipo"), sur.get("color"), sur.get("serie"),
                    sur.get("dimension"), sur.get("otros"), sur.get("situacion"),
                    sur.get("estado_conservacion"), sur.get("observacion"), sur.get("updated_at")
                ))

            self.db.commit()
            return {"status": "success"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error al procesar inserción en SQLite: {str(e)}"}

    def execute_initial_sync(self, api_client, limit: int = 20000) -> dict:
        """Descarga completa de la base de datos inicial y registro de marca en app_config."""
        try:
            response = api_client.initial_sync(limit=limit)
            data = response.get("data", response)

            res_db = self.process_download_sync(data)
            if res_db.get("status") == "error":
                return res_db

            self.populate_bienes_from_server()
            self.populate_personal_from_server()

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            set_config(self.db, "initial_sync_done", "true")
            set_config(self.db, "last_sync_timestamp", now_str)

            return {
                "status": "success",
                "message": f"Initial Sync completado con éxito el {now_str}.",
                "timestamp": now_str
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error en Initial Sync: {str(e)}"}

    def execute_sync_changes(self, api_client, limit: int = 20000) -> dict:
        """Sincronización diferencial basada en last_sync_timestamp."""
        last_sync = self.get_last_sync_timestamp()
        if not last_sync:
            return {"status": "error", "message": "Se requiere ejecutar Initial Sync primero."}

        try:
            # Primero subimos la cola. Descargar antes podría sobrescribir un
            # inventario hecho sin conexión.
            envio = sincronizar_inventarios_pendientes(api_client)
            if envio.get("pending", 0):
                return {
                    "status": "deferred",
                    "message": "Hay inventarios locales pendientes de sincronización.",
                }

            response = api_client.sync_changes(last_sync=last_sync, limit=limit)
            payload = response.get("data", {})
            changes = payload.get("changes", {})
            server_time = payload.get("server_time")

            res_db = self.process_download_sync(changes)
            if res_db.get("status") == "error":
                return res_db

            self.populate_bienes_from_server()

            if server_time:
                set_config(self.db, "last_sync_timestamp", server_time)

            total_novedades = sum(len(v) for v in changes.values() if isinstance(v, list))

            return {
                "status": "success",
                "message": f"Sincronización de cambios finalizada. {total_novedades} registros actualizados.",
                "server_time": server_time
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error en Sync Changes: {str(e)}"}

    def populate_bienes_from_server(self):
        """Puebla la tabla local 'bienes' únicamente desde 'inventory_records' aplicando las equivalencias de ubicaciones y depreciaciones."""
        try:
            sql = """
                INSERT OR REPLACE INTO bienes (
                    CodInt, ActaAnt, Inv, CodPat, DenBien, NroDocAdq, FechAdq,
                    ValAdq, DepAcum, ValNeto, CtaCont, DenCta, Estado, Marca,
                    Modelo, Tipo, Color, Serie, Dimension, Placa, NroMotor,
                    NroChasis, Matricula, AñoFab, Obs, FechInv, Otros,
                    Situacion, Inventariador
                )
                SELECT 
                    CAST(codigo_interno AS INTEGER),
                    codigo_ubicacion_inicial,
                    CASE WHEN COALESCE(inventariado, 0) = 1
                         THEN codigo_ubicacion_final ELSE '' END,
                    codigo_patrimonial,
                    denominacion,
                    nro_doc_adq,
                    fech_adq,
                    val_adq,
                    dep_acumulada,
                    valor_neto,
                    cuenta_contable,
                    denominacion_cuenta,
                    estado_conservacion,
                    marca,
                    modelo,
                    tipo,
                    color,
                    serie,
                    dimension,
                    placa,
                    nro_motor,
                    nro_chasis,
                    matricula,
                    CAST(anio AS TEXT),
                    observacion,
                    CASE WHEN COALESCE(inventariado, 0) = 1
                         THEN fecha_inventariado ELSE NULL END,
                    otros,
                    situacion,
                    CASE WHEN COALESCE(inventariado, 0) = 1
                         THEN CAST(user_id AS TEXT) ELSE NULL END
                FROM inventory_records;
            """
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            print("✅ Tabla 'bienes' sincronizada correctamente desde 'inventory_records'.")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Error al volcar inventory_records a bienes: {e}")

    def populate_personal_from_server(self):
            """Puebla la tabla local 'personal' cruzando 'locations' y 'personnel'."""
            try:
                sql = """
                    INSERT OR REPLACE INTO personal (
                        Acta, dep, prov, dist, local, area, oficina,
                        dni, nombre, apellidoPat, apellidoMat, EquiInv
                    )
                    SELECT 
                        COALESCE(l.codigo_ubicacion, CAST(l.id AS TEXT)),
                        NULL,
                        NULL,
                        NULL,
                        l.local,
                        l.area,
                        COALESCE(l.oficina, p.oficina),
                        p.codigo_personal,
                        p.nombres,
                        p.apellidos,
                        '',
                        p.cargo
                    FROM locations l
                    LEFT JOIN personnel p ON l.codigo_personal = p.codigo_personal;
                """
                cursor = self.db.cursor()
                cursor.execute(sql)
                self.db.commit()
                print("✅ Tabla local 'personal' actualizada correctamente.")
            except Exception as e:
                self.db.rollback()
                print(f"❌ Error al poblar tabla personal: {e}")
