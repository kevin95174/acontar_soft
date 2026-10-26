"""
services/db_mirror.py
Motor nativo de escritura y sincronización bidireccional sobre las tablas del servidor
(`inventory_records`, `assets`, `locations`, `personnel`, `surplus`, `users`, `asset_photos`),
incluyendo encolamiento offline en `inventory_sync_outbox` y `sync_mutations_outbox`.
"""

import json
import os
import threading
from datetime import datetime
from db.conex import iniciar_conexion_sqlite
from utils.api_client import ApiManagerAcontarSacClient

_BG_SYNC_LOCK = threading.Lock()


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_outbox_tables(cur):
    """Garantiza que las tablas de cola offline existan en la base de datos."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_sync_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id INTEGER NOT NULL UNIQUE,
        codigo_ubicacion_final TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        status TEXT NOT NULL DEFAULT 'pending'
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sync_mutations_outbox (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_key TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT DEFAULT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        UNIQUE(entity_type, entity_key)
    );
    """)


def enqueue_mutation(cur, entity_type: str, entity_key: str, payload: dict):
    """Inserta o actualiza una mutación pendiente en `sync_mutations_outbox`."""
    ensure_outbox_tables(cur)
    now_str = _now_iso()
    payload_json = json.dumps(payload, ensure_ascii=False)
    cur.execute("""
        INSERT INTO sync_mutations_outbox (
            entity_type, entity_key, payload, created_at, attempts, last_error, status
        ) VALUES (?, ?, ?, ?, 0, NULL, 'pending')
        ON CONFLICT(entity_type, entity_key) DO UPDATE SET
            payload = excluded.payload,
            created_at = excluded.created_at,
            attempts = 0,
            last_error = NULL,
            status = 'pending'
    """, (str(entity_type), str(entity_key), payload_json, now_str))


def remove_mutation(cur, entity_type: str, entity_key: str):
    """Elimina una mutación pendiente de la cola si el registro fue borrado o revertido."""
    ensure_outbox_tables(cur)
    cur.execute("""
        DELETE FROM sync_mutations_outbox
        WHERE entity_type = ? AND entity_key = ?
    """, (str(entity_type), str(entity_key)))


def find_inventory_record_id(cur, codigo) -> int | None:
    """Obtiene el `id` en `inventory_records` a partir de `CodPat` o `CodInt`."""
    codigo_str = str(codigo).strip()
    if not codigo_str:
        return None
    cur.execute("""
        SELECT id FROM inventory_records
        WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        LIMIT 1
    """, (codigo_str, codigo_str))
    row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else None


