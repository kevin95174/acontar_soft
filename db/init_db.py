# database/init_db.py


def _ensure_column(cursor, table: str, column: str, col_def: str):
    """Agrega una columna a una tabla existente si aún no existe (migración no destructiva)."""
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if existing_columns and column not in existing_columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except Exception as e:
        print(f"⚠️ Nota al migrar columna {table}.{column}: {e}")


def _is_physical_table(cursor, name: str) -> bool:
    """Devuelve True si `name` existe en SQLite como una tabla física (no una vista)."""
    cursor.execute(
        "SELECT type FROM sqlite_master WHERE name = ? AND type = 'table'",
        (name,),
    )
    return cursor.fetchone() is not None


def _migrate_legacy_tables_to_server_tables(cursor):
    """
    Migra cualquier dato existente en las antiguas tablas físicas (`bienes`, `personal`,
    `sobrantes`, `usuarios`) hacia las tablas nativas del servidor (`inventory_records`,
    `locations`, `personnel`, `surplus`, `users`) y elimina las tablas físicas duplicadas.
    """
    # 1. Migrar `personal` (tabla física) -> `locations` + `personnel`
    if _is_physical_table(cursor, "personal"):
        try:
            cursor.execute("""
                INSERT INTO locations (
                    codigo_ubicacion, dep, prov, dist, local, area, oficina,
                    codigo_personal, team_id, created_at, updated_at
                )
                SELECT
                    CAST(p.Acta AS TEXT),
                    COALESCE(p.dep, ''),
                    COALESCE(p.prov, ''),
                    COALESCE(p.dist, ''),
                    COALESCE(p.local, ''),
                    COALESCE(p.area, ''),
                    COALESCE(p.oficina, ''),
                    COALESCE(p.dni, ''),
                    COALESCE(p.EquiInv, ''),
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                FROM personal p
                WHERE p.Acta IS NOT NULL AND TRIM(CAST(p.Acta AS TEXT)) <> ''
                  AND NOT EXISTS (
                      SELECT 1 FROM locations l
                      WHERE CAST(l.codigo_ubicacion AS TEXT) = CAST(p.Acta AS TEXT)
                  );
            """)
            cursor.execute("""
                UPDATE locations
                SET dep = COALESCE(NULLIF((SELECT p.dep FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), dep),
                    prov = COALESCE(NULLIF((SELECT p.prov FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), prov),
                    dist = COALESCE(NULLIF((SELECT p.dist FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), dist),
                    local = COALESCE(NULLIF((SELECT p.local FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), local),
                    area = COALESCE(NULLIF((SELECT p.area FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), area),
                    oficina = COALESCE(NULLIF((SELECT p.oficina FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), oficina),
                    codigo_personal = COALESCE(NULLIF((SELECT p.dni FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), codigo_personal),
                    team_id = COALESCE(NULLIF((SELECT p.EquiInv FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)), ''), team_id)
                WHERE EXISTS (
                    SELECT 1 FROM personal p WHERE CAST(p.Acta AS TEXT) = CAST(locations.codigo_ubicacion AS TEXT)
                );
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO personnel (
                    codigo_personal, nombres, apellidos, apellido_mat, cargo, oficina, estado
                )
                SELECT
                    TRIM(CAST(p.dni AS TEXT)),
                    COALESCE(p.nombre, ''),
                    COALESCE(p.apellidoPat, ''),
                    COALESCE(p.apellidoMat, ''),
                    COALESCE(p.EquiInv, ''),
                    COALESCE(p.oficina, ''),
                    '1'
                FROM personal p
                WHERE p.dni IS NOT NULL AND TRIM(CAST(p.dni AS TEXT)) <> '';
            """)
            cursor.execute("DROP TABLE personal;")
            print("[OK] Tabla física 'personal' migrada a 'locations'/'personnel' y convertida en vista.")
        except Exception as e:
            print(f"⚠️ Error migrando tabla física personal: {e}")

    # 2. Migrar `bienes` (tabla física) -> `inventory_records`
    if _is_physical_table(cursor, "bienes"):
        try:
            # Actualizar registros existentes en inventory_records con los cambios locales de bienes
            cursor.execute("""
                UPDATE inventory_records
                SET codigo_ubicacion_final = CASE
                        WHEN COALESCE((SELECT TRIM(CAST(b.Inv AS TEXT)) FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), '') <> ''
                        THEN (SELECT TRIM(CAST(b.Inv AS TEXT)) FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT))
                        ELSE codigo_ubicacion_final
                    END,
                    inventariado = CASE
                        WHEN COALESCE((SELECT TRIM(CAST(b.Inv AS TEXT)) FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), '') <> ''
                        THEN 1
                        ELSE inventariado
                    END,
                    fecha_inventariado = COALESCE(
                        NULLIF((SELECT b.FechInv FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), ''),
                        fecha_inventariado
                    ),
                    inventariador_local = COALESCE(
                        NULLIF((SELECT b.Inventariador FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), ''),
                        inventariador_local
                    ),
                    equipo_local = COALESCE(
                        NULLIF((SELECT b.Equipo FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), ''),
                        equipo_local
                    ),
                    estado_conservacion = COALESCE(
                        NULLIF((SELECT b.Estado FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), ''),
                        estado_conservacion
                    ),
                    marca = COALESCE((SELECT b.Marca FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), marca),
                    modelo = COALESCE((SELECT b.Modelo FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), modelo),
                    tipo = COALESCE((SELECT b.Tipo FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), tipo),
                    color = COALESCE((SELECT b.Color FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), color),
                    serie = COALESCE((SELECT b.Serie FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), serie),
                    dimension = COALESCE((SELECT b.Dimension FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), dimension),
                    observacion = COALESCE((SELECT b.Obs FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), observacion),
                    otros = COALESCE((SELECT b.Otros FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), otros),
                    situacion = COALESCE((SELECT b.Situacion FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), situacion),
                    nota = COALESCE((SELECT b.Nota FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)), nota)
                WHERE EXISTS (
                    SELECT 1 FROM bienes b WHERE CAST(b.CodInt AS TEXT) = CAST(inventory_records.codigo_interno AS TEXT)
                );
            """)
            # Insertar en inventory_records aquellos bienes que solo existían localmente en `bienes`
            cursor.execute("""
                INSERT INTO inventory_records (
                    asset_id, codigo_interno, codigo_patrimonial, denominacion,
                    cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
                    val_adq, dep_acumulada, valor_neto, estado, situacion,
                    estado_conservacion, marca, modelo, tipo, color, serie,
                    dimension, otros, observacion, placa, nro_motor, nro_chasis,
                    matricula, anio, nota, codigo_ubicacion_inicial,
                    codigo_ubicacion_final, fecha_inventariado, inventariado,
                    inventariador_local, equipo_local
                )
                SELECT
                    b.CodInt,
                    CAST(b.CodInt AS TEXT),
                    COALESCE(b.CodPat, ''),
                    COALESCE(b.DenBien, ''),
                    COALESCE(b.CtaCont, ''),
                    COALESCE(b.DenCta, ''),
                    COALESCE(b.NroDocAdq, ''),
                    b.FechAdq,
                    COALESCE(b.ValAdq, 0),
                    COALESCE(b.DepAcum, 0),
                    COALESCE(b.ValNeto, 0),
                    COALESCE(b.Estado, ''),
                    COALESCE(b.Situacion, ''),
                    COALESCE(b.Estado, ''),
                    COALESCE(b.Marca, ''),
                    COALESCE(b.Modelo, ''),
                    COALESCE(b.Tipo, ''),
                    COALESCE(b.Color, ''),
                    COALESCE(b.Serie, ''),
                    COALESCE(b.Dimension, ''),
                    COALESCE(b.Otros, ''),
                    COALESCE(b.Obs, ''),
                    COALESCE(b.Placa, ''),
                    COALESCE(b.NroMotor, ''),
                    COALESCE(b.NroChasis, ''),
                    COALESCE(b.Matricula, ''),
                    COALESCE(b.AñoFab, ''),
                    COALESCE(b.Nota, ''),
                    COALESCE(b.ActaAnt, ''),
                    CASE WHEN COALESCE(TRIM(CAST(b.Inv AS TEXT)), '') <> '' THEN b.Inv ELSE 0 END,
                    b.FechInv,
                    CASE WHEN COALESCE(TRIM(CAST(b.Inv AS TEXT)), '') <> '' THEN 1 ELSE 0 END,
                    COALESCE(b.Inventariador, ''),
                    COALESCE(b.Equipo, '')
                FROM bienes b
                WHERE NOT EXISTS (
                    SELECT 1 FROM inventory_records ir
                    WHERE CAST(ir.codigo_interno AS TEXT) = CAST(b.CodInt AS TEXT)
                );
            """)
            cursor.execute("DROP TABLE bienes;")
            print("[OK] Tabla física 'bienes' migrada a 'inventory_records' y convertida en vista.")
        except Exception as e:
            print(f"⚠️ Error migrando tabla física bienes: {e}")

    # 3. Migrar `sobrantes` (tabla física) -> `surplus`
    if _is_physical_table(cursor, "sobrantes"):
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO surplus (
                    id, codigo_interno, codigo_patrimonial, codigo_ubicacion,
                    codigo_personal, local_override, area_override, oficina_override,
                    denominacion, marca, modelo, tipo, color, serie, dimension,
                    otros, situacion, estado_conservacion, observacion
                )
                SELECT
                    s.item,
                    '',
                    COALESCE(s.nota, ''),
                    COALESCE(s.acta, ''),
                    COALESCE((SELECT l.codigo_personal FROM locations l WHERE CAST(l.codigo_ubicacion AS TEXT) = CAST(s.acta AS TEXT) LIMIT 1), ''),
                    COALESCE(s.local, ''),
                    COALESCE(s.area, ''),
                    COALESCE(s.oficina, ''),
                    COALESCE(s.den, ''),
                    COALESCE(s.marca, ''),
                    COALESCE(s.modelo, ''),
                    COALESCE(s.tipo, ''),
                    COALESCE(s.color, ''),
                    COALESCE(s.serie, ''),
                    COALESCE(s.dim, ''),
                    COALESCE(s.otros, ''),
                    COALESCE(s.situacion, ''),
                    COALESCE(s.estado, ''),
                    COALESCE(s.obs, '')
                FROM sobrantes s;
            """)
            cursor.execute("DROP TABLE sobrantes;")
            print("[OK] Tabla física 'sobrantes' migrada a 'surplus' y convertida en vista.")
        except Exception as e:
            print(f"⚠️ Error migrando tabla física sobrantes: {e}")

    # 4. Migrar `usuarios` (tabla física) -> `users`
    if _is_physical_table(cursor, "usuarios"):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO users (
                    nombres, apellidos, apellido_mat, dni, usuario, password_hash, rol, estado
                )
                SELECT
                    COALESCE(u.Nombres, ''),
                    COALESCE(u.APat, ''),
                    COALESCE(u.AMat, ''),
                    COALESCE(u.dni, ''),
                    u.usuario,
                    COALESCE(u.password, ''),
                    COALESCE(u.equipo, 'inventariador'),
                    1
                FROM usuarios u
                WHERE u.usuario IS NOT NULL AND TRIM(CAST(u.usuario AS TEXT)) <> '';
            """)
            cursor.execute("DROP TABLE usuarios;")
            print("[OK] Tabla física 'usuarios' migrada a 'users' y convertida en vista.")
        except Exception as e:
            print(f"⚠️ Error migrando tabla física usuarios: {e}")


