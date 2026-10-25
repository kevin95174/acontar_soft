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


def init_db(connection):
    cursor = connection.cursor()

    # -------------------------------------------------------------
    # 1. TABLAS RÉPLICA DE SINCRONIZACIÓN (Servidor MySQL <-> SQLite)
    # -------------------------------------------------------------

    # 1.1 Locations (Ubicaciones)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_ubicacion TEXT DEFAULT NULL,
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

    # 1.2 Personnel (Personal)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personnel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_personal TEXT NOT NULL UNIQUE,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
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
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("DROP TABLE IF EXISTS users")
    except Exception:
        pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT DEFAULT '',
        apellidos TEXT DEFAULT '',
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

    # Cola persistente para cambios de inventario hechos cuando no hay red
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

    # Tabla para metadatos de sincronización
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_config (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # -------------------------------------------------------------
    # 3. TABLAS OPERATIVAS Y DE REPORTES LOCALES (GUI / Legacy)
    # -------------------------------------------------------------
    cursor.execute(""" CREATE TABLE IF NOT EXISTS baja (CodInt INTEGER PRIMARY KEY, Resolucion TEXT, Inv TEXT, CodPat TEXT, DenBien TEXT, NroDocAdq TEXT, FechAdq TEXT, ValAdq REAL, CtaCont TEXT, DenCta TEXT, Estado TEXT, Marca TEXT, Modelo TEXT, Tipo TEXT, Color TEXT, Serie TEXT, Dimension TEXT, Placa TEXT, NroMotor TEXT, NroChasis TEXT, Matricula TEXT, AñoFab TEXT, Nota TEXT, Obs TEXT, FechInv TEXT, Otros TEXT, Situacion TEXT, Inventariador TEXT, Equipo TEXT)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS bienes (CodInt INTEGER PRIMARY KEY, ActaAnt TEXT, Inv TEXT, CodPat TEXT, DenBien TEXT, NroDocAdq TEXT, FechAdq TEXT, ValAdq REAL, DepAcum REAL, ValNeto REAL, CtaCont TEXT, DenCta TEXT, Estado TEXT, Marca TEXT, Modelo TEXT, Tipo TEXT, Color TEXT, Serie TEXT, Dimension TEXT, Placa TEXT, NroMotor TEXT, NroChasis TEXT, Matricula TEXT, AñoFab TEXT, Nota TEXT, Obs TEXT, FechInv TEXT, Otros TEXT, Situacion TEXT, Inventariador TEXT, Equipo TEXT) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS bienesAfec (item INTEGER PRIMARY KEY, CodPat TEXT, denBienA TEXT, acta TEXT, local TEXT, area TEXT, oficina TEXT, estado TEXT, marca TEXT, modelo TEXT, tipo TEXT, serie TEXT, dimensiones TEXT, obs TEXT, afectante TEXT) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS cambios_det (item INTEGER PRIMARY KEY AUTOINCREMENT, CodInt INTEGER, ActaAnt TEXT, Inv TEXT, CodPat TEXT, DenBien TEXT, NroDocAdq TEXT, FechAdq TEXT, ValAdq REAL, DepAcum REAL, ValNeto REAL, CtaCont TEXT, DenCta TEXT, Estado TEXT, Marca TEXT, Modelo TEXT, Tipo TEXT, Color TEXT, Serie TEXT, Dimension TEXT, Placa TEXT, NroMotor TEXT, NroChasis TEXT, Matricula TEXT, AñoFab TEXT, Nota TEXT, Obs TEXT, FechInv TEXT, Otros TEXT, Situacion TEXT, Inventariador TEXT, Equipo TEXT) """)

    cursor.execute(""" CREATE TABLE IF NOT EXISTS catalogo (item TEXT, codigo TEXT, denominacion TEXT, unidad TEXT, grupo TEXT, clase TEXT, resolucion TEXT, estado TEXT)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS datos (id TEXT PRIMARY KEY, entidad TEXT, periodo TEXT, fecha TEXT)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS personal (Acta STRING PRIMARY KEY, dep TEXT, prov TEXT, dist TEXT, local TEXT, area TEXT, oficina TEXT, dni TEXT, nombre TEXT, apellidoPat TEXT, apellidoMat TEXT, EquiInv TEXT)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS sobrantes (item INTEGER PRIMARY KEY, acta VARCHAR, local VARCHAR, area VARCHAR, oficina VARCHAR, den VARCHAR, estado VARCHAR, dim VARCHAR, marca VARCHAR, modelo VARCHAR, serie VARCHAR, color VARCHAR, obs VARCHAR, tipo VARCHAR, otros VARCHAR, situacion VARCHAR, nota TEXT)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario STRING, password STRING, Nombres VARCHAR, APat VARCHAR, AMat VARCHAR, dni VARCHAR, equipo VARCHAR)""")

    cursor.execute(""" CREATE TABLE IF NOT EXISTS vehiculos (CodInt INTEGER PRIMARY KEY, Entidad TEXT, CodPat TEXT, DenBien TEXT, NroPlaca TEXT, Carroceria TEXT, Marca TEXT, Modelo TEXT, Categoria TEXT, NroChasis TEXT, NroEjes TEXT, NroMotor TEXT, NroSerie TEXT, AFab TEXT, Color TEXT, Combustible TEXT, Transm TEXT, Cilindrada TEXT, Kilometraje TEXT, NroTarjVehi TEXT, SistMotor TEXT, SistFrenos TEXT, SistRefri TEXT, SistElect TEXT, SistTrans TEXT, SistDirec TEXT, SistSusp TEXT, Crreria TEXT, Accesorios TEXT, OtrCarac TEXT, Apreciacion TEXT)""")

    # -------------------------------------------------------------
    # 4. MIGRACIONES NO DESTRUCTIVAS (Asegura columnas en BD previas)
    # -------------------------------------------------------------
    _ensure_column(cursor, "locations", "team_id", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "codigo_interno", "TEXT DEFAULT ''")
    _ensure_column(cursor, "surplus", "codigo_patrimonial", "TEXT DEFAULT ''")
    _ensure_column(cursor, "inventory_records", "nota", "TEXT DEFAULT ''")
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

    # -------------------------------------------------------------
    # 5. USUARIO POR DEFECTO PARA ACCESO SIN CONEXIÓN (user / user)
    # -------------------------------------------------------------
    cursor.execute("SELECT id FROM usuarios WHERE usuario = 'user'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO usuarios (usuario, password, Nombres, APat, AMat, dni, equipo)
            VALUES ('user', 'user', 'Usuario', 'Local', '', '00000000', 'OPERADOR')
        """)

    cursor.execute("SELECT id FROM users WHERE usuario = 'user'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (usuario, password_hash, nombres, apellidos, rol, estado)
            VALUES ('user', 'user', 'Usuario', 'Local', 'OPERADOR', 1)
        """)

    connection.commit()
