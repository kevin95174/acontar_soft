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
        usando INSERT OR REPLACE asegurando correspondencia 1:1 con MySQL.
        """
        try:
            cursor = self.db.cursor()

            # 1. Locations
            for loc in data.get("locations", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO locations (
                        id, codigo_ubicacion, local, area, oficina, piso, direccion,
                        codigo_personal, team_id, created_at, updated_at, deleted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    loc.get("id"), loc.get("codigo_ubicacion"), loc.get("local"),
                    loc.get("area"), loc.get("oficina"), loc.get("piso"),
                    loc.get("direccion"), loc.get("codigo_personal"),
                    loc.get("team_id", ""), loc.get("created_at"),
                    loc.get("updated_at"), loc.get("deleted_at")
                ))

            # 2. Personnel
            for per in data.get("personnel", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO personnel (
                        id, codigo_personal, nombres, apellidos, cargo, oficina,
                        telefono, email, estado, created_at, updated_at, deleted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    per.get("id"), per.get("codigo_personal"), per.get("nombres"),
                    per.get("apellidos"), per.get("cargo"), per.get("oficina"),
                    per.get("telefono"), per.get("email"), per.get("estado", "1"),
                    per.get("created_at"), per.get("updated_at"), per.get("deleted_at")
                ))

            # 3. Assets
            for ast in data.get("assets", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO assets (
                        id, codigo_interno, codigo_patrimonial, denominacion,
                        cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
                        val_adq, dep_acumulada, valor_neto, estado, situacion,
                        estado_conservacion, marca, modelo, tipo, color, serie,
                        dimension, otros, observacion, placa, nro_motor, nro_chasis,
                        matricula, anio, nota, codigo_personal, codigo_ubicacion_inicial,
                        codigo_ubicacion_final, user_id, foto_url, fecha_inventariado,
                        inventariado, fecha_servidor, created_at, updated_at, deleted_at,
                        Column8, Column9
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    ast.get("id"), ast.get("codigo_interno"), ast.get("codigo_patrimonial"),
                    ast.get("denominacion"), ast.get("cuenta_contable", ""), ast.get("denominacion_cuenta", ""),
                    ast.get("nro_doc_adq", ""), ast.get("fech_adq"), ast.get("val_adq", 0),
                    ast.get("dep_acumulada", 0), ast.get("valor_neto", 0), ast.get("estado", ""),
                    ast.get("situacion", ""), ast.get("estado_conservacion", ""), ast.get("marca", ""),
                    ast.get("modelo", ""), ast.get("tipo", ""), ast.get("color", ""),
                    ast.get("serie", ""), ast.get("dimension", ""), ast.get("otros", ""),
                    ast.get("observacion", ""), ast.get("placa", ""), ast.get("nro_motor", ""),
                    ast.get("nro_chasis", ""), ast.get("matricula", ""), ast.get("anio", ""),
                    ast.get("nota", ""), ast.get("codigo_personal", ""), ast.get("codigo_ubicacion_inicial", 0),
                    ast.get("codigo_ubicacion_final", 0), ast.get("user_id", 0), ast.get("foto_url", ""),
                    ast.get("fecha_inventariado"), ast.get("inventariado", 0), ast.get("fecha_servidor"),
                    ast.get("created_at"), ast.get("updated_at"), ast.get("deleted_at"),
                    ast.get("Column8"), ast.get("Column9")
                ))

            # 4. Inventory Records
            for inv in data.get("inventory_records", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO inventory_records (
                        id, asset_id, codigo_interno, codigo_patrimonial, denominacion,
                        cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
                        val_adq, dep_acumulada, valor_neto, estado, situacion,
                        estado_conservacion, marca, modelo, tipo, color, serie,
                        dimension, otros, observacion, placa, nro_motor, nro_chasis,
                        matricula, anio, nota, codigo_personal, codigo_ubicacion_inicial,
                        codigo_ubicacion_final, user_id, foto_url, fecha_inventariado,
                        inventariado, fecha_servidor, created_at, updated_at, deleted_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    inv.get("id"), inv.get("asset_id"), inv.get("codigo_interno"),
                    inv.get("codigo_patrimonial"), inv.get("denominacion"), inv.get("cuenta_contable", ""),
                    inv.get("denominacion_cuenta", ""), inv.get("nro_doc_adq", ""), inv.get("fech_adq"),
                    inv.get("val_adq", 0), inv.get("dep_acumulada", 0), inv.get("valor_neto", 0),
                    inv.get("estado", ""), inv.get("situacion", ""), inv.get("estado_conservacion", ""),
                    inv.get("marca", ""), inv.get("modelo", ""), inv.get("tipo", ""),
                    inv.get("color", ""), inv.get("serie", ""), inv.get("dimension", ""),
                    inv.get("otros", ""), inv.get("observacion", ""), inv.get("placa", ""),
                    inv.get("nro_motor", ""), inv.get("nro_chasis", ""), inv.get("matricula", ""),
                    inv.get("anio", ""), inv.get("nota", ""), inv.get("codigo_personal", ""),
                    inv.get("codigo_ubicacion_inicial", 0), inv.get("codigo_ubicacion_final", 0),
                    inv.get("user_id", 0), inv.get("foto_url", ""), inv.get("fecha_inventariado"),
                    inv.get("inventariado", 0), inv.get("fecha_servidor"), inv.get("created_at"),
                    inv.get("updated_at"), inv.get("deleted_at")
                ))

            # 5. Surplus
            for sur in data.get("surplus", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO surplus (
                        id, codigo_interno, codigo_patrimonial, codigo_ubicacion,
                        codigo_personal, denominacion, marca, modelo, tipo, color,
                        serie, dimension, otros, situacion, estado_conservacion,
                        observacion, created_at, updated_at, deleted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sur.get("id"), sur.get("codigo_interno", ""), sur.get("codigo_patrimonial", ""),
                    sur.get("codigo_ubicacion", 0), sur.get("codigo_personal", 0),
                    sur.get("denominacion"), sur.get("marca", ""), sur.get("modelo", ""),
                    sur.get("tipo", ""), sur.get("color", ""), sur.get("serie", ""),
                    sur.get("dimension", ""), sur.get("otros", ""), sur.get("situacion", ""),
                    sur.get("estado_conservacion", ""), sur.get("observacion", ""),
                    sur.get("created_at"), sur.get("updated_at"), sur.get("deleted_at")
                ))

            # 6. Asset Photos (si viene del servidor)
            for photo in data.get("asset_photos", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO asset_photos (
                        id, asset_id, codigo_interno, ruta_foto, fecha,
                        sincronizado, created_at, updated_at, deleted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    photo.get("id"), photo.get("asset_id"), photo.get("codigo_interno"),
                    photo.get("ruta_foto"), photo.get("fecha"), photo.get("sincronizado", 0),
                    photo.get("created_at"), photo.get("updated_at"), photo.get("deleted_at")
                ))

            # 7. Teams (si viene del servidor)
            for tm in data.get("teams", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO teams (
                        id, nombre, capturador_id, auxiliar_id, estado, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tm.get("id"), tm.get("nombre"), tm.get("capturador_id"),
                    tm.get("auxiliar_id"), tm.get("estado", "ACTIVO"),
                    tm.get("created_at"), tm.get("updated_at")
                ))

            # 8. Users (si viene del servidor)
            for usr in data.get("users", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO users (
                        id, nombres, apellidos, correo, usuario, password_hash,
                        rol, estado, created_at, updated_at, token
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usr.get("id"),
                    usr.get("nombres") or "",
                    usr.get("apellidos") or "",
                    usr.get("correo"),
                    usr.get("usuario") or "",
                    usr.get("password_hash") or "",
                    usr.get("rol") or "inventariador",
                    1 if usr.get("estado") is None else usr.get("estado"),
                    usr.get("created_at"),
                    usr.get("updated_at"),
                    usr.get("token") or ""
                ))

            # 9. Inventory Assignments (si viene del servidor)
            for asg in data.get("inventory_assignments", []):
                cursor.execute("""
                    INSERT OR REPLACE INTO inventory_assignments (
                        id, team_id, location_id, fecha_programada, estado, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    asg.get("id"), asg.get("team_id"), asg.get("location_id"),
                    asg.get("fecha_programada"), asg.get("estado", "PENDIENTE"),
                    asg.get("created_at"), asg.get("updated_at")
                ))

            self.db.commit()
            return {"status": "success"}

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error al procesar inserción en SQLite: {str(e)}"}

    def execute_initial_sync(self, api_client, limit: int = 20000) -> dict:
        """Descarga completa de la base de datos inicial y actualización de tablas operativas locales."""
        try:
            response = api_client.initial_sync(limit=limit)
            data = response.get("data", response)

            res_db = self.process_download_sync(data)
            if res_db.get("status") == "error":
                return res_db

            # Volcado y acoplamiento hacia las tablas locales de interfaz
            self.populate_bienes_from_server()
            self.populate_personal_from_server()
            self.populate_sobrantes_from_server()
            self.populate_usuarios_from_server()

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
            # 1. Primero subimos la cola local para no pisar cambios offline
            envio = sincronizar_inventarios_pendientes(api_client)
            if envio.get("pending", 0):
                return {
                    "status": "deferred",
                    "message": "Hay inventarios locales pendientes de sincronización.",
                }

            # 2. Descargamos novedades del servidor
            response = api_client.sync_changes(last_sync=last_sync, limit=limit)
            payload = response.get("data", {})
            changes = payload.get("changes", {})
            server_time = payload.get("server_time")

            res_db = self.process_download_sync(changes)
            if res_db.get("status") == "error":
                return res_db

            # 3. Refrescamos las tablas locales de trabajo
            self.populate_bienes_from_server()
            self.populate_personal_from_server()
            self.populate_sobrantes_from_server()
            self.populate_usuarios_from_server()

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
        """Puebla la tabla local 'bienes' desde 'inventory_records' aplicando todas las equivalencias."""
        try:
            sql = """
                INSERT OR REPLACE INTO bienes (
                    CodInt, ActaAnt, Inv, CodPat, DenBien, NroDocAdq, FechAdq,
                    ValAdq, DepAcum, ValNeto, CtaCont, DenCta, Estado, Marca,
                    Modelo, Tipo, Color, Serie, Dimension, Placa, NroMotor,
                    NroChasis, Matricula, AñoFab, Nota, Obs, FechInv, Otros,
                    Situacion, Inventariador, Equipo
                )
                SELECT 
                    CAST(ir.codigo_interno AS INTEGER),
                    ir.codigo_ubicacion_inicial,
                    CASE WHEN COALESCE(ir.inventariado, 0) = 1
                         THEN ir.codigo_ubicacion_final ELSE '' END,
                    ir.codigo_patrimonial,
                    ir.denominacion,
                    ir.nro_doc_adq,
                    ir.fech_adq,
                    ir.val_adq,
                    ir.dep_acumulada,
                    ir.valor_neto,
                    ir.cuenta_contable,
                    ir.denominacion_cuenta,
                    COALESCE(ir.estado_conservacion, ir.estado),
                    ir.marca,
                    ir.modelo,
                    ir.tipo,
                    ir.color,
                    ir.serie,
                    ir.dimension,
                    ir.placa,
                    ir.nro_motor,
                    ir.nro_chasis,
                    ir.matricula,
                    CAST(ir.anio AS TEXT),
                    ir.nota,
                    ir.observacion,
                    CASE WHEN COALESCE(ir.inventariado, 0) = 1
                         THEN ir.fecha_inventariado ELSE NULL END,
                    ir.otros,
                    ir.situacion,
                    CASE WHEN COALESCE(ir.inventariado, 0) = 1
                         THEN CAST(ir.user_id AS TEXT) ELSE NULL END,
                    COALESCE(loc.team_id, '')
                FROM inventory_records ir
                LEFT JOIN locations loc ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT);
            """
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            print("[OK] Tabla 'bienes' sincronizada correctamente desde 'inventory_records'.")
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] al volcar inventory_records a bienes: {e}")

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
            print("[OK] Tabla local 'personal' actualizada correctamente.")
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] al poblar tabla personal: {e}")

    def populate_sobrantes_from_server(self):
        """Puebla la tabla local 'sobrantes' cruzando 'surplus' con 'locations'."""
        try:
            sql = """
                INSERT OR REPLACE INTO sobrantes (
                    item, acta, local, area, oficina, den, estado, dim, marca,
                    modelo, serie, color, obs, tipo, otros, situacion, nota
                )
                SELECT 
                    s.id,
                    COALESCE(l.codigo_ubicacion, CAST(s.codigo_ubicacion AS TEXT)),
                    COALESCE(l.local, ''),
                    COALESCE(l.area, ''),
                    COALESCE(l.oficina, ''),
                    s.denominacion,
                    COALESCE(s.estado_conservacion, ''),
                    COALESCE(s.dimension, ''),
                    COALESCE(s.marca, ''),
                    COALESCE(s.modelo, ''),
                    COALESCE(s.serie, ''),
                    COALESCE(s.color, ''),
                    COALESCE(s.observacion, ''),
                    COALESCE(s.tipo, ''),
                    COALESCE(s.otros, ''),
                    COALESCE(s.situacion, ''),
                    COALESCE(s.codigo_patrimonial, '')
                FROM surplus s
                LEFT JOIN locations l ON CAST(l.codigo_ubicacion AS TEXT) = CAST(s.codigo_ubicacion AS TEXT);
            """
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            print("[OK] Tabla local 'sobrantes' actualizada correctamente.")
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] al poblar tabla sobrantes: {e}")

    def populate_usuarios_from_server(self):
        """Puebla la tabla local 'usuarios' desde 'users' para permitir el login offline."""
        try:
            sql = """
                INSERT OR REPLACE INTO usuarios (
                    id, usuario, password, Nombres, APat, AMat, dni, equipo
                )
                SELECT 
                    u.id,
                    u.usuario,
                    u.password_hash,
                    u.nombres,
                    u.apellidos,
                    '',
                    CAST(u.id AS TEXT),
                    COALESCE(u.rol, '')
                FROM users u;
            """
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            print("[OK] Tabla local 'usuarios' actualizada correctamente desde 'users'.")
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] al poblar tabla usuarios: {e}")
