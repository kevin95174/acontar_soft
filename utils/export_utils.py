"""
Módulo de utilidades centralizadas para la exportación estandarizada de
archivos PDF, Excel (.xlsx) y CSV en la aplicación.

Proporciona:
- Diálogos estándar 'Guardar como' (asksaveasfilename) con nombres sugeridos inteligentes.
- Sanitización de nombres de archivo y creación automática de carpetas destino.
- Generación de Excel estilizado y robusto con autoajuste de ancho de columnas.
- Diálogo estándar de éxito con opción de abrir el archivo directamente en el visor predeterminado del SO.
"""

import os
import re
import sys
import subprocess
from datetime import date
from tkinter import filedialog, messagebox as mb
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def sanitizar_nombre_archivo(nombre: str, reemplazo: str = "_") -> str:
    """
    Limpia un nombre de archivo eliminando caracteres no válidos para sistemas de archivos.
    """
    if not nombre:
        return "archivo"
    # Reemplazar saltos de línea y tabulaciones por espacios
    limpio = str(nombre).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    # Eliminar caracteres prohibidos en Windows/Linux: \ / : * ? " < > |
    limpio = re.sub(r'[\\/*?:"<>|]', reemplazo, limpio)
    # Reducir múltiples espacios o reemplazos consecutivos
    limpio = re.sub(rf'{re.escape(reemplazo)}+', reemplazo, limpio)
    limpio = re.sub(r'\s+', ' ', limpio).strip(' ._')
    # Limitar longitud para evitar problemas con MAX_PATH
    if len(limpio) > 120:
        limpio = limpio[:120].strip(' ._')
    return limpio or "archivo"


def generar_nombre_estandar(tipo_reporte: str, identificador: str = None, extension: str = "pdf", incluir_fecha: bool = True) -> str:
    """
    Genera un nombre estandarizado para archivos:
    Formato: [Tipo_Reporte]_[Identificador]_[YYYYMMDD].[ext]
    """
    tipo_limpio = sanitizar_nombre_archivo(tipo_reporte)
    partes = [tipo_limpio]

    if identificador:
        id_limpio = sanitizar_nombre_archivo(str(identificador))
        if id_limpio and id_limpio.lower() != tipo_limpio.lower():
            partes.append(id_limpio)

    if incluir_fecha:
        partes.append(date.today().strftime("%Y%m%d"))

    ext = extension.lstrip(".")
    return f"{'_'.join(partes)}.{ext}"


def solicitar_ruta_guardado(
    tipo: str = "pdf",
    nombre_sugerido: str = "",
    carpeta_defecto: str = "exportar",
    parent=None,
    titulo: str = None
) -> str | None:
    """
    Muestra un diálogo de guardar como estandarizado.
    Crea automáticamente la carpeta inicial si no existe.
    Retorna la ruta completa elegida o None si el usuario cancela.
    """
    tipo_norm = tipo.lower().strip()

    if tipo_norm in ("excel", "xlsx"):
        def_ext = ".xlsx"
        tipos_archivos = [("Archivos de Excel (*.xlsx)", "*.xlsx"), ("Todos los archivos", "*.*")]
        tit_defecto = "Guardar Archivo Excel"
        subcarpeta = carpeta_defecto or "exportar/reportes"
    elif tipo_norm == "csv":
        def_ext = ".csv"
        tipos_archivos = [("Archivos CSV (*.csv)", "*.csv"), ("Todos los archivos", "*.*")]
        tit_defecto = "Guardar Archivo CSV"
        subcarpeta = carpeta_defecto or "exportar"
    else:  # pdf
        def_ext = ".pdf"
        tipos_archivos = [("Archivos PDF (*.pdf)", "*.pdf"), ("Todos los archivos", "*.*")]
        tit_defecto = "Guardar Reporte PDF"
        subcarpeta = carpeta_defecto or "report_actas"

    os.makedirs(subcarpeta, exist_ok=True)

    if not nombre_sugerido:
        nombre_sugerido = f"Reporte_{date.today().strftime('%Y%m%d')}{def_ext}"
    else:
        nombre_sugerido = sanitizar_nombre_archivo(nombre_sugerido)
        if not nombre_sugerido.lower().endswith(def_ext):
            nombre_sugerido += def_ext

    ruta_elegida = filedialog.asksaveasfilename(
        title=titulo or tit_defecto,
        initialdir=os.path.abspath(subcarpeta),
        initialfile=nombre_sugerido,
        defaultextension=def_ext,
        filetypes=tipos_archivos,
        parent=parent
    )

    if not ruta_elegida:
        return None

    # Asegurar que el directorio de destino exista
    dir_destino = os.path.dirname(os.path.abspath(ruta_elegida))
    os.makedirs(dir_destino, exist_ok=True)

    return os.path.abspath(ruta_elegida)


