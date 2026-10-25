import sqlite3
from sqlite3 import Error
from db.conex import iniciar_conexion_sqlite

def obtener_oficinas():
    """Retorna la lista de oficinas registradas en la tabla personal ordenadas por código y nombre."""
    conn = iniciar_conexion_sqlite()
    if not conn:
        return []
    sql = """
        SELECT DISTINCT 
            CAST(Acta AS TEXT) AS Acta, 
            COALESCE(local, '') AS local, 
            COALESCE(area, '') AS area, 
            COALESCE(oficina, '') AS oficina 
        FROM personal 
        WHERE oficina IS NOT NULL AND TRIM(oficina) != ''
        ORDER BY oficina ASC
    """
    try:
        cur = conn.cursor()
        cur.execute(sql)
        filas = cur.fetchall()
        oficinas = []
        for f in filas:
            acta = str(f[0]).strip()
            local = str(f[1]).strip()
            area = str(f[2]).strip()
            oficina = str(f[3]).strip()
            display = f"[{acta}] {oficina} ({local})" if local else f"[{acta}] {oficina}"
            oficinas.append({
                "acta": acta,
                "local": local,
                "area": area,
                "oficina": oficina,
                "display": display
            })
        return oficinas
    except Error as e:
        print(f"Error en obtener_oficinas: {e}")
        return []
    finally:
        conn.close()

def filtrar_oficinas_predictivo(query, lista_oficinas):
    """
    Filtra predictivamente una lista de oficinas buscando por código de oficina (Acta),
    nombre de oficina o local, priorizando coincidencias exactas y de inicio.
    """
    if not query or not query.strip():
        return lista_oficinas

    q = query.strip().lower()

    exact_cod = []
    starts_cod = []
    starts_name = []
    contains_name = []
    others = []

    for o in lista_oficinas:
        acta = o["acta"].lower()
        ofi = o["oficina"].lower()
        loc = o["local"].lower()
        disp = o["display"].lower()

        if acta == q:
            exact_cod.append(o)
        elif acta.startswith(q):
            starts_cod.append(o)
        elif ofi.startswith(q):
            starts_name.append(o)
        elif q in ofi:
            contains_name.append(o)
        elif q in loc or q in disp:
            others.append(o)

    return exact_cod + starts_cod + starts_name + contains_name + others

def buscar_oficina_por_codigo(codigo, lista_oficinas):
    """Busca una oficina por su código exacto (Acta)."""
    if not codigo:
        return None
    c = str(codigo).strip().lower()
    for o in lista_oficinas:
        if o["acta"].lower() == c:
            return o
    return None

