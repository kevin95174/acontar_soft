import sqlite3
import os
import configparser
from datetime import datetime
from sqlite3 import Error
from db.conex import iniciar_conexion_sqlite
from services.db_mirror import (
    mirror_inventario,
    mirror_detalles,
    mirror_sobrante,
    mirror_delete_sobrante,
    mirror_personal,
    mirror_delete_personal,
    mirror_usuario,
    mirror_vehiculo,
    sincronizar_cola_completa,
    disparar_sincronizacion_background,
)

def exportar_data(tabla):
    conn_sqlite = iniciar_conexion_sqlite()
    slq = f""" SELECT * FROM {tabla} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(slq)
        column_names = [description[0] for description in cur.description]
        books = cur.fetchall()
        lista = [column_names, books]
        return lista
    except Error as e:
        print("Error selecting exportar_data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos(acta):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql = """
            SELECT 
                b.CodPat, b.CodInt, b.DenBien, b.ActaAnt, 
                p.local, p.area, p.oficina, 
                TRIM(COALESCE(p.nombre, '') || ' ' || COALESCE(p.apellidoPat, '') || ' ' || COALESCE(p.apellidoMat, '')) AS fullName, 
                b.Estado, b.Dimension, b.Marca, b.Modelo, 
                b.Serie, b.Color, b.Tipo, printf("%.2f", b.ValAdq), 
                b.Obs, b.Otros, b.Situacion, b.FechInv, b.Inventariador, b.Equipo
            FROM bienes b
            LEFT JOIN personal p ON b.ActaAnt = p.Acta 
            WHERE CAST(b.Inv AS TEXT) = ? 
            ORDER BY b.FechInv ASC;
        """
        cursor = conn_sqlite.cursor()
        cursor.execute(sql, (str(acta).strip(),))
        registros = cursor.fetchall()
        return registros if registros is not None else []
    except Exception as e:
        print(f"Error en mostrar_datos: {e}")
        return []  # Devolver siempre una lista para evitar 'NoneType' object is not iterable

def filtro_acta(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo, 
                Serie, Color, printf("%.2f", ValAdq), Obs, FechInv
                FROM personal INNER JOIN bienes ON bienes.Inv = personal.Acta WHERE bienes.Inv = "{Acta}" ORDER BY bienes.FechInv"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_criterio(Acta, criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo,
                Serie, Color, Tipo, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE Inv = "{Acta}" AND {criterio} LIKE "%{campo}%" ORDER BY bienes.FechInv """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_criterio_val1(Acta, criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo,
                Serie, Color, Tipo, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE Inv = "{Acta}" AND {criterio} LIKE "{campo}" ORDER BY bienes.FechInv """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def ordenar_datos(Acta, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo,
                Serie, Color, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE Inv = "{Acta}" ORDER BY {campo} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_bienes():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM bienes """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_print(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT
                        bienes.DenBien,
                        bienes.CodInt,
                        bienes.CodPat,
                        COALESCE(bienes.Inv || ' - ' || pu.local || ' - ' || pu.area || ' - ' || pu.oficina, 'No Inventariado') AS ubicacionActual,
                        COALESCE(bienes.ActaAnt || ' - ' || pa.local || ' - ' || pa.area || ' - ' || pa.oficina, '---') AS ubicacionAnterior
                    FROM 
                        bienes
                    INNER JOIN 
                        personal pa ON bienes.ActaAnt = pa.Acta
                    LEFT JOIN 
                        personal pu ON bienes.Inv = pu.Acta
                    WHERE 
                        bienes.CodInt = {codigo} OR bienes.CodPat = {codigo}
                    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_test(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    cod_str = str(Acta).strip()
    sql_sqlite = """
        SELECT
            b.CodPat, b.CodInt, b.DenBien, b.ActaAnt,
            p.local, p.area, p.oficina,
            TRIM(COALESCE(p.nombre, '') || ' ' || COALESCE(p.apellidoPat, '') || ' ' || COALESCE(p.apellidoMat, '')) AS fullName,
            b.Estado, b.Dimension, b.Marca, b.Modelo,
            b.Serie, b.Color, b.Tipo, printf("%.2f", b.ValAdq),
            b.Obs, b.Otros, b.Situacion, b.FechInv, b.Inventariador, b.Equipo
        FROM bienes b
        LEFT JOIN personal p ON b.ActaAnt = p.Acta
        WHERE b.CodPat = ? OR CAST(b.CodInt AS TEXT) = ?
        ORDER BY b.FechInv
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (cod_str, cod_str))
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_datos_sobrante(item):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT local, area, oficina, den FROM sobrantes WHERE item = {item}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_acta_ant(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt FROM bienes WHERE CodPat = {Acta} OR CodInt = {Acta}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def buscar_bien(codigo, valor):
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo).strip()
    
    if valor == 1:
        # Busca el bien por CodPat o CodInt con LEFT JOIN
        sql_sqlite = """
            SELECT 
                b.DenBien, b.Inv, b.ActaAnt, b.Marca, b.Serie, b.Modelo, 
                b.FechAdq, b.NroDocAdq, b.Color, b.Estado, b.Dimension, b.Obs, 
                COALESCE(p.local || ' ' || p.area || ' ' || p.oficina, 'SIN UBICACIÓN ASIGNADA') AS ubicacion, 
                b.Otros, b.Situacion, b.CodPat, b.Nota, b.tipo 
            FROM bienes b 
            LEFT JOIN personal p ON b.ActaAnt = p.Acta 
            WHERE b.CodPat = ? OR CAST(b.CodInt AS TEXT) = ?;
        """
        params = (codigo_str, codigo_str)

    elif valor == 2:
        # Busca la ubicación final (Inv) con LEFT JOIN para evitar descartar filas
        sql_sqlite = """
            SELECT 
                COALESCE(b.Inv || ' - ' || p.local || ' ' || p.area || ' ' || p.oficina, b.Inv, 'SIN UBICACIÓN') AS ubicacion
            FROM bienes b 
            LEFT JOIN personal p ON b.Inv = p.Acta 
            WHERE b.CodPat = ? OR CAST(b.CodInt AS TEXT) = ?;
        """
        params = (codigo_str, codigo_str)

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, params)
        books = cur.fetchall()
        return books
    except Exception as e:
        print("❌ Error selecting: " + str(e))
        return []
    finally:
        if conn_sqlite:
            conn_sqlite.close()

def buscar_bien_d(valor, codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo).strip()
    if valor == 1:
        sql_sqlite = """
            SELECT
                b.DenBien,
                b.Inv,
                COALESCE(b.ActaAnt || ' - ' || personal.local || ' ' || personal.area || ' ' || personal.oficina, b.ActaAnt, '') AS ubicacion,
                b.Marca, b.Serie, b.Modelo, b.FechAdq, b.NroDocAdq, b.Color, b.Estado, b.Dimension, b.Obs,
                b.Otros, b.Situacion, b.CodPat, b.Nota, b.Tipo, b.ValAdq,
                COALESCE(b.CtaCont || ' - ' || b.DenCta, b.CtaCont, ''),
                b.CodInt
            FROM bienes b
            LEFT JOIN personal ON b.ActaAnt = personal.Acta
            WHERE b.CodPat = ? OR CAST(b.CodInt AS TEXT) = ?
        """
        params = (codigo_str, codigo_str)
    elif valor == 2:
        sql_sqlite = """
            SELECT Marca, Modelo, Color, Serie, Estado, Dimension, Tipo
            FROM bienes
            WHERE CodPat = ? OR CAST(CodInt AS TEXT) = ?
        """
        params = (codigo_str, codigo_str)
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, params)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def actualizar_registro(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if len(data) > 0 else ""
        fech_val = data[1] if len(data) > 1 else None
        inv_user = data[2] if len(data) > 2 else ""
        equipo_val = data[3] if len(data) > 3 else ""
        mirror_inventario(
            cur,
            id_str,
            inv_val,
            fech_inv=fech_val,
            inventariador=inv_user,
            equipo=equipo_val,
        )
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()



def cabecera(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT local, area, oficina, dni, nombre ||' '|| apellidoPat ||' '|| apellidoMat AS fullName
                FROM personal WHERE Acta = {id}"""    
    
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        r = cur.fetchone()
        return(r)
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_codpat(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if isinstance(data, (list, tuple)) else data
        mirror_inventario(cur, id_str, inv_val)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_codint(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if isinstance(data, (list, tuple)) else data
        mirror_inventario(cur, id_str, inv_val)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reportes(Acta, valor):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1:
        sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY CodInt) Num, CodInt||' - '||CodPat, DenBien,
                Marca, Modelo, Tipo, Color, Serie, Dimension, Otros, Situacion, Estado, 
                Obs FROM bienes Where Inv = "{Acta}" """
    elif valor == 2:
        sql_sqlite = f"""SELECT 
                ROW_NUMBER() OVER(ORDER BY CodInt) AS Num, 
                CodInt || ' - ' || CodPat AS CodIntCodPat, 
                DenBien,
                CASE 
                    WHEN Marca <> '' THEN 'Marca: ' || Marca || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Modelo <> '' THEN 'Modelo: ' || Modelo || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Tipo <> '' THEN 'Tipo: ' || Tipo || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Color <> '' THEN 'Color: ' || Color || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Serie <> '' THEN 'Serie: ' || Serie || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Dimension <> '' THEN 'Dimension: ' || Dimension || ' '
                    ELSE ''
                END ||
                CASE 
                    WHEN Otros <> '' THEN 'Otros: ' || Otros || ' '
                    ELSE ''
                END AS DetallesTecnicos,
                '',
                '',
                '',
                '',
                '',
                '',
                Situacion, 
                Estado, 
                Obs 
            FROM bienes 
            WHERE Inv = '{Acta}' """
    else:
        sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY CodInt) Num, CodPat, DenBien,
                Marca, Modelo, Tipo, Color, Serie, Dimension, Otros, Situacion, Estado, 
                Obs FROM bienes Where Inv = "{Acta}" """

    # sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY CodInt) Num, SUBSTR(CodPat, 1, 12), SUBSTR(DenBien, 1, 35),
    #         SUBSTR(Marca, 1, 14), SUBSTR(Modelo, 1, 14), SUBSTR(Tipo, 1, 10), SUBSTR(Color, 1, 10),
    #         SUBSTR(Serie, 1, 14), SUBSTR(Dimension, 1, 10), SUBSTR(Otros, 1, 7), Situacion, Estado, 
    #         SUBSTR(Obs, 1, 9) FROM bienes Where Inv = "{Acta}" """
    
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reporte_faltantes(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY CodInt) Num, CodInt, CodPat, SUBSTR(DenBien, 1, 32),  Estado, 
            Dimension, Marca, Modelo, Serie, SUBSTR(Color, 1, 9), printf("%.2f", ValAdq), SUBSTR(Obs, 1, 9) FROM bienes Where ActaAnt = "{Acta}" AND Inv = '' """
    
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reportes_sobrantes(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    # sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY item) Num, "", den, marca, 
    #         modelo, tipo, color, serie, dim, otros, situacion, estado, 
    #         obs FROM sobrantes Where acta = "{Acta}" """

    sql_sqlite = f"""SELECT 
            ROW_NUMBER() OVER (ORDER BY item) AS Num,
            '',
            den,
            CASE 
                WHEN Marca <> '' THEN 'Marca: ' || Marca || ' '
                ELSE ''
            END ||
            CASE 
                WHEN Modelo <> '' THEN 'Modelo: ' || Modelo || ' '
                ELSE ''
            END ||
            CASE 
                WHEN tipo <> '' THEN 'Tipo: ' || tipo || ' '
                ELSE ''
            END ||
            CASE 
                WHEN color <> '' THEN 'Color: ' || color || ' '
                ELSE ''
            END ||
            CASE 
                WHEN serie <> '' THEN 'Serie: ' || serie || ' '
                ELSE ''
            END ||
            CASE 
                WHEN dim <> '' THEN 'Dim: ' || dim || ' '
                ELSE ''
            END ||
            CASE
                WHEN otros <> '' THEN 'Otros: ' || otros || ''
                ELSE ''
            END AS concatenados,
            '',
                '',
                '',
                '',
                '',
                '',
            situacion,
            estado,
            obs
        FROM 
            sobrantes 
        WHERE 
            acta = "{Acta}"; """
    
    # sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY item) Num, estado, SUBSTR(den, 1, 35), SUBSTR(dim, 1, 10), 
    #         SUBSTR(modelo, 1, 14), SUBSTR(tipo, 1, 10), SUBSTR(color, 1, 10), SUBSTR(serie, 1, 10),
    #         SUBSTR(marca, 1, 14), otros, situacion, estado, SUBSTR(obs, 1, 9) FROM sobrantes Where acta = "{Acta}" """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reportes_bienes_inv(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT ROW_NUMBER() OVER(ORDER BY CodInt) Num, CodInt, SUBSTR(CodPat, 1, 12), SUBSTR(DenBien, 1, 35),
            SUBSTR(Marca, 1, 14), SUBSTR(Modelo, 1, 14), SUBSTR(Tipo, 1, 10), SUBSTR(Color, 1, 10),
            SUBSTR(Serie, 1, 14), SUBSTR(Dimension, 1, 10), Estado, printf("%.2f", ValAdq), Obs FROM bienes Where Inv = "{Acta}" """
    
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def preview_acta(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    # sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
    #         Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where Inv = "{Acta}" """

    sql_sqlite = f"""
        SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where Inv = "{Acta}"
            UNION
        SELECT "", "", "-SOBRANTES-", "", "", "", "", "", "", "", ""
            UNION
        SELECT "", "", den, estado, dim, marca, modelo, serie, color,"",  obs FROM sobrantes Where acta = "{Acta}"
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def buscar_criterio_acta(Acta, criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
            Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where Inv = "{Acta}" AND {criterio} LIKE "%{campo}%" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def buscar_criterio_acta_ant(Acta, criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT ActaAnt, Inv, CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
            Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where ActaAnt = "{Acta}" AND {criterio} LIKE "%{campo}%" AND Inv="" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()


def buscar_data(criterio, campo, filtro_fotos="TODOS"):
    conn_sqlite = iniciar_conexion_sqlite()
    cond_fotos = ""
    if filtro_fotos == "SIN_FOTOS":
        cond_fotos = " AND COALESCE(fp.total_fotos, 0) = 0 "
    elif filtro_fotos == "CON_FOTOS":
        cond_fotos = " AND COALESCE(fp.total_fotos, 0) > 0 "

    sql_sqlite = f"""
        WITH fotos_por_bien AS (
            SELECT
                CAST(COALESCE(
                    NULLIF(TRIM(CAST(ap.codigo_interno AS TEXT)), ''),
                    NULLIF(TRIM(CAST(ast.codigo_interno AS TEXT)), ''),
                    CAST(ap.asset_id AS TEXT)
                ) AS TEXT) AS cod_int_key,
                COUNT(*) AS total_fotos
            FROM asset_photos ap
            LEFT JOIN assets ast ON ast.id = ap.asset_id
            WHERE ap.deleted_at IS NULL
              AND COALESCE(TRIM(ap.ruta_foto), '') <> ''
            GROUP BY cod_int_key
        )
        SELECT
            b.CodInt, b.ActaAnt, b.Inv, b.CodPat, b.DenBien, b.Estado, b.Dimension, b.Marca, b.Modelo,
            b.Serie, b.Color, b.CtaCont, printf("%.2f", b.ValAdq), b.Obs,
            COALESCE(fp.total_fotos, 0) AS TotalFotos
        FROM bienes b
        LEFT JOIN fotos_por_bien fp ON fp.cod_int_key = CAST(b.CodInt AS TEXT)
        WHERE b."{criterio}" LIKE ? {cond_fotos}
        ORDER BY b.Inv, b.FechInv DESC
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (f"%{campo}%",))
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
        return []
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()


def obtener_fotos_bien(codigo):
    """
    Devuelve la lista de fotografías activas en `asset_photos` para el bien indicado
    (por `CodInt` o `CodPat`), ordenadas de la más reciente a la más antigua.
    Cada elemento es un dict: `{'id', 'asset_id', 'codigo_interno', 'ruta_foto', 'fecha', 'sincronizado'}`.
    """
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo or "").strip()
    if not codigo_str:
        return []
    try:
        cur = conn_sqlite.cursor()
        cur.execute("""
            SELECT id, asset_id, codigo_interno, codigo_patrimonial
            FROM inventory_records
            WHERE CAST(codigo_interno AS TEXT) = ? OR codigo_patrimonial = ?
            LIMIT 1
        """, (codigo_str, codigo_str))
        row_inv = cur.fetchone()
        cod_int = str(row_inv[2]) if (row_inv and row_inv[2] is not None and str(row_inv[2]).strip() != "") else codigo_str
        inv_id = row_inv[0] if row_inv else -1
        ast_id = row_inv[1] if (row_inv and row_inv[1]) else -1

        cur.execute("""
            SELECT
                ap.id,
                COALESCE(ap.asset_id, 0),
                COALESCE(NULLIF(TRIM(CAST(ap.codigo_interno AS TEXT)), ''), CAST(ast.codigo_interno AS TEXT), ?),
                COALESCE(ap.ruta_foto, ''),
                COALESCE(ap.fecha, ap.created_at, ''),
                COALESCE(ap.sincronizado, 0)
            FROM asset_photos ap
            LEFT JOIN assets ast ON ast.id = ap.asset_id
            WHERE ap.deleted_at IS NULL
              AND COALESCE(TRIM(ap.ruta_foto), '') <> ''
              AND (
                  CAST(ap.codigo_interno AS TEXT) = ?
                  OR CAST(ast.codigo_interno AS TEXT) = ?
                  OR (ap.asset_id IS NOT NULL AND ap.asset_id > 0 AND ap.asset_id IN (?, ?))
              )
            ORDER BY ap.id DESC
        """, (cod_int, cod_int, cod_int, inv_id, ast_id))
        filas = cur.fetchall()
        return [
            {
                "id": r[0],
                "asset_id": r[1],
                "codigo_interno": str(r[2] or cod_int),
                "ruta_foto": str(r[3] or ""),
                "fecha": str(r[4] or ""),
                "sincronizado": int(r[5] or 0),
            }
            for r in filas
        ]
    except Exception as e:
        print(f"Error en obtener_fotos_bien: {e}")
        return []
    finally:
        if conn_sqlite:
            conn_sqlite.close()


def agregar_foto_bien(codigo, ruta_origen, photos_dir=None):
    """
    Copia una imagen a la carpeta local `photos/`, la registra en `asset_photos`
    vinculada al bien (`codigo_interno` y `asset_id`), actualiza `foto_url` y dispara
    la sincronización en segundo plano hacia el servidor.
    """
    import shutil
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo or "").strip()
    if not codigo_str:
        raise ValueError("Debe seleccionar un bien válido para asociar la fotografía.")
    if not ruta_origen or not os.path.exists(ruta_origen):
        raise ValueError("El archivo de imagen seleccionado no existe.")

    if not photos_dir:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        photos_dir = os.path.normpath(os.path.join(base_dir, "..", "photos"))
    os.makedirs(photos_dir, exist_ok=True)

    try:
        cur = conn_sqlite.cursor()
        cur.execute("""
            SELECT id, asset_id, codigo_interno
            FROM inventory_records
            WHERE CAST(codigo_interno AS TEXT) = ? OR codigo_patrimonial = ?
            LIMIT 1
        """, (codigo_str, codigo_str))
        row_inv = cur.fetchone()

        cur.execute("""
            SELECT id, codigo_interno
            FROM assets
            WHERE CAST(codigo_interno AS TEXT) = ? OR codigo_patrimonial = ?
            LIMIT 1
        """, (codigo_str, codigo_str))
        row_ast = cur.fetchone()

        cod_int = (
            str(row_inv[2]).strip()
            if (row_inv and row_inv[2] is not None and str(row_inv[2]).strip())
            else (str(row_ast[1]).strip() if (row_ast and row_ast[1]) else codigo_str)
        )
        asset_id = (
            row_ast[0]
            if row_ast
            else (row_inv[1] if (row_inv and row_inv[1]) else (row_inv[0] if row_inv else None))
        )

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:18]
        nombre_limpio = os.path.basename(ruta_origen).replace(" ", "_")
        nombre_destino = f"code_{cod_int}_{ts}_{nombre_limpio}"
        ruta_final = os.path.join(photos_dir, nombre_destino)
        shutil.copy2(ruta_origen, ruta_final)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO asset_photos (
                asset_id, codigo_interno, ruta_foto, fecha, sincronizado, created_at, updated_at, deleted_at
            ) VALUES (?, ?, ?, ?, 0, ?, ?, NULL)
        """, (asset_id, cod_int, nombre_destino, now_str, now_str, now_str))
        nuevo_id = cur.lastrowid

        cur.execute("""
            UPDATE inventory_records
            SET foto_url = COALESCE(NULLIF(TRIM(foto_url), ''), ?), updated_at = ?
            WHERE CAST(codigo_interno AS TEXT) = ?
        """, (nombre_destino, now_str, cod_int))
        cur.execute("""
            UPDATE assets
            SET foto_url = COALESCE(NULLIF(TRIM(foto_url), ''), ?), updated_at = ?
            WHERE CAST(codigo_interno AS TEXT) = ?
        """, (nombre_destino, now_str, cod_int))

        conn_sqlite.commit()
        disparar_sincronizacion_background()
        return {
            "id": nuevo_id,
            "asset_id": asset_id,
            "codigo_interno": cod_int,
            "ruta_foto": nombre_destino,
            "fecha": now_str,
            "sincronizado": 0,
        }
    except Exception as e:
        conn_sqlite.rollback()
        raise e
    finally:
        if conn_sqlite:
            conn_sqlite.close()


def eliminar_foto_bien(photo_id):
    """
    Marca una fotografía como eliminada (`deleted_at = CURRENT_TIMESTAMP`) en `asset_photos`.
    """
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            UPDATE asset_photos
            SET deleted_at = ?, updated_at = ?
            WHERE id = ?
        """, (now_str, now_str, int(photo_id)))
        conn_sqlite.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn_sqlite.rollback()
        print(f"Error en eliminar_foto_bien: {e}")
        return False
    finally:
        if conn_sqlite:
            conn_sqlite.close()