def mirror_inventario(
    cur,
    codigo,
    inv,
    fech_inv: str = None,
    user_id: int = 1,
    inventariador: str = None,
    equipo: str = None,
) -> int:
    """
    Actualiza directamente `inventory_records` y `assets` (asignación o liberación de inventario)
    y encola la operación en `inventory_sync_outbox` o `sync_mutations_outbox` (`uninventory`).
    Devuelve la cantidad de filas afectadas en `inventory_records`.
    """
    ensure_outbox_tables(cur)
    codigo_str = str(codigo).strip()
    inv_str = str(inv).strip() if inv is not None else ""
    es_desinventariado = (inv_str == "" or inv_str == "0")
    fech_str = fech_inv or datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    now_iso = _now_iso()
    uid = int(user_id or 1)
    inv_usr_str = str(inventariador).strip() if inventariador is not None else ""
    equipo_str = str(equipo).strip() if equipo is not None else ""

    record_id = find_inventory_record_id(cur, codigo_str)

    if es_desinventariado:
        cur.execute("""
            UPDATE inventory_records
            SET codigo_ubicacion_final = 0,
                inventariado = 0,
                fecha_inventariado = NULL,
                inventariador_local = '',
                equipo_local = '',
                fecha_servidor = NULL,
                updated_at = ?
            WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        """, (now_iso, codigo_str, codigo_str))
        affected = cur.rowcount

        cur.execute("""
            UPDATE assets
            SET codigo_ubicacion_final = 0,
                inventariado = 0,
                fecha_inventariado = NULL,
                updated_at = ?
            WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        """, (now_iso, codigo_str, codigo_str))

        if record_id is not None:
            cur.execute("DELETE FROM inventory_sync_outbox WHERE record_id = ?", (record_id,))
            enqueue_mutation(cur, "uninventory", str(record_id), {
                "id": record_id,
                "user_id": uid,
            })
    else:
        cur.execute("""
            UPDATE inventory_records
            SET codigo_ubicacion_final = ?,
                inventariado = 1,
                user_id = ?,
                fecha_inventariado = ?,
                inventariador_local = CASE WHEN ? <> '' THEN ? ELSE COALESCE(inventariador_local, '') END,
                equipo_local = CASE WHEN ? <> '' THEN ? ELSE COALESCE(equipo_local, '') END,
                fecha_servidor = NULL,
                updated_at = ?
            WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        """, (
            inv_str, uid, fech_str,
            inv_usr_str, inv_usr_str,
            equipo_str, equipo_str,
            now_iso, codigo_str, codigo_str,
        ))
        affected = cur.rowcount

        cur.execute("""
            UPDATE assets
            SET codigo_ubicacion_final = ?,
                inventariado = 1,
                user_id = ?,
                fecha_inventariado = ?,
                updated_at = ?
            WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        """, (inv_str, uid, fech_str, now_iso, codigo_str, codigo_str))

        if record_id is not None:
            remove_mutation(cur, "uninventory", str(record_id))
            cur.execute("""
                INSERT INTO inventory_sync_outbox (
                    record_id, codigo_ubicacion_final, user_id, created_at, status
                ) VALUES (?, ?, ?, ?, 'pending')
                ON CONFLICT(record_id) DO UPDATE SET
                    codigo_ubicacion_final = excluded.codigo_ubicacion_final,
                    user_id = excluded.user_id,
                    created_at = excluded.created_at,
                    attempts = 0,
                    last_error = NULL,
                    status = 'pending'
            """, (record_id, inv_str, uid, fech_str))

    return affected


