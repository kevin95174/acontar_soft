# services/sync_service.py
from datetime import datetime
from services.db_mirror import (
    reconciliar_tablas_locales_a_servidor,
    sincronizar_cola_completa,
)
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
        usando las tablas nativas del servidor (1:1 con MySQL), preservando
        las columnas auxiliares locales cuando no vienen en el JSON.
        """
        try:
            cursor = self.db.cursor()

            # 1. Locations
            for loc in data.get("locations", []):
                loc_id = loc.get("id")
                cod_ubi = loc.get("codigo_ubicacion")
                cursor.execute("""
                    INSERT OR REPLACE INTO locations (
                        id, codigo_ubicacion, dep, prov, dist, local, area, oficina,
                        piso, direccion, codigo_personal, team_id,
                        created_at, updated_at, deleted_at
                    ) VALUES (
                        ?, ?,
                        COALESCE(?, (SELECT dep FROM locations WHERE id = ? OR CAST(codigo_ubicacion AS TEXT) = CAST(? AS TEXT) LIMIT 1), ''),
                        COALESCE(?, (SELECT prov FROM locations WHERE id = ? OR CAST(codigo_ubicacion AS TEXT) = CAST(? AS TEXT) LIMIT 1), ''),
                        COALESCE(?, (SELECT dist FROM locations WHERE id = ? OR CAST(codigo_ubicacion AS TEXT) = CAST(? AS TEXT) LIMIT 1), ''),
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    loc_id, cod_ubi,
                    loc.get("dep"), loc_id, cod_ubi,
                    loc.get("prov"), loc_id, cod_ubi,
                    loc.get("dist"), loc_id, cod_ubi,
                    loc.get("local"), loc.get("area"), loc.get("oficina"),
                    loc.get("piso"), loc.get("direccion"), loc.get("codigo_personal"),
                    loc.get("team_id", ""), loc.get("created_at"),
                    loc.get("updated_at"), loc.get("deleted_at")
                ))

            # 2. Personnel
            for per in data.get("personnel", []):
                cod_per = per.get("codigo_personal")
                cursor.execute("""
                    INSERT OR REPLACE INTO personnel (
                        id, codigo_personal, nombres, apellidos, apellido_mat,
                        cargo, oficina, telefono, email, estado,
                        created_at, updated_at, deleted_at
                    ) VALUES (
                        ?, ?, ?, ?,
                        COALESCE(?, (SELECT apellido_mat FROM personnel WHERE codigo_personal = ? LIMIT 1), ''),
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    per.get("id"), cod_per, per.get("nombres"),
                    per.get("apellidos"),
                    per.get("apellido_mat"), cod_per,
                    per.get("cargo"), per.get("oficina"),
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
                inv_id = inv.get("id")
                cursor.execute("""
                    INSERT OR REPLACE INTO inventory_records (
                        id, asset_id, codigo_interno, codigo_patrimonial, denominacion,
                        cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
                        val_adq, dep_acumulada, valor_neto, estado, situacion,
                        estado_conservacion, marca, modelo, tipo, color, serie,
                        dimension, otros, observacion, placa, nro_motor, nro_chasis,
                        matricula, anio, nota, codigo_personal, codigo_ubicacion_inicial,
                        codigo_ubicacion_final, user_id, foto_url, fecha_inventariado,
                        inventariador_local, equipo_local,
                        inventariado, fecha_servidor, created_at, updated_at, deleted_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        COALESCE((SELECT inventariador_local FROM inventory_records WHERE id = ?), ''),
                        COALESCE((SELECT equipo_local FROM inventory_records WHERE id = ?), ''),
                        ?, ?, ?, ?, ?
                    )
                """, (
                    inv_id, inv.get("asset_id"), inv.get("codigo_interno"),
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
                    inv_id, inv_id,
                    inv.get("inventariado", 0), inv.get("fecha_servidor"), inv.get("created_at"),
                    inv.get("updated_at"), inv.get("deleted_at")
                ))

            # 5. Surplus
            for sur in data.get("surplus", []):
                sur_id = sur.get("id")
                cursor.execute("""
                    INSERT OR REPLACE INTO surplus (
                        id, codigo_interno, codigo_patrimonial, codigo_ubicacion,
                        codigo_personal, local_override, area_override, oficina_override,
                        denominacion, marca, modelo, tipo, color,
                        serie, dimension, otros, situacion, estado_conservacion,
                        observacion, created_at, updated_at, deleted_at
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        COALESCE(?, (SELECT local_override FROM surplus WHERE id = ?), ''),
                        COALESCE(?, (SELECT area_override FROM surplus WHERE id = ?), ''),
                        COALESCE(?, (SELECT oficina_override FROM surplus WHERE id = ?), ''),
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    sur_id, sur.get("codigo_interno", ""), sur.get("codigo_patrimonial", ""),
                    sur.get("codigo_ubicacion", 0), sur.get("codigo_personal", 0),
                    sur.get("local"), sur_id,
                    sur.get("area"), sur_id,
                    sur.get("oficina"), sur_id,
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
                usr_id = usr.get("id")
                usr_key = usr.get("usuario") or ""
                cursor.execute("""
                    INSERT OR REPLACE INTO users (
                        id, nombres, apellidos, apellido_mat, dni,
                        correo, usuario, password_hash,
                        rol, estado, created_at, updated_at, token
                    ) VALUES (
                        ?, ?, ?,
                        COALESCE((SELECT apellido_mat FROM users WHERE id = ? OR usuario = ? LIMIT 1), ''),
                        COALESCE((SELECT dni FROM users WHERE id = ? OR usuario = ? LIMIT 1), CAST(? AS TEXT)),
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    usr_id,
                    usr.get("nombres") or "",
                    usr.get("apellidos") or "",
                    usr_id, usr_key,
                    usr_id, usr_key, usr_id,
                    usr.get("correo"),
                    usr_key,
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
        """Descarga completa de la base de datos inicial en las tablas del servidor."""
        try:
            reconciliar_tablas_locales_a_servidor(self.db)
            sincronizar_cola_completa(api_client, limite=100)

            response = api_client.initial_sync(limit=limit)
            data = response.get("data", response)

            res_db = self.process_download_sync(data)
            if res_db.get("status") == "error":
                return res_db

            # Sembrar ficha técnica vehicular para activos con placa/motor/chasis
            self.populate_vehiculos_from_server()

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
            reconciliar_tablas_locales_a_servidor(self.db)
            envio = sincronizar_cola_completa(api_client, limite=100)
            if envio.get("pending", 0):
                return {
                    "status": "deferred",
                    "message": (
                        f"Hay {envio.get('pending')} cambios locales pendientes de sincronización "
                        f"({envio.get('pending_inventory', 0)} inventarios, {envio.get('pending_mutations', 0)} ediciones)."
                    ),
                }

            response = api_client.sync_changes(last_sync=last_sync, limit=limit)
            payload = response.get("data", {})
            changes = payload.get("changes", {})
            server_time = payload.get("server_time")

            res_db = self.process_download_sync(changes)
            if res_db.get("status") == "error":
                return res_db

            self.populate_vehiculos_from_server()

            if server_time:
                set_config(self.db, "last_sync_timestamp", server_time)

            total_novedades = sum(len(v) for v in changes.values() if isinstance(v, list))

            return {
                "status": "success",
                "message": (
                    f"Sincronización finalizada ({envio.get('synced', 0)} subidos, "
                    f"{total_novedades} descargados)."
                ),
                "server_time": server_time
            }

        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": f"Error en Sync Changes: {str(e)}"}

    def populate_bienes_from_server(self):
        """
        En el esquema unificado (Fase 2/3), `bienes` es una VISTA SQL viva sobre
        `inventory_records`, `locations` y `users`, por lo que siempre está 100%
        sincronizada en tiempo real sin duplicar filas.
        """
        print("[OK] Vista unificada 'bienes' activa sobre 'inventory_records' (sin duplicación).")

    def populate_personal_from_server(self):
        """
        En el esquema unificado (Fase 2/3), `personal` es una VISTA SQL viva sobre
        `locations` y `personnel`, reflejando los datos en tiempo real.
        """
        print("[OK] Vista unificada 'personal' activa sobre 'locations' + 'personnel' (sin duplicación).")

    def populate_sobrantes_from_server(self):
        """
        En el esquema unificado (Fase 2/3), `sobrantes` es una VISTA SQL viva sobre
        `surplus` y `locations`, reflejando los datos en tiempo real.
        """
        print("[OK] Vista unificada 'sobrantes' activa sobre 'surplus' + 'locations' (sin duplicación).")

    def populate_usuarios_from_server(self):
        """
        En el esquema unificado (Fase 2/3), `usuarios` es una VISTA SQL viva sobre `users`.
        """
        print("[OK] Vista unificada 'usuarios' activa sobre 'users' (sin duplicación).")

    def populate_vehiculos_from_server(self):
        """
        Registra automáticamente en la tabla local 'vehiculos' los bienes de 'inventory_records'
        que tengan datos vehiculares (placa, motor o chasis), sin sobrescribir las inspecciones
        mecánicas de sistemas ya registradas localmente.
        """
        try:
            sql = """
                INSERT OR IGNORE INTO vehiculos (
                    CodInt, Entidad, CodPat, DenBien, NroPlaca, Carroceria,
                    Marca, Modelo, Categoria, NroChasis, NroEjes, NroMotor,
                    NroSerie, AFab, Color
                )
                SELECT
                    CAST(ir.codigo_interno AS INTEGER),
                    COALESCE((SELECT entidad FROM datos LIMIT 1), ''),
                    ir.codigo_patrimonial,
                    ir.denominacion,
                    ir.placa,
                    ir.tipo,
                    ir.marca,
                    ir.modelo,
                    '',
                    ir.nro_chasis,
                    '',
                    ir.nro_motor,
                    ir.serie,
                    CAST(ir.anio AS TEXT),
                    ir.color
                FROM inventory_records ir
                WHERE COALESCE(TRIM(ir.placa), '') <> ''
                   OR COALESCE(TRIM(ir.nro_motor), '') <> ''
                   OR COALESCE(TRIM(ir.nro_chasis), '') <> '';
            """
            cursor = self.db.cursor()
            cursor.execute(sql)
            self.db.commit()
            print("[OK] Tabla local 'vehiculos' sincronizada desde 'inventory_records'.")
        except Exception as e:
            self.db.rollback()
            print(f"[ERROR] al poblar tabla vehiculos: {e}")