def obtener_mapa_conteo_fotos():
    """
    Devuelve un diccionario `{str(codigo_interno): int(total_fotos)}` con el conteo
    de fotografías activas en `asset_photos` para uso rápido en tablas de inventario.
    """
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        cur.execute("""
            SELECT
                CAST(COALESCE(
                    NULLIF(TRIM(CAST(ap.codigo_interno AS TEXT)), ''),
                    NULLIF(TRIM(CAST(ast.codigo_interno AS TEXT)), ''),
                    CAST(ap.asset_id AS TEXT)
                ) AS TEXT) AS cod_int_key,
                COUNT(*) AS total_fotos
            FROM asset_photos ap
            LEFT JOIN assets ast ON ast.id = ap.asset_id
            WHERE ap.deleted_at IS NULL
              AND COALESCE(TRIM(ap.ruta_foto), '') <> ''
            GROUP BY cod_int_key
        """)
        return {str(r[0]).strip(): int(r[1] or 0) for r in cur.fetchall() if r[0] is not None}
    except Exception as e:
        print(f"Error en obtener_mapa_conteo_fotos: {e}")
        return {}
    finally:
        if conn_sqlite:
            conn_sqlite.close()
        
def registrar_sobrantes(a, b, c, d, e, f, g, h, i, j, k, l, m="", n="", o="", p=""):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        mirror_sobrante(cur, None, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_sobrantes(acta, valor):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1:
        sql_sqlite = f"""SELECT item, acta, local, area, oficina, den, estado, 
                marca, modelo, serie, tipo, color, dim, otros, situacion, obs, nota FROM sobrantes Where acta = "{acta}" """
    elif valor == 2:
        sql_sqlite = f"""SELECT item, acta, local, area, oficina, den, estado, 
                marca, modelo, serie, tipo, color, dim, otros, situacion, obs, nota FROM sobrantes """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_sobrantes_test(item):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT item, acta, local, area, oficina, den, estado, 
                dim, marca, modelo, serie, color, obs FROM sobrantes Where item = {item} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()
        
def delete_sobrante(id):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        mirror_delete_sobrante(cur, int(id))
        conn_sqlite.commit()
        return True
    except Error as e:
        print("Error Deleting book:" + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_personal():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"SELECT * FROM personal"
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchall()
        return data
    except Error as e:
        print("Error showing personal: "+ str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def actualizar_personal(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        # data: [nombre, apellidoPat, apellidoMat, dni, dep, prov, dist, local, area, oficina, EquiInv]
        mirror_personal(
            cur,
            acta=id_str,
            dep=data[4] if len(data) > 4 else "",
            prov=data[5] if len(data) > 5 else "",
            dist=data[6] if len(data) > 6 else "",
            local=data[7] if len(data) > 7 else "",
            area=data[8] if len(data) > 8 else "",
            oficina=data[9] if len(data) > 9 else "",
            dni=data[3] if len(data) > 3 else "",
            nombre=data[0] if len(data) > 0 else "",
            apellido_pat=data[1] if len(data) > 1 else "",
            apellido_mat=data[2] if len(data) > 2 else "",
            equi_inv=data[10] if len(data) > 10 else "",
        )
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_personal(a, b, c, d, e, f, g, h, i, j, k, l=""):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        mirror_personal(cur, a, b, c, d, e, f, g, h, i, j, k, l)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def delete_personal(id):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        mirror_delete_personal(cur, id_str)
        conn_sqlite.commit()
        print("Item eliminado")
        return True
    except Error as e:
        print("Error Deleting personal:" + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_d_personal(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Acta, local, area, oficina, dni, nombre ||' '|| apellidoPat ||' '|| apellidoMat AS fullName, EquiInv FROM personal WHERE Acta = "{id}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchall()
        return data
    except Error as e:
        print("Error showing personal: "+ str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def data_label(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Inv FROM bienes Where CodPat = {Acta} OR CodInt = {Acta}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def data_label_nc(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt, CodPat, DenBien FROM bienes Where CodInt = "{Acta}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def data_label_ubi(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    # sql_sqlite = f"""SELECT local||' '|| area||' '|| oficina as ubicacion FROM personal Where Acta = "{Acta}" """
    sql_sqlite = f"""SELECT oficina as ubicacion FROM personal Where Acta = "{Acta}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def query_codpat(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat FROM bienes Where CodInt = {Acta}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def query_codint(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt FROM bienes Where CodInt = {Acta} OR CodPat = {Acta}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def total_bienes(total):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT count(Inv) FROM bienes Where ActaAnt = "{total}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def total_bienes_f(total):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT count(Inv) FROM bienes Where ActaAnt = "{total}" AND Inv = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def total_bienes_s(total):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT count(acta) FROM sobrantes Where acta = "{total}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def detalle_bienes(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT ActaAnt, Inv, CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
            Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where ActaAnt = "{Acta}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def detalle_bienes_faltantes(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT ActaAnt, Inv, CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
            Serie, Color, printf("%.2f", ValAdq), Obs FROM bienes Where ActaAnt = "{Acta}" AND Inv = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def imp_eti_fal(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat FROM bienes Where ActaAnt = "{Acta}" AND Inv = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def login(user, passw):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql_sqlite = f"""SELECT * FROM usuarios WHERE usuario = ? AND password = ? """
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (user, passw))
        books = cur.fetchall()
        if books:
            return 1
        else:
            return 2
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def login_user(user, passw):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat AS name, dni, equipo, id FROM usuarios WHERE usuario = ? AND password = ? """
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (user, passw))
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def inventariador():
    
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat AS name FROM usuarios """
    
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_usuario(a, b, c, d, e, f):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        mirror_usuario(cur, a, b, c, d, e, f, "OPERADOR")
        conn_sqlite.commit()
    except Error as e:
        print("Error al ingresar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def login_register(a, b, c, d, e, f, g):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        cur.execute("SELECT id FROM users WHERE usuario = ?", (a,))
        books = cur.fetchall()
        if books:
            print("Usuario ya existe")
            return 1
        else:
            mirror_usuario(cur, a, b, c, d, e, f, g)
            conn_sqlite.commit()
            print("Registrado con exito")
            return 2
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_codpat_test(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if len(data) > 0 else ""
        fech_val = data[1] if len(data) > 1 else None
        inv_user = data[2] if len(data) > 2 else ""
        equipo_val = data[3] if len(data) > 3 else ""
        mirror_inventario(
            cur,
            id_str,
            inv_val,
            fech_inv=fech_val,
            inventariador=inv_user,
            equipo=equipo_val,
        )
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_codpat_test(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Inv FROM bienes WHERE CodPat = {id} AND Inv = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        if books:
            return 1
        else:
            return 2
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_codint_test(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if len(data) > 0 else ""
        fech_val = data[1] if len(data) > 1 else None
        inv_user = data[2] if len(data) > 2 else ""
        equipo_val = data[3] if len(data) > 3 else ""
        mirror_inventario(
            cur,
            id_str,
            inv_val,
            fech_inv=fech_val,
            inventariador=inv_user,
            equipo=equipo_val,
        )
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_codint_test(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Inv FROM bienes WHERE CodInt = {id} AND Inv = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        if books:
            return 1
        else:
            return 2
        
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_bien_nuevo(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Inv FROM bienes WHERE CodInt = {id} AND Inv = '' AND ActaAnt = '' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        if books:
            return 1
        else:
            return 2
        
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registro_fecha(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if len(data) > 0 else ""
        fech_val = data[1] if len(data) > 1 else None
        mirror_inventario(cur, id_str, inv_val, fech_val)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def seleccionar_todo(tabla):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM "{tabla}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchall()
        return data
    except Error as e:
        print("Error selecting data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_codigo(cod):
    conn_sqlite = iniciar_conexion_sqlite()
    sql = f""" SELECT * FROM bienes WHERE CodInt = {cod} OR CodPat = {cod} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql)
        data = cur.fetchall()
        if data:
            return 1
        else:
            return 2
    except Error as e:
        print("Error validando data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def val_acta(cod):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM personal WHERE Acta = "{cod}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchall()
        if data:
            return 1
        else:
            return 2
    except Error as e:
        print("Error selecting data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def delete_table(tabla):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f" DELETE FROM '{tabla}' "

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
    except Error as e:
        print("Error deleting data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def actualizar_detalles(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        mirror_detalles(cur, id_str, {
            "marca": data[0] if len(data) > 0 else "",
            "modelo": data[1] if len(data) > 1 else "",
            "color": data[2] if len(data) > 2 else "",
            "serie": data[3] if len(data) > 3 else "",
            "estado": data[4] if len(data) > 4 else "",
            "dimension": data[5] if len(data) > 5 else "",
            "observacion": data[6] if len(data) > 6 else "",
            "otros": data[7] if len(data) > 7 else "",
            "situacion": data[8] if len(data) > 8 else "",
            "fech_adq": data[9] if len(data) > 9 else "",
            "nro_doc_adq": data[10] if len(data) > 10 else "",
            "nota": data[11] if len(data) > 11 else "",
            "tipo": data[12] if len(data) > 12 else "",
        })
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def estado_inventario():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = """
        WITH b_ant AS (
            SELECT
                CAST(codigo_ubicacion_inicial AS TEXT) AS acta_key,
                COUNT(*) AS total_bienes,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS total_faltantes
            FROM inventory_records
            GROUP BY CAST(codigo_ubicacion_inicial AS TEXT)
        ),
        b_inv AS (
            SELECT
                CAST(codigo_ubicacion_final AS TEXT) AS acta_key,
                COUNT(*) AS total_inv
            FROM inventory_records
            WHERE COALESCE(inventariado, 0) = 1
              AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0')
            GROUP BY CAST(codigo_ubicacion_final AS TEXT)
        ),
        s_agg AS (
            SELECT
                CAST(codigo_ubicacion AS TEXT) AS acta_key,
                COUNT(*) AS total_sobr
            FROM surplus
            GROUP BY CAST(codigo_ubicacion AS TEXT)
        )
        SELECT
            p.Acta,
            p.local,
            p.area,
            p.oficina,
            COALESCE(ba.total_bienes, 0) AS TBienes,
            COALESCE(bi.total_inv, 0) AS TInventariados,
            COALESCE(ba.total_faltantes, 0) AS TFaltantes,
            COALESCE(sa.total_sobr, 0) AS TSobrantes
        FROM personal p
        LEFT JOIN b_ant ba ON ba.acta_key = CAST(p.Acta AS TEXT)
        LEFT JOIN b_inv bi ON bi.acta_key = CAST(p.Acta AS TEXT)
        LEFT JOIN s_agg sa ON sa.acta_key = CAST(p.Acta AS TEXT)
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchall()
        return data
    except Error as e:
        print("Error selecting data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def buscar_estado(criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""
        WITH b_ant AS (
            SELECT
                CAST(codigo_ubicacion_inicial AS TEXT) AS acta_key,
                COUNT(*) AS total_bienes,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS total_faltantes
            FROM inventory_records
            GROUP BY CAST(codigo_ubicacion_inicial AS TEXT)
        ),
        b_inv AS (
            SELECT
                CAST(codigo_ubicacion_final AS TEXT) AS acta_key,
                COUNT(*) AS total_inv
            FROM inventory_records
            WHERE COALESCE(inventariado, 0) = 1
              AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0')
            GROUP BY CAST(codigo_ubicacion_final AS TEXT)
        ),
        s_agg AS (
            SELECT
                CAST(codigo_ubicacion AS TEXT) AS acta_key,
                COUNT(*) AS total_sobr
            FROM surplus
            GROUP BY CAST(codigo_ubicacion AS TEXT)
        )
        SELECT
            p.Acta,
            p.local,
            p.area,
            p.oficina,
            COALESCE(ba.total_bienes, 0) AS TBienes,
            COALESCE(bi.total_inv, 0) AS TInventariados,
            COALESCE(ba.total_faltantes, 0) AS TFaltantes,
            COALESCE(sa.total_sobr, 0) AS TSobrantes
        FROM personal p
        LEFT JOIN b_ant ba ON ba.acta_key = CAST(p.Acta AS TEXT)
        LEFT JOIN b_inv bi ON bi.acta_key = CAST(p.Acta AS TEXT)
        LEFT JOIN s_agg sa ON sa.acta_key = CAST(p.Acta AS TEXT)
        WHERE "{criterio}" LIKE "%{campo}%"
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def actualizar_sobrante(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        mirror_sobrante(cur, int(id), *data)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def update_inventario(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if isinstance(data, (list, tuple)) else data
        mirror_inventario(cur, id_str, inv_val)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def importar_inventario(data):
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        for row in data:
            if len(row) >= 19:
                codint = row[18]
                inv_val = row[0]
                fech_inv = str(row[2] or "").lstrip("'")
                inv_usr = row[15]
                equipo_val = row[16]
                mirror_inventario(
                    cur,
                    codint,
                    inv_val,
                    fech_inv=fech_inv,
                    inventariador=inv_usr,
                    equipo=equipo_val,
                )
                mirror_detalles(cur, codint, {
                    "denominacion": row[1],
                    "marca": row[3],
                    "modelo": row[4],
                    "serie": row[5],
                    "color": row[6],
                    "tipo": row[7],
                    "estado": row[8],
                    "dimension": row[9],
                    "observacion": row[10],
                    "otros": row[11],
                    "situacion": row[12],
                    "nro_doc_adq": row[13],
                    "fech_adq": row[14],
                    "nota": row[17],
                })
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_inventario(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT 
                    Inv, DenBien, "'"||FechInv AS FechInv, Marca, Modelo, Serie, Color, Tipo, Estado, Dimension, Obs, Otros, Situacion,
                    NroDocAdq, FechAdq, Inventariador, Equipo, Nota, CodInt
                        FROM bienes
                WHERE Inv = "{id}"
                """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def test_inventario():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT 
                    Inv, DenBien, FechInv, Marca, Modelo, Serie, Color, Estado, Dimension, Obs, CodInt
                        FROM bienes
                WHERE Inv != ""
                """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_catalogo():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM catalogo """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_catalogo_criterio(criterio, dato):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM catalogo WHERE {criterio} LIKE "%{dato}%" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reporte_bienes_ubi(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre, personal.apellidoPat, personal.apellidoMat, Estado, Dimension, Marca, Modelo, 
                Serie, Color, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.Inv = personal.Acta WHERE bienes.Inv = "{Acta}" ORDER BY bienes.FechInv"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def validad_inv():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt, Inv FROM bienes"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def analisis_1(valor):
    conn_sqlite = iniciar_conexion_sqlite()
    # 1. Por ubicación (optimizado con CTEs de una sola pasada sobre inventory_records y surplus)
    if valor == 1:
        sql_sqlite = """
            WITH b_ant AS (
                SELECT
                    CAST(codigo_ubicacion_inicial AS TEXT) AS acta_key,
                    COUNT(*) AS total_bienes,
                    SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS total_faltantes
                FROM inventory_records
                GROUP BY CAST(codigo_ubicacion_inicial AS TEXT)
            ),
            b_inv AS (
                SELECT
                    CAST(codigo_ubicacion_final AS TEXT) AS acta_key,
                    COUNT(*) AS total_inv
                FROM inventory_records
                WHERE COALESCE(inventariado, 0) = 1
                  AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0')
                GROUP BY CAST(codigo_ubicacion_final AS TEXT)
            ),
            s_agg AS (
                SELECT
                    CAST(codigo_ubicacion AS TEXT) AS acta_key,
                    COUNT(*) AS total_sobr
                FROM surplus
                GROUP BY CAST(codigo_ubicacion AS TEXT)
            )
            SELECT
                p.Acta,
                p.local,
                p.area,
                p.oficina,
                COALESCE(ba.total_bienes, 0) AS TBienes,
                COALESCE(bi.total_inv, 0) AS TInventariados,
                COALESCE(ba.total_faltantes, 0) AS TFaltantes,
                COALESCE(sa.total_sobr, 0) AS TSobrantes
            FROM personal p
            LEFT JOIN b_ant ba ON ba.acta_key = CAST(p.Acta AS TEXT)
            LEFT JOIN b_inv bi ON bi.acta_key = CAST(p.Acta AS TEXT)
            LEFT JOIN s_agg sa ON sa.acta_key = CAST(p.Acta AS TEXT)
        """
    # 2. Por cuenta contable (1 sola pasada con agregación condicional en lugar de 4 subconsultas correlacionadas)
    elif valor == 2:
        sql_sqlite = """
            SELECT
                SUBSTR(COALESCE(cuenta_contable, ''), 1, 4) AS Cuenta,
                COALESCE(cuenta_contable, '') AS CtaCont,
                COALESCE(denominacion_cuenta, '') AS DenCta,
                printf("%.2f", COALESCE(SUM(COALESCE(val_adq, 0)), 0)) AS ValorPat,
                COUNT(*) AS CantPat,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaValAdq,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN 1 ELSE 0 END) AS CuentaBInv,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaFalt,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS CuentaFalt
            FROM inventory_records
            GROUP BY COALESCE(cuenta_contable, '');
        """
    # 3. Por denominación del bien (1 sola pasada con agregación condicional)
    elif valor == 3:
        sql_sqlite = """
            SELECT
                COALESCE(denominacion, '') AS DenBien,
                printf("%.2f", COALESCE(SUM(COALESCE(val_adq, 0)), 0)) AS ValorPat,
                COUNT(*) AS CantPat,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaValAdq,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN 1 ELSE 0 END) AS CuentaBInv,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaFalt,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS CuentaFalt
            FROM inventory_records
            GROUP BY COALESCE(denominacion, '');
        """
    # 4. Por usuario / responsable (optimizado con CTEs de una sola pasada)
    elif valor == 4:
        sql_sqlite = """
            WITH b_ant AS (
                SELECT
                    CAST(codigo_ubicacion_inicial AS TEXT) AS acta_key,
                    COUNT(*) AS total_bienes,
                    SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS total_faltantes
                FROM inventory_records
                GROUP BY CAST(codigo_ubicacion_inicial AS TEXT)
            ),
            b_inv AS (
                SELECT
                    CAST(codigo_ubicacion_final AS TEXT) AS acta_key,
                    COUNT(*) AS total_inv
                FROM inventory_records
                WHERE COALESCE(inventariado, 0) = 1
                  AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0')
                GROUP BY CAST(codigo_ubicacion_final AS TEXT)
            ),
            s_agg AS (
                SELECT
                    CAST(codigo_ubicacion AS TEXT) AS acta_key,
                    COUNT(*) AS total_sobr
                FROM surplus
                GROUP BY CAST(codigo_ubicacion AS TEXT)
            )
            SELECT
                p.nombre || ' ' || p.apellidoPat || ' ' || p.apellidoMat AS usuario,
                p.local,
                p.area,
                p.oficina,
                SUM(COALESCE(ba.total_bienes, 0)) AS TBienes,
                SUM(COALESCE(bi.total_inv, 0)) AS TInventariados,
                SUM(COALESCE(ba.total_faltantes, 0)) AS TFaltantes,
                SUM(COALESCE(sa.total_sobr, 0)) AS TSobrantes
            FROM personal p
            LEFT JOIN b_ant ba ON ba.acta_key = CAST(p.Acta AS TEXT)
            LEFT JOIN b_inv bi ON bi.acta_key = CAST(p.Acta AS TEXT)
            LEFT JOIN s_agg sa ON sa.acta_key = CAST(p.Acta AS TEXT)
            GROUP BY usuario
        """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def reporte_01(valor):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1: #Bienes ubicados
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, personal.local||' - '||personal.area||' - '||personal.oficina AS Ubicacion 
            FROM bienes
            LEFT JOIN personal ON personal.Acta = bienes.Inv 
            WHERE Inv <> "" ORDER BY CodInt
                    """
    elif valor == 2: # Bienes de otras entidades
        sql_sqlite = f"""SELECT CodPat, denBienA, personal.local ||" - "|| personal.area ||" - "|| personal.oficina AS Ubicacion, estado, afectante 
                    FROM bienesAfec INNER JOIN personal ON personal.Acta=bienesAfec.acta ORDER BY (denBienA)
                    """
    elif valor == 3: # Bienes que no coinciden con la descripción
        sql_sqlite = f"""
                    """
    elif valor == 4: # Bienes para actualización de valor neto
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, CtaCont, DenCta, NroDocAdq, FechAdq, printf("%.2f", ValAdq) AS ValorAdq, printf("%.2f", DepAcum) AS DepAcum, printf("%.2f", ValNeto) AS ValNeto FROM bienes WHERE bienes.Inv <> '' AND ValNeto = 1
                    """
    elif valor == 5: # Bienes en desuso o depositos
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, personal.local ||" - "|| personal.area ||" - "|| personal.oficina AS Ubicacion, Estado, Marca, Modelo, Serie, Color, Situacion
                    FROM bienes INNER JOIN personal ON personal.Acta=bienes.Inv WHERE bienes.Situacion = 'D' 
                    """
    elif valor == 6: # Bienes afectados en uso o prestamo
        sql_sqlite = f"""
                    """
    elif valor == 7: # Bienes Faltantes
        sql_sqlite =f"""SELECT CodInt, CodPat, DenBien, Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, personal.local ||" - "|| personal.area ||" - "|| personal.oficina AS UltUbicacion
                    FROM bienes INNER JOIN personal ON personal.Acta=bienes.ActaAnt WHERE bienes.Inv = '' ORDER BY CodInt
                    """
    elif valor == 8: # Bienes Sobrantes
        sql_sqlite =f"""SELECT local ||" - "|| area ||" - "|| oficina AS Ubicacion, den, estado, marca, modelo, serie, tipo, color, dim FROM sobrantes
                    """
    elif valor == 9: # Bienes dados de bajo sin disposición
        sql_sqlite =f"""SELECT CodInt, CodPat, DenBien, local ||" - "|| area ||" - "|| oficina AS Ubicacion, Estado, Marca, Modelo, Serie, Color, Tipo, Resolucion FROM baja INNER JOIN personal ON personal.Acta = baja.Inv
                    """
    elif valor == 10: # Conciliacion de Inventario
        sql_sqlite = """
            SELECT
                SUBSTR(COALESCE(cuenta_contable, ''), 1, 4) AS Cuenta,
                COALESCE(cuenta_contable, '') AS CtaCont,
                COALESCE(denominacion_cuenta, '') AS DenCta,
                printf("%.2f", COALESCE(SUM(COALESCE(val_adq, 0)), 0)) AS ValorPat,
                COUNT(*) AS CantPat,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaValAdq,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 1 AND COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') NOT IN ('', '0') THEN 1 ELSE 0 END) AS CuentaBInv,
                printf("%.2f", COALESCE(SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN COALESCE(val_adq, 0) ELSE 0 END), 0)) AS SumaFalt,
                SUM(CASE WHEN COALESCE(inventariado, 0) = 0 OR COALESCE(CAST(codigo_ubicacion_final AS TEXT), '') IN ('', '0') THEN 1 ELSE 0 END) AS CuentaFalt
            FROM inventory_records
            GROUP BY COALESCE(cuenta_contable, '');
        """
        
    elif valor == 11: # Bienes que requieren actualización tecnica
        sql_sqlite =f"""
                SELECT CodInt, CodPat, DenBien, 'CORREGIDO', Estado, Marca, Modelo, Tipo, Serie, Color, Dimension, Obs FROM bienes 
                    WHERE CodInt IN (SELECT CodInt FROM cambios_det)
                UNION ALL
                SELECT CodInt, CodPat, DenBien, 'ORIGINAL', Estado, Marca, Modelo, Tipo, Serie, Color, Dimension, Obs FROM cambios_det
                    ORDER BY CodInt
        """
    elif valor == 12: # Ubicados
        sql_sqlite =f""" SELECT CodInt, CodPat, DenBien, CtaCont, DenCta, NroDocAdq, FechAdq, printf("%,.2f", ValAdq) FROM bienes WHERE Inv <> "" ORDER BY CtaCont, NroDocAdq, CodInt """

    elif valor == 13: # Faltantes
        sql_sqlite =f""" SELECT CodInt, CodPat, DenBien, CtaCont, DenCta, NroDocAdq, FechAdq, printf("%,.2f", ValAdq) FROM bienes WHERE Inv = "" ORDER BY CtaCont, NroDocAdq, CodInt """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def rep_vehiculos():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT vehiculos.CodInt, bienes.Inv, personal.local||' - '||personal.area||' - '||personal.local AS Ubicacion, 
                Entidad, vehiculos.CodPat, vehiculos.DenBien, vehiculos.NroPlaca, Carroceria, vehiculos.Marca, 
                vehiculos.Modelo, Categoria, vehiculos.NroChasis, vehiculos.NroEjes, vehiculos.NroMotor, 
                vehiculos.NroSerie, vehiculos.AFab, vehiculos.Color, Combustible, Transm, Cilindrada, Kilometraje, NroTarjVehi
            FROM vehiculos
            LEFT JOIN bienes ON bienes.CodInt = vehiculos.CodInt 
            LEFT JOIN personal ON personal.Acta = bienes.Inv
            """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting rep_vehiculos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_vehiculo(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""UPDATE vehiculos SET
                        SistMotor=?, SistFrenos=?, SistRefri=?, SistElect=?, SistTrans=?, SistDirec=?, SistSusp=?,
                        Crreria=?, Accesorios=?, OtrCarac=?, Apreciacion=?
                        WHERE CodPat = '{codigo}' OR CodInt = '{codigo}' """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error al ingresar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def selec_vehiculos(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT SistMotor, SistFrenos, SistRefri, SistElect, SistTrans, SistDirec, SistSusp,
                        Crreria, Accesorios, OtrCarac, Apreciacion FROM vehiculos WHERE CodPat = '{codigo}' OR CodInt = '{codigo}' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def selec_vehiculos_tab1(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT Entidad, DenBien, NroPlaca, Carroceria, Marca, Modelo, Categoria, NroChasis, NroEjes,
            NroMotor, NroSerie, AFab, Color, Combustible, Transm, Cilindrada, Kilometraje,
            NroTarjVehi FROM vehiculos WHERE CodPat = '{codigo}' OR CodInt = '{codigo}' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()
        
def actualizar_vehiculo(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo).strip()
    sql_sqlite = """
        UPDATE vehiculos SET 
            Entidad=?, DenBien=?, NroPlaca=?, Carroceria=?, Marca=?, Modelo=?, Categoria=?, NroChasis=?, NroEjes=?,
            NroMotor=?, NroSerie=?, AFab=?, Color=?, Combustible=?, Transm=?, Cilindrada=?, Kilometraje=?,
            NroTarjVehi=?
        WHERE CodPat = ? OR CAST(CodInt AS TEXT) = ?
    """
    try: 
        cur = conn_sqlite.cursor()
        params = list(data) + [codigo_str, codigo_str]
        cur.execute(sql_sqlite, params)
        if cur.rowcount == 0:
            # Si aún no existía en la tabla vehiculos, lo creamos buscando su CodInt/CodPat desde bienes
            cur.execute(
                "SELECT CodInt, CodPat FROM bienes WHERE CodPat = ? OR CAST(CodInt AS TEXT) = ? LIMIT 1",
                (codigo_str, codigo_str),
            )
            b_row = cur.fetchone()
            cod_int_val = b_row[0] if b_row else codigo_str
            cod_pat_val = b_row[1] if b_row else codigo_str
            cur.execute("""
                INSERT OR REPLACE INTO vehiculos (
                    CodInt, CodPat, Entidad, DenBien, NroPlaca, Carroceria, Marca, Modelo,
                    Categoria, NroChasis, NroEjes, NroMotor, NroSerie, AFab, Color,
                    Combustible, Transm, Cilindrada, Kilometraje, NroTarjVehi
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [cod_int_val, cod_pat_val] + list(data))
        mirror_vehiculo(cur, codigo_str, data)
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error al ingresar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()
    
def detalle_analisis(valor, criterio):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1:
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq) AS ValorAdq, Obs FROM bienes WHERE ActaAnt = "{criterio}" ORDER BY (DenBien) """
    elif valor == 2:
        sql_sqlite = f"""SELECT CtaCont, CodInt, CodPat, DenBien, FechAdq, NroDocAdq, printf("%.2f", ValAdq) AS ValorAdq FROM bienes WHERE CtaCont = "{criterio}" ORDER BY (DenBien) """
    elif valor == 3:
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq) AS ValorAdq, Obs FROM bienes WHERE DenBien = '{criterio}' ORDER BY (DenBien) """
    elif valor == 4:
        # sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq) AS ValorAdq, Obs FROM bienes WHERE usuario = '{criterio}' ORDER BY (DenBien) """

        sql_sqlite = f"""  
                    SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq) AS ValorAdq, Obs
                        FROM bienes
                        JOIN personal ON bienes.ActaAnt = personal.Acta
                        WHERE nombre || ' ' || apellidoPat || ' ' || apellidoMat = "{criterio}"
                    """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def detalle_analisis_crit(valor, criterio, buscar):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1:
        sql_sqlite = f"""SELECT CtaCont, CodInt, CodPat, DenBien, FechAdq, NroDocAdq, printf("%.2f", ValAdq) AS ValorAdq FROM bienes WHERE "{criterio}" = "{buscar}" ORDER BY (DenBien) """
    elif valor == 2:
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Estado, Dimension, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq) AS ValorAdq, Obs FROM bienes WHERE "{criterio}" = '{buscar}' ORDER BY (DenBien) """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def cambio_detalles(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT * FROM bienes WHERE CodInt = {codigo} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def insertar_tabla2(row):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" INSERT INTO cambios_det (CodInt, ActaAnt, Inv, CodPat, DenBien, NroDocAdq, FechAdq, ValAdq, DepAcum, ValNeto, CtaCont,      
                                        DenCta, Estado, Marca, Modelo, Tipo, Color, Serie, Dimension, Placa, NroMotor,
                                        NroChasis, Matricula, AñoFab, Nota, Obs, FechInv, Otros, Situacion, Inventariador, Equipo)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, row)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def ficha_levantamiento(acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT 1 as sort_index, ROW_NUMBER() OVER(ORDER BY CodInt) Num, CodInt, CodPat, DenBien, Marca, Modelo, Tipo, Color, Serie, Dimension, Otros,
                    Situacion, Estado, Obs FROM bienes WHERE Inv = '{acta}'
            UNION
                SELECT 2 as sort_index, "", "-SOBRANTES-", "", "", "", "", "", "", "", "", "", "", "", ""
            UNION
                SELECT 3 as sort_index, ROW_NUMBER() OVER(ORDER BY den) Num, '', '', den, marca, modelo, tipo, color, serie, dim, otros, situacion, 
                    estado, obs FROM sobrantes WHERE acta = '{acta}'
            ORDER BY sort_index, Num
            """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def analisis_ficha(acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT
                COUNT(*) AS CantBienes, 
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Estado = 'N') AS Nuevos,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Estado = 'B') AS Buenos,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Estado = 'R') AS Regulares,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Estado = 'M') AS Malos,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Situacion = 'U') AS En_uso,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Situacion = 'D') AS En_desuso,
                (SELECT COUNT(*) FROM bienes WHERE bienes.ActaAnt = '{acta}') AS Inv_anterior,
                (SELECT COUNT(*) FROM bienes WHERE bienes.ActaAnt <> '{acta}' AND bienes.Inv = '{acta}') AS Inv_de_otras_areas,
                (SELECT COUNT(*) FROM bienes WHERE bienes.ActaAnt = '{acta}' AND bienes.Inv <> '' AND bienes.Inv <> '{acta}') AS Inv_en_otras_areas,
                (SELECT COUNT(*) FROM bienes WHERE bienes.ActaAnt = '{acta}' AND bienes.Inv='') AS Faltantes,
                (SELECT COUNT(*) FROM sobrantes WHERE sobrantes.acta = '{acta}') AS Sobrantes,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}') AS CantInv,
                SUM(CASE WHEN Estado IN ('N', 'B', 'R', 'M') THEN 1 ELSE 0 END) AS TotalEstado,
                SUM(CASE WHEN Situacion IN ('U', 'D') THEN 1 ELSE 0 END) AS TotalSituacion,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Estado='') AS SinEstado,
                (SELECT COUNT(*) FROM bienes WHERE bienes.Inv = '{acta}' AND bienes.Situacion='') AS SinSituacion
            FROM bienes WHERE Inv = '{acta}'
            """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def select_inventariador(user):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql_sqlite = f"""SELECT dni, equipo FROM usuarios WHERE Nombres ||' '|| APat ||' '|| AMat = '{user}' """
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def select_equipo(equi):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat, dni, equipo FROM usuarios WHERE equipo = '{equi}' """
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        return books
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()
        
def datos_iniciales():
    """Devuelve (id, entidad, periodo, fecha) desde la BD. Si la tabla datos esta vacia, lee config.ini."""
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = """ SELECT * FROM datos """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        if books and (books[1] or books[2]):
            return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

    # Respaldo: leer desde config.ini si la tabla datos esta vacia
    cfg_path = "config.ini"
    if os.path.exists(cfg_path):
        try:
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path, encoding="utf-8")
            if "Settings" in cfg:
                ent = cfg["Settings"].get("entidad", "")
                per = cfg["Settings"].get("periodo", "")
                if ent or per:
                    return ("1", ent, per, "")
        except Exception:
            pass
    return ("1", "", "", "")

def actualizar_datos(codigo, data):
    """Guarda entidad, periodo y fecha. Usa INSERT OR REPLACE para manejar BD vacias.
    Tambien sincroniza config.ini para que label_gen pueda leerlo como respaldo."""
    entidad = str(data[0]) if len(data) > 0 else ""
    periodo = str(data[1]) if len(data) > 1 else ""
    fecha   = str(data[2]) if len(data) > 2 else ""

    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = """INSERT OR REPLACE INTO datos (id, entidad, periodo, fecha) VALUES (?, ?, ?, ?)"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (str(codigo), entidad, periodo, fecha))
        conn_sqlite.commit()
    except Error as e:
        print("Error al actualizar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

    # Sincronizar config.ini como respaldo para label_gen
    cfg_path = "config.ini"
    try:
        cfg = configparser.ConfigParser()
        if os.path.exists(cfg_path):
            cfg.read(cfg_path, encoding="utf-8")
        if "Settings" not in cfg:
            cfg["Settings"] = {}
        cfg["Settings"]["entidad"] = entidad
        cfg["Settings"]["periodo"] = periodo
        with open(cfg_path, "w", encoding="utf-8") as f:
            cfg.write(f)
    except Exception as e:
        print(f"Advertencia: no se pudo sincronizar config.ini: {e}")

def datos_exif(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    conn_sqlite.row_factory = sqlite3.Row  # Asegura que las filas sean accesibles como diccionarios
    sql_sqlite = f""" SELECT * FROM bienes WHERE CodInt = '{codigo}' OR CodPat = '{codigo}' """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        fila = cur.fetchone()  # Obtener una sola fila
        if fila:
            resultado = dict(fila)  # Convertir la fila a un diccionario
            return resultado
        else:
            return None  # O maneja el caso donde no hay resultados
    except sqlite3.Error as e:
        print("Error al seleccionar y mostrar datos: " + str(e))
        return None
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def datos_telefono(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    conn_sqlite.row_factory = sqlite3.Row  # Asegura que las filas sean accesibles como diccionarios
    sql_sqlite = f""" SELECT CodInt, DenBien, personal.area||' - '||personal.local AS Ubicacion, Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, Situacion FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE CodPat = "{codigo}" OR CodInt = "{codigo}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        fila = cur.fetchone()  # Obtener una sola fila
        if fila:
            resultado = dict(fila)  # Convertir la fila a un diccionario
            return resultado
        else:
            return None  # O maneja el caso donde no hay resultados
    except sqlite3.Error as e:
        print("Error al seleccionar y mostrar datos: " + str(e))
        return None
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def actualizar_detalles_app(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    id_str = str(id).strip()
    try:
        cur = conn_sqlite.cursor()
        mirror_detalles(cur, id_str, {
            "marca": data[0] if len(data) > 0 else "",
            "modelo": data[1] if len(data) > 1 else "",
            "serie": data[2] if len(data) > 2 else "",
            "tipo": data[3] if len(data) > 3 else "",
            "color": data[4] if len(data) > 4 else "",
            "dimension": data[5] if len(data) > 5 else "",
            "estado": data[6] if len(data) > 6 else "",
            "situacion": data[7] if len(data) > 7 else "",
        })
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def validar(cod):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM bienes WHERE CodInt = {cod} OR CodPat = {cod} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        data = cur.fetchone()
        if data:
            return data
        else:
            return 2
    except Error as e:
        print("Error selecting data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_en_inventario(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    cod_str = str(codigo).strip()
    try:
        cur = conn_sqlite.cursor()
        inv_val = data[0] if len(data) > 0 else ""
        fech_val = data[1] if len(data) > 1 else None
        inv_usr = data[2] if len(data) > 2 else ""
        equipo_val = data[3] if len(data) > 3 else ""
        mirror_inventario(
            cur,
            cod_str,
            inv_val,
            fech_inv=fech_val,
            inventariador=inv_usr,
            equipo=equipo_val,
        )
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error selecting: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def datos_ficha(ficha):
    conn_sqlite = iniciar_conexion_sqlite()  # Suponiendo que esta función maneja la conexión a la base de datos
    conn_sqlite.row_factory = sqlite3.Row  # Asegura que las filas sean accesibles como diccionarios

    sql_sqlite = f"""SELECT bienes.CodPat, bienes.CodInt, bienes.DenBien, personal.local, personal.area, 
                    personal.oficina, personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS Responsable, 
                    bienes.Estado, bienes.Dimension, bienes.Marca, bienes.Modelo, bienes.Serie, bienes.Color, bienes.Tipo,
                    printf("%.2f", bienes.ValAdq) AS Valor, bienes.Obs, bienes.Otros, bienes.Situacion,
                    bienes.FechInv AS Fecha, bienes.Inventariador, bienes.Equipo
            FROM personal 
            INNER JOIN bienes ON bienes.ActaAnt = personal.Acta 
            WHERE bienes.Inv = "{ficha}" 
            ORDER BY bienes.FechInv"""

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        filas = cur.fetchall()  # Obtener todas las filas

        if filas:
            # Crear una lista de bienes
            bienes = []
            for fila in filas:
                bien = dict(fila)
                bienes.append(bien)

            resultado = {"Bienes": bienes}
            return resultado
        else:
            return None  # Maneja el caso donde no hay resultados
    except sqlite3.Error as e:
        print("Error al seleccionar y mostrar datos: " + str(e))
        return None
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def datos_responsable(ficha):
    conn_sqlite = iniciar_conexion_sqlite()
    conn_sqlite.row_factory = sqlite3.Row
    sql_sqlite = f"""SELECT local, area, oficina, nombre ||' '|| apellidoPat ||' '|| apellidoMat AS fullName FROM personal WHERE Acta = "{ficha}" """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        fila = cur.fetchone()
        if fila:
            resultado = dict(fila)
            return resultado
        else:
            return None
    except Error as e:
        print("Error showing personal: "+ str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def datos_codigo(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    conn_sqlite.row_factory = sqlite3.Row
    cod_str = str(codigo).strip()
    sql_sqlite = """
        SELECT CodInt, CodPat, DenBien, 
               COALESCE(personal.local || ' ' || personal.area || ' ' || personal.oficina, '') AS Ubicacion,
               Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, Situacion
        FROM bienes
        LEFT JOIN personal ON bienes.ActaAnt = personal.Acta
        WHERE CAST(bienes.CodInt AS TEXT) = ? OR bienes.CodPat = ?
    """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (cod_str, cod_str))
        fila = cur.fetchone()
        if fila:
            resultado = dict(fila)
            return resultado
        else:
            return None
    except Error as e:
        print("Error showing personal: "+ str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def update_codigo(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    cod_str = str(codigo).strip()
    try:
        cur = conn_sqlite.cursor()
        mirror_detalles(cur, cod_str, {
            "marca": data[0] if len(data) > 0 else "",
            "modelo": data[1] if len(data) > 1 else "",
            "serie": data[2] if len(data) > 2 else "",
            "color": data[3] if len(data) > 3 else "",
            "tipo": data[4] if len(data) > 4 else "",
            "dimension": data[5] if len(data) > 5 else "",
            "estado": data[6] if len(data) > 6 else "",
            "situacion": data[7] if len(data) > 7 else "",
        })
        conn_sqlite.commit()
        disparar_sincronizacion_background()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def datos_combinados(ficha):
    conn_sqlite = iniciar_conexion_sqlite()
    conn_sqlite.row_factory = sqlite3.Row  # Asegura que las filas sean accesibles como diccionarios
    
    sql_sqlite = f"""
    SELECT 
        personal.local, 
        personal.area, 
        personal.oficina, 
        personal.nombre || ' ' || personal.apellidoPat || ' ' || personal.apellidoMat AS Responsable, 
        bienes.CodPat, 
        bienes.CodInt, 
        bienes.DenBien, 
        bienes.Estado, 
        bienes.Dimension, 
        bienes.Marca, 
        bienes.Modelo, 
        bienes.Serie, 
        bienes.Color, 
        bienes.Tipo, 
        printf("%.2f", bienes.ValAdq) AS Valor, 
        bienes.Obs, 
        bienes.Otros, 
        bienes.Situacion, 
        bienes.FechInv AS Fecha, 
        bienes.Inventariador, 
        bienes.Equipo
    FROM 
        bienes
    INNER JOIN 
        personal 
    ON 
        bienes.ActaAnt = personal.Acta 
    WHERE 
        bienes.Inv = ?
    ORDER BY 
        bienes.FechInv
    """

    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (ficha,))
        filas = cur.fetchall()  # Obtener todas las filas

        if filas:
            # Crear una lista de bienes
            bienes = []
            for fila in filas:
                bien = dict(fila)
                bienes.append(bien)

            # Tomar los primeros datos de personal para el resultado final
            local = filas[0]['local']
            area = filas[0]['area']
            oficina = filas[0]['oficina']
            responsable = filas[0]['Responsable']

            resultado = {
                "Local": local,
                "Area": area,
                "Oficina": oficina,
                "Responsable": responsable,
                "Bienes": bienes
            }
            return resultado
        else:
            return None  # Maneja el caso donde no hay resultados
    except sqlite3.Error as e:
        print("Error al seleccionar y mostrar datos: " + str(e))
        return None
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def login_user_1(user, passw):
    try:
        conn_sqlite = iniciar_conexion_sqlite()
        sql_sqlite = """SELECT Nombres ||' '|| APat ||' '|| AMat AS name, equipo 
                FROM usuarios 
                WHERE usuario = ? AND password = ?"""
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, (user, passw))
        result = cur.fetchone()  # Usar fetchone ya que solo se espera un único resultado
        
        if result:
            response = {
                "Message": 1,
                "Usuario": result[0],  # nombre completo
                "Equipo": result[1]    # equipo
            }
        else:
            response = {
                "Message": 2
            }
        return response
    except Error as e:
        print(f"Error al seleccionar: {e}")
        return {"Message": "Error", "Details": str(e)}
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def save_assets(self, assets):
    cursor = self.db.connection.cursor()
    for asset in assets:
        cursor.execute("""
            INSERT OR REPLACE INTO assets(
                id,
                codigo_interno,
                codigo_patrimonial,
                denominacion,
                nro_doc_adq,
                fech_adq,
                val_adq,
                estado,
                situacion,
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
                anio,
                nota,
                observacion,
                otros,
                codigo_ubicacion,
                codigo_personal,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            asset.get("id"),
            asset["codigo_interno"],
            asset["codigo_patrimonial"],
            asset["denominacion"],
            asset.get("nro_doc_adq"),
            asset.get("fech_adq"),
            asset.get("val_adq"),
            asset.get("estado"),
            asset.get("situacion"),
            asset["estado_conservacion"],
            asset.get("marca"),
            asset.get("modelo"),
            asset.get("tipo"),
            asset.get("color"),
            asset.get("serie"),
            asset.get("dimension"),
            asset.get("placa"),
            asset.get("nro_motor"),
            asset.get("nro_chasis"),
            asset.get("matricula"),
            asset.get("anio"),
            asset.get("nota"),
            asset.get("observacion"),
            asset.get("otros"),
            asset.get("codigo_ubicacion"),
            asset.get("codigo_personal"),
            asset.get("created_at"),
            asset.get("updated_at"),
            asset.get("deleted_at")
        ))

    self.db.connection.commit()

def save_locations(self, locations):
    cursor = self.db.connection.cursor()
    for location in locations:
        cursor.execute("""
            INSERT OR REPLACE INTO locations(
                id,
                codigo_ubicacion,
                local,
                area,
                oficina,
                piso,
                direccion,
                codigo_personal,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            location.get("id"),
            location.get("codigo_ubicacion"),
            location.get("local"),
            location.get("area"),
            location.get("oficina"),
            location.get("piso"),
            location.get("direccion"),
            location.get("codigo_personal"),
            location.get("created_at"),
            location.get("updated_at"),
            location.get("deleted_at")
        ))

    self.db.connection.commit()

def save_personnel(self, personnel_list):
    cursor = self.db.connection.cursor()
    for person in personnel_list:
        cursor.execute("""
            INSERT OR REPLACE INTO personnel(
                id,
                codigo_personal,
                nombres,
                apellidos,
                cargo,
                oficina,
                telefono,
                email,
                estado,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            person.get("id"),
            person["codigo_personal"],
            person["nombres"],
            person["apellidos"],
            person.get("cargo"),
            person.get("oficina"),
            person.get("telefono"),
            person.get("email"),
            person.get("estado", 1),
            person.get("created_at"),
            person.get("updated_at"),
            person.get("deleted_at")
        ))

    self.db.connection.commit()

def save_inventory_records(self, records):
    cursor = self.db.connection.cursor()
    for record in records:
        cursor.execute("""
            INSERT OR REPLACE INTO inventory_records(
                id,
                asset_id,
                codigo_interno,
                codigo_patrimonial,
                denominacion,
                marca,
                modelo,
                tipo,
                color,
                serie,
                dimension,
                otros,
                situacion,
                estado_conservacion,
                observacion,
                codigo_personal,
                codigo_ubicacion_inicial,
                codigo_ubicacion_final,
                user_id,
                foto_url,
                fecha_inventariado,
                inventariado,
                fecha_servidor,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            record.get("id"),
            record["asset_id"],
            record["codigo_interno"],
            record["codigo_patrimonial"],
            record["denominacion"],
            record.get("marca"),
            record.get("modelo"),
            record.get("tipo"),
            record.get("color"),
            record.get("serie"),
            record.get("dimension"),
            record.get("otros"),
            record.get("situacion"),
            record["estado_conservacion"],
            record.get("observacion"),
            record.get("codigo_personal"),
            record.get("codigo_ubicacion_inicial"),
            record.get("codigo_ubicacion_final"),
            record["user_id"],
            record.get("foto_url"),
            record["fecha_inventariado"],
            record.get("inventariado", 0),
            record.get("fecha_servidor"),
            record.get("created_at"),
            record.get("updated_at"),
            record.get("deleted_at")
        ))

    self.db.connection.commit()

def save_surplus(self, surplus_list):
    cursor = self.db.connection.cursor()
    for item in surplus_list:
        cursor.execute("""
            INSERT OR REPLACE INTO surplus(
                id,
                codigo_ubicacion,
                codigo_personal,
                denominacion,
                marca,
                modelo,
                tipo,
                color,
                serie,
                dimension,
                otros,
                situacion,
                estado_conservacion,
                observacion,
                created_at,
                updated_at,
                deleted_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            item.get("id"),
            item.get("codigo_ubicacion"),
            item.get("codigo_personal"),
            item["denominacion"],
            item.get("marca"),
            item.get("modelo"),
            item.get("tipo"),
            item.get("color"),
            item.get("serie"),
            item.get("dimension"),
            item.get("otros"),
            item.get("situacion"),
            item.get("estado_conservacion"),
            item.get("observacion"),
            item.get("created_at"),
            item.get("updated_at"),
            item.get("deleted_at")
        ))

    self.db.connection.commit()

def obtener_id_inventory_record(codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    codigo_str = str(codigo).strip()
    try:
        cur = conn_sqlite.cursor()
        cur.execute("""
            SELECT id 
            FROM inventory_records 
            WHERE codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ? 
            LIMIT 1
        """, (codigo_str, codigo_str))
        
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ Error al buscar ID en inventory_records: {e}")
        return None
    finally:
        conn_sqlite.close()


def registrar_inventario_local_pendiente(codigo, record_id, acta_destino, fecha,
                                         usuario, equipo, user_id):
    """Registra un inventario directamente sobre `inventory_records` y lo encola en `inventory_sync_outbox`."""
    conn_sqlite = iniciar_conexion_sqlite()
    try:
        cur = conn_sqlite.cursor()
        codigo_str = str(codigo).strip()
        cur.execute("""
            SELECT COALESCE(inventariado, 0) FROM inventory_records
            WHERE id = ? OR codigo_patrimonial = ? OR CAST(codigo_interno AS TEXT) = ?
            LIMIT 1
        """, (int(record_id or 0), codigo_str, codigo_str))
        row = cur.fetchone()
        if not row:
            raise ValueError("No se encontró el registro local de inventario.")
        if int(row[0] or 0) == 1:
            raise ValueError("El bien ya fue registrado localmente.")

        affected = mirror_inventario(
            cur,
            codigo_str,
            acta_destino,
            fech_inv=fecha,
            user_id=int(user_id or 1),
            inventariador=str(usuario or ""),
            equipo=str(equipo or ""),
        )
        if affected == 0:
            raise ValueError("No se pudo actualizar el registro en inventory_records.")

        conn_sqlite.commit()
        return {"success": True}
    except Exception as error:
        conn_sqlite.rollback()
        print(f"❌ Error al registrar el inventario localmente: {error}")
        return {"success": False, "message": str(error)}
    finally:
        conn_sqlite.close()


def sincronizar_inventarios_pendientes(api_client, limite=50):
    """Envía toda la cola local pendiente (inventario, detalles, sobrantes, ubicaciones, personal y fotos)."""
    return sincronizar_cola_completa(api_client, limite=limite)
