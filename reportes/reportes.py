import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas
from db.query import datos_iniciales

def iniciar_reporte(reporte, encabezados, datos, colWidths, direccion,
                    subtitulo=None, entidad=None, logo_path=None, mostrar_logo=True,
                    cols_metadata=None):

    if direccion.lower().endswith('.pdf'):
        pathpdf = direccion
    else:
        pdf_name = str(reporte).strip() + ".pdf"
        pathpdf = os.path.join(direccion, pdf_name)

    os.makedirs(os.path.dirname(os.path.abspath(pathpdf)), exist_ok=True)

    doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                            rightMargin=40, leftMargin=40,
                            topMargin=20, bottomMargin=50)
    
    elements = []

    # Obtener entidad y fecha dinámicamente si no se suministran
    datos_ini = datos_iniciales()
    if not entidad:
        entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1]) else "ENTIDAD"

    if not subtitulo:
        fecha_inv = str(datos_ini[3]) if (datos_ini and len(datos_ini) > 3 and datos_ini[3]) else (str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2]) else "")
        texto_inventario = f"Inventario patrimonial al {fecha_inv}" if fecha_inv else "Inventario patrimonial"
    else:
        texto_inventario = subtitulo

    # Títulos institucionales
    h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName='HELVETICA-BOLD')
    titulo1 = [[Paragraph(str(reporte), h1)]]
    titulo2 = [[Paragraph(str(texto_inventario), h1)]]
    titulo3 = [[Paragraph(str(entidad), h1)]]

    # Crear celdas de la tabla con los estilos y fuentes configurados por columna
    table_data = []
    for row in datos:
        row_data = []
        for index, cell in enumerate(row):
            meta = cols_metadata[index] if (cols_metadata and index < len(cols_metadata)) else {}
            fn = meta.get("font_name", "Helvetica")
            try:
                fs = float(meta.get("font_size", 7))
            except Exception:
                fs = 7.0
            align_str = str(meta.get("align", "LEFT")).upper()
            align_val = 1 if align_str == "CENTER" else (2 if align_str == "RIGHT" else 0)

            c_style = ParagraphStyle(
                name=f"Cell_{index}_{fn}_{fs}_{align_val}",
                fontName=fn,
                fontSize=fs,
                leading=fs + 1.5,
                alignment=align_val
            )
            row_data.append(Paragraph(str(cell if cell is not None else ""), c_style))
        table_data.append(row_data)
    
    tabla = titulo1 + titulo2 + titulo3 + [encabezados] + list(table_data)

    # Definir alturas de fila exactas para calibración milimétrica con el diseñador
    rowHeights = [26, 12, 24, 22] + [None] * (len(tabla) - 4)
    
    estilos_comunes = [
        # titulo Reporte...
        ('SPAN', (0, 0), (-1, 0)),
        # titulo2 inventario
        ('SPAN', (0, 1), (-1, 1)),
        # titulo3 inventario
        ('SPAN', (0, 2), (-1, 2)),
        # encabezado
        ('BACKGROUND', (0, 3), (-1, 3), '#DBDBDB'),
        # Bordes de la tabla
        ('GRID', (0, 3), (-1, -1), 0.5, colors.black),
        # cuerpo de la tabla
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
        # alinea verticalmente los títulos
        ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
        ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
        ('VALIGN', (0, 2), (-1, 2), 'TOP'),
        # alinea verticalmente toda la tabla
        ('VALIGN', (0, 3), (-1, -1), 'MIDDLE'),
        # Padding controlado para que las líneas coincidan con exactitud
        ('TOPPADDING', (0, 3), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 3), (-1, -1), 2),
        ('LEFTPADDING', (0, 3), (-1, -1), 3),
        ('RIGHTPADDING', (0, 3), (-1, -1), 3),
    ]

    # Aplicar color de fondo personalizado por columna en el encabezado si existe
    if cols_metadata:
        for idx_col, meta in enumerate(cols_metadata):
            bg = meta.get("header_bg")
            if bg:
                try:
                    estilos_comunes.append(('BACKGROUND', (idx_col, 3), (idx_col, 3), colors.HexColor(bg)))
                except Exception:
                    pass

    if str(reporte) == "CONCILIACIÓN DE INVENTARIO":
        estilos_comunes.extend([
            ('ALIGN', (2, 4), (2, -1), 'RIGHT'),
            ('ALIGN', (4, 4), (4, -1), 'RIGHT'),
            ('ALIGN', (6, 4), (6, -1), 'RIGHT'),
            ('ALIGN', (3, 4), (3, -1), 'CENTER'),
            ('ALIGN', (5, 4), (5, -1), 'CENTER'),
            ('ALIGN', (7, 4), (7, -1), 'CENTER'),
        ])
    
    # hAlign='LEFT' para que la tabla comience exactamente en leftMargin=40.0 pt
    t = Table(tabla, colWidths, rowHeights=rowHeights, repeatRows=4, style=estilos_comunes, hAlign='LEFT')
    elements.append(t)

    def make_canvas(*args, **kwargs):
        return PageNumCanvas(*args, orientacion=0, logo_path=logo_path, mostrar_logo=mostrar_logo, **kwargs)

    doc.build(elements, canvasmaker=make_canvas)
    return pathpdf
