import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas
from db.query import datos_iniciales

def iniciar_conciliacion(reporte, encabezados, datos, colWidths, direccion):

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

    # Obtener entidad y fecha dinámicamente de la BD / config.ini
    datos_ini = datos_iniciales()
    entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1]) else "ENTIDAD"
    fecha_inv = str(datos_ini[3]) if (datos_ini and len(datos_ini) > 3 and datos_ini[3]) else (str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2]) else "")
    texto_inventario = f"Inventario patrimonial al {fecha_inv}" if fecha_inv else "Inventario patrimonial"

    # Titulos
    h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName='HELVETICA-BOLD')
    titulo1 = [[Paragraph(str(reporte), h1)]]
    titulo2 = [[Paragraph(str(texto_inventario), h1)]]
    titulo3 = [[Paragraph(str(entidad), h1)]]

    c1 = ParagraphStyle(name='Normal', fontSize=7, leading=8, alignment=0)
    c2 = ParagraphStyle(name='Normal', fontSize=7, leading=8, alignment=2)
    c3 = ParagraphStyle(name='Normal', fontSize=7, leading=8, alignment=1)
    
    # Crear una lista para almacenar los datos de la tabla
    table_data = []
    # Iterar sobre las filas de la consulta
    for row in datos:
        # Crear una lista para almacenar las celdas de la fila
        row_data = []
        # Iterar sobre las celdas de la fila y crear un objeto Paragraph para cada una
        for index, cell in enumerate(row):

            if index in [0, 1, 2]:
                style = c1  # Alineación izquierda para columnas 1, 2 y 3
            elif index in [3, 5, 7]:
                style = c2  # Alineación centro para columnas 5, 7 y 9
            elif index in [4, 6, 8]:
                style = c3  # Alineación derecha para otras columnas (si es necesario)

            # Agregar la celda a la lista de celdas de la fila
            row_data.append(Paragraph(str(cell), style))
        
        # Agregar la fila completa a la lista de datos de la tabla
        table_data.append(row_data)
    
    tabla = titulo1 + titulo2 + titulo3 + [encabezados] + list(table_data)

    # Definir las alturas de fila, siendo 26 el valor para la primera fila
    rowHeights = [26, 10, 26] + [None] * (len(tabla) - 3)
    
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
                        # define el tamaño fuente y horientacion del cuerpo de la tabla
                        ('FONTSIZE', (0, 1), (-1, -1), 7),
                        ('ALIGN', (0, 3), (-1, 3), 'CENTER'),
                        # alinea verticalmente toda el titulo
                        ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
                        ('VALIGN', (0, 1), (-1, 1), 'MIDDLE'),
                        ('VALIGN', (0, 2), (-1, 2), 'TOP'),
                        # alinea verticalmente toda la tabla
                        ('VALIGN', (0, 3), (-1, -1), 'MIDDLE'),   
                        ('SPAN', (0, len(tabla)-1), (2, len(tabla)-1)),
                        ('ALIGN', (0, len(tabla)-1), (2, len(tabla)-1), 'CENTER')
                        ]

    t = Table(tabla, colWidths, rowHeights=rowHeights, repeatRows=4, style=estilos_comunes)
    
    elements.append(t)

    doc.build(elements, canvasmaker=PageNumCanvas)
    return pathpdf
