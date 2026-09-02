import sqlite3
import csv
from datetime import date

def exportar_inv(tabla):
    conn = sqlite3.connect('db/orap2022.db') 
    cursor = conn.cursor()
    cursor.execute(f""" SELECT * FROM "{tabla}" """)
    today = date.today()
    archivo = str(tabla)+"_"+today.strftime("%d_%m_%Y")+".csv"

    with open("exportar/"+archivo, "w", newline="", encoding='utf-8-sig') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=",", quoting=csv.QUOTE_ALL)
        csv_writer.writerow([i[0] for i in cursor.description])
        csv_writer.writerows(cursor)

def crear(nombd):
    connection = sqlite3.connect('db/'+ str(nombd)+'.db')
    cursor = connection.cursor()
    create_table = '''CREATE TABLE personal (
        Acta        STRING  PRIMARY KEY,
        dep         VARCHAR,
        prov        VARCHAR,
        dist        VARCHAR,
        local       VARCHAR,
        area        VARCHAR,
        oficina     VARCHAR,
        dni         VARCHAR,
        nombre      VARCHAR,
        apellidoPat VARCHAR,
        apellidoMat VARCHAR
                        );'''
    cursor.execute(create_table)

def importar(archivo, valor):
    conn = sqlite3.connect('db/orap2022.db')
    cur = conn.cursor()
    
    with open(archivo, 'r', encoding='utf-8') as fin:
        reader = csv.reader(fin, delimiter=',')
        next(reader)
        if valor == 1:
            sql = """INSERT INTO personal (Acta, dep, prov, dist, local, area, oficina, dni, 
                            nombre, apellidoPat, apellidoMat) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        else:
            sql = """INSERT INTO bienes (CodInt, ActaAnt, Inv, CodPat, DenBien, NroDocAdq, FechAdq, ValAdq, DepAcum, ValNeto,
                            CtaCont, DenCta, Estado, Marca, Modelo, Tipo, Color, Serie, Dimension, Placa, NroMotor, 
                            NroChasis, Matricula, AñoFab, Nota, Obs, FechInv, Otros, Situacion) VALUES(
                                                                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                                                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                                                                    ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cur.executemany(sql, reader)
        conn.commit()
        conn.close()

