import os
from tkinter import messagebox as mb
from utils.export_utils import guardar_excel_estandar, generar_nombre_estandar


def exportar_excel(arc, lista, datos, parent=None, preguntar_abrir=True):
    """
    Función estandarizada para exportar listas de datos a formato Excel (.xlsx).
    Mantiene compatibilidad con todas las llamadas del sistema y utiliza
    la utilidad centralizada utils.export_utils.guardar_excel_estandar.
    """
    try:
        if not datos:
            mb.showwarning("Atención", "No hay datos para exportar a Excel.", parent=parent)
            return None

        titulo = str(arc).strip() or "Reporte"
        sugerido = generar_nombre_estandar(titulo, extension="xlsx")

        ruta_guardada = guardar_excel_estandar(
            ruta_o_sugerido=sugerido,
            encabezados=lista,
            filas=datos,
            nombre_hoja="Datos",
            titulo_reporte=titulo,
            carpeta_defecto="exportar/reportes",
            parent=parent,
            preguntar_abrir=preguntar_abrir,
            mensaje_exito=f"Los datos de '{titulo}' se han exportado correctamente a Excel."
        )
        return ruta_guardada
    except Exception as e:
        mb.showerror(
            title="Error al exportar Excel",
            message=f"Ha ocurrido un error al exportar:\n{str(e)}",
            parent=parent
        )
        print(f"[EXP_EXCEL][ERROR] {e}")
        return None