def mirror_detalles(cur, codigo, fields: dict):
    """
    Actualiza directamente los detalles técnicos en `inventory_records` y `assets`,
    y encola la petición `update_technical_details` en `sync_mutations_outbox`.
    """
    ensure_outbox_tables(cur)
    codigo_str = str(codigo).strip()
    if not codigo_str:
        return

    now_iso = _now_iso()

    col_map = {
        "marca": fields.get("marca"),
        "modelo": fields.get("modelo"),
        "color": fields.get("color"),
        "serie": fields.get("serie"),
        "estado_conservacion": fields.get("estado"),
        "estado": fields.get("estado"),
        "dimension": fields.get("dimension"),
        "observacion": fields.get("observacion"),
        "otros": fields.get("otros"),
        "situacion": fields.get("situacion"),
        "fech_adq": fields.get("fech_adq"),
        "nro_doc_adq": fields.get("nro_doc_adq"),
        "nota": fields.get("nota"),
        "tipo": fields.get("tipo"),
        "denominacion": fields.get("denominacion"),
        "placa": fields.get("placa"),
        "nro_motor": fields.get("nro_motor"),
        "nro_chasis": fields.get("nro_chasis"),
        "anio": fields.get("anio"),
    }

    updates = {k: v for k, v in col_map.items() if v is not None}
    if not updates:
        return

    updates["updated_at"] = now_iso
    set_clause = ", ".join(f"{col} = ?" for col in updates.keys())
    params = list(updates.values()) + [codigo_str, codigo_str]

    cur.execute(f"""
        UPDATE inventory_records
        SET {set_clause}
        WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
    """, params)

    cur.execute(f"""
        UPDATE assets
        SET {set_clause}
        WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
    """, params)

    cur.execute("""
        SELECT id, asset_id, codigo_interno, codigo_patrimonial, denominacion,
               marca, modelo, tipo, color, serie, dimension, estado_conservacion,
               situacion, observacion, otros, nota, fech_adq, nro_doc_adq,
               placa, nro_motor, nro_chasis, anio
        FROM inventory_records
        WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
        LIMIT 1
    """, (codigo_str, codigo_str))
    row = cur.fetchone()

    if row:
        payload = {
            "id": row[0],
            "asset_id": row[1],
            "codigo_interno": str(row[2] or ""),
            "codigo_patrimonial": str(row[3] or ""),
            "denominacion": str(row[4] or ""),
            "marca": str(row[5] or ""),
            "modelo": str(row[6] or ""),
            "tipo": str(row[7] or ""),
            "color": str(row[8] or ""),
            "serie": str(row[9] or ""),
            "dimension": str(row[10] or ""),
            "estado_conservacion": str(row[11] or ""),
            "estado": str(row[11] or ""),
            "situacion": str(row[12] or ""),
            "observacion": str(row[13] or ""),
            "otros": str(row[14] or ""),
            "nota": str(row[15] or ""),
            "fech_adq": str(row[16] or ""),
            "nro_doc_adq": str(row[17] or ""),
            "placa": str(row[18] or ""),
            "nro_motor": str(row[19] or ""),
            "nro_chasis": str(row[20] or ""),
            "anio": str(row[21] or ""),
        }
        entity_key = str(row[0])
    else:
        payload = {"codigo": codigo_str, **{k: str(v) for k, v in updates.items() if k != "updated_at"}}
        entity_key = codigo_str

    enqueue_mutation(cur, "technical_details", entity_key, payload)