def _create_compatibility_views_and_triggers(cursor):
    """
    Crea las vistas dinámicas (`bienes`, `personal`, `sobrantes`, `usuarios`) directamente
    sobre las tablas del servidor (`inventory_records`, `locations`, `personnel`, `surplus`, `users`)
    y sus triggers `INSTEAD OF` para que cualquier lectura o escritura opere 100% sobre el esquema del servidor.
    """
    # Recrear vistas limpiamente para asegurar la definición más reciente
    for view_name in ("bienes", "personal", "sobrantes", "usuarios"):
        if not _is_physical_table(cursor, view_name):
            cursor.execute(f"DROP VIEW IF EXISTS {view_name};")

    # 1. VISTA `bienes` (31 columnas exactas) -> lee en vivo de `inventory_records` y `locations`
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS bienes AS
    SELECT
        CAST(COALESCE(NULLIF(ir.codigo_interno, ''), ir.id) AS INTEGER) AS CodInt,
        CAST(COALESCE(ir.codigo_ubicacion_inicial, '') AS TEXT) AS ActaAnt,
        CASE
            WHEN COALESCE(ir.inventariado, 0) = 1
                 AND COALESCE(TRIM(CAST(ir.codigo_ubicacion_final AS TEXT)), '') NOT IN ('', '0')
            THEN CAST(ir.codigo_ubicacion_final AS TEXT)
            ELSE ''
        END AS Inv,
        COALESCE(ir.codigo_patrimonial, '') AS CodPat,
        COALESCE(ir.denominacion, '') AS DenBien,
        COALESCE(ir.nro_doc_adq, '') AS NroDocAdq,
        COALESCE(ir.fech_adq, '') AS FechAdq,
        COALESCE(ir.val_adq, 0.0) AS ValAdq,
        COALESCE(ir.dep_acumulada, 0.0) AS DepAcum,
        COALESCE(ir.valor_neto, 0.0) AS ValNeto,
        COALESCE(ir.cuenta_contable, '') AS CtaCont,
        COALESCE(ir.denominacion_cuenta, '') AS DenCta,
        COALESCE(NULLIF(ir.estado_conservacion, ''), ir.estado, '') AS Estado,
        COALESCE(ir.marca, '') AS Marca,
        COALESCE(ir.modelo, '') AS Modelo,
        COALESCE(ir.tipo, '') AS Tipo,
        COALESCE(ir.color, '') AS Color,
        COALESCE(ir.serie, '') AS Serie,
        COALESCE(ir.dimension, '') AS Dimension,
        COALESCE(ir.placa, '') AS Placa,
        COALESCE(ir.nro_motor, '') AS NroMotor,
        COALESCE(ir.nro_chasis, '') AS NroChasis,
        COALESCE(ir.matricula, '') AS Matricula,
        CAST(COALESCE(ir.anio, '') AS TEXT) AS AñoFab,
        COALESCE(ir.nota, '') AS Nota,
        COALESCE(ir.observacion, '') AS Obs,
        CASE
            WHEN COALESCE(ir.inventariado, 0) = 1
            THEN COALESCE(ir.fecha_inventariado, '')
            ELSE ''
        END AS FechInv,
        COALESCE(ir.otros, '') AS Otros,
        COALESCE(ir.situacion, '') AS Situacion,
        CASE
            WHEN COALESCE(ir.inventariado, 0) = 1
            THEN COALESCE(
                NULLIF(ir.inventariador_local, ''),
                (SELECT TRIM(COALESCE(u.nombres, '') || ' ' || COALESCE(u.apellidos, '')) FROM users u WHERE u.id = ir.user_id),
                CAST(ir.user_id AS TEXT),
                ''
            )
            ELSE ''
        END AS Inventariador,
        COALESCE(NULLIF(ir.equipo_local, ''), loc.team_id, '') AS Equipo
    FROM inventory_records ir
    LEFT JOIN locations loc
        ON CAST(loc.codigo_ubicacion AS TEXT) = CAST(ir.codigo_ubicacion_inicial AS TEXT);
    """)

    # Triggers INSTEAD OF para `bienes` (por si algún importador CSV o script ejecuta SQL directo sobre `bienes`)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_bienes_insert
    INSTEAD OF INSERT ON bienes
    BEGIN
        INSERT OR REPLACE INTO inventory_records (
            id, asset_id, codigo_interno, codigo_patrimonial, denominacion,
            cuenta_contable, denominacion_cuenta, nro_doc_adq, fech_adq,
            val_adq, dep_acumulada, valor_neto, estado, situacion,
            estado_conservacion, marca, modelo, tipo, color, serie,
            dimension, otros, observacion, placa, nro_motor, nro_chasis,
            matricula, anio, nota, codigo_ubicacion_inicial,
            codigo_ubicacion_final, fecha_inventariado, inventariado,
            inventariador_local, equipo_local, updated_at
        ) VALUES (
            (SELECT id FROM inventory_records WHERE CAST(codigo_interno AS TEXT) = CAST(NEW.CodInt AS TEXT) LIMIT 1),
            COALESCE(NEW.CodInt, 0),
            CAST(NEW.CodInt AS TEXT),
            COALESCE(NEW.CodPat, ''),
            COALESCE(NEW.DenBien, ''),
            COALESCE(NEW.CtaCont, ''),
            COALESCE(NEW.DenCta, ''),
            COALESCE(NEW.NroDocAdq, ''),
            NEW.FechAdq,
            COALESCE(NEW.ValAdq, 0),
            COALESCE(NEW.DepAcum, 0),
            COALESCE(NEW.ValNeto, 0),
            COALESCE(NEW.Estado, ''),
            COALESCE(NEW.Situacion, ''),
            COALESCE(NEW.Estado, ''),
            COALESCE(NEW.Marca, ''),
            COALESCE(NEW.Modelo, ''),
            COALESCE(NEW.Tipo, ''),
            COALESCE(NEW.Color, ''),
            COALESCE(NEW.Serie, ''),
            COALESCE(NEW.Dimension, ''),
            COALESCE(NEW.Otros, ''),
            COALESCE(NEW.Obs, ''),
            COALESCE(NEW.Placa, ''),
            COALESCE(NEW.NroMotor, ''),
            COALESCE(NEW.NroChasis, ''),
            COALESCE(NEW.Matricula, ''),
            COALESCE(NEW.AñoFab, ''),
            COALESCE(NEW.Nota, ''),
            COALESCE(NEW.ActaAnt, ''),
            CASE WHEN COALESCE(TRIM(CAST(NEW.Inv AS TEXT)), '') NOT IN ('', '0') THEN NEW.Inv ELSE 0 END,
            NEW.FechInv,
            CASE WHEN COALESCE(TRIM(CAST(NEW.Inv AS TEXT)), '') NOT IN ('', '0') THEN 1 ELSE 0 END,
            COALESCE(NEW.Inventariador, ''),
            COALESCE(NEW.Equipo, ''),
            CURRENT_TIMESTAMP
        );
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_bienes_update
    INSTEAD OF UPDATE ON bienes
    BEGIN
        UPDATE inventory_records
        SET codigo_ubicacion_inicial = COALESCE(NEW.ActaAnt, codigo_ubicacion_inicial),
            codigo_ubicacion_final = CASE
                WHEN COALESCE(TRIM(CAST(NEW.Inv AS TEXT)), '') NOT IN ('', '0') THEN NEW.Inv
                ELSE 0
            END,
            inventariado = CASE
                WHEN COALESCE(TRIM(CAST(NEW.Inv AS TEXT)), '') NOT IN ('', '0') THEN 1
                ELSE 0
            END,
            codigo_patrimonial = COALESCE(NEW.CodPat, codigo_patrimonial),
            denominacion = COALESCE(NEW.DenBien, denominacion),
            nro_doc_adq = COALESCE(NEW.NroDocAdq, nro_doc_adq),
            fech_adq = COALESCE(NEW.FechAdq, fech_adq),
            val_adq = COALESCE(NEW.ValAdq, val_adq),
            dep_acumulada = COALESCE(NEW.DepAcum, dep_acumulada),
            valor_neto = COALESCE(NEW.ValNeto, valor_neto),
            cuenta_contable = COALESCE(NEW.CtaCont, cuenta_contable),
            denominacion_cuenta = COALESCE(NEW.DenCta, denominacion_cuenta),
            estado_conservacion = COALESCE(NEW.Estado, estado_conservacion),
            estado = COALESCE(NEW.Estado, estado),
            marca = COALESCE(NEW.Marca, marca),
            modelo = COALESCE(NEW.Modelo, modelo),
            tipo = COALESCE(NEW.Tipo, tipo),
            color = COALESCE(NEW.Color, color),
            serie = COALESCE(NEW.Serie, serie),
            dimension = COALESCE(NEW.Dimension, dimension),
            placa = COALESCE(NEW.Placa, placa),
            nro_motor = COALESCE(NEW.NroMotor, nro_motor),
            nro_chasis = COALESCE(NEW.NroChasis, nro_chasis),
            matricula = COALESCE(NEW.Matricula, matricula),
            anio = COALESCE(NEW.AñoFab, anio),
            nota = COALESCE(NEW.Nota, nota),
            observacion = COALESCE(NEW.Obs, observacion),
            fecha_inventariado = CASE
                WHEN COALESCE(TRIM(CAST(NEW.Inv AS TEXT)), '') NOT IN ('', '0') THEN COALESCE(NEW.FechInv, fecha_inventariado)
                ELSE NULL
            END,
            otros = COALESCE(NEW.Otros, otros),
            situacion = COALESCE(NEW.Situacion, situacion),
            inventariador_local = COALESCE(NEW.Inventariador, inventariador_local),
            equipo_local = COALESCE(NEW.Equipo, equipo_local),
            updated_at = CURRENT_TIMESTAMP
        WHERE CAST(codigo_interno AS TEXT) = CAST(OLD.CodInt AS TEXT)
           OR (codigo_patrimonial = OLD.CodPat AND COALESCE(OLD.CodPat, '') <> '');
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_bienes_delete
    INSTEAD OF DELETE ON bienes
    BEGIN
        DELETE FROM inventory_records
        WHERE CAST(codigo_interno AS TEXT) = CAST(OLD.CodInt AS TEXT);
    END;
    """)

    # 2. VISTA `personal` (12 columnas exactas) -> lee en vivo de `locations` y `personnel`
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS personal AS
    SELECT
        COALESCE(NULLIF(CAST(l.codigo_ubicacion AS TEXT), ''), CAST(l.id AS TEXT)) AS Acta,
        COALESCE(l.dep, '') AS dep,
        COALESCE(l.prov, '') AS prov,
        COALESCE(l.dist, '') AS dist,
        COALESCE(l.local, '') AS local,
        COALESCE(l.area, '') AS area,
        COALESCE(l.oficina, p.oficina, '') AS oficina,
        COALESCE(p.codigo_personal, l.codigo_personal, '') AS dni,
        COALESCE(p.nombres, '') AS nombre,
        COALESCE(p.apellidos, '') AS apellidoPat,
        COALESCE(p.apellido_mat, '') AS apellidoMat,
        COALESCE(NULLIF(l.team_id, ''), p.cargo, '') AS EquiInv
    FROM locations l
    LEFT JOIN personnel p ON l.codigo_personal = p.codigo_personal;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_personal_insert
    INSTEAD OF INSERT ON personal
    BEGIN
        INSERT OR REPLACE INTO locations (
            id, codigo_ubicacion, dep, prov, dist, local, area, oficina,
            codigo_personal, team_id, updated_at
        ) VALUES (
            (SELECT id FROM locations WHERE CAST(codigo_ubicacion AS TEXT) = CAST(NEW.Acta AS TEXT) LIMIT 1),
            CAST(NEW.Acta AS TEXT),
            COALESCE(NEW.dep, ''),
            COALESCE(NEW.prov, ''),
            COALESCE(NEW.dist, ''),
            COALESCE(NEW.local, ''),
            COALESCE(NEW.area, ''),
            COALESCE(NEW.oficina, ''),
            COALESCE(NEW.dni, ''),
            COALESCE(NEW.EquiInv, ''),
            CURRENT_TIMESTAMP
        );
        INSERT INTO personnel (
            codigo_personal, nombres, apellidos, apellido_mat, cargo, oficina, estado, updated_at
        )
        SELECT
            TRIM(CAST(NEW.dni AS TEXT)),
            COALESCE(NEW.nombre, ''),
            COALESCE(NEW.apellidoPat, ''),
            COALESCE(NEW.apellidoMat, ''),
            COALESCE(NEW.EquiInv, ''),
            COALESCE(NEW.oficina, ''),
            '1',
            CURRENT_TIMESTAMP
        WHERE NEW.dni IS NOT NULL AND TRIM(CAST(NEW.dni AS TEXT)) <> ''
        ON CONFLICT(codigo_personal) DO UPDATE SET
            nombres = excluded.nombres,
            apellidos = excluded.apellidos,
            apellido_mat = excluded.apellido_mat,
            cargo = COALESCE(NULLIF(excluded.cargo, ''), personnel.cargo),
            oficina = excluded.oficina,
            updated_at = CURRENT_TIMESTAMP;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_personal_update
    INSTEAD OF UPDATE ON personal
    BEGIN
        UPDATE locations
        SET dep = COALESCE(NEW.dep, dep),
            prov = COALESCE(NEW.prov, prov),
            dist = COALESCE(NEW.dist, dist),
            local = COALESCE(NEW.local, local),
            area = COALESCE(NEW.area, area),
            oficina = COALESCE(NEW.oficina, oficina),
            codigo_personal = COALESCE(NEW.dni, codigo_personal),
            team_id = COALESCE(NEW.EquiInv, team_id),
            updated_at = CURRENT_TIMESTAMP
        WHERE CAST(codigo_ubicacion AS TEXT) = CAST(OLD.Acta AS TEXT);

        INSERT INTO personnel (
            codigo_personal, nombres, apellidos, apellido_mat, cargo, oficina, estado, updated_at
        )
        SELECT
            TRIM(CAST(NEW.dni AS TEXT)),
            COALESCE(NEW.nombre, ''),
            COALESCE(NEW.apellidoPat, ''),
            COALESCE(NEW.apellidoMat, ''),
            COALESCE(NEW.EquiInv, ''),
            COALESCE(NEW.oficina, ''),
            '1',
            CURRENT_TIMESTAMP
        WHERE NEW.dni IS NOT NULL AND TRIM(CAST(NEW.dni AS TEXT)) <> ''
        ON CONFLICT(codigo_personal) DO UPDATE SET
            nombres = excluded.nombres,
            apellidos = excluded.apellidos,
            apellido_mat = excluded.apellido_mat,
            cargo = COALESCE(NULLIF(excluded.cargo, ''), personnel.cargo),
            oficina = excluded.oficina,
            updated_at = CURRENT_TIMESTAMP;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_personal_delete
    INSTEAD OF DELETE ON personal
    BEGIN
        DELETE FROM locations WHERE CAST(codigo_ubicacion AS TEXT) = CAST(OLD.Acta AS TEXT);
    END;
    """)

    # 3. VISTA `sobrantes` (17 columnas exactas) -> lee en vivo de `surplus` y `locations`
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS sobrantes AS
    SELECT
        s.id AS item,
        COALESCE(l.codigo_ubicacion, CAST(s.codigo_ubicacion AS TEXT), '') AS acta,
        COALESCE(NULLIF(s.local_override, ''), l.local, '') AS local,
        COALESCE(NULLIF(s.area_override, ''), l.area, '') AS area,
        COALESCE(NULLIF(s.oficina_override, ''), l.oficina, '') AS oficina,
        COALESCE(s.denominacion, '') AS den,
        COALESCE(s.estado_conservacion, '') AS estado,
        COALESCE(s.dimension, '') AS dim,
        COALESCE(s.marca, '') AS marca,
        COALESCE(s.modelo, '') AS modelo,
        COALESCE(s.serie, '') AS serie,
        COALESCE(s.color, '') AS color,
        COALESCE(s.observacion, '') AS obs,
        COALESCE(s.tipo, '') AS tipo,
        COALESCE(s.otros, '') AS otros,
        COALESCE(s.situacion, '') AS situacion,
        COALESCE(s.codigo_patrimonial, '') AS nota
    FROM surplus s
    LEFT JOIN locations l ON CAST(l.codigo_ubicacion AS TEXT) = CAST(s.codigo_ubicacion AS TEXT);
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_sobrantes_insert
    INSTEAD OF INSERT ON sobrantes
    BEGIN
        INSERT INTO surplus (
            codigo_interno, codigo_patrimonial, codigo_ubicacion, codigo_personal,
            local_override, area_override, oficina_override, denominacion,
            marca, modelo, tipo, color, serie, dimension, otros, situacion,
            estado_conservacion, observacion, created_at, updated_at
        ) VALUES (
            '',
            COALESCE(NEW.nota, ''),
            COALESCE(NEW.acta, ''),
            COALESCE((SELECT codigo_personal FROM locations WHERE CAST(codigo_ubicacion AS TEXT) = CAST(NEW.acta AS TEXT) LIMIT 1), ''),
            COALESCE(NEW.local, ''),
            COALESCE(NEW.area, ''),
            COALESCE(NEW.oficina, ''),
            COALESCE(NEW.den, ''),
            COALESCE(NEW.marca, ''),
            COALESCE(NEW.modelo, ''),
            COALESCE(NEW.tipo, ''),
            COALESCE(NEW.color, ''),
            COALESCE(NEW.serie, ''),
            COALESCE(NEW.dim, ''),
            COALESCE(NEW.otros, ''),
            COALESCE(NEW.situacion, ''),
            COALESCE(NEW.estado, ''),
            COALESCE(NEW.obs, ''),
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_sobrantes_update
    INSTEAD OF UPDATE ON sobrantes
    BEGIN
        UPDATE surplus
        SET codigo_ubicacion = COALESCE(NEW.acta, codigo_ubicacion),
            local_override = COALESCE(NEW.local, local_override),
            area_override = COALESCE(NEW.area, area_override),
            oficina_override = COALESCE(NEW.oficina, oficina_override),
            denominacion = COALESCE(NEW.den, denominacion),
            estado_conservacion = COALESCE(NEW.estado, estado_conservacion),
            dimension = COALESCE(NEW.dim, dimension),
            marca = COALESCE(NEW.marca, marca),
            modelo = COALESCE(NEW.modelo, modelo),
            serie = COALESCE(NEW.serie, serie),
            color = COALESCE(NEW.color, color),
            observacion = COALESCE(NEW.obs, observacion),
            tipo = COALESCE(NEW.tipo, tipo),
            otros = COALESCE(NEW.otros, otros),
            situacion = COALESCE(NEW.situacion, situacion),
            codigo_patrimonial = COALESCE(NEW.nota, codigo_patrimonial),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.item;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_sobrantes_delete
    INSTEAD OF DELETE ON sobrantes
    BEGIN
        DELETE FROM surplus WHERE id = OLD.item;
    END;
    """)

    # 4. VISTA `usuarios` (8 columnas exactas) -> lee en vivo de `users`
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS usuarios AS
    SELECT
        u.id AS id,
        COALESCE(u.usuario, '') AS usuario,
        COALESCE(u.password_hash, '') AS password,
        COALESCE(u.nombres, '') AS Nombres,
        COALESCE(u.apellidos, '') AS APat,
        COALESCE(u.apellido_mat, '') AS AMat,
        COALESCE(NULLIF(u.dni, ''), CAST(u.id AS TEXT)) AS dni,
        COALESCE(u.rol, '') AS equipo
    FROM users u;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_usuarios_insert
    INSTEAD OF INSERT ON usuarios
    BEGIN
        INSERT INTO users (
            nombres, apellidos, apellido_mat, dni, usuario, password_hash, rol, estado, created_at, updated_at
        ) VALUES (
            COALESCE(NEW.Nombres, ''),
            COALESCE(NEW.APat, ''),
            COALESCE(NEW.AMat, ''),
            COALESCE(NEW.dni, ''),
            NEW.usuario,
            COALESCE(NEW.password, ''),
            COALESCE(NEW.equipo, 'OPERADOR'),
            1,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT(usuario) DO UPDATE SET
            nombres = excluded.nombres,
            apellidos = excluded.apellidos,
            apellido_mat = excluded.apellido_mat,
            dni = excluded.dni,
            password_hash = excluded.password_hash,
            rol = excluded.rol,
            updated_at = CURRENT_TIMESTAMP;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_usuarios_update
    INSTEAD OF UPDATE ON usuarios
    BEGIN
        UPDATE users
        SET usuario = COALESCE(NEW.usuario, usuario),
            password_hash = COALESCE(NEW.password, password_hash),
            nombres = COALESCE(NEW.Nombres, nombres),
            apellidos = COALESCE(NEW.APat, apellidos),
            apellido_mat = COALESCE(NEW.AMat, apellido_mat),
            dni = COALESCE(NEW.dni, dni),
            rol = COALESCE(NEW.equipo, rol),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.id;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_usuarios_delete
    INSTEAD OF DELETE ON usuarios
    BEGIN
        DELETE FROM users WHERE id = OLD.id;
    END;
    """)


def init_db(connection):
    cursor = connection.cursor()

    # -------------------------------------------------------------
    # 1. TABLAS NATIVAS DEL SERVIDOR (Única Fuente de Verdad en SQLite)
    # -------------------------------------------------------------

    # 1.1 Locations (Ubicaciones / Fichas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_ubicacion TEXT DEFAULT NULL,
        dep TEXT DEFAULT '',
        prov TEXT DEFAULT '',
        dist TEXT DEFAULT '',
        local TEXT DEFAULT NULL,
        area TEXT DEFAULT NULL,
        oficina TEXT DEFAULT NULL,
        piso TEXT DEFAULT NULL,
        direccion TEXT DEFAULT NULL,
        codigo_personal TEXT DEFAULT NULL,
        team_id TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT NULL,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    # 1.2 Personnel (Personal / Responsables)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personnel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_personal TEXT NOT NULL UNIQUE,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        apellido_mat TEXT DEFAULT '',
        cargo TEXT DEFAULT NULL,
        oficina TEXT DEFAULT NULL,
        telefono TEXT DEFAULT NULL,
        email TEXT DEFAULT NULL,
        estado TEXT DEFAULT '1',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    # 1.3 Assets (Padrón / Maestro de Activos del Servidor)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY,
        codigo_interno TEXT DEFAULT '',
        codigo_patrimonial TEXT DEFAULT '',
        denominacion TEXT DEFAULT '',
        cuenta_contable TEXT DEFAULT '',
        denominacion_cuenta TEXT DEFAULT '',
        nro_doc_adq TEXT DEFAULT '',
        fech_adq DATE DEFAULT NULL,
        val_adq REAL DEFAULT 0,
        dep_acumulada REAL DEFAULT 0,
        valor_neto REAL DEFAULT 0,
        estado TEXT DEFAULT '',
        situacion TEXT DEFAULT '',
        estado_conservacion TEXT DEFAULT '',
        marca TEXT DEFAULT '',
        modelo TEXT DEFAULT '',
        tipo TEXT DEFAULT '',
        color TEXT DEFAULT '',
        serie TEXT DEFAULT '',
        dimension TEXT DEFAULT '',
        otros TEXT DEFAULT '',
        observacion TEXT DEFAULT '',
        placa TEXT DEFAULT '',
        nro_motor TEXT DEFAULT '',
        nro_chasis TEXT DEFAULT '',
        matricula TEXT DEFAULT '',
        anio TEXT DEFAULT '',
        nota TEXT DEFAULT '',
        codigo_personal TEXT DEFAULT '',
        codigo_ubicacion_inicial INTEGER DEFAULT 0,
        codigo_ubicacion_final INTEGER DEFAULT 0,
        user_id INTEGER DEFAULT 0,
        foto_url TEXT DEFAULT '',
        fecha_inventariado DATETIME DEFAULT NULL,
        inventariado INTEGER DEFAULT 0,
        fecha_servidor DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT NULL,
        deleted_at DATETIME DEFAULT NULL,
        Column8 TEXT DEFAULT NULL,
        Column9 TEXT DEFAULT NULL
    );
    """)

    # 1.4 Inventory Records (Levantamiento de Inventario en Terreno)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER DEFAULT 0,
        codigo_interno TEXT DEFAULT '',
        codigo_patrimonial TEXT DEFAULT '',
        denominacion TEXT DEFAULT '',
        cuenta_contable TEXT DEFAULT '',
        denominacion_cuenta TEXT DEFAULT '',
        nro_doc_adq TEXT DEFAULT '',
        fech_adq TEXT DEFAULT NULL,
        val_adq REAL DEFAULT 0,
        dep_acumulada REAL DEFAULT 0,
        valor_neto REAL DEFAULT 0,
        estado TEXT DEFAULT '',
        situacion TEXT DEFAULT '',
        estado_conservacion TEXT DEFAULT '',
        marca TEXT DEFAULT '',
        modelo TEXT DEFAULT '',
        tipo TEXT DEFAULT '',
        color TEXT DEFAULT '',
        serie TEXT DEFAULT '',
        dimension TEXT DEFAULT '',
        otros TEXT DEFAULT '',
        observacion TEXT DEFAULT '',
        placa TEXT DEFAULT '',
        nro_motor TEXT DEFAULT '',
        nro_chasis TEXT DEFAULT '',
        matricula TEXT DEFAULT '',
        anio TEXT DEFAULT '',
        nota TEXT DEFAULT '',
        codigo_personal TEXT DEFAULT '',
        codigo_ubicacion_inicial INTEGER DEFAULT 0,
        codigo_ubicacion_final INTEGER DEFAULT 0,
        user_id INTEGER DEFAULT 0,
        inventariador_local TEXT DEFAULT '',
        equipo_local TEXT DEFAULT '',
        foto_url TEXT DEFAULT '',
        fecha_inventariado DATETIME DEFAULT NULL,
        inventariado INTEGER DEFAULT 0,
        fecha_servidor DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT NULL,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    # 1.5 Surplus (Bienes Sobrantes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surplus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_interno TEXT DEFAULT '',
        codigo_patrimonial TEXT DEFAULT '',
        codigo_ubicacion INTEGER DEFAULT 0,
        codigo_personal INTEGER DEFAULT 0,
        local_override TEXT DEFAULT '',
        area_override TEXT DEFAULT '',
        oficina_override TEXT DEFAULT '',
        denominacion TEXT NOT NULL,
        marca TEXT DEFAULT '',
        modelo TEXT DEFAULT '',
        tipo TEXT DEFAULT '',
        color TEXT DEFAULT '',
        serie TEXT DEFAULT '',
        dimension TEXT DEFAULT '',
        otros TEXT DEFAULT '',
        situacion TEXT DEFAULT '',
        estado_conservacion TEXT DEFAULT '',
        observacion TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    # 1.6 Asset Photos (Fotografías de los Bienes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asset_photos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER DEFAULT NULL,
        codigo_interno TEXT DEFAULT NULL,
        ruta_foto TEXT DEFAULT NULL,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        sincronizado INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    # 1.7 Teams (Brigadas / Equipos de Captura)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        capturador_id INTEGER NOT NULL,
        auxiliar_id INTEGER DEFAULT NULL,
        estado TEXT DEFAULT 'ACTIVO',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 1.8 Users (Usuarios del Sistema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT DEFAULT '',
        apellidos TEXT DEFAULT '',
        apellido_mat TEXT DEFAULT '',
        dni TEXT DEFAULT '',
        correo TEXT DEFAULT NULL,
        usuario TEXT NOT NULL UNIQUE,
        password_hash TEXT DEFAULT '',
        rol TEXT DEFAULT 'inventariador',
        estado INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        token TEXT DEFAULT NULL
    );
    """)

    # 1.9 Inventory Assignments (Asignaciones de Brigadas a Ubicaciones)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER NOT NULL,
        location_id INTEGER NOT NULL,
        fecha_programada DATE NOT NULL,
        estado TEXT DEFAULT 'PENDIENTE',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # -------------------------------------------------------------
    # 2. TABLAS DE INFRAESTRUCTURA Y COLA OFFLINE
    # -------------------------------------------------------------
    cursor.execute("""
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

    cursor.execute("""
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_config (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # -------------------------------------------------------------
    # 3. TABLAS AUXILIARES LOCALES (Vehículos, Catálogo, Configuración, Bajas)
    # -------------------------------------------------------------
    cursor.execute(""" CREATE TABLE IF NOT EXISTS baja (CodInt INTEGER PRIMARY KEY, Resolucion TEXT, Inv TEXT, CodPat TEXT, DenBien TEXT, NroDocAdq TEXT, FechAdq TEXT, ValAdq REAL, CtaCont TEXT, DenCta TEXT, Estado TEXT, Marca TEXT, Modelo TEXT, Tipo TEXT, Color TEXT, Serie TEXT, Dimension TEXT, Placa TEXT, NroMotor TEXT, NroChasis TEXT, Matricula TEXT, AñoFab TEXT, Nota TEXT, Obs TEXT, FechInv TEXT, Otros TEXT, Situacion TEXT, Inventariador TEXT, Equipo TEXT)""")
    cursor.execute(""" CREATE TABLE IF NOT EXISTS bienesAfec (item INTEGER PRIMARY KEY, CodPat TEXT, denBienA TEXT, acta TEXT, local TEXT, area TEXT, oficina TEXT, estado TEXT, marca TEXT, modelo TEXT, tipo TEXT, serie TEXT, dimensiones TEXT, obs TEXT, afectante TEXT) """)
    cursor.execute(""" CREATE TABLE IF NOT EXISTS cambios_det (item INTEGER PRIMARY KEY AUTOINCREMENT, CodInt INTEGER, ActaAnt TEXT, Inv TEXT, CodPat TEXT, DenBien TEXT, NroDocAdq TEXT, FechAdq TEXT, ValAdq REAL, DepAcum REAL, ValNeto REAL, CtaCont TEXT, DenCta TEXT, Estado TEXT, Marca TEXT, Modelo TEXT, Tipo TEXT, Color TEXT, Serie TEXT, Dimension TEXT, Placa TEXT, NroMotor TEXT, NroChasis TEXT, Matricula TEXT, AñoFab TEXT, Nota TEXT, Obs TEXT, FechInv TEXT, Otros TEXT, Situacion TEXT, Inventariador TEXT, Equipo TEXT) """)
    cursor.execute(""" CREATE TABLE IF NOT EXISTS catalogo (item TEXT, codigo TEXT, denominacion TEXT, unidad TEXT, grupo TEXT, clase TEXT, resolucion TEXT, estado TEXT)""")
    cursor.execute(""" CREATE TABLE IF NOT EXISTS datos (id TEXT PRIMARY KEY, entidad TEXT, periodo TEXT, fecha TEXT)""")
    cursor.execute(""" CREATE TABLE IF NOT EXISTS vehiculos (CodInt INTEGER PRIMARY KEY, Entidad TEXT, CodPat TEXT, DenBien TEXT, NroPlaca TEXT, Carroceria TEXT, Marca TEXT, Modelo TEXT, Categoria TEXT, NroChasis TEXT, NroEjes TEXT, NroMotor TEXT, NroSerie TEXT, AFab TEXT, Color TEXT, Combustible TEXT, Transm TEXT, Cilindrada TEXT, Kilometraje TEXT, NroTarjVehi TEXT, SistMotor TEXT, SistFrenos TEXT, SistRefri TEXT, SistElect TEXT, SistTrans TEXT, SistDirec TEXT, SistSusp TEXT, Crreria TEXT, Accesorios TEXT, OtrCarac TEXT, Apreciacion TEXT)""")

    # -------------------------------------------------------------
    # 4. MIGRACIONES NO DESTRUCTIVAS DE COLUMNAS
    # -------------------------------------------------------------
    _ensure_column(cursor, "locations", "team_id", "TEXT DEFAULT ''")
    _ensure_column(cursor, "locations", "dep", "TEXT DEFAULT ''")
    _ensure_column(cursor, "locations", "prov", "TEXT DEFAULT ''")
    _ensure_column(cursor, "locations", "dist", "TEXT DEFAULT ''")
    _ensure_column(cursor, "personnel", "apellido_mat", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "codigo_interno", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "codigo_patrimonial", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "local_override", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "area_override", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "oficina_override", "TEXT DEFAULT ''")
    _ensure_column(cursor, "inventory_records", "nota", "TEXT DEFAULT ''")
    _ensure_column(cursor, "inventory_records", "inventariador_local", "TEXT DEFAULT ''")
    _ensure_column(cursor, "inventory_records", "equipo_local", "TEXT DEFAULT ''")
    _ensure_column(cursor, "users", "apellido_mat", "TEXT DEFAULT ''")
    _ensure_column(cursor, "users", "dni", "TEXT DEFAULT ''")
    _ensure_column(cursor, "assets", "cuenta_contable", "TEXT DEFAULT ''")
    _ensure_column(cursor, "assets", "denominacion_cuenta", "TEXT DEFAULT ''")
    _ensure_column(cursor, "assets", "dep_acumulada", "REAL DEFAULT 0")
    _ensure_column(cursor, "assets", "valor_neto", "REAL DEFAULT 0")
    _ensure_column(cursor, "assets", "codigo_ubicacion_inicial", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "assets", "codigo_ubicacion_final", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "assets", "user_id", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "assets", "foto_url", "TEXT DEFAULT ''")
    _ensure_column(cursor, "assets", "fecha_inventariado", "DATETIME DEFAULT NULL")
    _ensure_column(cursor, "assets", "inventariado", "INTEGER DEFAULT 0")
    _ensure_column(cursor, "assets", "fecha_servidor", "DATETIME DEFAULT CURRENT_TIMESTAMP")
    _ensure_column(cursor, "assets", "Column8", "TEXT DEFAULT NULL")
    _ensure_column(cursor, "assets", "Column9", "TEXT DEFAULT NULL")

    # Índices para acelerar sincronización y vistas
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_codint ON inventory_records(codigo_interno);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_codpat ON inventory_records(codigo_patrimonial);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_ubini ON inventory_records(codigo_ubicacion_inicial);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_ubfin ON inventory_records(codigo_ubicacion_final);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_ctacont ON inventory_records(cuenta_contable);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_inv_rec_den ON inventory_records(denominacion);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_locations_codubi ON locations(codigo_ubicacion);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personnel_codper ON personnel(codigo_personal);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_surplus_codubi ON surplus(codigo_ubicacion);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_outbox_mut_status ON sync_mutations_outbox(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_photos_codint ON asset_photos(codigo_interno);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_asset_photos_assetid ON asset_photos(asset_id);")

    # -------------------------------------------------------------
    # 5. MIGRAR TABLAS FÍSICAS ANTIGUAS Y CREAR VISTAS + TRIGGERS 1:1
    # -------------------------------------------------------------
    _migrate_legacy_tables_to_server_tables(cursor)
    _create_compatibility_views_and_triggers(cursor)

    # -------------------------------------------------------------
    # 6. USUARIO POR DEFECTO PARA ACCESO SIN CONEXIÓN (user / user)
    # -------------------------------------------------------------
    cursor.execute("SELECT id FROM users WHERE usuario = 'user'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (usuario, password_hash, nombres, apellidos, apellido_mat, dni, rol, estado)
            VALUES ('user', 'user', 'Usuario', 'Local', '', '00000000', 'OPERADOR', 1)
        """)

    connection.commit()
