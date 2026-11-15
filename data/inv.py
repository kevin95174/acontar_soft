import csv
import os
from datetime import date
from tkinter import messagebox as mb
from db.query import mostrar_inventario
from utils.export_utils import solicitar_ruta_guardado, generar_nombre_estandar, abrir_archivo_generado

def exportar_inv(acta, parent=None):
    try:
        r = mostrar_inventario(acta)
        if not r:
            mb.showwarning(title="Sin datos", message=f"No se encontraron registros para el acta {acta}.", parent=parent)
            return None
        sugerido = generar_nombre_estandar("Inventario_Acta", identificador=str(acta), extension="csv")
        ruta_csv = solicitar_ruta_guardado(
            tipo="csv",
            nombre_sugerido=sugerido,
            carpeta_defecto="exportar",
            parent=parent,
            titulo=f"Exportar Inventario Acta {acta} a CSV"
        )
        if not ruta_csv:
            return None

        os.makedirs(os.path.dirname(os.path.abspath(ruta_csv)), exist_ok=True)
        with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")
            csv_writer.writerows(r)

        abrir_archivo_generado(
            ruta_csv,
            parent=parent,
            mensaje_exito="Inventario exportado con éxito a formato CSV."
        )
        return ruta_csv
    except Exception as e:
        mb.showerror(message=f"Ha ocurrido un error al exportar el inventario:\n{e}", title="Error", parent=parent)
        return None