def mirror_sobrante(
    cur, item_id: int | None, acta, local, area, oficina, den, estado, dim,
    marca, modelo, serie, color, obs, tipo="", otros="", situacion="", nota=""
) -> int:
    """
    Inserta o actualiza un bien sobrante directamente en `surplus`
    y lo encola en `sync_mutations_outbox`. Devuelve el `id` del sobrante.
    """
    ensure_outbox_tables(cur)
    now_iso = _now_iso()
    acta_str = str(acta or "").strip()

    codigo_personal = ""
    if acta_str:
        cur.execute("""
            SELECT codigo_personal FROM locations
            WHERE CAST(codigo_ubicacion AS TEXT) = ?
            LIMIT 1
        """, (acta_str,))
        loc_row = cur.fetchone()
        if loc_row and loc_row[0]:
            codigo_personal = str(loc_row[0])

    if item_id is None:
        cur.execute("""
            INSERT INTO surplus (
                codigo_interno, codigo_patrimonial, codigo_ubicacion,
                codigo_personal, local_override, area_override, oficina_override,
                denominacion, marca, modelo, tipo, color,
                serie, dimension, otros, situacion, estado_conservacion,
                observacion, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            "",
            str(nota or ""),
            acta_str,
            codigo_personal,
            str(local or ""),
            str(area or ""),
            str(oficina or ""),
            str(den or ""),
            str(marca or ""),
            str(modelo or ""),
            str(tipo or ""),
            str(color or ""),
            str(serie or ""),
            str(dim or ""),
            str(otros or ""),
            str(situacion or ""),
            str(estado or ""),
            str(obs or ""),
            now_iso,
            now_iso,
        ))
        item_id = cur.lastrowid
    else:
        cur.execute("""
            INSERT OR REPLACE INTO surplus (
                id, codigo_interno, codigo_patrimonial, codigo_ubicacion,
                codigo_personal, local_override, area_override, oficina_override,
                denominacion, marca, modelo, tipo, color,
                serie, dimension, otros, situacion, estado_conservacion,
                observacion, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
                (SELECT created_at FROM surplus WHERE id = ?), ?
            ), ?, NULL)
        """, (
            int(item_id),
            "",
            str(nota or ""),
            acta_str,
            codigo_personal,
            str(local or ""),
            str(area or ""),
            str(oficina or ""),
            str(den or ""),
            str(marca or ""),
            str(modelo or ""),
            str(tipo or ""),
            str(color or ""),
            str(serie or ""),
            str(dim or ""),
            str(otros or ""),
            str(situacion or ""),
            str(estado or ""),
            str(obs or ""),
            int(item_id),
            now_iso,
            now_iso,
        ))

    payload = {
        "id": int(item_id),
        "codigo_interno": "",
        "codigo_patrimonial": str(nota or ""),
        "codigo_ubicacion": acta_str,
        "codigo_personal": codigo_personal,
        "local": str(local or ""),
        "area": str(area or ""),
        "oficina": str(oficina or ""),
        "denominacion": str(den or ""),
        "estado_conservacion": str(estado or ""),
        "dimension": str(dim or ""),
        "marca": str(marca or ""),
        "modelo": str(modelo or ""),
        "serie": str(serie or ""),
        "color": str(color or ""),
        "observacion": str(obs or ""),
        "tipo": str(tipo or ""),
        "otros": str(otros or ""),
        "situacion": str(situacion or ""),
    }
    enqueue_mutation(cur, "surplus", str(item_id), payload)
    return int(item_id)


def mirror_delete_sobrante(cur, item_id):
    """Elimina el sobrante de `surplus` y limpia su mutación pendiente."""
    ensure_outbox_tables(cur)
    cur.execute("DELETE FROM surplus WHERE id = ?", (int(item_id),))
    remove_mutation(cur, "surplus", str(item_id))


def mirror_personal(
    cur, acta, dep, prov, dist, local, area, oficina,
    dni, nombre, apellido_pat, apellido_mat, equi_inv=""
):
    """
    Inserta o actualiza directamente en `locations` y `personnel`,
    y encola ambas actualizaciones en `sync_mutations_outbox`.
    """
    ensure_outbox_tables(cur)
    now_iso = _now_iso()
    acta_str = str(acta or "").strip()
    dep_str = str(dep or "").strip()
    prov_str = str(prov or "").strip()
    dist_str = str(dist or "").strip()
    dni_str = str(dni or "").strip()
    nombre_str = str(nombre or "").strip()
    apat_str = str(apellido_pat or "").strip()
    amat_str = str(apellido_mat or "").strip()
    apellidos_full = " ".join(part for part in [apat_str, amat_str] if part).strip()
    local_str = str(local or "").strip()
    area_str = str(area or "").strip()
    oficina_str = str(oficina or "").strip()
    equi_str = str(equi_inv or "").strip()
    direccion_str = " - ".join(p for p in [dep_str, prov_str, dist_str] if p)

    if acta_str:
        cur.execute("""
            SELECT id FROM locations WHERE CAST(codigo_ubicacion AS TEXT) = ? LIMIT 1
        """, (acta_str,))
        loc_row = cur.fetchone()
        if loc_row:
            cur.execute("""
                UPDATE locations
                SET dep = ?, prov = ?, dist = ?, local = ?, area = ?, oficina = ?,
                    direccion = COALESCE(NULLIF(?, ''), direccion),
                    codigo_personal = ?, team_id = COALESCE(NULLIF(?, ''), team_id), updated_at = ?
                WHERE id = ?
            """, (dep_str, prov_str, dist_str, local_str, area_str, oficina_str, direccion_str, dni_str, equi_str, now_iso, loc_row[0]))
            loc_id = loc_row[0]
        else:
            cur.execute("""
                INSERT INTO locations (
                    codigo_ubicacion, dep, prov, dist, local, area, oficina, direccion,
                    codigo_personal, team_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (acta_str, dep_str, prov_str, dist_str, local_str, area_str, oficina_str, direccion_str, dni_str, equi_str, now_iso, now_iso))
            loc_id = cur.lastrowid

        loc_payload = {
            "id": loc_id,
            "codigo_ubicacion": acta_str,
            "local": local_str,
            "area": area_str,
            "oficina": oficina_str,
            "direccion": direccion_str,
            "codigo_personal": dni_str,
            "team_id": equi_str,
        }
        enqueue_mutation(cur, "location", acta_str, loc_payload)

    if dni_str:
        cur.execute("""
            INSERT INTO personnel (
                codigo_personal, nombres, apellidos, apellido_mat, cargo, oficina, estado, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, '1', ?, ?)
            ON CONFLICT(codigo_personal) DO UPDATE SET
                nombres = excluded.nombres,
                apellidos = excluded.apellidos,
                apellido_mat = excluded.apellido_mat,
                cargo = COALESCE(NULLIF(excluded.cargo, ''), personnel.cargo),
                oficina = excluded.oficina,
                updated_at = excluded.updated_at
        """, (dni_str, nombre_str, apat_str, amat_str, equi_str, oficina_str, now_iso, now_iso))

        per_payload = {
            "codigo_personal": dni_str,
            "nombres": nombre_str,
            "apellidos": apellidos_full,
            "cargo": equi_str,
            "oficina": oficina_str,
            "estado": "1",
        }
        enqueue_mutation(cur, "personnel", dni_str, per_payload)


