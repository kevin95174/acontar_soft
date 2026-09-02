import csv
from datetime import date
from tkinter import messagebox as mb
from db.query import mostrar_inventario

def exportar_inv(acta):
    try:
        r = mostrar_inventario(acta)
        today = date.today()
        archivo = str(acta)+"_"+today.strftime("%d_%m_%Y")+".csv"
        with open("exportar/"+archivo, "w", newline="") as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=",")
            csv_writer.writerows(r)
        mb.showinfo(message="Inventario exportado con exito", title="¡Atención!")
    except:
        mb.showerror(message="Ha ocurrido un error al exportar el inventario", title="Error")