def filtrar_bienes_oficina(acta, filtro="todos"):
    """
    Consulta los bienes de una oficina según el filtro:
      - 'ubicados': Bienes inventariados en esta oficina (bienes.Inv = acta)
      - 'faltantes': Bienes registrados en esta oficina que no fueron inventariados (bienes.ActaAnt = acta y bienes.Inv vacío)
      - 'primera_ubicacion': Bienes originalmente asignados a esta oficina (bienes.ActaAnt = acta)
      - 'todos': Todos los bienes vinculados (Inv = acta o ActaAnt = acta)
    """
    conn = iniciar_conexion_sqlite()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        acta_str = str(acta).strip()
        base_sql = """
            SELECT 
                COALESCE(b.CodInt, '') AS CodInt, 
                COALESCE(b.CodPat, '') AS CodPat, 
                COALESCE(b.DenBien, '') AS DenBien, 
                COALESCE(CAST(b.ActaAnt AS TEXT), '') AS ActaAnt, 
                COALESCE(CAST(b.Inv AS TEXT), '') AS Inv,
                COALESCE(pu.oficina, 'No Inventariado') AS oficina_actual,
                COALESCE(pa.oficina, 'Sin Oficina') AS oficina_anterior,
                COALESCE(b.Estado, '') AS Estado
            FROM bienes b
            LEFT JOIN personal pa ON CAST(b.ActaAnt AS TEXT) = CAST(pa.Acta AS TEXT)
            LEFT JOIN personal pu ON CAST(b.Inv AS TEXT) = CAST(pu.Acta AS TEXT)
        """
        if filtro == "ubicados":
            sql = base_sql + " WHERE TRIM(CAST(b.Inv AS TEXT)) = ? ORDER BY b.CodInt ASC"
            cur.execute(sql, (acta_str,))
        elif filtro == "faltantes":
            sql = base_sql + """ 
                WHERE TRIM(CAST(b.ActaAnt AS TEXT)) = ? 
                AND (b.Inv IS NULL OR TRIM(CAST(b.Inv AS TEXT)) = '' OR LOWER(TRIM(CAST(b.Inv AS TEXT))) = 'no inventariado') 
                ORDER BY b.CodInt ASC
            """
            cur.execute(sql, (acta_str,))
        elif filtro == "primera_ubicacion":
            sql = base_sql + " WHERE TRIM(CAST(b.ActaAnt AS TEXT)) = ? ORDER BY b.CodInt ASC"
            cur.execute(sql, (acta_str,))
        else: # todos
            sql = base_sql + " WHERE TRIM(CAST(b.ActaAnt AS TEXT)) = ? OR TRIM(CAST(b.Inv AS TEXT)) = ? ORDER BY b.CodInt ASC"
            cur.execute(sql, (acta_str, acta_str))

        filas = cur.fetchall()
        bienes = []
        for f in filas:
            codint = str(f[0]).strip()
            codpat = str(f[1]).strip()
            deno = str(f[2]).strip()
            acta_ant = str(f[3]).strip()
            inv = str(f[4]).strip()
            ofi_act = str(f[5]).strip()
            ofi_ant = str(f[6]).strip()
            estado = str(f[7]).strip()

            es_inventariado = bool(inv and inv.lower() != 'no inventariado')
            if es_inventariado and inv == acta_str:
                estado_filtro = "Ubicado"
                ofi_etiqueta = ofi_act if ofi_act != 'No Inventariado' else ofi_ant
            elif not es_inventariado and acta_ant == acta_str:
                estado_filtro = "Faltante"
                ofi_etiqueta = ofi_ant
            elif acta_ant == acta_str:
                estado_filtro = "Primera Ubic."
                ofi_etiqueta = ofi_ant
            else:
                estado_filtro = "Asignado"
                ofi_etiqueta = ofi_act if es_inventariado else ofi_ant

            bienes.append({
                "codint": codint,
                "codpat": codpat,
                "deno": deno,
                "acta_ant": acta_ant,
                "inv": inv,
                "oficina_actual": ofi_act,
                "oficina_anterior": ofi_ant,
                "estado_bien": estado,
                "estado_filtro": estado_filtro,
                "oficina_etiqueta": ofi_etiqueta
            })
        return bienes
    except Error as e:
        print(f"Error en filtrar_bienes_oficina: {e}")
        return []
    finally:
        conn.close()

def buscar_bien_por_codigo(codigo):
    """Busca un bien por código patrimonial o interno para agregar a una lista."""
    conn = iniciar_conexion_sqlite()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cod_str = str(codigo).strip()
        sql = """
            SELECT 
                COALESCE(b.CodInt, '') AS CodInt, 
                COALESCE(b.CodPat, '') AS CodPat, 
                COALESCE(b.DenBien, '') AS DenBien, 
                COALESCE(CAST(b.ActaAnt AS TEXT), '') AS ActaAnt, 
                COALESCE(CAST(b.Inv AS TEXT), '') AS Inv,
                COALESCE(pu.oficina, 'No Inventariado') AS oficina_actual,
                COALESCE(pa.oficina, 'Sin Oficina') AS oficina_anterior,
                COALESCE(b.Estado, '') AS Estado
            FROM bienes b
            LEFT JOIN personal pa ON CAST(b.ActaAnt AS TEXT) = CAST(pa.Acta AS TEXT)
            LEFT JOIN personal pu ON CAST(b.Inv AS TEXT) = CAST(pu.Acta AS TEXT)
            WHERE TRIM(CAST(b.CodInt AS TEXT)) = ? OR TRIM(CAST(b.CodPat AS TEXT)) = ?
            LIMIT 1
        """
        cur.execute(sql, (cod_str, cod_str))
        f = cur.fetchone()
        if not f:
            return None
        codint = str(f[0]).strip()
        codpat = str(f[1]).strip()
        deno = str(f[2]).strip()
        acta_ant = str(f[3]).strip()
        inv = str(f[4]).strip()
        ofi_act = str(f[5]).strip()
        ofi_ant = str(f[6]).strip()
        estado = str(f[7]).strip()

        es_inventariado = bool(inv and inv.lower() != 'no inventariado')
        estado_filtro = "Ubicado" if es_inventariado else "Pendiente"
        ofi_etiqueta = ofi_act if es_inventariado and ofi_act != 'No Inventariado' else ofi_ant

        return {
            "codint": codint,
            "codpat": codpat,
            "deno": deno,
            "acta_ant": acta_ant,
            "inv": inv,
            "oficina_actual": ofi_act,
            "oficina_anterior": ofi_ant,
            "estado_bien": estado,
            "estado_filtro": estado_filtro,
            "oficina_etiqueta": ofi_etiqueta
        }
    except Error as e:
        print(f"Error en buscar_bien_por_codigo: {e}")
        return None
    finally:
        conn.close()
