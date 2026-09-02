import sqlite3
from sqlite3 import Error
from db.conex import iniciar_conexion_sqlite

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

def mostrar_datos(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo, 
                Serie, Color, Tipo, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE bienes.Inv = "{Acta}" ORDER BY bienes.FechInv"""
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

def mostrar_datos_test(Acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodPat, CodInt, DenBien, ActaAnt, personal.local, personal.area, personal.oficina, 
                personal.nombre ||' '|| personal.apellidoPat ||' '|| personal.apellidoMat AS fullName, Estado, Dimension, Marca, Modelo, 
                Serie, Color, printf("%.2f", ValAdq), Obs, Otros, Situacion, FechInv, Inventariador, Equipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE CodPat = {Acta} OR CodInt = {Acta} ORDER BY bienes.FechInv"""
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
    if valor == 1:
        sql_sqlite = f"""SELECT DenBien, Inv, ActaAnt, Marca, Serie, Modelo, FechAdq, NroDocAdq, Color, Estado, Dimension, Obs,
                personal.local||' '||personal.area||' '||personal.oficina AS ubicacion, Otros, Situacion, CodPat, Nota, tipo
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE CodPat = "{codigo}" OR CodInt = "{codigo}" """
    elif valor == 2:
        sql_sqlite = f"""SELECT Inv ||' - '|| personal.local||' '||personal.area||' '||personal.oficina AS ubicacion
                FROM personal INNER JOIN bienes ON bienes.Inv = personal.Acta WHERE CodPat = "{codigo}" OR CodInt = "{codigo}" """

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

def buscar_bien_d(valor, codigo):
    conn_sqlite = iniciar_conexion_sqlite()
    if valor == 1:
        sql_sqlite = f"""SELECT DenBien, Inv, ActaAnt ||" - "||personal.local||' '||personal.area||' '||personal.oficina AS ubicacion, Marca, Serie, Modelo, FechAdq, NroDocAdq, Color, Estado, Dimension, Obs,
                Otros, Situacion, CodPat, Nota, Tipo, ValAdq, CtaCont ||' - '|| DenCta, CodInt
                FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta WHERE CodPat = "{codigo}" OR CodInt = "{codigo}" """
    elif valor == 2:
        sql_sqlite = f"""SELECT Marca, Modelo, Color, Serie, Estado, Dimension, Tipo
                FROM bienes WHERE CodPat = "{codigo}" OR CodInt = "{codigo}" """
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

def actualizar_registro(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" UPDATE bienes SET
                                Inv = ?,
                                FechInv = ?,
                                Inventariador = ?,
                                Equipo = ?
            WHERE CodPat = {id} OR CodInt = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f""" UPDATE bienes SET
                                Inv = ?
            WHERE CodPat = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_codint(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" UPDATE bienes SET
                                Inv = ?
            WHERE CodInt = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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


def buscar_data(criterio, campo):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT CodInt, ActaAnt, Inv, CodPat, DenBien, Estado, Dimension, Marca, Modelo, 
            Serie, Color, CtaCont, printf("%.2f", ValAdq), Obs FROM bienes WHERE "{criterio}" LIKE "%{campo}%" ORDER BY Inv, FechInv DESC"""
    
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
        
def registrar_sobrantes(a, b, c, d, e, f, g, h, i, j, k, l):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" INSERT INTO sobrantes
                (acta, local, area, oficina, den, estado, dim, marca, modelo, serie, color, obs) 
                VALUES ('{a}', '{b}', '{c}', '{d}', '{e}', '{f}', '{g}', '{h}', '{i}', '{j}', '{k}', '{l}') 
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def mostrar_sobrantes(acta):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT item, acta, local, area, oficina, den, estado, 
                marca, modelo, serie, tipo, color, dim, otros, situacion, obs, nota FROM sobrantes Where acta = "{acta}" """
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
    sql_sqlite = f"DELETE FROM sobrantes WHERE item = {id}"
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
        # print("Item eliminado")
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
    sql_sqlite = f""" UPDATE personal SET
                            nombre = ?,
                            apellidoPat = ?,
                            apellidoMat = ?,
                            dni = ?

            WHERE Acta = '{id}'
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_personal(a, b, c, d, e, f, g, h, i, j, k):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" INSERT INTO personal
                (Acta, dep, prov, dist, local, area, oficina, dni, nombre, apellidoPat, apellidoMat) 
                VALUES ('{a}', '{b}', '{c}', '{d}', '{e}', '{f}', '{g}', '{h}', '{i}', '{j}', '{k}') 
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def delete_personal(id):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"DELETE FROM personal WHERE Acta = {id}"
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
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
    sql_sqlite = f"""SELECT local||' - '|| oficina as ubicacion FROM personal Where Acta = "{Acta}" """
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
        sql_sqlite = f"""SELECT * FROM users WHERE usuario = ? AND password = ? """
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
        sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat AS name, dni, equipo FROM users WHERE usuario = ? AND password = ? """
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
    sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat AS name FROM users """
    
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
    sql_sqlite = f""" INSERT INTO users
                (usuario, password, Nombres, APat, AMat, dni) 
                VALUES ('{a}', '{b}', '{c}', '{d}', '{e}', '{f}') 
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
    except Error as e:
        print("Error al ingresar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def login_register(a, b, c, d, e, f, g):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""SELECT * FROM users WHERE usuario = ('{a}') """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchall()
        if books:
            print("Usuario ya existe")
            return 1
        else:
            sql_sqlite = f""" INSERT INTO users (usuario, password, Nombres, APat, AMat, dni, equipo) VALUES ('{a}', '{b}', '{c}', '{d}', '{e}', '{f}', '{g}') """
            cur.execute(sql_sqlite)
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
    sql_sqlite = f""" UPDATE bienes SET Inv = ? , FechInv = ?, Inventariador = ?, Equipo = ? WHERE CodPat = {id} OR CodInt = {id}"""
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f""" UPDATE bienes SET Inv = ?, FechInv = ?, Inventariador = ?, Equipo = ? WHERE CodInt = {id} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f""" UPDATE bienes SET Inv = ?, FechInv = ? WHERE CodInt = {id} """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f""" UPDATE bienes SET
                                Marca = ?,
                                Modelo = ?,
                                Color = ?,
                                Serie = ?,
                                Estado = ?,
                                Dimension = ?,
                                Obs = ?,
                                Otros = ?,
                                Situacion = ?,
                                FechAdq = ?,
                                NroDocAdq = ?,
                                Nota = ?,
                                Tipo = ?
            WHERE CodPat = {id} OR CodInt = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def estado_inventario():
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = """   SELECT Acta, local, area, oficina, 
                    SUM(CASE WHEN bienes.ActaAnt=personal.Acta THEN 1 ELSE 0 END) AS TBienes,
                    (SELECT COUNT(*) FROM bienes WHERE bienes.Inv=personal.Acta AND bienes.Inv <> '') AS TInventariados,
                    SUM(CASE WHEN bienes.Inv='' THEN 1 ELSE 0 END) AS TFaltantes,
                    (SELECT COUNT(*) FROM sobrantes WHERE sobrantes.acta=personal.Acta) AS TSobrantes
                FROM personal 
                LEFT JOIN bienes ON bienes.ActaAnt=personal.Acta
                GROUP BY personal.Acta

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
    sql_sqlite = f"""  SELECT Acta, local, area, oficina, 
                    SUM(CASE WHEN bienes.ActaAnt=personal.Acta THEN 1 ELSE 0 END) AS TBienes,
                    (SELECT COUNT(*) FROM bienes WHERE bienes.Inv=personal.Acta AND bienes.Inv <> '') AS TInventariados,
                    SUM(CASE WHEN bienes.Inv='' THEN 1 ELSE 0 END) AS TFaltantes,
                    (SELECT COUNT(*) FROM sobrantes WHERE sobrantes.acta=personal.Acta) AS TSobrantes
                FROM personal 
                LEFT JOIN bienes ON bienes.ActaAnt=personal.Acta
                WHERE "{criterio}" LIKE "%{campo}%"
                GROUP BY personal.Acta
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
    sql_sqlite = f"""  UPDATE sobrantes SET
                                acta = ?, local = ?, area = ?, oficina = ?, den = ?, estado = ?,
                                dim = ?, marca = ?, modelo = ?, serie = ?, color = ?, obs = ?,
                                tipo = ?, otros = ?, situacion = ?, nota = ?
                WHERE item = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def registrar_sobrantes(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" INSERT INTO sobrantes
                (acta, local, area, oficina, den, estado, dim, marca, modelo, serie, color, obs, tipo, otros, situacion, nota) 
                VALUES ('{a}', '{b}', '{c}', '{d}', '{e}', '{f}', '{g}', '{h}', '{i}', '{j}', '{k}', '{l}', '{m}', '{n}', '{o}', '{p}') 
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def update_inventario(id, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" UPDATE bienes SET
                                Inv = ?
            WHERE CodPat = {id} OR CodInt = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error updating data: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

def importar_inventario(data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" UPDATE bienes Set
                    Inv = ?, DenBien = ?,
                    FechInv = ?, Marca = ?, Modelo = ?, Serie = ?, Color = ?, Tipo = ?, Estado = ?, Dimension = ?,
                    Obs = ?, Otros = ?, Situacion = ?, NroDocAdq = ?, FechAdq = ?, Inventariador = ?, Equipo = ?, Nota = ?
                WHERE CodInt = ?
                """
    try:
        cur = conn_sqlite.cursor()
        cur.executemany(sql_sqlite, data)
        conn_sqlite.commit()
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
    # Por el estado de conservacion
    if valor == 1:
        sql_sqlite = """   SELECT Acta, local, area, oficina, 
                        SUM(CASE WHEN bienes.ActaAnt=personal.Acta THEN 1 ELSE 0 END) AS TBienes,
                        (SELECT COUNT(*) FROM bienes WHERE bienes.Inv=personal.Acta AND bienes.Inv <> '') AS TInventariados,
                        SUM(CASE WHEN bienes.Inv='' THEN 1 ELSE 0 END) AS TFaltantes,
                        (SELECT COUNT(*) FROM sobrantes WHERE sobrantes.acta=personal.Acta) AS TSobrantes
                    FROM personal 
                    LEFT JOIN bienes ON bienes.ActaAnt=personal.Acta
                    GROUP BY personal.Acta

                    """
    # Por cuenta contable
    elif valor == 2:
        sql_sqlite =f"""SELECT SUBSTR(CtaCont, 1,4) AS Cuenta, CtaCont, DenCta, printf("%.2f", SUM(ValAdq)) AS ValorPat, COUNT(CtaCont) AS CantPat, 
                        printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont)) AS SumaValAdq,
                        IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont),0) AS CuentaBInv,
                        printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont)) AS SumaFalt,
                        IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont),0) AS CuentaFalt
                        FROM bienes b
                        GROUP BY CtaCont;
                    """
    # Por denominacion del bien
    elif valor == 3:
        sql_sqlite = f"""SELECT DenBien,
                printf("%.2f", SUM(ValAdq)) AS ValorPat, 
                COUNT(CtaCont) AS CantPat,
                
                printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.DenBien = b.DenBien GROUP BY DenBien)) AS SumaValAdq,
                IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.DenBien = b.DenBien GROUP BY DenBien),0) AS CuentaBInv,
                
                printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.DenBien = b.DenBien GROUP BY DenBien)) AS SumaFalt,
                IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.DenBien = b.DenBien GROUP BY DenBien),0) AS CuentaFalt
        FROM bienes b
        GROUP BY DenBien;
                    """
    elif valor == 4:
        sql_sqlite = f"""   SELECT nombre||' '||apellidoPat||' '||apellidoMat AS usuario, local, area, oficina, 
                        SUM(CASE WHEN bienes.ActaAnt=personal.Acta THEN 1 ELSE 0 END) AS TBienes,
                        (SELECT COUNT(*) FROM bienes WHERE bienes.Inv=personal.Acta AND bienes.Inv <> '') AS TInventariados,
                        SUM(CASE WHEN bienes.Inv='' THEN 1 ELSE 0 END) AS TFaltantes,
                        (SELECT COUNT(*) FROM sobrantes WHERE sobrantes.acta=personal.Acta) AS TSobrantes
                    FROM personal 
                    LEFT JOIN bienes ON bienes.ActaAnt=personal.Acta
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
        sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, personal.local||' - '||personal.area||' - '||personal.local AS Ubicacion 
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
        sql_sqlite =f"""SELECT CodInt, CodPat, DenBien, Estado, Marca, Modelo, Serie, Color, printf("%.2f", ValAdq), personal.local ||" - "|| personal.area ||" - "|| personal.oficina AS UltUbicacion
                    FROM bienes INNER JOIN personal ON personal.Acta=bienes.ActaAnt WHERE bienes.Inv = ''
                    """
    elif valor == 8: # Bienes Sobrantes
        sql_sqlite =f"""SELECT local ||" - "|| area ||" - "|| oficina AS Ubicacion, den, estado, marca, modelo, serie, tipo, color, dim FROM sobrantes
                    """
    elif valor == 9: # Bienes dados de bajo sin disposición
        sql_sqlite =f"""SELECT CodInt, CodPat, DenBien, local ||" - "|| area ||" - "|| oficina AS Ubicacion, Estado, Marca, Modelo, Serie, Color, Tipo, Resolucion FROM baja INNER JOIN personal ON personal.Acta = baja.Inv
                    """
    elif valor == 10: # Conciliacion de Inventario
        sql_sqlite =f"""SELECT SUBSTR(CtaCont, 1,4) AS Cuenta, CtaCont, DenCta, printf("%.2f", SUM(ValAdq)) AS ValorPat, COUNT(CtaCont) AS CantPat, 
                        printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont)) AS SumaValAdq,
                        IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv <> '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont),0) AS CuentaBInv,
                        printf("%.2f",(SELECT SUM(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont)) AS SumaFalt,
                        IFNULL((SELECT COUNT(ValAdq) FROM bienes WHERE bienes.Inv = '' AND bienes.CtaCont = b.CtaCont GROUP BY CtaCont),0) AS CuentaFalt
                        FROM bienes b
                        GROUP BY CtaCont;
                    """
        
    elif valor == 11: # Bienes que requieren actualización tecnica
        sql_sqlite =f"""
                SELECT CodInt, CodPat, DenBien, 'CORREGIDO', Estado, Marca, Modelo, Tipo, Serie, Color, Dimension, Obs FROM bienes 
                    WHERE CodInt IN (SELECT CodInt FROM cambios_det)
                UNION ALL
                SELECT CodInt, CodPat, DenBien, 'ORIGINAL', Estado, Marca, Modelo, Tipo, Serie, Color, Dimension, Obs FROM cambios_det
                    ORDER BY CodInt
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
    sql_sqlite = f"""UPDATE vehiculos SET 
            Entidad=?, DenBien=?, NroPlaca=?, Carroceria=?, Marca=?, Modelo=?, Categoria=?, NroChasis=?, NroEjes=?,
            NroMotor=?, NroSerie=?, AFab=?, Color=?, Combustible=?, Transm=?, Cilindrada=?, Kilometraje=?,
            NroTarjVehi=? WHERE CodPat = '{codigo}' OR CodInt = '{codigo}' """
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
        sql_sqlite = f"""SELECT dni, equipo FROM users WHERE Nombres ||' '|| APat ||' '|| AMat = '{user}' """
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
        sql_sqlite = f"""SELECT Nombres ||' '|| APat ||' '|| AMat, dni, equipo FROM users WHERE equipo = '{equi}' """
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
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" SELECT * FROM datos """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite)
        books = cur.fetchone()
        return books
    except Error as e:
        print("Error selecting mostrar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()
        
def actualizar_datos(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f"""UPDATE datos SET entidad=?, periodo=?, fecha=? WHERE id = '{codigo}' """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
    except Error as e:
        print("Error al actualizar datos: " + str(e))
    finally:
        if conn_sqlite:
            cur.close()
            conn_sqlite.close()

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
    sql_sqlite = f""" UPDATE bienes SET
                                Marca = ?,
                                Modelo = ?,
                                Serie = ?,
                                Tipo = ?,
                                Color = ?,
                                Dimension = ?,
                                Estado = ?,
                                Situacion = ?
            WHERE CodPat = {id} OR CodInt = {id}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f""" UPDATE bienes SET Inv = ?, FechInv = ?, Inventariador = ?, Equipo = ? WHERE CodInt = {codigo} """
    try:
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
    sql_sqlite = f"""SELECT CodInt, CodPat, DenBien, 
    personal.local ||' '|| personal.area ||' '|| personal.oficina as Ubicacion,
    Marca, Modelo, Serie, Color, Tipo, Dimension, Estado, Situacion FROM personal INNER JOIN bienes ON bienes.ActaAnt = personal.Acta
    WHERE CodInt AND CodPat = {codigo} """
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

def update_codigo(codigo, data):
    conn_sqlite = iniciar_conexion_sqlite()
    sql_sqlite = f""" UPDATE bienes SET
                                Marca = ?,
                                Modelo = ?,
                                Serie = ?,
                                Color = ?,
                                Tipo = ?,
                                Dimension = ?,
                                Estado = ?,
                                Situacion = ?
            WHERE CodPat = {codigo} OR CodInt = {codigo}
            """
    try: 
        cur = conn_sqlite.cursor()
        cur.execute(sql_sqlite, data)
        conn_sqlite.commit()
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
                FROM users 
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