def mirror_delete_personal(cur, acta):
    """Elimina la ubicación de `locations` y limpia su mutación pendiente."""
    ensure_outbox_tables(cur)
    acta_str = str(acta or "").strip()
    if acta_str:
        cur.execute(
            "DELETE FROM locations WHERE CAST(codigo_ubicacion AS TEXT) = ? OR CAST(id AS TEXT) = ?",
            (acta_str, acta_str),
        )
        remove_mutation(cur, "location", acta_str)


def mirror_usuario(cur, usuario, password, nombres, apat, amat="", dni="", equipo="OPERADOR"):
    """Inserta o actualiza un usuario directamente en la tabla del servidor `users`."""
    now_iso = _now_iso()
    usr_str = str(usuario or "").strip()
    if not usr_str:
        return
    cur.execute("""
        INSERT INTO users (
            nombres, apellidos, apellido_mat, dni, usuario, password_hash, rol, estado, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ON CONFLICT(usuario) DO UPDATE SET
            nombres = excluded.nombres,
            apellidos = excluded.apellidos,
            apellido_mat = excluded.apellido_mat,
            dni = excluded.dni,
            password_hash = excluded.password_hash,
            rol = excluded.rol,
            updated_at = excluded.updated_at
    """, (
        str(nombres or "").strip(),
        str(apat or "").strip(),
        str(amat or "").strip(),
        str(dni or "").strip(),
        usr_str,
        str(password or ""),
        str(equipo or "inventariador"),
        now_iso,
        now_iso,
    ))


def mirror_vehiculo(cur, codigo, data):
    """
    Sincroniza los datos generales del vehículo editados en `vehiculos`
    directamente hacia `inventory_records`, `assets` y la cola `technical_details`.
    `data` = [Entidad, DenBien, NroPlaca, Carroceria, Marca, Modelo, Categoria,
              NroChasis, NroEjes, NroMotor, NroSerie, AFab, Color, ...]
    """
    if not data or len(data) < 13:
        return
    codigo_str = str(codigo).strip()
    den_bien = str(data[1] or "").strip()
    placa = str(data[2] or "").strip()
    marca = str(data[4] or "").strip()
    modelo = str(data[5] or "").strip()
    chasis = str(data[7] or "").strip()
    motor = str(data[9] or "").strip()
    serie = str(data[10] or "").strip()
    afab = str(data[11] or "").strip()
    color = str(data[12] or "").strip()

    mirror_detalles(cur, codigo_str, {
        "denominacion": den_bien if den_bien else None,
        "placa": placa,
        "marca": marca,
        "modelo": modelo,
        "nro_chasis": chasis,
        "nro_motor": motor,
        "serie": serie,
        "anio": afab,
        "color": color,
    })


