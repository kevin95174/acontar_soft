import sqlite3
from sqlite3 import Error
from db.conex import iniciar_conexion_sqlite

def formatear_texto_ubicacion(local="", area="", oficina="", formato=None, separador=None):
    """
    Construye el texto de ubicación para la etiqueta según el formato/patrón o niveles configurados:
      - Puede recibir un patrón con marcadores: '{local} - {area} - {oficina}', '{area} - {oficina}', etc.
      - O una lista de niveles en orden: ['local', 'area', 'oficina'], ['oficina', 'area'], etc.
      - O nombres de preset: 'Local - Área - Oficina', 'Solo Oficina', etc.
      - Si formato es None, consulta automáticamente la configuración de la etiqueta en label_layout.json.
    Descarta partes vacías o duplicadas y no deja separadores sueltos.
    """
    l = str(local or "").strip()
    a = str(area or "").strip()
    o = str(oficina or "").strip()

    if o.lower() in ("no inventariado", "sin oficina"):
        o = ""

    # Si no se especificó formato o separador, consultar el diseño de etiqueta guardado
    if formato is None or separador is None:
        try:
            from label.label_layout import get_label_layout
            layout = get_label_layout()
            cfg_ubi = layout.get("elements", {}).get("ubicacion", {})
            if formato is None:
                formato = cfg_ubi.get("patron") or cfg_ubi.get("niveles") or "Local - Área - Oficina"
            if separador is None:
                separador = cfg_ubi.get("separador", " - ")
        except Exception:
            if formato is None:
                formato = "Local - Área - Oficina"
            if separador is None:
                separador = " - "

    if not separador:
        separador = " - "

    mapa = {"local": l, "area": a, "oficina": o}
    niveles = []

    if isinstance(formato, (list, tuple)):
        niveles = [str(x).strip().lower() for x in formato]
    elif isinstance(formato, str) and "{" in formato:
        import re
        matches = re.findall(r'\{(local|area|oficina)\}', formato, re.IGNORECASE)
        if matches:
            niveles = [m.lower() for m in matches]
    elif isinstance(formato, str):
        f = formato.lower().strip()
        if "oficina - área - local" in f or "oficina - area - local" in f:
            niveles = ["oficina", "area", "local"]
        elif "local - área - oficina" in f or "local - area - oficina" in f or f in ("completo", "todos"):
            niveles = ["local", "area", "oficina"]
        elif "local - área" in f or "local - area" in f:
            niveles = ["local", "area"]
        elif "área - oficina" in f or "area - oficina" in f:
            niveles = ["area", "oficina"]
        elif "local - oficina" in f:
            niveles = ["local", "oficina"]
        elif "solo oficina" in f:
            niveles = ["oficina"]

    if not niveles:
        niveles = ["local", "area", "oficina"]

    partes = []
    for niv in niveles:
        val = mapa.get(niv, "").strip()
        if val and val not in partes:
            partes.append(val)

    return separador.join(partes) if partes else (o or a or l or "")

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