def abrir_archivo_generado(
    ruta_archivo: str,
    parent=None,
    mensaje_exito: str = None,
    titulo: str = "Acontar S.A.C."
) -> bool:
    """
    Pregunta al usuario si desea abrir el archivo generado y lo abre con la aplicación predeterminada del sistema.
    """
    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return False

    if mensaje_exito:
        msg = f"{mensaje_exito}\n\nUbicación:\n{ruta_archivo}\n\n¿Desea abrir el archivo ahora?"
        abrir = mb.askyesno(title=titulo, message=msg, parent=parent)
        if not abrir:
            return True

    try:
        if sys.platform.startswith("win"):
            os.startfile(os.path.abspath(ruta_archivo))
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["open", os.path.abspath(ruta_archivo)])
        else:
            subprocess.Popen(["xdg-open", os.path.abspath(ruta_archivo)])
        return True
    except Exception as e:
        mb.showerror(
            title="Error al abrir archivo",
            message=f"No se pudo abrir automáticamente el archivo:\n{e}\n\nPuede abrirlo manualmente en:\n{ruta_archivo}",
            parent=parent
        )
        return False


def guardar_excel_estandar(
    ruta_o_sugerido: str = None,
    encabezados: list = None,
    filas: list = None,
    nombre_hoja: str = "Datos",
    titulo_reporte: str = "Reporte",
    carpeta_defecto: str = "exportar/reportes",
    parent=None,
    preguntar_abrir: bool = True,
    mensaje_exito: str = None
) -> str | None:
    """
    Crea un archivo Excel (.xlsx) con estilo profesional:
    - Cabecera estilizada en azul marino con letras blancas.
    - Bordes finos y alineaciones correctas.
    - Columnas con ancho autoajustable seguro (mín 12, máx 60).
    - Manejo seguro de valores None o nulos.
    - Diálogo 'Guardar como' si no se proporciona una ruta completa.
    - Pregunta al usuario para abrirlo al finalizar.
    """
    encabezados = encabezados or []
    filas = filas or []

    # Determinar si ruta_o_sugerido ya es una ruta completa o si debemos abrir el diálogo
    if ruta_o_sugerido and (os.path.isabs(ruta_o_sugerido) or os.path.sep in ruta_o_sugerido or "/" in ruta_o_sugerido):
        ruta_final = os.path.abspath(ruta_o_sugerido)
        os.makedirs(os.path.dirname(ruta_final), exist_ok=True)
    else:
        sugerido = ruta_o_sugerido or generar_nombre_estandar(titulo_reporte, extension="xlsx")
        ruta_final = solicitar_ruta_guardado(
            tipo="excel",
            nombre_sugerido=sugerido,
            carpeta_defecto=carpeta_defecto,
            parent=parent,
            titulo=f"Guardar {titulo_reporte} en Excel"
        )
        if not ruta_final:
            return None

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sanitizar_nombre_archivo(nombre_hoja)[:31] or "Datos"

    # Estilos
    fuente_cabecera = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    relleno_cabecera = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    alineacion_cabecera = Alignment(horizontal="center", vertical="center", wrap_text=True)

    fuente_datos = Font(name="Calibri", size=10)
    borde_fino = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )
    relleno_cebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # Escribir encabezados
    ws.row_dimensions[1].height = 26
    for col_idx, enc in enumerate(encabezados, start=1):
        cell = ws.cell(row=1, column=col_idx)
        val_str = str(enc).replace("\n", " ").strip() if enc is not None else f"Columna {col_idx}"
        cell.value = val_str
        cell.font = fuente_cabecera
        cell.fill = relleno_cabecera
        cell.alignment = alineacion_cabecera
        cell.border = borde_fino

    # Escribir filas de datos
    fila_actual = 2
    for r_idx, fila in enumerate(filas, start=1):
        ws.row_dimensions[fila_actual].height = 20
        es_par = (r_idx % 2 == 0)

        for col_idx in range(1, len(encabezados) + 1):
            val = fila[col_idx - 1] if col_idx - 1 < len(fila) else ""
            cell = ws.cell(row=fila_actual, column=col_idx)

            if val is None:
                cell.value = ""
            elif isinstance(val, (int, float)):
                cell.value = val
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.value = str(val).strip()
                cell.alignment = Alignment(horizontal="left", vertical="center")

            cell.font = fuente_datos
            cell.border = borde_fino
            if es_par:
                cell.fill = relleno_cebra

        fila_actual += 1

    # Ajuste automático del ancho de columnas (mínimo 12, máximo 65)
    for col_cells in ws.columns:
        col_letter = get_column_letter(col_cells[0].column)
        max_len = 0
        for cell in col_cells:
            val_txt = str(cell.value or "")
            if len(val_txt) > max_len:
                max_len = len(val_txt)
        ws.column_dimensions[col_letter].width = max(12, min(max_len + 3, 65))

    # Congelar panel de encabezado
    ws.freeze_panes = "A2"

    # Guardar
    wb.save(ruta_final)

    # Notificar y preguntar si desea abrir
    if preguntar_abrir:
        msg = mensaje_exito or f"Los datos de '{titulo_reporte}' se exportaron con éxito a Excel."
        abrir_archivo_generado(ruta_final, parent=parent, mensaje_exito=msg)

    return ruta_final
