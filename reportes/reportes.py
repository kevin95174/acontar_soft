import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas

def iniciar_reporte(reporte, encabezados, datos, colWidths, direccion):

    pdf_name = str(reporte)+".pdf"
    pathpdf = os.path.join(direccion, pdf_name)

    doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                            rightMargin=40, leftMargin=40,
                            topMargin=20, bottomMargin=50)
    
    elements = []

    # Titulo 1        
    h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName = 'HELVETICA-BOLD')
    titulo1 = [[Paragraph(str(reporte),h1)]]
    titulo2 = [[Paragraph(str("Inventario patrimonial al 31-12-2024"),h1)]]
    titulo3 = [[Paragraph(str("Oficina Regional Sur Arequipa"),h1)]]

    c1 = ParagraphStyle(name='Normal', fontSize=7, leading=8)
    
    # Crear una lista para almacenar los datos de la tabla
    table_data = []
    # Iterar sobre las filas de la consulta
    for row in datos:
        # Crear una lista para almacenar las celdas de la fila
        row_data = []
        # Iterar sobre las celdas de la fila y crear un objeto Paragraph para cada una
        for index, cell in enumerate(row):
            # Agregar la celda a la lista de celdas de la fila
            row_data.append(Paragraph(str(cell), c1))
        
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
                        ]

    print(f"Reporte: {reporte}")
    print(f"Condición CONCILIACIÓN DE INVENTARIO: {str(reporte) == 'CONCILIACIÓN DE INVENTARIO'}")

    if str(reporte) == "CONCILIACIÓN DE INVENTARIO":
            estilos_comunes.extend(
                        ('ALIGN', (2, 4), (2, -1), 'RIGHT'),  # columna 3 alineada a la derecha
                        ('ALIGN', (4, 4), (4, -1), 'RIGHT'),  # columna 5 alineada a la derecha
                        ('ALIGN', (6, 4), (6, -1), 'RIGHT'),  # columna 7 alineada a la derecha
                        ('ALIGN', (3, 4), (3, -1), 'CENTER'),  # columna 4 centrada
                        ('ALIGN', (5, 4), (5, -1), 'CENTER'),  # columna 6 centrada
                        ('ALIGN', (7, 4), (7, -1), 'CENTER'),  # columna 8 centrada
                            )
    
    t=Table(tabla, colWidths, rowHeights=rowHeights, repeatRows =4, style=estilos_comunes)
    
    elements.append(t)

    doc.build(elements, canvasmaker=PageNumCanvas)