def filtrar_bienes_oficina(acta, filtro="todos", formato_ubicacion=None):
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
                COALESCE(b.Estado, '') AS Estado,
                COALESCE(pu.local, '') AS local_actual,
                COALESCE(pu.area, '') AS area_actual,
                COALESCE(pa.local, '') AS local_anterior,
                COALESCE(pa.area, '') AS area_anterior
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
            loc_act = str(f[8]).strip() if len(f) > 8 else ""
            are_act = str(f[9]).strip() if len(f) > 9 else ""
            loc_ant = str(f[10]).strip() if len(f) > 10 else ""
            are_ant = str(f[11]).strip() if len(f) > 11 else ""

            es_inventariado = bool(inv and inv.lower() != 'no inventariado')
            if es_inventariado and inv == acta_str:
                estado_filtro = "Ubicado"
                loc = loc_act if ofi_act != 'No Inventariado' else loc_ant
                are = are_act if ofi_act != 'No Inventariado' else are_ant
                ofi = ofi_act if ofi_act != 'No Inventariado' else ofi_ant
            elif not es_inventariado and acta_ant == acta_str:
                estado_filtro = "Faltante"
                loc = loc_ant
                are = are_ant
                ofi = ofi_ant
            elif acta_ant == acta_str:
                estado_filtro = "Primera Ubic."
                loc = loc_ant
                are = are_ant
                ofi = ofi_ant
            else:
                estado_filtro = "Asignado"
                loc = loc_act if es_inventariado else loc_ant
                are = are_act if es_inventariado else are_ant
                ofi = ofi_act if es_inventariado else ofi_ant

            ofi_etiqueta = formatear_texto_ubicacion(loc, are, ofi, formato_ubicacion)

            bienes.append({
                "codint": codint,
                "codpat": codpat,
                "deno": deno,
                "acta_ant": acta_ant,
                "inv": inv,
                "oficina_actual": ofi_act,
                "oficina_anterior": ofi_ant,
                "local": loc,
                "area": are,
                "oficina": ofi,
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

def buscar_bien_por_codigo(codigo, formato_ubicacion=None):
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
                COALESCE(b.Estado, '') AS Estado,
                COALESCE(pu.local, '') AS local_actual,
                COALESCE(pu.area, '') AS area_actual,
                COALESCE(pa.local, '') AS local_anterior,
                COALESCE(pa.area, '') AS area_anterior
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
        loc_act = str(f[8]).strip() if len(f) > 8 else ""
        are_act = str(f[9]).strip() if len(f) > 9 else ""
        loc_ant = str(f[10]).strip() if len(f) > 10 else ""
        are_ant = str(f[11]).strip() if len(f) > 11 else ""

        es_inventariado = bool(inv and inv.lower() != 'no inventariado')
        estado_filtro = "Ubicado" if es_inventariado else "Pendiente"
        
        loc = loc_act if (es_inventariado and ofi_act != 'No Inventariado') else loc_ant
        are = are_act if (es_inventariado and ofi_act != 'No Inventariado') else are_ant
        ofi = ofi_act if (es_inventariado and ofi_act != 'No Inventariado') else ofi_ant
        ofi_etiqueta = formatear_texto_ubicacion(loc, are, ofi, formato_ubicacion)

        return {
            "codint": codint,
            "codpat": codpat,
            "deno": deno,
            "acta_ant": acta_ant,
            "inv": inv,
            "oficina_actual": ofi_act,
            "oficina_anterior": ofi_ant,
            "local": loc,
            "area": are,
            "oficina": ofi,
            "estado_bien": estado,
            "estado_filtro": estado_filtro,
            "oficina_etiqueta": ofi_etiqueta
        }
    except Error as e:
        print(f"Error en buscar_bien_por_codigo: {e}")
        return None
    finally:
        conn.close()


def clave_codigo_natural(codigo):
    """
    Genera una tupla para ordenamiento natural numérico.
    Extrae la parte numérica principal para ordenar 1, 2, 10, 100 correlativamente de menor a mayor.
    """
    import re
    txt = str(codigo or "").strip()
    if not txt:
        return (1, 999999999, "")

    m = re.search(r'\d+', txt)
    if m:
        try:
            return (0, int(m.group(0)), txt)
        except ValueError:
            pass
    return (1, 999999999, txt.lower())


def ordenar_bienes_por_ubicacion_y_codigo(bienes, por_codigo_menor_a_mayor=True):
    """
    Ordena una lista de diccionarios de bienes según la jerarquía:
      1° Local (alfabético A-Z)
      2° Área (alfabético A-Z)
      3° Oficina (alfabético A-Z)
      4° Código Patrimonial o Interno (de menor a mayor numéricamente)
    """
    if not bienes:
        return []

    def _clave_multinivel(b):
        loc = str(b.get("local", "")).strip().lower()
        are = str(b.get("area", "")).strip().lower()
        ofi = str(b.get("oficina", "")).strip().lower()

        codpat = b.get("codpat", "")
        codint = b.get("codint", "")
        cod_ref = codpat if (codpat and str(codpat).strip()) else codint

        c_key = clave_codigo_natural(cod_ref)

        loc_sort = (1, "zzz") if not loc else (0, loc)
        are_sort = (1, "zzz") if not are else (0, are)
        ofi_sort = (1, "zzz") if not ofi else (0, ofi)

        return (loc_sort, are_sort, ofi_sort, c_key)

    return sorted(bienes, key=_clave_multinivel, reverse=not por_codigo_menor_a_mayor)


def obtener_todos_los_bienes_bd(filtro="todos", formato_ubicacion=None, ordenar=True):
    """
    Obtiene todos los bienes de la base de datos vinculados con su ubicación física en personal.
    Filtros soportados:
      - 'todos': Absolutamente todos los bienes de la entidad.
      - 'ubicados': Solo bienes con inventario registrado (Inv no vacío y no 'no inventariado').
      - 'faltantes': Solo bienes asignados originalmente que no han sido inventariados.
    Si ordenar=True, los devuelve ordenados por Local ➔ Área ➔ Oficina ➔ Código (menor a mayor).
    """
    conn = iniciar_conexion_sqlite()
    if not conn:
        return []
    try:
        cur = conn.cursor()
        sql = """
            SELECT 
                COALESCE(b.CodInt, '') AS CodInt, 
                COALESCE(b.CodPat, '') AS CodPat, 
                COALESCE(b.DenBien, '') AS DenBien, 
                COALESCE(CAST(b.ActaAnt AS TEXT), '') AS ActaAnt, 
                COALESCE(CAST(b.Inv AS TEXT), '') AS Inv,
                COALESCE(pu.oficina, 'No Inventariado') AS oficina_actual,
                COALESCE(pa.oficina, 'Sin Oficina') AS oficina_anterior,
                COALESCE(b.Estado, '') AS Estado,
                COALESCE(pu.local, '') AS local_actual,
                COALESCE(pu.area, '') AS area_actual,
                COALESCE(pa.local, '') AS local_anterior,
                COALESCE(pa.area, '') AS area_anterior
            FROM bienes b
            LEFT JOIN personal pa ON CAST(b.ActaAnt AS TEXT) = CAST(pa.Acta AS TEXT)
            LEFT JOIN personal pu ON CAST(b.Inv AS TEXT) = CAST(pu.Acta AS TEXT)
        """
        cur.execute(sql)
        filas = cur.fetchall()
        bienes = []

        filtro_norm = str(filtro or "todos").lower()

        for f in filas:
            codint = str(f[0]).strip()
            codpat = str(f[1]).strip()
            deno = str(f[2]).strip()
            acta_ant = str(f[3]).strip()
            inv = str(f[4]).strip()
            ofi_act = str(f[5]).strip()
            ofi_ant = str(f[6]).strip()
            estado = str(f[7]).strip()
            loc_act = str(f[8]).strip() if len(f) > 8 else ""
            are_act = str(f[9]).strip() if len(f) > 9 else ""
            loc_ant = str(f[10]).strip() if len(f) > 10 else ""
            are_ant = str(f[11]).strip() if len(f) > 11 else ""

            es_inventariado = bool(inv and inv.lower() not in ('no inventariado', ''))

            if filtro_norm in ("ubicados", "solo_ubicados") and not es_inventariado:
                continue
            if filtro_norm in ("faltantes", "solo_faltantes") and es_inventariado:
                continue

            if es_inventariado and ofi_act != 'No Inventariado':
                estado_filtro = "Ubicado"
                loc = loc_act
                are = are_act
                ofi = ofi_act
            elif not es_inventariado:
                estado_filtro = "Faltante"
                loc = loc_ant
                are = are_ant
                ofi = ofi_ant
            else:
                estado_filtro = "Asignado"
                loc = loc_act or loc_ant
                are = are_act or are_ant
                ofi = ofi_act if ofi_act != 'No Inventariado' else ofi_ant

            ofi_etiqueta = formatear_texto_ubicacion(loc, are, ofi, formato_ubicacion)

            bienes.append({
                "codint": codint,
                "codpat": codpat,
                "deno": deno,
                "acta_ant": acta_ant,
                "inv": inv,
                "oficina_actual": ofi_act,
                "oficina_anterior": ofi_ant,
                "local": loc,
                "area": are,
                "oficina": ofi,
                "estado_bien": estado,
                "estado_filtro": estado_filtro,
                "oficina_etiqueta": ofi_etiqueta
            })

        if ordenar:
            bienes = ordenar_bienes_por_ubicacion_y_codigo(bienes, por_codigo_menor_a_mayor=True)

        return bienes
    except Error as e:
        print(f"Error en obtener_todos_los_bienes_bd: {e}")
        return []
    finally:
        conn.close()


def obtener_estructura_primera_ubicacion():
    """
    Obtiene los valores únicos de Local, Área y Oficina correspondientes a la
    PRIMERA UBICACIÓN registrada (personal vinculado mediante bienes.ActaAnt).
    """
    conn = iniciar_conexion_sqlite()
    if not conn:
        return {"locales": [], "areas": [], "oficinas": []}
    try:
        cur = conn.cursor()
        sql = """
            SELECT DISTINCT
                COALESCE(pa.local, '') AS local,
                COALESCE(pa.area, '') AS area,
                COALESCE(pa.oficina, '') AS oficina
            FROM bienes b
            LEFT JOIN personal pa ON CAST(b.ActaAnt AS TEXT) = CAST(pa.Acta AS TEXT)
            ORDER BY pa.local ASC, pa.area ASC, pa.oficina ASC
        """
        cur.execute(sql)
        filas = cur.fetchall()

        locales = set()
        areas = set()
        oficinas = set()

        for f in filas:
            l = str(f[0] or "").strip()
            a = str(f[1] or "").strip()
            o = str(f[2] or "").strip()
            if l:
                locales.add(l)
            if a:
                areas.add(a)
            if o:
                oficinas.add(o)

        return {
            "locales": sorted(list(locales)),
            "areas": sorted(list(areas)),
            "oficinas": sorted(list(oficinas))
        }
    except Error as e:
        print(f"Error en obtener_estructura_primera_ubicacion: {e}")
        return {"locales": [], "areas": [], "oficinas": []}
    finally:
        conn.close()


def obtener_bienes_primera_ubicacion(local=None, area=None, oficina=None, denominacion=None, ordenar=True, formato_ubicacion=None):
    """
    Obtiene los bienes de la base de datos basándose ESTRICTAMENTE en su PRIMERA UBICACIÓN
    (bienes.ActaAnt ➔ personal).
    Permite filtrar opcionalmente por local, área, oficina y denominación del bien.
    Ordena por defecto: Local ➔ Área ➔ Oficina ➔ Código (de menor a mayor numéricamente).
    """
    conn = iniciar_conexion_sqlite()
    if not conn:
        return []
    try:
        cur = conn.cursor()

        condiciones = ["1=1"]
        params = []

        if local and str(local).strip() and not str(local).startswith("(Todos"):
            condiciones.append("LOWER(TRIM(COALESCE(pa.local, ''))) = ?")
            params.append(str(local).strip().lower())

        if area and str(area).strip() and not str(area).startswith("(Todas"):
            condiciones.append("LOWER(TRIM(COALESCE(pa.area, ''))) = ?")
            params.append(str(area).strip().lower())

        if oficina and str(oficina).strip() and not str(oficina).startswith("(Todas"):
            condiciones.append("LOWER(TRIM(COALESCE(pa.oficina, ''))) = ?")
            params.append(str(oficina).strip().lower())

        if denominacion and str(denominacion).strip():
            condiciones.append("LOWER(COALESCE(b.DenBien, '')) LIKE ?")
            params.append(f"%{str(denominacion).strip().lower()}%")

        where_clause = " AND ".join(condiciones)

        sql = f"""
            SELECT 
                COALESCE(b.CodInt, '') AS CodInt, 
                COALESCE(b.CodPat, '') AS CodPat, 
                COALESCE(b.DenBien, '') AS DenBien, 
                COALESCE(CAST(b.ActaAnt AS TEXT), '') AS ActaAnt, 
                COALESCE(CAST(b.Inv AS TEXT), '') AS Inv,
                COALESCE(b.Estado, '') AS Estado,
                COALESCE(pa.local, '') AS local_primera,
                COALESCE(pa.area, '') AS area_primera,
                COALESCE(pa.oficina, 'Sin Oficina Asignada') AS oficina_primera
            FROM bienes b
            LEFT JOIN personal pa ON CAST(b.ActaAnt AS TEXT) = CAST(pa.Acta AS TEXT)
            WHERE {where_clause}
        """

        cur.execute(sql, tuple(params))
        filas = cur.fetchall()
        bienes = []

        for f in filas:
            codint = str(f[0]).strip()
            codpat = str(f[1]).strip()
            deno = str(f[2]).strip()
            acta_ant = str(f[3]).strip()
            inv = str(f[4]).strip()
            estado = str(f[5]).strip()
            loc = str(f[6]).strip()
            are = str(f[7]).strip()
            ofi = str(f[8]).strip()

            ofi_etiqueta = formatear_texto_ubicacion(loc, are, ofi, formato_ubicacion)

            bienes.append({
                "codint": codint,
                "codpat": codpat,
                "deno": deno,
                "acta_ant": acta_ant,
                "inv": inv,
                "local": loc,
                "area": are,
                "oficina": ofi,
                "estado_bien": estado,
                "estado_filtro": "Primera Ubic.",
                "oficina_etiqueta": ofi_etiqueta
            })

        if ordenar:
            bienes = ordenar_bienes_por_ubicacion_y_codigo(bienes, por_codigo_menor_a_mayor=True)

        return bienes
    except Error as e:
        print(f"Error en obtener_bienes_primera_ubicacion: {e}")
        return []
    finally:
        conn.close()