def reconciliar_tablas_locales_a_servidor(conn):
    """
    Si aún existieran tablas físicas legacy (`bienes`, `personal`, `sobrantes`, `usuarios`),
    las migra a las tablas del servidor y activa las vistas unificadas.
    """
    try:
        from db.init_db import _is_physical_table, init_db
        cur = conn.cursor()
        ensure_outbox_tables(cur)
        if any(_is_physical_table(cur, t) for t in ("bienes", "personal", "sobrantes", "usuarios")):
            init_db(conn)
    except Exception as e:
        print(f"⚠️ Nota en reconciliar_tablas_locales_a_servidor: {e}")


def sincronizar_cola_completa(api_client, limite: int = 50) -> dict:
    """
    Envía todas las colas locales pendientes al servidor:
    1. `sync_mutations_outbox` (ubicaciones, personal, detalles técnicos, sobrantes, des-inventariado)
    2. `inventory_sync_outbox` (asignaciones de ubicación final / inventariado)
    3. `asset_photos` con `sincronizado = 0`
    Los fallos de red detienen el ciclo actual sin borrar ningún registro pendiente.
    """
    if api_client is None:
        return {"synced": 0, "pending": 0, "message": "Cliente API no disponible."}

    conn_sqlite = iniciar_conexion_sqlite()
    synced = 0
    network_failed = False

    try:
        cur = conn_sqlite.cursor()
        ensure_outbox_tables(cur)

        # ------------------------------------------------------------------
        # 1. Procesar `sync_mutations_outbox`
        # ------------------------------------------------------------------
        cur.execute("""
            SELECT id, entity_type, entity_key, payload
            FROM sync_mutations_outbox
            WHERE status = 'pending'
            ORDER BY id
            LIMIT ?
        """, (limite,))
        mutaciones = cur.fetchall()

        for mut_id, entity_type, entity_key, payload_raw in mutaciones:
            try:
                payload = json.loads(payload_raw) if payload_raw else {}
            except Exception:
                payload = {}

            try:
                if entity_type == "location":
                    respuesta = api_client.create_or_update_location(payload)
                elif entity_type == "personnel":
                    respuesta = api_client.create_or_update_personnel(payload)
                elif entity_type == "technical_details":
                    respuesta = api_client.update_technical_details(payload)
                elif entity_type == "surplus":
                    respuesta = api_client.create_or_update_surplus(payload)
                elif entity_type == "uninventory":
                    respuesta = api_client.uninventory_record(
                        payload.get("id", entity_key),
                        payload.get("user_id", 1),
                    )
                else:
                    respuesta = {"status_code": 200, "data": {}}

                status = respuesta.get("status_code")
                detalle = respuesta.get("data", {}).get("message", "Error de sincronización")
            except Exception as error:
                status, detalle = None, str(error)

            if status in (200, 201):
                cur.execute("DELETE FROM sync_mutations_outbox WHERE id = ?", (mut_id,))
                synced += 1
            elif status == 409:
                cur.execute("""
                    UPDATE sync_mutations_outbox
                    SET status = 'conflict', attempts = attempts + 1, last_error = ?
                    WHERE id = ?
                """, (detalle, mut_id))
            else:
                cur.execute("""
                    UPDATE sync_mutations_outbox
                    SET attempts = attempts + 1, last_error = ?
                    WHERE id = ?
                """, (detalle, mut_id))
                network_failed = True
                break

        # ------------------------------------------------------------------
        # 2. Procesar `inventory_sync_outbox`
        # ------------------------------------------------------------------
        if not network_failed:
            cur.execute("""
                SELECT id, record_id, codigo_ubicacion_final, user_id
                FROM inventory_sync_outbox
                WHERE status = 'pending'
                ORDER BY id
                LIMIT ?
            """, (limite,))
            pendientes = cur.fetchall()

            for outbox_id, record_id, ubicacion, user_id in pendientes:
                try:
                    respuesta = api_client.update_ubicacion_final(record_id, ubicacion, user_id)
                    status = respuesta.get("status_code")
                    detalle = respuesta.get("data", {}).get("message", "Error de sincronización")
                except Exception as error:
                    status, detalle = None, str(error)

                if status in (200, 201):
                    cur.execute("DELETE FROM inventory_sync_outbox WHERE id = ?", (outbox_id,))
                    cur.execute("""
                        UPDATE inventory_records
                        SET fecha_servidor = ? WHERE id = ?
                    """, (_now_iso(), record_id))
                    synced += 1
                elif status == 409:
                    cur.execute("""
                        UPDATE inventory_sync_outbox
                        SET status = 'conflict', attempts = attempts + 1, last_error = ?
                        WHERE id = ?
                    """, (detalle, outbox_id))
                else:
                    cur.execute("""
                        UPDATE inventory_sync_outbox
                        SET attempts = attempts + 1, last_error = ? WHERE id = ?
                    """, (detalle, outbox_id))
                    network_failed = True
                    break

        # ------------------------------------------------------------------
        # 3. Procesar fotos locales pendientes en `asset_photos` (sincronizado = 0)
        # ------------------------------------------------------------------
        if not network_failed:
            try:
                cur.execute("""
                    SELECT id, asset_id, codigo_interno, ruta_foto
                    FROM asset_photos
                    WHERE COALESCE(sincronizado, 0) = 0 AND deleted_at IS NULL
                    LIMIT 10
                """)
                fotos_pendientes = cur.fetchall()
                for foto_id, asset_id, cod_int, ruta_foto in fotos_pendientes:
                    if not ruta_foto or not os.path.exists(ruta_foto):
                        continue
                    rec_id = asset_id or find_inventory_record_id(cur, cod_int)
                    if not rec_id:
                        continue
                    res_foto = api_client.upload_photo(int(rec_id), 1, ruta_foto)
                    if res_foto.get("status_code") in (200, 201):
                        cur.execute("""
                            UPDATE asset_photos
                            SET sincronizado = 1, updated_at = ?
                            WHERE id = ?
                        """, (_now_iso(), foto_id))
                        synced += 1
                    else:
                        break
            except Exception as e_photo:
                print(f"⚠️ Nota al sincronizar fotos pendientes: {e_photo}")

        conn_sqlite.commit()

        cur.execute("SELECT COUNT(*) FROM inventory_sync_outbox WHERE status = 'pending'")
        pending_inv = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM sync_mutations_outbox WHERE status = 'pending'")
        pending_mut = cur.fetchone()[0]
        total_pending = pending_inv + pending_mut

        return {
            "synced": synced,
            "pending": total_pending,
            "pending_inventory": pending_inv,
            "pending_mutations": pending_mut,
        }
    except Exception as error:
        conn_sqlite.rollback()
        return {"synced": synced, "pending": 0, "message": str(error)}
    finally:
        conn_sqlite.close()


def disparar_sincronizacion_background(api_client=None):
    """
    Lanza un hilo ligero en segundo plano para vaciar la cola de sincronización
    después de una escritura local, sin bloquear la interfaz gráfica.
    """
    if not _BG_SYNC_LOCK.acquire(blocking=False):
        return

    def _worker():
        try:
            client = api_client or ApiManagerAcontarSacClient(timeout=15)
            sincronizar_cola_completa(client, limite=25)
        except Exception as e:
            print(f"⚠️ Sincronización en segundo plano diferida (modo offline): {e}")
        finally:
            _BG_SYNC_LOCK.release()

    threading.Thread(target=_worker, daemon=True).start()
