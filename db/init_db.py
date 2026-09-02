# database/init_db.py
def init_db(connection):
    cursor = connection.cursor()
    
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT NULL,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

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
        estado INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_interno TEXT NOT NULL,
        codigo_patrimonial TEXT NOT NULL,
        denominacion TEXT NOT NULL,
        nro_doc_adq TEXT DEFAULT NULL,
        fech_adq DATE DEFAULT NULL,
        val_adq REAL DEFAULT NULL,
        estado TEXT DEFAULT NULL,
        situacion TEXT DEFAULT NULL,
        estado_conservacion TEXT NOT NULL,
        marca TEXT DEFAULT NULL,
        modelo TEXT DEFAULT NULL,
        tipo TEXT DEFAULT NULL,
        color TEXT DEFAULT NULL,
        serie TEXT DEFAULT NULL,
        dimension TEXT DEFAULT NULL,
        placa TEXT DEFAULT NULL,
        nro_motor TEXT DEFAULT NULL,
        nro_chasis TEXT DEFAULT NULL,
        matricula TEXT DEFAULT NULL,
        anio INTEGER DEFAULT NULL,
        nota TEXT DEFAULT NULL,
        observacion TEXT DEFAULT NULL,
        otros TEXT DEFAULT NULL,
        codigo_ubicacion INTEGER DEFAULT NULL,
        codigo_personal TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        codigo_interno TEXT NOT NULL,
        codigo_patrimonial TEXT NOT NULL,
        denominacion TEXT NOT NULL,
        cuenta_contable TEXT,
        denominacion_cuenta TEXT,
        nro_doc_adq TEXT,
        fech_adq TEXT,
        val_adq REAL,
        dep_acumulada REAL,
        valor_neto REAL,
        marca TEXT,
        modelo TEXT,
        tipo TEXT,
        color TEXT,
        serie TEXT,
        dimension TEXT,
        otros TEXT,
        situacion TEXT,
        estado_conservacion TEXT NOT NULL,
        observacion TEXT,
        codigo_personal TEXT,
        codigo_ubicacion_inicial TEXT,
        codigo_ubicacion_final TEXT,
        user_id INTEGER,
        foto_url TEXT,
        fecha_inventariado TEXT,
        inventariado INTEGER DEFAULT 0,
        fecha_servidor TEXT,
        created_at TEXT,
        updated_at TEXT,
        deleted_at TEXT,
        estado TEXT,
        placa TEXT,
        nro_motor TEXT,
        nro_chasis TEXT,
        matricula TEXT,
        anio TEXT
    );
    """)

    # Cola persistente para cambios hechos cuando no hay red.  Se crea con
    # IF NOT EXISTS para que también sea una migración segura para las bases
    # locales ya instaladas.
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
    CREATE TABLE IF NOT EXISTS surplus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_ubicacion TEXT DEFAULT NULL,
        codigo_personal TEXT DEFAULT NULL,
        denominacion TEXT NOT NULL,
        marca TEXT DEFAULT NULL,
        modelo TEXT DEFAULT NULL,
        tipo TEXT DEFAULT NULL,
        color TEXT DEFAULT NULL,
        serie TEXT DEFAULT NULL,
        dimension TEXT DEFAULT NULL,
        otros TEXT DEFAULT NULL,
        situacion TEXT DEFAULT NULL,
        estado_conservacion TEXT DEFAULT NULL,
        observacion TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME DEFAULT NULL
    );
    """)

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


    connection.commit()

    
