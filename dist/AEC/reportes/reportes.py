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
        
        tabla = titulo1 + [encabezados] + list(table_data)

        # Definir las alturas de fila, siendo 20 el valor para la primera fila
        rowHeights = [55] + [None] * (len(tabla) - 1)
        
        t=Table(tabla, colWidths, rowHeights=rowHeights, repeatRows =2, style=[
                                        # titulo Reporte...
                                        ('SPAN', (0, 0), (-1, 0)),
                                        # encabezado
                                        ('BACKGROUND', (0, 1), (-1, 1), '#DBDBDB'),
                                        # Bordes de la tabla
                                        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
                                        # cuerpo de la tabla
                                        # define el tamaño fuente y horientacion del cuerpo de la tabla
                                        ('FONTSIZE', (0, 1), (-1, -1), 7),
                                        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                                        ('ALIGN', (0, 2), (10, -1), 'LEFT'),
                                        # centra la columna 11 ESTADO...
                                        # ('ALIGN', (4, 8), (4, -1), 'CENTER'),
                                        # ('ALIGN', (10, 8), (10, -1), 'CENTER'),
                                        ('ALIGN', (11, 3), (11, -1), 'RIGHT'),
                                        # alinea verticalmente toda la tabla
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        ])

        elements.append(t)

        doc.build(elements, canvasmaker=PageNumCanvas)
